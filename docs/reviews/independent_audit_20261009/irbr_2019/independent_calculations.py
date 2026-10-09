"""Recalcula as verificações sem acessar qualquer série de retornos."""
import gzip
import hashlib
import json
import math
import statistics
import xml.etree.ElementTree as ET
from datetime import datetime
from review_reader import PACKAGE, OUT, log

def ref(docid,group,pages):
    sources=json.loads((PACKAGE/'sources.json').read_text())
    s=next(s for s in sources if s['docid']==str(docid) and s['group']==group)
    return {k:s[k] for k in ['docid','group','received','original','original_sha256','url']} | {'pages_1_based':pages}

# Milhares de reais. Transcrição independente das páginas revisadas; não se usa
# o vetor de somas da decisão congelada como entrada.
components={
 '2015':dict(reported=763718,administrative_except_own_staff=266605-127461,
             other_noncontract_operating=11636+5700,property_expenses=5163+23466,
             other_financial=161,negative_permanent_tax=1726+2804,
             tax_provisions=3344,international_loss=2798),
 '2016':dict(reported=849874,administrative_except_own_staff=260807-146783,
             other_noncontract_operating=737+6757,property_expenses=1951+679,
             other_financial=40117,
             negative_permanent_tax=48+38+120+96+2866+2293+280+224+97+78+2566+993+3898,
             tax_provisions=2112,other_financial_tax=36318,
             international_loss_and_impairment=311+4736),
 '2017':dict(reported=925050,administrative_except_own_staff=277156-145151,
             other_noncontract_operating=1210+3731,property_other=400,
             negative_permanent_tax=1810+1448+11716+9454,
             other_financial_tax=28782,international_impairment_stock=5671,
             parent_property_loss_additional=11361)
}
upper_nominal={y:sum(v.values())*1000 for y,v in components.items()}
ipath=PACKAGE/'ipca_known.json';log(ipath,'independent_IPCA_factor_calculation')
ipca=json.loads(ipath.read_text())
months=[(datetime.strptime(x['data'],'%d/%m/%Y'),float(x['valor'])) for x in ipca['sgs433_known_monthly_values']]
assert max(d for d,v in months)<=datetime(2019,5,1)
factors={y:math.prod(1+v/100 for d,v in months if datetime(int(y),12,1)<d<=datetime(2019,5,1)) for y in components}
upper_real={y:upper_nominal[y]*factors[y] for y in components}
median_upper=max(upper_real.values())
qpath=PACKAGE/'selection_quote_record.txt';log(qpath,'independent_fixed_width_quote_parse')
qb=qpath.read_bytes(); q=qb.decode().rstrip('\r\n')
assert len(q)==245 and q[2:10]=='20190628' and q[12:24].strip()=='IRBR3'
price=int(q[108:121])/100; factor=int(q[210:217]);assert factor==1
shares_issued=312000000;treasury=1584600;shares_outstanding=shares_issued-treasury
cap=shares_issued*price;cap_outstanding=shares_outstanding*price
valuation={
 'components_brl_thousands':components,'annual_upper_nominal_brl':upper_nominal,
 'ipca_factors':factors,'annual_upper_real_brl':upper_real,'median_upper_brl':median_upper,
 'quote_close_brl':price,'quote_record_sha256':hashlib.sha256(qb).hexdigest(),
 'on_issued_shares':shares_issued,'treasury_shares':treasury,'on_outstanding_shares':shares_outstanding,
 'on_capitalization_issued_brl':cap,'on_capitalization_outstanding_brl':cap_outstanding,
 'pe_lower_issued':cap/median_upper,'pe_lower_outstanding':cap_outstanding/median_upper,
 'profit_required_at_25_outstanding_brl':cap_outstanding/25,
 'gap_vs_median_upper_brl':cap_outstanding/25-median_upper,
 'additional_2017_nominal_profit_needed_brl':(cap_outstanding/25-median_upper)/factors['2017'],
 'conclusion':'Cota inferior maior que 25 em ambas as bases de ações. Rejeição por preço corroborada.',
 'economic_assumption':'Custos ordinários de pessoal, subscrição, retrocessão, sinistros e mercado permanecem no ciclo; despesas extraordinárias e rubricas residuais devolvidas em bruto conforme tabela. Tetos condicionais a esse tratamento econômico; não lucro recorrente pontual.',
 'sources':[ref(67429,412,[28,29,30,31,85,86,87,88]),ref(71429,412,[3,21,22,23,74,75,76]),ref(82684,193,[58])]
}

def original_dfc(fn,col):
    path=PACKAGE/'review_originals'/fn
    log(path,'independent_DFC_arithmetic_from_original_XML',[1])
    root=ET.fromstring(gzip.decompress(path.read_bytes()))
    rows={n.findtext('PlanoConta/NumeroConta'):float(n.findtext('ValorConta'+str(col)))
          for n in root if n.findtext('PlanoConta/VersaoPlanoConta/CodigoTipoInformacaoFinanceira')=='2'
          and n.findtext('PlanoConta/NumeroConta','').startswith('6.01')}
    cfo=rows['6.01'];securities=rows['6.01.11']+rows['6.01.12']
    assert sum(v for k,v in rows.items() if k!='6.01')==cfo
    return {'scope':'consolidated','original_unit':1,'values_brl_thousands':rows,'cfo':cfo,
            'securities_net_within_cfo':securities,'cfo_minus_securities':cfo-securities,
            'qualification':'É subtotal analítico, não CFO econômico certificado; resgates incluem rendimento.'}
cash={'FY2018':original_dfc('cvm_81090_g0.xml.gz',1),'Q1_2019':original_dfc('cvm_82684_g0.xml.gz',4)}

economic={
 'roe_reported':{'2016':849874/((3174595+3328217)/2),'2017':925050/((3328217+3581183)/2),'2018':1218796/((3581183+4000780)/2)},
 '2018_roe_after_gross_removal_previrb_and_pdd':(1218796-159208-1780-51846)/((3581183+4000780)/2),
 'qualification_roe_removal':'Sensibilidade conservadora sem recompor tributos; não estimativa certificada de lucro recorrente.',
 '2018_profit_after_gross_removal_brl_thousands':1218796-159208-1780-51846,
 '2018_gross_dividends_brl_thousands':893410,
 '2018_gross_payout_reported':893410/1218796,
 '2018_gross_payout_removal_sensitivity':893410/(1218796-159208-1780-51846),
 'geographic':{
  '2017':{'foreign_loss_ratio_accounting_gross':1144546/1652866,'foreign_gross_margin_rate':376000/1652866,'foreign_margin':376000,'domestic_margin':555840},
  '2018':{'foreign_loss_ratio_accounting_gross':1988059/2345816,'foreign_gross_margin_rate':194011/2345816,'foreign_margin':194011,'domestic_margin':1158337},
  'Q1_2019':{'foreign_loss_ratio_accounting_gross':520541/586964,'foreign_gross_margin_rate':60557/586964,'foreign_margin':60557,'domestic_margin':257835}},
 'geographic_qualification':'Sinistros/prêmio ganho na visão contábil bruta; NÃO são as taxas retidas gerenciais 59%,55,9%,54,1%. Margem inclui custos de aquisição e retrocessão.',
 'credit':{
  'gross_insurer_balance_growth_2018':3327272/2293114-1,
  'total_net_credit_growth_2018':4652082/3220012-1,
  'insurer_estimated_plus_rvne_2017':630719+352740,'insurer_estimated_plus_rvne_2018':1459134+458013,
  'all_estimated_plus_rvne_2017':630719+352740+604007,
  'all_estimated_plus_rvne_2018':1459134+458013+950951,
  'all_estimated_plus_rvne_Q1_2019':1318332+477603+999228,
  'q1_estimated_insurer_change':1318332/1459134-1,
  'q1_estimated_reinsurer_change':999228/950951-1,
  'q1_actual_insurer_premium_receipts':1298545,
  'q1_overdue_gross_credit':671800,'q1_overdue_debit_offsets':339943,'q1_overdue_pdd':11255,'q1_overdue_net':320602,
  'q1_over181_gross_credit':220506,'q1_over181_offsets':207323,'q1_over181_pdd':5671,'q1_over181_net':7512,
  'qualification':'Mudança de classificação estimado→efetivo não é recebimento; notas permitem compensação legal. Total líquido aging não prova inexistência de atraso bruto.'},
 'prudential':{
  '2018':{'pla':3003046,'cmr':935813,'surplus':3003046-935813,'coverage':3003046/935813,'liquidity_surplus':293151},
  'Q1_2019':{'pla':2745243,'cmr':1011134,'surplus':2745243-1011134,'coverage':2745243/1011134,'liquidity_surplus':701221},
  'capital_surplus_change':1734109/2067233-1,
  '2018_liquidity_excluding_credit_rights':293151-1302813,
  'Q1_liquidity_excluding_credit_rights':701221-1463416,
  'qualification':'Exclusão dos direitos creditórios é cenário analítico, não regra CNSP nem descumprimento comprovado.'},
 'audit_reserve_discrepancy':{'amount':8823037-8805895,'fraction_of_reserves':(8823037-8805895)/8805895,
                             'fraction_of_profit':(8823037-8805895)/1218796,
                             'fraction_of_pla':(8823037-8805895)/3003046,
                             'fraction_of_surplus':(8823037-8805895)/2067233},
 'related_premium_share_2018':1942334/6963868,
}
economic['roe_reported_median']=statistics.median(economic['roe_reported'].values())
result={'valuation':valuation,'cash':cash,'economic':economic}
(OUT/'independent_calculations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
