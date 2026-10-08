#!/usr/bin/env python3
"""Independent fiscal adapter over frozen v11.2/v13 nominal events. No baseline writes.

Shares are fractional (inherited index convention); rights alone are integer.
Tax is reserved when assessed and paid after monthly close; sale cash is D+2.
"""
from __future__ import annotations
import argparse, bisect, csv, gzip, hashlib, json, math, sys
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from graham_v6_event_bridge.graham_event_resume import Engine, Event, PriceBook
from motor_eventos import State
from dataclasses import fields
EVENT_FIELDS={f.name for f in fields(Event)}
ROOT=Path('research/ir_100k_inputs');OUT=Path('research/ir_100k_results');END='2026-06-30'
BONUS_ITSA={'2021-12-21':18.191662,'2022-11-11':13.65162423,'2023-11-28':17.9172476,'2024-12-03':13.55518731,'2025-12-19':11.370033972}
ALIASES={'BRAV3':'ENAT3','RRRP3':'ENAT3','TIMS3':'TIMP3','AESB3':'TIET4','AURE3':'TIET4','ISAE4':'TRPL4','AXIA3':'ELET3','CPLE5':'CPLE6'}
def load():return json.loads(gzip.decompress((ROOT/'replay.json.gz').read_bytes()))
def dump(name,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or ['status']);w.writeheader();w.writerows(rows)
def tax_book(sales,enabled=True,gcap_exempt=False):
    months=defaultdict(list)
    for s in sales:months[s['date'][:7]].append(s)
    loss=0.;dayloss=0.;result=[]
    for month,rows in sorted(months.items()):
        stocks=[s for s in rows if s['venue']=='STOCK'];sv=sum(s['gross'] for s in stocks);sg=sum(s['gain'] for s in stocks)
        common=sg if sv>20000+1e-8 or sg<0 else 0.
        common+=sum(s['gain'] for s in rows if s['venue'] in ('ETF','RIGHT'))
        entering=loss; taxable=max(0,common-loss);loss=max(0,loss-common)
        # Resgates outside exchange are separately identified; no bolsa-loss offset.
        cg=sum(max(0,s['gain']) for s in rows if s['venue']=='GCAP')
        cg_tax=0 if gcap_exempt else cg*.15
        daygain=sum(s['gain'] for s in rows if s['venue']=='DAYTRADE');daytax=max(0,daygain-dayloss)*.20;dayloss=max(0,dayloss-daygain)
        result.append(dict(month=month,stock_sales=sv,stock_gain=sg,stock_exempt=sv<=20000+1e-8 and sg>=0,
                           common_gain=common,loss_open=entering,loss_close=loss,taxable_common=taxable,
                           gcap_positive_gain=cg,tax=(taxable*.15+cg_tax+daytax) if enabled else 0.,daytrade_gain=daygain,daytrade_loss=dayloss,tax_daytrade=daytax if enabled else 0.,tax_common=taxable*.15 if enabled else 0.,tax_gcap=cg_tax if enabled else 0.))
    return result

def target_weights(tickers,rule,sector):
    if not tickers:return {}
    tickers=sorted(tickers)
    if rule!='R16' and not rule.endswith('S'):return {t:1/len(tickers) for t in tickers}
    groups=defaultdict(list)
    for t in tickers:groups[sector(t)].append(t)
    return {t:1/len(groups)/len(ts) for ts in groups.values() for t in ts}

def allocate_sales(amount,values,weights,nav):
    """Sell overweight survivors first, then pro rata. Never sell all a survivor."""
    caps={t:max(0,v-weights[t]*nav) for t,v in values.items()};over=sum(caps.values());out={t:0. for t in values}
    if amount<=over and over:
        return {t:amount*c/over for t,c in caps.items()}
    out.update(caps);remaining=amount-over;capacity=sum(values[t]-out[t] for t in values)
    if remaining>1e-9:
        if remaining>=capacity-1e-8:raise ValueError('B2 cannot fund entrants without liquidating survivors')
        for t in out:out[t]+=remaining*(values[t]-out[t])/capacity
    return out

class Portfolio:
    def __init__(self,data,year,rule,scenario,policy,tax,*,unknown_exit=False,bonus_market=False,jcp_net=False,jcp_unclassified=False,gcap_exempt=False,cash_scale=1.,same_close=False,log=True):
        self.d=data
        if '_corporate_engine' not in data:data['_corporate_engine']=Engine(PriceBook(data['prices'],data['calendar']),[])
        self.legacy=data['_corporate_engine'];self.year=year;self.rule=rule;self.sc=scenario;self.policy=policy;self.tax=tax
        self.unknown_exit=unknown_exit;self.bonus_market=bonus_market;self.jcp_net=jcp_net;self.jcp_unclassified=jcp_unclassified;self.gcap_exempt=gcap_exempt;self.cash_scale=cash_scale;self.same_close=same_close;self.log=log
        self.h={};self.basis={};self.cash=100000.;self.pending=[];self.sales=[];self.paid=0.;self.payment=[];self.snap={};self.ledger=[];self.annual=[];self.rights=[];self.flags=set();self.unknown=[];self.divs=defaultdict(float)
        self.daybuys=defaultdict(lambda:[0.,0.]);self.taxrows=[];self.assessed=0.;self.jcp=0.;self.turn=0.;self.min_cash=100000.;self.cashdays=0;self.plan=None
        self.calendar=data['calendar'];self.events=defaultdict(list)
        for e in data['events']:self.events[e['date']].append(e)
        self.case=f'{year}_{rule}_{scenario}_{policy}_{"IR" if tax else "SEM_IR"}'
    def price(self,t,d):
        p=self.d['prices'].get(t,{}).get(d)
        if p is None or p<=0:raise ValueError(f'COTACAO_OBRIGATORIA_AUSENTE {t} {d}')
        return p
    def plus(self,d,n):return self.calendar[bisect.bisect_left(self.calendar,d)+n]
    def elig(self,y,t):
        key=f'{y}|{self.rule}|{self.sc}|{t}'
        # Code-only rename retains issuer identity. Merger successor requires its own evidence.
        if key not in self.d['eligibility'] and t in ('ISAE4','AXIA3'):key=f'{y}|{self.rule}|{self.sc}|{ALIASES[t]}'
        return self.d['eligibility'].get(key,['INDETERMINATE','Sem screener PIT para o sucessor/classe'])
    def sector(self,y,t):
        for yy in range(y,2019,-1):
            for a in (t,ALIASES.get(t,t)):
                sec=self.d['sectors'].get(f'{yy}|{a}')
                if sec:return sec
        raise ValueError(f'SETOR_AUSENTE {y} {t}')
    def selected(self,y):return ['BOVA11'] if self.rule=='BOVA11' else self.d['selections'][f'{y}|{self.rule}|{self.sc}']
    def liability(self):return self.assessed-self.paid
    def available(self):return max(0,self.cash-max(0,self.liability()))
    def nav(self,d):return self.cash+sum(x['amount'] for x in self.pending)+sum(q*self.price(t,d) for t,q in self.h.items())-self.liability()
    def record(self,d,kind,t='',**kw):
        if self.log:self.ledger.append(dict(case_id=self.case,date=d,kind=kind,ticker=t,cash=self.cash,tax_reserved=self.liability(),**kw))
    def assess(self):
        self.taxrows=tax_book(self.sales,self.tax,self.gcap_exempt);self.assessed=sum(r['tax'] for r in self.taxrows)
    def buy(self,d,t,amount,reason):
        if amount<=1e-8:return
        if amount>self.available()+1e-6:raise AssertionError(f'CAIXA_FICTICIO {d} {amount} > {self.available()}')
        p=self.price(t,d);q=amount/p;self.h[t]=self.h.get(t,0)+q;self.basis[t]=self.basis.get(t,0)+amount;self.cash-=amount
        self.daybuys[(d,t)][0]+=q;self.daybuys[(d,t)][1]+=amount
        self.record(d,'BUY',t,quantity=q,price=p,amount=amount,basis_after=self.basis[t],reason=reason)
    def sale_rows(self,d,t,q,reason,p,venue):
        old=self.h[t];todayq,todaycost=self.daybuys[(d,t)];matched=min(q,todayq) if venue in ('STOCK','ETF') else 0.
        out=[]
        if matched>1e-10:
            cost=matched*todaycost/todayq
            out.append(dict(date=d,ticker=t,quantity=matched,price=p,gross=matched*p,cost=cost,gain=matched*p-cost,venue='DAYTRADE',reason=reason))
        ordinary=q-matched
        if ordinary>1e-10:
            cost=(self.basis[t]-todaycost)*ordinary/(old-todayq) if matched else self.basis[t]*q/old
            out.append(dict(date=d,ticker=t,quantity=ordinary,price=p,gross=ordinary*p,cost=cost,gain=ordinary*p-cost,venue=venue,reason=reason))
        return out
    def sale(self,d,t,q,reason,price=None,venue=None,settle=None):
        if q<=1e-10:return
        old=self.h[t];p=self.price(t,d) if price is None else price
        if q>old+1e-7:raise AssertionError('SHORT')
        rows=self.sale_rows(d,t,q,reason,p,venue or ('ETF' if t=='BOVA11' else 'STOCK'))
        cost=sum(r['cost'] for r in rows);gross=sum(r['gross'] for r in rows)
        self.h[t]-=q;self.basis[t]-=cost
        for r in rows:
            if r['venue']=='DAYTRADE':self.daybuys[(d,t)][0]-=r['quantity'];self.daybuys[(d,t)][1]-=r['cost']
        if self.h[t]<1e-8:self.h.pop(t);self.basis.pop(t)
        self.sales.extend(rows);self.assess()
        settlement=settle or (d if self.same_close else self.plus(d,2))
        if settlement==d:self.cash+=gross
        else:self.pending.append(dict(date=settlement,amount=gross,kind='SALE',ticker=t))
        for row in rows:self.record(d,'SELL',t,**{k:v for k,v in row.items() if k not in ('date','ticker')},settlement=settlement,basis_after=self.basis.get(t,0))
    def settle(self,d):
        due=[p for p in self.pending if p['date']<=d];self.pending=[p for p in self.pending if p['date']>d]
        for p in due:self.cash+=p['amount'];self.record(d,'SETTLEMENT',p['ticker'],amount=p['amount'],origin=p['kind'])
        # Pay matured prior-month liabilities on the last B3 business day, reserving tax meanwhile.
        i=bisect.bisect_left(self.calendar,d)
        last=i+1==len(self.calendar) or self.calendar[i+1][:7]!=d[:7]
        if last:
            target=sum(r['tax'] for r in self.taxrows if r['month']<d[:7]);payment=max(0,target-self.paid)
            if payment>self.cash+1e-6:raise AssertionError('TAX_PAYMENT_UNFUNDED')
            if payment:self.cash-=payment;self.paid+=payment;self.payment.append(dict(date=d,amount=payment));self.record(d,'TAX_PAYMENT',amount=payment)
        for p in due:
            if p['kind']=='RIGHT':self.buy(d,'ITSA3',min(p['reinvest_amount'],self.available()),'RIGHTS_NET_REINVESTMENT')
    def corporate_effect(self,e,d):
        """Delegate entitlements and quantity/cash transformations to unchanged v6.

        It emits gross cash without reinvestment; this adapter alone controls tax,
        settlement and affordable purchases. Annual v9 cash buckets explicitly use
        current units, since their dates are accounting proxies, not dated rights.
        """
        args={k:v for k,v in e.items() if k in EVENT_FIELDS}
        args.update(date=d,source=e.get('source') or 'FISCAL_ADAPTER')
        if args['kind']=='BONUS_OTHER':args['kind']='SPINOFF'
        if args['kind']=='CASH':args['reinvest']='KEEP_CASH'
        st=State(d,d,100000,dict(self.h),snapshots=self.snap)
        if e.get('proxy') or 'date' not in e:
            previous=self.legacy.book.previous_session(d)
            st.snapshots={previous:dict(self.h)}
        self.legacy._apply(st,Event(**args))
        return st
    def apply(self,e,d):
        t=e['asset'];kind=e['kind'];q=self.h.get(t,0)
        rec=e.get('record_date')
        ent=self.snap.get(rec,{}).get(t,0) if rec else q
        if kind=='CASH':
            effect=self.corporate_effect(e,d)
            if not effect.ledger:return
            ent=effect.ledger[-1]['details']['entitled_quantity']
            amount=effect.cash*(self.cash_scale if e.get('proxy') else 1.)
            note=e.get('note','');capital='CAPITAL_REDUCTION' in note
            if e.get('proxy'):self.flags.add('PROVENTO_AGREGADO_V9_SEM_CRONOLOGIA_DOCUMENTAL')
            if capital:
                before=self.basis.get(t,0);self.basis[t]=max(0,before-amount)
                if amount>before+1e-8:
                    self.flags.add('RESTITUICAO_EXCEDE_BASE_GCAP_PROXY');self.sales.append(dict(date=d,ticker=t,quantity=0,price=0,gross=amount,cost=before,gain=amount-before,venue='GCAP',reason='CAPITAL_REDUCTION_EXCESS'));self.assess()
            else:self.divs[(d[:7],t)]+=amount
            withheld=0
            if self.jcp_net and ('JCP' in note.upper() or 'JUROS' in note.upper() or self.jcp_unclassified and (e.get('proxy') or note.startswith('HERDADO_V8'))):
                rate=.175 if d>='2026-01-01' else .15;withheld=amount*rate;self.jcp+=withheld
                self.flags.add('JCP_DATA_EX_PROXY_PARA_CREDITO_FISCAL')
            self.cash+=amount-withheld
            self.record(d,'CASH',t,amount=amount,withheld=withheld,event_id=e['event_id'],entitlement=ent,capital_reduction=capital,basis_after=self.basis.get(t,0))
            # Inherited gross ex-close convention, accounted ONCE; no dividend free cash after reinvestment.
            if q>0 and e.get('reinvest')!='KEEP_CASH':self.buy(d,t,min(amount-withheld,self.available()),'PROVENTO_EX_CLOSE')
        elif ent>0 and kind=='BONUS_OTHER':
            effect=self.corporate_effect(e,d);nt,f=e['legs'][0];newq=effect.holdings.get(nt,0)-self.h.get(nt,0);cost=newq*e['unit_cost']
            self.h=effect.holdings;self.basis[nt]=self.basis.get(nt,0)+cost
            self.record(d,kind,t,event_id=e['event_id'],successor=nt,delivered=newq,basis_add=cost)
        elif q>0 and kind in ('SPLIT','BONUS'):
            factor=e['factor'];newq=q*(factor-1);add=0
            if kind=='BONUS':
                if t=='ITSA3' and d in BONUS_ITSA:add=newq*BONUS_ITSA[d]
                elif t=='PSSA3' and d=='2021-10-21':add=newq*12.37267626833
                else:
                    self.flags.add('CUSTO_FISCAL_BONIFICACAO_NAO_DOCUMENTADO')
                    if self.bonus_market:add=newq*self.price(t,d)
            self.h=self.corporate_effect(e,d).holdings;self.basis[t]+=add
            self.record(d,kind,t,event_id=e['event_id'],quantity_before=q,quantity_after=self.h[t],basis_add=add,basis_after=self.basis[t])
        elif q>0 and kind in ('CONVERSION','MERGER'):
            effect=self.corporate_effect(e,d);cost=self.basis.pop(t);legs=e.get('legs',[])
            if len(legs)!=1:raise ValueError('MULTIPLE_LEGS_REQUIRE_BASIS_ALLOCATION')
            nt,f=legs[0];self.h=effect.holdings;self.basis[nt]=self.basis.get(nt,0)+cost
            amount=effect.cash
            if amount:
                # Unknown basis allocation for redeemable shares: zero cash-leg basis central.
                self.flags.add('ALOCACAO_FISCAL_RESGATE_SOCIETARIO_PROXY')
                self.sales.append(dict(date=d,ticker=t,quantity=q,price=e['amount'],gross=amount,cost=0,gain=amount,venue='GCAP',reason='MERGER_CASH_LEG'));self.assess()
                self.pending.append(dict(date=e.get('cash_date',d),amount=amount,kind='CORPORATE_CASH',ticker=t))
            self.record(d,kind,t,event_id=e['event_id'],quantity=q,successor=nt,delivered=q*f,basis_transferred=cost,cash_leg=amount)
        elif q>0 and kind=='CASH_OUT':
            effect=self.corporate_effect(e,d)
            venue=e.get('venue','STOCK');self.sale(d,t,q,'CASH_OUT',price=e['price'],venue=venue,settle=d if venue=='GCAP' else self.plus(d,2))
            assert self.h==effect.holdings
    def sell_rights(self,r,d):
        q=self.snap.get(r['record_date'],{}).get('ITSA3',0)
        n=int((Decimal(str(q))*Decimal(r['rights_per_share'])).to_integral_value(rounding=ROUND_FLOOR))
        if not q:return
        gross=0.;parts=[];before=self.assessed
        for qty,k in [(n//100*100,'standard_quote'),(n%100,'fractional_quote')]:
            if not qty:continue
            quote=r[k]
            if quote['date']!=d or quote['quantity']<qty or min(quote['trades'],quote['quantity'],quote['volume'])<=0:raise ValueError('RIGHTS_TRADE_NOT_PROVEN')
            v=qty*quote['close'];gross+=v;parts.append(dict(ticker=quote['ticker'],quantity=qty,price=quote['close'],proof=quote['record_sha256']))
            self.sales.append(dict(date=d,ticker=quote['ticker'],quantity=qty,price=quote['close'],gross=v,cost=0,gain=v,venue='RIGHT',reason='RIGHTS_SALE'))
        self.assess();incremental=self.assessed-before
        self.pending.append(dict(date=r['settlement_date'],amount=gross,reinvest_amount=max(0,gross-incremental),kind='RIGHT',ticker='ITSA3'))
        row=dict(case_id=self.case,event_id=r['event_id'],record_date=r['record_date'],eligible_shares=q,rights=n,discarded=q*float(r['rights_per_share'])-n,sale_date=d,gross=gross,incremental_tax=incremental,settlement_date=r['settlement_date'],parts=json.dumps(parts))
        self.rights.append(row);self.record(d,'RIGHTS_SALE','ITSA3',**{k:v for k,v in row.items() if k not in ('case_id',)})
    def renew(self,y,d):
        nav=self.nav(d);before=dict(self.h);costbefore=dict(self.basis);sales0=sum(r['gross'] for r in self.sales)
        selected=set(self.selected(y));statuses={t:self.elig(y,t) for t in self.h}
        for t,(st,why) in statuses.items():
            if st=='INDETERMINATE':self.unknown.append(dict(case_id=self.case,year=y,ticker=t,reason=why,value=self.h[t]*self.price(t,d)))
        if self.policy=='A':remove=set(self.h);retained=set()
        else:
            remove={t for t,(s,why) in statuses.items() if s=='FAIL' or s=='INDETERMINATE' and self.unknown_exit};retained=set(self.h)-remove
        for t in sorted(remove):self.sale(d,t,self.h[t],'ANNUAL_FULL' if self.policy=='A' else 'INELIGIBLE' if statuses[t][0]=='FAIL' else 'INDETERMINATE_SENSITIVITY')
        entrants=selected-retained;union=retained|selected
        w=target_weights(union,self.rule,lambda t:self.sector(y,t))
        # Minimum extra sale to fund entrant weights at the sale-day prices, net of tax.
        extra={};base_assessed=self.assessed
        if self.policy=='B2' and entrants and retained:
            values={t:self.h[t]*self.price(t,d) for t in retained};wealth=self.nav(d);neww=sum(w[t] for t in entrants)
            free=self.cash+sum(p['amount'] for p in self.pending)-self.liability()
            def trial(x):
                ss=allocate_sales(x,values,w,wealth);synthetic=[]
                for t,v in ss.items():
                    if v>0:synthetic.extend(self.sale_rows(d,t,v/self.price(t,d),'FUND_NEW_ENTRANTS',self.price(t,d),'STOCK'))
                taxsum=sum(r['tax'] for r in tax_book(self.sales+synthetic,self.tax,self.gcap_exempt));inc=taxsum-base_assessed
                return free+x-inc-neww*(wealth-inc),ss
            if trial(0)[0]<-1e-8:
                lo=0.;hi=sum(values.values())*(1-1e-9)
                if trial(hi)[0]<0:raise ValueError('B2_ENTRANTS_UNFUNDED')
                # 20k exemption creates a downward discontinuity. Locate the FIRST feasible
                # interval, including both sides of the sole stock-sales threshold.
                already=sum(r['gross'] for r in self.sales if r['date'][:7]==d[:7] and r['venue']=='STOCK')
                threshold=20000-already
                boundaries=sorted(set([0.,hi]+([threshold] if 0<threshold<hi else [])))
                for a,b in zip(boundaries,boundaries[1:]):
                    if trial(b)[0]>=0:lo=a;hi=b;break
                for _ in range(60):
                    mid=(lo+hi)/2
                    if trial(mid)[0]>=0:hi=mid
                    else:lo=mid
                extra=trial(hi)[1]
                for t,v in sorted(extra.items()):
                    if v>1e-8:self.sale(d,t,v/self.price(t,d),'FUND_NEW_ENTRANTS')
        turnover=(sum(r['gross'] for r in self.sales)-sales0)/nav;self.turn+=turnover
        settlement=d if self.same_close else self.plus(d,2);self.plan=dict(date=settlement,weights=w,entrants=entrants,year=y,retained=retained,allowed=selected)
        row=dict(case_id=self.case,year=y,signal_date=self.d['windows'][str(y)][0],sale_date=d,buy_date=settlement,nav_before=nav,
                 retained=';'.join(sorted(retained)),removed=';'.join(sorted(remove)),entrants=';'.join(sorted(entrants)),unknown=';'.join(sorted(t for t,x in statuses.items() if x[0]=='INDETERMINATE')),
                 retained_count=len(retained),removed_count=len(remove),entrants_count=len(entrants),partial_sales=len([v for v in extra.values() if v>1e-8]),turnover=turnover,target_weights=json.dumps(w,sort_keys=True),quantities_before=json.dumps(before,sort_keys=True),basis_before=json.dumps(costbefore,sort_keys=True),quantities_after_sales=json.dumps(self.h,sort_keys=True),basis_after_sales=json.dumps(self.basis,sort_keys=True))
        self.annual.append(row)
    def execute_plan(self,d):
        p=self.plan;nav=self.nav(d);w=p['weights'];funds=self.available()
        # Sale-day plan has settled. Allocate entrants first, then invest only residual cash
        # in underweight survivors. Price drift over D+2 never triggers more sales.
        needs={t:max(0,w[t]*nav-self.h.get(t,0)*self.price(t,d)) for t in w}
        for group in [sorted(p['entrants']),sorted((set(w)-p['entrants']) & p['allowed'])]:
            total=sum(needs[t] for t in group);budget=min(self.available(),total)
            if total:
                for t in group:self.buy(d,t,budget*needs[t]/total,'ANNUAL_PURCHASE')
        after=self.nav(d);actual={t:self.h.get(t,0)*self.price(t,d)/after for t in w}
        self.annual[-1].update(nav_after=after,cash_after=self.available(),entrants_funded=sum(self.h.get(t,0)>0 for t in p['entrants']),target_drift_l1=sum(abs(actual[t]-w[t]) for t in w),actual_weights=json.dumps(actual,sort_keys=True),basis_after_buys=json.dumps(self.basis,sort_keys=True),quantities_after_buys=json.dumps(self.h,sort_keys=True))
        self.plan=None
    def run(self):
        signal=self.d['windows'][str(self.year)][0];start=signal if self.same_close else self.plus(signal,1)
        renewal={(self.d['windows'][str(y)][0] if self.same_close else self.plus(self.d['windows'][str(y)][0],1)):y for y in range(self.year+1,2026)} if self.policy in ('A','B2') else {}
        rights={r['sale_date']:r for r in self.d['rights']}
        dates=[d for d in self.calendar if start<=d<=END]
        for d in dates:
            self.settle(d)
            for e in self.events[d]:self.apply(e,d)
            if d in rights:self.sell_rights(rights[d],d)
            if d==start:
                ss=self.selected(self.year);w=target_weights(ss,self.rule,lambda t:self.sector(self.year,t))
                for t,v in w.items():self.buy(d,t,100000*v,'INITIAL')
            if d in renewal:self.renew(renewal[d],d)
            if self.plan and self.plan['date']==d:self.execute_plan(d)
            self.snap[d]=dict(self.h)
            self.min_cash=min(self.min_cash,self.cash)
            if self.cash<-1e-6 or min(self.basis.values(),default=0)<-1e-6:raise AssertionError('NEGATIVE_CASH_OR_BASIS')
            if self.available()>1:self.cashdays+=1
        gross=self.nav(END);basis=sum(self.basis.values());pre_final=dict(self.h);finalsales=sum(r['gross'] for r in self.sales)
        for t in sorted(self.h):self.sale(END,t,self.h[t],'FINAL_LIQUIDATION')
        final=self.nav(END);final_turn=(sum(r['gross'] for r in self.sales)-finalsales)/gross
        # Economic June endpoint deducts the entire June liability; settle/pay later without exposure.
        for d in self.calendar:
            if END<d<='2026-07-31':self.settle(d)
        assert not self.h and not self.pending and abs(self.liability())<1e-6
        assert math.isclose(self.cash,final,abs_tol=1e-6)
        years=(date.fromisoformat(END)-date.fromisoformat(start)).days/365.25
        row=dict(case_id=self.case,formation=self.year,strategy=self.rule,scenario=self.sc,policy=self.policy,ir=self.tax,initial=100000,start=start,end=END,final_wealth=final,return_pct=(final/100000-1)*100,cagr_pct=((final/100000)**(1/years)-1)*100,tax_sales=self.assessed,tax_jcp=self.jcp,annual_turnover_sum=self.turn,annual_turnover_mean=self.turn/max(1,2025-self.year),final_turnover=final_turn,gross_before_final=gross,basis_before_final=basis,holdings_before_final=json.dumps(pre_final,sort_keys=True),cash_days=self.cashdays,min_cash=self.min_cash,unknown_decisions=len(self.unknown),max_monthly_dividend=max(self.divs.values(),default=0),status='PROXY_FISCAL_OU_PROVENTOS' if self.flags else 'CALCULADO_CONVENCAO_EX_CLOSE',limitations=';'.join(sorted(self.flags)))
        return row

def execute(data,options=None,log=True):
    rows=[];annual=[];ledger=[];monthly=[];yearly=[];rs=[];unknown=[];failures=[];realized=[]
    options=options or {}
    for year in range(2020,2026):
        for rule in ['R00','R03','R16','B00','B00S','B06','B06S','BOVA11']:
            for sc in (['central','conservative'] if rule.startswith('B') and rule!='BOVA11' else ['central']):
                for pol in (['BH'] if rule=='BOVA11' else ['A','B2','BH'] if rule.startswith('B') else ['A','B2']):
                    for tax in [False,True]:
                        p=Portfolio(data,year,rule,sc,pol,tax,log=log,**options)
                        try:r=p.run()
                        except (ValueError,AssertionError,KeyError) as e:
                            failures.append(dict(case_id=p.case,error=str(e)));continue
                        rows.append(r)
                        if log:
                            annual+=p.annual;ledger+=p.ledger;rs+=p.rights;unknown+=p.unknown
                            realized += [dict(case_id=p.case,competence=r['date'][:7],**r) for r in p.sales]
                            monthly += [dict(case_id=p.case,**r) for r in p.taxrows]
                            for y in range(year,2027):
                                yearly.append(dict(case_id=p.case,year=y,tax_assessed=sum(r['tax'] for r in p.taxrows if r['month'].startswith(str(y))),tax_paid=sum(r['amount'] for r in p.payment if r['date'].startswith(str(y))),sales=sum(r['gross'] for r in p.sales if r['date'].startswith(str(y))),gains=sum(r['gain'] for r in p.sales if r['date'].startswith(str(y)))))
        print('cohort',year,'computed',len(rows),'failures',len(failures),flush=True)
    return dict(results=rows,annual=annual,ledger=ledger,monthly=monthly,yearly=yearly,rights=rs,unknown=unknown,failures=failures,realized_sales=realized)

def main():
    OUT.mkdir(exist_ok=True,parents=True);data=load();result=execute(data)
    for name,rows in result.items():
        if name=='ledger':(OUT/'ledger.json.gz').write_bytes(gzip.compress(json.dumps(rows,sort_keys=True).encode(),mtime=0))
        else:dump(name+'.csv',rows)
    print('FINISHED',len(result['results']),len(result['failures']),flush=True)
if __name__=='__main__':main()
