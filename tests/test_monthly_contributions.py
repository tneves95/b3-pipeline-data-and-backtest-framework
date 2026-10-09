import json
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from monthly_contributions import waterfill, june_targets, xirr, frozen_compositions, coverage
from monthly_inputs import STUDY, START, END
from b00s_variants import read, sha


def test_two_assets_monthly_deficits_buy_loser_without_sale():
    values={'A':75000.,'B':25000.}
    buys,cash=waterfill(values,2500.,set(values))
    assert buys=={'B':2500.} and cash==0
    assert values=={'A':75000.,'B':25000.}


def test_proportional_deficits_and_unbuyable_cash():
    buys,cash=waterfill({'A':60.,'B':20.,'C':20.},10.,{'B','C'})
    assert buys=={'B':5.,'C':5.} and cash==0
    assert waterfill({'A':60.,'B':20.},10.,{'A'})==({},10.)


def test_third_issuer_requires_full_equal_june_review():
    targets,protected=june_targets({'A':75.,'B':25.},{'A','B','C'},{'A':.2,'B':-.1},True)
    assert targets==dict.fromkeys(['A','B','C'],100/3) and not protected


def test_no_constituent_change_does_not_reset_weights():
    values={'A':75.,'B':25.}
    assert june_targets(values,set(values),{},False)==(values,set())


@pytest.mark.parametrize('winner_weight,expected',[(.09,.09),(.12,.10)])
def test_twenty_issuer_winner_preservation_on_entry(winner_weight,expected):
    values={'A':winner_weight,**{f'B{i}':(1-winner_weight)/18 for i in range(18)}}
    wanted=set(values)|{'NEW'}
    targets,protected=june_targets(values,wanted,{'A':.20,**{k:0 for k in values if k!='A'}},True)
    assert protected=={'A'}
    assert targets['A']==pytest.approx(expected)
    assert sum(targets.values())==pytest.approx(1.)
    assert max(targets.values())<=.10+1e-14


def test_twenty_issuer_no_change_only_sells_excess_above_two_times():
    values={'A':.12,**{f'B{i}':.88/19 for i in range(19)}}
    targets,_=june_targets(values,set(values),{},False)
    assert targets['A']==pytest.approx(.10)
    assert sum(targets.values())==pytest.approx(1.)
    assert all(targets[c]>=values[c] for c in values if c!='A')


def test_sixteen_to_fifteen_disables_winner_exception():
    values={'A':.20,**{f'B{i}':.8/15 for i in range(15)}}
    wanted=set(values)-{'B14'}
    targets,protected=june_targets(values,wanted,dict.fromkeys(values,.2),True)
    assert not protected and all(v==pytest.approx(1/15) for v in targets.values())


def test_xirr_uses_actual_dates_and_cash_flows():
    assert xirr([('2020-01-01',-100),('2020-12-31',110)])==pytest.approx(.1)
    assert xirr([('2020-01-01',-100),('2020-07-01',-50),('2020-12-31',150)])==pytest.approx(0,abs=1e-12)


def test_calendar_is_144_first_sessions_with_same_460k_external_capital():
    c=read(STUDY/'contribution_calendar.csv');ibov={r['date'] for r in read(STUDY/'inputs/ibov_daily.csv')}
    assert len(c)==144 and len({r['month'] for r in c})==144
    assert c[0]['month']=='2014-07' and c[-1]['month']=='2026-06'
    assert 100000+sum(float(r['amount']) for r in c)==460000
    assert all(r['date']==min(d for d in ibov if d.startswith(r['month'])) for r in c)
    assert all(START<r['date']<=r['month_end']<=END for r in c)


def test_frozen_bh_and_no_duplicate_classes_or_spinoff_target():
    c=frozen_compositions()
    assert set(c['BH padrão',2014].values())==set('CCRO3 WEGE3 ITUB4 BBDC4 TBLE3 CMIG4 HYPE3 RADL3'.split())
    assert len(c['BESST-10 BH',2014])==10
    assert all('XPBR31' not in v.values() for v in c.values())
    assert all(c['BH padrão',y]==c['BH padrão',2014] for y in range(2015,2026))


def test_ranking_is_sector_capitalization_whole_universe_not_b00s_pass():
    rows=read(STUDY/'besst10_bh_ranking_2014.csv');selected=read(STUDY/'besst10_bh_selection_2014.csv')
    assert len(rows)>60 and len({r['cnpj'] for r in rows})==len(rows)
    assert all(r['sector_received']<=START and r['capital_received']<=START for r in rows)
    assert all(r['exact_class_prices']=='True' for r in selected)
    assert all(sum(x['sector']==r['sector'] for x in selected)==2 for r in selected)
    assert {'SULA11','RNEW11','ALUP11','TAEE11','NETC4','OIBR4'}<=set(r['ticker'] for r in rows)
    assert any(r['ticker']=='BBSE3' for r in selected)
    assert 'BBSE3' not in frozen_compositions()['V0',2014].values()


def test_ranking_freeze_bytes_unchanged():
    freeze=json.loads((STUDY/'inputs/ranking_freeze.json').read_text())
    root=STUDY.parents[1]
    assert freeze['returns_accessed'] is False
    for r in freeze['files']:assert sha(root/r['path'])==r['sha256']


def test_coverage_reports_missing_actual_price_instead_of_filling():
    checks=read(STUDY/'quote_coverage.csv')
    missing=[r for r in checks if r['status']=='MISSING_EXACT_CLOSE']
    assert missing and all(r['close']=='' for r in missing)
    assert any(r['ticker']=='ABCB2' and r['date']=='2014-07-01' for r in missing)
    assert all(r['ticker'] in ['ABCB2','ENBR3'] for r in missing)


def test_spinoff_does_not_create_new_buy_target_or_duplicate_entitlement():
    from monthly_contributions import process_events
    es=[dict(id='S',ticker='A',ex_date='2014-07-01',kind='SPINOFF',successor='X',ratio=.2,source='synthetic'),
        dict(id='D',ticker='A',ex_date='2014-07-01',kind='DISTRIBUTION',amount=1.,source='synthetic'),
        dict(id='B',ticker='A',ex_date='2014-07-01',kind='SHARES',factor=2.,source='synthetic')]
    book,buyers,principal,ledger=process_events({'origin':{'A':10.}},{'origin':'A'},{('A','2014-07-01'):5.},es,'2014-07-01')
    assert book=={'origin':{'A':22.,'X':2.}}
    assert buyers=={'origin':'A'} and principal==0
    assert len(ledger)==2 and all(r['external_flow']==0 for r in ledger)


def test_compulsory_redemption_uses_actual_units_and_internal_cash():
    from monthly_contributions import process_events
    e=dict(id='R',ticker='A',ex_date='2014-07-01',kind='REDEMPTION',amount=12.,source='synthetic')
    book,buyers,principal,ledger=process_events({'a':{'A':10.},'b':{'B':3.}},{'a':'A','b':'B'},{},[e],e['ex_date'])
    assert principal==120 and book['a']=={} and buyers=={'b':'B'}
    assert ledger[0]['external_flow']==0


def test_missing_price_keeps_contribution_cash_and_does_not_invent_mark():
    from monthly_contributions import simulate
    q={('A',START):100.,('B',START):100.,('A','2014-07-01'):110.,
       ('A','2014-07-31'):120.,('B','2014-07-31'):90.}
    r=simulate('V0',q,{}, {('V0',2014):{'a':'A','b':'B'}},end='2014-07-31')
    assert all(t['reason']=='INITIAL_EQUAL_ALLOCATION' for t in r['trades']) and r['summary']['cash']==2500
    assert r['summary']['final_wealth']==107500
    assert r['summary']['twr_pct'] is None
    assert r['contributions'][0]['nav_before'] is None


def test_twr_links_before_and_after_external_flow():
    from monthly_contributions import simulate
    q={('A',START):100.,('B',START):100.,('A','2014-07-01'):110.,('B','2014-07-01'):90.,
       ('A','2014-07-31'):121.,('B','2014-07-31'):81.}
    r=simulate('V0',q,{}, {('V0',2014):{'a':'A','b':'B'}},end='2014-07-31')
    assert r['summary']['final_wealth']==pytest.approx(103250.)
    assert r['summary']['twr_pct']==pytest.approx(100*(103250/102500-1))
    monthly=[t for t in r['trades'] if t['reason']=='MONTHLY_DEFICIT_BUY']
    assert len(monthly)==1 and monthly[0]['ticker']=='B'


def test_zero_contributions_same_equal_weight_bh_reproduces_existing_engine():
    from monthly_contributions import simulate,load_quotes,events
    from stage1_buyhold import trajectory,quotes,INITIAL
    from stage1_pit import DATES,OUT,gzread
    q,_=load_quotes();r=simulate('BH padrão',q,events(),frozen_compositions(),monthly=0)
    accepted,_=trajectory(quotes(),gzread(OUT/'cache/bh_owned_events.json.gz'),dict.fromkeys(INITIAL,1/8),list(DATES.values()))
    for d in DATES.values():
        expected=sum(x['index_component'] for x in accepted if x['date']==d)*100000
        actual=next(w['nav'] for w in r['wealth'] if w['date']==d and w['phase'] in ['INITIAL','MONTH_END'])
        assert actual==pytest.approx(expected,rel=3e-12)
    assert r['summary']['external_capital']==100000
    assert all(t['reason']=='INITIAL_EQUAL_ALLOCATION' for t in r['trades'])


def test_full_simulation_trades_and_external_flows_reconcile():
    from monthly_contributions import simulate,load_quotes,events
    q,_=load_quotes();r=simulate('V0',q,events(),frozen_compositions(),end='2016-06-30')
    assert len(r['contributions'])==24
    assert sum(x['external_deposit'] for x in r['contributions'])==60000
    assert r['summary']['external_capital']==160000
    assert all(t['date'][5:7]=='06' for t in r['trades'] if t['side']=='SELL')
    assert all(p['units']>=0 for p in r['positions'])
    assert all(w['cash']>=0 for w in r['wealth'])


def test_ibov_gets_the_same_exact_144_dated_contributions():
    from monthly_contributions import benchmark
    b=benchmark();c=read(STUDY/'contribution_calendar.csv')
    assert [r['date'] for r in b['contributions']]==[r['date'] for r in c]
    assert b['summary']['external_capital']==460000
    assert sum(r['external_deposit'] for r in b['contributions'])==360000


def test_accepted_shared_events_are_not_changed_or_processed_twice():
    from collections import Counter
    from monthly_contributions import events
    from b00s_variants import market
    from stage1_pit import OUT,gzread
    fields=lambda e:(e['ticker'],e['ex_date'],e['kind'],e.get('amount'),e.get('factor'),e.get('ratio'),e.get('successor'))
    _,old=market();bh=gzread(OUT/'cache/bh_owned_events.json.gz');names={e['ticker'] for e in bh}
    a=Counter(fields(e) for ds in old.values() for e in ds if e['ticker'] in names)
    b=Counter(fields(e) for e in bh)
    assert not (a-b)
    current=[e for ds in events().values() for e in ds]
    assert len({e['id'] for e in current})==len(current)
    assert all(Counter(fields(e) for e in current)[k]==v for k,v in b.items())
