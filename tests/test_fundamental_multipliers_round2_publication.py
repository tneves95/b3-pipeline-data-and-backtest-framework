"""Regression checks for the public aggregate boundary of the executed round."""
import json
from pathlib import Path
import pandas as pd
import pytest
from research.fundamental_multipliers_pilot.audit import sha256
from research.fundamental_multipliers_pilot.publish_round2 import publish,SCHEMAS,SUMMARY_KEYS


def fixture(local):
    local.mkdir()
    for name,columns in SCHEMAS.items():pd.DataFrame(columns=columns).to_csv(local/name,index=False)
    pd.DataFrame([dict(year=2022,original_equity_rows=10,missing_equity_rows=1,overlay_rows=1,
                       ticker='PRIVATE3',close=123456.78)]).to_csv(local/'quote_reconstruction_by_year.csv',index=False)
    (local/'sources').mkdir();(local/'sources/manifest.json').write_text('[]')
    summary={k:0 for k in SUMMARY_KEYS};summary['sources']=[dict(path='data/raw/example.zip',bytes=10,sha256='a'*64,role='original_quotes')]
    summary['outputs']=[dict(file=str(p.relative_to(local)),bytes=p.stat().st_size,sha256=sha256(p)) for p in sorted(local.rglob('*')) if p.is_file()]
    (local/'round2_manifest.json').write_text(json.dumps(summary))


def test_round2_publication_keeps_security_prices_out_and_verifies_schema(tmp_path):
    local=tmp_path/'private';fixture(local);output=tmp_path/'public';publish(local,output)
    for p in output.iterdir():
        text=p.read_text();assert 'PRIVATE3' not in text;assert '123456.78' not in text
    d=pd.read_csv(output/'quote_reconstruction_by_year.csv');assert 'ticker' not in d;assert 'close' not in d


def test_round2_publication_rejects_tampering_and_unreviewed_columns(tmp_path):
    local=tmp_path/'private';fixture(local)
    p=local/'return_coverage_by_cohort.csv';p.write_text(p.read_text()+'tampered')
    with pytest.raises(ValueError,match='Unverified'):publish(local,tmp_path/'public')
    p.write_text(','.join(SCHEMAS[p.name]+['nominal_close'])+'\n')
    manifest=json.loads((local/'round2_manifest.json').read_text())
    item=next(i for i in manifest['outputs'] if i['file']==p.name);item.update(bytes=p.stat().st_size,sha256=sha256(p))
    (local/'round2_manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='Unreviewed aggregate'):publish(local,tmp_path/'public')
