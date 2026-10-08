#!/usr/bin/env python3
"""Targeted CVM originals: missing versions that can change eligibility."""
from stage1_pit import *
from io import BytesIO
from xml.etree import ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import requests

TARGETS={'35261','54003','63076','54668','54757','123589','7822','34821','34545','39433','9891','9577','35576','54543','62839','71894','72337'}
MEMBERS=['Documento.xml','InfoFinaDFin.xml','PeriodoDemonstracaoFinanceira.xml','ComposicaoCapitalSocialDemonstracaoFinanceiraNegocios.xml']

def recover(row):
    doc=row['ID_DOC'];folder=OUT/'originals';folder.mkdir(exist_ok=True)
    path=folder/f'dfp_{doc}.zip';url=row['LINK_DOC'].replace('http:','https:')
    modern=folder/f'dfp_modern_{doc}.zip'
    if modern.exists():return parse_modern(modern,row)
    if not path.exists():
        response=requests.get(url,timeout=120);response.raise_for_status()
        with ZipFile(BytesIO(response.content)) as z:
            members=[n for n in z.namelist() if n.lower().endswith('.dfp')]
            if not members:
                with ZipFile(modern,'w',compression=8) as dest:
                    for n in z.namelist():
                        if 'DFP' in n and n.endswith('.xml'):dest.writestr(n,z.read(n))
                modern.with_suffix('.json').write_text(json.dumps(dict(url=url,received=row['DT_RECEB'],original_response_sha256=hashlib.sha256(response.content).hexdigest(),extract_sha256=hashlib.sha256(modern.read_bytes()).hexdigest()),indent=2))
                return parse_modern(modern,row)
            member=members[0]
            with ZipFile(BytesIO(z.read(member))) as zi, ZipFile(path,'w',compression=8) as zo:
                for n in MEMBERS:
                    if n in zi.namelist():zo.writestr(n,zi.read(n))
        manifest=dict(document=doc,url=url,received=row['DT_RECEB'],reference=row['DT_REFER'],cnpj=ident(row['CNPJ_CIA']),
            original_response_sha256=hashlib.sha256(response.content).hexdigest(),extract_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        path.with_suffix('.json').write_text(json.dumps(manifest,indent=2))
    print('original ready',doc,row['DENOM_CIA'],flush=True)
    return parse(path,row)

def parse(path,row):
    facts=[]
    with ZipFile(path) as z:
        periods={int(p.findtext('NumeroIdentificacaoPeriodo')):(p.findtext('DataInicioPeriodo')[:10],p.findtext('DataFimPeriodo')[:10]) for p in ET.fromstring(z.read('PeriodoDemonstracaoFinanceira.xml'))}
        document=ET.fromstring(z.read('Documento.xml'))
        scale=document.findtext('.//CodigoEscalaMoeda')
        # CVM 1 = unidade, 2 = mil; confirm against structured CSV overlaps.
        scale_value=1/1000 if scale=='1' else 1
        if scale not in ['1','2']:raise ValueError(('Unknown monetary scale',path,scale))
        for item in ET.fromstring(z.read('InfoFinaDFin.xml')):
            code=item.findtext('PlanoConta/NumeroConta') or ''
            desc=item.findtext('DescricaoConta1') or item.findtext('PlanoConta/DescricaoConta') or ''
            scope=item.findtext('PlanoConta/VersaoPlanoConta/CodigoTipoInformacaoFinanceira')
            if scope not in ['1','2']:continue
            n=norm(desc);metric=None
            if re.fullmatch(r'3\.\d{2}',code) and n.startswith('LUCRO') and 'PERIODO' in n:metric='ni'
            elif code=='3.01':metric='revenue'
            elif re.fullmatch(r'3\.\d{2}',code) and n.startswith('RESULTADO ANTES DO RESULTADO FINANCEIRO'):metric='ebit'
            elif code=='1':metric='assets'
            elif code=='1.01' and n.startswith('ATIVO CIRCULANTE'):metric='ca'
            elif code=='2.01' and n.startswith('PASSIVO CIRCULANTE'):metric='cl'
            elif re.fullmatch(r'2\.\d{2}',code) and n.startswith('PATRIMONIO LIQUIDO'):metric='equity'
            elif re.fullmatch(r'2\.\d{2}\.\d{2}',code) and n.startswith('CAPITAL SOCIAL'):metric='capital'
            elif code=='2.01.04':metric='debt_current'
            elif code=='2.02.01':metric='debt_long'
            elif code=='6.01':metric='ocf'
            elif code.startswith('6.03') and re.search(r'DIVIDEND|JUROS.*CAPITAL|JCP|JSCP',n) and not re.search(r'RECEBID|INVESTID|NAO CONTROLAD|REVERS|PRESCRIT',n):metric='distributions'
            elif code in ['7.08.04.01','7.08.04.02']:metric='distributions_dva'
            if metric is None:continue
            for p,(start,end) in periods.items():
                if not end or end.startswith('0001'):continue
                if code[0] in '367' and (pd.Timestamp(end)-pd.Timestamp(start)).days<330:continue
                value=num(item.findtext(f'ValorConta{p}'))
                if value is None:continue
                facts.append(dict(cnpj=ident(row['CNPJ_CIA']),year=int(end[:4]),period_end=end,received=row['DT_RECEB'],reference=row['DT_REFER'],version=int(row['VERSAO']),docid=row['ID_DOC'],perimeter={'1':'ind','2':'con'}[scope],metric=metric,value=value*scale_value,account=code,description=desc,source='recovered_original_'+row['ID_DOC']))
    if not any(r['metric']=='ni' for r in facts):raise ValueError(('No income extracted',path))
    return facts

def parse_modern(path,row):
    facts=[]
    with ZipFile(path) as z:
        member=next(n for n in z.namelist() if 'DFP' in n and n.endswith('.xml'))
        root=ET.fromstring(z.read(member));d=root.find('DadosDFP')
        assert d.findtext('EscalaMoeda')=='2'
        for section,perimeter in [('DfIndividuais','ind'),('DfConsolidadas','con')]:
            parent=d.find('Formulario/'+section)
            if parent is None:continue
            for item in parent.findall('.//Conta'):
                code=item.findtext('CodigoConta');desc=item.findtext('DescricaoConta');n=norm(desc)
                metric=None
                if re.fullmatch(r'3\.\d{2}',code) and n.startswith('LUCRO') and 'PERIODO' in n:metric='ni'
                elif code=='3.01':metric='revenue'
                elif code=='1':metric='assets'
                elif code=='1.01' and n.startswith('ATIVO CIRCULANTE'):metric='ca'
                elif code=='2.01' and n.startswith('PASSIVO CIRCULANTE'):metric='cl'
                elif re.fullmatch(r'2\.\d{2}',code) and n.startswith('PATRIMONIO LIQUIDO'):metric='equity'
                elif re.fullmatch(r'2\.\d{2}\.\d{2}',code) and n.startswith('CAPITAL SOCIAL'):metric='capital'
                elif code=='2.01.04':metric='debt_current'
                elif code=='2.02.01':metric='debt_long'
                elif code=='6.01':metric='ocf'
                elif code.startswith('6.03') and re.search(r'DIVIDEND|JUROS.*CAPITAL|JCP|JSCP',n) and not re.search(r'RECEBID|INVESTID|NAO CONTROLAD|REVERS|PRESCRIT',n):metric='distributions'
                elif code in ['7.08.04.01','7.08.04.02']:metric='distributions_dva'
                if metric is None:continue
                for p in ['Ultimo','Penultimo','Antepenultimo']:
                    end=d.findtext('DtFim'+p+'ExercicioSocial');v=num(item.findtext(p+'Exercicio'))
                    if not end or v is None:continue
                    end=pd.to_datetime(end,dayfirst=True).strftime('%Y-%m-%d')
                    facts.append(dict(cnpj=ident(row['CNPJ_CIA']),year=int(end[:4]),period_end=end,received=row['DT_RECEB'],reference=row['DT_REFER'],version=int(row['VERSAO']),docid=row['ID_DOC'],perimeter=perimeter,metric=metric,value=v,account=code,description=desc,source='recovered_original_'+row['ID_DOC']))
    assert any(r['metric']=='ni' for r in facts),path
    return facts

def main(root):
    metadata=[]
    for y in [2010,2011,2013,2015,2016,2017,2022]:
        with ZipFile(root/f'data/cvm/dfp_cia_aberta_{y}.zip') as z:
            d=csvzip(z,f'dfp_cia_aberta_{y}.csv');metadata.extend(d[d.ID_DOC.isin(TARGETS)].to_dict('records'))
    assert len(metadata)==len(TARGETS)
    with ThreadPoolExecutor(max_workers=3) as executor:
        results=list(executor.map(recover,metadata))
    facts=[r for rs in results for r in rs]
    (OUT/'recovered_facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2))
    print('Facts',len(facts),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);main(p.parse_args().data_root)
