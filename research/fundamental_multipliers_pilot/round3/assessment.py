"""Assess frozen sufficiency without using outcome directions to pass the gate."""
from __future__ import annotations
import json
import pandas as pd
from .statistics import covered


def assess(frame,coverage,protocol,output):
    limits=protocol['exploration_sufficiency'];rows=[]
    for horizon,g in frame.groupby('horizon_years'):
        mature=g[g.calendar_complete];usable=mature[covered(mature)]
        cv=coverage[coverage.horizon==horizon]
        cohorts=cv[(cv.dimension=='COHORT')&(cv.mature_n>0)]
        major=cv[(cv.dimension=='SECTOR')&(cv.mature_n>=limits['major_sector_minimum_observations'])]
        sizes=cv[(cv.dimension=='SIZE_ASSETS')&(cv.value!='UNKNOWN')&(cv.mature_n>0)]
        states=cv[cv.dimension=='ECONOMIC_STATE'].set_index('value').usable_fraction
        gap=max(states.get('OTHER',0)-states.get('DISTRESS_BDI',0),states.get('OTHER',0)-states.get('EXIT_OR_SUSPENSION',0))
        count=int((cohorts.usable_fraction>=limits['minimum_cohort_usable_fraction']).sum())
        broad=(len(usable)>=limits['minimum_usable_windows_per_horizon']
            and usable.cnpj.nunique()>=limits['minimum_distinct_companies']
            and count>=limits['minimum_cohorts']
            and (major.usable_fraction>=limits['minimum_major_sector_usable_fraction']).all()
            and (sizes.usable_fraction>=limits['minimum_size_tercile_usable_fraction']).all() and gap<=.2)
        rows.append(dict(horizon=horizon,mature_n=len(mature),usable_n=len(usable),usable_companies=usable.cnpj.nunique(),
            cohorts_above_half=count,mature_cohorts=len(cohorts),major_sectors_below_floor=int((major.usable_fraction<.4).sum()),
            size_groups_below_floor=int((sizes.usable_fraction<.4).sum()),problematic_coverage_gap=gap,
            representative_sufficiency=bool(broad),scope='CONDITIONAL_EXPLORATION_ONLY' if not broad else 'EXPLORATION_SUFFICIENT'))
    pd.DataFrame(rows).to_csv(output/'sufficiency.csv',index=False)
    boundary=[]
    for (horizon,year),g in frame[frame.calendar_complete&covered(frame)].groupby(['horizon_years','year']):
        low=g.wealth_low;high=g.wealth_high;market=g.ibov_wealth
        r=dict(horizon=horizon,cohort=year,usable_n=len(g))
        for name,robust,possible in [('3x',low>=3,high>=3),('loss',high<=.5,low<=.5),
                ('market',low>market,high>market)]:
            r['robust_'+name]=int(robust.sum());r['possible_'+name]=int(possible.sum())
            r['ambiguous_'+name]=int((possible&~robust).sum())
        boundary.append(r)
    pd.DataFrame(boundary).to_csv(output/'threshold_uncertainty.csv',index=False)
    note=dict(no_broad_predictive_claim=True,
        sufficient_size_is_not_representativeness='Many A/B observations do not remove disproportionately missing distress and exits',
        unknown_identity='94 eligible security/date observations (188 horizons) remain outside the mapped-company denominator; not 94 distinct companies',
        approximate_features='ROE is total annual income over mean positive total equity, not audited attributable shareholder ROE/prudential return; dividend yield is trailing gross ex-entitlement cash over raw price',
        next_order=[
            'Economic exits and predecessor/successor identities: reconcile existing CVM/B3 evidence before assuming delisting loss or lasting terminal price',
            'Missing subscription entitlements: use local FRE increases plus restored right quotations; resolve/bound material value without new capital',
            'Conflicting share factors/ex dates and restored upward breaks: corroborate mechanically with local originals; never erase genuine losses',
            'Exact historical class/treasury capital for P/L and P/VP; true EBITDA/NOPAT separately, not parser EBIT renamed',
            'Extend genuinely independent out-of-sample calendar blocks; no promotion based on 2021 five-year cohort alone'])
    (output/'assessment_notes.json').write_text(json.dumps(note,ensure_ascii=False,indent=2)+'\n')
    return rows
