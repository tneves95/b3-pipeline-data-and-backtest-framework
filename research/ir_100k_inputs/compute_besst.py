import csv,glob,json,math,statistics,os
from datetime import datetime
# Load selection defs by executing build script pieces (sets U,D,Q,rows)
ns={}
work=os.environ.get('BG_WORK_ROOT','/mnt/data/work_v9')
script_root=os.environ.get('BG_SCRIPT_ROOT', os.path.dirname(__file__) if '__file__' in globals() else '/mnt/data/work_v9')
exec(open(os.path.join(script_root,'build_selection.py')).read(),ns)
U=ns['U']; D=ns['D']; Q=ns['Q']; rows=ns['rows']; sidmap=ns['sidmap']
root=os.environ.get('BG_V8_ROOT',os.path.join(work,'Barsi_Graham_Retomada_v8'))
# Quotes
quotes={}
for f in glob.glob(root+'/**/quotes_202*.csv',recursive=True):
  # only shortest matching originals to avoid duplicate irrelevant? identical keys overwrite okay
  for r in csv.DictReader(open(f,encoding='utf-8-sig')):
    try: quotes[(r['ticker'],r['date'])]=float(r['price'])
    except: pass
# exact v8 returns / portfolios for 2020
exact_ind={r['ticker']:float(r['return_value']) for r in csv.DictReader(open(root+'/resultados/retornos_individuais_besst2020_v8.csv',encoding='utf-8-sig'))}
exact_ports={(r['portfolio'],r['scenario']):float(r['return_value']) for r in csv.DictReader(open(root+'/resultados/retornos_besst2020_cenarios_v8.csv',encoding='utf-8-sig'))}
# yearly entry dates/prices/sectors
u_by={(int(r['entry_year']),r['ticker']):r for r in U if r.get('entry_price')}
entry_dates={y:next(r['entry_date'] for r in U if int(r['entry_year'])==y) for y in range(2020,2026)}
end_dates={2020:entry_dates[2021],2021:entry_dates[2022],2022:entry_dates[2023],2023:entry_dates[2024],2024:entry_dates[2025],2025:'2026-06-30'}
# sid by y,ticker
sid_by={(int(r['entry_year']),r['ticker']):r['sid'] for r in U}
qevents=[]
for s,d,q in Q:qevents.append((s,d.isoformat(),q))

def qtyfac(y,t,start,end):
  sid=sid_by.get((y,t)); f=1.0
  if not sid:return f
  for ss,d,q in qevents:
    if ss==sid and start<d<=end:f*=q
  return f

def dps_for(t,y):
  if t=='TRPL4' and y>=2025:t='ISAE4'
  if t=='TIMP3' and y>=2021:t='TIMS3'
  if t=='VIVT4' and y>=2020:t='VIVT3'
  return D.get(t,{}).get(y)
def cash_dps_for(t,y):
  if t=='TRPL4' and y>=2025:t='ISAE4'
  if t=='TIMP3' and y>=2021:t='TIMS3'
  if t=='VIVT4' and y>=2020:t='VIVT3'
  return T.get(t,{}).get(y)
# supplements for maintenance only / structural successors
D.setdefault('TIMS3',{}).update({2021:.43283051,2022:.826301372,2023:1.20224288,2024:1.446355353,2025:1.665064467})
D.setdefault('AESB3',{}).update({2021:.23088333,2022:.10745060,2023:0.0,2024:.07461181})
D.setdefault('AURE3',{}).update({2024:.40,2025:.06})
# Total cash by calendar right-year for realized-return approximation. Selection D above is recurring-oriented.
T={k:dict(v) for k,v in D.items()}
# restore known extraordinary/capital-return cash for realized returns
T.setdefault('BBSE3',{}).update({2018:3.080,2020:4.126})
T.setdefault('BBDC4',{}).update({2019:2.015})
T.setdefault('BRSR6',{}).update({2018:2.210})
T.setdefault('CSMG3',{}).update({2018:4.025,2020:8.363})
T.setdefault('VIVT3',{}).update({2024:2.803,2025:2.465,2026:2.212})
T.setdefault('VIVT4',{}).update({2020:3.415})
T.setdefault('TRPL4',{}).update({2020:1.740,2021:3.589,2022:1.062,2023:2.204})
T.setdefault('ISAE4',{}).update({2020:1.740,2021:3.589,2022:1.062,2023:2.204,2025:3.286,2026:.925})
# observed cash rights in specific June-to-June windows where annual 50/50 interpolation is materially poor
WINDOW_CASH={
 (2024,'TRPL4'): 3*0.786945, # Jan/Feb/Mar 2025 rights, declared Dec/24
 (2025,'ISAE4'): 3*0.2250 + 0.2506 + 2*0.2506 + 3*0.1413,
 (2025,'TRPL4'): 3*0.2250 + 0.2506 + 2*0.2506 + 3*0.1413,
 (2025,'VIVT3'): 0.1025+0.0779+0.1248+0.1186+0.1063+0.1095 + 0.1017+0.0626+0.1142+1.2517+0.1878+0.0720,
 (2025,'CPFE3'): 3.7315,
}

# actual/known cash rights in 2026H1 where quickly verifiable; excludes post-30Jun rights.
H1_2026={
'BBAS3':.4277,'PSSA3':1.9412,'CPFE3':3.7315,'EGIE3':.4883,'VIVT3':1.7900,'ISAE4':.9251,'EQTL3':0.0,'TAEE4':.4893,
'CMIG4':.6868,'CSMG3':.8461,'BBSE3':2.55,'ABCB4':1.168,'BBDC4':.4113,'ITUB4':.8200,'BMGB4':.1,'CPLE6':1.0626,
'SAPR4':0.0,'SANB4':.6478,'NEOE3':0.0
}

# Exact event-level checkpoints inherited from v6, when the same ticker/window exists.
# These supersede the material cash interpolation for the central estimate only.
EXACT_CASE_RET={}
case_dir=glob.glob(root+'/herdado_v7/herdado_v6/checkpoints/casos_v6')
if case_dir:
  for jf in glob.glob(case_dir[0]+'/*.json'):
    try:
      d=json.load(open(jf,encoding='utf-8'))
      cid=d.get('case_id','')
      parts=cid.rsplit('_',2)
      if len(parts)!=3: continue
      tt,ss,ee=parts
      st=d['state']; nav=st.get('nav',[])
      final=next((x.get('nav') for x in reversed(nav) if x.get('date')==ee and x.get('nav') is not None),None)
      if final is None: continue
      EXACT_CASE_RET[(tt,ss,ee)]=final/float(st.get('initial_value',10000.0))-1
    except Exception:
      pass

# central annual individual return and cash scaling
# material precision: price + quantity factors + half annual DPS from adjacent calendar years;
# 2025-26 uses 2025 run-rate for 2026 H1. cash_scale for sensitivity.
def annual_ind(y,t,cash_scale=1.0):
  if y==2020 and t in exact_ind and abs(cash_scale-1)<1e-12:
    return exact_ind[t]
  start=entry_dates[y]; end=end_dates[y]
  r=u_by[(y,t)]; p0=float(r['entry_price'])
  if abs(cash_scale-1.0)<1e-12 and (t,start,end) in EXACT_CASE_RET:
    return EXACT_CASE_RET[(t,start,end)]
  # OPA EDP after 2023 entry (inherited exact scenario)
  if t=='ENBR3' and y==2023:
    return 0.00465707
  # Neoenergia OPA / compulsory redemption in 2026. For a passive holder, use the
  # compulsory redemption of R$34.02 plus cash rights constituted after 30/06/2025
  # and before redemption (R$0.8930651324 per share). Cash then remains idle.
  if t=='NEOE3' and y==2025:
    return (34.02 + 0.8930651324*cash_scale)/p0 - 1
  # Eletrobras only changed ticker/name to AXIA3 on 10/11/2025 (1:1).
  # Post-30/06/2025 ON cash rights in 2025 total R$3.647180054; no 2026 H1 cash right used.
  if t=='ELET3' and y==2025:
    p_ax=quotes.get(('AXIA3','2026-06-30'))
    if p_ax is None: return None
    return (p_ax + 3.647180054*cash_scale)/p0 - 1
  et=t
  extra_cash=0.0
  if t=='TRPL4' and y==2024: et='ISAE4'
  if t=='CPLE6' and y==2025:
    et='CPLE3'; extra_cash=.7749
  p1=quotes.get((et,end))
  if p1 is None:
    # if end date absent due predecessor, use last quote <= end same year (rare)
    cand=[(d,p) for (tt,d),p in quotes.items() if tt==et and d<=end and d>=start]
    if cand:p1=max(cand)[1]
  if p1 is None: return None
  fac=qtyfac(y,t,start,end)
  if (y,t) in WINDOW_CASH:
    cash=WINDOW_CASH[(y,t)]*cash_scale + extra_cash
  elif (y,et) in WINDOW_CASH:
    cash=WINDOW_CASH[(y,et)]*cash_scale + extra_cash
  else:
    d0=cash_dps_for(t,y) or 0.0
    d1=cash_dps_for(et,y+1)
    if y==2025:
      # second-half 2025 proxied by half of full-year 2025; 2026H1 uses observed rights where available.
      d1=H1_2026.get(t, H1_2026.get(et, 0.5*d0)) * 2.0
    if d1 is None:d1=0.0
    cash=(0.5*d0 + 0.5*d1*fac)*cash_scale + extra_cash
  return (p1*fac+cash)/p0-1

def members(y,port,scenario):
  xs=[r for r in rows if r['year']==y]
  fld={'B00':('cash5','conservative_b00'),'B00S':('cash5','conservative_b00'),
       'B06':('B06','B06_cons'),'B06S':('B06','B06_cons')}[port][0 if scenario=='central' else 1]
  return [r for r in xs if r[fld]]

def weights(y,port,scenario):
  ms=members(y,port,scenario)
  if not ms:return {}
  if port.endswith('S'):
    sectors=sorted(set(r['sector'] for r in ms)); sw=1/len(sectors)
    w={}
    for sec in sectors:
      sm=[r for r in ms if r['sector']==sec]
      for r in sm:w[r['ticker']]=sw/len(sm)
    return w
  return {r['ticker']:1/len(ms) for r in ms}

annual=[]; indiv=[]
for y in range(2020,2026):
  for port in ['B00','B00S','B06','B06S']:
    for sc in ['central','conservative']:
      w=weights(y,port,sc); vals=[]; low=[]; high=[]
      for t,wt in w.items():
        if y==2020:
          rv=exact_ind[t]
          # use broader approx uncertainty for first-year exact? central exact; +/-2% cash in v8 ~0.1%, we'll use +/-0.15pp at portfolio later
          rlo=rhi=rv
        else:
          rv=annual_ind(y,t,1.0); rlo=annual_ind(y,t,.80); rhi=annual_ind(y,t,1.20)
        if rv is None: raise RuntimeError(f'missing return {y} {t}')
        vals.append(wt*rv); low.append(wt*rlo); high.append(wt*rhi)
        indiv.append({'year':y,'ticker':t,'portfolio':port,'scenario':sc,'weight':wt,'return':rv,'return_cash_low':rlo,'return_cash_high':rhi})
      ret=sum(vals); lo=sum(low); hi=sum(high)
      if y==2020:
        ret=exact_ports[(port,sc)]; lo=ret-.0015; hi=ret+.0015
      annual.append({'year':y,'start':entry_dates[y],'end':end_dates[y],'portfolio':port,'scenario':sc,'n':len(w),'return':ret,'cash_low':lo,'cash_high':hi})

# chain renewable from each start through 2026
renew=[]
for port in ['B00','B00S','B06','B06S']:
 for sc in ['central','conservative']:
  for sy in range(2020,2026):
   fac=lofac=hifac=1.0
   for y in range(sy,2026):
    r=next(x for x in annual if x['year']==y and x['portfolio']==port and x['scenario']==sc)
    fac*=1+r['return']; lofac*=1+r['cash_low']; hifac*=1+r['cash_high']
   yrs=(datetime.strptime('2026-06-30','%Y-%m-%d')-datetime.strptime(entry_dates[sy],'%Y-%m-%d')).days/365.25
   renew.append({'portfolio':port,'scenario':sc,'start_year':sy,'start':entry_dates[sy],'end':'2026-06-30','return':fac-1,'cash_low':lofac-1,'cash_high':hifac-1,'cagr':fac**(1/yrs)-1,'final_10000':10000*fac})

# output
out=os.environ.get('BG_RESULTS_ROOT',os.path.join(work,'results_v9')); os.makedirs(out,exist_ok=True)
for fn,data in [('besst_annual.csv',annual),('besst_individual_annual.csv',indiv),('besst_renewal.csv',renew)]:
  with open(os.path.join(out,fn),'w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(data[0].keys())); w.writeheader(); w.writerows(data)
print('\nANNUAL')
for y in range(2020,2026):
 print(y,[(x['portfolio'],x['scenario'],round(x['return']*100,2),x['n']) for x in annual if x['year']==y])
print('\nFULL RENEW')
for x in renew:
 if x['start_year']==2020: print(x['portfolio'],x['scenario'],round(x['return']*100,2),round(x['cagr']*100,2),round(x['final_10000']), 'cashband',round(x['cash_low']*100,2),round(x['cash_high']*100,2))
