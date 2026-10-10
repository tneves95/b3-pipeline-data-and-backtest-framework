"""Opt-in retrieval of exact missing CVM document IDs, with fixed byte/count limits.

Only identified original DFP versions are requested. Full responses are temporary;
only the required financial XML is retained locally. No B3 downloads are made.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import tempfile
import threading
import xml.etree.ElementTree as ET
import zipfile

import pandas as pd
import requests
from .audit import HERE, sha256
from .filings import metric_for, parse_original

MAX_RESPONSE = 40 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024


def compact_original(response, destination):
    provenance=[]
    with zipfile.ZipFile(response) as outer:
        nested=next((n for n in outer.namelist() if n.lower().endswith('.dfp')),None)
        if nested:
            inner=zipfile.ZipFile(io.BytesIO(outer.read(nested)))
            members=['Documento.xml','InfoFinaDFin.xml','PeriodoDemonstracaoFinanceira.xml']
            raw_members=[(n,inner.read(n)) for n in members]
        else:
            names=[n for n in outer.namelist() if n.endswith('.xml') and 'DFP' in n]
            raw_members=[]
            for n in names:
                raw=outer.read(n);root=ET.fromstring(raw)
                d=root.find('DadosDFP')
                if d is None: continue
                for child in list(d):
                    if child.tag=='AnexosDocumento': d.remove(child)
                # Retain required identity, scale, periods and eight metrics; omit text notes and personal fields.
                for node in root.findall('Documento/ResponsavelDocumento'): root.find('Documento').remove(node)
                form=d.find('Formulario')
                for child in list(form):
                    if child.tag not in ('DfIndividuais','DfConsolidadas'): form.remove(child)
                for section in list(form):
                    for parent in section.iter():
                        for child in list(parent):
                            if child.tag=='Conta' and metric_for(child.findtext('CodigoConta',''),child.findtext('DescricaoConta','')) is None:
                                parent.remove(child)
                provenance.append(dict(member=n,original_member_sha256=hashlib.sha256(raw).hexdigest()))
                raw_members.append((Path(n).name,ET.tostring(root,encoding='utf-8',xml_declaration=True)))
                break
        if not raw_members: raise ValueError('No supported original DFP XML')
        with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for n,raw in raw_members:
                info=zipfile.ZipInfo(n,date_time=(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(info,raw)
                if nested: provenance.append(dict(member=n,original_member_sha256=hashlib.sha256(raw).hexdigest()))
    return provenance


def fetch(panel, output, scratch, maximum_documents=73, *, maximum_response=MAX_RESPONSE,
          maximum_total=MAX_TOTAL, read_timeout=60):
    if (output/'round2_manifest.json').exists():
        raise ValueError('Existing round checkpoint: use a new output directory')
    if not 0<maximum_response<=80*1024*1024 or not 0<maximum_total<=MAX_TOTAL:
        raise ValueError('Response/total limits exceed the directed retrieval policy')
    folder=output/'originals';folder.mkdir(parents=True,exist_ok=True);scratch.mkdir(parents=True,exist_ok=True)
    rows=panel[panel.status=='EXACT_ORIGINAL_NOT_LOCAL'].head(maximum_documents).to_dict('records')
    lock=threading.Lock();total=0
    def one(row):
        nonlocal total
        doc=str(row['required_docid']);doc=str(int(float(doc)))
        path=folder/f'dfp_{doc}.zip'
        url=f'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDownloadDocumento.aspx?CodigoInstituicao=1&NumeroSequencialDocumento={doc}'
        record=dict(required_docid=doc,url=url,status='NOT_REQUESTED',response_bytes=0)
        if path.exists():
            record['status']='COMPACT_ORIGINAL_ALREADY_LOCAL';return record
        actual=0;reserved=False
        try:
            with lock:
                if total + maximum_response > maximum_total:
                    record['status']='TOTAL_BYTE_BUDGET_REACHED';return record
                total += maximum_response
                reserved=True
            h=hashlib.sha256()
            with tempfile.TemporaryFile(dir=scratch) as f:
                with requests.get(url,stream=True,timeout=(15,read_timeout)) as response:
                    response.raise_for_status()
                    for chunk in response.iter_content(1 << 20):
                        actual+=len(chunk)
                        if actual>maximum_response: raise ValueError('Response byte budget exceeded')
                        h.update(chunk);f.write(chunk)
                f.seek(0)
                provenance=compact_original(f,path)
            required=dict(cnpj=row['cnpj'],period_end=row['requested_period'],version=int(row['required_filing_id'].rsplit('_',1)[1]))
            parse_original(path,required)
            path.with_suffix('.json').write_text(json.dumps(dict(document=doc,url=url,received=row['required_received'],
                reference=row['requested_period'],cnpj=row['cnpj'],original_response_sha256=h.hexdigest(),
                original_response_bytes=actual,extract_sha256=sha256(path),members=provenance),indent=2)+'\n')
            record.update(status='EXACT_ORIGINAL_FETCHED',response_bytes=actual,extract_bytes=path.stat().st_size)
        except Exception as e:
            if path.exists(): path.unlink()
            record.update(status='FETCH_OR_PARSE_FAILED',response_bytes=actual,reason=str(e)[:250])
        finally:
            if reserved:
                with lock: total -= maximum_response - actual
        print(f'CVM original {doc}: {record["status"]}',flush=True)
        return record
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(one,rows))
    pd.DataFrame(results).to_csv(output/'filing_fetch_attempts.csv',index=False)
    return results


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=HERE/'local_only/round2')
    p.add_argument('--scratch',type=Path,default=Path('/tmp/b3-fundamentals-round2'));p.add_argument('--max-documents',type=int,default=73)
    p.add_argument('--max-response-mib',type=int,default=40);p.add_argument('--max-total-mib',type=int,default=1024)
    p.add_argument('--read-timeout',type=int,default=60)
    a=p.parse_args();d=pd.read_csv(a.output/'filing_recovery.csv',dtype={'cnpj':str,'required_docid':str})
    result=fetch(d,a.output,a.scratch,a.max_documents,maximum_response=a.max_response_mib*1024*1024,
                 maximum_total=a.max_total_mib*1024*1024,read_timeout=a.read_timeout)
    print(json.dumps(dict(attempted=len(result),downloaded=sum(r['status']=='EXACT_ORIGINAL_FETCHED' for r in result),
        response_bytes=sum(r['response_bytes'] for r in result)),indent=2))

if __name__=='__main__':main()
