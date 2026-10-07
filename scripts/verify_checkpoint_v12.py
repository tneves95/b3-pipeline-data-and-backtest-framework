#!/usr/bin/env python3
"""Recompute historical regressions, optionally compare quotes to local B3 bytes."""
import argparse
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()))
from scripts.audit_alerts_v12 import BASE,INPUT,OUT,context,dump,m,rights
from scripts.audit_graham_v11_sources import cotahist_prices


def main(out,raw_dir=None):
    book,events,coverage,sels,evidence=context()
    checks=[]
    frozen={(int(r['start_year']),r['rule']):r for r in m.read_csv(BASE/'manutencao_documental_v11_1/graham_18_coortes.csv')}
    annual={int(r['year']):r for r in m.read_csv(BASE/'graham_corrigido_anuais_eventos.csv')}
    for y,(start,end) in m.bridge.WINDOWS.items():
        for rule in rights.RULES:
            weights=rights.weights_for(sels[y],rule)
            for label,stop,reference in [('v10_annual',end,float(annual[y][rule])),
                                         ('v11_1_maintain',m.END,float(frozen[y,rule]['maintain_return']))]:
                _,r,_=rights.simulate(book,events,coverage,start,stop,weights,10000,[])
                assert math.isclose(r['return'],reference,rel_tol=0,abs_tol=1e-9)
                checks.append(dict(year=y,rule=rule,reference=label,calculated=r['return'],expected=reference,
                                   difference=r['return']-reference,status='OK'))
    lb,le,_=m.bridge.load_legacy()
    legacy=m.bridge.legacy_parity(lb,le)
    assert all(r['status']=='OK' for r in legacy)
    dump(out,'regressao_v10_v11_1_36.csv',checks)
    dump(out,'regressao_v6_18.csv',legacy)
    if raw_dir:
        facts=json.loads((INPUT/'verified_facts.json').read_text())
        targets={('BBSE3',d) for a,b in m.bridge.WINDOWS.values() for d in (a,b)}
        targets.update((f['ticker'],f['ex_date']) for f in facts if f['ticker'] in ['BBSE3','GRND3','SLCE3','CPLE3']
                       and '2020-06-30'<f['ex_date']<=m.END)
        raw,manifest=cotahist_prices(raw_dir,targets)
        rows=[]
        for t,d in sorted(targets):
            r=raw[t,d]
            assert len(r)==1,(t,d,r)
            price=book.exact(t,d)
            assert math.isclose(price,r[0]['close'],rel_tol=0,abs_tol=1e-9)
            rows.append(dict(ticker=t,date=d,engine_close=price,**r[0],status='COINCIDE_COM_ARQUIVO_B3_LOCAL'))
        dump(out,'cotacoes_suplementares_ri_B3.csv',rows)
        (out/'cotahist_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print('Cotacoes locais:',len(rows),'(nao e coleta independente)')
    print('Regressoes v10/v11.1:',len(checks),'v6:',len(legacy))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT);p.add_argument('--raw-dir',type=Path)
    args=p.parse_args();main(args.out,args.raw_dir)
