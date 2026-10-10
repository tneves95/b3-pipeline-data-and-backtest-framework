"""Verify the session handoff in place, without network access or data mutation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1 << 20),b''):
            h.update(block)
    return h.hexdigest()


def main():
    project=Path(__file__).resolve().parents[3]
    default=project/'research/fundamental_multipliers_pilot/local_only/session_recovery_20261010/checkpoint.json'
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,default=default)
    args=parser.parse_args()
    state=json.loads(args.checkpoint.read_text())
    manifest=args.checkpoint.parent/state['artifact_inventory']['file']
    if digest(manifest)!=state['artifact_inventory']['sha256']:
        raise SystemExit('FAIL: recovery inventory hash differs from saved checkpoint')
    inventory=json.loads(manifest.read_text())
    roots={'project':project,'source':project.parent}
    failed=[]
    for item in inventory:
        relative=Path(item['file'])
        if item['root'] not in roots or relative.is_absolute() or '..' in relative.parts:
            failed.append('Unsafe saved path: '+str(relative));continue
        path=roots[item['root']]/relative
        if not path.is_file():failed.append('Missing: '+str(relative));continue
        if path.stat().st_size!=item['bytes'] or digest(path)!=item['sha256']:
            failed.append('Hash/size changed: '+str(relative))
    if failed:
        print('\n'.join(failed))
        raise SystemExit(1)
    print(f"OK: {len(inventory)} saved artifacts and original sources verified; no files changed.")
    print(f"PR #8: draft, no merge. Analysis commit: {state['analysis_commit']}")
    print('Next: follow RETOMADA.md; predictive coverage remains insufficient.')


if __name__=='__main__':main()
