"""Economic invariants for selective renewal and inherited ownership."""
import csv
import hashlib
import math
from pathlib import Path
import subprocess
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from stage1_continuity import renew_b2,advance
from stage1_buyhold import apply_day,trajectory,quotes
from stage1_segments import gross_factor
from stage1_pit import OUT,gzread,DATES


def test_no_review_turnover_without_entries_or_failures():
    h={'A':.8,'B':.2}
    after,ledger=renew_b2(h,{'A':'PASS','B':'PASS'},{'A':.5,'B':.5})
    assert after==h
    assert all(r['change']==0 for r in ledger)


def test_survivors_preserved_when_failures_finance_new_entries():
    h={'A':.6,'B':.1,'C':.3}
    after,ledger=renew_b2(h,{'A':'PASS','B':'PASS','C':'FAIL','D':'PASS'},{'A':.4,'B':.4,'D':.2})
    assert after==pytest.approx({'A':.6,'B':.1,'D':.3})
    assert sum(after.values())==pytest.approx(sum(h.values()))
    assert next(r for r in ledger if r['ticker']=='C')['reason']=='FAIL_EXIT'


def test_only_shortfall_reduces_survivors_and_keeps_their_relative_drift():
    after,_=renew_b2({'A':.6,'B':.3,'C':.1},{'A':'PASS','B':'PASS','C':'FAIL','D':'PASS'},
                     {'A':.3,'B':.3,'D':.4})
    assert after==pytest.approx({'A':.4,'B':.2,'D':.4})
    assert after['A']/after['B']==pytest.approx(2.)


@pytest.mark.parametrize('status',[{}, {'A':'INDETERMINATE'}, {'A':'PASS'}])
def test_missing_or_indeterminate_is_not_fail(status):
    after,ledger=renew_b2({'A':.7,'B':.3},status,{})
    assert after=={'A':.7,'B':.3}
    assert all(r['reason']=='PRESERVED' for r in ledger)


def test_fail_without_entries_is_redistributed_proportionally():
    after,_=renew_b2({'A':.6,'B':.3,'C':.1},{'A':'PASS','B':'PASS','C':'FAIL'},{'A':.5,'B':.5})
    assert after==pytest.approx({'A':2/3,'B':1/3})


def test_no_eligible_destination_cannot_silently_create_cash_or_zero():
    with pytest.raises(ValueError):renew_b2({'A':1},{'A':'FAIL'},{})


def test_only_pass_can_be_bought_as_new_entry():
    with pytest.raises(ValueError):renew_b2({'A':1},{'B':'INDETERMINATE'},{'B':1})


def test_advancing_requires_factor_for_every_inherited_right():
    with pytest.raises(ValueError):advance({'A':.9,'XP':.1},{'A':1.1})


def test_june_review_carries_index_level_and_does_not_reset_weights():
    carried=advance({'A':.5,'B':.5},{'A':2.,'B':.5})
    after,_=renew_b2(carried,{'A':'PASS','B':'PASS'},{'A':.5,'B':.5})
    assert after==carried=={'A':1.,'B':.25}
    assert sum(after.values())==1.25
    assert after['A']/sum(after.values())==.8


def event(t,day,kind,**kw):
    return dict(id=f'{t}_{day}_{kind}',ticker=t,ex_date=day,kind=kind,**kw)


def test_same_day_bonus_and_dividend_use_old_entitlement_once():
    after=apply_day({'A':1.},[event('A','b','SHARES',factor=2.),event('A','b','DISTRIBUTION',amount=10.)],{('A','b'):45.},'b')
    assert after['A']*45==pytest.approx(100.)


def test_spinoff_preserves_both_rights_and_june_value():
    p={('A','a'):100.,('A','b'):80.,('X','b'):20.,('A','c'):90.,('X','c'):30.}
    e=[event('A','b','SPINOFF',successor='X',ratio=1.)]
    jun,_=trajectory(p,e,{'A':1.},['a','b','c'])
    levels={r['date']:r['index_total'] for r in jun}
    assert levels==pytest.approx({'a':1.,'b':1.,'c':1.2})
    assert {r['ticker'] for r in jun if r['date']=='c'}=={'A','X'}


def test_right_detached_before_simultaneous_parent_reinvestment():
    after=apply_day({'A':1.},[event('A','b','RIGHT',successor='R',ratio=.1),event('A','b','DISTRIBUTION',amount=10.)],{('A','b'):50.},'b')
    assert after==pytest.approx({'A':1.2,'R':.1})
    converted=apply_day(after,[event('R','c','RIGHT_REINVEST',successor='A')],{('R','c'):5.,('A','c'):50.},'c')
    assert converted==pytest.approx({'A':1.21})
    assert math.fsum(after[t]*{'A':50.,'R':5.}[t] for t in after)==pytest.approx(converted['A']*50.)


def test_initial_date_entitlement_excluded_and_unknown_quote_rejected():
    e=[event('A','a','SHARES',factor=10)]
    rows,_=trajectory({('A','a'):10,('A','b'):10},e,{'A':1},['a','b'])
    assert rows[-1]['index_total']==1
    with pytest.raises(KeyError):trajectory({('A','a'):10},[],{'A':1},['a','b'])


def test_duplicate_event_is_rejected_across_full_trajectory():
    e=event('A','b','DISTRIBUTION',amount=1)
    with pytest.raises(ValueError):trajectory({('A','a'):10,('A','b'):9},[e,e],{'A':1},['a','b'])


def test_real_b2_revision_differs_from_annual_equal_weight_diagnostic():
    actual=list(csv.DictReader((OUT/'established_segments_pct.csv').open()))
    diagnostic=list(csv.DictReader((OUT/'annual_selection_diagnostic_pct.csv').open()))
    assert float(actual[0]['return_pct'])==pytest.approx(-45.06833294872517)
    assert float(actual[1]['return_pct'])==pytest.approx(3.51981821516617)
    assert float(diagnostic[1]['return_pct'])==pytest.approx(1.9284757835)
    assert diagnostic[1]['portfolio']=='R03 ANNUAL_EQUAL_WEIGHT_DIAGNOSTIC'
    review=list(csv.DictReader((OUT/'b2_reviews.csv').open()))
    assert sum(float(r['before']) for r in review)==pytest.approx(sum(float(r['after']) for r in review))
    ratios=[float(r['after'])/float(r['before']) for r in review if r['ticker'] in ['DIRR3','EZTC3','HBOR3']]
    assert ratios==pytest.approx([ratios[0]]*3)


def test_bh_independent_event_product_reconciles_non_spinoff_sleeves():
    prices=quotes();events=gzread(OUT/'cache/bh_owned_events.json.gz')
    rows=list(csv.DictReader((OUT/'bh_june_positions.csv').open()))
    # Independent product formula, not the persistent-unit implementation.
    for t in ['CCRO3','WEGE3','BBDC4','TBLE3','HYPE3','RADL3']:
        p={d:v for (s,d),v in prices.items() if s==t};es=[e for e in events if e['ticker']==t]
        factor=gross_factor(p,es,DATES[2014],DATES[2026])
        final=next(r for r in rows if r['ticker']==t and r['date']==DATES[2026])
        assert float(final['index_component'])==pytest.approx(.125*factor)


def test_bh_all_junes_reconcile_and_compound_to_same_final_index():
    positions=list(csv.DictReader((OUT/'bh_june_positions.csv').open()))
    annual=list(csv.DictReader((OUT/'bh_annual_pct.csv').open()))
    assert len(annual)==12
    for d in DATES.values():
        r=[x for x in positions if x['date']==d]
        assert sum(float(x['weight']) for x in r)==pytest.approx(1.)
        assert sum(float(x['index_component']) for x in r)==pytest.approx(float(r[0]['index_total']))
    final=float(annual[-1]['cumulative_pct'])
    assert 100*(math.prod(1+float(r['return_pct'])/100 for r in annual)-1)==pytest.approx(final)
    assert any(r['ticker']=='XPBR31' and r['date']==DATES[2026] for r in positions)


def test_b00s_variants_share_initial_year_and_twenty_initial_issuers():
    rows=list(csv.DictReader((OUT/'b00s_initial_pct.csv').open()))
    assert len(rows)==2 and rows[0]['return_pct']==rows[1]['return_pct']
    assert all(r['return_status'].startswith('EXPLORATORY') for r in rows)
    p=list(csv.DictReader((OUT/'b00s_initial_positions.csv').open()))
    assert len([r for r in p if r['date']==DATES[2014]])==20
    assert {r['ticker'] for r in p if r['date']==DATES[2015]}=={r['ticker'] for r in p if r['date']==DATES[2014]}


def test_contributions_reconcile_including_xp_in_original_itau_sleeve():
    annual=list(csv.DictReader((OUT/'bh_annual_pct.csv').open()))
    positions=list(csv.DictReader((OUT/'bh_issuer_annual_pct.csv').open()))
    for r in annual:
        group=[p for p in positions if p['year']==r['year']]
        assert len(group)==8
        assert math.fsum(float(p['contribution_pp']) for p in group)==pytest.approx(float(r['return_pct']))
    barsi=list(csv.DictReader((OUT/'b00s_initial_contributions.csv').open()))
    total=next(csv.DictReader((OUT/'b00s_initial_pct.csv').open()))
    assert len(barsi)==20
    assert math.fsum(float(p['contribution_pp']) for p in barsi)==pytest.approx(float(total['return_pct']))


def test_bh_ranking_does_not_duplicate_companies_or_use_late_quotes():
    rows=list(csv.DictReader((OUT/'bh_ranking_2014.csv').open()))
    assert len({r['cnpj'] for r in rows})==len(rows)
    assert all(r['on_quote_date']<=DATES[2014] for r in rows)
    chosen=[r for r in rows if r['selected']=='True']
    assert len(chosen)==8
    assert all(r['capital_received']<=DATES[2014] for r in chosen)
    assert all(r['class_price_method']=='CONTEMPORANEOUS_ON_PN_QUOTES' for r in chosen)


def test_owned_paths_replay_byte_identically_offline():
    names=['bh_selection_2014.csv','bh_ranking_2014.csv','bh_annual_pct.csv','bh_june_positions.csv','bh_event_ledger.csv','bh_owned_events.csv','bh_issuer_annual_pct.csv','b00s_initial_contributions.csv',
           'b00s_initial_pct.csv','b00s_initial_positions.csv','b00s_initial_events.csv','b00s_initial_event_ledger.csv','b00s_initial_sensitivity.csv']
    before={OUT/n:(OUT/n).read_bytes() for n in names}
    for script in ['stage1_bh_selection.py','stage1_buyhold.py','stage1_b00s_initial.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,check=True,capture_output=True)
    assert all(p.read_bytes()==data for p,data in before.items())
