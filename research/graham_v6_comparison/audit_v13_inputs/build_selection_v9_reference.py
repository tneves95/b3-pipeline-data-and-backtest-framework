import csv, glob, statistics, json, math, os
from datetime import date, datetime
work=os.environ.get('BG_WORK_ROOT','/mnt/data/work_v9')
root=os.environ.get('BG_V8_ROOT',os.path.join(work,'Barsi_Graham_Retomada_v8'))
univ=glob.glob(root+'/**/universo_besst_triagem.csv',recursive=True)[0]
events=glob.glob(root+'/**/eventos_quantidade_herdados.csv',recursive=True)[0]
U=list(csv.DictReader(open(univ,encoding='utf-8-sig')))
# ordinary / recurring-oriented annual DPS. Explicit capital returns / explicit extraordinary cash removed where known.
D={
'BBAS3':{2015:2.076,2016:.910,2017:.942,2018:1.510,2019:2.543,2020:1.472,2021:2.262,2022:4.139,2023:4.540,2024:3.219,2025:1.170},
'NEOE3':{2015:.30,2016:.30,2017:.30,2018:.186,2019:.578,2020:.409,2021:.526,2022:.799,2023:1.157,2024:1.090,2025:1.461}, # 15-17 proxy only for central no-cap continuity; not used cap until all five observed post-2018
'PSSA3':{2015:1.744,2016:1.328,2017:1.503,2018:4.037,2019:2.121,2020:2.141,2021:2.612,2022:1.159,2023:1.411,2024:1.543,2025:1.987},
'CPFE3':{2015:0,2016:.207,2017:.31,2018:.275,2019:.480,2020:1.801,2021:3.701,2022:3.242,2023:2.886,2024:2.754,2025:2.794},
'EGIE3':{2015:1.222,2016:1.972,2017:2.716,2018:4.218,2019:1.623,2020:1.725,2021:1.788,2022:2.989,2023:2.901,2024:2.668,2025:1.845},
'TIMP3':{2015:.1518,2016:.1936,2017:.139997,2018:.393892,2019:.465899,2020:.413},
'VIVT4':{2015:3.839,2016:1.327,2017:2.646,2018:4.119,2019:3.700},
'VIVT3':{2015:3.839,2016:1.327,2017:2.646,2018:4.119,2019:3.700,2020:3.415,2021:3.463,2022:3.056,2023:2.058,2024:1.895,2025:1.239},
'TRPL4':{2015:.5672445,2016:.37563575,2017:.759467,2018:.510,2019:1.060,2020:1.740,2021:3.589,2022:1.062,2023:2.204},
'ISAE4':{2015:.5672445,2016:.37563575,2017:.759467,2018:.510,2019:1.060,2020:1.740,2021:3.589,2022:1.062,2023:2.204,2025:3.286},
'EQTL3':{2015:.830,2016:.930,2017:.580,2018:1.211,2019:.950,2020:.320,2021:.720,2022:.640,2023:.350,2024:.450,2025:.789},
'ENBR3':{2015:.164,2016:1.151,2017:.120,2018:1.210,2019:.452,2020:.194,2021:1.000,2022:2.194,2023:1.420},
'TIET4':{2015:.7082,2016:.4324,2017:.1649,2018:.1560,2019:.1658,2020:.20},
'COCE5':{2015:.537,2016:.926,2017:1.992,2018:1.092,2019:1.870,2020:2.124,2021:3.616,2022:1.943,2023:.308,2024:.988,2025:1.352},
'TAEE4':{2015:.732,2016:.901,2017:.589,2018:.929,2019:.630,2020:1.070,2021:1.501,2022:1.618,2023:.972,2024:1.177,2025:1.076},
'OMGE3':{2018:.181},
'CMIG4':{2015:.610,2016:.496,2017:.122,2018:.644,2019:.725,2020:.614,2021:1.176,2022:1.532,2023:1.291,2024:1.059,2025:.898},
'CSMG3':{2015:.089,2016:.672,2017:2.094,2018:1.8097,2019:1.727,2020:.6251,2021:.945,2022:.384,2023:2.893,2024:2.772,2025:2.284}, # 2020 recurring rights re-expressed to post-split base; Copasa split occurred within 2020
'BBSE3':{2015:1.6747,2016:1.6525,2017:1.6168,2018:1.7276,2019:1.5679,2020:2.774,2021:.996,2022:1.953,2023:3.448,2024:2.633,2025:4.214},
'CXSE3':{2021:.245,2022:.649,2023:1.000,2024:1.065,2025:1.260},
'ABCB4':{2015:.865,2016:1.087,2017:1.086,2018:1.079,2019:1.050,2020:.159,2021:1.254,2022:1.397,2023:1.577,2024:1.645,2025:2.618},
'SBSP3':{2015:.369,2016:.219,2017:1.205,2018:1.030,2019:1.159,2020:1.377,2021:.398,2022:.943,2023:1.276,2024:1.440,2025:6.361},
'BBDC4':{2015:1.425,2016:1.328,2017:1.247,2018:1.148,2019:.97148,2020:.707,2021:1.026,2022:.424,2023:1.697,2024:1.114,2025:1.436},
'ITUB4':{2015:1.579,2016:1.705,2017:1.499,2018:3.183,2019:2.805,2020:1.304,2021:.909,2022:1.018,2023:1.257,2024:2.413,2025:4.732},
'BMGB4':{2019:.250,2020:.179,2021:.316,2022:.365,2023:.376,2024:.370,2025:.547},
'CPLE6':{2015:1.063,2016:1.255,2017:2.962,2018:1.163,2019:2.846,2020:3.100,2021:1.310,2022:.886,2023:.334,2024:.424,2025:.437},
'SAPR4':{2015:.520,2016:.630,2017:.662,2018:.681,2019:.876,2020:.202,2021:.222,2022:.307,2023:.309,2024:.316,2025:.399},
'SANB4':{2015:.863,2016:.070,2017:.775,2018:.925,2019:1.095,2020:1.469,2021:1.485,2022:1.174,2023:.874,2024:.843,2025:.983},
'BRSR6':{2015:.904,2016:.607,2017:.715,2018:1.3462,2019:1.244,2020:.657,2021:.954,2022:.881,2023:.917,2024:.995,2025:1.603},
'ELET3':{2018:0,2019:.83,2020:.03,2021:2.40,2022:.74,2023:.59,2024:.67,2025:2.66},
'ENEV3':{},'BRIT3':{},'FIQE3':{2021:.083,2022:.084,2023:.155,2024:.212,2025:.878},'DESK3':{2022:.014,2023:.020,2024:.042,2025:.139},
}
# build ticker->sid by year
sidmap={(int(r['entry_year']),r['ticker']):r['sid'] for r in U}
# quantity events
Q=[]
for r in csv.DictReader(open(events,encoding='utf-8-sig')):
    try: Q.append((r['sid'],datetime.strptime(r['date'],'%Y-%m-%d').date(),float(r['q'])))
    except: pass
# normalize annual dps from year-end share base to entry base for material splits/bonuses after that year.
def norm_dps(ticker, y, entry_year, entry_date):
    val=D.get(ticker,{}).get(y)
    if val is None: return None
    sid=sidmap.get((entry_year,ticker))
    if not sid: return val
    fac=1.0
    yend=date(y,12,31)
    ed=datetime.strptime(entry_date,'%Y-%m-%d').date()
    for s,d,q in Q:
        if s==sid and yend < d <= ed:
            # q is factor in inherited source. Ignore suspicious reductions unless actual reverse split; multiplication is appropriate generally.
            fac*=q
    return val/fac

# pre-cash continuity exceptions centrally allowed despite missing public listed 5y ledger
central_continuity={'NEOE3'}
# explicit cash history fails when any of 5 prior years has no positive DPS and no continuity exception
def cash5(t, y):
    years=range(y-5,y)
    vals=[D.get(t,{}).get(a) for a in years]
    if t in central_continuity and y<=2022: return True
    return all(v is not None and v>0 for v in vals)
# low recurrence conservative rule + NEOE continuity pre-2023
rows=[]; ports=[]
for y in range(2020,2026):
  candidates=[r for r in U if int(r['entry_year'])==y and r['preselection_pass']=='1']
  for r in candidates:
    t=r['ticker']; vals=[float(r[f'profit_l{i}']) for i in range(5)]; med=statistics.median(vals); ratio=min(vals)/med if med else 0
    b00= cash5(t,y)
    # preserve v8 CPFE 2020 exclusion (cash2015=0 already does); NEOE central continuity
    cons=b00 and ratio>=.30 and not (t=='NEOE3' and y<=2022)
    yrs=list(range(y-5,y)); nd=[norm_dps(t,a,y,r['entry_date']) for a in yrs]
    # NEOE cap is unresolved until actual 2018-2022 full five-year observed window
    cap_resolved=all(v is not None and v>0 for v in nd) and not (t=='NEOE3' and y<=2022)
    avg=sum(nd)/5 if cap_resolved else None; cap=avg/.06 if avg is not None else None; margin=cap/float(r['entry_price'])-1 if cap is not None else None
    b06=b00 and cap_resolved and margin>=0
    # conservative B06: apply conservative b00 + remove borderline <=2%, and suppress suspicious dividend-spike cases if cap is driven by one annual >2.5x median
    spike=False
    if cap_resolved:
      med_d=statistics.median(nd); spike=max(nd)>2.5*med_d if med_d>0 else False
    b06cons=cons and b06 and (margin is None or margin>0.02) and not spike
    rows.append({'year':y,'ticker':t,'sector':r['besst_sector'],'price':float(r['entry_price']),'profit_ratio':ratio,'cash5':int(b00),'conservative_b00':int(cons),'dps_norm':nd,'dps_avg':avg,'cap':cap,'margin':margin,'spike':int(spike),'B06':int(b06),'B06_cons':int(b06cons)})
  # build weights later

# force 2020 exactly v8 selections for consistency
v8=os.path.join(root,'resultados/carteiras_besst2020_cenarios_v8.csv')
v8r=list(csv.DictReader(open(v8,encoding='utf-8-sig')))
for rr in rows:
 if rr['year']==2020:
  t=rr['ticker']
  rr['cash5']=int(any(x['portfolio']=='B00' and x['scenario']=='central' and x['ticker']==t for x in v8r))
  rr['conservative_b00']=int(any(x['portfolio']=='B00' and x['scenario']=='conservative' and x['ticker']==t for x in v8r))
  rr['B06']=int(any(x['portfolio']=='B06' and x['scenario']=='central' and x['ticker']==t for x in v8r))
  rr['B06_cons']=int(any(x['portfolio']=='B06' and x['scenario']=='conservative' and x['ticker']==t for x in v8r))

# print selection summary
for y in range(2020,2026):
 xs=[r for r in rows if r['year']==y]
 print('\nYEAR',y)
 for fld in ['cash5','conservative_b00','B06','B06_cons']:
  ms=[r['ticker'] for r in xs if r[fld]]
  print(fld,len(ms),ms)
 print('B06 margins',[(r['ticker'],round(r['margin']*100,1) if r['margin'] is not None else None, r['spike']) for r in xs if r['cash5']])

out=os.path.join(work,'selection_rows.json'); json.dump(rows,open(out,'w'),ensure_ascii=False,indent=2)
