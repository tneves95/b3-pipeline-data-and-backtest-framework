"""PR6 fiscal adapter. Economic loop derived from frozen PR5 simulate().

PR5 source is imported unchanged. The differences are fiscal hooks, restricted
cash, reduced June purchase budget and the separate hypothetical final sale.
"""
from monthly_contributions import *

def simulate(portfolio,quote=None,byday=None,compositions=None,end=END,monthly=2500.,protect=True,
             initial_exclude_bradesco=False, fiscal=None):
    """No observations of later performance participate in constituent choice."""
    if fiscal is None:raise ValueError('Explicit frozen fiscal policy required')
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

    for r in trades:
        fiscal.buy(r['date'],r['lineage'],r['ticker'],r['units'],r['close'],r['reason'])

    def values_now(day):
        values,missing=mark(book,quote,day)
        nav=None if missing else math.fsum(values.values())+cash-fiscal.liability
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
            tax_liability=fiscal.liability,tax_restricted_cash=fiscal.reserve(),cash_available=fiscal.available(cash),tax_paid=sum(fiscal.paid_by_code.values())+fiscal.withheld,active_lineages=n,physical_securities=sum(len(u) for u in book.values()),
            maximum_lineage_weight=max(weights) if weights else None,hhi=sum(w*w for w in weights) if weights else None,
            twr_cumulative_pct=100*(twr-1) if not twr_missing else None,
            valuation_status='MISSING_EXACT_CLOSE:'+','.join(missing) if missing else 'EXACT_B3_CLOSE'))

    def buy_cash(day,amount,reason):
        nonlocal cash
        amount=min(amount,fiscal.available(cash))
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
            fiscal.buy(day,c,t,q,quote[t,day],reason)
            trades.append(dict(portfolio=portfolio,date=day,lineage=c,ticker=t,side='BUY',units=q,
                close=quote[t,day],amount=v,reason=reason,voluntary_sale=False))
        cash-=spend
        if abs(cash)<1e-8:cash=0.
        return spend,'INVESTED' if math.isclose(spend,amount,abs_tol=1e-8) else 'NO_BUYABLE_DEFICIT_RETAIN_CASH'

    record(START,'INITIAL',100000.,[])
    for day in sorted(sampledays|{d for d in byday if START<d<=end}):
        if day==START:continue
        cash-=fiscal.payment(day,cash)
        if fiscal.enabled and abs(cash)<1e-8:cash=0.
        if day in monthends:cash-=fiscal.assess(day,month_closed=True)
        if day in byday:
            held={t for u in book.values() for t in u}
            spawned={e['successor'] for e in byday[day] if e['kind']=='RIGHT' and e['ticker'] in held}
            relevant=[e for e in byday[day] if e['ticker'] in held or (e['kind']=='RIGHT_REINVEST' and e['ticker'] in spawned)]
            for e in relevant:
                if e['id'] in seen:raise ValueError('Duplicate processed event')
                seen.add(e['id'])
            before={c:u.copy() for c,u in book.items()}
            book,buyers,principal,led=process_events(book,buyers,quote,relevant,day)
            book,fiscal_cash=fiscal.corporate(day,before,book,relevant,quote,principal,month_closed=day in monthends)
            cash+=fiscal_cash
            event_ledger.extend(dict(portfolio=portfolio,**r) for r in led)
            shadow,shadow_buyers,shadow_principal,_=process_events(shadow,shadow_buyers,quote,byday[day],day)
            # The shadow measures each maintained issuer's own total return.
            # Principal from a different redeemed issuer is an internal funding
            # transfer in the actual book, not return earned by its recipients.
            if principal:
                cash+=principal
                spent,why=buy_cash(day,principal,'COMPULSORY_REDEMPTION_REINVESTMENT')
                event_ledger.append(dict(portfolio=portfolio,date=day,lineage='REDEMPTION_CASH',ticker='',units_before=0,
                    units_after=0,event_ids=';'.join(e['id'] for e in relevant if e['kind']=='REDEMPTION'),
                    event_kinds='REDEMPTION_CASH',external_flow=0,source='Accepted compulsory redemption',
                    cash_in=principal,cash_reinvested=spent,status=why))
        fiscal.verify(book)
        fiscal.available(cash)
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
            sales=0.;buys=0.;tax_cost_before=fiscal.withheld+fiscal.liability
            for c in sorted(book):
                value=values[c];target=targets.get(c,0)
                if value>target+1e-8:
                    fraction=(value-target)/value
                    for t,q in list(book[c].items()):
                        sold=q*fraction;amount=sold*quote[t,day];book[c][t]-=sold;cash+=amount;sales+=amount
                        fiscal.sell(day,c,t,sold,quote[t,day],'JUNE_REVIEW')
                        trades.append(dict(portfolio=portfolio,date=day,lineage=c,ticker=t,side='SELL',units=sold,
                            close=quote[t,day],amount=amount,reason='JUNE_COMPOSITION_REBALANCE' if changed else 'JUNE_EXCESS_ABOVE_TWO_TIMES',voluntary_sale=True))
                    if target==0:book.pop(c)
            cash-=fiscal.assess(day,month_closed=day in monthends)
            buyers=desired
            deficits={c:max(0.,targets[c]-math.fsum(q*quote[t,day] for t,q in book.get(c,{}).items())) for c in desired}
            total_deficit=math.fsum(deficits.values())
            scale=min(1.,fiscal.available(cash)/total_deficit) if total_deficit else 1.
            if scale<1-1e-12:
                targets={c:targets[c]-deficits[c]*(1-scale) for c in desired}
            for c in sorted(desired):
                now=math.fsum(q*quote[t,day] for t,q in book.get(c,{}).items());amount=max(0,targets[c]-now)
                if amount<=1e-8:continue
                t=buyers[c];q=amount/quote[t,day];book.setdefault(c,{})[t]=book.get(c,{}).get(t,0)+q
                cash-=amount;buys+=amount
                fiscal.buy(day,c,t,q,quote[t,day],'JUNE_REVIEW')
                trades.append(dict(portfolio=portfolio,date=day,lineage=c,ticker=t,side='BUY',units=q,
                    close=quote[t,day],amount=amount,reason='JUNE_COMPOSITION_REBALANCE' if changed else 'JUNE_EXCESS_REINVESTMENT',voluntary_sale=False))
            if abs(cash)<1e-7:cash=0.
            actual,miss,after=values_now(day)
            expected=nav-((fiscal.withheld+fiscal.liability)-tax_cost_before)
            if not math.isclose(expected,after,rel_tol=3e-12):raise ValueError(('June NAV/tax does not reconcile',expected,after))
            if fiscal.enabled:
                tax_factor=after/nav
                if not twr_missing:twr*=tax_factor
                if annual and annual[-1]['date']==day:
                    if annual[-1]['twr_pct'] is not None:
                        annual[-1]['twr_pct']=100*((1+annual[-1]['twr_pct']/100)*tax_factor-1)
                    annual[-1]['twr_cumulative_pct']=100*(twr-1) if not twr_missing else None
                    annual[-1]['nav']=after
            fiscal.verify(book)
            fiscal.available(cash)
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
    liquidation=fiscal.final_liquidation(end,book,quote,cash)
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
    summary.update(darf_paid=sum(fiscal.paid_by_code.values()),irrf_paid=fiscal.withheld,
        tax_paid=sum(fiscal.paid_by_code.values())+fiscal.withheld,unpaid_liability=fiscal.liability,
        restricted_cash=fiscal.reserve(),cash_available=fiscal.available(cash),income_withheld=fiscal.income_withheld,
        liquidation_wealth=liquidation['wealth'],liquidation_tax=liquidation['tax_increment'],
        liquidation_xirr_pct=100*xirr(flows[:-1]+[(end,liquidation['wealth'])]),
        remaining_acquisition_basis=math.fsum(fiscal.basis.values()))
    return dict(fiscal=fiscal,liquidation=liquidation,book=book,summary=summary,contributions=contributions,trades=trades,positions=position_rows,wealth=wealth,
        event_ledger=event_ledger,junes=junes,annual=annual,flows=flows)
