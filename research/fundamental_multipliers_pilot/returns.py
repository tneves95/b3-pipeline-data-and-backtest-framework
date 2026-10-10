"""Independent shareholder accounting. Restricted trajectories stay local-only.

No use of adjusted prices, no invented terminal liquidation, no outcome exclusion
based on the direction of price changes. Certification requires reviewed coverage
of the complete economic window, not merely the absence of skipped B3 events.
"""
from __future__ import annotations
from bisect import bisect_right
from collections import defaultdict
import json
import math
from pathlib import Path
import pandas as pd
from .audit import HERE, ROOT, sha256
from .quotes import QuoteBook


def apply_events(units, cash, events, price):
    """Old entitlements are simultaneous; detached rights may settle later that day."""
    if len({e['id'] for e in events})!=len(events):
        raise ValueError('DUPLICATE_ECONOMIC_EVENT')
    before=units.copy();after=units.copy()
    groups=defaultdict(list)
    for e in events:
        groups[e['ticker']].append(e)
    for ticker,items in groups.items():
        if ticker not in before: continue
        quantity=before[ticker];multiplier=1.;distribution=0.
        terminal=[e for e in items if e['kind'] in ('CONVERSION','REDEMPTION','EXTINGUISHMENT')]
        if len(terminal)>1: raise ValueError('AMBIGUOUS_TERMINAL_EVENTS')
        for e in items:
            kind=e['kind']
            if kind=='SHARES': multiplier*=e['factor']
            elif kind=='DISTRIBUTION': distribution+=e['amount']
            elif kind in ('RIGHT','SPINOFF'):
                child=e['successor'];after[child]=after.get(child,0.)+quantity*e['ratio']
            elif kind in ('CONVERSION','REDEMPTION','RIGHT_REINVEST','EXTINGUISHMENT','NO_ENTITLEMENT'): pass
            else: raise ValueError('UNSUPPORTED_ECONOMIC_EVENT:'+kind)
        if terminal and (multiplier!=1 or distribution):
            raise ValueError('AMBIGUOUS_SAME_DAY_TERMINAL_ENTITLEMENTS')
        if terminal:
            e=terminal[0];after.pop(ticker)
            if e['kind']=='CONVERSION':
                for child,ratio in e['legs']:
                    after[child]=after.get(child,0.)+quantity*ratio
                cash+=quantity*e.get('amount',0.)
            elif e['kind']=='REDEMPTION': cash+=quantity*e['amount']
            elif not e.get('documented_zero'): raise ValueError('UNDOCUMENTED_ZERO_RECOVERY')
        else:
            after[ticker]+=quantity*(multiplier-1.)
            if distribution: after[ticker]+=quantity*distribution/price(ticker)
    for e in events:
        if e['kind']=='RIGHT_REINVEST' and e['ticker'] in after:
            right=e['ticker'];parent=e['successor'];q=after.pop(right)
            if parent not in after: raise ValueError('RIGHT_SETTLEMENT_WITHOUT_PARENT')
            after[parent]+=q*price(right)/price(parent)
    if cash<0 or any(not math.isfinite(q) or q<0 for q in after.values()):
        raise ValueError('INVALID_SHAREHOLDER_HOLDINGS')
    return after,cash


def replay(book, initial, initial_isin, start, target, events, *, expected_isins=None):
    """One original unit of wealth, gross fractional ex-date reinvestment."""
    session=book.calendar[bisect_right(book.calendar,target)-1]
    opening=book.trade(initial,start,isin=initial_isin,max_age_sessions=0)
    units={initial:1./opening['close']};cash=0.;ledger=[];by_day=defaultdict(list)
    isins=dict(expected_isins or {});isins[initial]=initial_isin
    relevant=[e for e in events if start<e['ex_date']<=session]
    if len({e['id'] for e in relevant})!=len(relevant): raise ValueError('DUPLICATE_EVENT_ID')
    for e in relevant: by_day[e['ex_date']].append(e)
    for day,items in sorted(by_day.items()):
        owned=[e for e in items if e['ticker'] in units]
        spawned={e['successor'] for e in owned if e['kind'] in ('RIGHT','SPINOFF')}
        owned += [e for e in items if e['kind']=='RIGHT_REINVEST' and e['ticker'] in spawned and e not in owned]
        if not owned: continue
        # Identity is checked at every event valuation and at each economic leg.
        def price(ticker):
            q=book.trade(ticker,day,isin=isins.get(ticker),exact=True)
            if ticker not in isins: isins[ticker]=q['isin']
            return q['close']
        before=units.copy();old_cash=cash
        units,cash=apply_events(units,cash,owned,price)
        ledger.append(dict(date=day,event_ids=';'.join(e['id'] for e in owned),
            units_before=json.dumps(before,sort_keys=True),units_after=json.dumps(units,sort_keys=True),
            cash_before=old_cash,cash_after=cash))
    ending=[]
    for ticker,quantity in units.items():
        q=book.trade(ticker,session,isin=isins.get(ticker),max_age_sessions=0)
        ending.append(dict(ticker=ticker,isin=q['isin'],date=q['date'],quantity=quantity,close=q['close'],wealth=quantity*q['close']))
    wealth=math.fsum(r['wealth'] for r in ending)+cash
    return dict(nominal_total_return=wealth-1.,wealth_multiple=wealth,
                endpoint_session=session,cash_at_endpoint=cash,events_applied=len(ledger)),ledger,ending


def scope_covers(scope,start,target):
    return scope.get('certified',False) and scope['start']<=start and target<=scope['end']


def evaluate(panel, readiness, book, events, scopes, skipped, output):
    """Preserve the full historical denominator including unresolved and distressed names."""
    scope_by_ticker={s['ticker']:s for s in scopes}
    event_by_ticker=defaultdict(list)
    for e in events: event_by_ticker[e['ticker']].append(e)
    rows=[];ledgers=[];positions=[]
    representatives=panel[panel.company_representative].set_index(['cnpj','formation_date'])
    for o in readiness.itertuples():
        p=representatives.loc[(o.cnpj,o.formation_date)]
        target=o.calendar_endpoint
        reasons=[]
        scope=scope_by_ticker.get(o.ticker,{})
        result={}
        if not o.calendar_complete:
            state='CENSORED';reasons.append('HORIZON_NOT_MATURED')
        else:
            state='UNCERTIFIED'
            if not o.same_security_near_endpoint:
                if not (scope_covers(scope,o.formation_date,target) and scope.get('audited_terminal_path')):
                    state='CENSORED'
                    reasons.append('SECURITY_EXIT_OR_SUSPENSION_REQUIRES_ECONOMIC_LINEAGE')
            if not scope_covers(scope,o.formation_date,target):
                reasons.append(scope.get('blocker','COMPLETE_EVENT_CATALOG_NOT_RECONCILED'))
            if p.identity_status!='UNIQUE_MAP_RECEIPT_UNAUDITED':
                reasons.append('FORMATION_IDENTITY_AMBIGUOUS')
            if scope.get('certified') and (scope.get('cnpj')!=o.cnpj or scope.get('isin')!=o.isin):
                reasons.append('HISTORICAL_ISSUER_OR_CLASS_CONFLICT')
            unresolved=skipped[(skipped.isin_code==o.isin)&(skipped.event_date>o.formation_date)&(skipped.event_date<=target)]
            resolved=set(scope.get('resolved_skipped_dates',[]))
            if any(d not in resolved for d in unresolved.event_date):
                reasons.append('UNRESOLVED_MATERIAL_SKIPPED_EVENT')
                state='CENSORED'
            if not reasons:
                try:
                    result,ledger,ending=replay(book,o.ticker,o.isin,o.formation_date,target,events)
                    state='CERTIFIED'
                    ledgers.extend(dict(cnpj=o.cnpj,formation_date=o.formation_date,horizon_years=o.horizon_years,**r) for r in ledger)
                    positions.extend(dict(cnpj=o.cnpj,formation_date=o.formation_date,horizon_years=o.horizon_years,**r) for r in ending)
                except ValueError as e: reasons.append(str(e).split(':')[0])
        rows.append(dict(year=int(o.formation_date[:4]),cnpj=o.cnpj,ticker=o.ticker,isin=o.isin,
            formation_date=o.formation_date,horizon_years=o.horizon_years,calendar_endpoint=target,
            calendar_complete=o.calendar_complete,status=state,exclusion_causes=';'.join(sorted(set(reasons))),
            statement_status=p.statement_status,financial_sector=p.financial_sector,sector=p.sector,
            scope_id=scope.get('id'),**result))
    frame=pd.DataFrame(rows)
    frame.to_csv(output/'return_certification_matrix.csv',index=False)
    pd.DataFrame(ledgers).to_csv(output/'certified_event_ledger.csv',index=False)
    pd.DataFrame(positions).to_csv(output/'certified_endpoint_holdings.csv',index=False)
    return frame
