"""Monetary PR #5 simulation. Frozen eligibility, equal issuer targets, no tax.

External cash flows and total-return events are distinct. All voluntary trades
use the exact close; corporate descendants retain their parent's lineage.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date
from pathlib import Path
import argparse
import csv
import json
import math
import statistics

from stage1_pit import ROOT, OUT, DATES, gzread
from stage1_resume import canonical, event_day
from b00s_variants import read, write, jsonwrite, sha, market, identities
from monthly_inputs import STUDY, START, END

PORTFOLIOS=('V0','BH padrão','BESST-10 BH','V10','VVAL')


def security(t):
    return canonical({'MOTV3':'CCRO3'}.get(t,t))


def load_quotes():
    quote={};provenance={}
    for p in sorted((STUDY/'inputs').glob('quotes_*.json.gz')):
        d=gzread(p)
        for r in d['quotes']:
            k=security(r['ticker']),r['date']
            if k in quote and quote[k]!=r['close']:raise ValueError(('Overlapping quote',k))
            quote[k]=r['close'];provenance[k]=dict(r,source=d['source']['file'],zip_sha256=d['source']['sha256'])
    accepted,_=market()
    differences=[]
    for k,v in accepted.items():
        if k in quote and not math.isclose(v,quote[k],rel_tol=1e-12):differences.append((k,v,quote[k]))
    if differences:raise ValueError(('Frozen quotation mismatch',differences[:10]))
    return quote,provenance


def events():
    """Keep the accepted BH event overrides, with no second entitlement."""
    _,byday=market()
    inherited=[e for ds in byday.values() for e in ds]
    bh=gzread(OUT/'cache/bh_owned_events.json.gz')
    bh_names={e['ticker'] for e in bh}
    all_events=[e for e in inherited if e['ticker'] not in bh_names]+bh
    # BBSE was not admitted in B00S before 2018, but the accepted continuation
    # event cache still includes its original 2014–15 distributions.
    known={e['id'] for e in all_events}
    for e in gzread(OUT/'cache/continuation_events.json.gz'):
        if e['ticker']=='BBSE3' and e['ex_date']<=DATES[2015] and e['id'] not in known:
            all_events.append(e);known.add(e['id'])
    result=defaultdict(list)
    for e in all_events:
        if START<e['ex_date']<=END:result[e['ex_date']].append(e)
    ids=[e['id'] for es in result.values() for e in es]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate event')
    return result


def frozen_compositions():
    metadata=identities(); h=read(ROOT/'research/b00s_four_variants_2014_2026/results/holdings_by_june.csv')
    result=defaultdict(dict)
    for r in h:
        if r['variant'] not in ['V0','V10','VVAL'] or r['row_type']!='HOLDING' or r['ticker']=='XPBR31':continue
        t=r['ticker'];c=metadata[t]['cnpj'];key=r['variant'],int(r['year'])
        if c in result[key]:raise ValueError(('Duplicate economic issuer',key,t))
        result[key][c]=t
    initial=read(OUT/'bh_selection_2014.csv')
    standard={r['cnpj']:r['ticker'] for r in initial}
    besst={r['cnpj']:r['ticker'] for r in read(STUDY/'besst10_bh_selection_2014.csv')}
    for year in range(2014,2026):result['BH padrão',year]=standard.copy();result['BESST-10 BH',year]=besst.copy()
    return result


def waterfill(values, cash, buyers):
    """Spend available cash proportionally to positive monetary deficits."""
    if cash<0:raise ValueError('Negative cash')
    active=sorted(values)
    if not active or not cash:return {},cash
    nav=math.fsum(values.values())+cash;target=nav/len(active)
    deficits={c:max(0,target-values[c]) for c in active if c in buyers}
    deficits={c:d for c,d in deficits.items() if d>0}
    total=math.fsum(deficits.values());spend=min(cash,total)
    if not total:return {},cash
    allocations={c:spend*d/total for c,d in deficits.items()}
    last=sorted(allocations)[-1];allocations[last]=spend-math.fsum(v for c,v in allocations.items() if c!=last)
    return allocations,max(0,cash-spend)


def june_targets(values, wanted, trailing_returns, changed, protect=True):
    """June-only target changes. Return monetary targets and protected issuers."""
    nav=math.fsum(values.values());n=len(wanted)
    if not n:raise ValueError('No surviving issuer')
    if not changed:
        targets={c:values[c] for c in wanted}
        if n>15 and protect:
            limit=2*nav/n
            freed=math.fsum(max(0,v-limit) for v in targets.values())
            targets={c:min(v,limit) for c,v in targets.items()}
            buys,_=waterfill(targets,freed,set(targets))
            for c,v in buys.items():targets[c]+=v
        return targets,set()
    preserved={}
    comparable=[trailing_returns[c] for c in wanted if c in values and c in trailing_returns]
    med=statistics.median(comparable) if comparable else math.inf
    if n>15 and protect:
        for c in wanted:
            if c in values and values[c]/nav>=1.5/n and trailing_returns.get(c,-math.inf)>med:
                preserved[c]=min(values[c],2*nav/n)
    residual=(nav-math.fsum(preserved.values()))/(n-len(preserved))
    return {c:preserved.get(c,residual) for c in wanted},set(preserved)


def xirr(flows):
    """Unique dated IRR for deposits followed by one positive final NAV."""
    origin=date.fromisoformat(flows[0][0])
    terms=[((date.fromisoformat(d)-origin).days/365.0,v) for d,v in flows]
    def npv(log_rate):return math.fsum(v*math.exp(-log_rate*t) for t,v in terms)
    lo,hi=-5.,5.
    if npv(lo)*npv(hi)>0:raise ValueError('IRR not bracketed')
    for _ in range(150):
        mid=(lo+hi)/2
        if npv(mid)>0:lo=mid
        else:hi=mid
    return math.expm1((lo+hi)/2)


def coverage():
    quote,provenance=load_quotes();byday=events();compositions=frozen_compositions()
    calendar=read(STUDY/'contribution_calendar.csv'); dates={r['date'] for r in calendar}|{r['month_end'] for r in calendar}
    checks=[]
    for portfolio in PORTFOLIOS:
        held=set(compositions[portfolio,2014].values())
        for day in sorted(dates|set(byday)|set(DATES.values())):
            if not START<=day<=END:continue
            for e in sorted(byday.get(day,[]),key=lambda e:e['kind']=='RIGHT_REINVEST'):
                if e['ticker'] not in held:continue
                if e['kind']=='CONVERSION':held.remove(e['ticker']);held.update(t for t,_ in e['legs'])
                elif e['kind']=='REDEMPTION':held.remove(e['ticker'])
                elif e['kind'] in ['RIGHT','SPINOFF']:held.add(e['successor'])
                elif e['kind']=='RIGHT_REINVEST':held.remove(e['ticker'])
            if day in dates or day in DATES.values():
                phase='INITIAL' if day==START else 'MONTHLY_FIRST' if day in {r['date'] for r in calendar} else 'MONTH_END_OR_JUNE'
                for t in sorted(held):
                    checks.append(dict(portfolio=portfolio,date=day,phase=phase,ticker=t,
                        close=quote.get((t,day),''),status='EXACT_B3_CLOSE' if (t,day) in quote else 'MISSING_EXACT_CLOSE',
                        record_sha256=provenance.get((t,day),{}).get('record_sha256','')))
            if day in DATES.values() and portfolio not in ['BH padrão','BESST-10 BH'] and START<day<END:
                y=int(day[:4]);held=set(compositions[portfolio,y].values())|({'XPBR31'} if 'XPBR31' in held else set())
    write(STUDY/'quote_coverage.csv',checks)
    print('Coverage',len(checks),'missing',[(r['portfolio'],r['date'],r['ticker']) for r in checks if r['status']=='MISSING_EXACT_CLOSE'][:30],flush=True)
    return checks


if __name__=='__main__':coverage()
