"""Persist a small in-place inventory for a resumed Codespace window."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
from ..audit import HERE,ROOT,sha256

DESTINATION=HERE/'local_only/session_recovery_round3_20261010'


def save():
    DESTINATION.mkdir(parents=True,exist_ok=True)
    legacy=json.loads((HERE/'local_only/session_recovery_20261010/artifact_inventory.json').read_text())
    paths={(r['root'],r['file']) for r in legacy}
    new=[HERE/'protocol_round3.json',ROOT/'tests/test_fundamental_multipliers_round3.py']
    new+=list((HERE/'round3').glob('*.py'))+list((HERE/'round3').glob('*.txt'))
    new+=list((HERE/'published_round3').glob('*'))+list((HERE/'local_only/round3').rglob('*'))
    new+=list(HERE.glob('*RODADA3.md'))+[HERE/'publication_review_round3.json']
    for p in new:
        if p.is_file():paths.add(('project',str(p.relative_to(ROOT))))
    inventory=[]
    for kind,name in sorted(paths):
        p=(ROOT if kind=='project' else ROOT.parent)/name
        inventory.append(dict(root=kind,file=name,bytes=p.stat().st_size,sha256=sha256(p)))
    path=DESTINATION/'artifact_inventory.json'
    path.write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    state=dict(saved_utc=datetime.now(timezone.utc).isoformat(),head=head,
        branch='study/fundamentals-multipliers-pilot-20261009',pr=8,draft=True,merge_authorized=False,
        prior_public_checkpoint='49639c7d83690f8b22a8bee40356f232e9ae689a',
        private_evidence_commit='cc069eef1cceef5a4f43f929d1bb5b72f4ca3c34',
        inventory_sha256=sha256(path),inventory_files=len(inventory),
        resume_document='research/fundamental_multipliers_pilot/RETOMADA_RODADA3.md',
        publication='Only aggregate publication reviewed; all individual evidence remains local',
        conclusion='No reliable predictive indicator validated; conditional empirical results are saved, with missing-loss bounds')
    (DESTINATION/'checkpoint.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    print('Saved resumable state:',len(inventory),'file hashes; no data copies; head',head)


def verify():
    state=json.loads((DESTINATION/'checkpoint.json').read_text());path=DESTINATION/'artifact_inventory.json'
    if sha256(path)!=state['inventory_sha256']:raise ValueError('RECOVERY_INVENTORY_CHANGED')
    for r in json.loads(path.read_text()):
        if r['root'] not in ['project','source'] or Path(r['file']).is_absolute() or '..' in Path(r['file']).parts:
            raise ValueError('UNSAFE_RECOVERY_PATH')
        p=(ROOT if r['root']=='project' else ROOT.parent)/r['file']
        if not p.is_file() or p.stat().st_size!=r['bytes'] or sha256(p)!=r['sha256']:
            raise ValueError('RECOVERY_ARTIFACT_CHANGED: '+r['file'])
    print('OK:',state['inventory_files'],'third-round and preserved-source hashes; resume with',state['resume_document'])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['save','verify'])
    args=parser.parse_args();save() if args.action=='save' else verify()


if __name__=='__main__':main()
