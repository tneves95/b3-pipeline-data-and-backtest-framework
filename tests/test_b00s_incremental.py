"""Incremental PIT evidence and preservation independent of realized returns."""
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b00s_variants as m
from b00s_fundamentals import Fundamentals, valuation_gate
from b00s_documentary import load_reviews
from b00s_incremental import calculate_metrics

def test_reusing_a_dossier_does_not_reuse_annual_valuation_or_metric_proofs():
    from b00s_documentary import expand_incremental, DIMENSIONS
    previous=next(r for r in json.loads((m.INPUT/'economic_reviews_2015.json').read_text()) if r['ticker']=='TIMP3')
    saved=copy.deepcopy(previous)
    update=dict(reuse_previous=True,prior_assessment='2015:'+previous['cnpj'],years=[2016],cutoff='2016-06-30',
        cnpj=previous['cnpj'],ticker='TIMP3',valuation=dict(status='INDETERMINATE',reason='Review new tower sale and lease commitments',evidence=[]),
        incremental_review=dict(reason='Reviewed annual changes',evidence=[]),
        confirmed_dimensions={k:'Explicit unchanged-dimension finding' for k in DIMENSIONS})
    result=expand_incremental(update,previous)
    assert result['valuation']['status']=='INDETERMINATE'
    assert 'economic_metrics' not in result
    assert previous==saved
    assert result['dimensions']['capital_economics']['status']=='INDETERMINATE'
    del update['confirmed_dimensions']['governance']
    with pytest.raises(ValueError,match='Six explicit'):expand_incremental(update,previous)

def test_accepted_initial_documents_decisions_and_results_are_exact():
    assert m.verify_accepted_initial()==10
    assert m.verify_completed_batches()>=1

def test_actual_incremental_review_covers_each_2015_candidate():
    reviews=load_reviews();new={r['ticker']:r for (y,c),r in reviews.items() if y==2015}
    assert set(new)=={r['ticker'] for r in m.candidates() if r['year']==2015}
    for t,r in new.items():
        assert r['prior_assessment']=='2014:'+r['cnpj']
        assert r['incremental_review']['reason'] and r['incremental_review']['evidence']
        for d in r['dimensions'].values():
            assert d['prior_year']==2014 and d['review_2015']
    assert new['SBSP3']['dimensions']['financial_resilience']['status']=='INDETERMINATE'
    assert new['GETI4']['dimensions']['financial_resilience']['status']=='INDETERMINATE'
    assert any(all(d['status']=='SATISFACTORY' for d in r['dimensions'].values()) for r in new.values())

def test_proven_necessary_failure_is_not_erased_by_another_unknown():
    assert valuation_gate(20,{'real_eps_cagr':.029,'average_payout':None})=='REJECTED_REINVESTMENT'
    assert valuation_gate(20,{'real_eps_cagr':.06,'average_payout':None})=='INDETERMINATE'
    assert valuation_gate(15,{'real_eps_cagr':.029})=='PASS_MATURE'
    assert valuation_gate(20,dict(real_eps_cagr=.06,average_payout=.7,return_on_capital_median=.16,inflation_reference=.08,solidity_proven=True))=='PASS_REINVESTOR'

def test_eps_deflation_and_roic_include_actual_capital_not_roe():
    proof=dict(real_eps=dict(first=dict(year=2010,profit=100,weighted_shares=10),last=dict(year=2014,profit=200,weighted_shares=20)),
        roic=dict(annual_inputs=[dict(year=y,equity=100,interest_debt=50,cash_and_short_investments=10,ebit=20,pretax_income=16,income_tax_expense=4) for y in range(2011,2015)]))
    result=calculate_metrics(proof,{(2010,12):1,(2014,12):1.2})
    # Doubled aggregate earnings with doubled shares are zero nominal EPS growth.
    assert result['real_eps_cagr']==pytest.approx((1/1.2)**.25-1)
    assert result['return_on_capital_median']==pytest.approx(15/140)
    proof['real_eps']['last']['year']=2015
    with pytest.raises(ValueError,match='four EPS'):calculate_metrics(proof,{})

def test_subscribed_capital_requires_each_preferred_class_own_price():
    f=Fundamentals.__new__(Fundamentals);c='issuer';doc='1'
    f.fre={c:[dict(docid=doc,part='capital_social',raw=dict(ID_Capital_Social='A',Tipo_Capital='Capital Subscrito',Data_Autorizacao_Aprovacao='2014-01-01')),
        *[dict(docid=doc,part='capital_social_classe_acao',raw=dict(ID_Capital_Social='A',Tipo_Classe_Acao_Preferencial=k,Quantidade_Acoes=str(v))) for k,v in [('Preferencial Classe A',2),('Preferencial Classe B',8)]]]}
    f.identities=[dict(cnpj=c,year='2015',ticker=t,close=p,isin_code=t) for t,p in [('TEST3',10),('TEST6',12)]]
    f.base=SimpleNamespace(market={'actions':[]})
    cap=dict(docid=doc,on=10,pn=10,approved='2014-01-01',received='2015-05-01',capital_type='Capital Subscrito')
    value,classes,missing=f.capital(c,2015,cap)
    assert value is None and 'UNQUOTED_OR_UNRECONCILED_SHARE_CLASS' in missing
    assert next(r for r in classes if r['share_class']=='Preferencial Classe A')['price'] is None
    f.identities.append(dict(cnpj=c,year='2015',ticker='TEST5',close=11,isin_code='TEST5'))
    assert f.capital(c,2015,cap)[0]==218

def test_premium_failures_have_documented_numbers_and_no_future_assumption():
    facts={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2015}
    assert facts['PSSA3']['real_eps_cagr'] is None
    assert facts['PSSA3']['return_on_capital_median']==pytest.approx(.13977147329305792)
    robustness=facts['PSSA3']['documentary_assessment']['economic_metrics']['roe_robustness']
    assert robustness['roe_2012_upper_from_rounded_disclosure']<robustness['required_nominal_return']
    assert robustness['roe_2013_upper_from_rounded_adjusted_disclosure']<robustness['required_nominal_return']
    assert facts['TIMP3']['return_on_capital_median']==pytest.approx(.11518797409334317)
    for t in ['PSSA3','TIMP3']:
        r=facts[t]
        assert 15<r['normalized_pe']<=25
        assert r['valuation_status']=='REJECTED_REINVESTMENT'
        assert all(e['received']<='2015-06-30' for e in r['documentary_assessment']['economic_metrics']['evidence'])
    assert facts['ITUB4']['valuation_status']=='PASS_MATURE'
    assert facts['ITUB4']['market_cap'] is None
    assert facts['ITUB4']['normalized_pe'] is None
    assert facts['ITUB4']['normalized_pe_interval']['upper']<15
    assert facts['BRSR6']['market_cap'] is None

def test_tim_roic_reconciles_to_dated_statements_and_lease_debt():
    from stage1_pit import gzread
    review=next(r for (year,c),r in load_reviews().items() if year==2015 and r['ticker']=='TIMP3')
    proof=review['economic_metrics'];facts=gzread(m.INPUT/'cvm_directed_extract.json.gz')['facts']
    for row,source in zip(proof['roic']['annual_inputs'],proof['statement_sources']):
        actual={}
        for fact in source['records']:
            assert fact in facts
            assert fact['received']<=review['cutoff'] and fact['perimeter']=='con'
            assert fact['year']==row['year']
            actual[fact['statement']+fact['account']]=fact['value']*(1000 if fact['scale']=='MIL' else 1)
        assert row['ebit']==actual['DRE3.05']
        assert row['pretax_income']==actual['DRE3.07']
        assert row['income_tax_expense']==-actual['DRE3.08']
        assert row['equity']==actual['BPP2.03']
        assert row['cash_and_short_investments']==actual['BPA1.01.01']+actual['BPA1.01.02']
        assert row['interest_debt']==actual['BPP2.01.04']+actual['BPP2.02.01']+row['lease_included']

def test_bbas_bound_deducts_both_ownership_changes_and_cutoff_financing():
    import hashlib
    review=json.loads((m.ROOT/'docs/reviews/adversarial_2015.json').read_text())
    bank=next(r for r in review['company_reviews'] if r['ticker']=='BBAS3')
    bridge=bank['cateno']['resolved_bridge'];debt=bridge['financing'];proof=bank['numerical_proof']
    source=debt['reference_source']
    assert hashlib.sha256((m.INPUT/source['path']).read_bytes()).hexdigest()==source['sha256']
    rate=(1+debt['daily_CDI_percent']/100*1.11)**252-1
    cost=bridge['amortization_deduction']+bridge['fees_rounded_up']+debt['new_principal']*.2876*rate
    assert bridge['amortization_deduction']==pytest.approx(386000000*.5014)
    for year in ['2011','2013','2014']:
        old=bank['historical_profit_bounds_NOT_current_perimeter'][year]['lower']
        insurance=bank['bbse_ownership_bridge'][year].get('conservative_deduction',0)
        gross_cards=bridge['historical_gross_card_receipts'][year]
        expected=(old-insurance-.5*gross_cards)*proof['ipca_factors_from_fy_end'][year]-cost
        assert proof['annual_real_lower_bounds_after_all_bridge_costs'][year]==pytest.approx(expected)
        nominal=bank['valuation_proposal']['profit_bounds'][year]['lower']
        assert nominal*proof['ipca_factors_from_fy_end'][year]==pytest.approx(expected)
    assert proof['pe_upper']<15
    assert proof['separate_stress_with_100pct_amortization']['pe_upper']>15
    current=next(r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2015 and r['ticker']=='BBAS3')
    assert current['normalized_profit'] is None
    assert current['normalized_pe_interval']['upper']==pytest.approx(proof['pe_upper'])

def test_2016_review_resolves_admission_and_keeps_current_material_changes():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2016}
    assert set(rows)=={r['ticker'] for r in m.candidates() if r['year']==2016}
    for r in rows.values():
        a=r['documentary_assessment']
        assert a['prior_assessment']=='2015:'+r['cnpj']
        assert all(d['prior_year']==2015 and d['review_2016'] for d in a['dimensions'].values())
        assert all(e['received']<=r['cutoff'] for e in a['incremental_review']['evidence'])
    bank=rows['BRSR6']
    assert bank['valuation_status']=='PASS_MATURE'
    assert bank['market_cap']==pytest.approx(205052205*9.52+3519541*11.50+200402731*8.54)
    assert bank['normalized_pe_interval']['upper']==pytest.approx(11.839179995594288)
    assert rows['ITUB4']['valuation_status']=='INDETERMINATE'
    assert rows['ITUB4']['quality_category']=='QUALIFIED_SATISFACTORY'
    assert rows['BBDC4']['documentary_assessment']['dimensions']['governance']['status']=='INDETERMINATE'
    assert rows['BBDC4']['base_status']=='PASS'
    assert rows['EQTL3']['documentary_assessment']['dimensions']['financial_resilience']['status']=='SATISFACTORY'
    for ticker in ['PSSA3','TBLE3']:
        assert rows[ticker]['valuation_status']=='PASS_MATURE'
        assert rows[ticker]['normalized_pe'] is None
        assert rows[ticker]['normalized_pe_interval']['upper']<=15
    assert 'economic_metrics' not in rows['TIMP3']['documentary_assessment']
    assert rows['TIMP3']['valuation_status']=='INDETERMINATE'
    assert any(e['docid']=='tim_fourth_tranche_sec_20160610' for e in rows['TIMP3']['documentary_assessment']['valuation']['evidence'])

def test_downloaded_originals_match_delivery_version_and_embedded_pdf():
    import base64,gzip,hashlib,io,zipfile
    import xml.etree.ElementTree as ET
    rows=json.loads((m.INPUT/'review_original_sources.json').read_text())
    downloaded=[r for r in rows if 'submission' in r]
    assert {r['docid'] for r in downloaded}>={'53196','54003'}
    for r in downloaded:
        s=r['submission'];raw=gzip.decompress((m.INPUT/s['path']).read_bytes())
        meta=gzip.decompress((m.INPUT/s['metadata']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==s['sha256']
        assert hashlib.sha256(meta).hexdigest()==s['metadata_sha256']
        root=ET.fromstring(meta)
        assert root.findtext('.//NumeroSequencialDocumento')==r['docid']
        assert root.findtext('.//DataEntrega')[:10]==r['received']<=r['cutoff']
        assert root.findtext('.//NumeroVersaoDocumento')==s['version']
        inner=zipfile.ZipFile(io.BytesIO(raw))
        version=ET.fromstring(inner.read('FormularioDemonstracaoFinanceiraDFP.xml'))
        assert version.findtext('.//NumeroVersaoDocumento')==s['version']
        assert version.findtext('.//DataReferenciaDocumento')==s['reference']
        notes=ET.fromstring(inner.read('AnexoDocumento.xml'))
        node=next(n for n in notes if int(n.findtext('NumeroGrupoRelacionado','0'))==r['group'])
        original=base64.b64decode(node.findtext('ImagemObjetoArquivoPdf'),validate=True)
        assert hashlib.sha256(original).hexdigest()==r['original_sha256']
        assert original==gzip.decompress((m.INPUT/r['original']).read_bytes())

def test_2016_bbas_updated_financing_and_five_year_median_reconcile():
    import hashlib,statistics
    review=json.loads((m.ROOT/'docs/reviews/adversarial_2016.json').read_text())
    bank=next(r for r in review['company_reviews'] if r['ticker']=='BBAS3')
    proof=bank['numerical_proof'];real=[]
    for year in proof['fiscal_years']:
        b=bank['valuation_proposal']['profit_bounds'][year]
        if b['lower'] is None:real.append(float('-inf'));continue
        c=bank['bridge_components'][year]
        floor=c['historical_pre_restructuring_profit_floor']-c['card_deduction']-c['bbse_deduction']-c['cielo_ownership_deduction']-c['current_cost_nominal']
        assert b['lower']==pytest.approx(floor)
        real.append(floor*proof['ipca_factors'][year])
    assert statistics.median(real)==pytest.approx(proof['normalized_profit_lower'])
    assert proof['market_cap']/statistics.median(real)==pytest.approx(proof['pe_upper'])
