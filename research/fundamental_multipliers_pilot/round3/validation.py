"""Diversified mechanical cross-checks and documentary reference anchors."""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
import math
import numpy as np
import pandas as pd
from ..audit import HERE
from .scale import replay


def closed_form(book,isin,start,target,events):
    """Independent scalar formula for a continuous single-class shareholder.

    Uses the same economic inputs, but no portfolio engine/apply_events. It
    checks mechanics; it cannot prove a catalogue's completeness.
    """
    days=defaultdict(list)
    for e in events:
        if e['ticker']==isin and start<e['ex_date']<=target:
            if e['kind'] not in ['DISTRIBUTION','SHARES','NO_ENTITLEMENT']:
                raise ValueError('MULTI_LEG_NOT_SCALAR')
            days[e['ex_date']].append(e)
    factors=[]
    for day,items in sorted(days.items()):
        shares=math.prod(e['factor'] for e in items if e['kind']=='SHARES')
        cash=math.fsum(e['amount'] for e in items if e['kind']=='DISTRIBUTION')
        factors.append(shares+cash/book.trade(isin,day)['close'])
    return book.trade(isin,book.session(target))['close']/book.trade(isin,start)['close']*math.prod(factors)


def validate(book,matrix,events,output,protocol):
    anchors=[]
    for r in matrix[matrix.grade=='A'].itertuples():
        computed=replay(book,r.isin,r.formation_date,r.calendar_endpoint,events)['wealth_multiple']
        anchors.append(dict(cnpj=r.cnpj,formation_date=r.formation_date,horizon=r.horizon_years,
            economic_state='DISTRESS' if r.historical_distress else 'OTHER',
            relative_gap=computed/r.wealth_multiple-1))
    a=pd.DataFrame(anchors)
    if a.relative_gap.abs().max()>1e-8:raise ValueError('DOCUMENTARY_ANCHOR_REGRESSION')
    # Deterministic strata allocation before looking at their wealth. Hash does
    # not contain outcome and does not favor easy surviving price directions.
    candidates=matrix[matrix.grade=='B'].copy()
    candidates['sample_key']=candidates.apply(lambda r:hashlib.sha256(
        f"20261010|{r.cnpj}|{r.formation_date}|{r.horizon_years}".encode()).hexdigest(),axis=1)
    candidates['economic_state']=np.select([candidates.historical_distress,candidates.historical_exit_or_suspension],
        ['DISTRESS','EXIT_OR_SUSPENSION'],default='OTHER')
    sample=candidates.sort_values('sample_key').groupby(['horizon_years','year','economic_state'],sort=True).head(10)
    rows=[]
    for r in sample.itertuples():
        computed=replay(book,r.isin,r.formation_date,r.calendar_endpoint,events)['wealth_multiple']
        record=dict(cnpj=r.cnpj,formation_date=r.formation_date,horizon=r.horizon_years,cohort=r.year,
            sector=r.sector,economic_state=r.economic_state,engine_gap=computed/r.wealth_multiple-1)
        try:
            scalar=closed_form(book,r.isin,r.formation_date,r.calendar_endpoint,events)
            record.update(method='INDEPENDENT_SCALAR_SHARED_INPUTS',relative_gap=scalar/computed-1)
        except ValueError:
            record.update(method='MULTI_LEG_ENGINE_TESTED_SYNTHETICALLY',relative_gap=np.nan)
        rows.append(record)
    s=pd.DataFrame(rows)
    if s.engine_gap.abs().max()>1e-8 or s.relative_gap.abs().max()>1e-8:raise ValueError('SAMPLED_MECHANICS_REGRESSION')
    a.to_csv(output/'validation_documentary_anchors.csv',index=False)
    s.to_csv(output/'validation_diversified_sample.csv',index=False)
    comparator=matrix[matrix.calendar_complete&matrix.adj_comparator_wealth.notna()&matrix.wealth_multiple.notna()].copy()
    comparator['gap']=comparator.adj_comparator_wealth/comparator.wealth_multiple-1
    aggregate=[]
    for horizon,g in comparator.groupby('horizon_years'):
        for grade,v in g.groupby('grade'):
            aggregate.append(dict(horizon=horizon,check='ADJ_COMPARATOR_'+grade,n=len(v),companies=v.cnpj.nunique(),
                median_relative_gap=v.gap.median(),max_absolute_gap=v.gap.abs().max(),
                material_gap_n=int((v.gap.abs()>.15).sum())))
    for horizon in [3,5]:
        for label,frame in [('DOCUMENTARY_ANCHORS',a),('SCALAR_SHARED_INPUTS',s[s.method=='INDEPENDENT_SCALAR_SHARED_INPUTS'])]:
            g=frame[frame.horizon==horizon]
            aggregate.append(dict(horizon=horizon,check=label,n=len(g),companies=g.cnpj.nunique(),
                median_relative_gap=g.relative_gap.median(),max_absolute_gap=g.relative_gap.abs().max(),
                material_gap_n=int((g.relative_gap.abs()>.15).sum())))
    pd.DataFrame(aggregate).to_csv(output/'aggregates/return_validation.csv',index=False)
    summary=dict(anchors=len(a),anchor_companies=a.cnpj.nunique(),sample=len(s),sample_companies=s.cnpj.nunique(),
        sample_sectors=s.sector.nunique(),sample_cohorts=s.cohort.nunique(),economic_states=s.economic_state.value_counts().to_dict(),
        limitation='Diversified scalar checks use shared source inputs; 24 documentary anchors cover only three firms. B is approximation, not complete source audit; 15/30% are stress envelopes, not proven error bounds.')
    (output/'validation_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print('Validation',summary,flush=True)
    return summary
