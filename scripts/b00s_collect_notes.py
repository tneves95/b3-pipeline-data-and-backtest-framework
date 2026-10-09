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
import zipfile
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from b00s_variants import INPUT, jsonwrite

DEST=INPUT/'review_originals'
BASE='https://www.rad.cvm.gov.br/ENET/'

def unpack_download(job, raw):
    """Read original attachments when the public viewer has an empty header.

    The complete-document download includes the submitted DFP/ITR and CVM's
    dated delivery metadata. Do not use its newly rendered aggregate PDF.
    """
    docid=str(job['docid']);cutoff=job['cutoff']
    outer=zipfile.ZipFile(io.BytesIO(raw))
    names=[n for n in outer.namelist() if n.endswith(('.dfp','.itr'))]
    if len(names)!=1:raise ValueError('One submitted financial document required')
    name=names[0];kind=name.rsplit('.',1)[1].upper()
    meta_name=f'FormularioDemonstracaoFinanceira{kind}.xml'
    metadata=outer.read(meta_name);root=ET.fromstring(metadata)
    received=root.findtext('.//DataEntrega','')[:10]
    if root.findtext('.//NumeroSequencialDocumento')!=docid or not re.fullmatch(r'20\d\d-\d\d-\d\d',received):
        raise ValueError('Download identity or delivery date not verified')
    if received>cutoff:raise ValueError(('Future download',docid,received,cutoff))
    container=outer.read(name);inner=zipfile.ZipFile(io.BytesIO(container))
    inner_meta=ET.fromstring(inner.read(meta_name))
    for key in ['DataReferenciaDocumento','NumeroVersaoDocumento']:
        if root.findtext('.//'+key)!=inner_meta.findtext('.//'+key):raise ValueError('Different submitted version')
    prefix=DEST/f'cvm_{docid}'
    for suffix,content in [(f'.{kind.lower()}.gz',container),('.delivery.xml.gz',metadata)]:
        Path(str(prefix)+suffix).write_bytes(gzip.compress(content,mtime=0))
    rows=[]
    url='https://www.rad.cvm.gov.br/ENETCONSULTA/frmDownloadDocumento.aspx?CodigoInstituicao=1&NumeroSequencialDocumento='+docid
    for node in ET.fromstring(inner.read('AnexoDocumento.xml')):
        group=int(node.findtext('NumeroGrupoRelacionado','0'))
        if group not in job.get('groups',[412,1653,193,192]):continue
        pdfraw=base64.b64decode(node.findtext('ImagemObjetoArquivoPdf'),validate=True)
        if not pdfraw.startswith(b'%PDF'):raise ValueError('Not an original PDF attachment')
        path=DEST/f'cvm_{docid}_g{group}.pdf.gz';path.write_bytes(gzip.compress(pdfraw,mtime=0))
        pages=[p.extract_text() for p in PdfReader(io.BytesIO(pdfraw)).pages]
        textpath=DEST/f'cvm_{docid}_g{group}.pages.json.gz'
        textpath.write_bytes(gzip.compress(json.dumps(pages,ensure_ascii=False).encode(),mtime=0))
        rows.append(dict(docid=docid,group=group,status='ARCHIVED',received=received,
            receipt_label=root.findtext('.//DataEntrega'),cutoff=cutoff,ticker=job.get('ticker',''),url=url,
            original_sha256=hashlib.sha256(pdfraw).hexdigest(),original=str(path.relative_to(INPUT)),
            pages=str(textpath.relative_to(INPUT)),page_count=len(pages),
            extraction='Original PDF from AnexoDocumento.xml in submitted DFP/ITR. Delivery/version checked against CVM download metadata; generated aggregate PDF ignored.',
            submission=dict(path=str(Path(str(prefix)+f'.{kind.lower()}.gz').relative_to(INPUT)),sha256=hashlib.sha256(container).hexdigest(),
                metadata=str(Path(str(prefix)+'.delivery.xml.gz').relative_to(INPUT)),metadata_sha256=hashlib.sha256(metadata).hexdigest(),
                version=root.findtext('.//NumeroVersaoDocumento'),reference=root.findtext('.//DataReferenciaDocumento'))))
    if not rows:raise ValueError('No original financial attachments in download')
    return rows

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
    else:
        download='https://www.rad.cvm.gov.br/ENETCONSULTA/frmDownloadDocumento.aspx?CodigoInstituicao=1&NumeroSequencialDocumento='+docid
        response=session.get(download,timeout=(20,60));response.raise_for_status()
        return unpack_download(job,response.content)
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
