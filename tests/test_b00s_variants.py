import csv
import json
import math
from decimal import Decimal
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b00s_variants as m

@pytest.fixture(scope='module')
def runs():
    return {v:m.simulate(v) for v in ['V0','V10']}

def test_protected_271_files_and_protocol():
    assert m.verify_frozen()==271
    lock=json.loads((m.INPUT/'protocol_lock.json').read_text())
    assert lock['specification_sha256']==m.sha(m.ROOT/'docs/experimento_b00s_quatro_variantes_2014_2026.md')
    assert lock['valuation_thresholds']==[15,25]

def test_universe_is_frozen_control():
    assert len(m.candidates())==229
    assert len({r['cnpj'] for r in m.candidates()})==29
    assert all(r['base_status']=='PASS' and r['sector'] in ['Bancos','Energia','Saneamento','Seguros','Telecom'] for r in m.candidates())
    for y in range(2014,2026):
        rows=[r for r in m.candidates() if r['year']==y]
        assert len(rows)==len({r['cnpj'] for r in rows})

def test_v0_replay_matches_twelve_frozen_returns(runs):
    old=m.read(m.BASE/'annual_returns_pct.csv')
    assert len(runs['V0']['annual'])==12
    for r,o in zip(runs['V0']['annual'],old):assert r['return_pct']==pytest.approx(float(o['B00S B2']),abs=1e-10)
    assert runs['V0']['annual'][-1]['cumulative_pct']==pytest.approx(402.1319722398,abs=1e-10)

def test_initial_ten_has_nine_companies(runs):
    rows=[r for r in runs['V10']['positions'] if r['date']==m.DATES[2014] and r['phase']=='AFTER_REVIEW']
    assert len(rows)==9
    assert {r['ticker'] for r in rows}=={'ITUB4','BBDC4','CMIG4','TBLE3','CSMG3','SBSP3','PSSA3','TIMP3','VIVT4'}
    assert sum(r['weight_pct'] for r in rows)==pytest.approx(100)
    assert next(r['weight_pct'] for r in rows if r['ticker']=='PSSA3')==20

def test_tie_breaks_and_no_liquidity_churn():
    def row(t,med,sess,total):return dict(year=2014,ticker=t,sector='Bancos',cnpj=t,median_volume=med,sessions=sess,total_volume=total)
    rows=[row('A',9,126,9),row('B',10,125,9),row('C',10,126,8),row('D',10,126,9),row('E',10,126,9)]
    meta={r['ticker']:r for r in rows}
    chosen,_=m.select_ten(rows,{}, {},meta);assert set(chosen)=={'D','E'}
    chosen,d=m.select_ten(rows,{'A':.4,'B':.6},{'A':'INDETERMINATE','B':'PASS'},meta)
    assert set(chosen)=={'A','B'}
    chosen,_=m.select_ten(rows,{'A':.4,'B':.6},{'A':'FAIL','B':'PASS'},meta)
    assert set(chosen)=={'B','D'}

def test_continuity_slots_and_self_financing(runs):
    run=runs['V10']
    assert len(run['annual'])==12
    for y in range(2014,2026):
        rs=[r for r in run['reviews'] if r['year']==y]
        if y>2014:
            assert sum(r['change'] for r in rs)==pytest.approx(0,abs=1e-12)
            scales=[r['after']/r['before'] for r in rs if r['before']>0 and r['after']>0]
            assert max(scales)-min(scales)<1e-12
            assert all(r['base_status']=='FAIL' for r in rs if not r['after'])
        pos=[r for r in run['positions'] if r['date']==m.DATES[y] and r['phase']=='AFTER_REVIEW']
        bysector={}
        for p in pos:
            meta=m.identities()[p['ticker']];bysector.setdefault(meta['sector'],set()).add(meta['cnpj'])
        assert all(len(v)<=2 for v in bysector.values())
        assert sum(p['weight_pct'] for p in pos)==pytest.approx(100)

def test_exact_decimal_attribution_and_corporate_descendants(runs):
    for run in runs.values():
        rows=m.reconcile(run['holdings'],run['annual'])
        for a in run['annual']:
            s=sum((Decimal(str(r['contribution_pp'])) for r in rows if r['year']==a['year']),Decimal(0))
            assert s==Decimal(str(a['return_pct']))
    assert any('XPBR31' in r['descendants'] and r['ticker']=='ITUB4' for r in runs['V10']['holdings'])

def test_no_fictitious_zero_or_late_start():
    ds={(r['year'],r['ticker']):dict(quality_category='INDETERMINATE') for r in m.candidates()}
    run=m.simulate('VQ',ds)
    assert len(run['annual'])==12 and not run['holdings']
    assert all(r['return_pct']=='' and r['status']=='NOT_FORMED' for r in run['annual'])
