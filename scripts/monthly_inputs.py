"""PR #5 inputs only: historical universe, calendar and exact B3 quotes.

This module never calls the older writers or modifies their frozen artifacts.
The ranking is committed before any monetary performance is calculated.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date
from pathlib import Path
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import subprocess
from zipfile import ZipFile

from stage1_pit import ROOT, OUT, gzread, gzwrite
from stage1_select import Evidence, classify
from b00s_variants import read, write, jsonwrite, sha

STUDY = ROOT/'research/monthly_contributions_2014_2026'
BASELINE = '8671156586c2d12c3c8c121510db33144199338c'
START = '2014-06-30'
END = '2026-06-30'
DATA = Path('/workspaces/b3-pipeline-data-and-backtest-framework')


def ibov_calendar():
    rows=[]
    for year in range(2014,2027):
        p=ROOT/f'research/returns_2014_2026_inputs/b3/ibov_{year}.json'
        d=json.loads(p.read_text())
        for r in d['results']:
            for month in range(1,13):
                value=r.get(f'rateValue{month}')
                if value:
                    day=f'{year}-{month:02d}-{r["day"]:02d}'
                    if START<=day<=END:
                        rows.append(dict(date=day,close=float(value.replace('.','').replace(',','.')),
                            source=str(p.relative_to(ROOT)),source_sha256=sha(p)))
    rows.sort(key=lambda r:r['date'])
    assert len({r['date'] for r in rows})==len(rows)
    months=defaultdict(list)
    for r in rows:months[r['date'][:7]].append(r['date'])
    calendar=[dict(month=m,date=min(ds),month_end=max(ds),amount=2500,
        timing='FIRST_B3_SESSION_CLOSE') for m,ds in sorted(months.items()) if m>'2014-06']
    assert len(calendar)==144 and sum(r['amount'] for r in calendar)==360000
    assert rows[0]['date']==START and rows[-1]['date']==END
    write(STUDY/'inputs/ibov_daily.csv',rows)
    write(STUDY/'contribution_calendar.csv',calendar)
    return calendar


def archive_quotes(path, names=None, cutoff=None):
    source=dict(file=path.name,sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),
        url=f'https://bvmf.bmfbovespa.com.br/InstDados/SerHist/{path.name}',provenance='LOCAL_PREEXISTING')
    quotes=[]
    with ZipFile(path) as z:
        for member in z.namelist():
            with io.BufferedReader(z.open(member),buffer_size=1024*1024) as f:
                for lineno,line in enumerate(f,1):
                    if line[:2]!=b'01' or line[24:27]!=b'010':continue
                    t=line[12:24].decode().strip()
                    if names is None and not re.fullmatch(r'[A-Z]{4}(3|4|5|6|7|8|11)',t):continue
                    raw=line[2:10].decode();day=f'{raw[:4]}-{raw[4:6]}-{raw[6:8]}'
                    if cutoff and day>cutoff:continue
                    if not cutoff and not START<=day<=END:continue
                    if names is not None and t not in names:continue
                    factor=int(line[210:217]);assert factor>0
                    quotes.append(dict(ticker=t,date=day,close=int(line[108:121])/100/factor,
                        volume=int(line[170:188])/100,quotation_factor=factor,
                        isin_code=line[230:242].decode().strip(),line=lineno,
                        member=member,record_sha256=hashlib.sha256(line).hexdigest()))
    return dict(source=source,quotes=quotes)


def freeze_baseline():
    p=STUDY/'inputs/protected_pr3_pr4.json'
    if p.exists():return
    files=subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE],cwd=ROOT,text=True).splitlines()
    rows=[dict(path=n,sha256=sha(ROOT/n)) for n in files]
    jsonwrite(p,dict(commit=BASELINE,files=rows))


def rank_besst(raw_root=DATA):
    """All observed contemporaneous issuers, including unit-only and excluded classes.

    Missing class prices are disclosed scenarios, not mathematical bounds.
    Emitted capital is the primary measure; treasury maximum deduction is shown.
    A stock must have a real close at formation to be bought at formation.
    """
    frozen=STUDY/'inputs/ranking_freeze.json'
    if frozen.exists():
        for r in json.loads(frozen.read_text())['files']:
            if sha(ROOT/r['path'])!=r['sha256']:raise ValueError(('Frozen ranking changed',r['path']))
        print('Existing pre-return ranking retained',flush=True)
        return read(STUDY/'besst10_bh_selection_2014.csv')
    E=Evidence();_,sectors,caps=E.asof(2014)
    p=STUDY/'inputs/universe_quotes_2014.json.gz'
    if not p.exists():gzwrite(p,archive_quotes(raw_root/'data/raw/COTAHIST_A2014.ZIP',cutoff=START))
    data=gzread(p); qs=data['quotes']; groups=defaultdict(list); unresolved=[]
    for r in qs:
        c,method=E.identity(r)
        if not c:unresolved.append(r);continue
        groups[c].append(dict(r,identity_source=method))
    ranking=[];classes=[];excluded=[]
    treasury=E.treasury_asof
    for c,sector in sorted(sectors.items()):
        bs,_=classify(sector['sector'],sector['activity'],sector['name'])
        # Electrical distributors historically miscoded as equipment.
        if c=='61695227000193':bs='Energia'
        rawsector=sector['sector']
        if not bs and not any(x in rawsector for x in ['Telecom','Segur','Saneamento','Bancos','Energia']):continue
        own=groups.get(c,[]);at=[r for r in own if r['date']==START]
        if not bs:
            excluded.append(dict(cnpj=c,company=sector['name'],sector=rawsector,
                tickers=';'.join(sorted({r['ticker'] for r in own})),reason='OUTSIDE_STRICT_BESST_TAXONOMY',
                sector_received=sector['received'],sector_docid=sector['docid']))
            continue
        if not own:
            excluded.append(dict(cnpj=c,company=sector['name'],sector=bs,tickers='',
                reason='NO_LISTED_EQUITY_OBSERVED_IN_B3_2014_TO_CUTOFF',
                sector_received=sector['received'],sector_docid=sector['docid']))
            continue
        latest={}
        for r in sorted(own,key=lambda r:r['date']):latest[r['ticker']]=r
        liquid=[]
        sessions=sorted({r['date'] for r in qs})[-126:]
        for t in sorted({r['ticker'] for r in at}):
            rs=[r for r in own if r['ticker']==t and r['date'] in sessions]
            vols=sorted(r['volume'] for r in rs)
            med=(vols[(len(vols)-1)//2]+vols[len(vols)//2])/2
            liquid.append(dict(ticker=t,median_volume=med,sessions=len(rs),total_volume=sum(vols)))
        rep=max(liquid,key=lambda r:(r['median_volume'],r['sessions'],r['total_volume'],tuple(-ord(x) for x in r['ticker']))) if liquid else None
        capital=caps.get(c,{})
        on=capital.get('on');pn=capital.get('pn');note='';method='ISSUED_CLASSES_AT_EXACT_CLOSE'
        # Frozen contemporaneous Santander action, not the later FRE cited by PR3.
        if c=='90400888000142' and on is not None:
            on/=55;pn=(pn+19002100957)/55
            note='55:1 consolidation and PN bonus effective 2014-06-02; pre-existing PIT action; rounding unresolved, exclusion safely below bank leaders'
        quoted={r['ticker'][-1]:r for r in at if len(r['ticker'])==5}
        lastclasses={r['ticker'][-1]:r for r in latest.values() if len(r['ticker'])==5}
        onq=quoted.get('3');pnq=quoted.get('4')
        pns=[quoted[k] for k in '5678' if k in quoted]
        if pnq is None and len(pns)==1:pnq=pns[0]
        op=onq['close'] if onq else None;pp=pnq['close'] if pnq else None
        proxy=None;stress=None;last_cap=None
        # Unit proxies allocate a unit price equally across its documented shares;
        # they do not assert the market prices of unlisted control ON classes.
        unit_counts={'SULA':3,'TAEE':3,'ALUP':3,'RNEW':3,'CTAX':5}
        unit_cap_min=None;unit_cap_max=None
        units=[r for r in at if r['ticker'].endswith('11')]
        if units and not quoted and on is not None:
            u=units[0];parts=unit_counts.get(u['ticker'][:4])
            if parts:
                op=pp=u['close']/parts;method='UNIT_EQUAL_CLASS_PRICE_SCENARIO'
                unit_cap_min=u['close']*min(on,pn/(parts-1))
                unit_cap_max=u['close']*max(on,pn/(parts-1))
                note+='; unit scenarios constrained by ON+(parts-1)*PN=observed unit close; see unit source proof. RNEW/CTAX constitution pending primary PIT proof'
        missing_on=bool(on and not onq);missing_pn=bool(pn and not pnq)
        if on is not None and pn is not None:
            if missing_on and op is None and pp is not None:
                op=pp;method='MISSING_ON_PN_PARITY_SCENARIO'
            if missing_pn and pp is None and op is not None:
                pp=op;method='MISSING_PN_ON_PARITY_SCENARIO'
            if (not on or op is not None) and (not pn or pp is not None):
                proxy=on*(op or 0)+pn*(pp or 0)
                stress=proxy+(on*(op or 0) if missing_on else 0)+(pn*(pp or 0) if missing_pn else 0)
                lo=lastclasses.get('3');lp=lastclasses.get('4') or next((lastclasses[k] for k in '5678' if k in lastclasses),None)
                if (not on or lo) and (not pn or lp):last_cap=on*(lo['close'] if lo else 0)+pn*(lp['close'] if lp else 0)
        tq=treasury.get(c,{}).get('quantity',0)
        row=dict(cnpj=c,company=sector['name'],sector=bs,observed_tickers=';'.join(sorted(latest)),
            ticker=rep['ticker'] if rep else '',tradable_at_formation=bool(rep),
            on_shares=on,pn_shares=pn,on_price_used=op,pn_price_used=pp,
            market_cap=proxy,missing_class_double_price_scenario=stress,last_observed_class_cap=last_cap,
            unit_cap_min=unit_cap_min,unit_cap_max=unit_cap_max,
            last_on_date=lastclasses.get('3',{}).get('date',''),
            exact_class_prices=not missing_on and not missing_pn,
            price_method=method,treasury_shares=tq,
            treasury_maximum_value_deduction=tq*max(op or 0,pp or 0),
            capital_docid=capital.get('docid',''),capital_received=capital.get('received',''),
            capital_approved=capital.get('approved',''),capital_source=capital.get('source',''),
            sector_docid=sector['docid'],sector_received=sector['received'],sector_source=sector['source'],
            source_zip_sha256=data['source']['sha256'],median_volume=rep['median_volume'] if rep else 0,
            sessions=rep['sessions'] if rep else 0,total_volume=rep['total_volume'] if rep else 0,
            rank='',selected=False,initial_weight=0,note=note)
        ranking.append(row)
        for r in sorted(latest.values(),key=lambda r:r['ticker']):
            classes.append(dict(cnpj=c,company=sector['name'],sector=bs,**r,source_zip_sha256=data['source']['sha256']))
    for bs in sorted({r['sector'] for r in ranking}):
        g=sorted([r for r in ranking if r['sector']==bs and r['tradable_at_formation'] and r['market_cap'] is not None],
            key=lambda r:(-r['market_cap'],r['cnpj']))
        for i,r in enumerate(g,1):r['rank']=i;r['selected']=i<=2
    selected=[r for r in ranking if r['selected']]
    for r in selected:r['initial_weight']=1/len(selected)
    ranking.sort(key=lambda r:(r['sector'],int(r['rank']) if r['rank'] else 10000,r['cnpj']))
    write(STUDY/'besst10_bh_ranking_2014.csv',ranking)
    write(STUDY/'ranking_besst_market_cap_2014.csv',ranking)
    write(STUDY/'besst10_bh_selection_2014.csv',selected)
    write(STUDY/'inputs/besst_class_quotes_2014.csv',classes)
    write(STUDY/'inputs/besst_universe_exclusions_2014.csv',excluded)
    write(STUDY/'inputs/unresolved_equity_identities_2014.csv',list({r['ticker']:r for r in unresolved}.values()))
    jsonwrite(STUDY/'inputs/ranking_freeze.json',dict(cutoff=START,baseline=BASELINE,
        basis='ISSUED_CAPITAL; exact prices for leaders; disclosed missing-class scenarios for other issuers',
        tie_break='median traded BRL volume over last 126 sessions, session count, total BRL volume, ascending ticker; rank ties ascending CNPJ',
        returns_accessed=False,files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [
            STUDY/'besst10_bh_ranking_2014.csv',STUDY/'besst10_bh_selection_2014.csv',STUDY/'inputs/besst_class_quotes_2014.csv',STUDY/'inputs/besst_universe_exclusions_2014.csv']]))
    print('BESST selected',[(r['sector'],r['ticker'],r['market_cap']) for r in selected],flush=True)
    return selected


def freeze_quotes(raw_root=DATA):
    selected=read(STUDY/'besst10_bh_selection_2014.csv')
    holdings=read(ROOT/'research/b00s_four_variants_2014_2026/results/holdings_by_june.csv')
    names={r['ticker'] for r in holdings}|{r['ticker'] for r in selected}
    names.update('CCRO3 MOTV3 WEGE3 ITUB4 BBDC4 TBLE3 EGIE3 CMIG4 HYPE3 RADL3 XPBR31'.split())
    for p in [OUT/'cache/continuation_events.json.gz',OUT/'cache/b00s_initial_events.json.gz',OUT/'cache/bh_owned_events.json.gz']:
        for e in gzread(p):
            names.add(e['ticker'])
            if e.get('successor'):names.add(e['successor'])
            names.update(t for t,_ in e.get('legs',[]))
    names.update('EGIE3 MOTV3 ISAE4 AXIA3 AXIA7 DXCO3 GUAR3 YDUQ3'.split())
    sources=[]
    for year in range(2014,2027):
        p=STUDY/f'inputs/quotes_{year}.json.gz'
        if not p.exists():gzwrite(p,archive_quotes(raw_root/f'data/raw/COTAHIST_A{year}.ZIP',names=names))
        d=gzread(p);sources.append(d['source']);print('quotes',year,len(d['quotes']),flush=True)
    jsonwrite(STUDY/'inputs/quote_sources.json',sources)
    jsonwrite(STUDY/'inputs/quote_security_names.json',sorted(names))


def main():
    (STUDY/'inputs').mkdir(parents=True,exist_ok=True)
    freeze_baseline();ibov_calendar();rank_besst();freeze_quotes()

if __name__=='__main__':main()
