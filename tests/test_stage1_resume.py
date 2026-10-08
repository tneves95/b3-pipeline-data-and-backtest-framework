"""Continuity, ownership and deterministic incremental replay of the accepted prefix."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import stage1_resume as m
from stage1_continuation_audit import verify_frozen


def test_accepted_bh_ibov_and_initial_positions_are_immutable():
    verify_frozen()
    expected={'ibov_june_closes.csv':'21492f282eb19eec1f556c83963ced8a8b9cb1a5a84c9c8babd87f2c97d3664f',
              'conditional_legacy_segments_pct.csv':'32f5d2cd53de3ed7da92befe434cc5bc7a1124f49dc7fb56bfce87a69064820b'}
    for name,sha in expected.items():
        assert hashlib.sha256((ROOT/'research/returns_2014_2026_results'/name).read_bytes()).hexdigest()==sha


@pytest.mark.parametrize('portfolio,stem,start',[
    ('R03 B2','r03_continuation',2016),('B00S B2','b00s_b2_continuation',2015),
    ('B00S BH+entradas','b00s_bh_continuation',2015)])
def test_incremental_replay_and_independent_index_endpoint(portfolio,stem,start):
    paths=sorted(m.OUT.glob(stem+'_*.csv'));before={p:p.read_bytes() for p in paths}
    annual,positions,reviews,ledger=m.resume(portfolio,verbose=False)
    assert [r['year'] for r in annual]==list(range(start,2026))
    assert all(p.read_bytes()==data for p,data in before.items())
    for r in annual:
        initial=next(p['index_total'] for p in positions if p['date']==r['start'] and p['phase']=='BEFORE_REVIEW')
        end=sum(p['units']*p['nominal_close'] for p in positions if p['date']==r['end'] and p['phase']=='PERIOD_END')
        assert r['return_pct']==pytest.approx(100*(end/initial-1))
        assert r['cumulative_pct']==pytest.approx(100*(end-1))
    for year in range(start,2026):
        rs=[r for r in reviews if r['year']==year]
        assert sum(r['before'] for r in rs)==pytest.approx(sum(r['after'] for r in rs))
        survivors=[r for r in rs if r['before']>0 and r['after']>0]
        scales=[r['after']/r['before'] for r in survivors]
        assert max(scales)-min(scales)<1e-12
        assert all(r['status']=='FAIL' for r in rs if r['after']==0)
        if portfolio=='B00S BH+entradas':assert all(r['after']>0 for r in rs if r['before']>0)
    assert any(r['ticker']=='XPBR31' for r in positions) if portfolio!='R03 B2' else True
    verify_frozen()


def test_graham_inherits_the_accepted_2016_index_components():
    prior=m.read(m.OUT/'established_segment_positions.csv')
    now=m.read(m.OUT/'r03_continuation_positions.csv')
    a={m.canonical(r['ticker']):float(r['index_end']) for r in prior if r['year']=='2015'}
    b={r['ticker']:float(r['index_component']) for r in now if r['date']=='2016-06-30' and r['phase']=='BEFORE_REVIEW'}
    assert a==pytest.approx(b)
    assert sum(b.values())<.57


def test_same_day_right_is_owned_then_reinvested_without_external_funding():
    d='2026-05-20';q={('P',d):10,('R',d):2}
    events=[dict(id='right',ticker='P',kind='RIGHT',ex_date=d,successor='R',ratio=.5),
            dict(id='sell',ticker='R',kind='RIGHT_REINVEST',ex_date=d,successor='P')]
    assert m.event_day({'P':2},events,q,d)=={'P':2.2}


def test_conversion_distributes_per_old_share_and_retains_successor():
    d='2024-11-01'
    e=[dict(id='c',ticker='OLD',kind='CONVERSION',ex_date=d,legs=[['NEW',.6]],amount=1)]
    assert m.event_day({'OLD':2,'NEW':1},e,{('NEW',d):5},d)==pytest.approx({'NEW':2.6})


def test_compulsory_redemption_preserves_survivor_ratios():
    d='2026-05-15';q={('A',d):10,('B',d):20}
    e=[dict(id='r',ticker='OLD',kind='REDEMPTION',ex_date=d,amount=30)]
    a=m.event_day({'OLD':1,'A':2,'B':1},e,q,d)
    assert a==pytest.approx({'A':3.5,'B':1.75})
    assert sum(n*q[t,d] for t,n in a.items())==70


def test_all_failed_without_destination_is_not_silently_assumed_flat():
    with pytest.raises(ValueError):
        m.renew_b2({'A':1},{'A':'FAIL'}, {})


def test_lineage_is_not_failed_due_to_new_legal_shell_or_renamed_ticker():
    for y in range(2021,2025):
        status,_=m.selection('B00S',y)
        assert status['AESB3']==status['TIMS3']=='INDETERMINATE'
    assert m.selection('B00S',2025)[0]['TRPL4']=='INDETERMINATE'


def test_resolved_entries_and_undetermined_candidates_are_distinct():
    assert 'LINX3' in m.selection('R03',2016)[1]
    assert 'BBDC3' not in m.selection('R03',2016)[1]
    assert m.selection('R03',2018)[0]['CAML3']=='FAIL'
    assert m.selection('B00S',2018)[0]['IRBR3']=='INDETERMINATE'
    assert 'IRBR3' in m.selection('B00S',2019)[1]


def test_event_replay_is_stable_and_material_structures_not_double_counted():
    p=m.OUT/'cache/continuation_events.json.gz';before=p.read_bytes();m.freeze_events()
    assert p.read_bytes()==before
    events=m.gzread(p)
    def structures(t,d):return [e for e in events if e['ticker']==t and e['ex_date']==d and e['kind']=='SHARES']
    assert [e['factor'] for e in structures('GUAR3','2019-05-02')]==[8]
    assert [e['factor'] for e in structures('LIGT3','2021-06-28')]==[1]
    assert not structures('ELET3','2025-12-22')
    assert any(e['ticker']=='ELET3' and e['kind']=='SPINOFF' and e['successor']=='AXIA7' for e in events)
    assert [e['ex_date'] for e in events if e['ticker']=='ENBR3' and e['kind']=='REDEMPTION']==['2023-09-13']


def test_material_selection_sensitivity_is_not_hidden_as_an_error_bar():
    cases=m.read(m.OUT/'r03_selection_scenarios.csv')
    assert len(cases)==128 and len({r['case'] for r in cases})==128
    assert any(r['case']=='EVIDENCE_ONLY_BASE' and float(r['difference_from_base_pp'])==0 for r in cases)
    assert max(float(r['final_pct']) for r in cases)-min(float(r['final_pct']) for r in cases)>60


def test_rank_and_comparison_statistics_follow_published_annual_returns():
    out=ROOT/'research/returns_2014_2026_results';annual=m.read(out/'annual_returns_pct.csv')
    ranks=m.read(out/'annual_ranks.csv');stats=m.read(out/'consolidated_pct.csv')
    for s in stats:
        t=s['portfolio'];values=[float(r[t]) for r in annual]
        assert int(s['positive_years'])==sum(v>0 for v in values)
        if t!='IBOV':assert int(s['above_ibov_years'])==sum(float(r[t])>float(r['IBOV']) for r in annual)
        assert float(s['mean_rank'])==pytest.approx(sum(int(r[t]) for r in ranks)/12)
