"""Recover exact point-in-time annual versions from compact local CVM originals."""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
import pandas as pd
from .audit import HERE, ROOT, sha256

METRICS = ['net_income','revenue','ebit','operating_cash_flow','current_assets','current_liabilities','equity','total_assets']


def norm(text):
    return ''.join(x for x in unicodedata.normalize('NFKD', text or '') if not unicodedata.combining(x)).upper()


def metric_for(code, description):
    name = norm(description).strip()
    if re.fullmatch(r'3\.\d{2}', code) and name.startswith('LUCRO') and 'PERIODO' in name:
        return 'net_income'
    if code == '3.01': return 'revenue'
    if re.fullmatch(r'3\.\d{2}', code) and name.startswith('RESULTADO ANTES DO RESULTADO FINANCEIRO'):
        return 'ebit'
    if code == '6.01': return 'operating_cash_flow'
    if code == '1.01' and name.startswith('ATIVO CIRCULANTE'): return 'current_assets'
    if code == '2.01' and name.startswith('PASSIVO CIRCULANTE'): return 'current_liabilities'
    if re.fullmatch(r'2\.\d{2}',code) and name.startswith('PATRIMONIO LIQUIDO'): return 'equity'
    if code == '1': return 'total_assets'
    return None


def monetary_value(value, *, brazilian=False):
    if value is None or not str(value).strip(): return None
    text=str(value).strip()
    if brazilian:
        text=text.replace('.', '').replace(',', '.')
    return float(text)


def parse_original(path, required):
    """Read only the requested reference/version; never borrow a comparative period."""
    facts=[]
    with zipfile.ZipFile(path) as z:
        if 'InfoFinaDFin.xml' in z.namelist():
            document=ET.fromstring(z.read('Documento.xml'))
            cnpj=document.findtext('.//NumeroCnpjCompanhiaAberta')
            scale=document.findtext('.//CodigoEscalaMoeda')
            if cnpj != required['cnpj'] or scale not in ('1','2'):
                raise ValueError('Original identity or monetary scale mismatch')
            if document.findtext('.//DataReferenciaDocumento','')[:10] != required['period_end']:
                raise ValueError('Original reference mismatch')
            if int(document.findtext('.//NumeroVersaoDocumento')) != int(required['version']):
                raise ValueError('Original filing version mismatch')
            scalar=0.001 if scale == '1' else 1.
            periods={p.findtext('NumeroIdentificacaoPeriodo'):(p.findtext('DataInicioPeriodo','')[:10],p.findtext('DataFimPeriodo','')[:10])
                for p in ET.fromstring(z.read('PeriodoDemonstracaoFinanceira.xml'))}
            for item in ET.fromstring(z.read('InfoFinaDFin.xml')):
                code=item.findtext('PlanoConta/NumeroConta','')
                desc=item.findtext('DescricaoConta1') or item.findtext('PlanoConta/DescricaoConta') or ''
                metric=metric_for(code,desc)
                perimeter={'1':'ind','2':'con'}.get(item.findtext('PlanoConta/VersaoPlanoConta/CodigoTipoInformacaoFinanceira'))
                if metric is None or perimeter is None: continue
                for period,(start,end) in periods.items():
                    if end != required['period_end']: continue
                    if code[0] in '36' and (pd.Timestamp(end)-pd.Timestamp(start)).days < 330: continue
                    value=monetary_value(item.findtext('ValorConta'+period))
                    if value is not None:
                        facts.append(dict(metric=metric,perimeter=perimeter,value=value*scalar,account=code,description=desc))
        else:
            candidates=[n for n in z.namelist() if n.endswith('.xml') and 'DFP' in n]
            root=next((ET.fromstring(z.read(n)) for n in candidates if ET.fromstring(z.read(n)).find('DadosDFP') is not None),None)
            if root is None: raise ValueError('Unsupported original DFP structure')
            d=root.find('DadosDFP')
            if root.findtext('DadosEmpresa/CnpjEmpresa') != required['cnpj']:
                raise ValueError('Original CNPJ mismatch')
            if int(root.findtext('Documento/VersaoDocumento')) != int(required['version']):
                raise ValueError('Original filing version mismatch')
            if pd.to_datetime(d.findtext('DataReferencia'),dayfirst=True).strftime('%Y-%m-%d') != required['period_end']:
                raise ValueError('Original reference mismatch')
            scale=d.findtext('EscalaMoeda')
            if scale not in ('1','2'): raise ValueError('Unknown monetary scale')
            scalar=0.001 if scale == '1' else 1.
            for section,perimeter in [('DfIndividuais','ind'),('DfConsolidadas','con')]:
                parent=d.find('Formulario/'+section)
                if parent is None: continue
                for item in parent.findall('.//Conta'):
                    code=item.findtext('CodigoConta','');desc=item.findtext('DescricaoConta','')
                    metric=metric_for(code,desc)
                    if metric is None: continue
                    value=monetary_value(item.findtext('UltimoExercicio'), brazilian=True)
                    if value is not None:
                        facts.append(dict(metric=metric,perimeter=perimeter,value=value*scalar,account=code,description=desc))
    return facts


def collapse_facts(facts):
    """One consistent perimeter for all metrics, consolidated when available."""
    perimeter='con' if any(f['perimeter']=='con' for f in facts) else 'ind'
    result={m: None for m in METRICS}
    for metric in METRICS:
        values={f['value'] for f in facts if f['perimeter']==perimeter and f['metric']==metric}
        if len(values)>1: raise ValueError('Ambiguous metric in original statement: '+metric)
        if values: result[metric]=next(iter(values))
    return result,perimeter


def recover_local(panel, root: Path, output: Path):
    missing=panel[panel.statement_status=='KNOWN_FILING_VALUE_MISSING']
    folder=root/'research/returns_2014_2026_selection/originals'
    recovery=root/'research/returns_2014_2026_inputs/cvm_recovery'
    extracts=json.loads((recovery/'extracts_manifest.json').read_text())
    records=[];facts_out=[]
    for p in missing.itertuples():
        doc=str(int(p.required_docid))
        required=dict(cnpj=p.cnpj,period_end=p.requested_period,version=int(p.required_version))
        path=next((v for v in [folder/f'dfp_{doc}.zip',folder/f'dfp_modern_{doc}.zip',
                              recovery/f'{doc}_financial_extract.zip',output/'originals'/f'dfp_{doc}.zip']
                   if v.exists()),None)
        result=dict(year=p.year,cnpj=p.cnpj,ticker=p.ticker,required_filing_id=p.required_filing_id,
            required_docid=doc,required_received=p.required_received,requested_period=p.requested_period,
            status='EXACT_ORIGINAL_NOT_LOCAL',**{m:None for m in METRICS})
        if path:
            if path.parent in (folder, output/'originals'):
                manifest=json.loads(path.with_suffix('.json').read_text())
                if manifest['extract_sha256'] != sha256(path) or manifest['received'] != p.required_received:
                    raise ValueError('Local original manifest does not match required receipt/hash')
                if 'cnpj' in manifest and manifest['cnpj'] != p.cnpj:
                    raise ValueError('Local manifest CNPJ mismatch')
            else:
                with zipfile.ZipFile(path) as z:
                    for r in [r for r in extracts if str(r['document_id'])==doc]:
                        if hashlib.sha256(z.read(r['member'])).hexdigest()!=r['sha256']:
                            raise ValueError('Preserved CVM extract hash mismatch')
                attempts=json.loads((recovery/'attempts.json').read_text())
                attempt=next(a for a in attempts if str(a['document_id'])==doc)
                if attempt['receipt'] != p.required_received: raise ValueError('Original receipt mismatch')
            facts=parse_original(path,required)
            values,perimeter=collapse_facts(facts)
            result.update(**values,status='EXACT_ORIGINAL_RECOVERED',perimeter=perimeter,
                source_path=str(path.relative_to(root)),source_sha256=sha256(path))
            facts_out.extend(dict(f,required_filing_id=p.required_filing_id,required_docid=doc,
                source_sha256=result['source_sha256']) for f in facts)
        records.append(result)
    frame=pd.DataFrame(records)
    frame.to_csv(output/'filing_recovery.csv',index=False)
    pd.DataFrame(facts_out).to_csv(output/'filing_recovered_accounts.csv',index=False)
    return frame


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory',type=Path,default=HERE/'local_only/data')
    parser.add_argument('--output',type=Path,default=HERE/'local_only/round2')
    args=parser.parse_args()
    if (args.output/'round2_manifest.json').exists():
        raise ValueError('Existing round checkpoint: use a new output directory')
    args.output.mkdir(parents=True,exist_ok=True)
    panel=pd.read_csv(args.inventory/'panel_company_date_diagnostic.csv',dtype={'cnpj':str})
    result=recover_local(panel,ROOT,args.output)
    print(result.groupby('status').size().to_string())


if __name__=='__main__': main()
