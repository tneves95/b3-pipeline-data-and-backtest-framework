"""Execute corrected as-of readiness, exact filing recovery and shareholder certification.

Offline by default. New COTAHIST storage is a differential overlay. The accepted
inventory and every prior study/checkpoint remain read-only. Optional targeted
retrieval is exposed in fetch_filings/fetch_sources, never triggered by this module.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sqlite3
import pandas as pd
from .audit import HERE, ROOT, outcome_readiness, ratio, sha256
from .events import extract_reviewed_events, verify_reused_fre
from .filings import recover_local
from .publication import load_verified
from .quotes import build_overlay, QuoteBook
from .returns import evaluate

SIMPLE = ['income_positive','operating_margin','ocf_to_positive_income','current_ratio']


def assess_predictive_gate(matrix, unmapped_count):
    """Coverage decisions use the full formation denominator, never observed winners."""
    complete=matrix[matrix.calendar_complete]
    certified=complete[complete.status=='CERTIFIED']
    share=len(certified)/len(complete) if len(complete) else 0.
    cohort=complete.groupby(['year','horizon_years']).status.apply(lambda x:x.eq('CERTIFIED').mean())
    reasons=[]
    if share<.95 or (cohort<.95).any():
        reasons.append('Less than 95% of complete trajectories certified overall or within cohort/horizon')
    if int(certified.cnpj.nunique())<100:
        reasons.append('Fewer than 100 distinct certified companies; company/sector coverage not representative')
    if (complete.status=='CENSORED').any():
        reasons.append('Known distressed/disappearing trajectories still have unresolved economic censoring')
    if unmapped_count:
        reasons.append('Eligible historical formation securities still lack unambiguous issuer identity')
    return dict(passed=not reasons,indicators=SIMPLE,complex_indicators_required=False,
        mapped_complete_observations=len(complete),certified_total_returns=len(certified),
        certified_share_of_complete=share,unmapped_eligible_security_observations=unmapped_count,
        minimum_complete_coverage_overall_and_each_cohort=.95,minimum_distinct_certified_companies=100,
        economic_censoring_allowed=0,unmapped_formation_securities_allowed=0,
        reasons=reasons,estimates_computed=False,returns_computed=True)


def enrich_simple_indicators(panel, recovery):
    panel=panel.copy()
    recovered={r.required_filing_id:r for r in recovery[recovery.status=='EXACT_ORIGINAL_RECOVERED'].itertuples()}
    for index,p in panel.iterrows():
        f=recovered.get(p.required_filing_id)
        if f is not None:
            if f.required_received >= p.formation_date: raise ValueError('Recovered filing not public at formation')
            for metric in ['net_income','revenue','operating_cash_flow','current_assets','current_liabilities','equity','total_assets']:
                panel.loc[index,'raw_'+metric]=getattr(f,metric)
            panel.loc[index,'raw_ebitda']=f.ebit
            panel.loc[index,'statement_status']='AVAILABLE_AT_CUTOFF_RECOVERED'
    panel['raw_ebit']=panel.raw_ebitda
    for index,p in panel.iterrows():
        available=p.statement_status in ['AVAILABLE_AT_CUTOFF','AVAILABLE_AT_CUTOFF_RECOVERED']
        ni=p.raw_net_income
        panel.loc[index,'income_positive']=float(ni>0) if available and pd.notna(ni) else float('nan')
        panel.loc[index,'income_positive_status']='PIT_VALUE_AVAILABLE' if available and pd.notna(ni) else p.statement_status
        for name,num,den in [('operating_margin',p.raw_ebit,p.raw_revenue),
                             ('ocf_to_positive_income',p.raw_operating_cash_flow,ni),
                             ('current_ratio',p.raw_current_assets,p.raw_current_liabilities)]:
            if not available: value,status=float('nan'),p.statement_status
            elif p.financial_sector or pd.isna(p.sector): value,status=float('nan'),'FINANCIAL_OR_UNKNOWN_SECTOR'
            else: value,status=ratio(num,den)
            panel.loc[index,name]=value;panel.loc[index,name+'_status']=status
    return panel


def aggregate_round(matrix, readiness, panel, recovery, original_outcomes, unmapped):
    rows=[]
    for (year,horizon),group in matrix.groupby(['year','horizon_years']):
        old=original_outcomes[(original_outcomes.formation_date.str[:4].astype(int)==year)&(original_outcomes.horizon_years==horizon)]
        fixed=readiness[(readiness.formation_date.str[:4].astype(int)==year)&(readiness.horizon_years==horizon)]
        rows.append(dict(year=year,horizon_years=horizon,mapped_company_observations=len(group),
            certified=int(group.status.eq('CERTIFIED').sum()),uncertified=int(group.status.eq('UNCERTIFIED').sum()),
            censored=int(group.status.eq('CENSORED').sum()),calendar_complete=int(group.calendar_complete.sum()),
            horizon_not_matured=int((~group.calendar_complete).sum()),
            economic_censoring=int((group.status.eq('CENSORED')&group.calendar_complete).sum()),
            old_same_security_near_endpoint=int(old.same_security_near_endpoint.sum()),
            corrected_same_security_near_endpoint=int(fixed.same_security_near_endpoint.sum()),
            unmapped_eligible_security_observations=int((unmapped.year==year).sum())))
    coverage=pd.DataFrame(rows)
    causes=matrix[['year','horizon_years','exclusion_causes']].copy()
    causes['cause']=causes.exclusion_causes.str.split(';');causes=causes.explode('cause')
    causes=causes[causes.cause.fillna('')!=''].groupby(['year','horizon_years','cause']).size().reset_index(name='observations')
    causes['unit_type']='MAPPED_COMPANY_OBSERVATION'
    unresolved=[]
    for year,g in unmapped.groupby('year'):
        for horizon in [3,5]:
            unresolved.append(dict(year=year,horizon_years=horizon,
                cause='MISSING_OR_CONFLICTING_HISTORICAL_CNPJ',observations=len(g),
                unit_type='UNRESOLVED_SECURITY_OBSERVATION'))
    causes=pd.concat([causes,pd.DataFrame(unresolved)],ignore_index=True)
    features=[]
    joined=matrix.merge(panel[['cnpj','formation_date','financial_sector','sector']+SIMPLE],on=['cnpj','formation_date'],suffixes=('','_panel'))
    for (year,horizon),g in joined.groupby(['year','horizon_years']):
        for indicator in SIMPLE:
            features.append(dict(year=year,horizon_years=horizon,indicator=indicator,mapped_company_observations=len(g),
                indicator_available=int(g[indicator].notna().sum()),certified_return_and_indicator=int((g.status.eq('CERTIFIED')&g[indicator].notna()).sum()),
                predictive_gate_passed=False))
    filing=recovery.assign(recovered=recovery.status.eq('EXACT_ORIGINAL_RECOVERED')).groupby('year').agg(
        identified_missing_observations=('required_filing_id','size'),exact_originals_recovered=('recovered','sum')).reset_index()
    return coverage,causes,pd.DataFrame(features),filing


def run(source, inventory, output, scratch, *, build=False):
    if (output/'round2_manifest.json').exists():
        raise ValueError('Existing round checkpoint: use a new output directory')
    old_manifest=load_verified(inventory)
    db=source/'b3_market_data.sqlite';before=sha256(db)
    if before!=old_manifest['sqlite_sha256']: raise ValueError('Source database differs from accepted inventory')
    output.mkdir(parents=True,exist_ok=True);scratch.mkdir(parents=True,exist_ok=True)
    securities=pd.read_csv(inventory/'panel_security_date_diagnostic.csv',dtype={'cnpj':str,'quote_bdi':str})
    panel=securities[securities.company_representative].copy()
    unmapped=securities[securities.cnpj.isna()].copy()
    cutoffs=[(pd.Timestamp(d)+pd.DateOffset(years=h)).strftime('%Y-%m-%d') for d in securities.formation_date.unique() for h in [3,5]]
    if build:
        build_overlay(source,output,scratch,cutoffs)
    required=['quote_overlay.sqlite','endpoint_quote_snapshots.csv','exchange_calendar.csv','sources/manifest.json']
    if any(not (output/name).exists() for name in required): raise ValueError('Build overlay and fetch the four directed event sources first')
    quotes=pd.read_csv(output/'endpoint_quote_snapshots.csv',dtype={'bdi':str})
    calendar=pd.read_csv(output/'exchange_calendar.csv').date.tolist()
    skipped=pd.read_csv(inventory/'unhandled_events.csv')
    readiness=outcome_readiness(panel,quotes,skipped,output,max(calendar),calendar=calendar)
    # Formation identities absent from the initial company panel are retained separately,
    # without inventing CNPJs or counting multiple classes as distinct companies.
    unresolved=unmapped.copy();unresolved.company_representative=True
    unresolved.cnpj='UNRESOLVED:'+unresolved.ticker+':'+unresolved['isin']
    unidentified_output=output/'unmapped_diagnostics';unidentified_output.mkdir(exist_ok=True)
    unidentified=outcome_readiness(unresolved,quotes,skipped,unidentified_output,max(calendar),calendar=calendar)
    unidentified['unit_type']='UNRESOLVED_SECURITY_OBSERVATION'
    unidentified['status']='UNCERTIFIED_FORMATION_IDENTITY'
    unidentified['exclusion_causes']='MISSING_OR_CONFLICTING_HISTORICAL_CNPJ'
    unidentified.to_csv(output/'unmapped_return_observations.csv',index=False)
    recovery=recover_local(panel,ROOT,output)
    panel=enrich_simple_indicators(panel,recovery)
    panel.to_csv(output/'panel_simple_indicators_pit.csv',index=False)
    fre=verify_reused_fre(ROOT,source,output)
    events,scopes=extract_reviewed_events(ROOT,output,calendar)
    book=QuoteBook(db,output/'quote_overlay.sqlite',calendar)
    matrix=evaluate(panel,readiness,book,events,scopes,skipped,output)
    book.close()
    aggregates=aggregate_round(matrix,readiness,panel,recovery,pd.read_csv(inventory/'outcome_readiness.csv'),unmapped)
    for name,frame in zip(['return_coverage_by_cohort','remaining_causes_by_cohort','simple_indicator_coverage','filing_recovery_by_cohort'],aggregates):
        frame.to_csv(output/(name+'.csv'),index=False)
    # Material unresolved identities, distressed returns and economic exits keep the
    # inference gate closed regardless of how many surviving securities are calculable.
    cert=matrix[matrix.status=='CERTIFIED']
    gate=assess_predictive_gate(matrix,len(unmapped))
    (output/'predictive_gate.json').write_text(json.dumps(gate,indent=2)+'\n')
    # All source artifacts, including the 14 MB checkpoint, are rechecked after execution.
    load_verified(inventory)
    after=sha256(db)
    if after!=before: raise ValueError('Source SQLite changed during execution')
    reconstruction=pd.read_csv(output/'quote_reconstruction_by_year.csv')
    summary=dict(stage='AUDITED_NOMINAL_TOTAL_RETURNS_COMPUTED_INCOMPLETE_UNIVERSE',
        source_sqlite_unchanged=True,sqlite_sha256=before,previous_local_manifest_sha256=sha256(inventory/'manifest.json'),
        mapped_company_observations=len(panel),unmapped_eligible_security_observations=len(unmapped),
        unmapped_return_observations=len(unidentified),
        return_observations=len(matrix),certified_nominal_total_returns=len(cert),
        certified_distinct_companies=int(cert.cnpj.nunique()),
        certified_3y=int((cert.horizon_years==3).sum()),certified_5y=int((cert.horizon_years==5).sum()),
        certified_wealth_at_most_half=int((cert.wealth_multiple<=.5).sum()),
        real_and_relative_returns_certified=False,
        economic_censored=int((matrix.status.eq('CENSORED')&matrix.calendar_complete).sum()),
        time_censored=int((~matrix.calendar_complete).sum()),uncertified=int(matrix.status.eq('UNCERTIFIED').sum()),
        recovered_missing_equity_quotes=int(reconstruction.missing_equity_rows.sum()),
        overlay_quote_rows=int(reconstruction.overlay_rows.sum()),overlay_bytes=(output/'quote_overlay.sqlite').stat().st_size,
        identified_missing_filing_observations=len(recovery),exact_originals_recovered=int(recovery.status.eq('EXACT_ORIGINAL_RECOVERED').sum()),
        remaining_originals=int(recovery.status.ne('EXACT_ORIGINAL_RECOVERED').sum()),
        reused_fre_rows_verified=len(fre),reconciled_economic_event_records=len(events),
        predictive_gate=gate,publication_scope='Only aggregate counts, documentation, code, tests and provenance',
        code=[dict(file=p.name,sha256=sha256(p)) for p in sorted(HERE.glob('*.py'))],
        sources=old_manifest['sources'],
        outputs=[dict(file=str(p.relative_to(output)),bytes=p.stat().st_size,sha256=sha256(p))
                 for p in sorted(output.rglob('*')) if p.is_file() and p.name!='round2_manifest.json'])
    (output/'round2_manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['sources','outputs','code']},indent=2),flush=True)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,default=ROOT.parent);p.add_argument('--inventory',type=Path,default=HERE/'local_only/data')
    p.add_argument('--output',type=Path,default=HERE/'local_only/round2');p.add_argument('--scratch',type=Path,default=Path('/tmp/b3-fundamentals-round2'))
    p.add_argument('--build-overlay',action='store_true');a=p.parse_args()
    run(a.source_root.resolve(),a.inventory.resolve(),a.output.resolve(),a.scratch.resolve(),build=a.build_overlay)

if __name__=='__main__':main()
