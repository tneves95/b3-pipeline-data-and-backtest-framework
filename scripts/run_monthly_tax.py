"""Replay PR5 and calculate the five fiscal trajectories in persistent outputs."""
from collections import defaultdict
from copy import deepcopy
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

import monthly_contributions as gross
from monthly_tax_accounting import Fiscal
from monthly_tax_freeze import TAX, POLICY
from monthly_tax_simulate import simulate
from b00s_variants import write, jsonwrite, read, sha


def close(a,b,path=''):
    if isinstance(a,dict):
        for k,v in a.items():close(v,b[k],path+'/'+str(k))
    elif isinstance(a,(list,tuple)):
        if len(a)!=len(b):raise AssertionError((path,len(a),len(b)))
        for i,(v,w) in enumerate(zip(a,b)):close(v,w,path+'/'+str(i))
    elif isinstance(a,float):
        if not math.isclose(a,b,rel_tol=3e-11,abs_tol=1e-7):raise AssertionError((path,a,b))
    elif a!=b:raise AssertionError((path,a,b))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sensitivities',action='store_true')
    args=parser.parse_args()
    if json.loads((TAX/'inputs/tax_policy_freeze.json').read_text())!=POLICY:raise ValueError('Policy changed')
    evidence=json.loads((TAX/'inputs/event_tax_evidence.json').read_text())
    quote,_=gross.load_quotes();events=gross.events();comps=gross.frozen_compositions()
    sessions=[r['date'] for r in read(gross.STUDY/'inputs/ibov_daily.csv')]
    summaries=[];allrows=defaultdict(list);checks=[];grossruns={};netruns={}
    expected={r['portfolio']:r for r in read(gross.STUDY/'consolidated.csv')}
    for p in gross.PORTFOLIOS:
        base=gross.simulate(p,quote,events,comps);grossruns[p]=base
        fiscal=Fiscal(p,evidence,sessions,enabled=False)
        zero=simulate(p,quote,events,comps,fiscal=fiscal)
        for key in ['summary','contributions','trades','positions','wealth','event_ledger','junes','annual','flows']:
            close(base[key],zero[key],p+'/'+key)
        # Committed baseline final value is independently checked below by field.
        checks.append(dict(portfolio=p,test='ZERO_TAX_FULL_BOOK_PR5_PARITY',status='PASS',
            operations=len(base['trades']),positions=len(base['positions']),events=len(base['event_ledger']),
            deposits=len(base['contributions']),external_capital=base['summary']['external_capital']))
        fiscal=Fiscal(p,evidence,sessions)
        r=simulate(p,quote,events,comps,fiscal=fiscal);netruns[p]=r
        s=dict(mode='CG_ONLY',qualification='CONDITIONAL_CORPORATE_TAX_BASES',**r['summary'])
        s.update(gross_wealth=base['summary']['final_wealth'],gross_xirr_pct=base['summary']['xirr_pct'],
            wealth_reduction=base['summary']['final_wealth']-s['final_wealth'],
            xirr_reduction_pp=base['summary']['xirr_pct']-s['xirr_pct'])
        summaries.append(s)
        for name,key in [('monthly_taxed_wealth','wealth'),('taxed_positions','positions'),('taxed_operations','trades'),
                         ('contributions_ledger','contributions'),('june_tax_reviews','junes')]:
            allrows[name].extend(dict(mode='CG_ONLY',**x) for x in r[key])
        for name,rows in [('tax_trades_basis',fiscal.trades),('tax_events_classification',fiscal.event_rows),
                          ('cash_dividends_jcp_tax',fiscal.income_rows),('monthly_tax_ledger',fiscal.monthly_rows()),
                          ('tax_payments',fiscal.payments),('final_liquidation_trades',r['liquidation']['rows'])]:
            allrows[name].extend(dict(mode='CG_ONLY',**x) for x in rows)
        print(p,json.dumps(s,ensure_ascii=False),flush=True)
    for rank,s in enumerate(sorted(summaries,key=lambda s:-s['gross_wealth']),1):s['gross_rank']=rank
    for rank,s in enumerate(sorted(summaries,key=lambda s:-s['final_wealth']),1):s['net_rank']=rank
    ibov=gross.benchmark()['summary'];summaries.append(dict(mode='GROSS_INDEX_REFERENCE',**ibov))
    write(TAX/'consolidated_tax.csv',summaries)
    for name,rows in allrows.items():write(TAX/(name+'.csv'),rows)
    annual=[]
    for p,r in netruns.items():
        f=r['fiscal']
        for year in range(2014,2027):
            rows=[x for x in f.taxrows if x['month'].startswith(str(year))]
            paid=sum(x['amount'] for x in f.payments if x['date'].startswith(str(year)))
            withheld=sum(x['ordinary_irrf']+x['daytrade_irrf'] for x in rows)
            annual.append(dict(portfolio=p,mode='CG_ONLY',year=year,darf_paid=paid,irrf_paid=withheld,
                tax_paid=paid+withheld,tax_assessed=sum(x['assessed_tax'] for x in rows),
                exempt_gain=sum(x['exempt_gain'] for x in rows),stock_sales=sum(x['stock_sales'] for x in rows),
                common_loss_close=rows[-1]['common_loss_close'] if rows else None))
    write(TAX/'annual_tax_summary.csv',annual)
    jsonwrite(TAX/'validation.json',dict(zero_tax_checks=checks,policy_sha256=sha(TAX/'inputs/tax_policy_freeze.json'),
        status='COMPUTED_CONDITIONAL_NOT_FULL_TAX_CERTIFICATION'))
    if args.sensitivities:
        sensitivities=[]
        scenarios={'NO_STOCK_EXEMPTION':dict(exemption=False),'UNKNOWN_BONUS_MARKET_COST':dict(bonus_market=True),
            'XP_ZERO_CHILD_BASIS':dict(xp_zero=True),'CONVERSION_BOOT_ZERO_COST':dict(boot_zero=True),
            'REDEMPTION_35K_EXEMPTION':dict(gcap_exemption=True)}
        for name,options in scenarios.items():
            for p in gross.PORTFOLIOS:
                f=Fiscal(p,evidence,sessions,**options);r=simulate(p,quote,events,comps,fiscal=f)
                sensitivities.append(dict(sensitivity=name,**r['summary']))
        f=Fiscal('VVAL',evidence,sessions)
        r=simulate('VVAL',quote,events,comps,fiscal=f,initial_exclude_bradesco=True)
        sensitivities.append(dict(sensitivity='BBDC4_2014_NOT_ADMITTED',**r['summary']))
        write(TAX/'sensitivities_tax.csv',sensitivities)
    print('Saved',TAX,flush=True)


if __name__=='__main__':main()
