from pathlib import Path
import sys
import json
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b00s_fundamentals as f
import b00s_variants as m

def test_median_real_profit_not_current_pe():
    assert f.normalized_profit([10,20,30,40,1000],[2,1.8,1.6,1.4,1.2])==48
    assert f.normalized_profit([10,None,30,40,50],[1]*5) is None
    assert f.normalized_profit([10,20,30,40,50],[1,1,1,None,1]) is None

def test_capital_by_each_class_and_no_on_proxy():
    assert f.class_capitalization([{'quantity':100,'price':10},{'quantity':200,'price':15}])==4000
    assert f.class_capitalization([{'quantity':100,'price':None},{'quantity':200,'price':15}]) is None
    assert f.class_capitalization([{'quantity':0,'price':None},{'quantity':200,'price':15}])==3000

@pytest.mark.parametrize('pe,result',[(15,'PASS_MATURE'),(15.0001,'INDETERMINATE'),(25,'INDETERMINATE'),(25.0001,'REJECTED_PRICE'),(None,'INDETERMINATE'),(0,'INDETERMINATE')])
def test_two_valuation_channels(pe,result):
    assert f.valuation_gate(pe,{})==result

def test_reinvestment_requires_all_four_conditions_and_no_dy_gate():
    e=dict(real_eps_cagr=.04,average_payout=.8,return_on_capital_median=.12,inflation_reference=.06,solidity_proven=True,bazin_normalized_dy=.01,graham_pe_pb=100)
    assert f.valuation_gate(25,e)=='PASS_REINVESTOR'
    for k in ['real_eps_cagr','average_payout','return_on_capital_median','inflation_reference','solidity_proven']:
        assert f.valuation_gate(20,dict(e,**{k:None}))=='INDETERMINATE'
    assert f.valuation_gate(14,dict(e,average_payout=.2))=='PASS_MATURE'
    assert f.valuation_gate(20,dict(e,solidity_proven=False))=='REJECTED_REINVESTMENT'
    assert f.valuation_gate(20,dict(e,real_eps_cagr=.0399))=='REJECTED_REINVESTMENT'
    assert f.valuation_gate(20,dict(e,return_on_capital_median=.119))=='REJECTED_REINVESTMENT'
    assert f.valuation_gate(30,e,18,30)=='PASS_REINVESTOR'

def test_quality_cannot_compensate_missing_or_material_failure():
    dims={k:dict(status='HIGH',evidence=['dated-source']) for k in f.DIMENSIONS}
    assert f.quality_gate(dims)=='QUALIFIED_HIGH'
    dims['financial_resilience']=dict(status='INDETERMINATE',evidence=[])
    assert f.quality_gate(dims)=='INDETERMINATE'
    dims['financial_resilience']=dict(status='REJECTED_EVIDENCED',material_evidence='dated-material-finding')
    assert f.quality_gate(dims)=='REJECTED_EVIDENCED'
    with pytest.raises(ValueError):f.quality_gate({k:v for k,v in dims.items() if k!='governance'})

def test_frozen_decisions_have_no_future_sources_or_unapproved_base_names():
    ds=json.loads((m.INPUT/'fundamental_decisions.json').read_text())
    assert {(r['year'],r['ticker']) for r in ds}=={(r['year'],r['ticker']) for r in m.candidates()}
    assert m.sha(m.INPUT/'fundamental_decisions.json')==json.loads((m.INPUT/'fundamental_decisions_lock.json').read_text())['decisions_sha256']
    for r in ds:
        for e in r['profit_evidence']+r['payout_evidence']:assert e['received']<=r['cutoff']
        assert r['capital_source'] is None or r['capital_source']['received']<=r['cutoff']
        if r['sector'] not in ['Bancos','Seguros'] and r['return_on_capital_median'] is not None:
            assert r['return_on_capital_kind'].startswith('ROIC_')
            assert r['documentary_assessment']['economic_metrics']['roic']['annual_inputs']
        if r['valuation_status'].startswith('PASS'):
            assert r['perimeter_review']['status'] in ['COMPARABLE','COMPARABLE_BOUNDED']
            assert r['normalized_pe'] is not None or r['normalized_pe_interval']['upper']<=15

def test_price_and_quality_only_gate_entries():
    rows=[r for r in m.candidates() if r['year']==2015]
    holdings={'BBDC4':.6,'TBLE3':.4}
    ds={(r['year'],r['ticker']):dict(valuation_status='REJECTED_PRICE') for r in rows}
    targets=m.select_filtered(rows,holdings,ds,'VVAL')
    after,ledger=m.renew_b2(holdings,{'BBDC4':'PASS','TBLE3':'INDETERMINATE'},targets)
    assert after==holdings and not targets

def test_irbr_2019_not_rejected_by_future_events():
    r=next(r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['ticker']=='IRBR3' and r['year']==2019)
    assert r['quality_category']=='INDETERMINATE'
    assert all(e['received']<=m.DATES[2019] for e in r['profit_evidence'])
