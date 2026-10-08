#!/usr/bin/env python3
"""Gross index factors for established selections; no operational balances."""
from __future__ import annotations
import argparse
from bisect import bisect_right
import csv
import hashlib
import json
import math
from pathlib import Path
import sqlite3

from stage1_pit import ROOT,OUT,DATES,gzread,gzwrite,dump

CORRECTIONS=[dict(ticker='CMIG3',record_date='2014-12-26',kind='JCP',amount=.182789068,
    source='https://api.mziq.com/mzfilemanager/v2/d/716a131f-9624-452c-9088-0cd6983c1349/a2eb9f5f-37e1-8913-c1eb-c4281b5e23b2?origin=2',
    reason='Aviso: duas parcelas de 50%. PK do SQLite preservou somente .091394534.')]

def gross_factor(prices,events,start,end):
    """Exact closes; sum gross distributions, multiply share entitlements once.

    A distribution on the old entitlement and a split on the same ex-date
    have adjustment F + D/P_ex, not F*(1+D/P_ex).
    """
    if start not in prices or end not in prices:raise ValueError('Missing endpoint quote')
    if any(p<=0 or not math.isfinite(p) for p in prices.values()):raise ValueError('Invalid nominal quote')
    seen=set();by_date={}
    for e in events:
        if not start<e['ex_date']<=end:continue
        if e['id'] in seen:raise ValueError('Duplicate economic event')
        seen.add(e['id']);day=e['ex_date']
        if day not in prices:raise ValueError('Missing exact ex-date close')
        a=by_date.setdefault(day,dict(multiplier=1.,distribution=0.))
        if e['kind']=='DISTRIBUTION':a['distribution']+=e['amount']
        elif e['kind']=='SHARES':a['multiplier']*=e['factor']
        else:raise ValueError('Unsupported economic event')
    factor=prices[end]/prices[start]
    for day,e in sorted(by_date.items()):factor*=e['multiplier']+e['distribution']/prices[day]
    return factor

def freeze(root,years):
    market=gzread(OUT/'cache/market.json.gz')
    selected=list(csv.DictReader((OUT/'selected.csv').open()))
    identity={(int(r['year']),r['ticker']):r for r in csv.DictReader((OUT/'identity_sector.csv').open())}
    c=sqlite3.connect((root/'b3_market_data.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    c.execute('PRAGMA query_only=ON');c.row_factory=sqlite3.Row
    calendar=[r[0] for r in c.execute("SELECT DISTINCT date FROM prices WHERE date BETWEEN '2014-06-30' AND '2016-07-05' ORDER BY date")]
    output=[]
    for y in years:
        for r in [r for r in selected if int(r['year'])==y and r['strategy']=='R03']:
            t=r['ticker'];start,end=DATES[y],DATES[y+1]
            prices=[dict(p) for p in c.execute('SELECT date,close,isin_code FROM prices WHERE ticker=? AND date BETWEEN ? AND ? ORDER BY date',(t,start,end))]
            isins={p['isin_code'] for p in prices}
            # Same issuer/class histories can be filed under the successor ISIN.
            isins|={p['isin_code'] for p in market['isins'] if p['cnpj']==r['cnpj'] and p['share_class']=='ON'}
            events=[]
            for e in market['actions']:
                if e['isin_code'] not in isins or not start<=e['event_date']<end:continue
                j=bisect_right(calendar,e['event_date'])
                if j==len(calendar):raise ValueError('Calendar missing next session')
                ex=calendar[j]
                if e['event_type'] not in ['CASH_DIVIDEND','JCP']:
                    raise ValueError(('Structural event requires specific proof',t,e))
                events.append(dict(id=f"B3_{e['isin_code']}_{e['event_date']}_{e['event_type']}",ex_date=ex,
                    record_date=e['event_date'],kind='DISTRIBUTION',amount=e['value'],source='SQLite corporate_actions; B3',isin=e['isin_code']))
            for fix in CORRECTIONS:
                if fix['ticker']!=t or not start<=fix['record_date']<end:continue
                old=[e for e in events if e['record_date']==fix['record_date']]
                if len(old)!=1:raise ValueError(('Correction must replace one existing event',fix,old))
                old[0].update(amount=fix['amount'],source=fix['source'],correction=fix['reason'])
            # No detected split may silently be ignored in these segments.
            for isin in isins:
                gaps=list(c.execute('SELECT * FROM detected_splits WHERE isin_code=? AND ex_date>? AND ex_date<=?',(isin,start,end)))
                if gaps:raise ValueError(('Unreviewed split',t,[dict(x) for x in gaps]))
            output.append(dict(year=y,ticker=t,cnpj=r['cnpj'],start=start,end=end,prices=prices,events=events,
                observed_isins=sorted({p['isin_code'] for p in prices}),event_isins=sorted(isins),
                identity_source=identity[y,t]['identity_source']))
    c.close();gzwrite(OUT/'cache/established_segments.json.gz',output)

def run():
    cases=gzread(OUT/'cache/established_segments.json.gz');positions=[];rows=[]
    annual=list(csv.DictReader((ROOT/'research/returns_2014_2026_results/annual_returns_pct.csv').open()))
    screen=list(csv.DictReader((OUT/'screening.csv').open()))
    for y in sorted({r['year'] for r in cases}):
        unknown=[r for r in screen if int(r['year'])==y and r['strategy']=='R03' and r['status']=='INDETERMINATE']
        if unknown:raise ValueError(('Selection still indeterminate',y,unknown))
        group=[r for r in cases if r['year']==y];w=1/len(group)
        passed={r['ticker'] for r in screen if int(r['year'])==y and r['strategy']=='R03' and r['status']=='PASS'}
        assert {r['ticker'] for r in group}==passed
        for r in group:
            factor=gross_factor({p['date']:p['close'] for p in r['prices']},r['events'],r['start'],r['end'])
            positions.append(dict(year=y,ticker=r['ticker'],weight=w,return_pct=100*(factor-1),factor=factor,
                contribution_pp=100*w*(factor-1),events=len(r['events']),source='cache/established_segments.json.gz'))
        ret=math.fsum(r['contribution_pp'] for r in positions if r['year']==y)
        ibov=float(annual[y-2014]['IBOV'])
        rows.append(dict(year=y,portfolio='R03 B2',start=DATES[y],end=DATES[y+1],return_pct=ret,
            IBOV_pct=ibov,excess_pp=ret-ibov,selection='ESTABLISHED_IN_SCREENED_ON_UNIVERSE',
            return_status='GROSS_NOMINAL_B3_WITH_DIRECTED_CORRECTION'))
    dump('established_segment_positions.csv',positions);dump('established_segments_pct.csv',rows)
    for r in rows:print(r)

def verify_quotes(root):
    from audit_graham_v11_sources import cotahist_prices
    cases=gzread(OUT/'cache/established_segments.json.gz');targets=set();expected={}
    for r in cases:
        dates={r['start'],r['end']}|{e['ex_date'] for e in r['events']}
        for p in r['prices']:
            if p['date'] in dates:
                key=(r['ticker'],p['date']);targets.add(key);expected[key]=p['close']
    raw,manifest=cotahist_prices(root/'data/raw',targets);rows=[]
    for key in sorted(targets):
        assert len(raw[key])==1,(key,raw[key])
        r=raw[key][0]
        assert math.isclose(r['close'],expected[key],abs_tol=1e-12),(key,r,expected[key])
        rows.append(dict(ticker=key[0],date=key[1],sqlite_close=expected[key],**r,status='MATCH'))
    dump('segment_quote_validation.csv',rows)
    (OUT/'segment_quote_sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Validated exact quotes',len(rows))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');p.add_argument('--verify-quotes',action='store_true');p.add_argument('--data-root',type=Path,default=ROOT.parent)
    a=p.parse_args()
    if a.freeze:freeze(a.data_root,[2014,2015])
    if a.verify_quotes:verify_quotes(a.data_root)
    run()
