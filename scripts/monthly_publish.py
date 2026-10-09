"""Write PR #5 CSV/XLSX only; older studies are immutable inputs."""
from __future__ import annotations
from datetime import date
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import statistics

from b00s_variants import read,write,jsonwrite,sha
from stage1_pit import ROOT
from monthly_inputs import STUDY,START,END,BASELINE
from monthly_contributions import simulate,benchmark,load_quotes,events,frozen_compositions,PORTFOLIOS


def verify_protected():
    manifest=json.loads((STUDY/'inputs/protected_pr3_pr4.json').read_text())
    for r in manifest['files']:
        with (ROOT/r['path']).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=r['sha256']:raise ValueError(('Protected artifact modified',r['path']))
    return len(manifest['files'])


def monthly_returns(result):
    wealth=result['wealth'];portfolio=result['summary']['portfolio']
    previous=next(w['nav'] for w in wealth if w['date']==START)
    cumulative=1.;rows=[];points={r['date']:float(r['close']) for r in read(STUDY/'inputs/ibov_daily.csv')}
    prior_date=START
    for r in result['contributions']:
        month=r['date'][:7]
        last=next(w for w in wealth if w['date'].startswith(month) and w['phase']=='MONTH_END')
        nav=last['nav']
        if portfolio=='IBOV':ret=points[last['date']]/points[prior_date]-1
        else:
            ret=(r['nav_before']/previous)*(nav/r['nav_after'])-1 if all(v is not None for v in [r['nav_before'],r['nav_after'],nav,previous]) else None
        cumulative=cumulative*(1+ret) if ret is not None and cumulative is not None else None
        rows.append(dict(portfolio=portfolio,month=month,date=last['date'],nav=nav,external_capital=last['external_capital'],
            monthly_twr_pct=100*ret if ret is not None else None,cumulative_twr_pct=100*(cumulative-1) if cumulative is not None else None,
            status='EXACT_FLOW_ADJUSTED_TWR' if ret is not None else 'ND_MISSING_EXACT_MARK'))
        previous=nav;prior_date=last['date']
    return rows


def risk_metrics(result):
    monthly=monthly_returns(result)
    returns=[r['monthly_twr_pct']/100 for r in monthly if r['monthly_twr_pct'] is not None]
    all_valid=len(returns)==len(monthly)
    vol=statistics.stdev(returns)*math.sqrt(12)*100 if len(returns)>1 else None
    peak=1.;lowest=0.;index=1.
    if all_valid:
        for r in returns:
            index*=1+r;peak=max(peak,index);lowest=min(lowest,index/peak-1)
    return dict(monthly_volatility_annualized_pct=vol,volatility_valid_months=len(returns),
        volatility_status='ALL_144_MONTHS' if all_valid and len(monthly)==144 else 'AVAILABLE_MONTHS_ONLY',
        maximum_drawdown_pct=100*lowest if all_valid else None,
        drawdown_status='MONTH_END_TWR_INDEX' if all_valid else 'ND_CUMULATIVE_TWR_GAP'),monthly


def union_write(path,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    write(path,[dict.fromkeys(fields,'')|r for r in rows])


def export(results,destination):
    destination.mkdir(parents=True,exist_ok=True)
    ibov=next(r['summary']['final_wealth'] for r in results if r['summary']['portfolio']=='IBOV')
    summaries=[];monthly=[]
    for r in results:
        risk,m=risk_metrics(r);monthly.extend(m)
        summary=r['summary']|risk|dict(wealth_difference_vs_ibov=r['summary']['final_wealth']-ibov,
            wealth_ratio_vs_ibov=r['summary']['final_wealth']/ibov,
            external_contributions_total=r['summary']['external_capital']-100000,
            external_cash_final=0. if r['summary']['cash']==0 else None,
            external_contributions_invested=r['summary']['external_capital']-100000 if r['summary']['cash']==0 else None)
        summaries.append(summary)
    write(destination/'consolidated.csv',summaries)
    names={'contributions':'contributions_ledger','trades':'operations','positions':'monthly_positions',
        'wealth':'monthly_wealth','event_ledger':'internal_events_ledger','junes':'june_reviews','annual':'annual_and_cumulative_returns'}
    for key,name in names.items():
        selected=[r for r in results if key!='contributions' or r['summary']['portfolio']!='IBOV']
        union_write(destination/f'{name}.csv',[row for r in selected for row in r[key]])
    union_write(destination/'benchmark_contributions_ledger.csv',[row for r in results if r['summary']['portfolio']=='IBOV' for row in r['contributions']])
    write(destination/'monthly_returns.csv',monthly)
    flows=[dict(portfolio=r['summary']['portfolio'],date=d,investor_cash_flow=v,
        flow_type='FINAL_NAV' if i==len(r['flows'])-1 else 'INITIAL_CAPITAL' if i==0 else 'MONTHLY_DEPOSIT')
        for r in results for i,(d,v) in enumerate(r['flows'])]
    write(destination/'investor_cash_flows.csv',flows)
    return summaries


def run_batch(end,portfolios,destination):
    q,provenance=load_quotes();byday=events();compositions=frozen_compositions();results=[]
    for p in portfolios:
        result=simulate(p,q,byday,compositions,end=end)
        for row in result['positions']+result['trades']:
            source=provenance.get((row['ticker'],row['date']),{})
            row.update(observed_ticker=source.get('ticker',''),isin=source.get('isin_code',''),
                quote_source=source.get('source',''),quotation_factor=source.get('quotation_factor',''),
                zip_sha256=source.get('zip_sha256',''),record_sha256=source.get('record_sha256',''),quote_line=source.get('line',''))
        results.append(result)
        print(json.dumps(result['summary'],ensure_ascii=False),flush=True)
    bench=benchmark(end=end)
    bench_sources={r['date']:r for r in read(STUDY/'inputs/ibov_daily.csv')}
    for row in bench['positions']+bench['trades']:
        source=bench_sources[row['date']]
        row.update(observed_ticker='IBOV',isin='',quote_source=source['source'],quotation_factor=1,
            zip_sha256='',record_sha256=source['source_sha256'],quote_line='')
    results.append(bench);summaries=export(results,destination)
    return results,summaries


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--end',default=END);p.add_argument('--portfolios',nargs='+',default=list(PORTFOLIOS));p.add_argument('--output-dir',type=Path,default=STUDY)
    args=p.parse_args();run_batch(args.end,args.portfolios,args.output_dir)
