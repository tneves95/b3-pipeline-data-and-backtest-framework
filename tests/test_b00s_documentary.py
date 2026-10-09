"""Documentary decisions: invariants independent of subsequent stock returns."""
import gzip
import hashlib
import itertools
import json
import statistics
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b00s_documentary as d
import b00s_variants as m
import b00s_fundamentals as f

def test_each_initial_company_has_six_effective_judgements():
    reviews=d.load_reviews()
    initial=[r for r in m.candidates() if r['year']==2014]
    assert {c for y,c in reviews if y==2014}=={r['cnpj'] for r in initial}
    for r in reviews.values():
        assert set(r['dimensions'])==set(d.DIMENSIONS)
        assert any(x['status']=='SATISFACTORY' for x in r['dimensions'].values())
        assert all(x['reason'] and x['contrary_evidence'] and x['evidence'] for x in r['dimensions'].values())
        assert all(x.get('missing') for x in r['dimensions'].values() if x['status']=='INDETERMINATE')
    names={r['ticker'] for r in reviews.values() if f.quality_gate(r['dimensions']).startswith('QUALIFIED')}
    assert {'PSSA3','TBLE3','BBDC4'}<=names
    # Every additional cutoff needs its own reviewed input, never a blanket reuse.
    reviewed={2014}|{int(p.stem[-4:]) for p in m.INPUT.glob('economic_reviews_[0-9][0-9][0-9][0-9].json')}
    assert all(y in reviewed for y,c in reviews)

def test_original_dates_and_hashes_are_enforced(tmp_path,monkeypatch):
    raw=b'%PDF-original-for-validation';name='sample.pdf.gz'
    (tmp_path/name).write_bytes(gzip.compress(raw,mtime=0))
    src=dict(docid='1',group=412,status='ARCHIVED',received='2014-05-01',url='https://source.invalid',original=name,
             original_sha256=hashlib.sha256(raw).hexdigest(),page_count=2)
    ref=dict(docid='1',group=412,pages=[1])
    record=dict(ticker='TEST',cnpj='1',years=[2014],cutoff='2014-06-30',
        valuation=dict(status='COMPARABLE',reason='Reviewed',evidence=[ref]),
        dimensions={k:dict(status='SATISFACTORY',reason='Reason',contrary_evidence='Risk',evidence=[ref]) for k in d.DIMENSIONS})
    (tmp_path/'economic_reviews.json').write_text(json.dumps([record]))
    manifest=tmp_path/'review_original_sources.json';manifest.write_text(json.dumps([src]));monkeypatch.setattr(d,'INPUT',tmp_path)
    assert d.load_reviews()
    manifest.write_text(json.dumps([dict(src,received='2014-07-01')]))
    with pytest.raises(ValueError,match='Future'):d.load_reviews()
    manifest.write_text(json.dumps([src]));(tmp_path/name).write_bytes(gzip.compress(b'changed',mtime=0))
    with pytest.raises(ValueError,match='Altered original'):d.load_reviews()

def test_interval_keeps_all_five_observations_and_no_fictitious_point():
    lower=[1,3,5,7,9];upper=[2,6,8,9,15];factor=[1,1.1,1.2,1.3,1.4]
    r=dict(ticker='X',valuation=dict(profit_bounds={str(y):dict(lower=a,upper=b) for y,a,b in zip(range(2009,2014),lower,upper)}))
    interval=d.profit_interval([100]*5,factor,2014,r)
    for corner in itertools.product(*zip(lower,upper)):
        val=statistics.median(n*k for n,k in zip(corner,factor))
        assert interval['lower']<=val<=interval['upper']
    r['valuation']['profit_bounds']['2009']['lower']=None
    r['valuation']['profit_bounds']['2010']['lower']=None
    assert d.profit_interval([100]*5,factor,2014,r)['lower']==6
    r['valuation']['profit_bounds']['2011']['lower']=None
    assert d.profit_interval([100]*5,factor,2014,r)['lower'] is None

def test_false_median_invariance_claim_is_rejected():
    review=dict(ticker='X',valuation=dict(median_invariance_bounds={'2011':[1,1000]}))
    with pytest.raises(ValueError,match='invariant median'):d.profit_interval([1,2,3,4,5],[1]*5,2014,review)

def test_material_adjustments_and_premium_requirements():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2014}
    porto=rows['PSSA3']
    assert porto['normalized_pe']==pytest.approx(14.168997093640053)
    assert porto['reported_normalized_profit']>porto['normalized_profit']
    assert next(e['value'] for e in porto['profit_evidence'] if e['metric']=='documentary_adjusted_attributable_ni')==703500000
    assert rows['TIMP3']['valuation_status']=='INDETERMINATE' and 15<rows['TIMP3']['normalized_pe']<=25
    assert rows['VIVT4']['valuation_status']=='INDETERMINATE'
    for ticker,maximum in [('BBDC4',14.942658406089615),('CSMG3',11.236070722426666)]:
        r=rows[ticker]
        assert r['valuation_status']=='PASS_MATURE'
        assert r['normalized_pe'] is None and r['normalized_profit'] is None
        assert r['normalized_pe_interval']['upper']==pytest.approx(maximum)
        assert r['normalized_pe_interval']['upper']<=15

def test_accepted_control_observations_and_all_pr3_files_are_unchanged():
    assert m.verify_accepted_controls()==11
    import subprocess
    old='8d394e9ab563daebe43603a3e85f35f43c1402bc'
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',old],cwd=m.ROOT,text=True).splitlines()
    assert len(names)==840
    changed=subprocess.check_output(['git','diff','--name-only',old,'--',*names],cwd=m.ROOT,text=True)
    assert not changed

def test_reviews_were_committed_before_portfolio_replay():
    import subprocess
    freeze=json.loads((m.INPUT/'decision_freeze_record.json').read_text())
    for filename,key in [('economic_reviews.json','economic_reviews_sha256'),('fundamental_decisions.json','decisions_sha256')]:
        path=m.INPUT/filename
        if filename=='economic_reviews.json':assert m.sha(path)==freeze[key]
        committed=subprocess.check_output(['git','show',freeze['decision_commit']+':'+str(path.relative_to(m.ROOT))],cwd=m.ROOT)
        assert hashlib.sha256(committed).hexdigest()==freeze[key]
    assert m.verify_accepted_initial()==10
    if m.reviewed_through()>2014:
        latest=m.verify_decision_freeze()
        for r in latest['files']:
            committed=subprocess.check_output(['git','show',latest['decision_commit']+':'+r['path']],cwd=m.ROOT)
            assert hashlib.sha256(committed).hexdigest()==r['sha256']
