"""Leitor restrito ao pacote autorizado; registra cada leitura para a revisão cega."""
import argparse
import gzip
import hashlib
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path('/workspaces/b3-pipeline-data-and-backtest-framework/returns_2014_2026_stage1/.pr4-state')
PACKAGE = ROOT / 'audit-blind-20261009' / 'IRBR3_2019'
OUT = ROOT / 'independent-irb-2019'
LOG = OUT / 'read_log.jsonl'

def log(path, mode, pages=None, extra=None):
    p = pathlib.Path(path)
    record = dict(at=datetime.now(timezone.utc).isoformat(), path=str(p), mode=mode,
                  sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    if pages is not None:
        record['pages_1_based'] = pages
    if extra is not None:
        record['details'] = extra
    with LOG.open('a') as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + '\n')

def source(docid, group):
    path = PACKAGE / 'sources.json'
    sources = json.loads(path.read_text())
    log(path, 'source_registry_lookup')
    return next(s for s in sources if s['docid'] == str(docid) and s['group'] == int(group))

def pages_read(docid, group, page_list=None, pattern=None):
    s = source(docid, group)
    path = PACKAGE / s['pages']
    pages = json.loads(gzip.decompress(path.read_bytes()))
    if pattern:
        import re
        found = [i + 1 for i, t in enumerate(pages) if re.search(pattern, t, re.I)]
        log(path, 'machine_keyword_search', list(range(1,len(pages)+1)), {'pattern':pattern, 'matches':found})
        print(json.dumps({'docid':docid,'group':group,'matching_pages':found}))
        for n in found:
            lines = pages[n-1].splitlines()
            snippets = [line.strip() for line in lines if re.search(pattern,line,re.I)]
            print(n, ' | '.join(snippets)[:1200])
        return
    page_list = page_list or list(range(1,len(pages)+1))
    log(path, 'text_display_for_human_review', page_list)
    print(json.dumps({k:s[k] for k in ['docid','group','received','original_sha256']}, ensure_ascii=False))
    for n in page_list:
        print('\n--- DOCUMENTO', docid, 'GRUPO',group,'PÁGINA/UNIDADE',n,'---\n',pages[n-1])

def verify():
    sources=json.loads((PACKAGE/'sources.json').read_text())
    manifest=json.loads((PACKAGE/'bundle_manifest.json').read_text())
    rows=[]
    for s in sources:
        path=PACKAGE/s['original']
        compressed=path.read_bytes()
        raw=gzip.decompress(compressed)
        sha=hashlib.sha256(raw).hexdigest()
        log(path,'original_integrity_check',extra={'uncompressed_sha256':sha})
        row={'docid':s['docid'],'group':s['group'],'received':s['received'],'original':s['original'],
             'sha256':sha,'expected_sha256':s['original_sha256'],'match':sha==s['original_sha256'],
             'compressed_manifest_match':hashlib.sha256(compressed).hexdigest()==manifest['files'][s['original']]}
        if path.name.endswith('.pdf.gz'):
            import re
            row['uncompressed_format']='PDF'
            row['pdf_header']=raw[:8].decode('ascii',errors='replace')
            row['uncompressed_page_dictionary_count']=len(re.findall(rb'/Type\s*/Page\b',raw))
            row['page_count_note']='Contagem lexical parcial; não é validação de paginação se houver object streams.'
        rows.append(row)
    (OUT/'integrity_checks.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(rows,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--docid'); p.add_argument('--group',type=int)
    p.add_argument('--pages'); p.add_argument('--search'); p.add_argument('--verify',action='store_true')
    args=p.parse_args()
    if args.verify: verify()
    else:
        nums=[]
        if args.pages:
            for part in args.pages.split(','):
                if '-' in part:
                    lo,hi=map(int,part.split('-')); nums.extend(range(lo,hi+1))
                else: nums.append(int(part))
        pages_read(args.docid,args.group,nums or None,args.search)
