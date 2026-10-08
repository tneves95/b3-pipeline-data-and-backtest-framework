"""First B00S interval: frozen 2014 weights and owned economic rights only."""
import argparse
from bisect import bisect_right
import csv
import json
import math
from stage1_pit import ROOT,OUT,DATES,gzread,gzwrite,dump
from stage1_buyhold import trajectory


def inputs():
    selected=[r for r in csv.DictReader((OUT/'established_selections.csv').open()) if r['strategy']=='B00S' and r['year']=='2014']
    prices={}
    for y in (2014,2015):
        for r in gzread(OUT/f'cache/b00s_initial_quotes_{y}.json.gz')['quotes']:
            k=r['ticker'],r['date']
            if k in prices: raise ValueError(('Duplicate quote',k))
            prices[k]=r['close']
    return selected,prices


def freeze_events():
    selected,prices=inputs(); calendar=sorted(d for t,d in prices if t=='ITUB4')
    market=gzread(OUT/'cache/market.json.gz'); bh=gzread(OUT/'cache/bh_owned_events.json.gz'); events=[]
    def add(t,day,kind,source,**kw):
        events.append(dict(id=f'B00S_{t}_{day}_{kind}_{len(events)}',ticker=t,ex_date=day,kind=kind,source=source,**kw))
    shared={'BBDC4','ITUB4','CMIG4','TBLE3'}
    events.extend(e for e in bh if e['ticker'] in shared and DATES[2014]<e['ex_date']<=DATES[2015])
    for row in selected:
        t=row['ticker']
        if t in shared: continue
        mapped={'TRPL4':'ISAE4'}.get(t,t)
        isins={r['isin_code'] for r in market['isins'] if r['ticker']==mapped}
        for e in market['actions']:
            if e['isin_code'] not in isins or not DATES[2014]<=e['event_date']<DATES[2015]:continue
            if e['event_type'] not in ('CASH_DIVIDEND','JCP'): raise ValueError(('Unreviewed structural event',e))
            add(t,calendar[bisect_right(calendar,e['event_date'])],'DISTRIBUTION','cache/market.json.gz; B3',
                amount=e['value'],record_date=e['event_date'],isin=e['isin_code'],original_type=e['event_type'])
    add('GETI4','2014-08-07','DISTRIBUTION','originals/owned_proventos_44287.zip; PN payment 87; record date corroborated by historical B3-derived distribution table',amount=1.07262)
    add('GETI4','2015-05-11','DISTRIBUTION','originals/owned_proventos_50033.zip; PN payment 80; record date corroborated by historical B3-derived distribution table',amount=.33696)
    add('TIMP3','2015-05-13','DISTRIBUTION','originals/tim_2015_ago.pdf.gz; 2015-04-14 AGM, record 2015-05-12',amount=.151751431)
    add('LIGT3','2015-04-13','DISTRIBUTION','Light AGM 2015-04-10; entitlement on AGM date; source in b00s_initial_evidence.json',amount=.7719)
    add('CPFE3','2015-04-30','SHARES','https://www.sec.gov/Archives/edgar/data/1300482/000129281415001033/cpl20150429_6k.htm',factor=1.03194510783)
    # Rights are detached from the old units, sold at their first observed close,
    # and reinvested in their parent. Later reinvestments receive no past rights.
    for t,ex,ratio,first,source in [
      ('ABCB4','2014-07-01',.02541904,'2014-07-02','FRE 2015 capital increase; B3 ex 2014-07-01 transcription'),
      ('TRPL4','2014-07-17',.05631994,'2014-07-21','FRE 2015 doc 56621 capital increase 172049; ex-date inferred next session after approval'),
      ('ABCB4','2015-01-02',.02763470,'2015-01-08','B3 BDI 2015-01-02 transcription; replaces inconsistent FRE 3.57531927%')]:
        right=t[:4]+'2';add(t,ex,'RIGHT',source,successor=right,ratio=ratio)
        add(right,first,'RIGHT_REINVEST','COTAHIST first observed right close',successor=t)
    events.sort(key=lambda e:(e['ex_date'],e['ticker'],e['kind'],e['id']))
    gzwrite(OUT/'cache/b00s_initial_events.json.gz',events)


def run():
    selected,prices=inputs();events=gzread(OUT/'cache/b00s_initial_events.json.gz')
    positions,ledger=trajectory(prices,events,{r['ticker']:float(r['weight']) for r in selected},[DATES[2014],DATES[2015]])
    levels={r['date']:r['index_total'] for r in positions};ret=100*(levels[DATES[2015]]/levels[DATES[2014]]-1)
    ibov=float(next(csv.DictReader((ROOT/'research/returns_2014_2026_results/annual_returns_pct.csv').open()))['IBOV'])
    # Explicit exploratory status: tiny issuer/transcribed event uncertainties remain.
    rows=[dict(year=2014,portfolio=n,start=DATES[2014],end=DATES[2015],return_pct=ret,IBOV_pct=ibov,excess_pp=ret-ibov,
        selection='ESTABLISHED_2014_BESST_20',return_status='EXPLORATORY_DIRECTED_EVENTS_WITH_DISCLOSED_RIGHT_ASSUMPTIONS')
        for n in ['B00S B2','B00S BH+entradas']]
    dump('b00s_initial_pct.csv',rows);dump('b00s_initial_positions.csv',positions);dump('b00s_initial_event_ledger.csv',ledger)
    attribution=[]
    for s in selected:
        t=s['ticker'];pair={r['date']:r for r in positions if r['ticker']==t}
        left,right=pair[DATES[2014]]['index_component'],pair[DATES[2015]]['index_component']
        attribution.append(dict(ticker=t,sector=s['sector'],weight=float(s['weight']),return_pct=100*(right/left-1),contribution_pp=100*(right-left)))
    dump('b00s_initial_contributions.csv',attribution)
    fields=sorted(set().union(*(e.keys() for e in events)))
    dump('b00s_initial_events.csv',[{k:e.get(k,'') for k in fields} for e in events])
    # Sensitivity is published separately, never used to silently drop rights.
    no_rights=[e for e in events if e['kind'] not in ('RIGHT','RIGHT_REINVEST')]
    p,_=trajectory(prices,no_rights,{r['ticker']:float(r['weight']) for r in selected},[DATES[2014],DATES[2015]])
    without=100*(p[-1]['index_total']-1)
    dump('b00s_initial_sensitivity.csv',[dict(case='BASE_WITH_OWNED_RIGHTS',return_pct=ret,delta_pp=0),
        dict(case='DIAGNOSTIC_OMITTED_RIGHTS_NOT_PORTFOLIO',return_pct=without,delta_pp=without-ret)])
    print(json.dumps(rows,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--freeze-events',action='store_true');a=p.parse_args()
    if a.freeze_events:freeze_events()
    run()
