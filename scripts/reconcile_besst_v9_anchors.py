#!/usr/bin/env python3
"""Reconcile cash/stock reporting to the SAME v6 anchors used by Barsi v9.

Leaves every v9 return, selection and packaged file unchanged. Unanchored rows
remain material approximations. Requires audit_besst_v9_package.py first.
"""
import glob
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0,str(Path.cwd()))
from scripts.graham_corrected_maintenance_v11 import read_csv,write_csv


def main():
    runtime=Path('.cache/besst_v9_reproduction/runtime')
    v8=runtime/'Barsi_Graham_Retomada_v8'
    cases=v8/'herdado_v7/herdado_v6/checkpoints/casos_v6'
    results=runtime/'results_v9'
    out=Path('graham_v6_event_results/auditoria_besst_v9')
    quotes={}
    for filename in glob.glob(str(v8/'**/quotes_202*.csv'),recursive=True):
        for r in read_csv(Path(filename)):
            try:quotes[(r['ticker'],r['date'])]=float(r['price'])
            except (ValueError,KeyError):continue
    dates={2020:'2020-06-30',2021:'2021-06-30',2022:'2022-06-30',2023:'2023-06-30',2024:'2024-06-28',2025:'2025-06-30'}
    rows=[]; fixed=0
    for r in read_csv(results/'besst_maintenance_holdings.csv'):
        factor=float(r['factor']); cash=float(r['final_cash']);stock=float(r['final_stock']);weight=float(r['weight'])
        anchor_path='';anchor_sha='';holdings={}
        if '[EXACT_V6_ANCHOR]' in r['final_state']:
            case=cases/f"{r['ticker']}_{dates[int(r['start_year'])]}_2026-06-30.json"
            state=json.loads(case.read_text())['state']
            assert state['last_date']=='2026-06-30'
            initial=float(state['initial_value'])
            value=next(n['nav'] for n in reversed(state['nav']) if n['date']=='2026-06-30' and n['nav'] is not None)
            assert math.isclose(value/initial,factor,rel_tol=1e-9,abs_tol=1e-9)
            cash=state['cash']/initial;stock=value/initial-cash
            holdings={t:q/initial for t,q in state['holdings'].items()}
            anchor_path=str(case.relative_to(runtime));anchor_sha=hashlib.sha256(case.read_bytes()).hexdigest()
            fixed+=abs(factor-float(r['final_cash'])-float(r['final_stock']))>1e-9
            status='PATRIMONIO_DO_CHECKPOINT_V6'
        else:
            if r['final_state']!='CASH':
                holdings={r['final_state']:stock/quotes[(r['final_state'],'2026-06-30')]}
            status='PATRIMONIO_MODELO_MATERIAL_V9'
        assert math.isclose(cash+stock,factor,rel_tol=1e-9,abs_tol=1e-9)
        assert math.isclose(sum(q*quotes[(t,'2026-06-30')] for t,q in holdings.items()),stock,rel_tol=1e-9,abs_tol=1e-9)
        rows.append(dict(start_year=r['start_year'],strategy=r['portfolio'],scenario=r['scenario'],ticker=r['ticker'],
            initial_weight=weight,return_unchanged=r['return'],contribution=weight*float(r['return']),
            original_cash_per_unit=r['final_cash'],original_stock_per_unit=r['final_stock'],
            reconciled_cash_per_unit=cash,reconciled_stock_per_unit=stock,
            allocated_cash_10000=10000*weight*cash,allocated_stock_10000=10000*weight*stock,
            allocated_quantities_10000=json.dumps({t:10000*weight*q for t,q in holdings.items()},sort_keys=True),
            anchor_file=anchor_path,anchor_sha256=anchor_sha,status=status))
    checks=[]
    for r in read_csv(results/'besst_maintenance.csv'):
        ps=[p for p in rows if p['start_year']==r['start_year'] and p['strategy']==r['portfolio'] and p['scenario']==r['scenario']]
        total=sum(p['allocated_cash_10000']+p['allocated_stock_10000'] for p in ps)
        target=10000*(1+float(r['return']))
        assert math.isclose(total,target,rel_tol=1e-9,abs_tol=1e-8)
        checks.append(dict(start_year=r['start_year'],strategy=r['portfolio'],scenario=r['scenario'],
                           reconciled_wealth=total,reference_wealth=target,delta=total-target,status='OK'))
    write_csv(out/'patrimonio_posicoes_conciliado.csv',rows,list(rows[0]))
    write_csv(out/'patrimonio_48_carteiras_conciliado.csv',checks,list(checks[0]))
    summary=dict(positions=len(rows),portfolios=len(checks),reporting_discrepancies_fixed=fixed,
                 return_changes=0,selection_changes=0,remaining_arithmetic_mismatches=0,certified=False,
                 limitation='Reuses inherited v6 checkpoint; no independent documentary certification. Other v9 rows remain material approximations.')
    (out/'manifesto_patrimonio_conciliado.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary))


if __name__=='__main__':main()
