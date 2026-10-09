"""Directed local CVM extraction for the 29 frozen B00S issuers only.

Receipt is joined on the same reporting key, using the conservative last receipt
when a CVM metadata key collides. Originals are never rewritten. Runtime replay
uses only the compact frozen extract, not the database or these archives.
"""
from b00s_variants import *
from stage1_pit import ident, norm, gzwrite
from zipfile import ZipFile
from io import TextIOWrapper

def rows(z, member):
    with TextIOWrapper(z.open(member),encoding='latin1') as f:
        yield from csv.DictReader(f,delimiter=';')

def collect(data_root):
    wanted={r['cnpj'] for r in candidates()};facts=[];fre=[];audits=[];sources=[]
    for year in range(2010,2026):
        for kind in ['dfp','fre']:
            path=data_root/f'{kind}_cia_aberta_{year}.zip'
            digest=sha(path);url=f'https://dados.cvm.gov.br/dados/CIA_ABERTA/{kind.upper()}/DADOS/{path.name}'
            sources.append(dict(path=path.name,sha256=digest,url=url,bytes=path.stat().st_size))
            with ZipFile(path) as z:
                metas=list(rows(z,f'{kind}_cia_aberta_{year}.csv'))
                if kind=='dfp':
                    meta={}
                    for r in sorted(metas,key=lambda r:(r['DT_RECEB'],r['ID_DOC'])):
                        meta[r['CNPJ_CIA'],r['DT_REFER'],r['VERSAO']]=r
                    for perimeter in ['ind','con']:
                        for statement in ['DRE','BPA','BPP','DFC_MI','DFC_MD']:
                            member=f'dfp_cia_aberta_{statement}_{perimeter}_{year}.csv'
                            if member not in z.namelist():continue
                            for r in rows(z,member):
                                c=ident(r['CNPJ_CIA'])
                                if c not in wanted:continue
                                code=r['CD_CONTA'];desc=norm(r['DS_CONTA'])
                                keep=(statement=='DRE' and (len(code)<=7 or code.startswith('3.99.01.')) or
                                    statement in ['BPA','BPP'] and len(code)<=7 or
                                    statement.startswith('DFC') and (code in ['6.01','6.02','6.03'] or any(s in desc for s in ['IMOBILIZADO','INTANGIVEL','DIVIDEND','JUROS SOBRE','AQUISICAO','EMPRESTIM','JUROS PAG'])))
                                if not keep:continue
                                m=meta.get((r['CNPJ_CIA'],r['DT_REFER'],r['VERSAO']))
                                if not m:continue
                                if m['DT_RECEB'][:10]>'2025-06-30':continue
                                facts.append(dict(cnpj=c,year=int(r['DT_FIM_EXERC'][:4]),period_start=r.get('DT_INI_EXERC',''),
                                    period_end=r['DT_FIM_EXERC'],reference=r['DT_REFER'],version=int(r['VERSAO']),
                                    received=m['DT_RECEB'][:10],docid=m['ID_DOC'],perimeter=perimeter,statement=statement,
                                    account=code,description=r['DS_CONTA'],value=float(r['VL_CONTA']),scale=r['ESCALA_MOEDA'],
                                    source=member,archive_sha256=digest,url=url))
                    member=f'dfp_cia_aberta_parecer_{year}.csv'
                    if member in z.namelist():
                        for r in rows(z,member):
                            if ident(r['CNPJ_CIA']) not in wanted:continue
                            m=meta.get((r['CNPJ_CIA'],r['DT_REFER'],r['VERSAO']))
                            if m and m['DT_RECEB'][:10]<='2025-06-30':
                                audits.append(dict(cnpj=ident(r['CNPJ_CIA']),reference=r['DT_REFER'],received=m['DT_RECEB'][:10],docid=m['ID_DOC'],
                                    source=member,archive_sha256=digest,url=url,raw=r))
                else:
                    meta={r['ID_DOC']:r for r in metas}
                    for part in ['capital_social','capital_social_classe_acao','capital_social_aumento','capital_social_desdobramento',
                                 'capital_social_reducao','distribuicao_dividendos','distribuicao_dividendos_classe_acao',
                                 'endividamento','obrigacao','transacao_parte_relacionada','direito_acao']:
                        member=f'fre_cia_aberta_{part}_{year}.csv'
                        if member not in z.namelist():continue
                        for r in rows(z,member):
                            if ident(r['CNPJ_Companhia']) not in wanted:continue
                            m=meta.get(r['ID_Documento'])
                            if m and m['DT_RECEB'][:10]<='2025-06-30':
                                fre.append(dict(cnpj=ident(r['CNPJ_Companhia']),received=m['DT_RECEB'][:10],docid=m['ID_DOC'],
                                    source=member,part=part,archive_sha256=digest,url=m['LINK_DOC'],raw=r))
        print('Extracted',year,len(facts),len(fre),flush=True)
    # Archive rows retain raw reporting keys and hashes; no availability inferred
    # from a document's fiscal year or the retrieval date.
    gzwrite(INPUT/'cvm_directed_extract.json.gz',dict(facts=facts,fre=fre,audits=audits))
    jsonwrite(INPUT/'cvm_directed_sources.json',sources)
    print('Finished',len(facts),len(fre),len(audits))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);collect(p.parse_args().data_root)
