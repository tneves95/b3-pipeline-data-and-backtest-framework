"""Continuous gross-return index for the eight original 2014 issuers.

All holdings are dimensionless index units. No nominal investment, balances,
contributions, tax, rounding to trading lots or annual rebalance is simulated.
"""
import argparse
from bisect import bisect_right
from collections import defaultdict
import csv
import gzip
from html.parser import HTMLParser
import json
import math

from stage1_pit import ROOT, OUT, DATES, gzread, gzwrite, dump

INITIAL = 'CCRO3 WEGE3 ITUB4 BBDC4 TBLE3 CMIG4 HYPE3 RADL3'.split()
ALIASES = {'MOTV3':'CCRO3', 'EGIE3':'TBLE3'}


def quotes():
    result = {}
    for y in range(2014, 2027):
        for r in gzread(OUT/f'cache/owned_quotes_{y}.json.gz')['quotes']:
            t = ALIASES.get(r['ticker'], r['ticker'])
            key = (t, r['date'])
            if key in result: raise ValueError(('Overlapping aliases/duplicate quote', key))
            result[key] = r['close']
    return result


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self, tag, attrs):
        if tag=='tr': self.row=[]
        if tag in ('td','th'): self.cell=[]
    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in ('td','th') and self.cell is not None:
            if self.row is not None: self.row.append(' '.join(''.join(self.cell).split()))
            self.cell=None
        if tag=='tr' and self.row is not None:
            self.rows.append(self.row); self.row=None


def freeze_events():
    """Extract owned events from existing caches; explicit replacements avoid double counting."""
    prices=quotes(); calendar=sorted({d for t,d in prices if t=='ITUB4'})
    market=gzread(OUT/'cache/market.json.gz'); events=[]
    def add(t,day,kind,source,**kw):
        events.append(dict(id=f'{t}_{day}_{kind}_{len(events)}',ticker=t,ex_date=day,kind=kind,source=source,**kw))
    def next_session(day): return calendar[bisect_right(calendar,day)]
    for t in INITIAL:
        current={'CCRO3':'MOTV3','TBLE3':'EGIE3'}.get(t,t)
        isins={r['isin_code'] for r in market['isins'] if r['ticker']==current}
        for e in market['actions']:
            if e['isin_code'] not in isins or not DATES[2014]<=e['event_date']<DATES[2026]: continue
            if e['event_type'] not in ('CASH_DIVIDEND','JCP'): continue
            if t=='BBDC4' and e['event_date']>='2017-01-01': continue # full official rows below
            if t=='CMIG4' and e['event_date']<'2023-01-01': continue # full official rows below
            add(t,next_session(e['event_date']),'DISTRIBUTION','cache/market.json.gz; SQLite corporate_actions/B3',
                amount=e['value'],record_date=e['event_date'],isin=e['isin_code'],original_type=e['event_type'])
    # Official Bradesco rows preserve multiple tranches on the same record date.
    parser=Tables(); parser.feed(gzip.decompress((OUT/'originals/bradesco_remuneracao.html.gz').read_bytes()).decode())
    for row in parser.rows:
        if len(row)<6 or not row[5].startswith('R$'): continue
        try:
            d,m,y=row[2].split('/'); day=f'{y}-{m}-{d}'; amount=float(row[5][2:].replace('.','').replace(',','.'))
        except ValueError: continue
        if '2017-01-01'<=day<DATES[2026]:
            add('BBDC4',next_session(day),'DISTRIBUTION','https://www.bradescori.com.br/informacoes-ao-mercado/remuneracao-aos-acionistas/',
                amount=amount,record_date=day,original_type=row[1],payment_date=row[3])
    cemig='https://api.mziq.com/mzfilemanager/v2/d/716a131f-9624-452c-9088-0cd6983c1349/a2eb9f5f-37e1-8913-c1eb-c4281b5e23b2?origin=2'
    for day,amount in [
        ('2014-11-10',.874208588),('2014-12-29',.182789068),('2015-05-04',.450866721),
        ('2016-01-04',.158947016),('2016-05-02',.344889593),('2016-12-27',.301999330),
        ('2017-05-15',.243559559),('2018-05-02',.500288822),('2018-12-26',.144013969),
        ('2019-05-06',.450798011),('2019-12-26',.27431232108),('2020-08-03',.24974833850),
        ('2020-09-28',.07904259285),('2021-01-04',.28553346242),('2021-05-03',.61169613494),
        ('2021-12-22',.56435026590),('2022-03-29',.14473821881),('2022-05-02',.59741792736),
        ('2022-06-27',.160416299),('2022-09-26',.21428027494),('2022-12-22',.18114181218),('2022-12-28',.23426869112)]:
        add('CMIG4',day,'DISTRIBUTION',cemig,amount=amount,entitlement='pre-event units; PN')
    # Curated structural list replaces, rather than supplements, the incomplete B3 list.
    structural={
      'WEGE3':[('2015-04-01',2),('2018-04-25',1.3),('2021-04-28',2)],
      'ITUB4':[('2015-07-14',1.1),('2016-10-18',1.1),('2018-11-21',1.5),('2025-03-18',1.1),('2025-12-26',1.03)],
      'BBDC4':[('2015-03-27',1.2),('2016-04-18',1.1),('2017-05-02',1.1),('2018-04-02',1.1),('2019-04-01',1.2),('2020-04-14',1.1),('2021-04-19',1.1),('2022-04-19',1.1)],
      'TBLE3':[('2018-12-12',1.25),('2025-11-27',1.4)],
      'CMIG4':[('2020-08-03',1.04113103206),('2021-05-03',1.11496899948),('2022-05-02',1.29999999976),('2024-04-30',1.3000000002726)],
      'RADL3':[('2020-09-21',5),('2023-05-22',1.04),('2025-12-23',1.02)]}
    sources={
      'WEGE3':'https://ri.weg.net/4433-2/; owned_capital_events_fre.json; B3',
      'ITUB4':'https://www.itau.com.br/relacoes-com-investidores/informacoes-ao-mercado/recompra/; owned_capital_events_fre.json; B3',
      'BBDC4':'originals/bradesco_remuneracao.html.gz; owned_capital_events_fre.json; SEC 6K 20150317/20160404/20180319/20200403',
      'TBLE3':'originals/engie_bonus_2018_doe.pdf.gz p34; owned_capital_events_fre.json; B3 2025-11-26',
      'CMIG4':cemig+'; owned_capital_events_fre.json; B3 2024-04-29',
      'RADL3':'https://ri.rd.com.br/Download.aspx?Arquivo=HFkRorg9OyPF+k5NkdNbXw%3D%3D; originals/radl_bonus_2023.pdf.gz; owned_capital_events_fre.json; B3'}
    for t,items in structural.items():
        for day,factor in items: add(t,day,'SHARES',sources[t],factor=factor)
    add('CMIG4','2017-10-27','RIGHT','https://ri.cemig.com.br/docs/cemig-2017-10-26-NBfWkJHw.pdf',
        successor='CMIG2',ratio=.158876242)
    add('CMIG2','2017-10-30','RIGHT_REINVEST','COTAHIST_A2017.ZIP; first traded close',successor='CMIG4')
    add('ITUB4','2021-10-04','SPINOFF','B3 OC 108/2021-PRE',successor='XPBR31',ratio=1/43.3128323)
    fx=json.loads((OUT/'originals/xp_gross_ptax.json').read_text())
    xp=json.loads((OUT/'bh_evidence.json').read_text())['xp_distributions']
    assert len(xp)==len(fx)
    for declared,f in zip(xp,fx):
        day,usd=declared['ex_date'],declared['usd']
        assert f['data']['value'][0]['dataHoraCotacao'].startswith(day)
        rate=f['data']['value'][0]['cotacaoVenda']
        add('XPBR31',day,'DISTRIBUTION',declared['source'],
            amount=usd*rate,usd_per_bdr=usd,ptax_venda=rate,fx_source=f['url'])
    events.sort(key=lambda e:(e['ex_date'],e['ticker'],e['kind'],e['id']))
    gzwrite(OUT/'cache/bh_owned_events.json.gz',events)
    return events


def apply_day(units, events, prices, day):
    """Apply old entitlements simultaneously; spawned rights are real positions."""
    before=units.copy(); after=units.copy(); grouped=defaultdict(list)
    if len({e['id'] for e in events})!=len(events): raise ValueError('Duplicate event')
    for e in events:
        if e['ex_date']!=day: raise ValueError('Event date mismatch')
        grouped[e['ticker']].append(e)
    for t,items in grouped.items():
        if t not in before: raise ValueError(('Event for unheld security',t,day))
        q=before[t]; multiplier=1.; distribution=0.
        for e in items:
            kind=e['kind']
            if kind=='SHARES': multiplier*=e['factor']
            elif kind=='DISTRIBUTION': distribution+=e['amount']
            elif kind in ('SPINOFF','RIGHT'):
                child=e['successor']; after[child]=after.get(child,0.)+q*e['ratio']
            elif kind=='RIGHT_REINVEST':
                child=e['successor']; after[child]+=q*prices[t,day]/prices[child,day]; del after[t]
            else: raise ValueError(('Unsupported event',kind))
        if t in after:
            after[t]+=q*(multiplier-1)+(q*distribution/prices[t,day] if distribution else 0.)
    if any(v<0 or not math.isfinite(v) for v in after.values()): raise ValueError('Invalid units')
    return after


def trajectory(prices, events, initial, dates):
    if not math.isclose(math.fsum(initial.values()),1): raise ValueError('Initial weights must sum to one')
    units={t:w/prices[t,dates[0]] for t,w in initial.items()}
    june=[]; ledger=[]; bydate=defaultdict(list); seen=set()
    for e in events:
        if e['id'] in seen: raise ValueError('Duplicate economic event')
        seen.add(e['id'])
        if dates[0]<e['ex_date']<=dates[-1]: bydate[e['ex_date']].append(e)
    for day in sorted(set(dates)|bydate.keys()):
        if day in bydate:
            before=units.copy(); units=apply_day(units,bydate[day],prices,day)
            for t in sorted(before.keys()|units.keys()):
                if before.get(t)!=units.get(t):
                    ledger.append(dict(date=day,ticker=t,units_before=before.get(t,0),units_after=units.get(t,0),
                        event_ids=';'.join(e['id'] for e in bydate[day])))
        if day in dates:
            nav=math.fsum(q*prices[t,day] for t,q in units.items())
            for t,q in sorted(units.items()):
                june.append(dict(date=day,ticker=t,units=q,nominal_close=prices[t,day],index_component=q*prices[t,day],index_total=nav,weight=q*prices[t,day]/nav))
    return june,ledger


def run():
    prices=quotes(); events=gzread(OUT/'cache/bh_owned_events.json.gz')
    selected=list(csv.DictReader((OUT/'bh_selection_2014.csv').open()))
    initial={r['ticker']:float(r['initial_weight']) for r in selected}
    if set(initial)!=set(INITIAL) or len(selected)!=8:raise ValueError('2014 selection requires review')
    positions,ledger=trajectory(prices,events,initial,list(DATES.values()))
    levels={r['date']:r['index_total'] for r in positions}
    ibov={int(r['year']):float(r['ibov_points']) for r in csv.DictReader((ROOT/'research/returns_2014_2026_results/ibov_june_closes.csv').open())}
    rows=[]
    attribution=[]
    for y in range(2014,2026):
        a,b=DATES[y],DATES[y+1]; r=100*(levels[b]/levels[a]-1); benchmark=100*(ibov[y+1]/ibov[y]-1)
        rows.append(dict(year=y,portfolio='BH padrão',start=a,end=b,return_pct=r,cumulative_pct=100*(levels[b]-1),
                         IBOV_pct=benchmark,excess_pp=r-benchmark,selection='2014_EIGHT_ISSUERS_EXPLICIT_CLASS_CONVENTION',
                         return_status='GROSS_CONTINUOUS_OWNED_RIGHTS'))
        for t in INITIAL:
            owned={t,'XPBR31'} if t=='ITUB4' else {t}
            left=math.fsum(x['index_component'] for x in positions if x['date']==a and x['ticker'] in owned)
            right=math.fsum(x['index_component'] for x in positions if x['date']==b and x['ticker'] in owned)
            attribution.append(dict(year=y,original_issuer_ticker=t,start=a,end=b,start_weight=left/levels[a],
                return_pct=100*(right/left-1),contribution_pp=100*(right-left)/levels[a],
                includes_successor='XPBR31' if t=='ITUB4' and b>='2021-10-04' else ''))
    dump('bh_annual_pct.csv',rows); dump('bh_june_positions.csv',positions); dump('bh_event_ledger.csv',ledger)
    dump('bh_issuer_annual_pct.csv',attribution)
    # Variable event fields are normalized for a reviewable flat audit.
    fields=sorted(set().union(*(e.keys() for e in events)))
    dump('bh_owned_events.csv',[{k:e.get(k,'') for k in fields} for e in events])
    print(json.dumps(rows,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--freeze-events',action='store_true');a=p.parse_args()
    if a.freeze_events: freeze_events()
    run()
