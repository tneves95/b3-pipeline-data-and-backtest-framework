"""Publish exact aggregate schemas and provenance; individual B3 trajectories stay local."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
from .audit import HERE, sha256

SCHEMAS={
    'return_coverage_by_cohort.csv':['year','horizon_years','mapped_company_observations','certified','uncertified','censored',
        'calendar_complete','horizon_not_matured','economic_censoring','old_same_security_near_endpoint',
        'corrected_same_security_near_endpoint','unmapped_eligible_security_observations'],
    'remaining_causes_by_cohort.csv':['year','horizon_years','cause','observations','unit_type'],
    'simple_indicator_coverage.csv':['year','horizon_years','indicator','mapped_company_observations','indicator_available',
        'certified_return_and_indicator','predictive_gate_passed'],
    'filing_recovery_by_cohort.csv':['year','identified_missing_observations','exact_originals_recovered'],
}
SUMMARY_KEYS=['stage','source_sqlite_unchanged','sqlite_sha256','previous_local_manifest_sha256',
    'mapped_company_observations','unmapped_eligible_security_observations','unmapped_return_observations','return_observations',
    'certified_nominal_total_returns','certified_distinct_companies','certified_3y','certified_5y','certified_wealth_at_most_half',
    'real_and_relative_returns_certified','economic_censored','time_censored','uncertified',
    'recovered_missing_equity_quotes','overlay_quote_rows','overlay_bytes','identified_missing_filing_observations',
    'exact_originals_recovered','remaining_originals','reused_fre_rows_verified','reconciled_economic_event_records',
    'predictive_gate','publication_scope','code']


def publish(local,output):
    if local.resolve()==output.resolve() or local.resolve() in output.resolve().parents:
        raise ValueError('Publication must be separate from granular evidence')
    manifest=json.loads((local/'round2_manifest.json').read_text())
    for item in manifest['outputs']:
        name=Path(item['file'])
        if name.is_absolute() or '..' in name.parts: raise ValueError('Unsafe local manifest path')
        path=local/name
        if path.stat().st_size!=item['bytes'] or sha256(path)!=item['sha256']:
            raise ValueError('Unverified local artifact: '+str(name))
    frames={}
    for name,schema in SCHEMAS.items():
        frame=pd.read_csv(local/name)
        if list(frame.columns)!=schema: raise ValueError('Unreviewed aggregate schema: '+name)
        frames[name]=frame
    reconstruction=pd.read_csv(local/'quote_reconstruction_by_year.csv')
    fields=['year','original_equity_rows','original_right_rows','missing_equity_rows','missing_right_rows',
            'identity_mismatches','close_mismatches','factor_mismatches','overlay_rows']
    frames['quote_reconstruction_by_year.csv']=reconstruction.reindex(columns=fields,fill_value=0)
    expected=set(frames)|{'manifest.json','local_artifact_inventory.csv'}
    output.mkdir(parents=True,exist_ok=True)
    if {p.name for p in output.iterdir()}-expected: raise ValueError('Unreviewed extra public file')
    for name,frame in frames.items(): frame.to_csv(output/name,index=False)
    inventory=pd.DataFrame([{**item,'publication':'LOCAL_ONLY'} for item in manifest['outputs']])
    # Artifact names/sizes/hashes convey reproduction provenance, never record contents.
    inventory.to_csv(output/'local_artifact_inventory.csv',index=False)
    summary={k:manifest[k] for k in SUMMARY_KEYS}
    summary['local_manifest_sha256']=sha256(local/'round2_manifest.json')
    summary['publication_code_sha256']=sha256(Path(__file__))
    summary['source_files']=[{k:r[k] for k in ['path','bytes','sha256','role']} for r in manifest['sources']]
    for source in summary['source_files']:
        if Path(source['path']).is_absolute() or '..' in Path(source['path']).parts: raise ValueError('Unsafe source path')
    source_manifest=json.loads((local/'sources/manifest.json').read_text())
    summary['directed_primary_sources']=source_manifest
    summary['outputs']=[dict(file=p.name,bytes=p.stat().st_size,sha256=sha256(p)) for p in sorted(output.iterdir()) if p.name!='manifest.json']
    (output/'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--local',type=Path,default=HERE/'local_only/round2')
    p.add_argument('--output',type=Path,default=HERE/'published_round2');a=p.parse_args();r=publish(a.local,a.output)
    print(json.dumps(dict(published_files=len(r['outputs'])+1,certified_returns=r['certified_nominal_total_returns']),indent=2))

if __name__=='__main__': main()
