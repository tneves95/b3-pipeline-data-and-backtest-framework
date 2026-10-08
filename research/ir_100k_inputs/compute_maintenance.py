import csv,glob,json,math,os
from datetime import datetime
ns={}
work=os.environ.get('BG_WORK_ROOT','/mnt/data/work_v9')
script_root=os.environ.get('BG_SCRIPT_ROOT', os.path.dirname(__file__) if '__file__' in globals() else '/mnt/data/work_v9')
exec(open(os.path.join(script_root,'compute_besst.py')).read(),ns)
# imported objects from compute_besst
U=ns['U'];D=ns['D'];T=ns['T'];Q=ns['Q'];quotes=ns['quotes'];exact_ind=ns['exact_ind'];entry_dates=ns['entry_dates'];end_dates=ns['end_dates'];rows=ns['rows'];weights=ns['weights'];u_by=ns['u_by'];H1_2026=ns['H1_2026'];WINDOW_CASH=ns['WINDOW_CASH'];EXACT_CASE_RET=ns['EXACT_CASE_RET']
# improve successor cash rights for 2025-26 where primary dates are known
WINDOW_CASH_2025_26={
    'TIMS3': 0.1323151001+0.1994595735+0.1757968072+0.7482883774+0.1632708888+0.1674573219,
    'AURE3': 0.0,
}
# sid map for generic ticker paths (same legal share class in each annual window)
sid_any={}
for r in U:
    if r.get('sid') and r.get('ticker'): sid_any.setdefault(r['ticker'],r['sid'])
qev=[(s,d.isoformat(),q) for s,d,q in Q]

def qfac_state(t,start,end):
    sid=sid_any.get(t)
    if not sid:return 1.0
    f=1.0
    for s,d,q in qev:
        if s==sid and start<d<=end:f*=q
    return f

def dps(t,y):
    # successor code continuity
    if t=='TIMP3' and y>=2021:t='TIMS3'
    if t=='VIVT4' and y>=2020:t='VIVT3'
    if t=='TRPL4' and y>=2025:t='ISAE4'
    return T.get(t,{}).get(y,0.0) or 0.0

def end_ticker_for_segment(t,y):
    if t=='TRPL4' and y==2024:return 'ISAE4'
    if t=='CPLE6' and y==2025:return 'CPLE3'
    return t

def generic_segment(shares,cash,t,y,cash_scale=1.0):
    start=entry_dates[y]; end=end_dates[y]
    et=end_ticker_for_segment(t,y)
    p1=quotes.get((et,end))
    if p1 is None:
        cand=[(d,p) for (tt,d),p in quotes.items() if tt==et and start<=d<=end]
        if not cand: raise RuntimeError(f'No end quote {t}->{et} {y} {end}')
        p1=max(cand)[1]
    fac=qfac_state(t,start,end)
    start_shares=shares
    shares*=fac
    if (y,t) in WINDOW_CASH:
        cps=WINDOW_CASH[(y,t)]
    elif (y,et) in WINDOW_CASH:
        cps=WINDOW_CASH[(y,et)]
    elif y==2025 and t in WINDOW_CASH_2025_26:
        cps=WINDOW_CASH_2025_26[t]
    else:
        d0=dps(t,y)
        if y==2025:
            # same material-precision convention used in annual-renewal engine
            h1=H1_2026.get(t,H1_2026.get(et,0.5*d0))
            d1=2.0*h1
        else:
            d1=dps(et,y+1)
        cps=0.5*d0+0.5*d1*fac
    div_cash=start_shares*cps*cash_scale
    # theoretical reinvestment in the surviving security at interval end; preserves return convention approximately
    shares += div_cash/p1
    # CPLE6 reorganization: capital redemption is not reinvested and remains cash
    if t=='CPLE6' and y==2025:
        cash += start_shares*0.7749
    return shares,cash,et

def aesb_merger_segment(shares,cash,cash_scale=1.0,option='default'):
    # 28/06/2024 -> 30/06/2025. AESB April dividend is before interval start.
    # B3 adjusted factors; option 1 is default if shareholder does not elect another option.
    if option=='default':
        ratio=0.67498865568; cash_leg=1.18438832610
    elif option=='all_cash':
        ratio=0.0; cash_leg=11.84388326100
    else: raise ValueError(option)
    old=shares
    cash += old*cash_leg
    shares=old*ratio
    if shares>0:
        p1=quotes[('AURE3','2025-06-30')]
        # AURE dividend whose right occurred after the combination, Apr/2025.
        post_div=0.05703266*cash_scale
        shares += old*ratio*post_div/p1
    return shares,cash,('AURE3' if shares>0 else 'CASH')

def simulate_holding(start_year,ticker,cash_scale=1.0,aes_option='default'):
    # wealth normalized to 1 at formation date
    cash=0.0
    state=ticker
    # first interval can use exact v8 event-level return for 2020
    if start_year==2020:
        rv=exact_ind[ticker]
        state={'TIMP3':'TIMS3','VIVT4':'VIVT3','TIET4':'AESB3'}.get(ticker,ticker)
        p1=quotes.get((state,entry_dates[2021]))
        if p1 is None: raise RuntimeError(f'No 2021 quote for successor {ticker}->{state}')
        shares=(1+rv)/p1
        year=2021
    else:
        p0=quotes.get((ticker,entry_dates[start_year]))
        if p0 is None:
            # entry price in universe is authoritative if exact date quote missing
            rr=next(r for r in U if int(r['entry_year'])==start_year and r['ticker']==ticker)
            p0=float(rr['entry_price'])
        shares=1.0/p0
        year=start_year
    # run through remaining annual windows
    while year<=2025:
        if state=='CASH':
            year+=1; continue
        if state=='ENBR3' and year==2023:
            # inherited OPA scenario: cash at R$23.73 on 11/07/2023, thereafter idle
            cash += shares*23.73
            shares=0.0; state='CASH'; year+=1; continue
        if state=='NEOE3' and year==2025:
            # passive holder through compulsory redemption on 15/05/2026: R$34.02,
            # plus R$0.8930651324 of post-30/06/2025 cash rights; thereafter idle cash.
            cash += shares*(34.02 + 0.8930651324*cash_scale)
            shares=0.0; state='CASH'; year+=1; continue
        if state=='ELET3' and year==2025:
            # Pure ticker/name change ELET3 -> AXIA3, 1:1. Cash rights after 30/06/2025: R$3.647180054/ON.
            p1=quotes[('AXIA3','2026-06-30')]
            div=shares*3.647180054*cash_scale
            shares += div/p1
            state='AXIA3'; year+=1; continue
        if state=='AESB3' and year==2024:
            shares,cash,state=aesb_merger_segment(shares,cash,cash_scale,aes_option)
            year+=1; continue
        shares,cash,state=generic_segment(shares,cash,state,year,cash_scale)
        year+=1
    # final mark
    if state=='CASH' or shares==0:
        stock=0.0
    else:
        p=quotes.get((state,'2026-06-30'))
        if p is None: raise RuntimeError(f'No final quote {state}')
        stock=shares*p
    return {'factor':stock+cash,'stock':stock,'cash':cash,'final_state':state,'shares':shares}

# compute maintenance portfolio results per formation/scenario
out=[];hold=[]
for sy in range(2020,2026):
    for port in ['B00','B00S','B06','B06S']:
        for sc in ['central','conservative']:
            w=weights(sy,port,sc)
            if not w: continue
            vals=[];lows=[];highs=[]
            for t,wt in w.items():
                a=simulate_holding(sy,t,1.0,'default')
                lo=simulate_holding(sy,t,.95,'default')
                hi=simulate_holding(sy,t,1.05,'default')
                # Where v6 has an event-level checkpoint for the full same-ticker horizon, anchor the central
                # factor to that exact result and retain only the cash-sensitivity delta from the material model.
                exret=EXACT_CASE_RET.get((t,entry_dates[sy],'2026-06-30'))
                if exret is not None:
                    approx=a['factor']; exactfac=1.0+exret
                    lo['factor']=exactfac + (lo['factor']-approx)
                    hi['factor']=exactfac + (hi['factor']-approx)
                    a['factor']=exactfac
                    a['final_state']=a.get('final_state',t)+' [EXACT_V6_ANCHOR]'
                vals.append(wt*a['factor']); lows.append(wt*lo['factor']); highs.append(wt*hi['factor'])
                hold.append({'start_year':sy,'portfolio':port,'scenario':sc,'ticker':t,'weight':wt,'factor':a['factor'],'return':a['factor']-1,'cash_low_factor':lo['factor'],'cash_high_factor':hi['factor'],'final_state':a['final_state'],'final_cash':a['cash'],'final_stock':a['stock']})
            fac=sum(vals); lof=sum(lows); hif=sum(highs)
            yrs=(datetime.strptime('2026-06-30','%Y-%m-%d')-datetime.strptime(entry_dates[sy],'%Y-%m-%d')).days/365.25
            out.append({'start_year':sy,'start':entry_dates[sy],'end':'2026-06-30','portfolio':port,'scenario':sc,'n':len(w),'return':fac-1,'cash_low':lof-1,'cash_high':hif-1,'cagr':fac**(1/yrs)-1,'final_10000':10000*fac})
# AES default-option sensitivity for affected maintenance portfolios: recompute all, switching AESB merger to all-cash where applicable
sens=[]
for sy in range(2020,2025):
 for port in ['B00','B00S','B06','B06S']:
  for sc in ['central','conservative']:
   w=weights(sy,port,sc)
   if not w:continue
   if not any(t in ('TIET4','AESB3') for t in w):continue
   fac_def=0;fac_cash=0
   for t,wt in w.items():
    fac_def+=wt*simulate_holding(sy,t,1.0,'default')['factor']
    fac_cash+=wt*simulate_holding(sy,t,1.0,'all_cash')['factor']
   sens.append({'start_year':sy,'portfolio':port,'scenario':sc,'default_return':fac_def-1,'all_cash_return':fac_cash-1,'diff_pp':(fac_cash-fac_def)*100})

od=os.environ.get('BG_RESULTS_ROOT',os.path.join(work,'results_v9'));os.makedirs(od,exist_ok=True)
for fn,data in [('besst_maintenance.csv',out),('besst_maintenance_holdings.csv',hold),('besst_aes_sensitivity.csv',sens)]:
    with open(os.path.join(od,fn),'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0].keys()));w.writeheader();w.writerows(data)
print('MAINTENANCE CENTRAL/CONS')
for sy in range(2020,2026):
 print('\n',sy)
 for r in out:
  if r['start_year']==sy:print(r['portfolio'],r['scenario'],round(r['return']*100,2),round(r['cagr']*100,2),round(r['final_10000']), 'cashband',round(r['cash_low']*100,2),round(r['cash_high']*100,2))
print('\nAES SENS')
for r in sens:print(r)
