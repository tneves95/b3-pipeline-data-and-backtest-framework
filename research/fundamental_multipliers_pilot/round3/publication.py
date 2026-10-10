"""Strict aggregate-only publication; no individual B3 record can pass schema."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import numpy as np
import pandas as pd
from ..audit import HERE,ROOT,sha256

COUNTS='n companies selected_n rejected_n selected_companies sector_matched_n sector_matched_selected_n'.split()
SELECTED='mean_return median_return multiplier_rate severe_loss_rate relative_ibov_mean market_outperformance_rate'.split()
UNIVERSE='universe_mean_return universe_median_return universe_multiplier_rate universe_severe_loss_rate'.split()
CONTRAST='selected_minus_universe selected_minus_rejected bombs_avoided winners_excluded top_decile_winners_excluded selected_fraction bombs_avoided_excess winners_excluded_excess relative_ibov_difference sector_neutral_difference sector_neutral_relative_difference'.split()
METRICS=COUNTS+SELECTED[:2]+UNIVERSE[:2]+CONTRAST[:2]+SELECTED[2:4]+UNIVERSE[2:]+CONTRAST[2:8]+SELECTED[4:5]+CONTRAST[8:9]+SELECTED[5:]+CONTRAST[9:]
# Exact order is recorded independently from the producing module.
SCHEMAS={
 'coverage.csv':'horizon dimension value n companies mature_n A B C time_censored usable_fraction'.split(),
 'uncertainty_causes.csv':'horizon cohort cause n'.split(),
 'indicator_coverage.csv':'horizon cohort indicator n feature_known usable_pairs'.split(),
 'filter_results.csv':'horizon partition filter universe_n feature_known_n feature_coverage unknown_outcomes_n usable_coverage'.split()+METRICS+
    'sample_sufficient conditional_mean_difference_ci_low conditional_mean_difference_ci_high conditional_p validated_time_general conditional_q_BH conditional_q_BY'.split(),
 'filter_cohorts.csv':'horizon filter cohort'.split()+METRICS,
 'filter_sensitivity.csv':'horizon filter scenario'.split()+METRICS,
 'filter_missing_bounds.csv':'horizon partition filter selected_unknown rejected_unknown loss_advantage_low loss_advantage_high bombs_avoided_low bombs_avoided_high winners_excluded_low winners_excluded_high'.split(),
 'filter_stability.csv':'horizon filter check value n effect'.split(),
 'indicator_results.csv':'horizon partition indicator target n companies universe_n cohort_equal_spearman conditional_ci_low conditional_ci_high conditional_p validated_time_general conditional_q_BH conditional_q_BY'.split(),
 'indicator_quintiles.csv':'horizon indicator quintile'.split()+METRICS,
 'return_validation.csv':'horizon check n companies median_relative_gap max_absolute_gap material_gap_n'.split(),
 'financial_stratification.csv':'horizon partition financial indicator n companies cohort_equal_spearman inference'.split(),
 'sufficiency.csv':'horizon mature_n usable_n usable_companies cohorts_above_half mature_cohorts major_sectors_below_floor size_groups_below_floor problematic_coverage_gap representative_sufficiency scope'.split(),
 'threshold_uncertainty.csv':'horizon cohort usable_n robust_3x possible_3x ambiguous_3x robust_loss possible_loss ambiguous_loss robust_market possible_market ambiguous_market'.split(),
}
TEXT={'dimension','value','cause','partition','filter','scenario','check','indicator','target','inference','scope'}
FORBIDDEN={'ticker','isin','isin_code','cnpj','date','quote_date','close','adj_close','volume','wealth_multiple','nominal_total_return'}


def validate_schema(frame,name):
    expected=SCHEMAS[name]
    if list(frame.columns)!=expected or FORBIDDEN.intersection(frame.columns):
        raise ValueError('PUBLICATION_SCHEMA_REJECTED: '+name)
    for column in frame:
        if column in TEXT:
            if frame[column].astype(str).str.contains(r'\b(?:BR[A-Z0-9]{10}|[A-Z]{4}\d{1,2}|\d{14})\b',regex=True).any():
                raise ValueError('INDIVIDUAL_IDENTIFIER_IN_AGGREGATE')
            continue
        if column in ['sample_sufficient','validated_time_general','financial','representative_sufficiency']:continue
        v=pd.to_numeric(frame[column],errors='raise')
        if np.isinf(v.to_numpy(dtype=float)).any():raise ValueError('INFINITE_AGGREGATE')
        if column in ['n','companies','selected_n','rejected_n','selected_companies','A','B','C','mature_n','time_censored']:
            if not ((v>=0)&(v<=10000)&(v==v.round())).all():raise ValueError('INVALID_AGGREGATE_COUNT')


def suppress_small_cells(frame):
    """Suppress outcome summaries below five windows or three issuers.

    This publication floor affects disclosure only. Local calculations retain
    every case and their denominators; no observation is excluded from analysis.
    """
    f=frame.copy()
    if 'n' not in f:return f
    small=f.n<5
    if 'companies' in f:small |= f.companies<3
    if 'selected_n' in f:
        ss=(f.selected_n<5)|(f.selected_companies<3)
        for c in SELECTED:
            if c in f:f.loc[ss,c]=np.nan
        small_contrast=ss|(f.rejected_n<5)|small
        for c in CONTRAST:
            if c in f:f.loc[small_contrast,c]=np.nan
    for c in UNIVERSE+['effect','cohort_equal_spearman','conditional_ci_low','conditional_ci_high',
            'conditional_mean_difference_ci_low','conditional_mean_difference_ci_high','conditional_p',
            'conditional_q_BH','conditional_q_BY','median_relative_gap','max_absolute_gap']:
        if c in f:f.loc[small,c]=np.nan
    return f


def publish(local,public):
    manifest=json.loads((local/'run_manifest.json').read_text())
    if not manifest['source_sqlite_unchanged']:raise ValueError('SOURCE_NOT_IMMUTABLE')
    for r in manifest['inputs']:
        if sha256(Path(r['path']))!=r['sha256']:raise ValueError('INPUT_HASH_CHANGED')
    for r in manifest['outputs']:
        if sha256(local/r['file'])!=r['sha256']:raise ValueError('OUTPUT_HASH_CHANGED: '+r['file'])
    for r in manifest['code']:
        if sha256(ROOT/r['path'])!=r['sha256']:raise ValueError('ANALYSIS_CODE_CHANGED')
    public.mkdir(parents=True,exist_ok=True)
    for name in SCHEMAS:
        f=pd.read_csv(local/'aggregates'/name);validate_schema(f,name)
        f=suppress_small_cells(f)
        f.to_csv(public/name,index=False,float_format='%.10g')
    previous=pd.read_csv(HERE/'published_round2/return_coverage_by_cohort.csv')
    previous[['year','horizon_years','unmapped_eligible_security_observations']].to_csv(public/'unresolved_identity_coverage.csv',index=False)
    provenance=dict(version=3,protocol_sha256=manifest['protocol_sha256'],
        inputs=[dict(file=Path(r['path']).name,bytes=r['bytes'],sha256=r['sha256']) for r in manifest['inputs']],
        code=manifest['code'],completed_utc=manifest['completed_utc'],environment=manifest['environment'],
        source_sqlite_unchanged=True,preserved_prior_artifacts=413,validation=manifest['validation'],
        private_evidence='Original quotes, events, issuer paths, financial panel and primary PDF stay local_only; no individual B3 data included',
        small_cell_policy='Outcome summary suppressed below 5 windows or 3 issuers; counts retained',
        statistical_method=json.loads((local/'aggregates/statistical_method.json').read_text()),
        assessment=json.loads((local/'aggregates/assessment_notes.json').read_text()))
    (public/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
    def public_name(p):
        return str(p.relative_to(HERE)) if HERE in p.parents else p.name
    files=[dict(file=public_name(p),bytes=p.stat().st_size,sha256=sha256(p))
        for p in sorted(public.iterdir()) if p.is_file() and p.name!='publication_review_round3.json']
    review=dict(version=3,files=files,total_bytes=sum(r['bytes'] for r in files),
        raw_quotes_published=False,individual_B3_trajectories_published=False,primary_PDF_published=False,
        redistribution='Only own aggregates, code, synthetic tests and provenance; all source evidence remains local',
        pr=8,draft_required=True,merge_authorized=False)
    review_path=HERE/'publication_review_round3.json' if HERE in public.parents else public/'publication_review_round3.json'
    review_path.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
    print('Audited aggregate publication:',len(files),'files,',review['total_bytes'],'bytes',flush=True)
    return review


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local',type=Path,default=HERE/'local_only/round3')
    parser.add_argument('--public',type=Path,default=HERE/'published_round3')
    args=parser.parse_args();publish(args.local,args.public)


if __name__=='__main__':main()
