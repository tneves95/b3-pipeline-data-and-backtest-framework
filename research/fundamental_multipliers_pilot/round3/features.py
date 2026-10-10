"""Historical features from exact annual filing versions known at formation."""
from __future__ import annotations
from bisect import bisect_right
from collections import defaultdict
import calendar
import json
import math
import numpy as np
import pandas as pd
from ..audit import HERE, ROOT, choose_known_filing


def divide(a,b):
    return float(a/b) if pd.notna(a) and pd.notna(b) and b>0 else np.nan


def statement(metadata,values,cnpj,period,cutoff):
    m=choose_known_filing(metadata,cutoff,period)
    if m is None:return {},'NO_PRIOR_KNOWN_FILING'
    fid=f"{cnpj}_DFP_{period}_{int(m.version)}"
    v=values.get(fid)
    if v is None:return {},'EXACT_KNOWN_VERSION_VALUES_MISSING'
    if str(v.get('filing_date',m.received))!=str(m.received):
        return {},'RECEIPT_DISAGREEMENT'
    if str(m.received)>=cutoff:raise ValueError('LOOKAHEAD_RECEIPT')
    return v,'EXACT_KNOWN_VERSION_AVAILABLE'


def ibov_series(root):
    values={}
    for path in sorted((root/'research/returns_2014_2026_inputs/b3').glob('ibov_*.json')):
        year=int(path.stem.split('_')[-1]);data=json.loads(path.read_text())
        for r in data['results']:
            day=int(r['day'])
            for month in range(1,13):
                v=r.get(f'rateValue{month}')
                if not v or day>calendar.monthrange(year,month)[1]:continue
                values[f'{year}-{month:02}-{day:02}']=float(str(v).replace('.','').replace(',','.'))
    dates=sorted(values)
    def asof(day):
        i=bisect_right(dates,day)-1
        if i<0:raise ValueError('IBOV_BEFORE_HISTORY')
        if (pd.Timestamp(day)-pd.Timestamp(dates[i])).days>10:raise ValueError('IBOV_STALE')
        return values[dates[i]]
    return asof


def make_features(book,panel,events,output,protocol):
    meta=pd.read_csv(HERE/'local_only/data/annual_filing_versions.csv',dtype={'cnpj':str})
    meta=meta[meta.doc_type=='DFP'].copy()
    meta['version']=pd.to_numeric(meta.version);meta['docid']=pd.to_numeric(meta.docid)
    by_company={c:g for c,g in meta.groupby('cnpj')}
    f=pd.read_sql_query("SELECT * FROM fundamentals_pit WHERE doc_type='DFP'",book.conn)
    values={r['filing_id']:r for r in f.to_dict('records')}
    recovered=pd.read_csv(HERE/'local_only/round2/filing_recovery.csv',dtype={'cnpj':str})
    for r in recovered.to_dict('records'):
        values[r['required_filing_id']]=dict(r,filing_date=r['required_received'],ebitda=r['ebit'])
    grouped=defaultdict(list)
    for e in events:grouped[e['ticker']].append(e)
    uncertainty=pd.read_csv(output/'scaled_material_uncertainty.csv')
    risk_dates={i:g.date.tolist() for i,g in uncertainty.groupby('isin')}
    rows=[];history=[]
    for p in panel.to_dict('records'):
        c=p['cnpj'];day=p['formation_date'];year=int(p['year']);period=f'{year-1}-12-31'
        statements=[]
        for offset in range(4):
            ref=f'{year-1-offset}-12-31'
            v,status=statement(by_company.get(c,meta.iloc[:0]),values,c,ref,day)
            statements.append(v);history.append(dict(cnpj=c,formation_date=day,period=ref,status=status,
                filing_id=v.get('filing_id'),received=v.get('filing_date')))
        # Accepted round2 values are the exact latest required annual statement,
        # including recovered originals. Never substitute an older annual filing.
        now={k:p.get('raw_'+k,np.nan) for k in ['revenue','net_income','total_assets',
            'current_assets','current_liabilities','operating_cash_flow','financial_debt','equity']}
        now['ebit']=p.get('raw_ebit',np.nan)
        if pd.isna(now['ebit']):now['ebit']=p.get('raw_ebitda',np.nan)  # parser stores EBIT; no EBITDA claim
        r={k:p[k] for k in ['cnpj','year','formation_date','ticker','isin','sector','financial_sector','statement_status']}
        r['sector_group']=str(p.get('sector','UNKNOWN')).replace('Emp. Adm. Part. - ','')
        if r['sector_group'] in ['nan','None','']:r['sector_group']='UNKNOWN'
        r['assets']=now['total_assets'];r['liquidity_proxy']=p['financial_volume_h1']
        for feature in protocol['indicators']:r[feature]=np.nan
        ni=now['net_income'];rev=now['revenue'];cash=now['operating_cash_flow'];assets=now['total_assets']
        r['income_positive']=float(ni>0) if pd.notna(ni) else np.nan
        r['net_margin']=divide(ni,rev)
        prior=statements[1];older=statements[3]
        eq0=prior.get('equity',np.nan);eq1=now['equity']
        avg=(eq0+eq1)/2 if pd.notna(eq0) and pd.notna(eq1) and eq0>0 and eq1>0 else np.nan
        r['roe_average_equity']=divide(ni,avg)
        r['revenue_growth_1y']=divide(rev,prior.get('revenue',np.nan))-1
        r['revenue_growth_3y']=divide(rev,older.get('revenue',np.nan))**(1/3)-1 if pd.notna(rev) and rev>0 else np.nan
        profits=[ni]+[s.get('net_income',np.nan) for s in statements[1:3]]
        r['income_consistency_3y']=float(all(x>0 for x in profits)) if all(pd.notna(x) for x in profits) else np.nan
        nonfinance=p['financial_sector']==False and pd.notna(p.get('sector'))
        if nonfinance:
            r['operating_margin']=divide(now['ebit'],rev)
            r['ocf_to_positive_income']=divide(cash,ni)
            r['current_ratio']=divide(now['current_assets'],now['current_liabilities'])
            r['financial_debt_assets']=divide(now['financial_debt'],assets)
            r['ocf_assets']=divide(cash,assets)
        # Raw-price trailing cash yield is a feature approximation, independent
        # of future returns. No valuation numerator uses adjusted prices.
        begin=(pd.Timestamp(day)-pd.DateOffset(years=1)).strftime('%Y-%m-%d')
        known=[e for e in grouped[p['isin']] if begin<e['ex_date']<=day]
        risk=any(e['kind'] not in ['SHARES','DISTRIBUTION','NO_ENTITLEMENT'] for e in known)
        risk=risk or any(begin<date<=day for date in risk_dates.get(p['isin'],[]))
        if year>2014 and not risk:
            try:
                dividend=0.
                for e in known:
                    if e['kind']!='DISTRIBUTION':continue
                    factor=math.prod(q['factor'] for q in known if q['kind']=='SHARES' and q['ex_date']>=e['ex_date'])
                    dividend+=e['amount']/factor
                r['dividend_yield']=dividend/book.trade(p['isin'],day)['close']
            except ValueError:pass
        # Per-share earnings require contemporaneous class capital; leave payout
        # and valuation missing rather than mixing old earnings with future shares.
        rows.append(r)
    frame=pd.DataFrame(rows)
    # Porte is explicitly book assets, not fabricated historical market value.
    frame['size_tercile']=frame.groupby('year').assets.transform(
        lambda x:np.ceil(x.rank(method='min',pct=True)*3)).map({1:'SMALL_ASSETS',2:'MID_ASSETS',3:'LARGE_ASSETS'}).fillna('UNKNOWN')
    frame.to_csv(output/'features_pit.csv',index=False)
    pd.DataFrame(history).to_csv(output/'historical_statement_provenance.csv',index=False)
    reasons={'pe':'Historical issued/treasury/class/unit capital not reconciled at cutoff',
        'pb':'Historical issued/treasury/class/unit capital not reconciled at cutoff',
        'ev_ebitda':'Parser EBIT is not EBITDA; actual historical EBITDA unavailable',
        'roic':'Consistent historical NOPAT and invested capital unavailable',
        'payout':'Per-share earnings require compatible historical capital',
        'dividend_yield':'Approximate trailing gross cash yield; ex-date shares normalized, not exact accounting payout'}
    (output/'feature_limitations.json').write_text(json.dumps(reasons,ensure_ascii=False,indent=2)+'\n')
    return frame


def join_matrix(matrix,features,root):
    features=features.drop(columns=['year','ticker','isin','sector','financial_sector'])
    frame=matrix.merge(features,on=['cnpj','formation_date'],validate='many_to_one')
    benchmark=ibov_series(root)
    frame['ibov_wealth']=np.nan
    for i,r in frame[frame.calendar_complete].iterrows():
        frame.loc[i,'ibov_wealth']=benchmark(r.calendar_endpoint)/benchmark(r.formation_date)
    frame['relative_ibov_return']=frame.wealth_multiple/frame.ibov_wealth-1
    return frame
