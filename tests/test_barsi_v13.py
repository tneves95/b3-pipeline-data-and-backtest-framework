"""Directed event replay and economic failure cases; no database/network in CI."""
from collections import Counter
from dataclasses import replace
import gzip
import hashlib
import json
import math
from pathlib import Path

import pytest
from scripts import reconstruct_barsi_v13 as a
from scripts.analyze_barsi_graham_v13 import ranking, ranking_order
from motor_eventos import MissingData


@pytest.fixture(scope='module')
def event_fixture():
    data=json.loads(gzip.decompress((a.OUT/'nominal_event_prices.json.gz').read_bytes()))
    book=a.m.bridge.PriceBook(data['prices'],data['calendar'])
    return book,a.load_events()[0]


@pytest.mark.parametrize('row',a.m.read_csv(a.OUT/'ativos_calculados_v13.csv'),
                         ids=lambda r:r['ticker']+'_'+r['year']+'_'+r['mechanism'])
def test_replay_all_38_paths_without_sqlite(row,event_fixture):
    book,events=event_fixture
    result,state=a.simulate(book,events,row['ticker'],row['start'],row['end'])
    assert result['return']==pytest.approx(float(row['event_return']),abs=1e-11)
    assert result['cash']==pytest.approx(float(row['cash']),abs=1e-8)
    assert result['holdings']==pytest.approx(json.loads(row['final_holdings']))
    assert state.initial_value==10000


@pytest.mark.parametrize('ticker,successor,date,kind',[
    ('TIMP3','TIMS3','2020-10-13','MERGER'),
    ('VIVT4','VIVT3','2020-11-23','CONVERSION')])
def test_migration_consumes_predecessor_without_fake_price_or_cash(ticker,successor,date,kind):
    events=a.load_events()[0];event=next(e for e in events if e.asset==ticker and e.kind==kind)
    start='2020-10-09' if ticker=='TIMP3' else '2020-11-20'
    book=a.m.bridge.PriceBook({ticker:{start:10},successor:{date:12}},[start,date])
    result,state=a.simulate(book,[event],ticker,start,date)
    assert result['holdings']=={successor:1000}
    assert result['cash']==0 and result['return']==pytest.approx(.2)
    assert date not in book.prices[ticker]
    assert event.legs==[[successor,1.0]] or event.legs==((successor,1.0),)
    assert state.exposure_closed[0]['asset']==ticker
    with pytest.raises(MissingData):
        a.simulate(book,[],ticker,start,date)


def test_executed_factors_exclude_proposal_and_preserve_net_one():
    events=a.load_events()[0]
    quantity=[e for e in events if e.kind in ('SPLIT','BONUS')]
    assert [(e.asset,e.date,e.factor) for e in quantity]==[
        ('PSSA3','2021-10-21',2.0),('VIVT3','2025-04-15',2.0),('TIMS3','2025-07-03',1.0)]
    assert not any(e.asset=='PSSA3' and e.factor==3 for e in quantity)


def test_tim_distinct_equal_tranches_use_same_record_date_position():
    events=[e for e in a.load_events()[0] if e.asset=='TIMS3' and e.record_date=='2024-04-09']
    assert len(events)==3
    assert sorted(e.amount for e in events)==[.180146751,.180559931,.180559931]
    book=a.m.bridge.PriceBook({'TIMS3':{'2024-04-09':10,'2024-04-10':10}},['2024-04-09','2024-04-10'])
    result,_=a.simulate(book,events,'TIMS3','2024-04-09','2024-04-10')
    assert result['return']==pytest.approx(.0541266613)


def test_sapr_formation_date_entitlement_is_kept(event_fixture):
    book,events=event_fixture
    event=next(e for e in events if e.asset=='SAPR4' and e.record_date=='2020-06-30')
    _,state=a.simulate(book,events,'SAPR4','2020-06-30','2021-06-30')
    assert event.event_id in state.applied


def test_bounds_replace_the_own_old_contribution_and_no_double_count():
    row=dict(ticker='PSSA3',weight=.1,v9_return=1,v9_cash_low=.9,v9_cash_high=1.2,v13_return=1.5,alternative_return='')
    assert a.replacement(row,'v13_four','high')==1.5
    assert .1*(a.replacement(row,'v13_four','high')-a.replacement(row,'v9','high'))==pytest.approx(.03)
    # A v12 position must not receive a v13 delta; neither target family overlaps.
    old=dict(row,ticker='BBSE3',v13_return='',alternative_return=1.3)
    assert a.replacement(old,'v12_plus_v13','high')==1.3
    assert a.replacement(old,'v13_four','high')==1.2
    assert not (set(a.FAMILIES)&{'BBSE3','SBSP3','CSMG3','ENBR3'})


def test_every_renewal_chains_annual_capital_without_new_funds():
    annual=a.m.read_csv(a.OUT/'comparacao_anuais_manutencao_v13.csv')
    for row in a.m.read_csv(a.OUT/'comparacao_coortes_v13.csv'):
        if row['mechanism']!='renew':continue
        selected=[x for x in annual if x['mechanism']=='annual' and int(x['year'])>=int(row['start_year']) and
                  all(x[k]==row[k] for k in ['strategy','scenario','experiment'])]
        assert len(selected)==2026-int(row['start_year'])
        for field in ['central_return','low_return','high_return']:
            assert math.prod(1+float(x[field]) for x in selected)-1==pytest.approx(float(row[field]),abs=1e-11)
        assert float(row['final_value'])==pytest.approx(10000*(1+float(row['central_return'])))
        assert row['external_contributions']=='0'


def test_equal_results_share_rank_and_do_not_create_an_alphabetical_winner():
    values={'R16':2.6,'R03':2.6,'B00S':2.0}
    ranks=ranking(values)
    assert ranks=={'R16':1,'R03':1,'B00S':3}
    assert ranking_order(values,ranks)=='R03 = R16 > B00S'


def test_daily_risk_is_not_fabricated_from_sparse_events():
    assert a.daily_metrics([{'nav':100},{'nav':None},{'nav':120}])['volatility_252']==''
    daily=a.daily_metrics([{'nav':100},{'nav':90},{'nav':108}])
    assert daily['max_drawdown']==pytest.approx(-.1)
    rows=a.m.read_csv(a.OUT/'risco_diario_cobertura_v13.csv')
    for row in rows:
        if row['strategy'] in ['B00','B00S','B06','B06S']:
            assert row['volatility_252']==row['max_drawdown']==''


def test_sources_preserve_original_bytes_and_explicit_derived_excerpt_hashes():
    sources={r['id']:r for r in json.loads((a.INPUT/'sources_manifest.json').read_text())}
    for row in sources.values():
        p=Path(row['stored_gzip'])
        assert a.sha(p)==row['stored_gzip_sha256']
        expected=row.get('excerpt_sha256',row['sha256'])
        assert hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest()==expected
        if 'excerpt_sha256' in row:
            assert row['stored_content']=='DERIVED_PDF_PAGES_NOT_FULL_ORIGINAL'
            assert row['excerpt_original_pages_1_based']
    for fact in json.loads((a.INPUT/'cash_facts.json').read_text()):
        assert fact['source_sha256']==[sources[i]['sha256'] for i in fact['source_ids']]
        assert fact['isin']==a.ISINS[fact['ticker']]


def test_baselines_and_v12_complete_manifest_are_unchanged():
    baseline=json.loads((a.BASE/'manifesto_arquivos.json').read_text())
    assert len(baseline)==71
    for name,row in baseline.items():assert a.sha(a.BASE/name)==row['sha256']
    v12=json.loads((a.V12/'checkpoint_manifest.json').read_text())
    assert len(v12)==66
    for name,row in v12.items():assert a.sha(name)==row['sha256']
    assert a.sha('graham_v6_event_bridge/motor_eventos.py')=='56672b7810cb543bd1fdf4887c21811713e3c803229855ccf4a16b30c3051d11'


def test_v13_changes_only_the_216_declared_positions():
    old=a.m.read_csv(a.V12/'barsi_posicao_ano_1212.csv');new=a.m.read_csv(a.OUT/'alternativas_barsi_v13_por_posicao.csv')
    assert len(old)==len(new)==1212
    assert sum(r['v13_return']!='' for r in new)==216
    for before,after in zip(old,new):
        assert all(after[k]==v for k,v in before.items())
        if after['ticker'] not in a.FAMILIES:assert after['v13_return']==''


def test_v11_2_reexecution_and_cutoff_preserved():
    checks=a.m.read_csv(a.OUT/'regressao_economica_v11_2_36.csv')
    assert len(checks)==36
    assert all(abs(float(r['difference']))<1e-9 for r in checks)
    facts=json.loads((a.INPUT/'cash_facts.json').read_text())
    assert all('2020-06-30'<r['ex_date']<=a.m.END for r in facts)
    # A receivable after the horizon is a theoretical ex-date reinvestment,
    # explicitly retained as this study's convention, not actual paid cash.
    assert any(r['pay_date_or_deadline']>a.m.END and r['kind']=='CAPITAL_REDUCTION' for r in facts)
