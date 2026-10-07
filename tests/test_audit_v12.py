"""Economic failure cases and integrity checks for the separate v12 checkpoint."""
from dataclasses import asdict
import gzip
import json
import math
from pathlib import Path
import pytest
from scripts import audit_alerts_v12 as a
from scripts.audit_barsi_comparability_v12 import wealth_share, weighted_replacement


def fixture(amount=.4, kind='CASH_DIVIDEND'):
    book=a.m.bridge.PriceBook({'CPLE3':{'2025-04-24':10,'2025-04-25':10}},['2025-04-24','2025-04-25'])
    event=a.m.Event('old','2025-04-25','CASH','CPLE3','legacy',record_date='2025-04-24',amount=.3,note='DIV')
    alert=dict(ticker='CPLE3',date_com='2025-04-24',kind=kind,amount_or_multiplier=str(amount),source='B3',status='REVIEW',detail='')
    fact=dict(ticker='CPLE3',ex_date='2025-04-25',kind='DIV',amount=amount,source_id='notice',
              source_url='https://issuer.example/notice',source_sha256='verified',pay_date='2025-05-15')
    return book,event,alert,fact


def test_cash_dividend_alias_requires_replacement_of_correct_type():
    book,event,alert,fact=fixture()
    jcp=a.m.Event('jcp','2025-04-25','CASH','CPLE3','legacy',record_date='2025-04-24',amount=.15,note='JCP')
    row,change,_,_=a.classify(alert,1,[event,jcp],book,[fact],{})
    assert change['action']=='REPLACE'
    changed=a.amend([event,jcp],change)
    assert len(changed)==2
    assert next(e.amount for e in changed if e.event_id=='jcp')==.15
    result=a.m.safe_result(a.m.Engine(book,changed),'2025-04-24','2025-04-25','CPLE3')
    assert result['return']==pytest.approx(.055)  # .4 dividend + .15 JCP on 10
    assert event.amount==.3


def test_nearby_nominal_value_is_not_documentary_confirmation():
    book,event,alert,fact=fixture()
    fact['amount']+=1e-8
    row,change,_,_=a.classify(alert,1,[event],book,[fact],{})
    assert change['action']=='KEEP'
    assert row['documentary_status']=='CONCILIACAO_PARCIAL'


def test_no_gross_up_or_addition_from_ratio_alone():
    book,event,alert,fact=fixture(.255,'JCP')
    event=a.m.Event('old','2025-04-25','CASH','CPLE3','legacy',record_date='2025-04-24',amount=.3,note='JCP')
    row,change,_,_=a.classify(alert,1,[event],book,[],{})
    assert row['ratio_b3_to_same_kind']==pytest.approx(.85)
    assert change['action']=='KEEP'


def test_cemig_two_payment_total_is_never_duplicated():
    book,event,alert,_=fixture()
    event=a.m.Event('total','2025-04-25','CASH','CMIG3','legacy',record_date='2025-04-24',amount=.2,note='JCP; 2 parcelas')
    alert.update(ticker='CMIG3',kind='JCP',amount_or_multiplier='.1')
    row,change,_,_=a.classify(alert,1,[event],book,[],{})
    assert row['classification']=='MESMO_EVENTO_AGREGADO'
    assert a.amend([event],change)==[event]


def test_duplicate_addition_and_unknown_replacement_are_rejected():
    _,event,_,_=fixture()
    with pytest.raises(ValueError,match='Duplicate'):
        a.amend([event],dict(action='ADD',event=asdict(event)))
    with pytest.raises(ValueError,match='Ambiguous'):
        a.amend([event],dict(action='REPLACE',event=asdict(event),old_id='missing'))


def test_entitlement_uses_actual_position_not_merely_membership():
    book=a.m.bridge.PriceBook({'TGMA3':{'2025-06-30':10,'2025-07-01':11}},['2025-06-30','2025-07-01'])
    engine=a.m.Engine(book,[]);state=engine.initialize('2025-06-30',{'TGMA3':1})
    engine.advance(state,'2025-07-01')
    runner=a.Runner(book,[],{},[])
    states=[(2025,{'TGMA3':1},state)]
    assert runner.exposure(states,'TGMA3','2025-04-09')==[]
    assert runner.exposure(states,'TGMA3','2025-06-30')==[(2025,1000,1)]


def test_wealth_coverage_includes_cash_and_uses_wealth_not_name_count():
    rows=[dict(ticker='CASH_OUT',weight=.1,v9_return=3,alternative_return=''),
          dict(ticker='OTHER',weight=.9,v9_return=0,alternative_return=.2)]
    assert wealth_share(rows,lambda r:r['ticker']=='CASH_OUT')==pytest.approx(.4/1.3)
    assert weighted_replacement(rows)==pytest.approx(.48)


def test_original_sources_hash_the_uncompressed_original_bytes():
    for r in json.loads((a.INPUT/'sources_manifest.json').read_text()):
        if not r.get('sha256'):continue
        p=Path(r['stored_gzip'])
        assert a.sha(p)==r['stored_gzip_sha256']
        assert a.rowsha(r)!=r['sha256']
        import hashlib
        assert hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest()==r['sha256']


def test_v11_2_baseline_and_engine_are_immutable():
    for name,r in json.loads((a.BASE/'manifesto_arquivos.json').read_text()).items():
        assert a.sha(a.BASE/name)==r['sha256']
    assert a.sha('graham_v6_event_bridge/motor_eventos.py')=='56672b7810cb543bd1fdf4887c21811713e3c803229855ccf4a16b30c3051d11'


def test_checkpoint_accounts_for_all_alerts_and_no_exposure_has_zero_impact():
    rows=a.m.read_csv(a.OUT/'matriz_45_alertas_classificados.csv')
    assert len(rows)==45 and len({r['alert_id'] for r in rows})==45
    assert sum(r['decision']=='ADD' for r in rows)==9
    assert sum(r['decision']=='REPLACE' for r in rows)==3
    impacts=a.m.read_csv(a.OUT/'impacto_alertas_por_carteira.csv')
    assert len(impacts)==45*36
    for r in impacts:
        if r['exposure']=='False':
            assert float(r['accepted_delta_pp'])==0
            assert float(r['scenario_max_abs_pp'])==0


def test_joint_grendene_impact_is_recalculated_not_sum_of_isolated_shocks():
    row=next(r for r in a.m.read_csv(a.OUT/'impacto_conjunto_36_carteiras.csv') if
             (r['start_year'],r['rule'],r['mechanism'])==('2022','R00','maintain'))
    assert float(row['delta_pp'])>float(row['sum_isolated_deltas_pp'])+.04


def test_bbse_upper_sensitivity_substitutes_instead_of_double_counting():
    r=json.loads((a.OUT/'resumo_comparabilidade.json').read_text())
    ps=a.m.read_csv(a.OUT/'barsi_posicao_ano_1212.csv')
    p=next(p for p in ps if (p['year'],p['strategy'],p['scenario'],p['mechanism'],p['ticker'])==('2020','B00S','central','maintain','BBSE3'))
    expected=r['b00s_v9_high']+float(p['weight'])*(float(p['alternative_return'])-float(p['v9_cash_high']))
    assert r['b00s_high_with_bbse_replaced']==pytest.approx(expected)
    assert r['r16_minus_high_after_bbse_pp']==pytest.approx(.12660094385461562)


def test_barsi_dates_contributions_and_renewal_are_aligned():
    ps=a.m.read_csv(a.OUT/'barsi_posicao_ano_1212.csv')
    assert len(ps)==1212
    for r in ps:
        year=int(r['year']);start,end=a.m.bridge.WINDOWS[year]
        assert r['start']==start
        assert r['end']==(end if r['mechanism']=='annual' else a.m.END)
        if r['alternative_return']:
            assert float(r['weighted_difference_pp'])==pytest.approx(100*float(r['weight'])*(float(r['alternative_return'])-float(r['v9_return'])))
    annual=a.m.read_csv(a.OUT/'barsi_alternativas_96_anuais_manutencao.csv')
    for r in a.m.read_csv(a.OUT/'barsi_manutencao_renovacao_96.csv'):
        if r['mechanism']!='renew':continue
        factors=[1+float(x['partial_event_alternative']) for x in annual if x['mechanism']=='annual' and
                 x['strategy']==r['strategy'] and x['scenario']==r['scenario'] and int(x['year'])>=int(r['start_year'])]
        assert math.prod(factors)-1==pytest.approx(float(r['alternative_return']))


def test_all_twelve_records_retain_unknown_event_uncertainty():
    matrix=a.m.read_csv(a.OUT/'matriz_12_ativo_ano_atualizada.csv')
    assert len(matrix)==12
    assert all(r['fully_certified']=='False' for r in matrix)
    assert all(r['max_impact_unknown_events']=='NAO_LIMITADO_DOCUMENTALMENTE' for r in matrix)
    facts=a.m.read_csv(a.OUT/'fatos_12_confrontados.csv')
    assert sum(r['ticker']=='TGMA3' and r['status']=='PRESENTE_NO_BASELINE' for r in facts)==5
    assert sum(r['ticker']=='SBSP3' and r['status']=='PRESENTE_NO_BASELINE' for r in facts)==2


def test_barsi_position_sums_reproduce_both_frozen_v9_series():
    root=Path('research/graham_v6_comparison')
    for filename,mode,year_column in [('besst_v9_annual_frozen.csv','annual','year'),
                                      ('besst_v9_maintenance_frozen.csv','maintain','start_year')]:
        frozen={(r[year_column],r['strategy'],r['scenario']):float(r['return']) for r in a.m.read_csv(root/filename)}
        for r in a.m.read_csv(a.OUT/'barsi_alternativas_96_anuais_manutencao.csv'):
            if r['mechanism']==mode:
                assert float(r['baseline_v9'])==pytest.approx(frozen[r['year'],r['strategy'],r['scenario']],abs=1e-10)


def test_bbse_uses_nominal_official_column_and_excludes_post_cutoff():
    from bs4 import BeautifulSoup
    sources={r['id']:r for r in json.loads((a.INPUT/'sources_manifest.json').read_text())}
    source=sources['BBSE_RI']
    html=gzip.decompress(Path(source['stored_gzip']).read_bytes()).decode()
    factual=json.loads((a.INPUT/'verified_facts.json').read_text())
    lookup={r['ex_date']:r for r in factual if r['ticker']=='BBSE3'}
    from datetime import datetime
    matched=0
    for tr in BeautifulSoup(html,'html.parser').select('tr'):
        c=[td.get_text(' ',strip=True) for td in tr.select('td')]
        if len(c)!=9 or c[0] not in list(map(str,range(2020,2027))):continue
        ex=datetime.strptime(c[4],'%d/%m/%Y').date().isoformat()
        assert lookup[ex]['amount']==float(c[6].replace(',','.'))
        assert lookup[ex]['updated_amount']==float(c[7].replace(',','.'))
        if '2020-06-30'<ex<=a.m.END:matched+=1
    assert matched==12
    assert '2026-08-07' in lookup  # recorded, but ineligible before the June cutoff
