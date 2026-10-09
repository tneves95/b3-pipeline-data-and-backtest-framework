import json
import math
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from monthly_tax_accounting import Fiscal, tax_book, due_date
from monthly_tax_freeze import TAX, POLICY
from b00s_variants import read


def sale(d,t,gross,gain,kind='STOCK'):
    return dict(date=d,ticker=t,gross_value=gross,realized_gain_loss=gain,asset_tax_type=kind)


def test_average_cost_three_deposits_then_partial_sale():
    f=Fiscal('synthetic',{},[])
    for d,q,p in [('2020-01-02',10,10),('2020-02-03',20,20),('2020-03-02',30,30)]:
        f.buy(d,'a','A',q,p,'DEPOSIT')
    f.sell('2020-06-30','a','A',15,40,'REVIEW')
    assert f.sales[-1]['cost_removed']==pytest.approx(350)
    assert f.sales[-1]['realized_gain_loss']==pytest.approx(250)
    assert f.q['A']==45 and f.basis['A']==pytest.approx(1050)


@pytest.mark.parametrize('gross,tax',[(19999,0),(20000,0),(20001,1500)])
def test_monthly_exemption_aggregates_different_tickers(gross,tax):
    rows=[sale('2020-06-01','A',gross/2,5000),sale('2020-06-30','B',gross/2,5000)]
    r=tax_book(rows)[0]
    assert r['assessed_tax']==tax
    assert r['stock_sales']==gross
    assert r['ordinary_irrf']+r['darf_6015']==pytest.approx(tax)


def test_exempt_gains_do_not_consume_prior_loss_and_loss_is_prospective():
    rows=[sale('2020-01-02','A',30000,1000),sale('2020-02-03','A',10000,-500),
          sale('2020-03-02','A',10000,1000),sale('2020-04-01','A',30000,800)]
    a,b,c,d=tax_book(rows)
    assert a['common_tax']==150 and b['common_loss_close']==500
    assert c['common_loss_close']==500 and c['common_tax']==0
    assert d['common_taxable_base']==300 and d['common_tax']==45


def test_right_and_bdr_are_not_stock_exempt_and_losses_are_separate_from_daytrade():
    rows=[sale('2020-01-02','A',100,-100,'DAYTRADE'),sale('2020-02-03','XPBR31',100,80,'BDR'),
          sale('2020-02-03','ITSA1',30,30,'RIGHT')]
    a,b=tax_book(rows)
    assert b['common_tax']==pytest.approx(16.5)
    assert b['daytrade_loss_close']==100


def test_irrf_is_credit_not_second_tax_and_unused_credit_is_not_cash_refund():
    a,b,c=tax_book([sale('2020-01-02','A',40000,-100),sale('2020-02-03','A',30000,1100),
                    sale('2021-01-04','A',40000,2000)])
    assert a['ordinary_irrf']==2 and a['ordinary_irrf_credit_close']==2
    assert b['common_tax']==150 and b['ordinary_irrf_credit_used']==3.5
    assert b['darf_6015']==146.5
    x,y=tax_book([sale('2020-01-02','A',40000,-100),sale('2021-01-04','A',40000,2000)])
    assert y['prior_year_irrf_exported_DIRPF']==2
    assert y['ordinary_irrf_credit_open']==0


def test_same_day_matching_uses_purchase_cost_and_preserves_old_basis():
    f=Fiscal('synthetic',{},[])
    f.buy('2020-01-02','a','A',100,10,'INITIAL')
    f.buy('2020-06-30','a','A',5,30,'REINVEST')
    f.sell('2020-06-30','a','A',20,30,'REVIEW')
    assert [r['asset_tax_type'] for r in f.sales]==['DAYTRADE','STOCK']
    assert f.sales[0]['realized_gain_loss']==0
    assert f.sales[1]['cost_removed']==150
    assert f.basis['A']==850 and f.q['A']==85


def test_daytrade_positive_gain_rate_irrf_and_loss_carry():
    a,b=tax_book([sale('2020-01-02','A',1000,-100,'DAYTRADE'),sale('2020-02-03','A',3000,300,'DAYTRADE')])
    assert b['daytrade_tax']==40
    assert b['daytrade_irrf']==3 and b['darf_6015']==37


def test_darf_next_month_minimum_and_cash_reserve():
    f=Fiscal('synthetic',{},['2020-01-31','2020-02-28','2020-03-31'])
    f.sales=[sale('2020-01-02','R',20,20,'RIGHT')]
    assert f.assess('2020-01-31',month_closed=True)==0
    assert f.liability==3 and f.available(20)==17
    assert f.payment('2020-02-28',20)==0
    f.sales.append(sale('2020-02-03','R',60,60,'RIGHT'));f.assess('2020-02-28',month_closed=True)
    assert f.liability==12 and f.payment('2020-03-31',12)==12
    assert f.liability==0
    assert due_date('2026-06',[])=='2026-07-31'


def test_insufficient_reserve_is_rejected_without_invented_contribution():
    f=Fiscal('synthetic',{},['2020-02-28'])
    f.sales=[sale('2020-01-02','R',1000,1000,'RIGHT')];f.assess('2020-01-31',month_closed=True)
    with pytest.raises(ValueError,match='UNFUNDED_RESERVE'):f.available(149)
    with pytest.raises(ValueError,match='DARF_UNFUNDED'):f.payment('2020-02-28',149)


def test_potential_exemption_tax_is_reserved_until_month_closes():
    f=Fiscal('synthetic',{},[]);f.sales=[sale('2020-06-01','A',19000,10000)]
    f.assess('2020-06-01');assert f.liability==0 and f.precaution==1500
    f.assess('2020-06-30',month_closed=True);assert f.precaution==0


@pytest.mark.parametrize('kind,unit,market,expected',[
    ('STOCK_SPLIT',0,False,100),('BONUS_SHARES',12,False,220),
    ('BONUS_SHARES',None,False,100),('BONUS_SHARES',None,True,300)])
def test_split_declared_bonus_and_unknown_cost_sensitivity(kind,unit,market,expected):
    ev=dict(economic_kind='SHARES',share_kind=kind,unit_basis=unit,original_type='',amount_basis='UNKNOWN')
    f=Fiscal('synthetic',{'E':ev},[],bonus_market=market)
    f.buy('2020-01-02','a','A',10,10,'INITIAL')
    e=dict(id='E',ticker='A',kind='SHARES',factor=2,source='synthetic')
    after,cash=f.corporate('2020-02-03',{'a':{'A':10}},{'a':{'A':20}},[e],{('A','2020-02-03'):20},0)
    f.verify(after);assert f.basis['A']==expected and cash==0


def test_final_liquidation_is_separate_and_uses_actual_remaining_cost():
    f=Fiscal('synthetic',{},[]);f.buy('2020-01-02','a','A',1000,10,'INITIAL')
    end=f.final_liquidation('2026-06-30',{'a':{'A':1000}},{('A','2026-06-30'):30},0)
    assert end['wealth']==27000 and end['tax_increment']==3000
    assert f.q['A']==1000 and not f.sales and f.liability==0


def test_frozen_policy_and_replayed_five_books_exist():
    assert json.loads((TAX/'inputs/tax_policy_freeze.json').read_text())==POLICY
    v=json.loads((TAX/'validation.json').read_text())['zero_tax_checks']
    assert len(v)==5 and all(r['status']=='PASS' and r['deposits']==144 and r['external_capital']==460000 for r in v)


def test_calculated_books_keep_bh_and_june_sale_constraints_and_cash():
    ops=read(TAX/'taxed_operations.csv');rows=read(TAX/'monthly_taxed_wealth.csv')
    for r in ops:
        if r['side']=='SELL':
            assert r['portfolio'] not in ['BH padrão','BESST-10 BH']
            assert r['date'][5:7]=='06'
    for r in rows:
        assert float(r['cash'])>=-1e-7
        assert float(r['cash_available'])>=0
        assert float(r['tax_liability'])<=float(r['tax_restricted_cash'])+1e-7


def test_main_and_final_ranking_are_actual_calculated_results():
    rows=[r for r in read(TAX/'consolidated_tax.csv') if r['mode']=='CG_ONLY']
    assert len(rows)==5
    for r in rows:
        assert float(r['external_capital'])==460000 and int(r['external_contributions'])==144
        assert float(r['liquidation_wealth'])<float(r['final_wealth'])<=float(r['gross_wealth'])
        assert float(r['liquidation_tax'])==pytest.approx(float(r['final_wealth'])-float(r['liquidation_wealth']))
