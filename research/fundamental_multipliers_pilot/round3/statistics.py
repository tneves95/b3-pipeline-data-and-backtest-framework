"""Frozen exploratory estimands, company dependence and missing-outcome bounds.

Resampling intervals condition on this observed calendar. There are too few
independent horizon-sized periods for confirmatory time-general p-values.
"""
from __future__ import annotations
import json
import math
import numpy as np
import pandas as pd
from scipy import stats

FILTERS={
    'positive_income':('income_positive',lambda x:x==1),
    'cash_conversion':('ocf_to_positive_income',lambda x:x>=1),
    'margin_positive':('operating_margin',lambda x:x>0),
    'liquidity':('current_ratio',lambda x:x>=1),
    'leverage_low':('financial_debt_assets',lambda x:x<=.4),
    'roe_high':('roe_average_equity',lambda x:x>=.15),
    'cash_assets_positive':('ocf_assets',lambda x:x>0),
    'revenue_growing':('revenue_growth_1y',lambda x:x>0),
    'income_consistent':('income_consistency_3y',lambda x:x==1),
    'pe_low':('pe',lambda x:(x>0)&(x<=10)),
    'pb_low':('pb',lambda x:(x>0)&(x<=1.5)),
    'dividend_yield_high':('dividend_yield',lambda x:x>=.04),
}


def filter_mask(frame,names):
    all_known=pd.Series(True,index=frame.index);selected=all_known.copy()
    rejected=pd.Series(False,index=frame.index)
    for name in names:
        feature,predicate=FILTERS[name]
        available=frame[feature].notna();condition=predicate(frame[feature])
        all_known &= available
        rejected |= available & ~condition
        selected &= available & condition
    # AND has a known false result as soon as one condition fails. A firm with
    # negative profit is rejected by profit+cash, never silently lost because
    # FCO/positive profit is undefined. Missing inputs alone remain unknown.
    return all_known | rejected,selected


def partitions(frame,horizon,protocol):
    oos=protocol['oos'][f'{horizon}y']
    result={'ALL':frame,'DEVELOPMENT':frame[frame.year.isin(oos['development'])],
        'OOS':frame[frame.year.isin(oos['evaluation'])],
        'PURGED_DESCRIPTIVE':frame[frame.year.isin(oos['purged'])]}
    return result


def missing_binary_bounds(selected_loss,rejected_loss,selected_win,rejected_win,
                          selected_known,rejected_known,selected_unknown,rejected_unknown):
    ns=selected_known+selected_unknown;nr=rejected_known+rejected_unknown
    if not ns or not nr:return {k:np.nan for k in ['loss_advantage_low','loss_advantage_high','bombs_avoided_low','bombs_avoided_high','winners_excluded_low','winners_excluded_high']}
    fraction=lambda a,b:a/b if b else np.nan
    return dict(loss_advantage_low=rejected_loss/nr-(selected_loss+selected_unknown)/ns,
        loss_advantage_high=(rejected_loss+rejected_unknown)/nr-selected_loss/ns,
        bombs_avoided_low=fraction(rejected_loss,rejected_loss+selected_loss+selected_unknown),
        bombs_avoided_high=fraction(rejected_loss+rejected_unknown,rejected_loss+rejected_unknown+selected_loss),
        winners_excluded_low=fraction(rejected_win,rejected_win+selected_win+selected_unknown),
        winners_excluded_high=fraction(rejected_win+rejected_unknown,rejected_win+rejected_unknown+selected_win))


def mean_difference(values,selected):
    return float(values[selected].mean()-values[~selected].mean()) if selected.any() and (~selected).any() else np.nan


def cluster_difference(frame,value,selected,seed=20261010,reps=999):
    """Every draw repeats a company's entire historical path, never its rows iid."""
    f=pd.DataFrame(dict(c=frame.cnpj.to_numpy(),v=np.asarray(value),s=np.asarray(selected,dtype=bool)))
    f['vs']=f.v*f.s;f['vr']=f.v*~f.s;f['ns']=f.s.astype(int);f['nr']=(~f.s).astype(int)
    g=f.groupby('c')[['vs','vr','ns','nr']].sum().to_numpy();n=len(g)
    if n<2 or not g[:,2].sum() or not g[:,3].sum():return (np.nan,np.nan,np.nan)
    rng=np.random.default_rng(seed);draw=rng.multinomial(n,np.full(n,1/n),size=reps)@g
    valid=(draw[:,2]>0)&(draw[:,3]>0)
    delta=draw[valid,0]/draw[valid,2]-draw[valid,1]/draw[valid,3]
    observed=g[:,0].sum()/g[:,2].sum()-g[:,1].sum()/g[:,3].sum()
    lo,hi=np.quantile(delta,[.025,.975])
    # Centered cluster bootstrap is an approximate conditional exploratory test,
    # not a general-time null test. Multiplicity applies to its declared family.
    p=(1+np.sum(np.abs(delta-observed)>=abs(observed)))/(1+len(delta))
    return float(lo),float(hi),float(p)


def sector_difference(frame,value,selected):
    f=frame[['year','sector_group']].copy();f['value']=np.asarray(value);f['selected']=np.asarray(selected)
    effects=[];weights=[]
    for _,g in f.groupby(['year','sector_group'],dropna=False):
        a=g[g.selected];b=g[~g.selected]
        if len(a)>=5 and len(b)>=5:
            effects.append(a.value.mean()-b.value.mean());weights.append(len(a))
    return float(np.average(effects,weights=weights)) if effects else np.nan


def effect_metrics(frame,wealth,selected):
    wealth=np.asarray(wealth);selected=np.asarray(selected,dtype=bool);n=len(frame)
    a=wealth[selected];b=wealth[~selected];loss=wealth<=.5;win=wealth>=3
    frac=lambda a,b:float(a/b) if b else np.nan
    ibov=frame.ibov_wealth.to_numpy()
    ranking=pd.DataFrame(dict(year=frame.year.to_numpy(),wealth=wealth))
    # Top decile is separate from a fixed 3x multiplier. Average tied ranks
    # preserve ties; decile estimates condition on the covered feature universe.
    decile=ranking.groupby('year').wealth.rank(method='average',pct=True).to_numpy()>=.9
    support=frame[['year','sector_group']].copy();support['s']=selected
    cells=support.groupby(['year','sector_group']).s.agg(['sum','count'])
    matched=cells[(cells['sum']>=5)&((cells['count']-cells['sum'])>=5)]
    result=dict(n=n,companies=frame.cnpj.nunique(),selected_n=len(a),rejected_n=len(b),
        selected_companies=frame.loc[selected,'cnpj'].nunique(),
        sector_matched_n=int(matched['count'].sum()),sector_matched_selected_n=int(matched['sum'].sum()),
        mean_return=float(a.mean()-1) if len(a) else np.nan,
        median_return=float(np.median(a)-1) if len(a) else np.nan,
        universe_mean_return=float(wealth.mean()-1) if n else np.nan,
        universe_median_return=float(np.median(wealth)-1) if n else np.nan,
        selected_minus_universe=float(a.mean()-wealth.mean()) if len(a) else np.nan,
        selected_minus_rejected=mean_difference(wealth,selected),
        multiplier_rate=frac(np.sum(win&selected),len(a)),severe_loss_rate=frac(np.sum(loss&selected),len(a)),
        universe_multiplier_rate=frac(win.sum(),n),universe_severe_loss_rate=frac(loss.sum(),n),
        bombs_avoided=frac(np.sum(loss&~selected),loss.sum()),winners_excluded=frac(np.sum(win&~selected),win.sum()),
        top_decile_winners_excluded=frac(np.sum(decile&~selected),decile.sum()),
        selected_fraction=frac(len(a),n),
        bombs_avoided_excess=frac(np.sum(loss&~selected),loss.sum())-frac(len(b),n),
        winners_excluded_excess=frac(np.sum(win&~selected),win.sum())-frac(len(b),n),
        relative_ibov_mean=float((wealth/ibov-1)[selected].mean()) if len(a) else np.nan,
        relative_ibov_difference=mean_difference(wealth/ibov-1,selected),
        market_outperformance_rate=frac(np.sum((wealth>ibov)&selected),len(a)),
        sector_neutral_difference=sector_difference(frame,wealth-1,selected),
        sector_neutral_relative_difference=sector_difference(frame,wealth/ibov-1,selected))
    if not len(a):
        for k in ['bombs_avoided','winners_excluded','top_decile_winners_excluded','bombs_avoided_excess','winners_excluded_excess']:result[k]=np.nan
    return result


def covered(frame):return frame.grade.isin(['A','B']) & frame.wealth_multiple.notna()


def filters_analysis(frame,protocol,output):
    definitions=[[k] for k in protocol['frozen_filters']]+protocol['pairs']+protocol['triples']
    results=[];bounds=[];sensitivity=[];cohorts=[];stability=[]
    minimum=protocol['exploration_sufficiency']
    for horizon,all_rows in frame[frame.calendar_complete].groupby('horizon_years'):
        for label,part in partitions(all_rows,horizon,protocol).items():
            for names in definitions:
                name='+'.join(names);known,selected=filter_mask(part,names)
                universe=part[known].copy();sel=selected[known];usable=covered(universe)
                f=universe[usable];s=sel[usable].to_numpy();w=f.wealth_multiple.to_numpy()
                base=dict(horizon=horizon,partition=label,filter=name,universe_n=len(part),
                    feature_known_n=len(universe),feature_coverage=len(universe)/len(part) if len(part) else 0,
                    unknown_outcomes_n=int((~usable).sum()),usable_coverage=len(f)/len(universe) if len(universe) else 0)
                metrics=effect_metrics(f,w,s)
                adequate=(len(f)>=minimum['model_minimum_complete_pairs'] and f.cnpj.nunique()>=minimum['model_minimum_distinct_companies']
                    and s.sum()>=minimum['model_minimum_selected_and_rejected'] and (~s).sum()>=minimum['model_minimum_selected_and_rejected'])
                lo,hi,p=cluster_difference(f,w,s) if adequate else (np.nan,np.nan,np.nan)
                results.append(dict(**base,**metrics,sample_sufficient=bool(adequate),
                    conditional_mean_difference_ci_low=lo,conditional_mean_difference_ci_high=hi,
                    conditional_p=p,validated_time_general=False))
                unknown=universe[~usable];us=sel[~usable].sum();ur=(~sel[~usable]).sum()
                bs=missing_binary_bounds(int(((w<=.5)&s).sum()),int(((w<=.5)&~s).sum()),
                    int(((w>=3)&s).sum()),int(((w>=3)&~s).sum()),int(s.sum()),int((~s).sum()),int(us),int(ur))
                bounds.append(dict(horizon=horizon,partition=label,filter=name,selected_unknown=int(us),rejected_unknown=int(ur),**bs))
                if label!='ALL':continue
                # All B paths receive interval sensitivity. Adverse scenarios
                # move selected and rejected wealth in opposing directions.
                for scenario,delta,adverse in [('B_LOW15',-.15,False),('B_HIGH15',.15,False),
                        ('B_LOW30',-.30,False),('B_HIGH30',.30,False),('B_ADVERSE15',-.15,True),('B_ADVERSE30',-.30,True)]:
                    multiplier=np.where(f.grade.to_numpy()=='B',1+np.where(s,delta,-delta) if adverse else 1+delta,1)
                    sensitivity.append(dict(horizon=horizon,filter=name,scenario=scenario,**effect_metrics(f,w*multiplier,s)))
                a=f[f.grade=='A'];sa=sel.loc[a.index].to_numpy()
                sensitivity.append(dict(horizon=horizon,filter=name,scenario='A_ONLY_DESCRIPTIVE',**effect_metrics(a,a.wealth_multiple.to_numpy(),sa)))
                hypothetical=universe.wealth_multiple.where(usable,0).to_numpy()
                sensitivity.append(dict(horizon=horizon,filter=name,scenario='C_ZERO_HYPOTHETICAL',**effect_metrics(universe,hypothetical,sel.to_numpy())))
                for year,g in f.groupby('year'):
                    sy=sel.loc[g.index].to_numpy()
                    cohorts.append(dict(horizon=horizon,filter=name,cohort=year,**effect_metrics(g,g.wealth_multiple.to_numpy(),sy)))
                phases=[]
                for phase in range(horizon):
                    g=f[(f.year-2014)%horizon==phase];sg=sel.loc[g.index].to_numpy()
                    value=mean_difference(g.wealth_multiple.to_numpy(),sg);phases.append(value)
                    stability.append(dict(horizon=horizon,filter=name,check='NONOVERLAPPING_PHASE',value=phase,n=len(g),effect=value))
                # Remove each whole issuer, preserving overlapping paths together.
                if len(f) and s.any() and (~s).any():
                    g=pd.DataFrame(dict(c=f.cnpj.to_numpy(),vs=w*s,vr=w*~s,ns=s,nr=~s)).groupby('c').sum()
                    total=g.sum();remaining=total-g
                    loo=remaining.vs/remaining.ns-remaining.vr/remaining.nr
                    for key,value in [('MIN_EFFECT',loo.min()),('MAX_EFFECT',loo.max())]:
                        stability.append(dict(horizon=horizon,filter=name,check='LEAVE_COMPANY_OUT_'+key,value=0,n=len(g),effect=float(value)))
    r=pd.DataFrame(results)
    # Full declared filter x horizon x partition family, including insignificant
    # and ineligible tests. Ineligible tests use p=1 for adjustment, remain null.
    valid=r.conditional_p.notna()
    p=r.conditional_p.fillna(1).to_numpy()
    r['conditional_q_BH']=stats.false_discovery_control(p,method='bh')
    r['conditional_q_BY']=stats.false_discovery_control(p,method='by')
    r.loc[~valid,['conditional_q_BH','conditional_q_BY']]=np.nan
    r.to_csv(output/'filter_results.csv',index=False)
    pd.DataFrame(bounds).to_csv(output/'filter_missing_bounds.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(output/'filter_sensitivity.csv',index=False)
    pd.DataFrame(cohorts).to_csv(output/'filter_cohorts.csv',index=False)
    pd.DataFrame(stability).to_csv(output/'filter_stability.csv',index=False)
    return r


def rank_effect(frame,feature,target):
    ranked=[]
    for _,g in frame.groupby('year'):
        if len(g)<10 or g[feature].nunique()<2:continue
        x=g[feature].rank(method='average');y=g[target].rank(method='average')
        x=(x-x.mean())/x.std(ddof=0);y=(y-y.mean())/y.std(ddof=0)
        ranked.append(pd.DataFrame(dict(cnpj=g.cnpj,x=x,y=y,cohort_weight=1/len(g))))
    if not ranked:return np.nan,None
    r=pd.concat(ranked);r['xy']=r.x*r.y*r.cohort_weight
    return float(r.xy.sum()/r.cohort_weight.sum()),r


def univariate_analysis(frame,protocol,output):
    results=[];quintiles=[]
    for horizon,hf in frame[frame.calendar_complete].groupby('horizon_years'):
        for partition,part in partitions(hf,horizon,protocol).items():
            for feature in protocol['indicators']:
                f=part[covered(part)&part[feature].notna()].copy()
                for target in ['nominal_total_return','relative_ibov_return']:
                    effect,r=rank_effect(f,feature,target)
                    adequate=len(f)>=200 and f.cnpj.nunique()>=80 and r is not None
                    low=high=p=np.nan
                    if adequate:
                        g=r.groupby('cnpj')[['xy','cohort_weight']].sum().to_numpy();n=len(g)
                        rng=np.random.default_rng(protocol['inference']['seed'])
                        d=rng.multinomial(n,np.full(n,1/n),size=protocol['inference']['bootstrap_replications'])@g
                        bs=d[:,0]/d[:,1];low,high=np.quantile(bs,[.025,.975]);p=(1+np.sum(abs(bs-effect)>=abs(effect)))/(1+len(bs))
                    results.append(dict(horizon=horizon,partition=partition,indicator=feature,target=target,
                        n=len(f),companies=f.cnpj.nunique(),universe_n=len(part),cohort_equal_spearman=effect,
                        conditional_ci_low=low,conditional_ci_high=high,conditional_p=p,validated_time_general=False))
                if partition!='ALL' or f[feature].nunique()<5:continue
                # Average ties stay together. A binary or repeated threshold is
                # not broken into arbitrary winners merely to populate quintiles.
                f['quintile']=f.groupby('year')[feature].transform(lambda x:np.ceil(x.rank(method='average',pct=True)*5)).clip(1,5)
                for q,g in f.groupby('quintile'):
                    s=np.ones(len(g),dtype=bool)
                    quintiles.append(dict(horizon=horizon,indicator=feature,quintile=int(q),**effect_metrics(g,g.wealth_multiple.to_numpy(),s)))
    r=pd.DataFrame(results);valid=r.conditional_p.notna();p=r.conditional_p.fillna(1).to_numpy()
    r['conditional_q_BH']=stats.false_discovery_control(p,method='bh');r['conditional_q_BY']=stats.false_discovery_control(p,method='by')
    r.loc[~valid,['conditional_q_BH','conditional_q_BY']]=np.nan
    r.to_csv(output/'indicator_results.csv',index=False);pd.DataFrame(quintiles).to_csv(output/'indicator_quintiles.csv',index=False)
    return r


def coverage_tables(frame,protocol,output):
    rows=[];causes=[];availability=[]
    for horizon,hf in frame.groupby('horizon_years'):
        dimensions={'TOTAL':pd.Series('ALL',index=hf.index),'COHORT':hf.year.astype(str),
            'SECTOR':hf.sector_group,'SIZE_ASSETS':hf.size_tercile,
            'ECONOMIC_STATE':np.select([hf.historical_distress,hf.historical_exit_or_suspension],
                ['DISTRESS_BDI','EXIT_OR_SUSPENSION'],default='OTHER'),
            'FINANCIAL':hf.financial_sector.astype(str)}
        for dimension,values in dimensions.items():
            g=hf.assign(dimension_value=values)
            for value,s in g.groupby('dimension_value'):
                mature=s[s.calendar_complete];counts=mature.grade.value_counts()
                rows.append(dict(horizon=horizon,dimension=dimension,value=value,n=len(s),companies=s.cnpj.nunique(),
                    mature_n=len(mature),A=int(counts.get('A',0)),B=int(counts.get('B',0)),C=int(counts.get('C',0)),
                    time_censored=len(s)-len(mature),usable_fraction=float(covered(mature).mean()) if len(mature) else np.nan))
        for (year,cause),g in hf.assign(cause=hf.uncertainty_causes.fillna('').str.split(';')).explode('cause').groupby(['year','cause']):
            if cause:causes.append(dict(horizon=horizon,cohort=year,cause=cause,n=len(g)))
        for feature in protocol['indicators']:
            for year,g in hf[hf.calendar_complete].groupby('year'):
                availability.append(dict(horizon=horizon,cohort=year,indicator=feature,n=len(g),
                    feature_known=int(g[feature].notna().sum()),usable_pairs=int((g[feature].notna()&covered(g)).sum())))
    pd.DataFrame(rows).to_csv(output/'coverage.csv',index=False)
    pd.DataFrame(causes).to_csv(output/'uncertainty_causes.csv',index=False)
    pd.DataFrame(availability).to_csv(output/'indicator_coverage.csv',index=False)
    return pd.DataFrame(rows)


def run_statistics(frame,protocol,output):
    output.mkdir(parents=True,exist_ok=True)
    coverage=coverage_tables(frame,protocol,output)
    filters=filters_analysis(frame,protocol,output)
    indicators=univariate_analysis(frame,protocol,output)
    sector_results=[]
    for (horizon,financial),g in frame[frame.calendar_complete].groupby(['horizon_years','financial_sector']):
        for partition,part in partitions(g,horizon,protocol).items():
            for feature in protocol['indicators']:
                f=part[covered(part)&part[feature].notna()]
                effect,_=rank_effect(f,feature,'relative_ibov_return')
                sector_results.append(dict(horizon=horizon,partition=partition,financial=bool(financial),indicator=feature,
                    n=len(f),companies=f.cnpj.nunique(),cohort_equal_spearman=effect,inference='DESCRIPTIVE_ONLY'))
    pd.DataFrame(sector_results).to_csv(output/'financial_stratification.csv',index=False)
    # Union of every declared continuous association and filter test, including
    # held-out/purged descriptive partitions. No favorable family subdivision.
    all_p=np.concatenate([filters.conditional_p.fillna(1).to_numpy(),indicators.conditional_p.fillna(1).to_numpy()])
    bh=stats.false_discovery_control(all_p,method='bh');by=stats.false_discovery_control(all_p,method='by')
    offset=0
    for table,name in [(filters,'filter_results.csv'),(indicators,'indicator_results.csv')]:
        n=len(table);valid=table.conditional_p.notna()
        table['conditional_q_BH']=bh[offset:offset+n];table['conditional_q_BY']=by[offset:offset+n]
        table.loc[~valid,['conditional_q_BH','conditional_q_BY']]=np.nan
        table.to_csv(output/name,index=False);offset+=n
    metadata=dict(method='Frozen thresholds and cohorts; conditional company-cluster bootstrap, 999 draws',
        no_time_general_confirmation=True,nominal_returns=True,benchmark='B3 total-return Ibovespa, historical endpoint asof',
        missing_C='Retained denominator; binary worst-case bounds and explicitly hypothetical zero recovery',
        multiplicity='BH/BY over union of 448 declared associations and filters x horizons x partitions (ineligible p=1); conditional tests only',
        cohort_generalization='Ten 3y/eight 5y cohorts overlap; only ~3/~2 independent horizon blocks',
        five_year_oos='One cohort (2021), not independent temporal confirmation')
    (output/'statistical_method.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    print('Exploration executed:',len(filters),'filter/partition/horizon rows and',len(indicators),'indicator tests',flush=True)
    return coverage,filters,indicators
