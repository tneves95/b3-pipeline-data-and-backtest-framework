"""Causal replay bridge for the VVAL legacy versus PIT-reaudited June exits.

Use only frozen data; deliberately reinstate disputed legacy FAIL decisions
as counterfactuals, never as permissible financial reasons to sell.
"""
from __future__ import annotations
import csv
from itertools import combinations
import json
import math
from pathlib import Path

import monthly_contributions as original
from monthly_reaudit_simulate import simulate
from monthly_maintenance_reaudit import maintenance_evidence, guard_prior
from monthly_tax_accounting import Fiscal
from monthly_policy_corrected import FAIL_REASON

ROOT=original.ROOT
OLD=ROOT/'research/monthly_policy_corrected_2014_2026'
NEW=ROOT/'research/monthly_reaudited_2014_2026'
OUT=ROOT/'research/monthly_allocation_reaudited_2014_2026'
DISPUTED=[('TIET11',2016),('CPFE3',2020),('BRSR6',2021),('SBSP3',2024)]

def read_csv(path):
    with path.open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def write(path,rows):
    if not rows:raise ValueError('Missing rows')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def main():
    guard_prior()
    meta=original.identities()
    proof=maintenance_evidence()
    evidence=json.loads((ROOT/'research/monthly_tax_2014_2026/inputs/event_tax_evidence_stage2.json').read_text())
    quotes,_=original.load_quotes()
    evday=original.events()
    comps=original.frozen_compositions()
    sessions=[r['date'] for r in original.read(original.STUDY/'inputs/ibov_daily.csv')]
    old_row=next(r for r in read_csv(OLD/'consolidated_policy_corrected.csv') if r['portfolio']=='VVAL')
    new_row=next(r for r in read_csv(NEW/'consolidated_policy_corrected.csv') if r['portfolio']=='VVAL')
    cases={};summary=[];yearly=[];npos=len(DISPUTED)
    for mask in range(1<<npos):
        names=[f'{t}/{y}' for i,(t,y) in enumerate(DISPUTED) if mask & (1<<i)]
        ev=dict(proof)
        for i,(ticker,year) in enumerate(DISPUTED):
            if not (mask & (1<<i)):continue
            c=meta[ticker]['cnpj']
            key=('VVAL',year,c)
            ev[key]=dict(status='FAIL',reason=FAIL_REASON,
                source='COUNTERFACTUAL_LEGACY_UNSUPPORTED_EXIT',
                source_line=0,source_ticker=ticker,
                source_reason='NOT_ECONOMICALLY_CERTIFIED')
        fiscal=Fiscal('VVAL',evidence,sessions,enabled=False,income_mode='NONE')
        run=simulate('VVAL',quote=quotes,byday=evday,compositions=comps,
                     evidence=ev,fiscal=fiscal)
        s=run['summary']
        assert s['external_capital']==460000. and s['external_contributions']==144
        assert all(t['reason']==FAIL_REASON for t in run['trades'] if t['side']=='SELL')
        cases[mask]=float(s['final_wealth'])
        summary.append(dict(case_mask=mask,reintroduced_unsupported_exits=';'.join(names) or 'NONE',
            gross_final_wealth=s['final_wealth'],xirr_pct=s['xirr_pct'],
            sales=s['voluntary_sales'],delta_vs_reaudited=s['final_wealth']-float(new_row['final_wealth'])))
        for r in run['annual']:
            yearly.append(dict(case_mask=mask,year=r['closing_year'],date=r['date'],
                nav=r['nav'],xirr_final=s['xirr_pct']))
        print('VVAL BRIDGE',mask,names,
              'wealth',round(s['final_wealth'],2),'XIRR',round(s['xirr_pct'],6),
              'sales',s['voluntary_sales'],flush=True)

    assert math.isclose(cases[0],float(new_row['final_wealth']),abs_tol=1e-6)
    shapley=[]
    for i,(ticker,year) in enumerate(DISPUTED):
        effect=0.
        for m in range(1<<npos):
            if m & (1<<i):continue
            n=m.bit_count()
            w=math.factorial(n)*math.factorial(npos-n-1)/math.factorial(npos)
            effect+=w*(cases[m | (1<<i)]-cases[m])
        shapley.append(dict(sale=ticker,original_sale_year=year,
             modeled_legacy_exit_advantage_R=effect,
             reason='Counterfactual Shapley marginal over 16 replays; NOT proof of proper exit'))
    assert math.isclose(sum(x['modeled_legacy_exit_advantage_R'] for x in shapley),
                        cases[(1<<npos)-1]-cases[0],abs_tol=1e-5)
    bridge=dict(old_pr6_gross_wealth=float(old_row['final_wealth']),
        new_pr6_gross_wealth=float(new_row['final_wealth']),
        legacy_minus_reaudited_R=float(old_row['final_wealth'])-float(new_row['final_wealth']),
        all_four_forced_old_gross_wealth=cases[(1<<npos)-1],
        all_four_minus_reaudited=cases[(1<<npos)-1]-cases[0],
        historical_legacy_minus_four_forced= float(old_row['final_wealth'])-cases[(1<<npos)-1],
        shapley_sum=sum(x['modeled_legacy_exit_advantage_R'] for x in shapley),
        method='Shapley valuation of four challenged sale decisions under the reaudited engine, plus bridge residual',
        limitations='Forced FAIL decisions were DOCUMENTALLY INVALID; this is an explanation of historical backtest effects, not a recommended trade policy; nonlinear interactions including annual admission and purchases are shared across decisions; original legacy may not be fully replicated due to other review differences')
    OUT.mkdir(parents=True,exist_ok=True)
    write(OUT/'vval_forced_sales_counterfactuals.csv',summary)
    write(OUT/'vval_forced_sales_annual.csv',yearly)
    write(OUT/'vval_shapley_attribution.csv',shapley)
    (OUT/'vval_legacy_to_reaudited_bridge.json').write_text(
        json.dumps(bridge,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('VVAL BRIDGE FINAL',json.dumps(bridge,ensure_ascii=False),flush=True)
    print('VVAL SHAPLEY',json.dumps(shapley,ensure_ascii=False),flush=True)
    guard_prior()

if __name__=='__main__':
    main()
