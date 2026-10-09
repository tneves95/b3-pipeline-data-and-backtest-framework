import csv
import json
import math
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import monthly_corrected_simulate as engine
from monthly_policy_corrected import (references,recognize_winners,allocate_cash,review_members,
                                      maintenance_evidence,FAIL_REASON,BH)
from monthly_tax_accounting import Fiscal
from run_monthly_corrected import guard_legacy,OUT


def test_absence_or_pass_or_indeterminate_never_authorizes_exit():
    buyers={'p':'PASS','i':'INDETERMINATE','f':'FAIL'}
    evidence={('V0',2015,c):{'status':s,'reason':FAIL_REASON} for c,s in [('p','PASS'),('i','INDETERMINATE'),('f','FAIL')]}
    kept,exits,entries=review_members('V0',2015,buyers,{'new':'NEW'},evidence)
    assert kept=={'p':'PASS','i':'INDETERMINATE','new':'NEW'}
    assert set(exits)=={'f'} and entries=={'new'}


@pytest.mark.parametrize('portfolio',sorted(BH))
def test_bh_ignores_voluntary_exit_and_admission(portfolio):
    buyers={'a':'A'};ev={(portfolio,2015,'a'):{'status':'FAIL','reason':FAIL_REASON}}
    assert review_members(portfolio,2015,buyers,{'b':'B'},ev)==(buyers,{},set())


def test_winner_reference_is_not_cap_and_marker_survives_dilution():
    buyers={str(i):str(i) for i in range(20)}
    values={c:84/19 for c in buyers};values['0']=16
    winners=recognize_winners(buyers,set(),values,100,{c:1 if c=='0' else 0 for c in buyers})
    assert winners=={'0'} and references(buyers,winners)['0']==.1
    buys,_=allocate_cash(values,2.5,set(buyers),102.5,references(buyers,winners))
    assert '0' not in buys and values['0']==16
    values['0']=8
    assert recognize_winners(buyers,winners,values,100,{c:0 for c in buyers})==winners
    buys,_=allocate_cash(values,2.5,set(buyers),102.5,references(buyers,winners))
    assert buys['0']>0


def test_n16_to15_suspends_reference_without_erasing_marker():
    buyers={str(i):str(i) for i in range(16)};winners={'0'}
    assert references(buyers,winners)['0']==2/16
    del buyers['15']
    winners=recognize_winners(buyers,winners,{},100,{})
    assert winners=={'0'} and references(buyers,winners)['0']==1/15
    buyers['new']='NEW'
    assert references(buyers,winners)['0']==2/16


def synthetic(monkeypatch,*,fail=False,entry=False):
    start='2014-06-30';end='2015-06-30';buyers={str(i):f'T{i}' for i in range(20)}
    desired=buyers.copy()
    if entry:desired['new']='NEW'
    quote={(t,d):(4. if t=='T0' and d==end else 1.) for t in list(buyers.values())+['NEW'] for d in [start,end]}
    monkeypatch.setattr(engine,'read',lambda p:[{'date':end,'month_end':end}])
    evidence={('V0',2015,'1'):dict(status='FAIL',reason=FAIL_REASON,source='synthetic',source_line=2,source_ticker='T1')} if fail else {}
    f=Fiscal('V0',{},[start,end],enabled=False)
    return engine.simulate('V0',quote,{}, {('V0',2014):buyers,('V0',2015):desired},end=end,monthly=0,fiscal=f,evidence=evidence)


def test_engine_preserves_above_2x_winner_wholly(monkeypatch):
    r=synthetic(monkeypatch)
    assert not [x for x in r['trades'] if x['side']=='SELL']
    assert r['book']['0']['T0']==5000
    final=[x for x in r['positions'] if x['phase']=='AFTER_JUNE_REVIEW' and x['ticker']=='T0'][0]
    assert final['winner_flag'] and final['security_weight']>final['buy_reference_weight']


def test_engine_june_entry_waits_for_cash_without_incumbent_sales(monkeypatch):
    r=synthetic(monkeypatch,entry=True)
    assert len(r['trades'])==20 and 'new' not in r['book']
    assert r['summary']['active_lineages']==21
    assert next(x for x in r['junes'] if x['lineage']=='new')['unfunded_eligible']


def test_engine_sells_only_confirmed_fail(monkeypatch):
    r=synthetic(monkeypatch,fail=True,entry=True)
    sells=[x for x in r['trades'] if x['side']=='SELL']
    assert len(sells)==1 and sells[0]['ticker']=='T1' and sells[0]['reason']==FAIL_REASON
    assert r['book']['0']['T0']==5000
    assert 'new' in r['book']


def read(p):
    with p.open() as f:return list(csv.DictReader(f))


def test_preserved_legacy_checkpoint_hashes():assert guard_legacy()>20


def test_actual_gross_outputs_and_authorized_sales():
    rows=read(OUT/'consolidated_policy_corrected.csv')
    assert len(rows)==5
    proofs=maintenance_evidence()
    trades=read(OUT/'GROSS/trades.csv')
    for r in rows:
        assert float(r['external_capital'])==460000 and int(r['external_contributions'])==144
        if r['portfolio'] in BH:
            assert int(r['voluntary_sales'])==0
            assert float(r['final_wealth'])==pytest.approx(float(r['original_pr5_wealth']),abs=1e-6)
    for t in trades:
        if t['side']=='SELL':
            p=proofs[t['portfolio'],int(t['date'][:4]),t['lineage']]
            assert t['reason']==p['reason']==FAIL_REASON and t['date'][5:7]=='06'
    for p in ['V0','V10','VVAL']:
        actual=[r for r in trades if r['portfolio']==p and r['side']=='SELL']
        assert len(actual)==len([k for k in proofs if k[0]==p])


def test_actual_cash_and_deposit_integrity():
    for r in read(OUT/'GROSS/wealth.csv'):
        assert float(r['cash_available'])>=-1e-6
        assert float(r['tax_paid'])==0 and float(r['tax_liability'])==0
    rows=read(OUT/'GROSS/contributions.csv')
    for p in {r['portfolio'] for r in rows}:
        group=[r for r in rows if r['portfolio']==p]
        assert len(group)==144 and len({r['date'] for r in group})==144
        assert all(float(r['external_deposit'])==2500 for r in group)
