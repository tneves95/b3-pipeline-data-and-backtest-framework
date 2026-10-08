#!/usr/bin/env python3
"""Hash the continuation without downloading or rewriting protected baselines."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SEL=ROOT/'research/returns_2014_2026_selection'
RESULT=ROOT/'research/returns_2014_2026_results'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while block:=f.read(8*1024*1024):h.update(block)
    return h.hexdigest()

def main(data_root=None):
    prior=json.loads((ROOT/'research/returns_2014_2026_inputs/coverage/manifest.json').read_text())
    path=SEL/'source_archives.json'
    if data_root:
        if sha(data_root/'b3_market_data.sqlite')!=prior['sqlite_sha256']:
            raise ValueError('SQLite changed since original checkpoint; review source changes before publishing')
        known={r['path']:r for r in prior['source_archives']}
        if path.exists():known.update({r['path']:r for r in json.loads(path.read_text())})
        files=[]
        for kind in ['dfp','fca','fre']:
            for y in range(2010,2026):
                rel=f'data/cvm/{kind}_cia_aberta_{y}.zip';p=data_root/rel
                files.append(known.get(rel) or dict(path=rel,sha256=sha(p)))
        path.write_text(json.dumps(files,ensure_ascii=False,indent=2)+'\n')
    selection=dict(status='B2_CONTINUITY_CORRECTED_BH_TWELVE_INTERVALS_B00S_FIRST_INTERVAL_EXPLORATORY',
        resumed_from='1ceab3f9fdc476e32b134c6271597fc8d98f99d4',sqlite_connection='mode=ro; PRAGMA query_only=ON',
        sqlite_sha256=prior['sqlite_sha256'],sqlite_unchanged=True,
        ibov_closes_sha256=sha(RESULT/'ibov_june_closes.csv'),
        established_selections=[dict(strategy='R03',years=[2014,2015]),dict(strategy='B00S',years=[2014,2015,2016])],
        calculated_intervals=[dict(strategy='R03 B2',count=2),dict(strategy='BH padrão',count=12),
                              dict(strategy='B00S B2',count=1),dict(strategy='B00S BH+entradas',count=1)],
        qualifications=['BH class valuation conventions','B00S transcribed and inferred rights evidence'],
        prior_original_documents_added=17,parsed_original_statement_facts=1306,prior_raw_cotahist_quotes_verified=54,
        source_integrity='SHA256 archived extracts, frozen caches, original response hashes and local source archives',
        exclusions_are_not_zero_returns=True,monetary_simulation=False,taxes=False,external_contributions=False,
        files=[dict(path=str(p.relative_to(SEL)),sha256=sha(p),bytes=p.stat().st_size)
            for p in sorted(SEL.rglob('*')) if p.is_file() and p.name!='manifest.json'])
    (SEL/'manifest.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n')
    files=[ROOT/'.github/workflows/returns-stage1.yml',ROOT/'docs/checkpoint_returns_2014_2026_stage1.md']
    files+=list((ROOT/'scripts').glob('*stage1*.py'))
    files+=[ROOT/'tests/test_returns_stage1.py',ROOT/'tests/test_stage1_pit.py',ROOT/'tests/test_stage1_continuity.py']
    for folder in ['returns_2014_2026_inputs','returns_2014_2026_results','returns_2014_2026_selection']:
        files.extend(p for p in (ROOT/'research'/folder).rglob('*') if p.is_file() and p.name!='delivery_manifest.json')
    manifest=dict(status='PARTIAL_NOT_FULL_FOUR_PORTFOLIO_STUDY',files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(set(files))])
    (RESULT/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Files',len(manifest['files']))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path);main(p.parse_args().data_root)
