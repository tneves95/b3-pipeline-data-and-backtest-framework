"""Fiscal state for PR6, separate from the frozen PR5 economic decisions.

The monthly exemption/loss ordering and same-day matching reuse the contracts
of PR2's tax_book/sale_rows. No PR2 positions, results or settlement convention
are imported. Money stays in the portfolio until withholding/DARF payment.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import date
import calendar
import math
from monthly_tax_income import historical_jcp_rate, jcp_retention, dividend_tax


def next_month(month):
    y,m=map(int,month.split('-'));return f'{y+(m==12):04d}-{m%12+1:02d}'


def due_date(month, sessions):
    following=next_month(month);days=[d for d in sessions if d.startswith(following)]
    if days:return max(days)
    y,m=map(int,following.split('-'));d=date(y,m,calendar.monthrange(y,m)[1])
    from datetime import timedelta
    while d.weekday()>4:d-=timedelta(days=1)
    return d.isoformat()


def tax_book(sales, enabled=True, exemption=True, gcap_exemption=False):
    """CPF/month aggregate; exempt net gains do not consume prior common losses."""
    months=defaultdict(list)
    for s in sales:months[s['date'][:7]].append(s)
    loss=dayloss=credit=daycredit=0.;year=None;out=[]
    for month,rows in sorted(months.items()):
        exported=dayexported=0.
        if year is not None and year!=month[:4]:
            exported,dayexported=credit,daycredit;credit=daycredit=0.
        year=month[:4]
        stock=[r for r in rows if r['asset_tax_type']=='STOCK']
        stock_sales=math.fsum(r['gross_value'] for r in stock)
        stock_gain=math.fsum(r['realized_gain_loss'] for r in stock)
        exempt=exemption and stock_sales<=20000+1e-8
        common=(min(0.,stock_gain) if exempt else stock_gain)+math.fsum(
            r['realized_gain_loss'] for r in rows if r['asset_tax_type'] in ('BDR','ETF','RIGHT'))
        entering=loss;base=max(0.,common-loss);loss=max(0.,loss-common)
        dg=math.fsum(r['realized_gain_loss'] for r in rows if r['asset_tax_type']=='DAYTRADE')
        dlopen=dayloss;dbase=max(0.,dg-dayloss);dayloss=max(0.,dayloss-dg)
        gc=[r for r in rows if r['asset_tax_type']=='GCAP']
        gc_sales=math.fsum(r['gross_value'] for r in gc)
        gc_gain=math.fsum(max(0.,r['realized_gain_loss']) for r in gc)
        gc_base=0. if gcap_exemption and gc_sales<=35000+1e-8 else gc_gain
        ordinary_sales=math.fsum(r['gross_value'] for r in rows if r['asset_tax_type'] in ('STOCK','BDR','ETF','RIGHT'))
        irrf=ordinary_sales*.00005
        irrf=irrf if enabled and irrf>1.+1e-10 else 0.
        daily=defaultdict(float)
        for r in rows:
            if r['asset_tax_type']=='DAYTRADE':daily[r['date']]+=r['realized_gain_loss']
        day_irrf=math.fsum(max(0,v)*.01 for v in daily.values()) if enabled else 0.
        common_tax=base*.15 if enabled else 0.;daytax=dbase*.20 if enabled else 0.
        gctax=gc_base*.15 if enabled else 0.
        credit_open,dcopen=credit,daycredit
        used=min(common_tax,credit+irrf);dused=min(daytax,daycredit+day_irrf)
        credit+=irrf-used;daycredit+=day_irrf-dused
        # Conservative reserve until month closes: an exempt month may cross20k.
        possible_base=max(0.,stock_gain+math.fsum(r['realized_gain_loss'] for r in rows
             if r['asset_tax_type'] in ('BDR','ETF','RIGHT'))-entering)
        precaution=max(0.,possible_base*.15-common_tax) if enabled and exempt else 0.
        out.append(dict(month=month,stock_sales=stock_sales,stock_gain=stock_gain,
            stock_exempt=exempt,exempt_gain=max(0.,stock_gain) if exempt else 0.,
            common_gain=common,common_loss_open=entering,common_loss_close=loss,
            common_taxable_base=base,common_tax=common_tax,daytrade_gain=dg,
            daytrade_loss_open=dlopen,daytrade_loss_close=dayloss,daytrade_taxable_base=dbase,
            daytrade_tax=daytax,gcap_sales=gc_sales,gcap_positive_gain=gc_gain,gcap_tax=gctax,
            ordinary_irrf=irrf,daytrade_irrf=day_irrf,ordinary_irrf_credit_open=credit_open,
            ordinary_irrf_credit_used=used,ordinary_irrf_credit_close=credit,
            daytrade_irrf_credit_open=dcopen,daytrade_irrf_credit_used=dused,daytrade_irrf_credit_close=daycredit,
            prior_year_irrf_exported_DIRPF=exported,prior_year_daytrade_irrf_refund_pending=dayexported,
            darf_6015=common_tax+daytax-used-dused,darf_4600=gctax,
            assessed_tax=common_tax+daytax+gctax,precautionary_exemption_reserve=precaution))
    return out


class Fiscal:
    def __init__(self,portfolio,evidence,sessions,*,enabled=True,exemption=True,
                 bonus_market=False,xp_zero=False,boot_zero=False,gcap_exemption=False,
                 income_mode='NONE'):
        self.portfolio=portfolio;self.evidence=evidence;self.sessions=sessions
        self.enabled=enabled;self.exemption=exemption;self.bonus_market=bonus_market
        self.xp_zero=xp_zero;self.boot_zero=boot_zero;self.gcap_exemption=gcap_exemption
        self.income_mode=income_mode
        self.q=defaultdict(float);self.basis=defaultdict(float);self.daybuys=defaultdict(lambda:[0.,0.])
        self.trades=[];self.sales=[];self.event_rows=[];self.income_rows=[];self.payments=[]
        self.taxrows=[];self.paid_by_code={'6015':0.,'4600':0.};self.withheld=0.
        self.liability=0.;self.precaution=0.;self.income_withheld=0.;self.closed=set()
        self.min_available=0.;self.dividends=defaultdict(float)
        self._assessed_sales=-1

    def income(self,day,c,t,q,e):
        """Tax known gross cash only; amount convention and timing stay visible."""
        ev=self.evidence[e['id']];value=q*e['amount'];typ=ev.get('distribution_type','UNKNOWN')
        basis=ev['amount_basis'];retention=0.;taxdate=day;rate=None
        status='CG_ONLY_NO_ADDITIONAL_INCOME_TAX'
        payments=ev.get('payment_date','').split(';') if ev.get('payment_date') else []
        if typ=='JCP' and self.income_mode!='NONE':
            if self.income_mode=='CERTIFIED_PARTIAL':
                rate=ev.get('tax_rate')
                if basis=='GROSS' and rate is not None:
                    retention=value*rate;status='GROSS_RATE_SUPPORTED_EX_DATE_REINVESTMENT_PROXY'
                elif basis=='NET_ALREADY_WITHHELD':status='NO_SECOND_WITHHOLDING'
                else:status='ND_AMOUNT_BASIS_OR_TAX_DATE_UNRESOLVED'
            else:
                taxdate=payments[0] if payments and self.income_mode=='UNKNOWN_GROSS_PAYMENT' else day
                rate=ev.get('tax_rate') or historical_jcp_rate(taxdate)
                retention=0. if basis=='NET_ALREADY_WITHHELD' else value*rate
                status='NO_SECOND_WITHHOLDING' if basis=='NET_ALREADY_WITHHELD' else 'CONDITIONAL_UNKNOWN_GROSS_OR_DATE_PROXY'
        elif typ=='UNKNOWN' and self.income_mode=='UNKNOWN_AS_JCP':
            rate=historical_jcp_rate(day);retention=value*rate;status='CONDITIONAL_UNCLASSIFIED_DISTRIBUTION_AS_JCP'
        elif typ=='DIVIDEND':
            # This report must not confuse the economic ex-date with pay/credit.
            taxdate=payments[0] if payments else day;k=c,taxdate[:7]
            previous=self.dividends[k];self.dividends[k]+=value
            if self.income_mode!='NONE':
                retention=dividend_tax(self.dividends[k],int(taxdate[:4]))-dividend_tax(previous,int(taxdate[:4]))
            status='DIVIDEND_2026_MONTHLY_TEST' if taxdate>='2026-01-01' else 'HISTORICAL_DOMESTIC_DIVIDEND_EXEMPT'
        if retention>value+1e-8:raise ValueError(('DIVIDEND_THRESHOLD_REQUIRES_PRIOR_RESERVE',e['id']))
        if not self.enabled:retention=0.
        self.income_withheld+=retention
        self.income_rows.append(dict(portfolio=self.portfolio,date=day,issuer=c,ticker=t,event_id=e['id'],
            source_amount=value,gross_amount=value if basis=='GROSS' else None,
            withheld_additional=retention,reinvested=value-retention,distribution_type=typ,
            original_type=ev['original_type'],amount_basis=basis,tax_rate=rate,
            source_payment_dates=ev.get('payment_date',''),tax_date_used=taxdate,
            rate_status=ev.get('rate_status','UNRESOLVED'),date_status=status,
            economic_tax_timing='EX_DATE_PROXY' if retention else 'NO_ADDITIONAL_RETENTION',
            monthly_dividend_total_so_far=self.dividends[c,taxdate[:7]] if typ=='DIVIDEND' else None,
            source=e['source'],amount_evidence=ev.get('evidence','')))
        return value-retention

    def reserve(self):return self.liability+self.precaution

    def available(self,cash):
        value=cash-self.reserve()
        if value< -1e-5:raise ValueError(('UNFUNDED_RESERVE',self.portfolio,cash,self.reserve()))
        return max(0.,value)

    def buy(self,d,c,t,q,p,reason,*,market=True):
        if q<=1e-14:return
        old=self.basis[t]/self.q[t] if self.q[t] else 0.;value=q*p
        self.q[t]+=q;self.basis[t]+=value
        if market:
            k=d,t;self.daybuys[k][0]+=q;self.daybuys[k][1]+=value
        self.trades.append(dict(date=d,portfolio=self.portfolio,ticker=t,issuer=c,
            asset_tax_type='BDR' if t=='XPBR31' else 'STOCK',side='BUY',quantity=q,
            nominal_unit_price=p,gross_value=value,average_cost_before=old,cost_removed=0.,
            realized_gain_loss=0.,exemption_bucket='',tax_due=0.,irrf=0.,
            tax_cash_reserved=self.reserve(),basis_after=self.basis[t],reason=reason))

    def sell(self,d,c,t,q,p,reason,category=None):
        if q<=1e-12:return
        oldq=self.q[t];oldbasis=self.basis[t]
        if q>oldq+1e-7:raise ValueError(('FISCAL_SHORT',t,d,q,oldq))
        category=category or ('BDR' if t=='XPBR31' else 'STOCK')
        bq,bc=self.daybuys[d,t]
        matched=min(q,bq) if category in ('STOCK','BDR','ETF') else 0.
        pieces=[]
        if matched>1e-12:pieces.append((matched,matched*bc/bq,'DAYTRADE'))
        normal=q-matched
        if normal>1e-12:
            cost=(oldbasis-bc)*normal/(oldq-bq) if matched else oldbasis*normal/oldq
            pieces.append((normal,cost,category))
        for qty,cost,cat in pieces:
            gain=qty*p-cost
            if abs(gain)<1e-8:gain=0.
            row=dict(date=d,portfolio=self.portfolio,ticker=t,issuer=c,asset_tax_type=cat,
                side='SELL',quantity=qty,nominal_unit_price=p,gross_value=qty*p,
                average_cost_before=oldbasis/oldq,cost_removed=cost,realized_gain_loss=gain,
                exemption_bucket='MONTHLY_ALL_STOCKS_20K' if cat=='STOCK' else 'NO_20K_EXEMPTION',
                tax_due=None,irrf=None,tax_cash_reserved=self.reserve(),reason=reason)
            self.trades.append(row);self.sales.append(row)
            self.q[t]-=qty;self.basis[t]-=cost
            if cat=='DAYTRADE':self.daybuys[d,t][0]-=qty;self.daybuys[d,t][1]-=cost
            row['basis_after']=self.basis[t]
        if abs(self.q[t])<1e-8:self.q[t]=self.basis[t]=0.

    def assess(self,day,*,month_closed=False):
        if month_closed:self.closed.add(day[:7])
        if self._assessed_sales!=len(self.sales):
            self.taxrows=tax_book(self.sales,self.enabled,self.exemption,self.gcap_exemption)
            self._assessed_sales=len(self.sales)
        total_withheld=math.fsum(r['ordinary_irrf']+r['daytrade_irrf'] for r in self.taxrows)
        delta=total_withheld-self.withheld
        if delta< -1e-6:raise ValueError(('WITHHOLDING_REVERSED',delta))
        self.withheld=total_withheld
        due=math.fsum(r['darf_6015']+r['darf_4600'] for r in self.taxrows)
        self.liability=max(0.,due-sum(self.paid_by_code.values()))
        if self.liability<1e-8:self.liability=0.
        self.precaution=math.fsum(r['precautionary_exemption_reserve'] for r in self.taxrows if r['month'] not in self.closed)
        return max(0.,delta)

    def payment(self,day,cash):
        """Consume restricted cash; paying a recognized liability does not change NAV."""
        amount=0.
        for code in ['6015','4600']:
            eligible=math.fsum(r['darf_'+code] for r in self.taxrows if due_date(r['month'],self.sessions)<=day)
            due=eligible-self.paid_by_code[code]
            if due>=10-1e-8:
                if due>cash-amount+1e-6:raise ValueError(('DARF_UNFUNDED',day,code,due,cash))
                amount+=due;self.paid_by_code[code]+=due
                self.payments.append(dict(portfolio=self.portfolio,date=day,revenue_code=code,amount=due,
                    calendar_status='B3_SESSION_BANK_CALENDAR_PROXY'))
        self.liability=max(0.,self.liability-amount)
        if self.liability<1e-8:self.liability=0.
        return amount

    def verify(self,book):
        actual=defaultdict(float)
        for u in book.values():
            for t,q in u.items():actual[t]+=q
        for t in set(actual)|set(self.q):
            if not math.isclose(actual[t],self.q[t],rel_tol=2e-11,abs_tol=1e-7):
                raise ValueError(('BASIS_QUANTITY_MISMATCH',t,actual[t],self.q[t]))
            if self.basis[t]<-1e-6:raise ValueError(('NEGATIVE_COST',t,self.basis[t]))

    def corporate(self,day,before,after,events,quote,principal,*,month_closed=False):
        """Account for the exact PR5 entitlement; fund tax from its cash leg.

        Structural transformations precede reinvestment buys; all entitlements
        are based on the pre-event quantities, just as PR5's apply_day does.
        """
        oldreserve=self.reserve();reinvest=[];event_row_start=len(self.event_rows)
        for c,u in before.items():
            relevant=[e for e in events if e['ticker'] in u]
            for e in relevant:
                t=e['ticker'];q=u[t];k=e['kind'];ev=self.evidence[e['id']]
                if k=='SHARES':
                    added=q*(e['factor']-1);unit=ev['unit_basis']
                    potential_bonus=ev['share_kind']=='BONUS_SHARES' or (not ev['share_kind'] and 1<e['factor']<2)
                    if unit is None:unit=quote[t,day] if self.bonus_market and potential_bonus else 0.
                    self.q[t]+=added;self.basis[t]+=max(0.,added)*unit
                elif k in ('RIGHT','SPINOFF'):
                    child=e['successor'];newq=q*e['ratio'];cost=0.
                    if k=='SPINOFF' and child=='XPBR31' and not self.xp_zero:
                        pv=q*quote[t,day];cv=newq*quote[child,day]
                        cost=self.basis[t]*cv/(pv+cv);self.basis[t]-=cost
                    elif k=='SPINOFF' and child!='XPBR31' and self.bonus_market:cost=newq*quote[child,day]
                    self.q[child]+=newq;self.basis[child]+=cost
                self.event_rows.append(dict(ev,portfolio=self.portfolio,issuer=c,quantity_held=q,
                    event_id=e['id'],date=day,total_cost_after_structural=self.basis[t]))
            for e in relevant:
                if e['kind']=='DISTRIBUTION':
                    t=e['ticker'];gross=u[t]*e['amount'];value=self.income(day,c,t,u[t],e)
                    after[c][t]-=(gross-value)/quote[t,day]
                    if self.evidence[e['id']].get('distribution_type')=='CAPITAL_RETURN':
                        cost=min(self.basis[t],value);self.basis[t]-=cost
                        row=dict(date=day,portfolio=self.portfolio,ticker=t,issuer=c,asset_tax_type='GCAP',
                            side='CAPITAL_RETURN',quantity=u[t],nominal_unit_price=e['amount'],gross_value=value,
                            average_cost_before=(self.basis[t]+cost)/self.q[t],cost_removed=cost,
                            realized_gain_loss=value-cost,exemption_bucket='SPECIFIC_CAPITAL_RETURN_NO_20K',
                            tax_due=None,irrf=0.,tax_cash_reserved=self.reserve(),basis_after=self.basis[t],reason=e['id'])
                        self.sales.append(row);self.trades.append(row);reinvest.append((c,t,value,e['id']))
                    else:self.buy(day,c,t,value/quote[t,day],quote[t,day],'DISTRIBUTION_REINVESTMENT')
            # Rights may have been created on the same day, hence inspect live q.
            spawned={e['successor'] for e in relevant if e['kind']=='RIGHT'}
            for e in events:
                t=e['ticker'];k=e['kind']
                if k=='RIGHT_REINVEST' and (t in u or t in spawned):
                    qty=self.q[t];value=qty*quote[t,day]
                    if t in spawned and t not in u:
                        self.event_rows.append(dict(self.evidence[e['id']],portfolio=self.portfolio,issuer=c,quantity_held=qty,
                            event_id=e['id'],date=day,total_cost_after_structural=self.basis[t]))
                    self.sell(day,c,t,qty,quote[t,day],e['id'],'RIGHT')
                    reinvest.append((c,e['successor'],value,e['id']))
                elif t in u and k=='CONVERSION':
                    qty=self.q[t];cost=self.basis[t];child,ratio=e['legs'][0]
                    if len(e['legs'])!=1:raise ValueError('Unmapped multiple conversion legs')
                    boot=u[t]*e.get('amount',0.);remaining=qty*ratio*quote[child,day] if boot else 0.
                    cash_cost=0. if self.boot_zero else cost*boot/(boot+remaining) if boot else 0.
                    if boot:
                        row=dict(date=day,portfolio=self.portfolio,ticker=t,issuer=c,asset_tax_type='GCAP',
                            side='SELL_CASH_LEG',quantity=u[t],nominal_unit_price=e['amount'],gross_value=boot,
                            average_cost_before=cost/qty,cost_removed=cash_cost,realized_gain_loss=boot-cash_cost,
                            exemption_bucket='NO_20K_EXEMPTION',tax_due=None,irrf=0.,tax_cash_reserved=self.reserve(),
                            basis_after=cost-cash_cost,reason=e['id'])
                        self.sales.append(row);self.trades.append(row);reinvest.append((c,child,boot,e['id']))
                    self.q[t]=self.basis[t]=0.;self.q[child]+=qty*ratio;self.basis[child]+=cost-cash_cost
                elif t in u and k=='REDEMPTION':
                    self.sell(day,c,t,self.q[t],e['amount'],e['id'],'GCAP')
        withheld=self.assess(day,month_closed=month_closed)
        required=max(0.,self.reserve()-oldreserve)+withheld
        inflows=principal+math.fsum(v for c,t,v,eid in reinvest)
        if required>inflows+1e-6:raise ValueError(('CORPORATE_TAX_UNFUNDED',day,required,inflows))
        withheld_from_reinvestment=0.
        for c,t,value,eid in reinvest:
            diverted=required*value/inflows if inflows else 0.;net=value-diverted
            after[c][t]-=diverted/quote[t,day]
            self.buy(day,c,t,net/quote[t,day],quote[t,day],eid+'_NET_REINVEST')
            withheld_from_reinvestment+=diverted
        emap={e['id']:e for e in events}
        for row in self.event_rows[event_row_start:]:
            t=row['ticker'] if 'ticker' in row else emap[row['event_id']]['ticker']
            e=emap[row['event_id']];child=e.get('successor') or (e.get('legs') or [('',0)])[0][0]
            row.update(fiscal_quantity_after_event_day=self.q[t],fiscal_cost_after_event_day=self.basis[t],
                successor=child,successor_quantity_after_event_day=self.q[child] if child else None,
                successor_cost_after_event_day=self.basis[child] if child else None)
        return after,withheld_from_reinvestment-withheld

    def final_liquidation(self,day,book,quote,cash):
        other=deepcopy(self)
        for c,u in sorted(book.items()):
            for t,q in sorted(u.items()):
                if q>1e-12:other.sell(day,c,t,q,quote[t,day],'HYPOTHETICAL_FINAL_LIQUIDATION');cash+=q*quote[t,day]
        cash-=other.assess(day,month_closed=True)
        monthly=other.monthly_rows()
        return dict(wealth=cash-other.liability,tax_increment=(other.withheld+other.liability)-(self.withheld+self.liability),
            liability=other.liability,cash_before_final_darf=cash,
            realized_gain=math.fsum(s['realized_gain_loss'] for s in other.sales[len(self.sales):]),
            rows=other.sales[len(self.sales):],monthly_tax=monthly)

    def monthly_rows(self):
        rows=deepcopy(self.taxrows)
        allocations=defaultdict(list)
        for code in ['6015','4600']:
            remaining={r['month']:r['darf_'+code] for r in rows}
            for payment in [p for p in self.payments if p['revenue_code']==code]:
                balance=payment['amount']
                for r in rows:
                    if due_date(r['month'],self.sessions)>payment['date']:continue
                    used=min(balance,remaining[r['month']]);balance-=used;remaining[r['month']]-=used
                    if used>1e-9:allocations[r['month'],code].append((payment['date'],used))
                if balance>1e-6:raise ValueError('Payment allocation mismatch')
        for r in rows:
            r.update(portfolio=self.portfolio,darf_due_date=due_date(r['month'],self.sessions),
                date_status='B3_SESSION_BANK_CALENDAR_PROXY')
            for code in ['6015','4600']:
                payments=allocations[r['month'],code]
                r['darf_'+code+'_paid']=sum(v for d,v in payments)
                r['darf_'+code+'_payment_dates']=';'.join(d for d,v in payments)
                r['darf_'+code+'_unpaid']=r['darf_'+code]-r['darf_'+code+'_paid']
            r['tax_reserved_at_close']=r['darf_6015']+r['darf_4600']
        # Tax per trade is an explicit pro-rata attribution of monthly liability,
        # not an independent per-trade computation of the exemption.
        for month in {r['date'][:7] for r in self.sales}:
            monthrow=next(r for r in rows if r['month']==month)
            selected=[r for r in self.sales if r['date'].startswith(month)]
            common=[r for r in selected if r['asset_tax_type'] in ['STOCK','BDR','ETF','RIGHT']
                    and not (r['asset_tax_type']=='STOCK' and monthrow['stock_exempt'])]
            groups=[(common,monthrow['common_tax']),
                ([r for r in selected if r['asset_tax_type']=='DAYTRADE'],monthrow['daytrade_tax']),
                ([r for r in selected if r['asset_tax_type']=='GCAP'],monthrow['gcap_tax'])]
            for r in selected:r['tax_due']=0.;r['irrf']=0.;r['tax_allocation']='PRO_RATA_MONTHLY_POSITIVE_GAINS_AFTER_LOSS_OFFSET'
            for group,tax in groups:
                total=sum(max(0,r['realized_gain_loss']) for r in group)
                for r in group:r['tax_due']=tax*max(0,r['realized_gain_loss'])/total if total else 0.
            ordinary=[r for r in selected if r['asset_tax_type'] in ['STOCK','BDR','ETF','RIGHT']]
            total=sum(r['gross_value'] for r in ordinary)
            for r in ordinary:r['irrf']=monthrow['ordinary_irrf']*r['gross_value']/total if total else 0.
            days=[r for r in selected if r['asset_tax_type']=='DAYTRADE'];positive=sum(max(0,r['realized_gain_loss']) for r in days)
            for r in days:r['irrf']=monthrow['daytrade_irrf']*max(0,r['realized_gain_loss'])/positive if positive else 0.
        return rows
