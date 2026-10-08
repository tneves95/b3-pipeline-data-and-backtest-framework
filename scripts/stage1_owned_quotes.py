"""Freeze only owned securities/rights from the existing local COTAHIST archives."""
import argparse
import hashlib
import io
from pathlib import Path
from zipfile import ZipFile
from stage1_pit import ROOT, OUT, gzwrite, gzread

NAMES = set('CCRO3 MOTV3 WEGE3 ITUB4 BBDC4 TBLE3 EGIE3 CMIG4 HYPE3 RADL3 XPBR31 CMIG1 CMIG2 CCRO1 WEGE1 ITUB2 BBDC2 HYPE1 RADL1'.split())

def freeze(root, names=None, stem='owned_quotes', years=None, end='2026-06-30'):
    names=NAMES if names is None else names
    years=range(2014,2027) if years is None else years
    rows=[]; sources=[]
    for year in years:
        cache=OUT/f'cache/{stem}_{year}.json.gz'
        if cache.exists():
            data=gzread(cache);rows.extend(data['quotes']);sources.append(data['source']);continue
        path=root/f'data/raw/COTAHIST_A{year}.ZIP'
        source=dict(file=path.name,sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),
                    url=f'https://bvmf.bmfbovespa.com.br/InstDados/SerHist/{path.name}',provenance='LOCAL_PREEXISTING')
        selected=[]
        with ZipFile(path) as z:
            for name in z.namelist():
                with io.BufferedReader(z.open(name),buffer_size=1024*1024) as f:
                    for lineno,line in enumerate(f,1):
                        if line[:2]!=b'01' or line[24:27]!=b'010':continue
                        t=line[12:24].decode().strip()
                        if t not in names:continue
                        raw=line[2:10].decode();day=raw[:4]+'-'+raw[4:6]+'-'+raw[6:8]
                        if not '2014-06-30'<=day<=end:continue
                        factor=int(line[210:217]);assert factor>0
                        selected.append(dict(ticker=t,date=day,close=int(line[108:121])/100/factor,
                            isin=line[230:242].decode().strip(),quotation_factor=factor,
                            line=lineno,record_sha256=hashlib.sha256(line).hexdigest()))
        selected.sort(key=lambda r:(r['ticker'],r['date']))
        gzwrite(cache,dict(source=source,quotes=selected));rows.extend(selected);sources.append(source)
        print(year,len(selected),flush=True)
    return rows,sources

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=ROOT.parent)
    freeze(p.parse_args().data_root)
