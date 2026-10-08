"""Economic invariants and complete offline replay of the fiscal checkpoint."""
import copy,csv,gzip,json,math
from pathlib import Path
import pytest
from scripts.simulate_ir_100k import Portfolio,load,tax_book,target_weights,allocate_sales,END

def s(d,gross,gain,venue='STOCK'):
    return dict(date=d,gross=gross,gain=gain,venue=venue)

def test_monthly_exemption_and_no_lookback_loss():
    a=tax_book([s('2023-01-02',10000,3000),s('2023-01-03',10000,3000),s('2023-02-03',50000,20000),s('2023-03-01',5000,-2000),s('2023-04-01',21000,1000),s('2023-05-01',21000,2000)])
    assert [r['tax'] for r in a]==[0,3000,0,0,150]
    assert a[2]['loss_close']==2000 and a[3]['loss_close']==1000
    assert tax_book([s('2023-01-01',20000.01,6000)])[0]['tax']==900

@pytest.mark.parametrize('venue',['ETF','RIGHT'])
def test_rights_etf_no_20k_exemption_and_common_loss_offset(venue):
    a=tax_book([s('2023-01-02',2000,-100),s('2023-02-01',1000,1000,venue)])
    assert a[-1]['tax']==135
    assert tax_book([s('2023-01-01',1000,1000,venue)],False)[0]['tax']==0

def test_gcap_no_loss_pool():
    r=tax_book([s('2023-01-02',2000,-1000),s('2023-01-03',1000,1000,'GCAP')])[0]
    assert r['tax']==150 and r['loss_close']==1000

def test_union_sector_weights_and_minimal_sales():
    names=list('ABCDEF');w=target_weights(names,'R00',lambda t:'setor')
    v={t:20000 for t in 'ABCDE'};sales=allocate_sales(100000/6,v,w,100000)
    assert sum(sales.values())==pytest.approx(100000/6)
    assert all(q==pytest.approx(100000/30) for q in sales.values())
    w=target_weights(names,'B00S',lambda t:'S1' if t=='A' else 'S2')
    assert w['A']==.5 and w['B']==.1
    v={'A':60000,'B':40000};w={'A':.4,'B':.4,'C':.2}
    assert allocate_sales(10000,v,w,100000)=={'A':10000,'B':0}

@pytest.fixture(scope='module')
def data():return load()

def synthetic(data,rule='R00',tax=True):
    d=copy.deepcopy(data);d['selections']['2021|'+rule+'|central']=list('ABCDEF');day='2021-07-01'
    for t in 'ABCDEF':
        d['prices'][t]={day:10,'2021-07-02':10,'2021-07-05':10};d['eligibility'][f'2021|{rule}|central|{t}']=['PASS','fixture'];d['sectors'][f'2021|{t}']='S'
    p=Portfolio(d,2020,rule,'central','B2',tax)
    p.h={t:2000 for t in 'ABCDE'};p.basis={t:10000 for t in 'ABCDE'};p.cash=0
    return p,day

def test_b2_funds_sixth_entrant_with_minimum_partial_sales(data):
    p,day=synthetic(data);p.renew(2021,day)
    # 16,666.67 sale <=20k: realized 8,333.33 gain is exempt.
    assert sum(s['gross'] for s in p.sales)==pytest.approx(100000/6)
    assert p.assessed==0 and not p.available()
    assert len(p.h)==5 and all(q>0 for q in p.h.values())
    p.settle('2021-07-02');assert p.available()==0
    p.settle('2021-07-05');p.execute_plan('2021-07-05')
    assert len(p.h)==6 and sum(p.h.values())*10==pytest.approx(100000)
    assert p.available()==pytest.approx(0,abs=1e-8)

def test_b2_tax_reservation_changes_required_sale_and_preserves_average_basis(data):
    p,day=synthetic(data);p.sales=[s('2021-07-01',15000,10000)];p.assess();p.paid=p.assessed
    oldq=dict(p.h);oldbasis=dict(p.basis);p.renew(2021,day)
    extra=p.sales[1:];assert sum(x['gross'] for x in extra)>100000/6
    assert p.assessed>1500
    for t in p.h:assert p.basis[t]/p.h[t]==pytest.approx(oldbasis[t]/oldq[t])
    assert p.cash==0 and p.available()==0
    p.settle('2021-07-05');p.execute_plan('2021-07-05');assert p.h['F']>0 and p.cash>=-1e-8

def test_no_entry_no_eligible_sale_and_unknown_is_not_fail(data):
    p,day=synthetic(data);p.d['selections']['2021|R00|central']=list('ABCDE')
    p.d['eligibility']['2021|R00|central|A']=['INDETERMINATE','fixture']
    q=dict(p.h);basis=dict(p.basis);p.renew(2021,day)
    assert p.sales==[] and p.assessed==0 and p.h==q and p.basis==basis
    assert p.unknown[0]['ticker']=='A'

def test_sale_lock_and_exact_execution_no_fill(data):
    p,day=synthetic(data);p.sale(day,'A',100,'test')
    with pytest.raises(AssertionError,match='CAIXA_FICTICIO'):p.buy(day,'F',100,'test')
    p.settle('2021-07-05');p.buy('2021-07-05','F',100,'test')
    with pytest.raises(ValueError,match='COTACAO'):p.price('F','2021-07-06')

def test_split_bonus_merger_and_capital_return_basis(data):
    p,day=synthetic(data);p.apply(dict(asset='A',kind='SPLIT',factor=2,event_id='a'),day)
    assert p.h['A']==4000 and p.basis['A']==10000 and not p.sales
    p.apply(dict(asset='A',kind='CONVERSION',legs=[['F',.5]],event_id='b'),day)
    assert p.h['F']==2000 and p.basis['F']==10000 and 'A' not in p.h and not p.sales
    p.apply(dict(asset='F',kind='CASH',amount=1,note='CAPITAL_REDUCTION',event_id='c'),day)
    assert p.h['F']==2200 and p.basis['F']==10000
    p.h['ITSA3']=1000;p.basis['ITSA3']=10000
    p.apply(dict(asset='ITSA3',kind='BONUS',factor=1.05,event_id='d'),'2023-11-28')
    assert p.basis['ITSA3']==pytest.approx(10000+50*17.9172476)
    assert not p.sales

def test_rights_integer_standard_and_fractional_actual_trade(data):
    p=Portfolio(data,2020,'R00','central','B2',True);r=data['rights'][0]
    p.snap[r['record_date']]={'ITSA3':10000};p.cash=0
    p.sell_rights(r,r['sale_date']);a=p.rights[0];parts=json.loads(a['parts'])
    assert a['rights']==139 and [(x['ticker'],x['quantity']) for x in parts]==[('ITSA1',100),('ITSA1F',39)]
    assert a['gross']==pytest.approx(100*2.88+39*3.3)
    p.settle(r['settlement_date'])
    assert p.basis['ITSA3']==pytest.approx(a['gross']*.85)
    assert p.h['ITSA3']==pytest.approx(a['gross']*.85/r['reinvest_price'])
    assert a['discarded']>0

def test_bova_mechanical_frozen_reference_and_operational_d1(data):
    same=Portfolio(data,2020,'BOVA11','central','BH',True,same_close=True).run()
    assert same['gross_before_final']==pytest.approx(184512.11525867715)
    assert same['tax_sales']==pytest.approx(12676.817288801572)
    assert same['final_wealth']==pytest.approx(171835.29796987557)
    operational=Portfolio(data,2020,'BOVA11','central','BH',True).run()
    assert operational['start']=='2020-07-01'
    assert operational['final_wealth']==pytest.approx(170041.54078549848)

@pytest.mark.parametrize('ticker',['CPLE3','SYNE3','ENAT3','PSSA3','TIMP3','VIVT4','SAPR4'])
def test_no_tax_same_close_matches_original_event_engine(data,ticker):
    from scripts.audit_alerts_v12 import m
    from dataclasses import fields
    year=2022 if ticker=='SYNE3' else 2020
    d=copy.deepcopy(data);d['rights']=[];d['selections'][f'{year}|R00|central']=[ticker]
    p=Portfolio(d,year,'R00','central','BH',False,same_close=True)
    expected=Portfolio(d,year,'R00','central','BH',False,same_close=True).run()['gross_before_final']
    args={f.name for f in fields(m.Event)}
    # Limit to the SAME documented event set, excluding generic cash proxies.
    events=[m.Event(**{k:v for k,v in e.items() if k in args}) for e in d['events'] if not e.get('proxy') and e['kind']!='BONUS_OTHER']
    book=m.bridge.PriceBook(d['prices'],d['calendar']);engine=m.Engine(book,events)
    state=engine.initialize(d['windows'][str(year)][0],{ticker:1},capital=100000);engine.advance(state,END)
    assert expected==pytest.approx(engine.result(state,False)['final_value'],abs=1e-6)

def test_2021_proven_valuation_failure_not_indeterminate(data):
    for t in ['ITSA3','ENAT3','SEER3','SBSP3','SLCE3']:
        assert data['eligibility'][f'2021|R03|central|{t}'][0]=='FAIL'
    assert data['eligibility']['2021|B06|central|BBAS3'][0]=='PASS'

ROWS=list(csv.DictReader(open('research/ir_100k_results/results.csv',encoding='utf-8-sig')))
@pytest.mark.parametrize('row',ROWS,ids=lambda r:r['case_id'])
def test_every_published_result_replays_without_database(data,row):
    p=Portfolio(data,int(row['formation']),row['strategy'],row['scenario'],row['policy'],row['ir']=='True',log=False);r=p.run()
    for k in ['final_wealth','tax_sales','annual_turnover_sum','basis_before_final']:assert r[k]==pytest.approx(float(row[k]),abs=1e-7)
    assert not p.h and not p.pending and p.cash==pytest.approx(r['final_wealth'])
    assert p.paid==pytest.approx(p.assessed)
    assert p.min_cash>=-1e-7 and p.assessed>=0
    assert r['max_monthly_dividend']<50000
    if r['formation']==2025:assert r['annual_turnover_sum']==0

def test_complete_factorial_and_no_b1():
    assert len(ROWS)==372 and len({r['case_id'] for r in ROWS})==372
    assert set(r['policy'] for r in ROWS)=={'A','B2','BH'}
    for year in range(2020,2026):
        rs=[r for r in ROWS if int(r['formation'])==year and r['scenario']=='central']
        assert len(rs)==38

def test_same_day_reinvestment_does_not_disguise_old_cost_as_daytrade(data):
    p,day=synthetic(data);p.cash=1000;p.buy(day,'A',1000,'DIVIDEND')
    p.sale(day,'A',200,'PARTIAL')
    dt=[r for r in p.sales if r['venue']=='DAYTRADE'];common=[r for r in p.sales if r['venue']=='STOCK']
    assert dt[0]['quantity']==100 and dt[0]['gain']==0
    assert common[0]['quantity']==100 and common[0]['gain']==500
    assert p.basis['A']==9500 and p.h['A']==1900

def test_daytrade_loss_separate_from_common():
    r=tax_book([s('2024-01-02',30000,-1000),s('2024-01-03',10000,1000,'DAYTRADE')])[0]
    assert r['tax']==200 and r['loss_close']==1000

def test_axia7_bonus_adds_new_security_and_declared_cost(data):
    p=Portfolio(data,2025,'B00','central','BH',True);p.h={'AXIA3':100};p.basis={'AXIA3':4000};p.snap['2025-12-19']={'AXIA3':100}
    e=next(e for e in data['events'] if e['event_id']=='IR_AXIA_BONUS');p.apply(e,e['date'])
    assert p.h['AXIA3']==100 and p.basis['AXIA3']==4000
    assert p.h['AXIA7']==pytest.approx(26.28378881074)
    assert p.basis['AXIA7']==pytest.approx(26.28378881074*49.44)
    assert p.sales==[] and p.assessed==0

def test_b06_does_not_buy_retained_above_cap(data):
    p,day=synthetic(data,rule='B06');p.d['selections']['2021|B06|central']=list('BCD');p.cash=10000
    p.h['A']=100;p.basis['A']=500;p.h['E']=100;p.basis['E']=500
    p.renew(2021,day);p.settle('2021-07-05');p.execute_plan('2021-07-05')
    assert p.h['A']==100 and p.h['E']==100
    assert not p.sales

def test_independent_original_engine_actual_100k_parity():
    rows=list(csv.DictReader(open('research/ir_100k_results/old_engine_parity_100k.csv',encoding='utf-8-sig')))
    assert len(rows)==18 and all(r['status']=='PASS' and abs(float(r['difference']))<1e-6 for r in rows)

def test_sensitivities_keep_only_same_cases_and_paired_decomposition():
    rows=list(csv.DictReader(open('research/ir_100k_results/sensitivities.csv',encoding='utf-8-sig')))
    assert len(rows)==372*7 and {r['case_id'] for r in rows}=={r['case_id'] for r in ROWS}
    for r in csv.DictReader(open('research/ir_100k_results/decomposition.csv',encoding='utf-8-sig')):
        assert float(r['B2_minus_A_net'])==pytest.approx(float(r['composition_and_execution_effect'])+float(r['differential_tax_effect']),abs=1e-8)
