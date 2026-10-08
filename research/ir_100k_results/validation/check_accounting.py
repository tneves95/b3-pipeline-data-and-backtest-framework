"""Validate completed artifacts; does not generate or reconstruct returns."""
import csv,gzip,hashlib,json,math
from pathlib import Path
root=Path('research/ir_100k_results')
def read(name):return list(csv.DictReader(open(root/name,encoding='utf-8-sig')))
r=read('results.csv');sens=read('sensitivities.csv');assert len(r)==372 and len(sens)==2604
assert len({x['case_id'] for x in r})==372 and len({(x['case_id'],x['assumption']) for x in sens})==2604
assert {x['policy'] for x in r}=={'A','B2','BH'} and all(float(x['initial'])==100000 for x in r)
assert not read('failures.csv')
years=read('yearly.csv');annual=read('annual.csv');ledger=json.loads(gzip.decompress((root/'ledger.json.gz').read_bytes()))
for x in r:
 ys=[a for a in years if a['case_id']==x['case_id']];assert math.isclose(sum(float(a['tax_paid']) for a in ys),float(x['tax_sales']),abs_tol=1e-6)
 assert math.isclose(sum(float(a['tax_assessed']) for a in ys),float(x['tax_sales']),abs_tol=1e-6)
 assert float(x['min_cash'])>=-1e-6
for a in annual:
 if '_B2_' not in a['case_id']:continue
 qb=json.loads(a['quantities_before']);qa=json.loads(a['quantities_after_sales']);bb=json.loads(a['basis_before']);ba=json.loads(a['basis_after_sales'])
 for t in a['retained'].split(';'):
  if not t:continue
  assert qa[t]>0 and qa[t]<=qb[t]+1e-8
  # Same-day buys are paired separately: the unchanged old-lot average is
  # explicitly tested in pytest; fully untouched positions must preserve total basis.
  if abs(qa[t]-qb[t])<1e-8:assert math.isclose(ba[t],bb[t],abs_tol=1e-6)
 assert int(a['entrants_funded'])==int(a['entrants_count'])
for row in ledger:
 assert row['cash']>=-1e-6
 if row['kind']=='BUY':assert row['cash']+1e-6>=row['tax_reserved']
print(json.dumps(dict(status='PASS',main=372,sensitivities=2604,annual_rows=len(annual),ledger_rows=len(ledger),checks=['no extra renewal policy','100k every cohort','assessed equals paid tax','nonnegative cash','tax reserved before buying','untouched survivors retain basis','all entrants financed','no failed main case']),indent=2))
