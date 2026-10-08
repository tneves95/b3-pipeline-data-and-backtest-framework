"""Explicit online collection of original, dated CVM note/management attachments.

Not used in offline replay. The public ENET viewer embeds each original PDF in
hdnConteudoArquivo. Preserve the decoded original and its SHA-256, not a screenshot.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import base64
import gzip
import hashlib
import io
import json
import re
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from b00s_variants import INPUT, jsonwrite

DEST=INPUT/'review_originals'
BASE='https://www.rad.cvm.gov.br/ENET/'

def collect(job):
    docid,cutoff=job['docid'],job['cutoff']
    url=BASE+'frmGerenciaPaginaFRE.aspx?CodigoTipoInstituicao=1&NumeroSequencialDocumento='+docid
    session=requests.Session()
    session.headers['User-Agent']='Mozilla/5.0'
    for attempt in range(3):
        response=session.get(url,timeout=60);response.raise_for_status()
        page=BeautifulSoup(response.content,'html.parser')
        node=page.find(id='lblDataEnvio');receipt=node.get_text(strip=True) if node else ''
        if re.match(r'\d{2}/\d{2}/\d{4}',receipt):break
    else:raise ValueError(('CVM returned no dated header',docid))
    dd,mm,yyyy=receipt[:10].split('/');received=f'{yyyy}-{mm}-{dd}'
    if received>cutoff:raise ValueError(('Future document',docid,received,cutoff))
    if page.find(id='hdnHabilitaCaptcha').get('value')=='S':raise ValueError('Interactive CAPTCHA required; no bypass')
    token=page.find(id='hdnHash')['value']
    kind=page.find(id='hdnCodigoTipoDocumento')['value']
    rows=[]
    # DFP and ITR use different public viewer group IDs. Read the form's
    # advertised attachments; do not confuse a wrong group with absent evidence.
    advertised={o.get('value'):o.get_text(' ',strip=True) for o in page.find_all('option')}
    groups=[int(k.split('|')[1]) for k,v in advertised.items() if k and k.startswith('PDF|')
            and (v=='Notas Explicativas' or v.startswith('Relatório da Administração')
                 or v=='Comentário do Desempenho')]
    if not groups:raise ValueError(('No relevant attachment groups advertised',docid))
    for group in job.get('groups',groups):
        name=f'cvm_{docid}_g{group}'
        path=DEST/(name+'.pdf.gz')
        view=BASE+'frmExibirArquivoFRE.aspx'
        params=dict(NumeroSequencialDocumento=docid,CodigoGrupo=group,CodigoQuadro=0,Tipo='PDF',CodTipoDocumento=kind,Hash=token)
        r=session.get(view,params=params,timeout=60);r.raise_for_status()
        pdfpage=BeautifulSoup(r.content,'html.parser');node=pdfpage.find(id='hdnConteudoArquivo')
        if not node or not node.get('value'):
            rows.append(dict(docid=docid,group=group,status='ATTACHMENT_ABSENT',received=received,url=url));continue
        raw=base64.b64decode(node['value'],validate=True)
        if not raw.startswith(b'%PDF'):raise ValueError(('Not a PDF',name))
        digest=hashlib.sha256(raw).hexdigest();path.write_bytes(gzip.compress(raw,mtime=0))
        pdf=PdfReader(io.BytesIO(raw));pages=[p.extract_text() for p in pdf.pages]
        textpath=DEST/(name+'.pages.json.gz')
        textpath.write_bytes(gzip.compress(json.dumps(pages,ensure_ascii=False).encode(),mtime=0))
        rows.append(dict(docid=docid,group=group,status='ARCHIVED',received=received,receipt_label=receipt,
            cutoff=cutoff,ticker=job.get('ticker',''),url=url,original_sha256=digest,
            original=str(path.relative_to(INPUT)),pages=str(textpath.relative_to(INPUT)),page_count=len(pages),
            extraction='Decoded original PDF embedded by the public CVM attachment viewer; page numbers are 1-based'))
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('jobs');args=p.parse_args()
    DEST.mkdir(parents=True,exist_ok=True)
    mp=INPUT/'review_original_sources.json';old=json.loads(mp.read_text()) if mp.exists() else []
    jobs=json.loads(Path(args.jobs).read_text());results={(r['docid'],r['group']):r for r in old};failed=[]
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures={ex.submit(collect,j):j for j in jobs}
        for f in as_completed(futures):
            job=futures[f]
            try:
                for r in f.result():results[r['docid'],r['group']]=r
                print(job['ticker'],job['docid'],'archived',flush=True)
            except Exception as e:
                failed.append(job);print(job,str(e),flush=True)
            jsonwrite(mp,[v for k,v in sorted(results.items())])
    if failed:raise SystemExit(f'{len(failed)} collection jobs failed; archived successes preserved')

if __name__=='__main__':main()
