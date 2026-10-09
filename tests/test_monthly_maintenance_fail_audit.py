import csv
import hashlib
import json
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audit_monthly_maintenance_fail import classify,OUT


def rows(name):
    with (OUT/name).open() as f:return list(csv.DictReader(f))


def decision(**kwargs):
    args=dict(false_zeros=[],known_nonpositive=[],screen_status='INDETERMINATE',cash_rejection=False,
              positive_distribution_evidence=False,source_liquidity=None,actual_liquidity=None,complete_positive=False)
    args.update(kwargs);return classify(**args)


def test_absence_or_unresolved_zeros_are_not_proof_of_fail():
    assert decision()=='INDETERMINATE_FAIL_NOT_PROVED'
    assert decision(false_zeros=[2020])=='INDETERMINATE_FAIL_NOT_PROVED'
    assert decision(cash_rejection=True)=='INDETERMINATE_FAIL_NOT_PROVED'


def test_real_loss_is_not_erased_by_another_bad_zero():
    assert decision(false_zeros=[2020],known_nonpositive=[2019],screen_status='PASS',complete_positive=False)=='NONPOSITIVE_PROFIT_DOCUMENTED'


def test_unit_liquidity_is_distinct_from_inherited_class():
    assert decision(source_liquidity=False,actual_liquidity=True)=='WRONG_SECURITY_LIQUIDITY'
    assert decision(source_liquidity=False,actual_liquidity=False)=='LIQUIDITY_FILTER_MATCHES'


def test_distribution_conflict_is_not_certified_approval():
    assert decision(cash_rejection=True,positive_distribution_evidence=True,screen_status='PASS')=='DISTRIBUTION_GAP_DISPUTED'


def test_complete_coverage_of_all_voluntary_sales_in_all_modes():
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert set(manifest['mode_counts'].values())=={18}
    audited=rows('sales_audit_all_modes.csv')
    assert len(audited)==54
    for mode in manifest['mode_counts']:
        with (ROOT/'research/monthly_policy_corrected_2014_2026'/mode/'trades.csv').open() as f:
            original=[r for r in csv.DictReader(f) if r['side']=='SELL']
        expected={(r['portfolio'],r['date'],r['ticker'],r['amount']) for r in original}
        actual={(r['portfolio'],r['date'],r['ticker'],r['amount']) for r in audited if r['mode']==mode}
        assert actual==expected
    assert manifest['no_results_recalculated'] is True


@pytest.mark.parametrize('ticker,year,badyears',[('BRSR6',2021,{2019,2020}),('SBSP3',2024,{2022,2023})])
def test_false_profit_zeros_contradicted_by_receipt_before_cutoff(ticker,year,badyears):
    findings=[r for r in rows('exit_evidence_audit.csv') if r['ticker']==ticker and int(r['year'])==year]
    assert len(findings)==1 and findings[0]['classification']=='LEGACY_PROFIT_ZERO_CONTRADICTED'
    facts=[r for r in rows('pit_facts.csv') if r['ticker']==ticker and int(r['review_year'])==year and r['metric']=='NI']
    assert len(facts)==5 and all(float(r['value_brl'])>0 for r in facts)
    actual={int(r['fiscal_year']) for r in facts if r['legacy_zero_contradicted']=='True'}
    assert actual==badyears
    assert all(r['received']<=r['cutoff'] for r in facts)


def test_all_statement_facts_are_pit_and_cash_gap_has_same_year_evidence():
    facts=rows('pit_facts.csv')
    assert all(r['received']<=r['cutoff'] for r in facts if r['received'])
    gap=next(r for r in rows('exit_evidence_audit.csv') if r['ticker']=='CPFE3')
    assert gap['cash_gap_years']==gap['cash_conflict_years']=='2015'
    payments=[r for r in facts if r['ticker']=='CPFE3' and r['fiscal_year']=='2015' and r['metric']=='distributions']
    assert len(payments)==1 and float(payments[0]['value_brl'])==-850000


def test_real_losses_and_actual_liquidity_remain_separate():
    findings=rows('exit_evidence_audit.csv')
    known={r['ticker'] for r in findings if r['classification']=='NONPOSITIVE_PROFIT_DOCUMENTED'}
    assert known=={'CSMG3','LIGT3','IRBR3','AURE3'}
    coce=[r for r in rows('actual_security_liquidity.csv') if r['ticker']=='COCE5']
    assert len(coce)==2 and all(float(r['median_volume'])<1e6 for r in coce)
    unit=next(r for r in rows('actual_security_liquidity.csv') if r['ticker']=='TIET11')
    assert float(unit['median_volume'])==17226607 and unit['liquidity_pass']=='True'


def test_audit_does_not_change_prior_results_or_inputs():
    manifest=json.loads((OUT/'manifest.json').read_text())
    for section in ['old_results_protected','sources']:
        for name,expected in manifest[section].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
