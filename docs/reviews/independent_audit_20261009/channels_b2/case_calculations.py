"""Cálculos PIT dos dois casos; não importa código do projeto nem séries de retorno."""
import hashlib
import json
import math
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
B=HERE.parent/'audit-blind-20261009'
log=[]
def read(p):
    raw=p.read_bytes();log.append({'path':str(p),'sha256_file':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'operation':'read_only'})
    return raw
def jread(p):return json.loads(read(p))
cases=[]
for case in ['TIMP3_2014','SBSP3_2014']:
    d=jread(B/case/'decision.json');i=jread(B/case/'ipca_known.json');q=jread(B/case/'selection_quotes.json')
    level=1.;index={}
    for r in i['sgs433_known_monthly_values']:
        day,month,year=map(int,r['data'].split('/'));level*=1+float(r['valor'])/100;index[year,month]=level
    availability=i['known_may_availability']
    assert availability['release_date']<=d['cutoff']
    archive=read(B/case/availability['original'])
    assert hashlib.sha256(archive).hexdigest()==availability['sha256']
    quote=q['quotes'][0];assert quote['date']==d['cutoff']
    assert hashlib.sha256(quote['raw_record'].encode()).hexdigest()==quote['record_sha256']
    rawclose=int(quote['raw_record'][108:121])/100
    assert rawclose==quote['close']==d['capital_classes'][0]['price']
    profits={r['fiscal_year']:r['value'] for r in d['profit_evidence'] if r['metric']=='attributable_ni'}
    profits.update({int(y):r['adjusted_profit'] for y,r in d['documentary_assessment']['valuation'].get('profit_overrides',{}).items()})
    annual=[{'fiscal_year':fy,'attributable_profit':profits[fy],
        'known_ipca_factor':index[2014,5]/index[fy,12],
        'profit_cutoff_currency':profits[fy]*index[2014,5]/index[fy,12]} for fy in range(2009,2014)]
    median=statistics.median(r['profit_cutoff_currency'] for r in annual)
    capital=sum(r['quantity']*r['price'] for r in d['capital_classes'])
    assert math.isclose(median,d['normalized_profit'],rel_tol=1e-12)
    assert math.isclose(capital,d['market_cap'],rel_tol=1e-12)
    inflation=index[2014,5]/index[2013,5]-1
    assert math.isclose(inflation,d['inflation_reference'],rel_tol=1e-12)
    distributions={r['fiscal_year']:float(r['raw']['Dividendo_Distribuido_Total']) for r in d['payout_evidence']}
    distributions[2013]=843305000 if case=='TIMP3_2014' else 537465000
    payout_diagnostic=[dict(year=y,distributions=distributions[y],profit=profits[y],
                           payout=distributions[y]/profits[y]) for y in range(2009,2014)]
    result=dict(case=case,cutoff=d['cutoff'],ipca_availability=availability,
        quote=quote,raw_close_reproduced=rawclose,annual_profits=annual,normalized_profit=median,
        class_capitalization=capital,normalized_pe=capital/median,
        inflation_known_12_months=inflation,premium_roc_minimum=inflation+.06,
        payout_independent_diagnostic=payout_diagnostic,
        average_payout_independent_diagnostic=statistics.mean(r['payout'] for r in payout_diagnostic),
        payout_sources2013='34545/g412 p59 mínimos357.583mi; 37056/g193 p76 aprova complemento485.722mi em10/04/2014'
            if case=='TIMP3_2014' else '37910/g193 p51 AGO30/04/2014:456.845mi+80.620mi',
        payout_limitation='Diagnóstico por lucro atribuível ajustado apenas pelos overrides documentais; outros ajustes econômicos, reservas/exercícios e JCP precisam ponte antes de certificação final. Não basta para PASS_REINVESTOR.',
        normalized_profit_source_records=d['profit_evidence'],payout_source_records=d['payout_evidence'])
    if case=='TIMP3_2014':
        facts=jread(B/case/'financial_extract.json')['facts'];inputs=[];capitals={}
        for fy in range(2010,2014):
            src=[]
            def metric(account):
                eligible=[r for r in facts if r['year']==fy and r['perimeter']=='con' and r['account']==account
                          and r['received']<=d['cutoff'] and r['period_end']<=d['cutoff']]
                r=max(eligible,key=lambda r:(r['received'],r['reference'],r['version']));src.append(r)
                return r['value']*1000
            equity=metric('2.03');debt=metric('2.01.04')+metric('2.02.01');cash=metric('1.01.01')+metric('1.01.02')
            ebit=metric('3.05');pretax=metric('3.07');tax_expense=-metric('3.08')
            capitals[fy]=equity+debt-cash
            point=dict(year=fy,equity=equity,interest_debt_without_extra_leases=debt,
                cash_and_current_investments=cash,capital=capitals[fy],ebit=ebit,pretax=pretax,tax_expense=tax_expense,sources=src)
            if fy>2010:
                point['nopat']=ebit*(1-tax_expense/pretax)
                point['average_capital']=(capitals[fy]+capitals[fy-1])/2
                point['roic_without_extra_leases']=point['nopat']/point['average_capital']
            inputs.append(point)
        med_roc=statistics.median(r['roic_without_extra_leases'] for r in inputs if r['year']>2010)
        result.update(roic_same_frozen_formula_diagnostic=inputs,roic_median_same_formula=med_roc,
            rejects_under_same_frozen_formula=med_roc<inflation+.06,
            roic_conclusion='ISSUE: insumos2010–13 já disponíveis produzem mediana11,80247897%, abaixo mínimo12,37507440%; duas observações suficientes mesmo se terceiro variar. Omissão de leases positivos favorece o retorno. Antes de REJECTED formal, confirmar coerência do capital econômico/tributário e ajustes do NOPAT como nos casos congelados, sem usar2014/2015.',
            roic_limitations=['Cálculo direto de contas primárias transportadas, sem rebaixar VQ por baixo indicador.',
                'Goodwill permanece no equity; aquisições não foram retiradas do capital.',
                'Não certifica normalização integral do capital: remover ativo fiscal/equity poderia mudar retorno; não foi presumido.',
                'Não certifica retorno incremental; não transforma diagnóstico em prova econômica definitiva.'])
    cases.append(result)
with (HERE/'case_calculations.json').open('x') as f:json.dump(cases,f,ensure_ascii=False,indent=2);f.write('\n')
with (HERE/'scope_access_supplement.json').open('x') as f:json.dump({'accessed':log,'returns_accessed':False,'network_calls':0},f,ensure_ascii=False,indent=2);f.write('\n')
for c in cases:print(c['case'],c['normalized_pe'],c['average_payout_independent_diagnostic'],c.get('roic_median_same_formula'))
