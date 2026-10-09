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

def test_three_profit_ceilings_can_reject_price_without_fabricating_missing_years():
    from b00s_documentary import profit_interval
    from b00s_fundamentals import bounded_valuation
    review={'ticker':'TEST3','valuation':{'profit_bounds':{
        str(y):dict(lower=None,upper=v) for y,v in
        zip(range(2014,2019),[None,90,95,100,None])}}}
    profit=profit_interval([None,80,85,90,110],[1]*5,2019,review)
    assert profit==dict(lower=None,upper=100)
    capital=dict(lower=2501,upper=None)
    missing=['FIVE_COMPARABLE_ATTRIBUTABLE_PROFITS_MISSING','UNQUOTED_OR_UNRECONCILED_SHARE_CLASS']
    assert bounded_valuation(capital,profit,missing)==(None,'INDETERMINATE')
    interval,status=bounded_valuation(capital,profit,missing,['UNQUOTED_OR_UNRECONCILED_SHARE_CLASS'])
    assert interval==dict(lower=25.01,upper=None) and status=='REJECTED_PRICE'
    assert bounded_valuation(dict(lower=2500,upper=None),profit)[1]=='INDETERMINATE'
    # A lower price endpoint never admits a mature company or proves reinvestment.
    assert bounded_valuation(dict(lower=1400,upper=None),profit)[1]=='INDETERMINATE'
    assert bounded_valuation(dict(lower=1400,upper=1500),dict(lower=100,upper=None))[1]=='PASS_MATURE'

def test_irb_2019_price_rejection_is_separate_from_dated_quality_assessment():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2019}
    assert set(rows)=={r['ticker'] for r in m.candidates() if r['year']==2019}
    irb=rows['IRBR3'];review=irb['documentary_assessment'];proof=review['numerical_proof']
    real=[]
    for year,items in proof['annual_additions'].items():
        upper=sum(item['amount_brl'] for item in items)
        assert upper==review['valuation']['profit_bounds'][year]['upper']
        real.append(upper*proof['ipca_factors'][year])
    assert proof['median_upper']==pytest.approx(max(real))
    assert proof['market_cap_on_lower']==312000000*98.50
    assert proof['pe_lower']==pytest.approx(proof['market_cap_on_lower']/max(real))
    assert proof['treasury_sensitivity']['pe_lower']>25
    assert irb['normalized_pe'] is None and irb['market_cap'] is None
    assert irb['normalized_pe_interval']['lower']==pytest.approx(proof['pe_lower'])
    assert irb['normalized_pe_interval']['upper'] is None
    assert irb['valuation_status']=='REJECTED_PRICE'
    assert irb['quality_category']=='QUALIFIED_SATISFACTORY'
    assert all(d['status']=='SATISFACTORY' for d in review['dimensions'].values())
    assert {r['ticker'] for r in rows.values() if r['quality_category'].startswith('QUALIFIED')}=={'ABCB4','BBSE3','IRBR3','PSSA3'}
    assert rows['CPFE3']['market_cap'] is None  # June issuance invalidates the old FRE count.

def test_reusing_a_dossier_does_not_reuse_annual_valuation_or_metric_proofs():
    from b00s_documentary import expand_incremental, DIMENSIONS
    previous=next(r for r in json.loads((m.INPUT/'economic_reviews_2015.json').read_text()) if r['ticker']=='TIMP3')
    previous['numerical_proof']={'cutoff':'2015-06-30','annual_lease_cost':123}
    saved=copy.deepcopy(previous)
    update=dict(reuse_previous=True,prior_assessment='2015:'+previous['cnpj'],years=[2016],cutoff='2016-06-30',
        cnpj=previous['cnpj'],ticker='TIMP3',valuation=dict(status='INDETERMINATE',reason='Review new tower sale and lease commitments',evidence=[]),
        incremental_review=dict(reason='Reviewed annual changes',evidence=[]),
        confirmed_dimensions={k:'Explicit unchanged-dimension finding' for k in DIMENSIONS})
    result=expand_incremental(update,previous)
    assert result['valuation']['status']=='INDETERMINATE'
    assert 'economic_metrics' not in result
    assert 'numerical_proof' not in result
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
        if s['path'].endswith('.submission.xml.gz'):
            # Validate the submitted XML independently of the collection path;
            # the download's newly generated aggregate PDF is not evidence.
            import re
            submitted=ET.fromstring(raw)
            kind={'XmlDemonstracoesFinanceiras':'DFP',
                  'XmlInformacoesTrimestraisFinanceiras':'ITR'}[submitted.tag]
            assert submitted.findtext('Documento/VersaoDocumento')==s['version']
            date=submitted.findtext(f'Dados{kind}/DataReferencia')
            assert '-'.join(reversed(date.split('/')))==s['reference'][:10]
            for child,metadata in [('CnpjEmpresa','NumeroCnpjCompanhiaAberta'),('CodigoCvm','CodigoCvm')]:
                assert re.sub(r'\D','',submitted.findtext('DadosEmpresa/'+child))==re.sub(r'\D','',root.findtext('.//CompanhiaAberta/'+metadata))
            assert submitted.findtext('Documento/TipoDocumento')==root.findtext('.//CodigoTipoDocumento')
            if r.get('source_format')=='original_xml':
                original=raw
                assert 'NOT PDF pagination' in r['extraction']
                assert submitted.find(f'Dados{kind}/Formulario') is not None
            else:
                notes=submitted.find(f'Dados{kind}/AnexosDocumento')
                node=next(n for n in notes if int(n.findtext('NumeroGrupoRelacionado','0'))==r['group'])
                original=base64.b64decode(node.findtext('ImagemObjetoArquivoPdf'),validate=True)
        else:
            inner=zipfile.ZipFile(io.BytesIO(raw))
            kind=Path(s['path']).suffixes[-2][1:].upper()
            assert kind in ['DFP','ITR']
            version=ET.fromstring(inner.read(f'FormularioDemonstracaoFinanceira{kind}.xml'))
            assert version.findtext('.//NumeroVersaoDocumento')==s['version']
            assert version.findtext('.//DataReferenciaDocumento')==s['reference']
            if r.get('source_format')=='original_xml':
                # Native audit/DFC records use logical units, not PDF pages.
                member='InfoFinaDFin.xml' if r['group']==0 else 'AnexoTexto.xml'
                original=inner.read(member)
                ET.fromstring(original)
                assert 'NOT PDF pagination' in r['extraction']
            else:
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

def test_2017_material_updates_do_not_become_automatic_approvals_or_exits():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2017}
    assert set(rows)=={r['ticker'] for r in m.candidates() if r['year']==2017}
    for r in rows.values():
        a=r['documentary_assessment']
        assert len(a['dimensions'])==6
        assert all(e['received']<=r['cutoff'] for e in a['incremental_review']['evidence'])
        if r['ticker']!='SAPR4':
            assert a['prior_assessment']=='2016:'+r['cnpj']
            assert all(d['prior_year']==2016 and d['review_2017'] for d in a['dimensions'].values())
    # Itaú's current, unresolved BankBoston proceeding changes the entry gate,
    # never the base screen or the B2 right to retain an existing position.
    bank=rows['ITUB4']
    assert bank['documentary_assessment']['dimensions']['governance']['status']=='INDETERMINATE'
    assert bank['quality_category']=='INDETERMINATE'
    assert bank['base_status']=='PASS'
    assert any(e['docid']=='66912' for e in bank['documentary_assessment']['dimensions']['governance']['evidence'])
    for ticker in ['ABCB4','PSSA3','TBLE3']:
        assert rows[ticker]['quality_category']=='QUALIFIED_SATISFACTORY'
    # Five tranches are now documented, but the newly reported prior-period
    # correction prevents transporting the earlier earnings floors blindly.
    tim=rows['TIMP3']['documentary_assessment']
    assert tim['valuation']['status']=='INDETERMINATE'
    assert 'economic_metrics' not in tim
    assert '370' in tim['valuation']['reason']
    assert rows['SAPR4']['valuation_status']=='PASS_MATURE'
    assert rows['SAPR4']['quality_category']=='INDETERMINATE'
    assert rows['SAPR4']['normalized_profit'] is None
    assert rows['SAPR4']['normalized_pe'] is None
    assert rows['SAPR4']['normalized_pe_interval']['upper']<=15

def test_sapr_2017_bound_reconciles_historical_tax_and_delivered_lease():
    import hashlib, math
    review=next(r for r in json.loads((m.INPUT/'economic_reviews_2017.json').read_text()) if r['ticker']=='SAPR4')
    proof=review['numerical_proof'];lease=proof['lease_bridge'];bounds=review['valuation']['profit_bounds']
    sources=json.loads((m.INPUT/'ipc_fipe_availability_2017.json').read_text())
    for src in sources:
        assert hashlib.sha256((m.INPUT/src['file']).read_bytes()).hexdigest()==src['sha256']
    rates=json.loads((m.INPUT/'ipc_fipe_sgs193_june2016_may2017.json').read_text())
    assert len(rates)==12 and rates[-1]['data']=='01/05/2017'
    fipe=math.prod(1+float(r['valor'])/100 for r in rates)-1
    rate=(1+lease['annual_contract_rate'])*(1+fipe)-1
    cost=lease['march_2017_liability']*(1+rate)**.25*rate+868000
    assert lease['annual_amortization_from_q1']==4*(288000-72000)
    assert lease['annual_gross_cost_charged_to_each_real_fiscal_floor']==pytest.approx(cost)
    real_floors=[]
    for year,row in proof['tax_bridge']['rows'].items():
        assert row['closing_provisions']==row['opening_provisions']+row['additions']-row['gross_reversals']
        assert row['opening_dta']==pytest.approx(.34*row['opening_provisions'],abs=1000)
        assert row['closing_dta']==pytest.approx(.34*row['closing_provisions'],abs=1000)
        x=row['deduction_inputs']
        # Historical tax on the reversal is reconciled; all other deductions
        # and current lease costs remain gross. No speculative future tax credit.
        nominal=x['reported']-.66*x['provision_releases']-sum(x[k] for k in ['other_revenue','asset_sale_revenue','other_financial_revenue','non_jcp_positive_tax','positive_pdd_reversal'])
        factor=row['ipca_factor_same_as_proposal'];expected=nominal*factor-cost
        assert bounds[year]['lower']*factor==pytest.approx(expected)
        real_floors.append(expected)
    assert set(bounds)=={'2012','2013','2014','2015','2016'}
    assert bounds['2012']['lower'] is None and bounds['2015']['lower'] is None
    # With two unbounded lower endpoints, the five-year median lower bound is
    # the smallest proved floor, not the median of a shortened three-year sample.
    capital=167911724*9.25+335823449*10.90
    assert proof['median_lower']==pytest.approx(min(real_floors))
    actual=next(r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2017 and r['ticker']=='SAPR4')
    assert actual['market_cap']==pytest.approx(capital)
    assert actual['normalized_pe_interval']['upper']==pytest.approx(capital/min(real_floors))

def test_bbse_2018_admission_uses_five_year_bound_after_disposals_and_costs():
    import hashlib, statistics
    r=next(x for x in json.loads((m.INPUT/'economic_reviews_2018.json').read_text()) if x['ticker']=='BBSE3')
    proof=r['numerical_proof'];bounds=r['valuation']['profit_bounds']
    assert set(bounds)=={'2013','2014','2015','2016','2017'}
    assert bounds['2013']['lower'] is None and bounds['2014']['lower'] is None
    assert hashlib.sha256((m.INPUT/'ipca_sgs433.json').read_bytes()).hexdigest()==proof['ipca_source_sha256']
    real=[float('-inf')]*2
    for row in proof['annual_rows']:
        c=row['components'];factor=row['ipca_factor_to_known_may2018']
        floor=c['reported_attributable_profit']-sum(v for k,v in c.items() if k!='reported_attributable_profit')
        assert floor==pytest.approx(row['nominal_lower_before_new_erp'])
        after_cost=floor*factor-590300
        assert bounds[str(row['fiscal_year'])]['lower']*factor==pytest.approx(after_cost)
        real.append(after_cost)
    # Retains SH2 losses and costs while removing positive investee earnings,
    # gross broker commissions and the gross IRB disposal gain, without sale cash.
    last=proof['annual_rows'][-1]['components']
    assert last['irb_disposal_gain_gross']==269246000
    assert last['sh2_positive_subsidiary_profit_half']==.5*(6240000+83778000+1222000)
    assert last['sh2_all_broker_commissions_gross']==283420000
    capital=2000000000*24.46;median=statistics.median(real)
    assert median==pytest.approx(proof['normalized_profit_interval']['lower'])
    assert capital/median==pytest.approx(14.946834439509185)
    actual=next(x for x in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if x['year']==2018 and x['ticker']=='BBSE3')
    assert actual['market_cap']==pytest.approx(capital)
    assert actual['normalized_pe_interval']['upper']==pytest.approx(capital/median)
    assert actual['normalized_profit'] is None and actual['normalized_pe'] is None
    assert actual['valuation_status']=='PASS_MATURE'
    assert actual['quality_category']=='QUALIFIED_SATISFACTORY'
    assert all(e['received']<='2018-06-29' for e in actual['documentary_assessment']['valuation']['evidence'])


def test_2018_material_changes_refresh_dossiers_without_forcing_base_exits():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2018}
    assert set(rows)=={r['ticker'] for r in m.candidates() if r['year']==2018}
    for r in rows.values():
        a=r['documentary_assessment']
        assert len(a['dimensions'])==6
        assert all(e['received']<=r['cutoff'] for e in a['incremental_review']['evidence'])
        if a.get('reuse_previous'):
            assert a['prior_assessment']=='2017:'+r['cnpj']
            assert all(d['review_2018'] for d in a['dimensions'].values())
        elif r['ticker']!='BBSE3':
            assert a['prior_assessment']['year']==2017
            assert all(d['reason'] and d['evidence'] for d in a['dimensions'].values())
    sapr=rows['SAPR4'];assessment=sapr['documentary_assessment']
    assert sapr['base_status']=='PASS'
    assert 'numerical_proof' not in assessment  # no obsolete one-stage lease cost
    assert '194,461' in assessment['valuation']['reason']
    assert any(e['docid']=='sapr_curitiba_contract_201806' for e in assessment['valuation']['evidence'])
    assert rows['TBLE3']['base_status']=='PASS'
    assert rows['TBLE3']['quality_category']=='INDETERMINATE'
    assert rows['ABCB4']['quality_category']==rows['PSSA3']['quality_category']=='QUALIFIED_SATISFACTORY'


def test_2020_material_review_keeps_quality_and_valuation_separate():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2020}
    assert set(rows)=={r['ticker'] for r in m.candidates() if r['year']==2020}
    assert {t for t,r in rows.items() if r['quality_category']=='QUALIFIED_SATISFACTORY'}=={'ABCB4','BBDC4','BBSE3','PSSA3'}
    for r in rows.values():
        a=r['documentary_assessment']
        assert len(a['dimensions'])==6
        for d in a['dimensions'].values():
            assert d['reason'] and d['contrary_evidence'] and d['evidence']
            assert all(e['received']<=r['cutoff'] for e in d['evidence'])
    # New resolution affects the buy filter, never a retrospective 2019 decision.
    b=rows['BBDC4']['documentary_assessment']
    assert b['dimensions']['governance']['status']=='SATISFACTORY'
    assert b['dimensions']['governance']['prior_year']==2019
    old=next(r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2019 and r['ticker']=='BBDC4')
    assert old['quality_category']=='INDETERMINATE'
    eq=rows['EQTL3']
    assert eq['market_cap_interval']=={'lower':1010186085*23.22,'upper':1010186085*23.22}
    assert eq['valuation_status']=='INDETERMINATE'
    assert eq['normalized_pe'] is None
    for t in ['NEOE3','TIET4']:
        assert not rows[t]['documentary_assessment'].get('reuse_previous')
        assert rows[t]['documentary_assessment']['dimensions']['durability']['status']=='SATISFACTORY'


def test_tim_2020_diagnostic_is_not_a_certified_reinvestment_approval():
    import statistics
    r=next(r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2020 and r['ticker']=='TIMP3')
    a=r['documentary_assessment'];p=a['numerical_proof'];x=p['resolved'];d=p['conditional_diagnostic']
    assert x['ifrs2019_net_income']+x['ifrs16_net_adjustment_to_pre_ifrs_basis']==x['pre_ifrs2019_reported_net_income']
    assert x['management_normalized_pre_ifrs_rounded']-x['ifrs16_net_adjustment_to_pre_ifrs_basis']==x['same_normalizations_with_ifrs16_illustrative']
    real=[v*d['ipca_factors'][y] for y,v in d['nominal_profit_after_only_listed_gains'].items()]
    assert statistics.median(real)==pytest.approx(d['median'])
    assert d['market_cap']/d['median']==pytest.approx(d['pe'])
    assert d['real_eps_cagr_removing_only_listed_gains']<.04<d['real_eps_cagr_using_rounded_management2019_ifrs_equivalent']
    assert d['not_certified_bound_or_point']
    assert a['valuation']['status']==r['valuation_status']=='INDETERMINATE'
    assert 'profit_overrides' not in a['valuation'] and 'profit_bounds' not in a['valuation']
    assert 'economic_metrics' not in a


def test_2020_irb_deterioration_updates_retained_position_without_backdating():
    reviews=load_reviews()
    irb=reviews[2020,'33376989000191']
    for name in ['earnings_reliability','financial_resilience','governance']:
        d=irb['dimensions'][name]
        assert d['status']=='REJECTED_EVIDENCED' and d['material_evidence']
        assert all(e['received']<='2020-06-30' for e in d['evidence'])
    rows=json.loads((m.INPUT/'fundamental_decisions.json').read_text())
    assert not any(r['year']==2020 and r['ticker']=='IRBR3' for r in rows)
    old=next(r for r in rows if r['year']==2019 and r['ticker']=='IRBR3')
    assert old['quality_category']=='QUALIFIED_SATISFACTORY'
    statuses,_=m.selection('B00S',2020)
    assert statuses['IRBR3']=='INDETERMINATE'
    from b00s_incremental_report import retained_review_sections
    # No future return is needed to exercise the reporting of the retained case.
    ledger=[dict(year='2020',variant='VQ',ticker='IRBR3',base_status='INDETERMINATE',before='0.025',after='0.025')]
    summary,dossier=retained_review_sections(2020,[r for r in rows if r['year']==2020],ledger)
    assert 'IRBR3' in summary and 'REJECTED_EVIDENCED' in dossier
    assert 'sem nova candidatura PASS' in dossier
    assert 'venda extraordinária' in summary


def test_2021_copasa_economic_floor_does_not_invent_profits_or_reinvestment():
    from b00s_fundamentals import bounded_valuation
    r=next(r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2021 and r['ticker']=='CSMG3')
    a=r['documentary_assessment'];v=a['valuation'];p=a['numerical_proof']
    assert set(v['profit_bounds'])=={'2016','2017','2018','2019','2020'}
    for year in ['2016','2017']:
        assert v['profit_bounds'][year]['lower'] is None and v['profit_bounds'][year]['upper'] is None
    for year,proof in p['fiscal_floors'].items():
        assert proof['nominal_lower']==v['profit_bounds'][year]['lower']
        assert proof['nominal_lower']*proof['ipca_factor']==pytest.approx(proof['real_lower'])
    extra=p['documented_nonrecurring_cost']
    assert extra['net_addback_lower']==pytest.approx(extra['conservative_amount_after_rounding']-extra['income_tax_maximum_at_34pct']-extra['incremental_profit_sharing_maximum'])
    assert p['median_lower']==pytest.approx(min(x['real_lower'] for x in p['fiscal_floors'].values()))
    assert r['normalized_profit'] is None and r['normalized_pe'] is None
    assert r['valuation_status']=='PASS_MATURE' and r['normalized_pe_interval']['upper']==pytest.approx(14.7423118185)
    assert r['real_eps_cagr'] is None and r['average_payout'] is None
    # Removing documented exceptional-cost normalization crosses15. This
    # admission depends on the audited bridge, not the raw P/E or a point estimate.
    raw_floor=(p['fiscal_floors']['2018']['nominal_lower']-extra['net_addback_lower'])*p['fiscal_floors']['2018']['ipca_factor']
    cap={'lower':p['capitalization'],'upper':p['capitalization']}
    assert bounded_valuation(cap,{'lower':raw_floor,'upper':None})[1]=='INDETERMINATE'
    assert r['quality_category']=='INDETERMINATE'


def test_2021_reuses_issuer_dossiers_and_resolves_material_financial_changes():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2021}
    assert len(rows)==20 and set(rows)=={r['ticker'] for r in m.candidates() if r['year']==2021}
    vivo=rows['VIVT3']['documentary_assessment']
    assert vivo['prior_assessment']=='2020:'+rows['VIVT3']['cnpj']
    assert load_reviews()[2020,rows['VIVT3']['cnpj']]['ticker']=='VIVT4'
    for r in rows.values():
        a=r['documentary_assessment']
        assert len(a['dimensions'])==6
        for d in a['dimensions'].values():
            assert d['reason'] and d['evidence'] and d['contrary_evidence']
            assert all(e['received']<=r['cutoff'] for e in d['evidence'])
    for ticker in ['CSMG3','SBSP3']:
        d=rows[ticker]['documentary_assessment']['dimensions']['financial_resilience']
        assert d['status']=='SATISFACTORY'
    # Prudential and cash evidence can improve without proving every dimension.
    assert rows['TAEE4']['documentary_assessment']['dimensions']['financial_resilience']['status']=='SATISFACTORY'
    assert rows['TAEE4']['quality_category']=='INDETERMINATE'
    assert rows['VIVT3']['valuation_status']=='INDETERMINATE'
    assert rows['SANB4']['valuation_status']=='INDETERMINATE'


def test_2021_credit_method_change_is_explicit_without_retrospective_rejection():
    rows=json.loads((m.INPUT/'fundamental_decisions.json').read_text())
    porto=next(r for r in rows if r['year']==2021 and r['ticker']=='PSSA3')
    d=porto['documentary_assessment']['dimensions']['earnings_reliability']
    assert '1.890' in d['reason'] and '1.620' in d['reason'] and '123,8%' in d['reason']
    assert any(e['docid']=='103273' and e['group']==192 and 25 in e['pages'] for e in d['evidence'])
    assert porto['quality_category']=='QUALIFIED_SATISFACTORY'
    assert next(r for r in rows if r['year']==2020 and r['ticker']=='PSSA3')['quality_category']=='QUALIFIED_SATISFACTORY'


def test_2022_santander_three_floors_preserve_five_year_window_and_getnet_costs():
    r=next(r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2022 and r['ticker']=='SANB4')
    a=r['documentary_assessment']; v=a['valuation']; p=a['numerical_proof']
    assert set(v['profit_bounds'])=={'2017','2018','2019','2020','2021'}
    for year in ['2017','2021']:
        assert v['profit_bounds'][year]['lower'] is None
        assert v['profit_bounds'][year]['upper'] is None
    for proof in p['annual']:
        assert proof['lower_nominal']==proof['reported_attributable_profit']-sum(proof['deductions'].values())
        assert v['profit_bounds'][str(proof['fy'])]['lower']==proof['lower_nominal']
        assert proof['lower_real']==pytest.approx(proof['lower_nominal']*proof['ipca_to_known_may'])
        assert proof['deductions']['getnet_whole_ifrs_profit_before_eliminations']>0
        assert proof['deductions']['superdigital_all_positive_revenues_and_tax']>0
    assert p['median_lower']==pytest.approx(min(x['lower_real'] for x in p['annual']))
    assert r['market_cap']==pytest.approx(3818695031*13.85+3679836020*15.14)
    assert r['normalized_pe_interval']['upper']==pytest.approx(11.106253563647076)
    assert r['valuation_status']=='PASS_MATURE'
    assert r['normalized_profit'] is None and r['normalized_pe'] is None
    assert r['real_eps_cagr'] is None and r['average_payout'] is None
    assert a['dimensions']['capital_economics']['status']=='SATISFACTORY'
    assert a['dimensions']['capital_allocation']['status']=='INDETERMINATE'
    # A distinct contract sensitivity is not a guaranteed ceiling or a new
    # historical-income deduction chosen after subsequent returns.
    stress=p['new_contract_sensitivity']
    assert stress['stress_pe']==pytest.approx(r['market_cap']/(p['median_lower']-stress['stress_current_q1_gross_charges']))
    assert stress['stress_pe']<15
    prior=load_reviews()[2021,r['cnpj']]
    assert prior['valuation']['status']=='INDETERMINATE'


def test_2022_rolling_review_preserves_old_floors_and_current_material_evidence():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2022}
    assert len(rows)==20 and set(rows)=={r['ticker'] for r in m.candidates() if r['year']==2022}
    for r in rows.values():
        a=r['documentary_assessment']
        assert a['prior_assessment']=='2021:'+r['cnpj']
        assert len(a['dimensions'])==6
        for d in a['dimensions'].values():
            assert d['reason'] and d['contrary_evidence'] and d['evidence']
            assert all(e['received']<=r['cutoff'] for e in d['evidence'])
    c=rows['CSMG3'];a=c['documentary_assessment'];p=a['numerical_proof']
    assert c['valuation_status']=='PASS_MATURE'
    assert a['dimensions']['governance']['status']=='INDETERMINATE'
    assert load_reviews()[2021,c['cnpj']]['dimensions']['governance']['status']=='SATISFACTORY'
    assert any(e['docid']=='116984' and e['group']==1654 for e in a['dimensions']['governance']['evidence'])
    assert set(a['valuation']['profit_bounds'])=={'2017','2018','2019','2020','2021'}
    previous=load_reviews()[2021,c['cnpj']]['numerical_proof']
    for year, proof in p['fiscal_floors'].items():
        assert proof['nominal_lower']==previous['fiscal_floors'][year]['nominal_lower']
        assert proof['ipca_factor']>previous['fiscal_floors'][year]['ipca_factor']
    assert c['normalized_pe_interval']['upper']==pytest.approx(9.812788996663288)
    assert any(e['docid']=='114201' and 16 in e['pages'] for e in a['dimensions']['financial_resilience']['evidence'])
    porto=rows['PSSA3']
    assert porto['quality_category']=='QUALIFIED_SATISFACTORY'
    assert porto['capital_classes']==[dict(share_class='ON',quantity=646586060.0,price=17.76)]
    assert any(e['docid']=='114461' and e['group']==192 and 21 in e['pages'] for e in porto['documentary_assessment']['dimensions']['financial_resilience']['evidence'])


def test_2023_four_copasa_bounds_keep_the_unknown_year_in_the_median():
    import statistics
    r=next(r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2023 and r['ticker']=='CSMG3')
    a=r['documentary_assessment'];p=a['numerical_proof'];floors=p['fiscal_floors']
    assert p['cutoff']==r['cutoff']=='2023-06-30'
    assert set(a['valuation']['profit_bounds'])=={'2018','2019','2020','2021','2022'}
    assert a['valuation']['profit_bounds']['2021']['lower'] is None
    old=load_reviews()[2022,r['cnpj']]['numerical_proof']['fiscal_floors']
    for year in ('2018','2019','2020'):
        assert floors[year]['nominal_lower']==old[year]['nominal_lower']
    current=floors['2022']
    assert current['reported_attributable_profit']-sum(v for k,v in current.items() if k.endswith('_removed'))==current['nominal_lower']==550200000
    assert current['financial_asset_and_other_revenue']-current['ordinary_amortized_cost_accretion_retained']==current['financial_asset_and_other_revenue_removed']
    assert current['judicial_provision_reversals_removed']==38103000
    assert current['prodes_subsidy_removed']==2407000
    lower=statistics.median([float('-inf')]+[v['real_lower'] for v in floors.values()])
    assert lower==pytest.approx(floors['2020']['real_lower'])
    assert p['median_lower']==pytest.approx(lower)
    assert r['normalized_pe_interval']['upper']==pytest.approx(14.258466868652224)
    assert r['valuation_status']=='PASS_MATURE'
    assert r['normalized_profit'] is None and r['normalized_pe'] is None
    assert r['real_eps_cagr'] is None and r['average_payout'] is None
    assert a['dimensions']['governance']['status']=='INDETERMINATE'


def test_2023_retained_pass_issuer_does_not_expand_original_buy_universe():
    rows=[r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2023]
    assert len(rows)==19
    assert {r['ticker'] for r in rows}=={r['ticker'] for r in m.candidates() if r['year']==2023}
    assert 'TBLE3' not in {r['ticker'] for r in rows}
    assert m.selection('B00S',2023)[0]['TBLE3']=='PASS'
    retained=load_reviews()[2023,'02474103000119']
    assert retained['prior_assessment']=='2022:02474103000119'
    assert len(retained['dimensions'])==6
    from b00s_incremental_report import retained_review_sections
    ledger=[dict(year='2023',variant='VQ',ticker='TBLE3',base_status='PASS',before='0.3',after='0.3')]
    summary,dossier=retained_review_sections(2023,rows,ledger)
    assert 'fora do universo original de novas compras' in dossier
    assert 'sem nova candidatura PASS' not in dossier
    assert 'TBLE3' in summary and 'venda extraordinária' in summary


def test_2023_material_changes_use_current_documents_and_no_diagnostic_admission():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2023}
    for r in rows.values():
        a=r['documentary_assessment']
        assert a['prior_assessment']=='2022:'+r['cnpj']
        assert len(a['dimensions'])==6
        for d in a['dimensions'].values():
            assert d['reason'] and d['contrary_evidence'] and d['evidence']
            assert all(e['received']<=r['cutoff'] for e in d['evidence'])
    assert rows['CPLE6']['market_cap']==pytest.approx(1054090460*8.23+3128000*26.85+1679335290*8.29)
    assert rows['CPFE3']['documentary_assessment']['dimensions']['financial_resilience']['status']=='SATISFACTORY'
    assert load_reviews()[2022,rows['CPFE3']['cnpj']]['dimensions']['financial_resilience']['status']=='INDETERMINATE'
    porto=rows['PSSA3']['documentary_assessment']
    assert rows['PSSA3']['quality_category']=='QUALIFIED_SATISFACTORY'
    assert any(e['docid']=='126312' and e['group']==193 and 18 in e['pages'] for e in porto['dimensions']['earnings_reliability']['evidence'])
    taee=rows['TAEE4']['documentary_assessment']
    assert taee['numerical_proof']['kind']=='NON_CERTIFYING_2022_COMPONENT_BRIDGE'
    assert taee['valuation']['status']==rows['TAEE4']['valuation_status']=='INDETERMINATE'
    assert 'profit_bounds' not in taee['valuation'] and 'profit_overrides' not in taee['valuation']
    sanb=rows['SANB4']
    assert sanb['valuation_status']=='PASS_MATURE'
    assert sanb['normalized_pe_interval']['upper']==pytest.approx(11.298540120717973)
    assert sanb['real_eps_cagr'] is None


def test_2024_rolling_median_keeps_unknowns_and_preserves_historical_floors():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2024}
    for t in ['CSMG3','SANB4']:
        r=rows[t];a=r['documentary_assessment'];v=a['valuation']
        assert set(v['profit_bounds'])=={'2019','2020','2021','2022','2023'}
        assert v['profit_bounds']['2021']['lower'] is None
        assert v['profit_bounds']['2023']['lower'] is None
        assert r['valuation_status']=='PASS_MATURE'
        assert r['normalized_profit'] is None and r['normalized_pe'] is None
        assert r['real_eps_cagr'] is None
    c=rows['CSMG3'];p=c['documentary_assessment']['numerical_proof']
    old=load_reviews()[2023,c['cnpj']]['numerical_proof']['fiscal_floors']
    for y,floor in p['fiscal_floors'].items():assert floor['nominal_lower']==old[y]['nominal_lower']
    assert c['normalized_pe_interval']['upper']==pytest.approx(13.551172976321116)
    sanb=rows['SANB4'];p=sanb['documentary_assessment']['numerical_proof']
    assert sanb['normalized_pe_interval']['upper']==pytest.approx(14.385675808057046)
    assert sanb['market_cap']==pytest.approx(3818695031*13.13+3679836020*14.43)
    for annual in p['annual']:
        assert annual['lower_nominal']==annual['reported_attributable_profit']-sum(annual['deductions'].values())
        assert annual['deductions']['whole_psa_ifrs_profit_before_eliminations']>0


def test_2024_directed_component_bridges_do_not_become_certified_profits():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2024}
    for t in ['CPFE3','NEOE3','TAEE4']:
        r=rows[t];a=r['documentary_assessment'];p=a['numerical_proof']
        assert r['valuation_status']=='INDETERMINATE'
        assert 'profit_bounds' not in a['valuation'] and 'profit_overrides' not in a['valuation']
        if 'annual' in p:
            for annual in p['annual']:
                assert not annual['certified']
                assert annual['component_subtotal']==annual['reported_attributable']-sum(annual['deductions'].values())
                assert annual['real_component_subtotal']==pytest.approx(annual['component_subtotal']*annual['ipca_factor'])
        else:
            assert not p['certified']
            assert p['component_subtotal']==pytest.approx(p['reported_attributable_profit']-sum(p['deductions'].values()))
            assert p['real_component_subtotal']<p['required_real_median']
            assert p['deductions']['holding_escrow']==26400000
            assert p['ordinary_items_retained']['sudam_sudene']==40895000
    neo=rows['NEOE3']['documentary_assessment']['numerical_proof']
    assert next(a for a in neo['annual'] if a['fiscal_year']==2023)['deductions']['eapsa_acquisition_gain_gross']==1555000000
    assert neo['losses_retained']['gic_2023']==198000000
    assert neo['losses_retained']['itabapoana_2023']==166000000


def test_2024_review_uses_executed_events_and_assesses_every_candidate():
    rows={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2024}
    assert len(rows)==20 and set(rows)=={r['ticker'] for r in m.candidates() if r['year']==2024}
    assert {'ELET3','BMGB4'}<=set(rows)
    for r in rows.values():
        a=r['documentary_assessment'];assert len(a['dimensions'])==6
        for d in a['dimensions'].values():
            assert d['reason'] and d['contrary_evidence'] and d['evidence']
            assert all(e['received']<=r['cutoff'] for e in d['evidence'])
    cpfe=rows['CPFE3']['documentary_assessment']['dimensions']['financial_resilience']
    assert cpfe['status']=='SATISFACTORY'
    assert any(e['docid']=='cpfl_loan_extension_20240521' and e['received']=='2024-05-21' for e in cpfe['evidence'])
    assert rows['CPLE6']['market_cap'] is None and rows['ELET3']['market_cap'] is None
    assert rows['PSSA3']['quality_category']=='QUALIFIED_SATISFACTORY'
    assert m.selection('B00S',2024)[0]['SBSP3']=='FAIL'


def test_explicit_solidity_judgement_is_sourced_and_not_defaulted():
    assert 'solidity_proven' not in calculate_metrics({}, {})
    with pytest.raises(ValueError, match='sourced economic judgement'):
        calculate_metrics({'solidity': {'proven': True, 'reason': 'unsupported'}}, {})
    for proven in [True, False]:
        proof={'solidity': {'proven': proven, 'reason': 'Dated prudential assessment'},
               'evidence': [{'docid': '1', 'group': 192, 'pages': [1]}]}
        assert calculate_metrics(proof, {})['solidity_proven'] is proven
    # True alone still does not supply growth, payout or return on capital.
    assert valuation_gate(20, calculate_metrics(proof, {}) | {'solidity_proven': True})=='INDETERMINATE'


def test_2025_median_price_and_premium_endpoint_have_different_proofs():
    from b00s_documentary import profit_interval
    facts={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2025}
    pssa=facts['PSSA3'];review=pssa['documentary_assessment'];proof=review['numerical_proof']
    assert review['valuation']['status']=='COMPARABLE'
    assert pssa['normalized_profit_interval']['lower']==pssa['normalized_profit_interval']['upper']
    assert pssa['normalized_pe']==pytest.approx(proof['normalized_pe'])
    assert 15<pssa['normalized_pe']<25
    assert proof['premium_endpoint']['real_eps_cagr_lower']<.04<proof['premium_endpoint']['real_eps_cagr_upper']
    assert proof['premium_endpoint']['weighted_shares']=={'2020':648800000, '2024':648563000}
    assert proof['premium_endpoint']['losses_kept']
    assert pssa['real_eps_cagr'] is None and pssa['valuation_status']=='INDETERMINATE'
    assert pssa['solidity_proven'] is True
    assert proof['premium_roe']['two_of_three_years_lower']>proof['premium_roe']['required']
    assert proof['normalized_payout_certified'] is False


def test_2025_rolling_floors_do_not_reuse_aged_or_uncertified_observations():
    facts={r['ticker']:r for r in json.loads((m.INPUT/'fundamental_decisions.json').read_text()) if r['year']==2025}
    csmg=facts['CSMG3'];cp=csmg['documentary_assessment']['numerical_proof']
    assert cp['window']==list(range(2020,2025))
    assert set(cp['fiscal_floors'])=={'2020','2022','2023','2024'}
    assert cp['pe_upper']==pytest.approx(17.1542310605673)
    for y in ['2023','2024']:
        a=cp['fiscal_floors'][y]
        assert a['nominal_lower']==a['reported_attributable_profit']-sum(a['deductions'].values())
        assert a['losses_not_added_back']
    assert csmg['valuation_status']=='INDETERMINATE'
    sanb=facts['SANB4'];sp=sanb['documentary_assessment']['numerical_proof']
    assert {a['fy']for a in sp['annual']}=={2020,2022}
    assert sp['directed_2024_bridge']['certified'] is False
    assert sp['median_lower'] is None and sanb['valuation_status']=='INDETERMINATE'
    assert facts['TAEE4']['documentary_assessment']['numerical_proof']['comparative_restatement_delta']==-114000
    assert facts['TAEE4']['documentary_assessment']['numerical_proof']['certified'] is False


def test_2025_material_changes_and_all_six_reviews_use_current_originals():
    reviews={r['ticker']:r for (y,c),r in load_reviews().items() if y==2025}
    assert set(reviews)=={r['ticker']for r in m.candidates()if r['year']==2025}
    assert len(reviews)==19
    for r in reviews.values():
        assert len(r['dimensions'])==6 and r['prior_assessment']=='2024:'+r['cnpj']
        for d in r['dimensions'].values():
            assert d['prior_year']==2024 and d['review_2025']
            assert all(e['received']<='2025-06-30' for e in d['evidence'])
            if d['status']=='INDETERMINATE':assert d['missing']
    csmg=reviews['CSMG3']['dimensions']['governance']
    assert csmg['status']=='SATISFACTORY'
    assert any(e['docid']=='145717'and e['group']==1654 and e['original'].endswith('.xml.gz')for e in csmg['evidence'])
    assert reviews['TBLE3']['dimensions']['financial_resilience']['status']=='SATISFACTORY'
    assert reviews['TBLE3']['dimensions']['capital_allocation']['status']=='INDETERMINATE'
    assert {'ABCB4','BBDC4','BBSE3','PSSA3'}=={t for t,r in reviews.items()if all(d['status']=='SATISFACTORY'for d in r['dimensions'].values())}
