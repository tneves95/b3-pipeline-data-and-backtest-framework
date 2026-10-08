"""Incremental percentage trajectories from the accepted 5cf7eb4 positions.

Replay is offline. Initial segments, BH and IBOV are immutable inputs.
Unproved entries stay outside the evidence-only case and are measured separately.
"""
from __future__ import annotations
import argparse
from bisect import bisect_right
from collections import defaultdict
import csv
import json
import math
from functools import lru_cache

from stage1_pit import ROOT, OUT, DATES, gzread, gzwrite, dump
from stage1_continuity import renew_b2
from stage1_buyhold import apply_day

LEGACY=ROOT/'research/graham_v6_comparison'
ALIASES={'EGIE3':'TBLE3','DTEX3':'DXCO3','RIAA3':'GUAR3','ESTC3':'YDUQ3',
         'ISAE4':'TRPL4','AXIA3':'ELET3'}
def canonical(t): return ALIASES.get(t,t)
def read(p): return list(csv.DictReader(p.open(encoding='utf-8-sig')))

@lru_cache(maxsize=1)
def prices():
    result={}; raw=[]
    for year in range(2015,2027):
        rows=gzread(OUT/f'cache/continuation_quotes_{year}.json.gz')['quotes']
        raw.extend(rows)
        for r in rows:
            key=canonical(r['ticker']),r['date']
            if key in result: raise ValueError(('Duplicate security/date',key))
            result[key]=r['close']
    extra=sorted((OUT/'cache').glob('continuation_extra_quotes_*.json.gz'))
    extra+=sorted((OUT/'cache').glob('continuation_irb_quotes_*.json.gz'))
    for path in extra:
        for r in gzread(path)['quotes']:
            key=canonical(r['ticker']),r['date']
            if key in result: raise ValueError(('Duplicate extra quote',key))
            result[key]=r['close'];raw.append(r)
    return result,raw

@lru_cache(maxsize=None)
def selection(strategy,year,overrides=()):
    """Inherited screeners supply decisions, never inherited portfolio returns."""
    screen=read(OUT/'screening.csv')
    subset=[r for r in screen if r['strategy']==strategy and int(r['year'])==year]
    status={canonical(r['ticker']):r['status'] for r in subset}
    sector={canonical(r['ticker']):r['sector'] for r in subset}
    if year<2020:
        for r in json.loads((OUT/'continuation_selection_resolutions.json').read_text()):
            if r['strategy']==strategy and year in r['years']:
                status[canonical(r['ticker'])]=r['status']
        for y,t in overrides:
            if y==year: status[canonical(t)]='PASS'
        chosen=sorted(t for t,s in status.items() if s=='PASS')
        if strategy=='R03': targets={t:1/len(chosen) for t in chosen}
        else:
            groups={sector[t] for t in chosen}
            targets={t:1/len(groups)/sum(sector[u]==sector[t] for u in chosen) for t in chosen}
        return status,targets
    weights=[r for r in read(ROOT/'research/returns_2014_2026_results/conditional_legacy_weights.csv')
             if r['strategy']==strategy and int(r['year'])==year]
    targets={canonical(r['ticker']):float(r['weight']) for r in weights}
    if strategy=='R03':
        if year<2022:
            legacy=[r for r in json.loads((ROOT/'graham_legacy_reference_2020_2025.json').read_text()) if r['year']==year]
            for r in legacy:
                t=canonical(r['ticker'])
                status[t]='FAIL' if any(r.get(f'legacy_f{i}')==0 for i in range(1,7)) else 'INDETERMINATE'
        else:
            for r in read(ROOT/f'graham_final_{year}.csv'):
                status[canonical(r['ticker'])]='PASS' if r['R03_final']=='True' else 'FAIL'
    else:
        universe=read(LEGACY/'audit_v13_inputs/universe_v9_snapshot.csv')
        for r in universe:
            if int(r['entry_year'])==year and r['preselection_pass']=='0':
                status[canonical(r['ticker'])]='FAIL'
        for r in json.loads((LEGACY/'execution_v11_2_2026_10_07/auditoria_besst_v9/selection_rows.json').read_text()):
            if r['year']==year and not r['cash5']: status[canonical(r['ticker'])]='FAIL'
    status.update({t:'PASS' for t in targets})
    if strategy=='B00S':
        # A new legal shell does not falsify the predecessor's five-year record.
        # Preserve inherited exposure pending full lineage/liquidity certification.
        for t in ('AESB3','TIMS3'):
            if t not in targets and 2021<=year<=2024:
                status[t]='INDETERMINATE'
        if year==2025 and 'TRPL4' not in targets:
            status['TRPL4']='INDETERMINATE' # renamed ISAE4; old ticker liquidity is not a failure
    return status,targets

def freeze_events():
    quote,raw=prices(); calendar=sorted(d for t,d in quote if t=='ITUB4')
    market=gzread(OUT/'cache/market.json.gz');events=[]
    names={t for t,d in quote};isin_names=defaultdict(set)
    for r in raw: isin_names[r['isin']].add(canonical(r['ticker']))
    # Old records can live under a renamed issuer's current class ISIN.
    for r in market['isins']:
        t=canonical(r['ticker'])
        if t in names: isin_names[r['isin_code']].add(t)
    def add(t,day,kind,source,**kw):
        events.append(dict(id=f'CONT_{len(events)}_{t}_{day}',ticker=t,ex_date=day,kind=kind,source=source,**kw))
    for e in market['actions']:
        if not DATES[2015]<=e['event_date']<DATES[2026]: continue
        ts=isin_names[e['isin_code']]
        if not ts: continue
        if len(ts)!=1: raise ValueError(('Unresolved ISIN lineage',e,ts))
        t=next(iter(ts)); day=calendar[bisect_right(calendar,e['event_date'])]
        if e['event_type'] in ('CASH_DIVIDEND','JCP'):
            add(t,day,'DISTRIBUTION','cache/market.json.gz; B3',amount=e['value'],record_date=e['event_date'])
        elif e['event_type'] in ('STOCK_SPLIT','BONUS_SHARES'):
            add(t,day,'SHARES','cache/market.json.gz; B3',factor=1+e['factor']/100,record_date=e['event_date'])
        elif e['event_type']=='REVERSE_SPLIT':
            add(t,day,'SHARES','cache/market.json.gz; B3',factor=e['factor'],record_date=e['event_date'])
        else: raise ValueError(('Unsupported B3 action',e))
    # Reuse the full reconciled records, replacing their covered asset/date range.
    for filename,start in [
        ('checkpoint_v12_2026_10_07/eventos_cenario_v12.json',DATES[2020]),
        ('checkpoint_v13_2026_10_07/eventos_utilizados.json',DATES[2020])]:
        records=json.loads((LEGACY/filename).read_text())
        covered={canonical(r['asset']) for r in records}
        events=[e for e in events if not (e['ticker'] in covered and e['ex_date']>start)]
        for r in records:
            if r['kind']=='CASH_OUT':continue # voluntary OPA is not a compulsory redemption
            if not start<r['date']<=DATES[2026]:continue
            t=canonical(r['asset']); kw={}
            if r['kind']=='CASH':kind='DISTRIBUTION';kw['amount']=r['amount']
            elif r['kind'] in ('BONUS','SPLIT'):kind='SHARES';kw['factor']=r['factor']
            elif r['kind'] in ('MERGER','CONVERSION'):kind='CONVERSION';kw['legs']=[[canonical(u),q] for u,q in r['legs']]
            else:raise ValueError(r)
            add(t,r['date'],kind,r['source'],legacy_id=r['event_id'],**kw)
    bh=gzread(OUT/'cache/bh_owned_events.json.gz')
    covered={e['ticker'] for e in bh}
    events=[e for e in events if e['ticker'] not in covered]
    for e in bh:
        if DATES[2015]<e['ex_date']<=DATES[2026]: events.append(e.copy())
    # ON gets the same capital multiplier, but never PN dividend amounts.
    for t,pn in [('BBDC3','BBDC4'),('ITUB3','ITUB4'),('CMIG3','CMIG4')]:
        events=[e for e in events if not(e['ticker']==t and e['kind']=='SHARES')]
        for e in bh:
            if e['ticker']==pn and e['kind']=='SHARES' and e['ex_date']>DATES[2015]:
                events.append(dict(e,id=e['id']+'_ON',ticker=t))
    for r in json.loads((LEGACY/'itsa_rights_verified_2026_10_07.json').read_text()):
        add('ITSA3',r['ex_date'],'RIGHT',r['source_url'],successor='ITSA1',ratio=float(r['rights_per_share']))
        first=min(d for t,d in quote if t=='ITSA1' and d>=r['available_from'])
        add('ITSA1',first,'RIGHT_REINVEST','COTAHIST first negotiated close; fractional index',successor='ITSA3')
    for e in json.loads((OUT/'continuation_event_resolutions.json').read_text()):
        # Explicit supersession keys prevent duplication of corrected B3 events.
        dates=e.pop('replace_dates',[])
        events=[old for old in events if not(old['ticker']==e['ticker'] and old['ex_date'] in dates and old['kind']==e['kind'])]
        events.append(e)
    # PNC is a separate security, not an increase in ON units.
    events=[e for e in events if not(e['ticker']=='ELET3' and e['kind']=='SHARES' and e['ex_date']=='2025-12-22')]
    events.sort(key=lambda e:(e['ex_date'],e['ticker'],e['id']))
    if len({e['id'] for e in events})!=len(events):raise ValueError('Duplicate event identity')
    gzwrite(OUT/'cache/continuation_events.json.gz',events)
    keys=sorted(set().union(*(e.keys() for e in events)))
    dump('continuation_events.csv',[{k:e.get(k,'') for k in keys} for e in events])
    print('Frozen shared events',len(events))

def event_day(units,events,quote,day):
    ordinary=[e for e in events if e['kind'] not in ('CONVERSION','REDEMPTION') and e['ticker'] in units]
    result=apply_day(units,ordinary,quote,day)
    newly_available=[e for e in events if e['kind']=='RIGHT_REINVEST'
                     and e['ticker'] not in units and e['ticker'] in result]
    if newly_available: result=apply_day(result,newly_available,quote,day)
    # Conversion distributions are amounts per old entitlement, reinvested in successor.
    for e in events:
        t=e['ticker']
        if t not in units:continue
        if e['kind']=='CONVERSION':
            q=result.pop(t)
            for child,ratio in e['legs']: result[child]=result.get(child,0)+q*ratio
            if e.get('amount'):
                child=e['legs'][0][0];result[child]+=units[t]*e['amount']/quote[child,day]
        elif e['kind']=='REDEMPTION':
            q=result.pop(t);v=q*e['amount']
            nav=math.fsum(n*quote[u,day] for u,n in result.items())
            if nav<=0:raise ValueError('Redemption without surviving index constituents')
            result={u:n*(1+v/nav) for u,n in result.items()}
    return result

def resume(portfolio,overrides=(),save=True,event_transform=None,decision_transform=None,verbose=True):
    quote,_=prices();events=gzread(OUT/'cache/continuation_events.json.gz')
    if event_transform: events=event_transform(events)
    strategy='R03' if portfolio=='R03 B2' else 'B00S';start_year=2016 if strategy=='R03' else 2015
    if strategy=='R03':
        prior=[r for r in read(OUT/'established_segment_positions.csv') if r['year']=='2015']
        units={canonical(r['ticker']):float(r['index_end'])/quote[canonical(r['ticker']),DATES[2016]] for r in prior}
    else:
        prior=[r for r in read(OUT/'b00s_initial_positions.csv') if r['date']==DATES[2015]]
        units={canonical(r['ticker']):float(r['units']) for r in prior}
    bydate=defaultdict(list)
    for e in events: bydate[e['ex_date']].append(e)
    annual=[];positions=[];reviews=[];ledger=[];decisions=[]
    ibov={int(r['year']):float(r['ibov_points']) for r in read(ROOT/'research/returns_2014_2026_results/ibov_june_closes.csv')}
    def snapshot(day,phase):
        nav=math.fsum(q*quote[t,day] for t,q in units.items())
        for t,q in sorted(units.items()):
            positions.append(dict(portfolio=portfolio,date=day,phase=phase,ticker=t,units=q,nominal_close=quote[t,day],
                                  index_component=q*quote[t,day],index_total=nav,weight=q*quote[t,day]/nav))
        return nav
    for year in range(start_year,2026):
        start,end=DATES[year],DATES[year+1];nav=snapshot(start,'BEFORE_REVIEW')
        status,targets=selection(strategy,year,overrides)
        status=status.copy();targets=targets.copy()
        if decision_transform: status,targets=decision_transform(year,status,targets)
        # Different listed representations of the same inherited issuer.
        if 'TIET11' in units:
            status['TIET11']=status.get('TIET4','INDETERMINATE')
            if 'TIET4' in targets: targets['TIET11']=targets.pop('TIET4')
        holdings={t:q*quote[t,start] for t,q in units.items()}
        if portfolio=='B00S BH+entradas':status={t:'RETAIN' for t in holdings}|{t:'PASS' for t in targets}
        decisions.extend(dict(portfolio=portfolio,year=year,ticker=t,status=status.get(t,'INDETERMINATE'),
            target=targets.get(t,0),inherited=t in holdings) for t in sorted(status.keys()|targets.keys()|holdings.keys()))
        after,review=renew_b2(holdings,status,targets)
        units={t:v/quote[t,start] for t,v in after.items()}
        reviews.extend(dict(portfolio=portfolio,year=year,date=start,status=status.get(r['ticker'],'INDETERMINATE'),**r) for r in review)
        snapshot(start,'AFTER_REVIEW')
        for day in sorted(d for d in bydate if start<d<=end):
            spawned={e['successor'] for e in bydate[day]
                     if e['ticker'] in units and e['kind']=='RIGHT'}
            relevant=[e for e in bydate[day] if e['ticker'] in units
                      or (e['kind']=='RIGHT_REINVEST' and e['ticker'] in spawned)]
            if not relevant:continue
            before=units.copy();units=event_day(units,relevant,quote,day)
            for t in sorted(before.keys()|units.keys()):
                if units.get(t)!=before.get(t):ledger.append(dict(portfolio=portfolio,date=day,ticker=t,
                    units_before=before.get(t,0),units_after=units.get(t,0),event_ids=';'.join(e['id'] for e in relevant)))
        final=snapshot(end,'PERIOD_END');ret=100*(final/nav-1);bench=100*(ibov[year+1]/ibov[year]-1)
        annual.append(dict(year=year,portfolio=portfolio,start=start,end=end,return_pct=ret,cumulative_pct=100*(final-1),
            IBOV_pct=bench,excess_pp=ret-bench,return_status='CONTINUOUS_QUALIFIED_RECONSTRUCTION'))
        if verbose: print(portfolio,year,round(ret,6),round(100*(final-1),6),len(units),flush=True)
    if save:
        stem={'R03 B2':'r03_continuation','B00S B2':'b00s_b2_continuation','B00S BH+entradas':'b00s_bh_continuation'}[portfolio]
        for suffix,rows in [('pct',annual),('positions',positions),('reviews',reviews),('ledger',ledger),('decisions',decisions)]:dump(stem+'_'+suffix+'.csv',rows)
    return annual,positions,reviews,ledger

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--freeze-events',action='store_true');p.add_argument('--portfolio',default='R03 B2');a=p.parse_args()
    if a.freeze_events:freeze_events()
    resume(a.portfolio)
