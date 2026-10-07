#!/usr/bin/env python3
"""Consolidated exploratory strategy diagnosis after the directed v13 audit.

No screening rerun, no optimisation, no post-hoc selection changes. Cohorts are
nested/overlapping; win frequencies and scenario ranges are descriptive only.
"""
import argparse
from collections import defaultdict, Counter
from datetime import date
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path.cwd()))
from scripts.reconstruct_barsi_v13 import BASE,V12,OUT,INPUT,FAMILIES,EXPERIMENTS,context,dump,m,rights,sha,replacement,chained_returns,daily_metrics


def ranking(values):
    # Competition ranks: equal economic returns share a place, never break a
    # tie alphabetically and accidentally count an exclusive winner.
    return {s:1+sum(v>value and not math.isclose(v,value,rel_tol=0,abs_tol=1e-10)
                    for v in values.values()) for s,value in values.items()}


def ranking_order(values, ranks):
    return ' > '.join(' = '.join(sorted(s for s in values if ranks[s]==r))
                      for r in sorted(set(ranks.values())))


def concentration(weights):
    vals=list(weights.values())
    assert math.isclose(sum(vals),1,abs_tol=1e-9)
    hhi=sum(x*x for x in vals)
    return dict(position_count=len(vals),max_weight=max(vals),top3_weight=sum(sorted(vals,reverse=True)[:3]),hhi=hhi,effective_positions=1/hhi)


def main(out):
    book,events,coverage,sels,evidence=context()
    cohorts=m.read_csv(out/'comparacao_coortes_v13.csv')
    impacts=m.read_csv(V12/'impacto_conjunto_36_carteiras.csv')
    g={(int(r['start_year']),r['rule'],r['mechanism']):float(r['baseline_v11_2']) for r in impacts}
    gv12={(int(r['start_year']),r['rule'],r['mechanism']):float(r['candidate_v12']) for r in impacts}
    b={(int(r['start_year']),r['strategy'],r['scenario'],r['mechanism'],r['experiment']):r for r in cohorts}
    bova={y:book.exact('BOVA11',m.END)/book.exact('BOVA11',start)-1 for y,(start,_) in m.bridge.WINDOWS.items()}
    rankings=[];freq=[];orders=[];pairs=[]
    for y in m.bridge.WINDOWS:
        for mode in ['maintain','renew']:
            for sc in ['central','conservative']:
                original={s:float(b[y,s,sc,mode,'v9']['central_return']) for s in ['B00','B00S','B06','B06S']}
                original.update({s:g[y,s,mode] for s in rights.RULES});original['BOVA11']=bova[y]
                baseline_ranks=ranking(original)
                for expt in EXPERIMENTS:
                    values={s:float(b[y,s,sc,mode,expt]['central_return']) for s in ['B00','B00S','B06','B06S']}
                    values.update({s:g[y,s,mode] for s in rights.RULES});values['BOVA11']=bova[y]
                    ranks=ranking(values)
                    for s in values:
                        years=(date.fromisoformat(m.END)-date.fromisoformat(m.bridge.WINDOWS[y][0])).days/365.25
                        rankings.append(dict(start_year=y,mechanism=mode,scenario=sc,experiment=expt,strategy=s,
                                             return_value=values[s],cagr=(1+values[s])**(1/years)-1,
                                             rank=ranks[s],rank_v9=baseline_ranks[s],rank_changed=ranks[s]!=baseline_ranks[s],
                                             delta_vs_v9_pp=100*(values[s]-original[s]),margin_vs_bova_pp=100*(values[s]-bova[y])))
                    if expt=='v12_plus_v13':
                        ordered=sorted(values,key=lambda s:(ranks[s],s));winner,runner=ordered[:2]
                        leaders=[s for s in ordered if ranks[s]==1]
                        orders.append(dict(start_year=y,mechanism=mode,scenario=sc,order=ranking_order(values,ranks),winner=' = '.join(leaders),
                                           winner_return=values[winner],runner_up=runner,winner_margin_pp=100*(values[winner]-values[runner])))
                        for lhs,rhs in [('R03','R00'),('R16','R03'),('B06','B00'),('B06S','B00S'),('B00S','B00'),('B06S','B06')]:
                            pairs.append(dict(start_year=y,mechanism=mode,scenario=sc,left=lhs,right=rhs,left_minus_right_pp=100*(values[lhs]-values[rhs]),left_wins=values[lhs]>values[rhs]))
    dump(out,'rankings_v13.csv',rankings);dump(out,'ordem_seis_formacoes.csv',orders);dump(out,'comparacoes_regras.csv',pairs)
    for mode in ['maintain','renew']:
        for sc in ['central','conservative']:
            for s in ['R00','R03','R16','B00','B00S','B06','B06S','BOVA11']:
                rs=[r for r in rankings if (r['mechanism'],r['scenario'],r['experiment'],r['strategy'])==(mode,sc,'v12_plus_v13',s)]
                freq.append(dict(mechanism=mode,scenario=sc,strategy=s,cohorts=6,wins=sum(r['rank']==1 for r in rs),
                                 win_definition='LIDERANCA_INCLUI_EMPATES; SOMA_PODE_EXCEDER_SEIS',
                                 beats_bova=sum(r['margin_vs_bova_pp']>0 for r in rs),mean_rank=statistics.mean(r['rank'] for r in rs),
                                 best_rank=min(r['rank'] for r in rs),worst_rank=max(r['rank'] for r in rs),
                                 min_cagr=min(r['cagr'] for r in rs),max_cagr=max(r['cagr'] for r in rs),
                                 inference='DESCRITIVO; SEIS_COORTES_SOBREPOSTAS; NAO_TESTE_ESTATISTICO'))
    dump(out,'frequencias_estabilidade_v13.csv',freq)
    switches=[]
    for sc in ['central','conservative']:
        for s in ['R00','R03','R16','B00','B00S','B06','B06S']:
            for y in m.bridge.WINDOWS:
                rows={r['mechanism']:r for r in rankings if r['scenario']==sc and r['strategy']==s and r['start_year']==y and r['experiment']=='v12_plus_v13'}
                maintain,renew=rows['maintain']['return_value'],rows['renew']['return_value']
                switches.append(dict(start_year=y,strategy=s,scenario=sc,maintain=maintain,renew=renew,
                                     renew_minus_maintain_pp=100*(renew-maintain),
                                     decision='EMPATE' if math.isclose(maintain,renew,abs_tol=1e-10) else 'RENOVAR' if renew>maintain else 'MANTER'))
    dump(out,'manter_ou_renovar_v13.csv',switches)
    # Materiality/confidence under tested composition and return conventions.
    stress=m.read_csv(out/'sensibilidades_carteiras_v13.csv');confidence=[]
    for y in m.bridge.WINDOWS:
        for mode in ['maintain','renew']:
            ranges={}
            for s in ['R00','R03','R16','B00','B00S','B06','B06S','BOVA11']:
                if s.startswith('R'):vals=[g[y,s,mode],gv12[y,s,mode]]
                elif s=='BOVA11':vals=[bova[y]]
                else:
                    vals=[float(r[k]) for r in cohorts if int(r['start_year'])==y and r['mechanism']==mode and r['strategy']==s and
                          r['experiment'] in ['v9','v12_partial','v13_four','v12_plus_v13'] for k in ['central_return','low_return','high_return']]
                    vals += [float(r['return_value']) for r in stress if int(r['start_year'])==y and r['mechanism']==mode and r['strategy']==s and
                             r['sensitivity'] in ['cash_minus20','cash_plus20','capital_keep_cash']]
                ranges[s]=(min(vals),max(vals))
            for s,(lo,hi) in ranges.items():
                central=g[y,s,mode] if s.startswith('R') else bova[y] if s=='BOVA11' else float(b[y,s,'central',mode,'v12_plus_v13']['central_return'])
                competitors=[a for a in ranges if a!=s]
                worst_other=max(ranges[a][1] for a in competitors);best_other=max(ranges[a][0] for a in competitors)
                conclusion='LIDERA_EM_TODOS_OS_CENARIOS_TESTADOS' if lo>worst_other else 'NAO_LIDERA_NOS_CENARIOS_TESTADOS' if hi<best_other else 'LIDERANCA_DEPENDE_DO_CENARIO'
                # Equal Graham paths in both alternatives are a correlated
                # tie, not two independently varying uncertainty intervals.
                if s in rights.RULES:
                    peers=[a for a in rights.RULES if g[y,a,mode]==g[y,s,mode] and gv12[y,a,mode]==gv12[y,s,mode]]
                    if len(peers)>1 and lo>max(ranges[a][1] for a in ranges if a not in peers):
                        conclusion='LIDERANCA_COMPARTILHADA_NOS_CENARIOS_TESTADOS'
                shared=conclusion=='LIDERANCA_COMPARTILHADA_NOS_CENARIOS_TESTADOS'
                minor=max([abs(float(r['delta_pp'])) for r in stress if int(r['start_year'])==y and r['mechanism']==mode and r['strategy']==s and r['sensitivity']=='pssa_initial_notice'],default=0)
                confidence.append(dict(start_year=y,mechanism=mode,strategy=s,central_return=central,scenario_min=lo,scenario_max=hi,
                                       scenario_amplitude_pp=100*(hi-lo),margin_vs_bova_pp=100*(central-bova[y]),
                                       min_margin_vs_bova_pp=100*(lo-bova[y]),max_margin_vs_bova_pp=100*(hi-bova[y]),
                                       min_margin_vs_best_competitor_pp=0 if shared else 100*(lo-worst_other),max_margin_vs_best_competitor_pp=0 if shared else 100*(hi-best_other),
                                       conclusion=conclusion,confidence_scope='CONDICIONAL_A_SELECOES_E_METODOS_TESTADOS; NAO_PROBABILISTICO',
                                       tested_minor_pssa_refinement_max_pp=minor,
                                       potential_rank_inverters='Composicao, tratamento de caixa, historico TIM/PN-ON na selecao, universo PIT incompleto; efeito desconhecido nao limitado',
                                       unbounded_risks='Universo e historico PIT parcial; caixa/aproximacoes residuais; fracionamento real; sem limite para eventos desconhecidos'))
    dump(out,'matriz_confianca_materialidade_v13.csv',confidence)
    # Concentration, attribution and replacing the biggest contributor with cash.
    ps=m.read_csv(out/'alternativas_barsi_v13_por_posicao.csv')
    gpositions=m.read_csv(BASE/'direitos_itsa_v11_2/graham_posicoes.csv')
    selection=m.read_csv(BASE/'carteiras_selecionadas_768_posicoes.csv')
    conrows=[];drivers=[]
    for y in m.bridge.WINDOWS:
        for s in ['R00','R03','R16','B00','B00S','B06','B06S']:
            scenarios=['central'] if s.startswith('R') else ['central','conservative']
            for sc in scenarios:
                if s.startswith('R'):
                    rs=[r for r in gpositions if int(r['start_year'])==y and r['rule']==s]
                    positions=[dict(ticker=r['ticker'],weight=float(r['weight']),ret=float(r['return']),contribution=float(r['contribution'])) for r in rs]
                else:
                    rs=[r for r in ps if (int(r['year']),r['strategy'],r['scenario'],r['mechanism'])==(y,s,sc,'maintain')]
                    positions=[dict(ticker=r['ticker'],weight=float(r['weight']),ret=replacement(r,'v12_plus_v13'),contribution=float(r['weight'])*replacement(r,'v12_plus_v13')) for r in rs]
                weights={p['ticker']:p['weight'] for p in positions}
                sectors=defaultdict(float)
                for p in positions:
                    label=next((r['sector'] for r in selection if int(r['year'])==y and r['strategy']==s and r['ticker']==p['ticker']),'NAO_MAPEADO')
                    sectors[label]+=p['weight']
                final=sum(p['contribution'] for p in positions);expected=g[y,s,'maintain'] if s.startswith('R') else float(b[y,s,sc,'maintain','v12_plus_v13']['central_return'])
                assert math.isclose(final,expected,abs_tol=1e-9)
                top=max(positions,key=lambda p:p['contribution'])
                final_weights={p['ticker']:p['weight']*(1+p['ret'])/(1+final) for p in positions}
                conrows.append(dict(start_year=y,strategy=s,scenario=sc,**concentration(weights),sector_count=len(sectors),
                                    max_sector_weight=max(sectors.values()),final_hhi=sum(w*w for w in final_weights.values()),
                                    max_final_weight=max(final_weights.values()),largest_gain_ticker=top['ticker'],largest_gain_contribution_pp=100*top['contribution'],
                                    return_with_top_gain_replaced_by_cash=final-top['contribution'],
                                    top_gain_share_of_net_gain=top['contribution']/final if final else '',
                                    stress_label='ATRIBUICAO_EX_POST; NAO_NOVA_SELECAO_NEM_LIMITE_DE_ERRO'))
                for p in positions:
                    drivers.append(dict(start_year=y,strategy=s,scenario=sc,**p,final_wealth_share=final_weights[p['ticker']]))
    dump(out,'concentracao_manutencao_v13.csv',conrows);dump(out,'contribuicoes_manutencao_v13.csv',drivers)
    # Same-calendar daily paths only where actually supported. We do not invent
    # daily Barsi totals from annual approximate cash or interpolate missing NAV.
    risk=[];regress=[]
    for y in m.bridge.WINDOWS:
        start=m.bridge.WINDOWS[y][0]
        for mode in ['maintain','renew']:
            for rule in rights.RULES:
                capital=10000.;nav=[]
                for p in [y] if mode=='maintain' else range(y,2026):
                    a,bb=m.bridge.WINDOWS[p];bb=m.END if mode=='maintain' else bb
                    st,result,_=rights.simulate(book,events,coverage,a,bb,rights.weights_for(sels[p],rule),capital,evidence)
                    nav.extend(st.nav if not nav else st.nav[1:]);capital=result['final_value']
                actual=capital/10000-1;ref=g[y,rule,mode]
                assert math.isclose(actual,ref,abs_tol=1e-9)
                regress.append(dict(start_year=y,strategy=rule,mechanism=mode,calculated=actual,baseline_v11_2=ref,difference=actual-ref,status='OK'))
                risk.append(dict(start_year=y,strategy=rule,mechanism=mode,**daily_metrics(nav),scope='GRAHAM_BASELINE_V11_2; NAO_COMPARAVEL_A_RISCO_BARSI_PARCIAL'))
            nav=[dict(date=d,nav=book.prices['BOVA11'].get(d)) for d in book.calendar if start<=d<=m.END]
            risk.append(dict(start_year=y,strategy='BOVA11',mechanism=mode,**daily_metrics(nav),scope='COTA_NOMINAL_BENCHMARK'))
            for s in ['B00','B00S','B06','B06S']:
                risk.append(dict(start_year=y,strategy=s,mechanism=mode,daily_status='NOT_ESTIMATED_RESIDUAL_EVENT_PATHS_MISSING',daily_observations='',volatility_252='',max_drawdown='',scope='Nao interpolar caixa anual v9 para fabricar risco diario comparavel'))
    dump(out,'risco_diario_cobertura_v13.csv',risk);dump(out,'regressao_economica_v11_2_36.csv',regress)
    # Reconstruct the narrow R16/B00S comparison for every directed alternative.
    contrast=[]
    for r in cohorts:
        if (r['start_year'],r['strategy'],r['scenario'],r['mechanism'])!=('2020','B00S','central','maintain'):continue
        central,low,high=(float(r[k]) for k in ['central_return','low_return','high_return'])
        contrast.append(dict(experiment=r['experiment'],b00s_central=central,b00s_low=low,b00s_high=high,r16_v11_2=g[2020,'R16','maintain'],
                             r16_minus_central_pp=100*(g[2020,'R16','maintain']-central),r16_minus_high_pp=100*(g[2020,'R16','maintain']-high)))
    dump(out,'confronto_R16_B00S_2020.csv',contrast)
    summary=dict(baseline='v11.2 PROVISORIA',all_v12_unchanged=True,
                 ranks_changed_joint={mode:sum(r['rank_changed'] for r in rankings if r['mechanism']==mode and r['scenario']=='central' and r['experiment']=='v12_plus_v13') for mode in ['maintain','renew']},
                 wins_central=[r for r in freq if r['scenario']=='central' and r['wins']],
                 ranking_orders_central=[r for r in orders if r['scenario']=='central'],
                 risk_paths_computable=Counter(r['daily_status'] for r in risk),
                 strategic_scope='Exploratorio; seis coortes sobrepostas, sem teste estatistico ou universo alternativo; encerrar auditoria dirigida nesta rodada')
    (out/'resumo_estrategico.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT);main(p.parse_args().out)
