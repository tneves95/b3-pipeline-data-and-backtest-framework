"""Replay PR5 and calculate the five fiscal trajectories in persistent outputs."""
from collections import defaultdict
from copy import deepcopy
import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

import monthly_contributions as gross
from monthly_tax_accounting import Fiscal
from monthly_tax_freeze import TAX, POLICY
from monthly_tax_simulate import simulate
from b00s_variants import jsonwrite, read, sha


def write(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys or ['status']);writer.writeheader();writer.writerows(rows)


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
    evidence=json.loads((TAX/'inputs/event_tax_evidence_stage2.json').read_text())
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
        for field in ['final_wealth','xirr_pct','external_capital']:
            close(base['summary'][field],float(expected[p][field]),p+'/committed_PR5/'+field)
        checks.append(dict(portfolio=p,test='ZERO_TAX_FULL_BOOK_PR5_PARITY',status='PASS',
            operations=len(base['trades']),positions=len(base['positions']),events=len(base['event_ledger']),
            deposits=len(base['contributions']),external_capital=base['summary']['external_capital']))
        for mode,income_mode in [('CG_ONLY','NONE'),('CG_PLUS_JCP_CERTIFIED_PARTIAL','CERTIFIED_PARTIAL')]:
            fiscal=Fiscal(p,evidence,sessions,income_mode=income_mode)
            r=simulate(p,quote,events,comps,fiscal=fiscal);netruns[mode,p]=r
            s=dict(mode=mode,qualification='CONDITIONAL_CORPORATE_BASES_AND_INCOME_TIMING' if income_mode!='NONE' else 'CONDITIONAL_CORPORATE_TAX_BASES',**r['summary'])
            s.update(gross_wealth=base['summary']['final_wealth'],gross_xirr_pct=base['summary']['xirr_pct'],
                wealth_reduction=base['summary']['final_wealth']-s['final_wealth'],
                xirr_reduction_pp=base['summary']['xirr_pct']-s['xirr_pct'])
            s.update(wealth_reduction_pct=100*s['wealth_reduction']/s['gross_wealth'],
                full_historical_certified_wealth=None,full_historical_status='ND_UNRESOLVED_AMOUNTS_DATES_AND_CORPORATE_TAX_BASES',
                gross_issuer_hhi=float(expected[p]['issuer_hhi']),gross_maximum_issuer_weight=float(expected[p]['maximum_issuer_weight']))
            issuer_values=defaultdict(float);sector_values=defaultdict(float);metadata=gross.identities()
            for c,u in r['book'].items():
                for t,q in u.items():
                    issuer='XP_SPINOFF' if t=='XPBR31' else metadata.get(t,{}).get('cnpj',c)
                    issuer_values[issuer]+=q*quote[t,gross.END]
                    sector_values[metadata.get(t,{}).get('sector','Unclassified')]+=q*quote[t,gross.END]
            s.update(issuer_hhi=sum((v/s['final_wealth'])**2 for v in issuer_values.values()),
                maximum_issuer_weight=max(issuer_values.values())/s['final_wealth'],
                sector_hhi=sum((v/s['final_wealth'])**2 for v in sector_values.values()),economic_issuers=len(issuer_values))
            summaries.append(s)
            monthly_rows=fiscal.monthly_rows()
            for name,key in [('monthly_taxed_wealth','wealth'),('taxed_positions','positions'),('taxed_operations','trades'),
                             ('contributions_ledger','contributions'),('june_tax_reviews','junes')]:
                allrows[name].extend(dict(mode=mode,**x) for x in r[key])
            for c,u in r['book'].items():
                for t,q in u.items():
                    value=q*quote[t,gross.END];cost=fiscal.basis[t]
                    allrows['final_tax_positions'].append(dict(mode=mode,portfolio=p,date=gross.END,issuer=c,ticker=t,
                        quantity=q,total_acquisition_cost=cost,average_cost=cost/q if q else None,
                        close=quote[t,gross.END],market_value=value,unrealized_gain=value-cost,
                        asset_tax_type='BDR' if t=='XPBR31' else 'STOCK',status='CONDITIONAL_CORPORATE_BASES'))
            for name,rows in [('tax_trades_basis',fiscal.trades),('tax_events_classification',fiscal.event_rows),
                          ('cash_dividends_jcp_tax',fiscal.income_rows),('monthly_tax_ledger',monthly_rows),
                          ('tax_payments',fiscal.payments),('final_liquidation_trades',r['liquidation']['rows']),
                          ('final_liquidation_monthly_tax',[x for x in r['liquidation']['monthly_tax'] if x['month']=='2026-06'])]:
                allrows[name].extend(dict(mode=mode,**x) for x in rows)
            print(mode,p,round(s['final_wealth'],2),round(s['xirr_pct'],6),round(s['tax_paid'],2),round(s['income_withheld'],2),flush=True)
    for mode in sorted({s['mode'] for s in summaries}):
        group=[s for s in summaries if s['mode']==mode]
        for rank,s in enumerate(sorted(group,key=lambda s:-s['gross_wealth']),1):s['gross_rank']=rank
        for rank,s in enumerate(sorted(group,key=lambda s:-s['final_wealth']),1):s['net_rank']=rank
        for rank,s in enumerate(sorted(group,key=lambda s:-s['liquidation_wealth']),1):s['liquidation_rank']=rank
    ibov=gross.benchmark()['summary'];summaries.append(dict(mode='GROSS_INDEX_REFERENCE',**ibov))
    write(TAX/'consolidated_tax.csv',summaries)
    for name,rows in allrows.items():write(TAX/(name+'.csv'),rows)
    annual=[]
    for (mode,p),r in netruns.items():
        f=r['fiscal']
        for year in range(2014,2027):
            rows=[x for x in f.taxrows if x['month'].startswith(str(year))]
            paid=sum(x['amount'] for x in f.payments if x['date'].startswith(str(year)))
            withheld=sum(x['ordinary_irrf']+x['daytrade_irrf'] for x in rows)
            annual.append(dict(portfolio=p,mode=mode,year=year,darf_paid=paid,irrf_paid=withheld,
                income_withheld=sum(x['withheld_additional'] for x in f.income_rows if x['date'].startswith(str(year))),
                tax_paid=paid+withheld,tax_assessed=sum(x['assessed_tax'] for x in rows),
                exempt_gain=sum(x['exempt_gain'] for x in rows),stock_sales=sum(x['stock_sales'] for x in rows),
                common_loss_close=rows[-1]['common_loss_close'] if rows else None))
    write(TAX/'annual_tax_summary.csv',annual)
    income_coverage=[];dividend_control=[]
    for (mode,p),r in netruns.items():
        f=r['fiscal'];envelopes=defaultdict(float);dividends=defaultdict(float)
        kinds=defaultdict(lambda:dict(events=0,source_amount=0.,additional_withholding=0.))
        for inc in f.income_rows:
            key=inc['distribution_type'],inc['amount_basis'],inc['rate_status']
            k=kinds[key];k['events']+=1;k['source_amount']+=inc['source_amount'];k['additional_withholding']+=inc['withheld_additional']
            pd=inc['source_payment_dates'].split(';')[0] or inc['date']
            if pd[:4]=='2026':
                # Also show the envelope including every distribution, so a
                # missing cash/JCP type is not silently assumed exempt dividend.
                group=inc['issuer'],pd[:7];envelopes[group]+=inc['source_amount']
                if inc['distribution_type']=='DIVIDEND':dividends[group]+=inc['source_amount']
        for (typ,basis,rate),values in sorted(kinds.items()):
            income_coverage.append(dict(mode=mode,portfolio=p,distribution_type=typ,amount_basis=basis,rate_status=rate,**values))
        for (issuer,month),amount in sorted(envelopes.items()):
            dividend_control.append(dict(mode=mode,portfolio=p,issuer=issuer,month=month,
                known_dividends=dividends[issuer,month],all_distributions_cash_envelope=amount,
                threshold=50000,threshold_crossed=dividends[issuer,month]>50000,
                envelope_crossed=amount>50000,within_horizon=month<='2026-06',
                date_basis='Known payment date; otherwise ex-date proxy; unsplit multiple tranches grouped on first listed payment',
                transitional_exception_required=dividends[issuer,month]>50000))
    write(TAX/'income_coverage.csv',income_coverage)
    write(TAX/'dividend_monthly_issuer_2026.csv',dividend_control)
    jsonwrite(TAX/'validation.json',dict(zero_tax_checks=checks,policy_sha256=sha(TAX/'inputs/tax_policy_freeze.json'),
        status='COMPUTED_CONDITIONAL_NOT_FULL_TAX_CERTIFICATION'))
    if args.sensitivities:
        sensitivities=[]
        scenarios={'NO_STOCK_EXEMPTION':dict(exemption=False),'UNKNOWN_BONUS_MARKET_COST':dict(bonus_market=True),
            'XP_ZERO_CHILD_BASIS':dict(xp_zero=True),'CONVERSION_BOOT_ZERO_COST':dict(boot_zero=True),
            'REDEMPTION_35K_EXEMPTION':dict(gcap_exemption=True),
            'JCP_UNKNOWN_GROSS_EX_DATE':dict(income_mode='UNKNOWN_GROSS'),
            'JCP_UNKNOWN_GROSS_PAYMENT_DATE':dict(income_mode='UNKNOWN_GROSS_PAYMENT'),
            'UNCLASSIFIED_DISTRIBUTION_AS_JCP':dict(income_mode='UNKNOWN_AS_JCP')}
        for name,options in scenarios.items():
            for p in gross.PORTFOLIOS:
                f=Fiscal(p,evidence,sessions,**options);r=simulate(p,quote,events,comps,fiscal=f)
                sensitivities.append(dict(sensitivity=name,**r['summary']))
                print('SENSITIVITY',name,p,round(r['summary']['final_wealth'],2),flush=True)
        f=Fiscal('VVAL',evidence,sessions)
        r=simulate('VVAL',quote,events,comps,fiscal=f,initial_exclude_bradesco=True)
        sensitivities.append(dict(sensitivity='BBDC4_2014_NOT_ADMITTED',**r['summary']))
        for name in {r['sensitivity'] for r in sensitivities}:
            group=[r for r in sensitivities if r['sensitivity']==name]
            for rank,r in enumerate(sorted(group,key=lambda r:-r['final_wealth']),1):r['net_rank']=rank
        write(TAX/'sensitivities_tax.csv',sensitivities)
    print('Saved',TAX,flush=True)


if __name__=='__main__':main()
