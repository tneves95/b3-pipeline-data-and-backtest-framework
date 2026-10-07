#!/usr/bin/env python3
"""Directed v13 alternatives on immutable v9/v11.2/v12 inputs.

Run from repository root. Uses the unchanged v6 engine and nominal local prices.
No selection changes, fictional predecessor prices, database writes or new funds.
The policy remains a fractional, gross, ex-close theoretical index. Actual forced
auction of odd lots is a documented limitation, not silently presented as traded.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from datetime import date
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
sys.path.insert(0, str(Path.cwd()))
from scripts.audit_alerts_v12 import BASE, OUT as V12, context, dump, m, rights, sha
from scripts.audit_graham_v11_sources import cotahist_prices

INPUT = Path('research/graham_v6_comparison/audit_v13_inputs')
OUT = Path('research/graham_v6_comparison/checkpoint_v13_2026_10_07')
FAMILIES = {'PSSA3':'PSSA3','TIMP3':'TIM','TIMS3':'TIM',
            'VIVT4':'VIVT','VIVT3':'VIVT','SAPR4':'SAPR4'}
ISINS = {'PSSA3':'BRPSSAACNOR7','TIMP3':'BRTIMPACNOR1','TIMS3':'BRTIMSACNOR5',
         'VIVT4':'BRVIVTACNPR7','VIVT3':'BRVIVTACNOR0','SAPR4':'BRSAPRACNPR6'}
EXPERIMENTS = ('v9','v12_partial','isolated_PSSA3','isolated_TIM','isolated_VIVT',
               'isolated_SAPR4','v13_four','v12_plus_v13')
SENSITIVITIES = ('cash_minus20','cash_plus20','capital_keep_cash',
                 'pssa_initial_notice','no_capital_distributions','no_cash')


def load_events():
    sources={r['id']:r for r in json.loads((INPUT/'sources_manifest.json').read_text())}
    facts=json.loads((INPUT/'cash_facts.json').read_text())
    events=[m.Event(f['event_id'], f['ex_date'], 'CASH', f['ticker'], ';'.join(f['source_urls']),
                    record_date=f['record_date'], amount=f['amount'],
                    note=f['kind']+'; bruto nominal; pagamento='+f['pay_date_or_deadline']+'; '+f['note']) for f in facts]
    for f in json.loads((INPUT/'structural_facts.json').read_text()):
        args={k:v for k,v in f.items() if k!='source_ids'}
        args['source']=';'.join(sources[i]['url'] for i in f['source_ids'])
        args['order']=10
        events.append(m.Event(**args))
    return events, facts, sources


def event_book(book):
    # These six securities have independently checked nominal SQLite quotes.
    # expand_with_sqlite preserves inherited entries; no synthetic quote is made.
    return m.bridge.expand_with_sqlite(book, set(FAMILIES))


def simulate(book, events, ticker, start, end, capital=10000):
    eng=m.Engine(book,events)  # coverage is intentionally not labelled RECONCILED
    st=eng.initialize(start,{ticker:1},capital)
    eng.advance(st,end)
    result=eng.result(st,require_complete=False)
    if end>='2020-10-13':assert 'TIMP3' not in st.holdings
    if end>='2020-11-23':assert 'VIVT4' not in st.holdings
    assert len(st.applied)==len(set(st.applied)) and st.cash>=0
    for line in st.ledger:
        if line['kind'] in ('MERGER','CONVERSION'):
            q=line['details']['consumed'];assert line['asset'] not in line['after']
            for a,f in line['details']['legs']:
                assert math.isclose(line['after'][a]-line['before'].get(a,0),q*f,abs_tol=1e-9)
            assert line['cash_after']==line['cash_before']  # both verified migrations have no cash leg
    return result, st


def replacement(row, experiment, bound='central'):
    old = float(row['v9_return' if bound=='central' else 'v9_cash_'+bound])
    use12=experiment in ('v12_partial','v12_plus_v13')
    use13=experiment in ('v13_four','v12_plus_v13') or experiment=='isolated_'+FAMILIES.get(row['ticker'],'?')
    if use13 and row.get('v13_return','')!='':return float(row['v13_return'])
    if use12 and row.get('alternative_return','')!='':return float(row['alternative_return'])
    return old


def portfolio_return(rows, experiment, bound='central'):
    return math.fsum(float(r['weight'])*replacement(r,experiment,bound) for r in rows)


def chained_returns(returns):
    if not returns:raise ValueError('Empty cohort')
    return math.prod(1+r for r in returns)-1


def daily_metrics(nav):
    if len(nav)<2 or any(r['nav'] is None for r in nav):
        return dict(daily_status='INCOMPLETE_NO_METRICS',daily_observations=len(nav),volatility_252='',max_drawdown='')
    vals=[r['nav'] for r in nav];daily=[b/a-1 for a,b in zip(vals,vals[1:])]
    high=vals[0];dd=0
    for v in vals:high=max(high,v);dd=min(dd,v/high-1)
    return dict(daily_status='FULL_NOMINAL_EVENT_PATH',daily_observations=len(vals),
                volatility_252=statistics.stdev(daily)*math.sqrt(252),max_drawdown=dd)


def main(out, raw_dir=None):
    out.mkdir(parents=True,exist_ok=True)
    lb,le,_=m.bridge.load_legacy()
    assert all(x['status']=='OK' for x in m.bridge.legacy_parity(lb,le))
    book,_,_,_,_=context();book=event_book(book)
    events,facts,sources=load_events()
    original=m.read_csv(V12/'barsi_posicao_ano_1212.csv')
    cases=sorted({(int(r['year']),r['mechanism'],r['ticker'],r['start'],r['end']) for r in original if r['ticker'] in FAMILIES})
    results={};states={};case_rows=[];ledgers=[];sensitivity=[];quote_targets=set()
    # Stress cash recognition in the four reconstructed exposures, not all v9.
    # +/-20% cash is a named deterministic scenario, not a statistical interval.
    for y,mode,t,start,end in cases:
        result,state=simulate(book,events,t,start,end)
        key=(y,mode,t);results[key]=result['return'];states[key]=state
        cid=f'{t}_{start}_{end}'
        case_rows.append(dict(case_id=cid,year=y,mechanism=mode,ticker=t,start=start,end=end,
                              event_return=result['return'],final_value=result['final_value'],
                              final_holdings=json.dumps(result['holdings'],sort_keys=True),cash=result['cash'],
                              applied_economic_events=len(state.ledger)-1,coverage='PROVISIONAL_EVENT_INDEX',
                              **daily_metrics(state.nav)))
        for line in state.ledger[1:]:
            ledgers.append(dict(case_id=cid,**line))
            quote_targets.update((a,line['date']) for a in line['after'])
            quote_targets.update((a,book.previous_session(line['date'])) for a in line['before'])
        quote_targets.add((t,start));quote_targets.update((a,end) for a in state.holdings)
        # Mechanical consistency when processing the same path incrementally.
        eng=m.Engine(book,events);incremental=eng.initialize(start,{t:1})
        first_end=m.bridge.WINDOWS[y][1];eng.advance(incremental,first_end)
        annual,_=simulate(book,events,t,start,first_end)
        assert math.isclose(eng.result(incremental,False)['return'],annual['return'],abs_tol=1e-12)
        eng.advance(incremental,end)
        assert math.isclose(eng.result(incremental,False)['return'],result['return'],abs_tol=1e-12)
        for label in SENSITIVITIES:
            altered=[]
            for e in events:
                iscapital=e.kind=='CASH' and e.note.startswith('CAPITAL_REDUCTION')
                if label=='no_cash' and e.kind=='CASH':continue
                if label=='no_capital_distributions' and iscapital:continue
                if label in ('cash_minus20','cash_plus20') and e.kind=='CASH':
                    e=replace(e,amount=e.amount*(.8 if label=='cash_minus20' else 1.2))
                if label=='capital_keep_cash' and iscapital:e=replace(e,reinvest='KEEP_CASH')
                if label=='pssa_initial_notice' and e.event_id=='V13_PSSA3_2026-03-30_JCP_020':
                    e=replace(e,amount=.54228396511)
                altered.append(e)
            alt,_=simulate(book,altered,t,start,end)
            sensitivity.append(dict(year=y,mechanism=mode,ticker=t,sensitivity=label,event_return=alt['return'],
                                    central_return=result['return'],delta_pp=100*(alt['return']-result['return'])))
    dump(out,'ativos_calculados_v13.csv',case_rows)
    dump(out,'sensibilidades_ativos_v13.csv',sensitivity)
    (out/'ledger_4_ativos.json.gz').write_bytes(gzip.compress(json.dumps(ledgers,ensure_ascii=False,sort_keys=True).encode(),mtime=0))
    position_rows=[]
    for r in original:
        r=dict(r);key=(int(r['year']),r['mechanism'],r['ticker'])
        alt=results.get(key,'');r['v13_return']=alt
        r['v13_weighted_delta_pp']=100*float(r['weight'])*(alt-float(r['v9_return'])) if alt!='' else ''
        r['v13_exposure']=alt!='';r['v13_status']='CALCULADO_MOTOR_V6_FRACIONARIO_PROVISORIO' if alt!='' else 'PRESERVADO_V9_OU_CENARIO_V12'
        position_rows.append(r)
    dump(out,'alternativas_barsi_v13_por_posicao.csv',position_rows)
    portfolios=[];coverage=[]
    grouped=defaultdict(list)
    for r in position_rows:grouped[int(r['year']),r['strategy'],r['scenario'],r['mechanism']].append(r)
    for (y,s,sc,mode),rs in sorted(grouped.items()):
        assert math.isclose(sum(float(r['weight']) for r in rs),1,abs_tol=1e-10)
        base=portfolio_return(rs,'v9');wealth=1+base
        for expt in EXPERIMENTS:
            central=portfolio_return(rs,expt)
            portfolios.append(dict(year=y,strategy=s,scenario=sc,mechanism=mode,experiment=expt,
                                   central_return=central,low_return=portfolio_return(rs,expt,'low'),
                                   high_return=portfolio_return(rs,expt,'high'),delta_vs_v9_pp=100*(central-base)))
        def share(predicate):return 100*sum(float(r['weight'])*(1+float(r['v9_return'])) for r in rs if predicate(r))/wealth
        old=lambda r:r['event_calculation_available']=='True'
        new=lambda r:old(r) or r['v13_return']!=''
        coverage.append(dict(year=y,strategy=s,scenario=sc,mechanism=mode,total_position_cases=len(rs),
                             new_reconstructed_position_cases=sum(r['v13_return']!='' for r in rs),
                             event_calculation_position_cases=sum(new(r) for r in rs),
                             v12_event_wealth_pct=share(old),v13_event_wealth_pct=share(new),
                             remaining_approximate_wealth_pct=share(lambda r:not new(r)),
                             denominator='PATRIMONIO_FINAL_V9_INCLUI_CAIXA',fully_certified=False))
    dump(out,'comparacao_anuais_manutencao_v13.csv',portfolios)
    dump(out,'cobertura_patrimonial_v13.csv',coverage)
    cohorts=[]
    for y in m.bridge.WINDOWS:
        for s in ('B00','B00S','B06','B06S'):
            for sc in ('central','conservative'):
                for mode in ('maintain','renew'):
                    for expt in EXPERIMENTS:
                        selected=[p for p in portfolios if p['strategy']==s and p['scenario']==sc and p['experiment']==expt and
                                  (p['year']==y and p['mechanism']=='maintain' if mode=='maintain' else p['year']>=y and p['mechanism']=='annual')]
                        central=chained_returns([p['central_return'] for p in selected])
                        low=chained_returns([p['low_return'] for p in selected]);high=chained_returns([p['high_return'] for p in selected])
                        start=m.bridge.WINDOWS[y][0];years=(date.fromisoformat(m.END)-date.fromisoformat(start)).days/365.25
                        cohorts.append(dict(start_year=y,strategy=s,scenario=sc,mechanism=mode,experiment=expt,
                                            central_return=central,low_return=low,high_return=high,final_value=10000*(1+central),
                                            cagr=(1+central)**(1/years)-1,periods=len(selected),initial_capital=10000,
                                            external_contributions=0,scope='SUBSTITUICAO_PARCIAL; SEM_CERTIFICACAO_INTEGRAL'))
    lookup={(r['start_year'],r['strategy'],r['scenario'],r['mechanism'],r['experiment']):r for r in cohorts}
    for r in cohorts:
        base=lookup[r['start_year'],r['strategy'],r['scenario'],r['mechanism'],'v9']['central_return']
        r['delta_vs_v9_pp']=100*(r['central_return']-base)
    dump(out,'comparacao_coortes_v13.csv',cohorts)
    # Portfolio-level stress: recompute annual factors before chaining renewal.
    stressed=[];smap={(r['year'],r['mechanism'],r['ticker'],r['sensitivity']):r['event_return'] for r in sensitivity}
    for r in cohorts:
        if r['experiment']!='v12_plus_v13':continue
        y,s,sc,mode=r['start_year'],r['strategy'],r['scenario'],r['mechanism']
        for label in SENSITIVITIES:
            period_returns=[]
            bound='low' if label=='cash_minus20' else 'high' if label=='cash_plus20' else 'central'
            for yr in [y] if mode=='maintain' else range(y,2026):
                pm='maintain' if mode=='maintain' else 'annual';rs=grouped[yr,s,sc,pm]
                period_returns.append(sum(float(p['weight'])*(smap[yr,pm,p['ticker'],label] if p['v13_return']!='' else replacement(p,'v12_plus_v13',bound)) for p in rs))
            val=chained_returns(period_returns)
            stressed.append(dict(start_year=y,strategy=s,scenario=sc,mechanism=mode,sensitivity=label,return_value=val,
                                 central_return=r['central_return'],delta_pp=100*(val-r['central_return']),residual_v9_bound=bound))
    dump(out,'sensibilidades_carteiras_v13.csv',stressed)
    # Evidence matrix distinguishes a frozen RI table from exact verified notices.
    matrix=[]
    for group in ['PSSA3','TIM','VIVT','SAPR4']:
        fs=[f for f in facts if FAMILIES[f['ticker']]==group]
        es=[e for e in events if FAMILIES[e.asset]==group]
        source_ids=set(i for f in fs for i in f['source_ids'])
        sf=[f for f in json.loads((INPUT/'structural_facts.json').read_text()) if FAMILIES[f['asset']]==group]
        source_ids.update(i for f in sf for i in f['source_ids'])
        if group=='SAPR4':source_ids.add('SAPR_ZERO26')
        if group=='PSSA3':source_ids.add('PSSA_2021-05-17_7')
        matrix.append(dict(exposure=group,cash_tranches=len(fs),structural_events=len(sf),
                           executed_unique_cases=sum(FAMILIES[c['ticker']]==group for c in case_rows),
                           statuses=';'.join(sorted({f['status'] for f in fs})),source_ids=';'.join(sorted(source_ids)),
                           source_urls=';'.join(sources[i]['url'] for i in sorted(source_ids)),
                           source_sha256=';'.join(sources[i]['sha256'] for i in sorted(source_ids)),
                           policy='GROSS_EX_CLOSE_FRACTIONAL_NO_EXTERNAL_CASH',
                           completeness='CATALOGO_DIRIGIDO_PROVISORIO; NAO_CERTIFICADO',
                           limitation='Leilao de sobras nao reproduzido no indice fracionario' if group in ('TIM','VIVT') else 'Completude integral nao certificada; nenhuma pesquisa de centavos adicional'))
    dump(out,'matriz_4_ativos_fontes.csv',matrix)
    if raw_dir:
        raw,manifest=cotahist_prices(raw_dir,quote_targets)
        quotes=[]
        for t,d in sorted(quote_targets):
            rs=raw[t,d];assert len(rs)==1,(t,d,rs)
            price=book.exact(t,d);r=rs[0]
            assert math.isclose(price,r['close'],rel_tol=0,abs_tol=1e-10),(t,d,price,r)
            assert r['isin']==ISINS[t],(t,d,r['isin'])
            quotes.append(dict(ticker=t,date=d,engine_close=price,**r,status='ISIN_PRECO_NOMINAL_COINCIDENTES_ARQUIVO_LOCAL'))
        dump(out,'cotacoes_cotahist_v13.csv',quotes)
        (out/'cotahist_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Compact, frozen minimal quote fixture for CI event-return reproduction.
    # Daily metrics and raw COTAHIST checks still require the local data.
    fixture=dict(prices={t:{d:book.exact(t,d) for tt,d in sorted(quote_targets) if tt==t} for t in ISINS},calendar=book.calendar)
    (out/'nominal_event_prices.json.gz').write_bytes(gzip.compress(json.dumps(fixture,sort_keys=True).encode(),mtime=0))
    (out/'eventos_utilizados.json').write_text(json.dumps([asdict(e) for e in events],ensure_ascii=False,indent=2)+'\n')
    summary=dict(unique_cases=len(cases),target_position_rows=sum(r['v13_return']!='' for r in position_rows),cash_tranches=len(facts),
                 structural_events=sum(e.kind!='CASH' for e in events),baseline='v11.2 PROVISORIA PRESERVADA',
                 v12_preserved=True,fully_certified=False)
    (out/'resumo_execucao.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary));print('2020 maintenance standalone:',[(r['ticker'],r['event_return']) for r in case_rows if r['year']==2020 and r['mechanism']=='maintain'])
    print('2020 B00S:',[(r['experiment'],r['central_return'],r['high_return']) for r in cohorts if (r['start_year'],r['strategy'],r['scenario'],r['mechanism'])==(2020,'B00S','central','maintain')])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT);p.add_argument('--raw-dir',type=Path)
    args=p.parse_args();main(args.out,args.raw_dir)
