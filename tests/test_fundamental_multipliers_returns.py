"""Economic regressions: as-of prices, entitlements, exits and PIT statement versions."""
import json
from pathlib import Path
import sqlite3
import zipfile

import pandas as pd
import pytest

from research.fundamental_multipliers_pilot.filings import collapse_facts, monetary_value, parse_original
from research.fundamental_multipliers_pilot.quotes import QuoteBook, collect_endpoint_quotes
from research.fundamental_multipliers_pilot.returns import apply_events, replay, evaluate
from research.fundamental_multipliers_pilot.round2 import assess_predictive_gate


def quote_record(day, close, isin='BRTESTACNOR1', ticker='TEST3', bdi='08'):
    raw=bytearray(b' '*245)
    for start,end,value in [(0,2,b'01'),(2,10,day.replace('-','').encode()),(10,12,bdi.encode()),
            (12,24,ticker.ljust(12).encode()),(24,27,b'010'),(108,121,f'{int(close*100):013d}'.encode()),
            (210,217,b'0000001'),(230,242,isin.encode())]:
        raw[start:end]=value
    return bytes(raw)+b'\n'


def test_asof_extract_handles_unsorted_archives_and_future_trades(tmp_path):
    (tmp_path/'data/raw').mkdir(parents=True)
    with zipfile.ZipFile(tmp_path/'data/raw/COTAHIST_A2022.ZIP','w') as z:
        z.writestr('quotes.txt',quote_record('2022-06-30',9)+quote_record('2022-06-27',7)+
                   quote_record('2022-06-28',8)+quote_record('2022-06-01',6))
    q,calendar=collect_endpoint_quotes(tmp_path,['2022-06-28','2022-06-30'],years=[2022])
    assert q.set_index('cutoff').loc['2022-06-28','date']=='2022-06-28'
    assert q.set_index('cutoff').loc['2022-06-30','close']==9
    assert calendar==['2022-06-01','2022-06-27','2022-06-28','2022-06-30']


def test_simultaneous_bonus_and_dividend_uses_old_entitlement():
    e=[dict(id='bonus',ticker='A',kind='SHARES',factor=2),dict(id='cash',ticker='A',kind='DISTRIBUTION',amount=2)]
    units,cash=apply_events({'A':1},0,e,lambda t:10)
    assert units=={'A':2.2};assert cash==0


def test_detached_right_settles_on_same_day_without_external_subscription_cash():
    e=[dict(id='right',ticker='A',kind='RIGHT',successor='R',ratio=.3),
       dict(id='settle',ticker='R',kind='RIGHT_REINVEST',successor='A')]
    units,cash=apply_events({'A':2},0,e,lambda t:{'A':10,'R':2}[t])
    assert units['A']==pytest.approx(2.12);assert 'R' not in units;assert cash==0


def test_compulsory_redemption_keeps_nominal_cash_to_target():
    units,cash=apply_events({'A':2},0,[dict(id='exit',ticker='A',kind='REDEMPTION',amount=7)],lambda t:None)
    assert units=={};assert cash==14
    units,cash=apply_events({'A':2},0,[dict(id='merge',ticker='A',kind='CONVERSION',legs=[['B',.5]],amount=3)],lambda t:None)
    assert units=={'B':1};assert cash==6


def test_unexplained_security_disappearance_is_never_zero_or_last_quote_return():
    class Book:
        calendar=['2020-06-30','2023-06-30']
        def trade(self,ticker,day,**kw):
            if day=='2023-06-30':raise ValueError('STALE_OR_SUSPENDED_QUOTE')
            return dict(close=10,isin='I',date=day)
    with pytest.raises(ValueError,match='STALE'):
        replay(Book(),'A','I','2020-06-30','2023-06-30',[])
    r,ledger,end=replay(Book(),'A','I','2020-06-30','2023-06-30',
        [dict(id='exit',ticker='A',kind='REDEMPTION',ex_date='2021-06-30',amount=4)])
    assert r['wealth_multiple']==pytest.approx(.4)
    assert r['nominal_total_return']==pytest.approx(-.6)


def test_unverified_zero_recovery_and_duplicate_events_fail():
    e=dict(id='bankruptcy',ticker='A',kind='EXTINGUISHMENT')
    with pytest.raises(ValueError,match='UNDOCUMENTED_ZERO'):
        apply_events({'A':1},0,[e],lambda t:1)
    with pytest.raises(ValueError,match='DUPLICATE'):
        apply_events({'A':1},0,[e,e],lambda t:1)


def test_no_skipped_events_is_not_a_return_certificate(tmp_path):
    panel=pd.DataFrame([dict(cnpj='001',formation_date='2020-06-30',company_representative=True,
        statement_status='AVAILABLE_AT_CUTOFF',financial_sector=False,sector='X',identity_status='UNIQUE_MAP_RECEIPT_UNAUDITED')])
    readiness=pd.DataFrame([dict(cnpj='001',ticker='A',isin='I',formation_date='2020-06-30',horizon_years=3,
        calendar_endpoint='2023-06-30',calendar_complete=True,same_security_near_endpoint=True)])
    r=evaluate(panel,readiness,None,[],[],pd.DataFrame(columns=['isin_code','event_date']),tmp_path)
    assert r.iloc[0].status=='UNCERTIFIED'
    assert 'COMPLETE_EVENT_CATALOG' in r.iloc[0].exclusion_causes


def legacy_dfp(path,version=1,scale='2'):
    document=f'<Documento><NumeroCnpjCompanhiaAberta>001</NumeroCnpjCompanhiaAberta><CodigoEscalaMoeda>{scale}</CodigoEscalaMoeda><DataReferenciaDocumento>2019-12-31T00:00:00</DataReferenciaDocumento><NumeroVersaoDocumento>{version}</NumeroVersaoDocumento></Documento>'
    periods='<Periods><P><NumeroIdentificacaoPeriodo>1</NumeroIdentificacaoPeriodo><DataInicioPeriodo>2019-01-01</DataInicioPeriodo><DataFimPeriodo>2019-12-31</DataFimPeriodo></P><P><NumeroIdentificacaoPeriodo>2</NumeroIdentificacaoPeriodo><DataInicioPeriodo>2018-01-01</DataInicioPeriodo><DataFimPeriodo>2018-12-31</DataFimPeriodo></P></Periods>'
    accounts='<Rows><Row><PlanoConta><NumeroConta>3.11</NumeroConta><VersaoPlanoConta><CodigoTipoInformacaoFinanceira>2</CodigoTipoInformacaoFinanceira></VersaoPlanoConta></PlanoConta><DescricaoConta1>Lucro/Prejuízo do Período</DescricaoConta1><ValorConta1>-1000.5</ValorConta1><ValorConta2>99999</ValorConta2></Row></Rows>'
    with zipfile.ZipFile(path,'w') as z:
        for n,v in [('Documento.xml',document),('PeriodoDemonstracaoFinanceira.xml',periods),('InfoFinaDFin.xml',accounts)]:z.writestr(n,v)


def test_recovery_preserves_original_version_loss_scale_and_reference(tmp_path):
    p=tmp_path/'dfp.zip';legacy_dfp(p,scale='1');required=dict(cnpj='001',version=1,period_end='2019-12-31')
    facts=parse_original(p,required);values,perimeter=collapse_facts(facts)
    assert values['net_income']==pytest.approx(-1.0005);assert perimeter=='con'
    assert values['ebit'] is None
    with pytest.raises(ValueError,match='version mismatch'):parse_original(p,dict(required,version=2))
    with pytest.raises(ValueError,match='reference mismatch'):parse_original(p,dict(required,period_end='2018-12-31'))


def test_brazilian_modern_xml_format_and_consistent_statement_perimeter():
    assert monetary_value('5.890.219',brazilian=True)==5890219
    assert monetary_value('-1.234,56',brazilian=True)==-1234.56
    values,scope=collapse_facts([dict(metric='net_income',perimeter='con',value=-2),
                               dict(metric='operating_cash_flow',perimeter='ind',value=10)])
    assert scope=='con';assert values['operating_cash_flow'] is None
    with pytest.raises(ValueError,match='Ambiguous'):
        collapse_facts([dict(metric='net_income',perimeter='con',value=1),dict(metric='net_income',perimeter='con',value=2)])


def test_modern_original_parser_keeps_exact_period_version_and_ebit(tmp_path):
    p=tmp_path/'modern.zip'
    xml='''<XmlDemonstracoesFinanceiras><DadosEmpresa><CnpjEmpresa>001</CnpjEmpresa></DadosEmpresa>
    <Documento><VersaoDocumento>2</VersaoDocumento></Documento><DadosDFP><DataReferencia>31/12/2022</DataReferencia>
    <EscalaMoeda>2</EscalaMoeda><Formulario><DfConsolidadas><DRE>
    <Conta><CodigoConta>3.11</CodigoConta><DescricaoConta>Lucro/Prejuízo do Período</DescricaoConta><UltimoExercicio>-1.234.567</UltimoExercicio><PenultimoExercicio>999.999.999</PenultimoExercicio></Conta>
    <Conta><CodigoConta>3.05</CodigoConta><DescricaoConta>Resultado Antes do Resultado Financeiro e dos Tributos</DescricaoConta><UltimoExercicio>2.000.000</UltimoExercicio></Conta>
    </DRE></DfConsolidadas></Formulario></DadosDFP></XmlDemonstracoesFinanceiras>'''
    with zipfile.ZipFile(p,'w') as z:z.writestr('DFP.xml',xml)
    required=dict(cnpj='001',version=2,period_end='2022-12-31')
    values,_=collapse_facts(parse_original(p,required))
    assert values['net_income']==-1234567;assert values['ebit']==2000000
    with pytest.raises(ValueError,match='version mismatch'):parse_original(p,dict(required,version=1))


def test_quote_overlay_restores_distressed_trade_without_modifying_source(tmp_path):
    source=tmp_path/'base.sqlite';overlay=tmp_path/'overlay.sqlite'
    c=sqlite3.connect(source);c.execute('create table prices(ticker,isin_code,date,close)')
    c.execute("insert into prices values ('A','OLD','2020-06-30',10)");c.commit();c.close()
    before=source.read_bytes()
    c=sqlite3.connect(overlay);c.execute('create table quotes(ticker,isin,date,close)')
    c.execute("insert into quotes values ('A','OLD','2023-06-30',1)");c.commit();c.close()
    book=QuoteBook(source,overlay,['2020-06-30','2023-06-30'])
    assert book.trade('A','2023-06-30',isin='OLD')['close']==1
    with pytest.raises(ValueError,match='IDENTITY'):book.trade('A','2023-06-30',isin='NEW')
    book.close();assert source.read_bytes()==before


def test_company_and_class_conflict_cannot_receive_a_ticker_based_certificate(tmp_path):
    panel=pd.DataFrame([dict(cnpj='002',formation_date='2020-06-30',company_representative=True,
        statement_status='AVAILABLE_AT_CUTOFF',financial_sector=False,sector='X',identity_status='UNIQUE_MAP_RECEIPT_UNAUDITED')])
    readiness=pd.DataFrame([dict(cnpj='002',ticker='A',isin='NEW',formation_date='2020-06-30',horizon_years=3,
        calendar_endpoint='2023-06-30',calendar_complete=True,same_security_near_endpoint=True)])
    scopes=[dict(ticker='A',cnpj='001',isin='OLD',certified=True,start='2014-01-01',end='2026-01-01')]
    r=evaluate(panel,readiness,None,[],scopes,pd.DataFrame(columns=['isin_code','event_date']),tmp_path)
    assert r.iloc[0].status=='UNCERTIFIED'
    assert 'HISTORICAL_ISSUER_OR_CLASS_CONFLICT' in r.iloc[0].exclusion_causes


def test_predictive_gate_retains_distressed_and_unmapped_formation_denominator():
    # Even 99% coverage and 100 distinct companies cannot excuse known unresolved losses.
    matrix=pd.DataFrame([dict(cnpj=str(i),year=2019,horizon_years=3,
        calendar_complete=True,status='CERTIFIED') for i in range(100)]+[
        dict(cnpj='distressed',year=2019,horizon_years=3,calendar_complete=True,status='CENSORED')])
    gate=assess_predictive_gate(matrix,0)
    assert not gate['passed']
    assert gate['mapped_complete_observations']==101
    assert any('distressed' in r for r in gate['reasons'])
    gate=assess_predictive_gate(matrix.iloc[:100],1)
    assert not gate['passed']
    assert any('historical formation securities' in r for r in gate['reasons'])
