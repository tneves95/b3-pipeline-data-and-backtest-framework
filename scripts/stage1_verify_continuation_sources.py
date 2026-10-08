"""Optional local provenance verification; never recollect or rebuild accepted series."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile
from stage1_resume import OUT, gzread


def verify(data_root):
    archives={};extracts={};count=0
    for name in ['continuation_targeted_fre.json','continuation_b00s_targeted_fre.json',
                 'continuation_capital_events_fre.json','continuation_irb_capital_fre.json']:
        for r in json.loads((OUT/name).read_text()):
            member=r['source_member'];year=int(member[-8:-4])
            if year not in archives:archives[year]=ZipFile(data_root/f'data/cvm/fre_cia_aberta_{year}.zip')
            if member not in extracts:
                raw=list(csv.DictReader(io.TextIOWrapper(archives[year].open(member),encoding='latin1'),delimiter=';'))
                extracts[member]={json.dumps(x,sort_keys=True) for x in raw}
            original={k:v for k,v in r.items() if k not in ('archive','kind','source_member','metadata')}
            assert json.dumps(original,sort_keys=True) in extracts[member],(name,r['ID_Documento'])
            count+=1
    sources={}
    for p in sorted((OUT/'cache').glob('continuation*quotes*.json.gz')):
        d=gzread(p);s=d['source'];sources[s['file']]=s['sha256']
    for name,sha in sources.items():
        with (data_root/'data/raw'/name).open('rb') as f:
            assert hashlib.file_digest(f,'sha256').hexdigest()==sha,name
    for z in archives.values():z.close()
    print('Verified original FRE rows:',count,'COTAHIST source hashes:',len(sources))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True)
    verify(p.parse_args().data_root)
