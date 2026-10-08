#!/usr/bin/env python3
"""Independent old-engine comparator at actual 100k capital, without operational delay."""
import gzip,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.simulate_ir_100k import load,Portfolio,target_weights,dump,OUT
from scripts.audit_alerts_v12 import m,BASE,rights

def main():
    d=load();book=m.bridge.PriceBook(d['prices'],d['calendar']);events=[m.Event(**r) for r in json.loads((BASE/'manutencao_documental_v11_1/eventos_utilizados.json').read_text())];rows=[]
    for y in range(2020,2026):
        for rule in ['R00','R03','R16']:
            cap=100000.
            for yy in range(y,2026):
                p=Portfolio(d,yy,rule,'central','A',False)
                w=target_weights(p.selected(yy),rule,lambda t:p.sector(yy,t));start,end=d['windows'][str(yy)]
                _,res,_=rights.simulate(book,events,{},start,end,w,cap,d['rights']);cap=res['final_value']
            actual=Portfolio(d,y,rule,'central','A',False,same_close=True,log=False).run()['final_wealth']
            delta=actual-cap;rows.append(dict(formation=y,rule=rule,capital=100000,original_engine=cap,new_same_close=actual,difference=delta,status='PASS' if abs(delta)<1e-6 else 'FAIL'))
    dump('old_engine_parity_100k.csv',rows)
    print('old engine parity',len(rows),'max difference',max(abs(r['difference']) for r in rows),flush=True)
    if any(r['status']!='PASS' for r in rows):raise RuntimeError('Gross parity failed: inspect old_engine_parity_100k.csv')
if __name__=='__main__':main()
