import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import monthly_maintenance_reaudit as maintenance
import monthly_reaudit_simulate as engine
from monthly_policy_corrected import FAIL_REASON, references, recognize_winners, allocate_cash
from monthly_tax_accounting import Fiscal
from monthly_contributions import xirr

OUT=maintenance.OUT
MODES=['GROSS','CG_ONLY','CG_PLUS_JCP_CERTIFIED_PARTIAL']


def rows(path):
    with path.open() as f:return list(csv.DictReader(f))


def test_missing_pass_and_indeterminate_never_authorize_sale():
    held={'p':'P','i':'I','u':'U','f':'F'}
    evidence={('V0',2024,c):dict(status=s,reason=FAIL_REASON) for c,s in [('p','PASS'),('i','INDETERMINATE'),('f','FAIL')]}
    kept,exits,entries=maintenance.review_members('V0',2024,held,{'n':'N'},evidence)
    assert kept=={'p':'P','i':'I','u':'U','n':'N'} and set(exits)=={'f'} and entries=={'n'}


@pytest.mark.parametrize('portfolio',['BH padrão','BESST-10 BH'])
def test_bh_no_voluntary_sales_even_if_evidence_fail(portfolio):
    assert maintenance.review_members(portfolio,2024,{'a':'A'},{'b':'B'},
        {(portfolio,2024,'a'):dict(status='FAIL')})==({'a':'A'},{},set())


def test_v10_retained_sector_slots_block_replacement(monkeypatch):
    monkeypatch.setattr(maintenance.economic,'identities',lambda:{t:dict(sector='Saneamento') for t in ['SBSP3','SAPR4','CSMG3']})
    held={'sb':'SBSP3','sa':'SAPR4'};new={'cs':'CSMG3'}
    kept,exits,entries=maintenance.review_members('V10',2024,held,new,{})
    assert kept==held and not exits and not entries
    ev={('V10',2024,'sb'):dict(status='FAIL',reason=FAIL_REASON)}
    kept,exits,entries=maintenance.review_members('V10',2024,held,new,ev)
    assert kept=={'sa':'SAPR4','cs':'CSMG3'} and set(exits)=={'sb'} and entries=={'cs'}


def test_failed_audited_candidate_cannot_reenter():
    ev={('V0',2025,'a'):dict(status='FAIL',reason=FAIL_REASON)}
    assert maintenance.review_members('V0',2025,{}, {'a':'AURE3'},ev)==({}, {}, set())


def synthetic(monkeypatch,fail=False,entry=False):
    start='2014-06-30';end='2015-06-30';buyers={str(i):f'T{i}' for i in range(20)}
    desired=buyers.copy()
    if entry:desired['new']='NEW'
    quote={(t,d):(4. if t=='T0' and d==end else 1.) for t in list(buyers.values())+['NEW'] for d in [start,end]}
    monkeypatch.setattr(engine,'read',lambda p:[{'date':end,'month_end':end}])
    ev={('V0',2015,'1'):dict(status='FAIL',reason=FAIL_REASON,source='test',source_line=2,source_ticker='T1')} if fail else {}
    return engine.simulate('V0',quote,{}, {('V0',2014):buyers,('V0',2015):desired},end=end,monthly=0,
        fiscal=Fiscal('V0',{},[start,end],enabled=False),evidence=ev)


def test_new_engine_winner_above_twice_kept_whole(monkeypatch):
    r=synthetic(monkeypatch)
    assert r['book']['0']['T0']==5000 and r['summary']['voluntary_sales']==0
    assert any(j['lineage']=='0' and j['winner_flag'] for j in r['junes'])


def test_new_engine_entry_does_not_liquidate_incumbents(monkeypatch):
    r=synthetic(monkeypatch,entry=True)
    assert r['summary']['voluntary_sales']==0 and 'new' not in r['book']
    assert next(j for j in r['junes'] if j['lineage']=='new')['unfunded_eligible']


def test_new_engine_only_proved_fail_sold(monkeypatch):
    r=synthetic(monkeypatch,fail=True)
    sells=[t for t in r['trades'] if t['side']=='SELL']
    assert len(sells)==1 and sells[0]['ticker']=='T1' and sells[0]['maintenance_status']=='FAIL'


def test_winner_marker_and_contributions_resume_below_reference():
    buyers={str(i):str(i) for i in range(20)};winner={'0'}
    values={c:84/19 for c in buyers};values['0']=16.
    assert '0' not in allocate_cash(values,2.5,set(buyers),102.5,references(buyers,winner))[0]
    values['0']=8.
    assert recognize_winners(buyers,winner,values,100,{c:0. for c in buyers})==winner
    assert allocate_cash(values,2.5,set(buyers),102.5,references(buyers,winner))[0]['0']>0


def test_prior_checkpoints_and_sources_preserved():assert maintenance.guard_prior()>=70


def test_reaudited_decisions_and_successors_are_pit():
    decisions=rows(OUT/'maintenance_reviews.csv');facts=rows(OUT/'maintenance_pit_facts.csv')
    assert len({(r['portfolio'],r['year'],r['lineage']) for r in decisions})==len(decisions)
    assert all(r['received']<=r['cutoff'] and r['period_end']<=r['cutoff'] for r in facts)
    for t,y in [('TIET11','2016'),('CPFE3','2020'),('BRSR6','2021'),('SBSP3','2024')]:
        assert all(r['status']!='FAIL' for r in decisions if r['ticker']==t and r['year']==y)
    aes=[r for r in decisions if r['ticker']=='AESB3']
    assert len(aes)==12 and all(r['status']=='INDETERMINATE' for r in aes)
    aure=[r for r in decisions if r['ticker']=='AURE3' and r['year']=='2025']
    assert len(aure)==3 and all(r['status']=='FAIL' and r['issuer_cnpj']=='28594234000123' for r in aure)
    assert all(r['nonpositive_years']=='2021;2023' for r in aure)
    for f in facts:
        if f['actual_ticker']=='AESB3':assert f['issuer_cnpj']=='37663076000107'


@pytest.mark.parametrize('mode',MODES)
def test_gross_and_tax_sales_have_substantive_authorization(mode):
    trades=rows(OUT/mode/'trades.csv');proof=rows(OUT/'maintenance_reviews.csv')
    expected_bad={('TIET11','2016'),('CPFE3','2020'),('BRSR6','2021'),('SBSP3','2024')}
    counts={}
    for r in trades:
        if r['side']!='SELL':continue
        assert (r['ticker'],r['date'][:4]) not in expected_bad
        assert r['date'][5:7]=='06' and r['reason']==FAIL_REASON and r['maintenance_status']=='FAIL'
        p=proof[int(r['proof_line'])-2]
        assert (p['portfolio'],p['year'],p['lineage'],p['ticker'],p['status'])==(r['portfolio'],r['date'][:4],r['lineage'],r['ticker'],'FAIL')
        counts[r['portfolio']]=counts.get(r['portfolio'],0)+1
    assert counts=={'V0':6,'V10':1,'VVAL':3}
    # A new sale of AURE in VVAL is a later documented FAIL, not the annulled
    # TIET2016 exit carried forward by its old label.
    assert {r['portfolio'] for r in trades if r['side']=='SELL' and r['ticker']=='AURE3'}=={'V0','VVAL'}


@pytest.mark.parametrize('mode',MODES)
def test_gross_and_tax_flows_xirr_cash_and_final_cost_reconcile(mode):
    name={'GROSS':'consolidated_policy_corrected.csv','CG_ONLY':'consolidated_tax_corrected.csv',
          'CG_PLUS_JCP_CERTIFIED_PARTIAL':'consolidated_income_corrected.csv'}[mode]
    totals=rows(OUT/name);flows=rows(OUT/mode/'investor_flows.csv')
    wealth=rows(OUT/mode/'wealth.csv');positions=rows(OUT/mode/'final_positions.csv')
    tax=rows(OUT/mode/'annual_tax.csv')
    for s in totals:
        p=s['portfolio'];f=[(r['date'],float(r['amount'])) for r in flows if r['portfolio']==p]
        assert len(f)==146 and math.isclose(-sum(v for d,v in f[:-1]),460000,abs_tol=1e-8)
        assert math.isclose(100*xirr(f),float(s['xirr_pct']),abs_tol=1e-9)
        pos=[r for r in positions if r['portfolio']==p]
        assert math.isclose(sum(float(r['value']) for r in pos)+float(s['cash'])-float(s['unpaid_liability']),float(s['final_wealth']),abs_tol=1e-6)
        assert math.isclose(sum(float(r['total_acquisition_cost']) for r in pos),float(s['remaining_acquisition_basis']),abs_tol=1e-6)
        assert math.isclose(sum(float(r['tax_paid']) for r in tax if r['portfolio']==p),float(s['tax_paid']),abs_tol=1e-6)
        assert math.isclose(sum(float(r['income_withheld']) for r in tax if r['portfolio']==p),float(s['income_withheld']),abs_tol=1e-6)
    assert all(float(r['cash_available'])>=-1e-6 for r in wealth)
    assert all(math.isclose(float(r['cash'])-float(r['tax_restricted_cash']),float(r['cash_available']),abs_tol=1e-6) for r in wealth)


def test_gross_v10_incumbents_retained_and_original_two_sector_slots():
    junes=rows(OUT/'GROSS/junes.csv')
    for r in junes:
        if r['portfolio']=='V10':assert int(r['N'])<=10
        if r['portfolio']=='V10' and r['date'][:4] in ['2024','2025']:
            assert not (r['ticker']=='CSMG3' and r['entry']=='True')
    for mode in MODES:
        trades=rows(OUT/mode/'trades.csv')
        assert not any(r['side']=='SELL' and r['ticker']=='SBSP3' for r in trades)


def test_gross_bh_exact_parity_with_previous():
    s=rows(OUT/'consolidated_policy_corrected.csv')
    for r in s:
        if 'BH' in r['portfolio']:
            assert float(r['final_wealth'])==float(r['previous_checkpoint_wealth'])
            assert float(r['xirr_pct'])==float(r['previous_checkpoint_xirr_pct'])


@pytest.mark.parametrize('mode',MODES[1:])
def test_final_liquidation_separate_and_tax_not_double_counted(mode):
    name='consolidated_tax_corrected.csv' if mode=='CG_ONLY' else 'consolidated_income_corrected.csv'
    for s in rows(OUT/name):
        assert math.isclose(float(s['final_wealth'])-float(s['liquidation_tax']),float(s['liquidation_wealth']),abs_tol=1e-6)
        assert float(s['unpaid_liability'])==0 and float(s['liquidation_tax'])>=0


def test_net_jcp_not_withheld_twice():
    rows_=rows(OUT/'CG_PLUS_JCP_CERTIFIED_PARTIAL/income.csv')
    net=[r for r in rows_ if r['amount_basis']=='NET_ALREADY_WITHHELD']
    assert net and all(float(r['withheld_additional'])==0 for r in net)


def test_reaudited_input_manifest():
    m=json.loads((OUT/'maintenance_manifest.json').read_text())
    for path,h in m['files'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
