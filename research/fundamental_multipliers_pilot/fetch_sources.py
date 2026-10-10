"""Opt-in retrieval of four directed primary sources; snapshots remain local."""
import gzip
import hashlib
import json
from pathlib import Path
import requests
from .audit import HERE

URLS = {
    'irb_cash.html': 'https://ri.irbre.com/servicos-aos-investidores/historico-de-dividendos-e-remuneracao-aos-acionistas/',
    'irb_capital.html': 'https://ri.irbre.com/servicos-aos-investidores/recompra-de-acoes-desdobramentos-e-subscricao/',
    'irb_offer_2022.pdf': 'https://api.mziq.com/mzfilemanager/v2/d/0d797649-90df-4c56-aa01-6ee9c8a13d75/815cf4c8-5e02-116d-7f9e-ac7f924bd297?origin=2',
    'light_cash.html': 'https://ri.light.com.br/divulgacoes-e-resultados/dividendos-e-jscp/',
}


def fetch(folder):
    if (folder.parent/'round2_manifest.json').exists():
        raise ValueError('Existing round checkpoint: use a new output directory')
    folder.mkdir(parents=True, exist_ok=True)
    records=[]
    for name,url in URLS.items():
        path=folder/(name+'.gz')
        if path.exists():
            raw=gzip.decompress(path.read_bytes())
        else:
            chunks=[];size=0
            with requests.get(url,stream=True,timeout=(15,60)) as response:
                response.raise_for_status()
                for chunk in response.iter_content(1 << 16):
                    size+=len(chunk)
                    if size>5*1024*1024: raise ValueError('Directed source exceeds 5 MB limit')
                    chunks.append(chunk)
            raw=b''.join(chunks)
            path.write_bytes(gzip.compress(raw,mtime=0))
        records.append(dict(file=path.name,url=url,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                            compressed_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        print(name,len(raw),flush=True)
    (folder/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    return records


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE/'local_only/round2/sources')
    args=parser.parse_args();fetch(args.output)

if __name__=='__main__': main()
