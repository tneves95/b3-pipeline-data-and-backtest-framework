"""Scale raw-price shareholder returns without trusting price-detected splits.

All individual prices, events and returns are local-only. FRE is used to corroborate
share mechanics, never to change a genuine crash into an artificial split. The
observed exchange calendar determines record/ex dates and maturity sessions.
"""
from __future__ import annotations
from bisect import bisect_left,bisect_right
from collections import defaultdict
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import zipfile
import numpy as np
import pandas as pd
from ..audit import ROOT,HERE,sha256
from ..quotes import readonly_database
from ..returns import apply_events


class Prices:
    def __init__(self,source,round2):
        self.calendar=pd.read_csv(round2/'exchange_calendar.csv').date.tolist()
        self.conn=readonly_database(source/'b3_market_data.sqlite')
        raw=pd.read_sql_query("""SELECT ticker,isin_code isin,date,close,adj_close,quotation_factor
            FROM prices WHERE date>='2014-01-01' AND
            (substr(isin_code,7,2)='AC' OR substr(isin_code,7,4)='CDAM')""",self.conn)
        delta=readonly_database(round2/'quote_overlay.sqlite')
        overlay=pd.read_sql_query('SELECT ticker,isin,date,close,quotation_factor FROM quotes',delta);delta.close()
        # Original prices retain their adjusted comparator; overlay rows override raw values.
        d=raw.merge(overlay[['ticker','date','isin','close','quotation_factor']],on=['ticker','date'],how='outer',suffixes=('','_delta'))
        for field in ['isin','close','quotation_factor']:
            d[field]=d[field+'_delta'].combine_first(d[field]);d=d.drop(columns=field+'_delta')
        d=d.sort_values(['isin','date','ticker']).reset_index(drop=True)
        self.frame=d
        self.series={}
        for isin,g in d.groupby('isin',sort=False):
            if g.date.duplicated().any():
                # Two aliases trading simultaneously cannot be silently treated as one class.
                raise ValueError('Ambiguous same-ISIN daily quotes: '+isin)
            self.series[isin]=dict(dates=g.date.to_numpy(),prices=g.close.to_numpy(),
                tickers=g.ticker.to_numpy(),adjusted=g.adj_close.to_numpy(),factors=g.quotation_factor.to_numpy())
        self.tickers={t:g[['isin','date']].sort_values('date') for t,g in d.groupby('ticker',sort=False)}

    def next_session(self,record):
        n=bisect_right(self.calendar,record)
        return self.calendar[n] if n<len(self.calendar) else None

    def session(self,target):
        n=bisect_right(self.calendar,target)-1
        if n<0:raise ValueError('NO_HISTORICAL_SESSION')
        return self.calendar[n]

    def age(self,a,b):
        return bisect_right(self.calendar,b)-bisect_right(self.calendar,a)

    def trade(self,isin,day,max_age=5):
        s=self.series.get(isin)
        if s is None:raise ValueError('MISSING_SECURITY_QUOTES')
        i=int(np.searchsorted(s['dates'],day,side='right'))-1
        if i<0:raise ValueError('NO_TRADE_BEFORE_TARGET')
        age=self.age(s['dates'][i],day)
        if age>max_age:raise ValueError('SUSPENDED_OR_EXITED_SECURITY')
        price=float(s['prices'][i])
        if not math.isfinite(price) or price<=0:raise ValueError('NONPOSITIVE_PRICE')
        return dict(isin=isin,date=s['dates'][i],close=price,ticker=s['tickers'][i],
            adj_close=s['adjusted'][i],age_sessions=age)

    def isin_for_ticker(self,ticker,day,*,allow_future=False):
        g=self.tickers.get(ticker)
        if g is None:raise ValueError('MISSING_SUCCESSOR_IDENTITY')
        before=g[g.date<=day]
        if len(before) and self.age(before.iloc[-1].date,day)<=20:
            return before.iloc[-1]['isin']
        after=g[g.date>day]
        limit=60 if ticker.endswith(('1','2')) else 5
        if allow_future and len(after) and self.age(day,after.iloc[0].date)<=limit:
            return after.iloc[0]['isin']
        raise ValueError('SUCCESSOR_IDENTITY_NOT_OBSERVED_AT_EVENT')

    def observed_gap(self,isin,start,end):
        s=self.series[isin];dates=s['dates']
        a=int(np.searchsorted(dates,start,'left'));b=int(np.searchsorted(dates,end,'right'))
        positions=np.searchsorted(self.calendar,dates[a:b])
        return int(np.diff(positions).max()) if len(positions)>1 else 0

    def close(self):self.conn.close()


def fre_capital(source,wanted,output):
    """Stream pre-existing originals; retain unique issuer/class mechanics, not bases."""
    rows=[]
    for year in range(2014,2027):
        archive=source/'data/cvm'/f'fre_cia_aberta_{year}.zip'
        member=f'fre_cia_aberta_capital_social_desdobramento_{year}.csv'
        with zipfile.ZipFile(archive) as z:
            if member not in z.namelist():continue
            for r in csv.DictReader(io.TextIOWrapper(z.open(member),encoding='latin1'),delimiter=';'):
                cnpj=re.sub(r'\D','',r['CNPJ_Companhia'])
                kind=r.get('Tipo_Evento','')
                if cnpj not in wanted or kind not in ['Desdobramento','Grupamento','Bonificação']:continue
                date=r.get('Data_Aprovacao','')
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',date) or date<'2013-01-01':continue
                values={}
                for cls,field in [('ON','Ordinarias'),('PN','Preferenciais'),('ALL','Total')]:
                    stem='Quantidade_'+('Total_Acoes' if cls=='ALL' else 'Acoes_'+field)
                    try:a=float(r[stem+'_Antes_Aprovacao']);b=float(r[stem+'_Depois_Aprovacao'])
                    except (ValueError,KeyError):continue
                    if a>0 and b>0:values[cls]=b/a
                if not values:continue
                rows.append(dict(cnpj=cnpj,approved=date,kind=kind,ratios=values,
                    docid=r['ID_Documento'],source_member=member,
                    row_sha256=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()))
    grouped=defaultdict(list)
    for r in rows:grouped[(r['cnpj'],r['approved'],r['kind'])].append(r)
    unique=[]
    for key,g in sorted(grouped.items()):
        ratios={};ambiguous=False
        for cls in ['ON','PN','ALL']:
            values=[r['ratios'][cls] for r in g if cls in r['ratios']]
            if values:
                if max(values)/min(values)>1.02:ambiguous=True
                ratios[cls]=float(np.median(values))
        unique.append(dict(cnpj=key[0],approved=key[1],kind=key[2],ratios=ratios,
            ambiguous=ambiguous,docs=sorted({r['docid'] for r in g}),source_members=sorted({r['source_member'] for r in g})))
    (output/'fre_unique_capital_evidence.json').write_text(json.dumps(unique,ensure_ascii=False,indent=2)+'\n')
    return unique


def class_factor(r,ticker):
    ratios=r['ratios']
    if ticker.endswith('11'):
        values=[ratios[c] for c in ['ON','PN'] if c in ratios]
        if len(values)==2 and max(values)/min(values)>1.02:return None
        return values[0] if values else ratios.get('ALL')
    return ratios.get('ON' if ticker.endswith('3') else 'PN')


def build_events(book,source,round2,panel,output):
    mapping=pd.read_sql_query('SELECT * FROM company_isin_map',book.conn,dtype={'cnpj':str})
    issuer={isin:set(g.cnpj) for isin,g in mapping.groupby('isin_code')}
    for r in panel.itertuples():issuer.setdefault(r.isin,set()).add(r.cnpj)
    fre=fre_capital(source,set(panel.cnpj),output)
    by_issuer=defaultdict(list)
    for r in fre:by_issuer[r['cnpj']].append(r)
    cash=pd.read_sql_query("SELECT * FROM corporate_actions WHERE event_date>='2014-01-01'",book.conn)
    stock=pd.read_sql_query("SELECT * FROM stock_actions WHERE ex_date>='2014-01-01'",book.conn)
    skipped=pd.read_sql_query("SELECT * FROM skipped_events WHERE event_date>='2014-01-01'",book.conn)
    events=[];flags=[];counter=0
    def add(isin,day,kind,source_tag,**kw):
        nonlocal counter
        if day is None:return
        counter+=1;events.append(dict(id=f'R3_{counter}',ticker=isin,ex_date=day,kind=kind,source=source_tag,**kw))
    for r in cash.itertuples():
        if r.isin_code not in book.series:continue
        day=book.next_session(r.event_date)
        if r.event_type in ['CASH_DIVIDEND','JCP']:
            if r.value>0:add(r.isin_code,day,'DISTRIBUTION','B3_CASH_RECORD_SHIFTED',amount=r.value,record_date=r.event_date)
        elif r.event_type in ['STOCK_SPLIT','REVERSE_SPLIT','BONUS_SHARES']:
            factor=1+r.factor/100 if r.event_type=='BONUS_SHARES' else r.factor
            if factor>0:add(r.isin_code,day,'SHARES','B3_ORIGINAL',factor=factor,record_date=r.event_date)
    # FRE corroborates material mechanics independently of prices. Match official
    # dates, price-detector dates or an observed break only after the documentary approval.
    for isin,companies in issuer.items():
        if isin not in book.series or len(companies)!=1:continue
        series=book.series[isin]
        candidates=stock[stock.isin_code==isin]
        for r in by_issuer[next(iter(companies))]:
            pos=int(np.searchsorted(series['dates'],r['approved'],'right'))
            if pos==0 or pos>=len(series['dates']):continue
            ticker=series['tickers'][pos];factor=class_factor(r,ticker)
            if factor is None or factor<=0:continue
            if r['ambiguous']:
                flags.append(dict(isin=isin,date=r['approved'],cause='CONFLICTING_DOCUMENTARY_SHARE_FACTORS'));continue
            matching=[]
            for q in candidates.itertuples():
                f=1+q.factor/100 if q.action_type=='BONUS_SHARES' else q.factor
                # Approval can precede entitlement by months. Small bonuses
                # must not be booked once at approval and again at their ex-date.
                distance=book.age(r['approved'],q.ex_date)
                documentary_window=90 if r['kind']=='Bonificação' else 10
                if f>0 and abs(f/factor-1)<=.02 and -2<=distance<=documentary_window:
                    day=book.next_session(q.ex_date) if q.source=='B3' else q.ex_date
                    matching.append((q.source!='B3',day))
            if matching:day=sorted(matching)[0][1]
            else:
                breaks=[]
                for i in range(pos,min(pos+11,len(series['dates']))):
                    gross=series['prices'][i]/series['prices'][i-1]*factor
                    if math.isfinite(gross) and abs(math.log(gross))<math.log(1.25):
                        breaks.append((abs(math.log(gross)),series['dates'][i]))
                if abs(math.log(factor))<math.log(1.15):day=series['dates'][pos]
                elif breaks:day=min(breaks)[1]
                else:
                    flags.append(dict(isin=isin,date=r['approved'],cause='DOCUMENTED_CAPITAL_EX_DATE_UNRESOLVED'));continue
            # Replace alternate representations of the same documentary kind. Two
            # genuine opposite mechanics on one day retain their net quantity.
            same_kind='BONUS_SHARES' if r['kind']=='Bonificação' else ('STOCK_SPLIT' if factor>1 else 'REVERSE_SPLIT')
            existing=[e for e in events if e['ticker']==isin and e['kind']=='SHARES'
                and abs(book.age(e['ex_date'],day))<=10 and abs(e['factor']/factor-1)<=.02]
            for e in existing:events.remove(e)
            add(isin,day,'SHARES','FRE_DOCUMENTARY',factor=factor,approved=r['approved'],docs=r['docs'])
    # Price-only detections are risk markers, not corrections to returns.
    for r in stock[stock.source!='B3'].itertuples():
        if r.isin_code not in book.series:continue
        factor=1+r.factor/100 if r.action_type=='BONUS_SHARES' else r.factor
        covered=any(e['ticker']==r.isin_code and e['kind']=='SHARES'
            and abs(book.age(e['ex_date'],r.ex_date))<=10 and factor>0 and abs(e['factor']/factor-1)<=.02 for e in events)
        if not covered:flags.append(dict(isin=r.isin_code,date=r.ex_date,cause='UNCORROBORATED_PRICE_DETECTED_SPLIT'))
    # Reuse specific prior economic resolutions, not the prior universe's certificate.
    prior=json.loads(gzip.decompress((ROOT/'research/returns_2014_2026_selection/cache/continuation_events.json.gz').read_bytes()))
    reviewed=pd.read_csv(round2/'reconciled_economic_events.csv').replace({np.nan:None}).to_dict('records')
    def normalize(r):
        result={k:v for k,v in r.items() if v is not None}
        for k in ['legs','replace_dates']:
            if isinstance(result.get(k),str):
                import ast
                result[k]=ast.literal_eval(result[k])
        return result
    primary=[normalize(r) for r in reviewed if str(r.get('id','')).startswith('REVIEWED_')]
    structural=[e for e in prior if e['kind']!='DISTRIBUTION']
    primary.extend(e for e in prior if e['kind']=='DISTRIBUTION' and e.get('source') not in ['B3','cache/market.json.gz'])
    scopes=json.loads((round2/'certification_scopes.json').read_text())
    for scope in scopes:
        if scope.get('certified'):
            events=[e for e in events if not(e['ticker']==scope['isin'] and e['kind'] in ['DISTRIBUTION','SHARES']
                and scope['start']<=e['ex_date']<=scope['end'])]
    # Canonical identity/date/kind economics prevent duplicated cache entries.
    reused={}
    for e in structural+primary:
        try:
            parent=book.isin_for_ticker(e['ticker'],e['ex_date'],allow_future=e['ticker'].endswith(('1','2')))
            r=dict(e,ticker=parent)
            if e['kind'] in ['RIGHT','SPINOFF','RIGHT_REINVEST']:
                r['successor']=book.isin_for_ticker(e['successor'],e['ex_date'],allow_future=True)
            elif e['kind']=='CONVERSION':
                r['legs']=[[book.isin_for_ticker(t,e['ex_date'],allow_future=True),q] for t,q in e['legs']]
        except ValueError:
            continue
        key=economic_key(parent,e)
        reused[key]=r
    for r in reused.values():
        if r['kind']=='DISTRIBUTION':
            events=[e for e in events if not(e['ticker']==r['ticker'] and e['kind']=='DISTRIBUTION' and e['ex_date']==r['ex_date'] and e['source']!='REUSED_SPECIFIC_EVIDENCE')]
        elif r['kind']=='SHARES':
            events=[e for e in events if not(e['ticker']==r['ticker'] and e['kind']=='SHARES' and abs(book.age(e['ex_date'],r['ex_date']))<=10 and e['source']!='REUSED_SPECIFIC_EVIDENCE')]
            flags=[f for f in flags if not(f['isin']==r['ticker'] and abs(book.age(f['date'],r['ex_date']))<=10)]
        add(r['ticker'],r['ex_date'],r['kind'],'REUSED_SPECIFIC_EVIDENCE',
            original_id=r.get('id'),original_source=r.get('source'),
            **{k:v for k,v in r.items() if k not in ['id','ticker','isin','ex_date','kind','source']})
    for scope in scopes:
        if scope.get('certified') and scope['ticker']=='IRBR3':
            # Reviewed empty cash window and authoritative structural events.
            flags=[f for f in flags if not(f['isin']==scope['isin'] and scope['start']<=f['date']<=scope['end'])]
    # Missing subscription entitlements can be material even without a skipped flag.
    rightspans=pd.read_csv(round2/'historical_security_spans.csv')
    for r in rightspans[rightspans.ticker.str.fullmatch(r'[A-Z]{4}[12]')].itertuples():
        parent=r.ticker[:4]
        possible=panel[panel.ticker.str.startswith(parent)]
        for isin in possible['isin'].unique():
            known=any(e['kind']=='RIGHT' and e['ticker']==isin and e.get('successor')==r.isin
                and abs(book.age(e['ex_date'],r.first_date))<=60 for e in events)
            if not known:flags.append(dict(isin=isin,date=r.first_date,cause='SUBSCRIPTION_RIGHT_ENTITLEMENT_NOT_RECONCILED'))
    # Skipped capital rows covered by documentary share mechanics are resolved in
    # quantity. Conversions/redemptions need an explicit economic path.
    for r in skipped.itertuples():
        if r.isin_code not in book.series:continue
        day=book.next_session(r.event_date)
        relevant=[e for e in events if e['ticker']==r.isin_code and abs(book.age(e['ex_date'],r.event_date))<=10]
        covered=any(e['kind'] in ['CONVERSION','REDEMPTION','SPINOFF'] for e in relevant)
        if r.label in ['DESDOBRAMENTO','GRUPAMENTO','BONIFICACAO']:
            covered=covered or any(e['kind']=='SHARES' and e['source'] in ['FRE_DOCUMENTARY','REUSED_SPECIFIC_EVIDENCE'] for e in relevant)
        if r.label in ['DESDOBRAMENTO','GRUPAMENTO'] and any(s['ticker']=='LIGT3' and r.event_date in s.get('resolved_skipped_dates',[]) for s in scopes):
            covered=True
        if not covered:flags.append(dict(isin=r.isin_code,date=day or r.event_date,cause='UNRESOLVED_MATERIAL_'+r.label.replace(' ','_')))
    # A targeted primary ITR supplies mechanics omitted from the compact FRE.
    # This later document is used for realized returns, never historical features.
    document=HERE/'local_only/round3/gpc_itr_201606.pdf'
    if not document.exists() or sha256(document)!='3a73dce8d37e1050e2699cf261a8ce8d0394584c9246704a966e4a406f5528cb':
        raise ValueError('MISSING_TARGETED_PRIMARY_GPC_ITR')
    isin='BRGPCPACNOR4';factor=1/61;approved='2016-05-09'
    s=book.series[isin];left=int(np.searchsorted(s['dates'],approved,'right'))
    matches=[(abs(math.log(s['prices'][i]/s['prices'][i-1]*factor)),s['dates'][i])
        for i in range(left,min(left+51,len(s['dates'])))
        if abs(math.log(s['prices'][i]/s['prices'][i-1]*factor))<math.log(1.25)]
    if not matches:raise ValueError('TARGETED_GPC_EXDATE_UNRESOLVED')
    add(isin,min(matches)[1],'SHARES','PRIMARY_ITR_DOCUMENTARY',factor=factor,
        approved=approved,document_sha256=sha256(document),document_page=59)
    # A known official factor contradicted by the ex-date price mechanics remains
    # uncertain. Documentary factors do not lose their status because price fell.
    for e in events:
        if e['kind']=='SHARES' and e['source']=='B3_ORIGINAL':
            try:
                before=book.trade(e['ticker'],book.calendar[bisect_left(book.calendar,e['ex_date'])-1])
                after=book.trade(e['ticker'],e['ex_date'])
                gross=after['close']/before['close']*e['factor']
                if gross<.4 or gross>2.5:flags.append(dict(isin=e['ticker'],date=e['ex_date'],cause='OFFICIAL_FACTOR_PRICE_CONTRADICTION'))
            except ValueError:flags.append(dict(isin=e['ticker'],date=e['ex_date'],cause='MISSING_MATERIAL_EVENT_PRICE'))
    # The old split detector omitted non-BDI02 observations. A restored raw
    # upward break must not masquerade as a multiplier just because there is no
    # row in stock_actions. Never repair such breaks using prices alone.
    wanted=set(panel['isin'])
    for isin in wanted:
        if isin not in book.series:continue
        series=book.series[isin]
        with np.errstate(divide='ignore',invalid='ignore'):
            ratios=series['prices'][1:]/series['prices'][:-1]
        for i in np.flatnonzero(ratios>2.5)+1:
            day=series['dates'][i]
            mechanics=[e for e in events if e['ticker']==isin and e['kind']=='SHARES'
                and abs(book.age(e['ex_date'],day))<=5]
            corrected=ratios[i-1]*math.prod(e['factor'] for e in mechanics)
            if not mechanics or corrected>2.5:
                flags.append(dict(isin=isin,date=day,cause='RESTORED_UPWARD_PRICE_BREAK_NEEDS_DOCUMENTARY_MECHANICS'))
    events=sorted(events,key=lambda e:(e['ex_date'],e['id']))
    flags=list({(r['isin'],r['date'],r['cause']):r for r in flags}.values())
    (output/'scaled_economic_events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2)+'\n')
    pd.DataFrame(flags,columns=['isin','date','cause']).to_csv(output/'scaled_material_uncertainty.csv',index=False)
    return events,flags


def economic_key(parent,event):
    """Collapse the same primary mechanics despite harmless floating rounding.

    Distinct cash tranches and opposite simultaneous quantity factors remain
    distinct. This is an economics key, never an identifier-only deduplication.
    """
    rounded=lambda field: round(float(event[field]),7) if field in event else None
    return (parent,event['ex_date'],event['kind'],rounded('amount'),rounded('factor'),
        event.get('successor'),json.dumps(event.get('legs'),sort_keys=True))


def replay(book,initial,start,target,events,*,event_limit=5):
    session=book.session(target);opening=book.trade(initial,start)
    units={initial:1/opening['close']};cash=0.;days=defaultdict(list);visited={initial};counts=0
    active={initial:start};holding_intervals=[]
    relevant=[e for e in events if start<e['ex_date']<=session]
    reachable={initial};changed=True
    while changed:
        previous=len(reachable)
        for e in relevant:
            if e['ticker'] not in reachable:continue
            if e['kind'] in ['RIGHT','SPINOFF','RIGHT_REINVEST']:reachable.add(e['successor'])
            elif e['kind']=='CONVERSION':reachable.update(t for t,q in e['legs'])
        changed=len(reachable)>previous
    for e in relevant:
        if e['ticker'] not in reachable:continue
        if start<e['ex_date']<=session:days[e['ex_date']].append(e)
    for day,items in sorted(days.items()):
        owned=[e for e in items if e['ticker'] in units]
        spawned={e['successor'] for e in owned if e['kind'] in ['RIGHT','SPINOFF']}
        owned.extend(e for e in items if e['kind']=='RIGHT_REINVEST' and e['ticker'] in spawned and e not in owned)
        if not owned:continue
        def price(isin):return book.trade(isin,day,max_age=event_limit)['close']
        previous=set(units)
        units,cash=apply_events(units,cash,owned,price)
        for isin in previous-set(units):
            holding_intervals.append(dict(isin=isin,start=active.pop(isin),end=day))
        for isin in set(units)-previous:active[isin]=day
        visited.update(units);counts+=len(owned)
    values=[];stale=opening['age_sessions']
    for isin,quantity in units.items():
        q=book.trade(isin,session);stale=max(stale,q['age_sessions']);values.append(quantity*q['close'])
    wealth=math.fsum(values)+cash
    if not math.isfinite(wealth) or wealth<0:raise ValueError('INVALID_FINAL_WEALTH')
    holding_intervals.extend(dict(isin=isin,start=day,end=session) for isin,day in active.items())
    return dict(wealth_multiple=wealth,nominal_total_return=wealth-1,endpoint_session=session,
        events_applied=counts,cash_at_endpoint=cash,max_endpoint_staleness=stale,visited_isins=sorted(visited),
        holding_intervals=holding_intervals)


def build_matrix(book,panel,events,flags,round2,output,protocol):
    prior=pd.read_csv(round2/'return_certification_matrix.csv',dtype={'cnpj':str})
    anchors={(r.cnpj,r.formation_date,r.horizon_years):r for r in prior[prior.status=='CERTIFIED'].itertuples()}
    by_isin=defaultdict(list)
    for r in flags:by_isin[r['isin']].append(r)
    raw_coverage=pd.read_csv(HERE/'local_only/data/raw_quote_coverage.csv',dtype={'bdi':str})
    trouble=raw_coverage[raw_coverage.bdi.isin(['07','08'])]
    distressed={isin:g for isin,g in trouble.groupby('isin')}
    rows=[]
    for p in panel.itertuples():
        for horizon in [3,5]:
            target=(pd.Timestamp(p.formation_date)+pd.DateOffset(years=horizon)).strftime('%Y-%m-%d')
            complete=target<=max(book.calendar);reasons=[];result={};grade='C'
            economic=p.isin in distressed and any(
                (pd.Timestamp(r.first_date)<=pd.Timestamp(target) and pd.Timestamp(r.last_date)>=pd.Timestamp(p.formation_date))
                for r in distressed.get(p.isin,pd.DataFrame()).itertuples())
            try:
                end=book.trade(p.isin,book.session(target)) if complete else None
                exited=complete and end is None
            except ValueError:exited=True
            anchor=anchors.get((p.cnpj,p.formation_date,horizon))
            if not complete:reasons=['HORIZON_NOT_MATURED']
            elif anchor is not None:
                grade='A';result=dict(wealth_multiple=anchor.wealth_multiple,
                    nominal_total_return=anchor.nominal_total_return,endpoint_session=anchor.endpoint_session,
                    events_applied=anchor.events_applied,cash_at_endpoint=anchor.cash_at_endpoint,
                    max_endpoint_staleness=0,visited_isins=[p.isin])
            else:
                try:
                    result=replay(book,p.isin,p.formation_date,target,events)
                    for interval in result['holding_intervals']:
                        isin=interval['isin'];left=interval['start'];right=interval['end']
                        reasons.extend(r['cause'] for r in by_isin.get(isin,[]) if left<r['date']<=right)
                        if book.observed_gap(isin,left,right)>60:
                            reasons.append('LONG_TRADING_SUSPENSION')
                    grade='B' if not reasons else 'C'
                except ValueError as error:reasons.append(str(error).split(':')[0])
            approx_adj=np.nan
            if complete:
                try:
                    a=book.trade(p.isin,p.formation_date);b=book.trade(p.isin,book.session(target))
                    if pd.notna(a['adj_close']) and a['adj_close']>0 and pd.notna(b['adj_close']):
                        approx_adj=b['adj_close']/a['adj_close']
                except ValueError:pass
            wealth=result.get('wealth_multiple',np.nan)
            delta=0 if grade=='A' else protocol['materiality']['B_wealth_sensitivity_fraction']
            rows.append(dict(year=p.year,cnpj=p.cnpj,ticker=p.ticker,isin=p.isin,formation_date=p.formation_date,
                horizon_years=horizon,calendar_endpoint=target,calendar_complete=complete,grade=grade,
                uncertainty_causes=';'.join(sorted(set(reasons))),historical_distress=bool(economic),historical_exit_or_suspension=bool(exited),
                financial_sector=p.financial_sector,sector=p.sector or 'UNKNOWN',
                wealth_multiple=wealth,wealth_low=wealth*(1-delta),wealth_high=wealth*(1+delta),
                adj_comparator_wealth=approx_adj,**{k:v for k,v in result.items() if k!='wealth_multiple'}))
    frame=pd.DataFrame(rows)
    frame.to_csv(output/'return_estimates_A_B_C.csv',index=False)
    print('Return grades',frame.groupby(['horizon_years','grade']).size().to_dict(),flush=True)
    return frame
