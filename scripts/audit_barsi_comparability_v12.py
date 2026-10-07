#!/usr/bin/env python3
"""Position/year comparability; targeted event alternatives, no change to v9.

The only newly assembled Barsi event catalog is BBSE3 (official nominal cash).
SBSP3/CSMG3/ENBR3 reuse the same class and event book already used by Graham.
Numerical event coverage is deliberately distinct from documentary certification.
"""
import argparse
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()))
from scripts.audit_alerts_v12 import BASE,INPUT,OUT,context,dump,sha,m,rights

RUNTIME=Path('.cache/besst_v9_reproduction/runtime')
V8=RUNTIME/'Barsi_Graham_Retomada_v8'
TARGETS={'BBSE3','SBSP3','CSMG3','ENBR3'}


def weighted_replacement(rows, field='alternative_return'):
    return sum(float(r['weight'])*(float(r[field]) if r[field]!='' else float(r['v9_return'])) for r in rows)


def wealth_share(rows, predicate):
    denominator=sum(float(r['weight'])*(1+float(r['v9_return'])) for r in rows)
    return sum(float(r['weight'])*(1+float(r['v9_return'])) for r in rows if predicate(r))/denominator


def main(out):
    book,events,coverage,_,evidence=context()
    facts=json.loads((INPUT/'verified_facts.json').read_text())
    bbse=[m.Event('V12_BBSE_'+f['ex_date'],f['ex_date'],'CASH','BBSE3',f['source_url'],
                  record_date=f['record_date'],amount=f['amount'],note='DIV; valor nominal bruto, sem atualizacao SELIC posterior; pagamento='+f['pay_date'])
          for f in facts if f['ticker']=='BBSE3' and '2020-06-30'<f['ex_date']<=m.END]
    assert len(bbse)==12
    alternatives={}
    for y,(start,end) in m.bridge.WINDOWS.items():
        for mode,stop in [('annual',end),('maintain',m.END)]:
            for t in TARGETS:
                if start not in book.prices.get(t,{}):continue
                ev=bbse if t=='BBSE3' else events
                try:result=m.safe_result(m.Engine(book,ev,coverage),start,stop,t)
                except Exception as exc:
                    # A position unavailable in the v9 universe is never filled.
                    if t=='ENBR3' and y>=2024:continue
                    raise RuntimeError((t,y,mode,str(exc))) from exc
                alternatives[y,mode,t]=result['return']
    paths={'annual':RUNTIME/'results_v9/besst_individual_annual.csv',
           'maintain':RUNTIME/'results_v9/besst_maintenance_holdings.csv'}
    cases=V8/'herdado_v7/herdado_v6/checkpoints/casos_v6'
    rows=[]
    for mode,path in paths.items():
        for r in m.read_csv(path):
            year=int(r['year' if mode=='annual' else 'start_year']);t=r['ticker']
            start,end=m.bridge.WINDOWS[year]
            if mode=='maintain':end=m.END
            case=cases/f'{t}_{start}_{end}.json'
            if mode=='annual' and year==2020:
                cls='EVENTOS_V8_HERDADOS';reference=V8/'dados/eventos_retorno_besst2020_v8.csv'
            elif case.exists():
                cls='CHECKPOINT_EVENTOS_V6_HERDADO';reference=case
            else:
                cls='APROXIMACAO_CAIXA_V9';reference=Path('.cache/besst_v9_reproduction/Barsi_Graham_Comparacao_Final_v9/scripts')/('compute_besst.py' if mode=='annual' else 'compute_maintenance.py')
            alt=alternatives.get((year,mode,t),'')
            weight,rv=float(r['weight']),float(r['return'])
            low=float(r['return_cash_low']) if mode=='annual' else float(r['cash_low_factor'])-1
            high=float(r['return_cash_high']) if mode=='annual' else float(r['cash_high_factor'])-1
            rows.append(dict(mechanism=mode,year=year,start=start,end=end,strategy=r['portfolio'],scenario=r['scenario'],ticker=t,
                             weight=weight,v9_return=rv,v9_cash_low=low,v9_cash_high=high,coverage_class=cls,
                             reference_file=str(reference.relative_to(Path('.cache/besst_v9_reproduction'))),reference_sha256=sha(reference),
                             alternative_return=alt,weighted_difference_pp=100*weight*(alt-rv) if alt!='' else '',
                             alternative_scope=('CATALOGO_CAIXA_RI_NOMINAL_VERIFICADO; estrutura e completude geral pendentes' if t=='BBSE3' else
                                                'MESMA_CLASSE_E_MOTOR_GRAHAM; cobertura documental herdada parcial') if alt!='' else 'PENDENTE; nao recalculado',
                             event_calculation_available=cls!='APROXIMACAO_CAIXA_V9' or alt!='',
                             fully_document_certified=False,
                             delta_to_high_pp=100*weight*(alt-high) if alt!='' else '',
                             v9_high_minus_central_pp=100*weight*(high-rv)))
    assert len(rows)==1212
    dump(out,'barsi_posicao_ano_1212.csv',rows)
    cover,portfolios=[],[]
    for y in m.bridge.WINDOWS:
        for s in ('B00','B00S','B06','B06S'):
            for scenario in ('central','conservative'):
                for mode in ('annual','maintain'):
                    ps=[r for r in rows if (r['year'],r['strategy'],r['scenario'],r['mechanism'])==(y,s,scenario,mode)]
                    assert math.isclose(sum(p['weight'] for p in ps),1,abs_tol=1e-10)
                    base=sum(p['weight']*p['v9_return'] for p in ps)
                    alt=weighted_replacement(ps)
                    portfolios.append(dict(year=y,strategy=s,scenario=scenario,mechanism=mode,baseline_v9=base,
                                           partial_event_alternative=alt,delta_pp=100*(alt-base),
                                           substituted_tickers=';'.join(sorted(p['ticker'] for p in ps if p['alternative_return']!='')),
                                           unchanged_other_positions=True,certified=False))
                    cover.append(dict(year=y,strategy=s,scenario=scenario,mechanism=mode,
                                      denominator='patrimonio final v9 da carteira; inclusive caixa; peso*(1+retorno)',
                                      final_wealth_per_10000=10000*(1+base),
                                      inherited_event_wealth_pct=100*wealth_share(ps,lambda p:p['coverage_class']!='APROXIMACAO_CAIXA_V9'),
                                      event_calculation_wealth_pct=100*wealth_share(ps,lambda p:p['event_calculation_available']),
                                      primary_cash_catalog_bbse_wealth_pct=100*wealth_share(ps,lambda p:p['ticker']=='BBSE3'),
                                      complete_document_certification_wealth_pct=0,
                                      event_initial_weight_pct=100*sum(p['weight'] for p in ps if p['event_calculation_available']),
                                      limitation='Evento calculado ou checkpoint reproduzido nao prova completude documental; BBSE valores nominais sem atualizacao; nenhuma classe de acao foi trocada'))
    dump(out,'barsi_cobertura_patrimonial_96.csv',cover)
    dump(out,'barsi_alternativas_96_anuais_manutencao.csv',portfolios)
    # Renewal uses the annual selection at each June date, preserving v9 weights.
    comparison=[]
    for y in m.bridge.WINDOWS:
        for s in ('B00','B00S','B06','B06S'):
            for scenario in ('central','conservative'):
                for mode in ('maintain','renew'):
                    ps=[p for p in portfolios if p['strategy']==s and p['scenario']==scenario and
                        (p['mechanism']=='maintain' and p['year']==y if mode=='maintain' else p['mechanism']=='annual' and p['year']>=y)]
                    b=math.prod(1+p['baseline_v9'] for p in ps)-1
                    a=math.prod(1+p['partial_event_alternative'] for p in ps)-1
                    comparison.append(dict(start_year=y,strategy=s,scenario=scenario,mechanism=mode,v9_return=b,
                                           alternative_return=a,delta_pp=100*(a-b),scope='SUBSTITUICAO_PARCIAL_4_ATIVOS; demais v9 preservados',certified=False))
    dump(out,'barsi_manutencao_renovacao_96.csv',comparison)
    baseline_g={(int(r['start_year']),r['rule'],r['mechanism']):float(r['baseline_v11_2']) for r in m.read_csv(out/'impacto_conjunto_36_carteiras.csv')}
    candidate_g={(int(r['start_year']),r['rule'],r['mechanism']):float(r['candidate_v12']) for r in m.read_csv(out/'impacto_conjunto_36_carteiras.csv')}
    rankings=[]
    for y in m.bridge.WINDOWS:
        for mode in ('maintain','renew'):
            original={r['strategy']:r['v9_return'] for r in comparison if r['start_year']==y and r['mechanism']==mode and r['scenario']=='central'}
            alternative={r['strategy']:r['alternative_return'] for r in comparison if r['start_year']==y and r['mechanism']==mode and r['scenario']=='central'}
            original.update({s:baseline_g[y,s,mode] for s in rights.RULES})
            alternative.update({s:candidate_g[y,s,mode] for s in rights.RULES})
            bova=book.exact('BOVA11',m.END)/book.exact('BOVA11',m.bridge.WINDOWS[y][0])-1
            original['BOVA11']=alternative['BOVA11']=bova
            for s in original:
                before=sorted(original,key=lambda k:(-original[k],k)).index(s)+1
                after=sorted(alternative,key=lambda k:(-alternative[k],k)).index(s)+1
                rankings.append(dict(start_year=y,mechanism=mode,strategy=s,before=before,after_partial=after,changed=before!=after,
                                     baseline_return=original[s],partial_alternative_return=alternative[s],certified=False))
    dump(out,'ranking_comparabilidade_parcial_96.csv',rankings)
    ps=[r for r in rows if (r['mechanism'],r['year'],r['strategy'],r['scenario'])==('maintain',2020,'B00S','central')]
    r16=baseline_g[2020,'R16','maintain']
    v9central=sum(r['weight']*r['v9_return'] for r in ps)
    v9high=sum(r['weight']*r['v9_cash_high'] for r in ps)
    material=[]
    for rank,p in enumerate(sorted(ps,key=lambda r:-r['weight']*(1+r['v9_return'])),1):
        # Replace the selected position in the upper sensitivity; do not add its
        # central delta on top of the old high (that would count cash twice).
        residual_high=v9high+p['weight']*(p['alternative_return']-p['v9_cash_high']) if p['alternative_return']!='' else ''
        material.append(dict(priority_by_final_wealth=rank,ticker=p['ticker'],weight=p['weight'],v9_return=p['v9_return'],
                             final_wealth_share_pct=100*p['weight']*(1+p['v9_return'])/(1+v9central),
                             asset_extra_above_own_v9_high_needed_to_close_gap_pp=100*(r16-v9high)/p['weight'],
                             central_asset_revision_needed_to_tie_r16_pp=100*(r16-v9central)/p['weight'],
                             available_event_return=p['alternative_return'],
                             actual_weighted_revision_pp=p['weighted_difference_pp'],
                             b00s_high_with_only_this_replacement=residual_high,
                             r16_minus_that_scenario_pp=100*(r16-residual_high) if residual_high!='' else '',
                             conclusion='Faltam catalogo por evento e limite de erro documental; faixa v9 nao limita omissoes'))
    dump(out,'prioridades_materiais_B00S_2020.csv',material)
    bbse_row=next(r for r in material if r['ticker']=='BBSE3')
    summary=dict(position_year_rows=len(rows),targeted_tickers=sorted(TARGETS),new_primary_catalog='BBSE3: 12 datas-ex nominais',
                 r16_baseline=r16,b00s_v9_central=v9central,b00s_v9_high=v9high,r16_minus_v9_high_pp=100*(r16-v9high),
                 bbse_isolated_weighted_revision_pp=bbse_row['actual_weighted_revision_pp'],
                 b00s_high_with_bbse_replaced=bbse_row['b00s_high_with_only_this_replacement'],
                 r16_minus_high_after_bbse_pp=bbse_row['r16_minus_that_scenario_pp'],
                 mathematical_minimum='Uma posicao de peso 10% com revisao superior a gap/0.10 acima de seu proprio limite v9 pode inverter o confronto; nao ha prova de que tal erro exista.',
                 minimum_next_documentary_work='PSSA3, TIMP3->TIMS3, VIVT4->VIVT3 e SAPR4: maiores pesos remanescentes; nao ha conjunto finito comprovadamente suficiente para certificar sem limitar os demais erros.',
                 rank_changes_partial=sum(r['changed'] for r in rankings),fully_certified=False)
    (out/'resumo_comparabilidade.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=OUT);main(p.parse_args().out)
