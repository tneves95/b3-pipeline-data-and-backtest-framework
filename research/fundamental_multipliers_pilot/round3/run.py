"""Offline third-round execution; immutable prior checkpoints remain verifiable."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import pandas as pd
from ..audit import HERE,ROOT,sha256
from .scale import Prices,build_events,build_matrix
from .features import make_features,join_matrix
from .statistics import run_statistics
from .validation import validate
from .assessment import assess


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE/'local_only/round3')
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if HERE/'local_only' not in out.parents and Path('/tmp') not in out.parents:
        raise SystemExit('Individual output must stay in local_only or /tmp')
    previous=HERE/'recovery/verify_checkpoint.py'
    subprocess.run([sys.executable,str(previous)],check=True)
    protocol_path=HERE/'protocol_round3.json';protocol=json.loads(protocol_path.read_text())
    input_paths=[ROOT.parent/'b3_market_data.sqlite',HERE/'local_only/round2/quote_overlay.sqlite',
        HERE/'local_only/round2/panel_simple_indicators_pit.csv',
        HERE/'local_only/round2/return_certification_matrix.csv',
        HERE/'local_only/round2/reconciled_economic_events.csv',
        HERE/'local_only/round2/certification_scopes.json',HERE/'local_only/round2/exchange_calendar.csv',
        HERE/'local_only/data/raw_quote_coverage.csv',HERE/'local_only/data/annual_filing_versions.csv',
        HERE/'local_only/round2/filing_recovery.csv',HERE/'local_only/round3/gpc_itr_201606.pdf',protocol_path,
        ROOT/'research/returns_2014_2026_selection/cache/continuation_events.json.gz']
    input_paths+=sorted((ROOT.parent/'data/cvm').glob('fre_cia_aberta_*.zip'))
    input_paths+=sorted((ROOT/'research/returns_2014_2026_inputs/b3').glob('ibov_*.json'))
    inputs=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha256(p)) for p in input_paths]
    panel=pd.read_csv(HERE/'local_only/round2/panel_simple_indicators_pit.csv',dtype={'cnpj':str})
    book=Prices(ROOT.parent,HERE/'local_only/round2')
    try:
        events,flags=build_events(book,ROOT.parent,HERE/'local_only/round2',panel,out)
        matrix=build_matrix(book,panel,events,flags,HERE/'local_only/round2',out,protocol)
        features=make_features(book,panel,events,out,protocol)
        analysis=join_matrix(matrix,features,ROOT);analysis.to_csv(out/'analysis_panel.csv',index=False)
        aggregates=out/'aggregates';coverage,_,_=run_statistics(analysis,protocol,aggregates)
        validation=validate(book,matrix,events,out,protocol)
        assess(analysis,coverage,protocol,aggregates)
    finally:book.close()
    for r in inputs:
        if sha256(Path(r['path']))!=r['sha256']:raise ValueError('IMMUTABLE_INPUT_CHANGED: '+r['path'])
    subprocess.run([sys.executable,str(previous)],check=True)
    outputs=[dict(file=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha256(p))
        for p in sorted(out.rglob('*')) if p.is_file() and p.name!='run_manifest.json']
    code=[dict(path=str(p.relative_to(ROOT)),sha256=sha256(p)) for p in sorted(Path(__file__).parent.glob('*.py'))]
    manifest=dict(version=3,completed_utc=datetime.now(timezone.utc).isoformat(),source_sqlite_unchanged=True,
        preserved_prior_artifacts=413,inputs=inputs,outputs=outputs,code=code,
        protocol_sha256=sha256(protocol_path),validation=validation,
        environment={k:importlib.metadata.version(k) for k in ['pandas','numpy','scipy','pyarrow']},
        return_counts=matrix.groupby(['horizon_years','calendar_complete','grade']).size().to_dict())
    manifest['return_counts']={str(k):int(v) for k,v in manifest['return_counts'].items()}
    (out/'run_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Completed offline third round:',out,flush=True)


if __name__=='__main__':main()
