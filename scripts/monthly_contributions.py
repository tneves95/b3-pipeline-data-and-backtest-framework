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
from bisect import bisect_right

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
    # The new BH owns BBSE before it was ever admitted to the old B00S.
    # Reuse the frozen underlying B3 rows and the accepted next-session rule.
    known={e['id'] for e in all_events}
    for e in gzread(OUT/'cache/continuation_events.json.gz'):
        if e['ticker']=='BBSE3' and e['ex_date']<=DATES[2015] and e['id'] not in known:
            all_events.append(e);known.add(e['id'])
    calendar=sorted(r['date'] for r in read(STUDY/'inputs/ibov_daily.csv'))
    raw=gzread(OUT/'cache/market.json.gz')
    for e in raw['actions']:
        if e['isin_code']=='BRBBSEACNOR5' and START<e['event_date']<DATES[2015] and e['event_type'] in ['CASH_DIVIDEND','JCP']:
            day=calendar[bisect_right(calendar,e['event_date'])]
            all_events.append(dict(id=f'PR5_BBSE3_{day}_{e["event_type"]}',ticker='BBSE3',ex_date=day,
                kind='DISTRIBUTION',amount=e['value'],record_date=e['event_date'],
                source='PR3 cache/market.json.gz; pre-existing B3 row; accepted next-session convention',
                qualification='Inherited B3 cache amount convention; not newly certified issuer remuneration'))
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


def waterfill(values, cash, buyers, total_nav=None):
    """Spend available cash proportionally to positive monetary deficits."""
    if cash<0:raise ValueError('Negative cash')
    active=sorted(values)
    if not active or not cash:return {},cash
    nav=math.fsum(values.values())+cash if total_nav is None else total_nav;target=nav/len(active)
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


def process_events(book, buyers, quote, event_list, day):
    """Apply each entitlement to the actual units, preserving economic lineage."""
    before={c:u.copy() for c,u in book.items()};buyers=buyers.copy();ledger=[];redemption=0.
    ordinary=[e for e in event_list if e['kind'] not in ['CONVERSION','REDEMPTION']]
    after={}
    for c,u in before.items():
        spawned={e['successor'] for e in ordinary if e['kind']=='RIGHT' and e['ticker'] in u}
        relevant=[e for e in ordinary if e['ticker'] in u or (e['kind']=='RIGHT_REINVEST' and e['ticker'] in spawned)]
        after[c]=event_day(u,relevant,quote,day)
    for e in event_list:
        t=e['ticker']
        for c,u in after.items():
            if t not in before[c]:continue
            q=before[c][t]
            if e['kind']=='CONVERSION':
                actual=u.pop(t)
                for child,ratio in e['legs']:u[child]=u.get(child,0)+actual*ratio
                if e.get('amount'):
                    child=e['legs'][0][0];u[child]+=q*e['amount']/quote[child,day]
                if buyers.get(c)==t:buyers[c]=e['legs'][0][0]
            elif e['kind']=='REDEMPTION':
                actual=u.pop(t);redemption+=actual*e['amount']
                if buyers.get(c)==t:buyers.pop(c)
    for c in before:
        spawned={e['successor'] for e in ordinary if e['kind']=='RIGHT' and e['ticker'] in before[c]}
        relevant=[e for e in event_list if e['ticker'] in before[c] or (e['kind']=='RIGHT_REINVEST' and e['ticker'] in spawned)]
        if not relevant:continue
        for t in sorted(set(before[c])|set(after[c])):
            if before[c].get(t,0)!=after[c].get(t,0):
                ledger.append(dict(date=day,lineage=c,ticker=t,units_before=before[c].get(t,0),
                    units_after=after[c].get(t,0),event_ids=';'.join(e['id'] for e in relevant),
                    event_kinds=';'.join(sorted({e['kind'] for e in relevant})),external_flow=0,
                    source=';'.join(sorted({e['source'] for e in relevant}))))
    return after,buyers,redemption,ledger


def mark(book,quote,day):
    values={};missing=[]
    for c,u in book.items():
        absent=[t for t,q in u.items() if q and (t,day) not in quote]
        if absent:missing.extend(absent);values[c]=None
        else:values[c]=math.fsum(q*quote[t,day] for t,q in u.items())
    return values,sorted(set(missing))


def simulate(portfolio,quote=None,byday=None,compositions=None,end=END,monthly=2500.,protect=True,
             initial_exclude_bradesco=False):
    """No observations of later performance participate in constituent choice."""
    if quote is None:quote,_=load_quotes()
    byday=events() if byday is None else byday
    compositions=frozen_compositions() if compositions is None else compositions
    wanted=compositions[portfolio,2014].copy()
    bradesco='60746948000112'
    if initial_exclude_bradesco:wanted={c:t for c,t in wanted.items() if t!='BBDC4'}
    buyers=wanted.copy();book={c:{t:100000/len(wanted)/quote[t,START]} for c,t in wanted.items()}
    shadow={c:u.copy() for c,u in book.items()};shadow_buyers=buyers.copy()
    shadow_initial={c:100000/len(wanted) for c in wanted};cash=0.;external=100000.
    calendar=read(STUDY/'contribution_calendar.csv')
    deposits={r['date']:monthly for r in calendar if r['date']<=end}
    monthends={r['month_end'] for r in calendar if r['month_end']<=end}
    reviews={d for y,d in DATES.items() if 2015<=y<=2025 and d<=end and portfolio not in ['BH padrão','BESST-10 BH']}
    sampledays={START,end}|set(deposits)|monthends|reviews
    flows=[(START,-100000.)];trades=[];position_rows=[];wealth=[];contributions=[];event_ledger=[];junes=[];annual=[]
    twr=1.;annual_twr=1.;previous_nav=100000.;twr_missing=[];period_missing=[];seen=set();turnover=0.;last_year=2014
    invested_external=100000.
    for c,t in sorted(wanted.items()):
        trades.append(dict(portfolio=portfolio,date=START,lineage=c,ticker=t,side='BUY',units=book[c][t],
            close=quote[t,START],amount=100000/len(wanted),reason='INITIAL_EQUAL_ALLOCATION',voluntary_sale=False))

    def values_now(day):
        values,missing=mark(book,quote,day)
        nav=None if missing else math.fsum(values.values())+cash
        return values,missing,nav

    def record(day,phase,nav,missing):
        values,_,_=values_now(day);n=len(buyers)
        for c,u in sorted(book.items()):
            for t,q in sorted(u.items()):
                price=quote.get((t,day));value=q*price if price is not None else None
                position_rows.append(dict(portfolio=portfolio,date=day,phase=phase,lineage=c,ticker=t,units=q,
                    close=price,position_value=value,lineage_value=values[c],nav=nav,
                    security_weight=value/nav if value is not None and nav else None,
                    lineage_weight=values[c]/nav if values[c] is not None and nav else None,
                    target_weight=1/n if c in buyers and n else 0,limit_weight=2/n if n>15 and protect else None,
                    monthly_buy_target=t==buyers.get(c),valuation_status='MISSING_EXACT_CLOSE' if price is None else 'EXACT_B3_CLOSE'))
        weights=[v/nav for c,v in values.items() if v and nav]
        wealth.append(dict(portfolio=portfolio,date=day,phase=phase,nav=nav,cash=cash,external_capital=external,
            active_lineages=n,physical_securities=sum(len(u) for u in book.values()),
            maximum_lineage_weight=max(weights) if weights else None,hhi=sum(w*w for w in weights) if weights else None,
            twr_cumulative_pct=100*(twr-1) if not twr_missing else None,
            valuation_status='MISSING_EXACT_CLOSE:'+','.join(missing) if missing else 'EXACT_B3_CLOSE'))

    def buy_cash(day,amount,reason):
        nonlocal cash
        values,missing,nav=values_now(day)
        if missing:return 0.,'UNVALUED_POSITION:'+','.join(missing)
        active={c:values.get(c,0) for c in buyers}
        available={c for c,t in buyers.items() if (t,day) in quote}
        # Include inactive descendants in total NAV rather than multiplying targets.
        alloc,left=waterfill(active,amount,available,total_nav=nav)
        spend=min(amount,math.fsum(alloc.values()))
        if alloc:
            total=math.fsum(alloc.values());alloc={c:v*spend/total for c,v in alloc.items()}
            last=sorted(alloc)[-1];alloc[last]=spend-math.fsum(v for c,v in alloc.items() if c!=last)
        for c,v in alloc.items():
            t=buyers[c];q=v/quote[t,day];book.setdefault(c,{})[t]=book.get(c,{}).get(t,0)+q
            trades.append(dict(portfolio=portfolio,date=day,lineage=c,ticker=t,side='BUY',units=q,
                close=quote[t,day],amount=v,reason=reason,voluntary_sale=False))
        cash-=spend
        if abs(cash)<1e-8:cash=0.
        return spend,'INVESTED' if math.isclose(spend,amount,abs_tol=1e-8) else 'NO_BUYABLE_DEFICIT_RETAIN_CASH'

    record(START,'INITIAL',100000.,[])
    for day in sorted(sampledays|{d for d in byday if START<d<=end}):
        if day==START:continue
        if day in byday:
            held={t for u in book.values() for t in u}
            spawned={e['successor'] for e in byday[day] if e['kind']=='RIGHT' and e['ticker'] in held}
            relevant=[e for e in byday[day] if e['ticker'] in held or (e['kind']=='RIGHT_REINVEST' and e['ticker'] in spawned)]
            for e in relevant:
                if e['id'] in seen:raise ValueError('Duplicate processed event')
                seen.add(e['id'])
            book,buyers,principal,led=process_events(book,buyers,quote,relevant,day)
            event_ledger.extend(dict(portfolio=portfolio,**r) for r in led)
            shadow,shadow_buyers,shadow_principal,_=process_events(shadow,shadow_buyers,quote,byday[day],day)
            if shadow_principal:
                sv,sm=mark(shadow,quote,day)
                if sm:raise ValueError(('Unpriced shadow redemption',sm))
                total=math.fsum(sv.values())
                for c,u in shadow.items():
                    for t,q in list(u.items()):u[t]+=shadow_principal*q/total
            if principal:
                cash+=principal
                spent,why=buy_cash(day,principal,'COMPULSORY_REDEMPTION_REINVESTMENT')
                event_ledger.append(dict(portfolio=portfolio,date=day,lineage='REDEMPTION_CASH',ticker='',units_before=0,
                    units_after=0,event_ids=';'.join(e['id'] for e in relevant if e['kind']=='REDEMPTION'),
                    event_kinds='REDEMPTION_CASH',external_flow=0,source=f'principal={principal}; invested={spent}; {why}'))
        if day not in sampledays:continue
        values,missing,nav=values_now(day)
        if missing or previous_nav is None:
            # A missing mark matters for TWR only if an external flow intervenes.
            if day in deposits:
                if deposits[day]:twr_missing.append(day);period_missing.append(day)
        elif not period_missing:
            annual_twr*=nav/previous_nav
        if nav is not None and previous_nav is not None and not twr_missing:twr*=nav/previous_nav
        if day in deposits:
            record(day,'BEFORE_DEPOSIT',nav,missing)
            amount=deposits[day];cash+=amount;external+=amount;flows.append((day,-amount))
            after_nav=nav+amount if nav is not None else None
            spent,why=buy_cash(day,cash,'MONTHLY_DEFICIT_BUY') if monthly else (0.,'ZERO_CONTRIBUTION_VALIDATION')
            invested_external+=spent
            contributions.append(dict(portfolio=portfolio,date=day,external_deposit=amount,investor_cash_flow=-amount,
                nav_before=nav,nav_after=after_nav,invested_cash=spent,cash_after=cash,status=why))
            nav=after_nav
            actual_values,actual_missing,actual_nav=values_now(day)
            if nav is not None and not math.isclose(nav,actual_nav,rel_tol=3e-12):
                raise ValueError(('Contribution NAV does not reconcile',portfolio,day,nav,actual_nav))
            record(day,'AFTER_DEPOSIT',nav,missing)
        if day in monthends or day==end:
            record(day,'MONTH_END',nav,missing)
        if day in DATES.values() and day>START:
            y=int(day[:4])
            annual.append(dict(portfolio=portfolio,formation_year=last_year,closing_year=y,date=day,nav=nav,
                external_capital=external,twr_pct=100*(annual_twr-1) if not period_missing else None,
                twr_cumulative_pct=100*(twr-1) if not twr_missing else None,
                status='ND_UNVALUED_FLOW_DATE:'+','.join(period_missing) if period_missing else 'EXACT_FLOW_ADJUSTED_TWR'))
            annual_twr=1.;period_missing=[];last_year=y
        if day in reviews:
            if missing:raise ValueError(('Unvalued June review',portfolio,day,missing))
            y=int(day[:4]);desired=compositions[portfolio,y].copy()
            entries=set(desired)-set(buyers);exits=set(buyers)-set(desired)
            sv,sm=mark(shadow,quote,day)
            if sm:raise ValueError(('Unpriced trailing return',sm))
            trailing={c:sv.get(c,0)/v-1 for c,v in shadow_initial.items() if v and c in buyers}
            # Include the entire marked book and cash in the rebalance capital.
            current={c:values.get(c,0) for c in buyers}
            current['UNALLOCATED_CASH']=cash+math.fsum(v for c,v in values.items() if c not in buyers)
            changed=bool(entries or exits)
            targets,protected=june_targets(current,set(desired),trailing,changed,protect)
            sales=0.;buys=0.
            for c in sorted(book):
                value=values[c];target=targets.get(c,0)
                if value>target+1e-8:
                    fraction=(value-target)/value
                    for t,q in list(book[c].items()):
                        sold=q*fraction;amount=sold*quote[t,day];book[c][t]-=sold;cash+=amount;sales+=amount
                        trades.append(dict(portfolio=portfolio,date=day,lineage=c,ticker=t,side='SELL',units=sold,
                            close=quote[t,day],amount=amount,reason='JUNE_COMPOSITION_REBALANCE' if changed else 'JUNE_EXCESS_ABOVE_TWO_TIMES',voluntary_sale=True))
                    if target==0:book.pop(c)
            buyers=desired
            for c in sorted(desired):
                now=math.fsum(q*quote[t,day] for t,q in book.get(c,{}).items());amount=max(0,targets[c]-now)
                if amount<=1e-8:continue
                t=buyers[c];q=amount/quote[t,day];book.setdefault(c,{})[t]=book.get(c,{}).get(t,0)+q
                cash-=amount;buys+=amount
                trades.append(dict(portfolio=portfolio,date=day,lineage=c,ticker=t,side='BUY',units=q,
                    close=quote[t,day],amount=amount,reason='JUNE_COMPOSITION_REBALANCE' if changed else 'JUNE_EXCESS_REINVESTMENT',voluntary_sale=False))
            if abs(cash)<1e-7:cash=0.
            actual,miss,after=values_now(day)
            if not math.isclose(nav,after,rel_tol=3e-12):raise ValueError(('June NAV changed',nav,after))
            turnover+=min(sales,buys)/nav
            for c in sorted(set(values)|set(desired)):
                junes.append(dict(portfolio=portfolio,date=day,lineage=c,ticker=desired.get(c,''),
                    before=values.get(c,0),after=actual.get(c,0),entry=c in entries,exit=c in exits,
                    trailing_12m_return=trailing.get(c),winner_protected=c in protected,N=len(buyers),
                    sales_total=sales,buys_total=buys,turnover=min(sales,buys)/nav,
                    reason='CONSTITUENT_CHANGE' if changed else 'NO_COMPOSITION_CHANGE'))
            record(day,'AFTER_JUNE_REVIEW',after,miss)
            shadow={c:u.copy() for c,u in book.items()};shadow_buyers=buyers.copy()
            shadow_initial=actual.copy();nav=after
        previous_nav=nav if nav is not None else previous_nav
        if cash< -1e-6 or any(q< -1e-10 for u in book.values() for q in u.values()):raise ValueError('Negative balance')
    final_values,missing,final=values_now(end)
    if missing:raise ValueError(('Unvalued final portfolio',missing))
    flows.append((end,final));years=(date.fromisoformat(end)-date.fromisoformat(START)).days/365.25
    summary=dict(portfolio=portfolio,end=end,final_wealth=final,external_capital=external,
        gain_after_external_capital=final-external,xirr_pct=100*xirr(flows),
        twr_pct=100*(twr-1) if not twr_missing else None,
        twr_cagr_pct=100*(twr**(1/years)-1) if not twr_missing else None,
        twr_status='ND_UNVALUED_FLOW_DATE:'+','.join(twr_missing) if twr_missing else 'EXACT_FLOW_ADJUSTED_TWR',
        cash=cash,external_contributions=len(deposits),active_lineages=len(buyers),
        maximum_lineage_weight=max(final_values.values())/final,
        lineage_hhi=sum((v/final)**2 for v in final_values.values()),june_turnover_sum=turnover,
        events_processed=len(seen),voluntary_sales=sum(r['side']=='SELL' for r in trades),
        buy_operations=sum(r['side']=='BUY' for r in trades),
        ranking_status='CONDITIONAL_NET_MISSING_ON_SCENARIO' if portfolio=='BESST-10 BH' else 'FROZEN_PR4_OR_BH_SELECTION')
    return dict(summary=summary,contributions=contributions,trades=trades,positions=position_rows,wealth=wealth,
        event_ledger=event_ledger,junes=junes,annual=annual,flows=flows)


def benchmark(end=END,monthly=2500.):
    points={r['date']:float(r['close']) for r in read(STUDY/'inputs/ibov_daily.csv')}
    calendar=[r for r in read(STUDY/'contribution_calendar.csv') if r['date']<=end]
    units=100000/points[START];flows=[(START,-100000.)];wealth=[];contributions=[];positions=[];external=100000.
    trades=[dict(portfolio='IBOV',date=START,lineage='IBOV',ticker='IBOV',side='BUY',units=units,
        close=points[START],amount=100000.,reason='INITIAL_EQUAL_ALLOCATION',voluntary_sale=False)]
    deposits={r['date']:monthly for r in calendar};monthends={r['month_end'] for r in calendar}
    for day in sorted({START,end}|set(deposits)|monthends):
        before=units*points[day]
        if day in deposits:
            amount=deposits[day];units+=amount/points[day];external+=amount;flows.append((day,-amount))
            contributions.append(dict(portfolio='IBOV',date=day,external_deposit=amount,investor_cash_flow=-amount,
                nav_before=before,nav_after=before+amount,invested_cash=amount,cash_after=0.,status='FRACTIONAL_INDEX_POINTS'))
            trades.append(dict(portfolio='IBOV',date=day,lineage='IBOV',ticker='IBOV',side='BUY',units=amount/points[day],
                close=points[day],amount=amount,reason='MONTHLY_DEFICIT_BUY',voluntary_sale=False))
        value=units*points[day]
        wealth.append(dict(portfolio='IBOV',date=day,phase='INITIAL' if day==START else 'MONTH_END' if day in monthends else 'AFTER_DEPOSIT',
            nav=value,cash=0.,external_capital=external,active_lineages=1,physical_securities=1,
            maximum_lineage_weight=1.,hhi=1.,twr_cumulative_pct=100*(points[day]/points[START]-1),valuation_status='OFFICIAL_B3_IBOV'))
        positions.append(dict(portfolio='IBOV',date=day,phase=wealth[-1]['phase'],lineage='IBOV',ticker='IBOV',units=units,
            close=points[day],position_value=value,lineage_value=value,nav=value,security_weight=1.,lineage_weight=1.,
            target_weight=1.,limit_weight=None,monthly_buy_target=True,valuation_status='OFFICIAL_B3_IBOV'))
    final=units*points[end];flows.append((end,final));years=(date.fromisoformat(end)-date.fromisoformat(START)).days/365.25
    annual=[]
    for y in range(2015,int(end[:4])+1):
        day=DATES[y]
        if day>end:continue
        row=next(w for w in wealth if w['date']==day)
        annual.append(dict(portfolio='IBOV',formation_year=y-1,closing_year=y,date=day,nav=row['nav'],external_capital=row['external_capital'],
            twr_pct=100*(points[day]/points[DATES[y-1]]-1),twr_cumulative_pct=100*(points[day]/points[START]-1),status='OFFICIAL_B3_TOTAL_RETURN_INDEX'))
    summary=dict(portfolio='IBOV',end=end,final_wealth=final,external_capital=external,gain_after_external_capital=final-external,
        xirr_pct=100*xirr(flows),twr_pct=100*(points[end]/points[START]-1),
        twr_cagr_pct=100*((points[end]/points[START])**(1/years)-1),twr_status='OFFICIAL_B3_TOTAL_RETURN_INDEX',
        cash=0.,external_contributions=len(calendar),active_lineages=1,maximum_lineage_weight=1.,lineage_hhi=1.,
        june_turnover_sum=0.,events_processed=0,voluntary_sales=0,buy_operations=len(calendar)+1,ranking_status='BENCHMARK_SAME_DATED_EXTERNAL_FLOWS')
    return dict(summary=summary,contributions=contributions,trades=trades,positions=positions,wealth=wealth,event_ledger=[],junes=[],annual=annual,flows=flows)


if __name__=='__main__':coverage()
