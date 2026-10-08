"""PIT regressions and percentage-only index mechanics."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import stage1_select as select
import stage1_segments as segments
from stage1_pit import OUT,DATES,gzread

@pytest.fixture(scope='module')
def evidence():return select.Evidence()

def test_recovered_copel_is_available_only_after_real_receipt(evidence):
    rs=[r for r in evidence.facts if r['docid']=='35261' and r['metric']=='ni' and r['perimeter']=='con' and r['year']==2013]
    assert len(rs)==1
    assert rs[0]['received']=='2014-03-17'
    assert rs[0]['value']==1101435
    idx,_,_=evidence.asof(2014)
    assert select.val(idx,'76483817000120',2013,'ni')==1101435
    assert select.metric(idx,'76483817000120',2013,'ni')['docid']=='35261'

def test_bank_account_code_is_not_mistaken_for_current_assets(evidence):
    idx,_,_=evidence.asof(2020)
    # Bradesco's consolidated IFRS 1.01 is cash, not current assets.
    assert select.val(idx,'60746948000112',2019,'ca','con') is None
    assert select.val(idx,'60746948000112',2019,'ca','ind')==572182438

def test_empty_ifrs_comparative_does_not_overwrite_reported_profit(evidence):
    idx,_,_=evidence.asof(2014)
    assert select.val(idx,'60872504000123',2009,'ni','con') is None
    assert select.val(idx,'60872504000123',2009,'ni')==7706907
    # The 2009 third column of Sao Martinho is blank, not a proven loss.
    assert select.val(idx,'51466860000156',2009,'ni') is None

def test_capital_authorization_and_receipt_are_both_before_cutoff(evidence):
    for y in [2014,2015,2016]:
        _,_,caps=evidence.asof(y)
        assert caps
        assert all(r['received']<=DATES[y] and r['approved']<=DATES[y] for r in caps.values())
        assert all(r.get('capital_type')!='Capital Autorizado' for r in caps.values())

def test_strict_besst_excludes_insurance_brokers_and_gas():
    assert select.classify('Emp. Adm. Part. - Seguradoras e Corretoras','Corretagem de seguros','Wiz')[0] is None
    assert select.classify('Saneamento, Serv. Água e Gás','Distribuição de gás canalizado','Comgás')[0] is None
    assert select.classify('Saneamento, Serv. Água e Gás','Abastecimento de água e esgoto','Sabesp')[0]=='Saneamento'
    assert select.classify('Comércio (Atacado e Varejo)','Comércio de produtos farmacêuticos','Raia Drogasil')[1]=='Saúde'

def test_known_failure_is_not_masked_by_a_different_missing_year():
    rows=list(csv.DictReader((OUT/'screening.csv').open()))
    r=next(r for r in rows if r['year']=='2014' and r['strategy']=='R03' and r['ticker']=='BPHA3')
    assert r['missing_earnings']=='2009'
    assert r['F3']=='False' and r['status']=='FAIL' # published 2013 loss

def test_incomplete_earnings_are_not_silently_failed():
    rows=list(csv.DictReader((OUT/'screening.csv').open()))
    r=next(r for r in rows if r['year']=='2016' and r['strategy']=='R03' and r['ticker']=='LINX3')
    assert r['status']=='INDETERMINATE' and r['missing_earnings']=='2009'

def test_established_weights_obey_equal_names_or_equal_sectors():
    rows=list(csv.DictReader((OUT/'established_selections.csv').open()))
    for y,s in {(r['year'],r['strategy']) for r in rows}:
        group=[r for r in rows if (r['year'],r['strategy'])==(y,s)]
        assert sum(float(r['weight']) for r in group)==pytest.approx(1)
        if s=='R03':assert all(float(r['weight'])==pytest.approx(1/len(group)) for r in group)
        else:
            sectors={r['sector'] for r in group}
            for sector in sectors:
                assert sum(float(r['weight']) for r in group if r['sector']==sector)==pytest.approx(1/len(sectors))

def test_distribution_reinvests_on_ex_close_without_double_counting():
    p={'2014-06-30':100.,'2014-07-01':90.,'2015-06-30':99.}
    e=[dict(id='a',ex_date='2014-07-01',kind='DISTRIBUTION',amount=10.)]
    assert segments.gross_factor(p,e,'2014-06-30','2015-06-30')==pytest.approx(1.1)

def test_simultaneous_distribution_and_split_use_original_entitlement():
    p={'a':100.,'b':45.,'c':45.}
    e=[dict(id='a',ex_date='b',kind='DISTRIBUTION',amount=10.),dict(id='b',ex_date='b',kind='SHARES',factor=2.)]
    assert segments.gross_factor(p,e,'a','c')==pytest.approx(1.)

def test_missing_exact_quote_cannot_be_replaced_by_stale_price():
    with pytest.raises(ValueError,match='ex-date'):
        segments.gross_factor({'a':100.,'c':110.},[dict(id='a',ex_date='b',kind='DISTRIBUTION',amount=10.)],'a','c')

def test_duplicate_event_is_rejected():
    e=dict(id='same',ex_date='b',kind='DISTRIBUTION',amount=1.)
    with pytest.raises(ValueError,match='Duplicate'):
        segments.gross_factor({'a':100.,'b':99.},[e,e],'a','b')

def test_formation_ex_dividend_is_not_earned_twice():
    e=dict(id='already_ex',ex_date='a',kind='DISTRIBUTION',amount=10.)
    assert segments.gross_factor({'a':90.,'b':99.},[e],'a','b')==pytest.approx(1.1)

def test_original_extracts_match_archived_hashes():
    for p in (OUT/'originals').glob('dfp*.json'):
        m=json.loads(p.read_text())
        assert hashlib.sha256(p.with_suffix('.zip').read_bytes()).hexdigest()==m['extract_sha256']

def test_segment_replay_and_ibov_are_unchanged():
    paths=[OUT/'established_segments_pct.csv',OUT/'established_segment_positions.csv',ROOT/'research/returns_2014_2026_results/ibov_june_closes.csv']
    before={p:p.read_bytes() for p in paths}
    subprocess.run([sys.executable,str(ROOT/'scripts/stage1_segments.py')],cwd=ROOT,check=True,capture_output=True)
    assert all(p.read_bytes()==v for p,v in before.items())

def test_selected_fact_provenance_is_before_each_formation():
    traces=gzread(OUT/'established_selection_evidence.json.gz')
    assert len(traces)==71
    for r in traces:
        assert r['capital'] is None or r['capital']['received']<=r['date']
        assert all(f['received']<=r['date'] and f['period_end']<=r['date'] for f in r['facts'])
        assert r['market']['sector_received']<=r['date']

def test_all_boundary_and_reinvestment_quotes_match_raw_cotahist():
    rows=list(csv.DictReader((OUT/'segment_quote_validation.csv').open()))
    assert len(rows)==54
    assert all(r['status']=='MATCH' and float(r['sqlite_close'])==float(r['close']) for r in rows)
    assert all(len(r['record_sha256'])==64 for r in rows)
