#!/usr/bin/env python3
"""Economic decomposition and bounded *assumptions* on the same A/B2/BH cases."""
import csv,gzip,hashlib,json,sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.simulate_ir_100k import load,execute,Portfolio,OUT,dump

def read(name):return list(csv.DictReader(open(OUT/name,encoding='utf-8-sig')))
def enrich_rankings(comparison):
    for r in comparison:
        peers=[p for p in comparison if p['formation']==r['formation'] and p['scenario']==r['scenario']]
        # Conservative tables also contain common Graham and BOVA references.
        if r['scenario']=='conservative':peers +=[p for p in comparison if p['formation']==r['formation'] and p['scenario']=='central' and (p['strategy'].startswith('R') or p['strategy']=='BOVA11')]
        r['rank_gross']=1+sum(float(p['gross_wealth'])>float(r['gross_wealth'])+1e-6 for p in peers)
        r['rank_net']=1+sum(float(p['net_wealth'])>float(r['net_wealth'])+1e-6 for p in peers)
        r['rank_change_tax']=r['rank_gross']-r['rank_net']

def tax_ranking_summary(comparison):
    rows=[]
    for y in range(2020,2026):
        peers=[r for r in comparison if int(r['formation'])==y and r['scenario']=='central']
        rows.append(dict(formation=y,gross_leader=' = '.join(r['strategy']+' '+r['policy'] for r in peers if int(r['rank_gross'])==1),net_leader=' = '.join(r['strategy']+' '+r['policy'] for r in peers if int(r['rank_net'])==1),rank_movements=sum(int(r['rank_change_tax'])!=0 for r in peers),gross_leader_wealth=max(float(r['gross_wealth']) for r in peers),net_leader_wealth=max(float(r['net_wealth']) for r in peers)))
    return rows

def main():
    data=load();base=read('results.csv');lookup={r['case_id']:r for r in base};sens=[]
    # These columns change one missing-data assumption, never the policy universe.
    controls={'indeterminate_exit':{'unknown_exit':True},'bonus_market_proxy':{'bonus_market':True},'gcap_zero_bound':{'gcap_exempt':True},
              'jcp_identified_net':{'jcp_net':True},'jcp_unclassified_upper':{'jcp_net':True,'jcp_unclassified':True},
              'v9_cash_minus20':{'cash_scale':.8},'v9_cash_plus20':{'cash_scale':1.2}}
    for label,options in controls.items():
        result=execute(data,options,log=False)
        if result['failures']:raise RuntimeError((label,result['failures']))
        for r in result['results']:
            sens.append(dict(case_id=r['case_id'],assumption=label,final_wealth=r['final_wealth'],tax_sales=r['tax_sales'],tax_jcp=r['tax_jcp'],delta_vs_central=r['final_wealth']-float(lookup[r['case_id']]['final_wealth']),status='SENSIBILIDADE_DE_HIPOTESE_NAO_LIMITE_FISCAL_CERTIFICADO'))
        print('sensitivity complete',label,flush=True)
    dump('sensitivities.csv',sens)
    grouped=defaultdict(dict)
    for r in base:grouped[int(r['formation']),r['strategy'],r['scenario']][r['policy'],r['ir']]=r
    comparison=[]
    for (y,s,sc),rs in grouped.items():
        for pol in sorted({k[0] for k in rs}):
            gross=rs[pol,'False'];net=rs[pol,'True'];g=float(gross['final_wealth']);n=float(net['final_wealth'])
            sr={r['assumption']:r for r in sens if r['case_id']==net['case_id']}
            row=dict(formation=y,strategy=s,scenario=sc,policy=pol,gross_wealth=g,net_wealth=n,net_return_pct=float(net['return_pct']),net_cagr_pct=float(net['cagr_pct']),ir_paid=float(net['tax_sales']),tax_effect_wealth=g-n,compound_and_allocation_tax_effect=g-n-float(net['tax_sales']),turnover=float(net['annual_turnover_sum']),unknown_decisions=net['unknown_decisions'],status=net['status'])
            for label,r in sr.items():row['wealth_'+label]=float(r['final_wealth'])
            row['one_at_a_time_min']=min([n]+[float(r['final_wealth']) for r in sr.values()]);row['one_at_a_time_max']=max([n]+[float(r['final_wealth']) for r in sr.values()])
            comparison.append(row)
    enrich_rankings(comparison)
    dump('comparison_rankings.csv',comparison)
    decomposition=[]
    for (y,s,sc),rs in grouped.items():
        if ('A','False') not in rs:continue
        a0=float(rs['A','False']['final_wealth']);a1=float(rs['A','True']['final_wealth']);b0=float(rs['B2','False']['final_wealth']);b1=float(rs['B2','True']['final_wealth'])
        composition=b0-a0;fiscal=(a0-a1)-(b0-b1)
        assert abs(b1-a1-composition-fiscal)<1e-6
        decomposition.append(dict(formation=y,strategy=s,scenario=sc,A_gross=a0,B2_gross=b0,A_net=a1,B2_net=b1,B2_minus_A_net=b1-a1,composition_and_execution_effect=composition,differential_tax_effect=fiscal,A_tax_drag=a0-a1,B2_tax_drag=b0-b1,winner='TIE' if abs(b1-a1)<1e-6 else 'B2' if b1>a1 else 'A'))
    dump('decomposition.csv',decomposition)
    sensitivity_lookup={(r['case_id'],r['assumption']):r for r in sens}
    robustness=[]
    for r in decomposition:
        prefix=f"{r['formation']}_{r['strategy']}_{r['scenario']}"
        deltas={label:sensitivity_lookup[prefix+'_B2_IR',label]['final_wealth']-sensitivity_lookup[prefix+'_A_IR',label]['final_wealth'] for label in controls}
        vals=[r['B2_minus_A_net']]+list(deltas.values())
        robustness.append(dict(formation=r['formation'],strategy=r['strategy'],scenario=r['scenario'],central_difference=r['B2_minus_A_net'],min_paired_difference=min(vals),max_paired_difference=max(vals),winner_changes=min(vals)<-1e-6 and max(vals)>1e-6,**deltas))
    dump('paired_robustness.csv',robustness)

    # Mechanical same-close is a diagnostic, never a third policy or an investable portfolio.
    frozen=list(csv.DictReader(open('research/graham_v6_comparison/checkpoint_v13_2026_10_07/comparacao_coortes_v13.csv',encoding='utf-8-sig')))
    mechanical=[]
    for r in base:
        if r['ir']=='True' or r['policy']=='B2':continue
        p=Portfolio(data,int(r['formation']),r['strategy'],r['scenario'],r['policy'],False,same_close=True,log=False);m=p.run()
        ref=next((float(x['final_value'])*10 for x in frozen if x['start_year']==r['formation'] and x['strategy']==r['strategy'] and x['scenario']==r['scenario'] and x['mechanism']==('renew' if r['policy']=='A' else 'maintain') and x['experiment']=='v12_plus_v13'),None)
        mechanical.append(dict(case_id=r['case_id'],same_close_wealth=m['final_wealth'],operational_wealth=r['final_wealth'],operational_minus_sameclose=float(r['final_wealth'])-m['final_wealth'],v13_gross_reference=ref,sameclose_minus_v13=m['final_wealth']-ref if ref else '',interpretation='DIAGNOSTICO: diferenca residual de eventos agregados, alocacao e fatos societarios; nao paridade forcada'))
    dump('mechanical_bridge.csv',mechanical)
    # Exposure to unresolved bonus cost / approximate cash in the actual taxable paths.
    led=json.loads(gzip.decompress((OUT/'ledger.json.gz').read_bytes()));unresolved={e['event_id'] for e in data['events'] if e.get('proxy') or e['kind']=='BONUS' and not(e['asset']=='ITSA3' or e['asset']=='PSSA3')}
    exposure=[]
    for r in base:
        if r['ir']!='True':continue
        rows=[x for x in led if x['case_id']==r['case_id'] and x.get('event_id') in unresolved]
        exposure.append(dict(case_id=r['case_id'],proxy_cash=sum(x.get('amount',0) for x in rows if x['kind']=='CASH'),unresolved_bonus_events=sum(x['kind']=='BONUS' for x in rows),final_net=r['final_wealth'],status=r['status']))
    dump('approximation_exposure.csv',exposure)
    # Main central figures are generated directly from the data to avoid transcription.
    doc=[];doc.append('# Checkpoint — IR R$ 100 mil, A × B2\n\nExecução no Codespaces, 07/10/2026 (America/Sao_Paulo; UTC 08/10). Baseline v11.2 provisória, v12 e v13 preservadas. Sem merge.\n')
    doc.append('**372 simulações principais calculadas**, sem falha operacional: seis formações, sete regras A/B2 com e sem IR, quatro referências Barsi buy and hold, BOVA11, e os universos Barsi central/conservative já existentes. As políticas são somente A e B2; BH é referência. Resultados monetários abaixo arredondados ao real; CSVs conservam precisão para reprodução.\n')
    doc.append('**Status: checkpoint econômico provisório.** O cálculo foi executado; os resultados Barsi conservam proventos agregados v9, e custos fiscais de algumas bonificações ainda são aproximações. A faixa de hipóteses calculada não é intervalo de confiança nem certificação fiscal.\n')
    doc.append('**Conclusão econômica:** no universo central, B2 supera A nas três regras Graham nas cinco formações que têm renovação; em 2025 há empate. Isso não implica pagar menos imposto nominal: R03/2020 B2 termina com R$ 328.364, contra R$ 324.308 de A, apesar de pagar R$ 25.378 de IR, contra R$ 25.118. Da vantagem de R$ 4.056, R$ 3.194 vêm da carteira/execução sem IR e R$ 862 da diferença de efeito fiscal acumulado.\n')
    doc.append('A vantagem Graham não é universal sobre Barsi: B00S buy and hold lidera as formações centrais de 2022 e 2024; B00S B2 lidera 2023. R03 B2 lidera 2020, R00 B2 lidera 2021, e R03 A/B2 empatam na liderança de 2025. Em 2020 B00S BH termina em R$ 225.397 e BOVA11 em R$ 170.042. Barsi manter continua competitivo, principalmente nas formações intermediárias. Essas comparações respeitam o mesmo capital e a saída final tributada, mas conservam as limitações documentais descritas no protocolo.\n')
    changed=[r for r in robustness if r['scenario']=='central' and r['winner_changes']]
    doc.append('**Sensibilidade da decisão A/B2:** a direção da vantagem Graham central permanece em todos os testes isolados calculados. Entre as regras Barsi, a escolha A/B2 muda em '+', '.join(str(r['strategy'])+'/'+str(r['formation']) for r in changed)+'. Essas preferências não são robustas às hipóteses pendentes. A faixa considera alterações isoladas, sem afirmar robustez a todas as combinações de erros. Veja [paired_robustness.csv](../research/ir_100k_results/paired_robustness.csv).\n')
    for year in range(2020,2026):
        doc.append(f'\n## Formação {year}\n\nPatrimônio final em 30/06/2026, capital inicial R$ 100.000. Universo central.\n\n| Regra / política | Sem IR (R$) | Com IR (R$) | Retorno líquido | IR pago (R$) | Giro anual acumulado | Rank líquido |\n|---|---:|---:|---:|---:|---:|---:|')
        for r in comparison:
            if r['formation']==year and r['scenario']=='central':doc.append(f"| {r['strategy']} {r['policy']} | {r['gross_wealth']:,.0f} | {r['net_wealth']:,.0f} | {r['net_return_pct']:.2f}% | {r['ir_paid']:,.0f} | {r['turnover']:.2f}× | {r['rank_net']} |")
    doc.append('\n## Decomposição de R03\n\nValores em reais; diferença positiva favorece B2. O efeito fiscal inclui o reinvestimento do imposto e as mudanças de quantidades necessárias para financiá-lo. A diferença líquida não é sinônimo de economia de imposto.\n\n| Formação | A líquido | B2 líquido | B00S BH líquido | Efeito carteira/executar B2−A sem IR | Diferença dos efeitos fiscais | B2−A líquido |\n|---|---:|---:|---:|---:|---:|---:|')
    for y in range(2020,2026):
        d=next(r for r in decomposition if r['formation']==y and r['strategy']=='R03' and r['scenario']=='central');bh=next(r for r in comparison if r['formation']==y and r['strategy']=='B00S' and r['policy']=='BH' and r['scenario']=='central')
        doc.append(f"| {y} | {d['A_net']:,.0f} | {d['B2_net']:,.0f} | {bh['net_wealth']:,.0f} | {d['composition_and_execution_effect']:,.0f} | {d['differential_tax_effect']:,.0f} | {d['B2_minus_A_net']:,.0f} |")
    doc.append('\n## Vencedor A × B2 por formação\n\n| Regra | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |\n|---|---|---|---|---|---|---|')
    for rule in ['R00','R03','R16','B00','B00S','B06','B06S']:
        doc.append('| '+rule+' | '+' | '.join(next(r['winner'] for r in decomposition if r['formation']==y and r['strategy']==rule and r['scenario']=='central') for y in range(2020,2026))+' |')
    doc.append('\n## Hipóteses e arquivos\n\nO protocolo, as limitações, as fontes e os comandos estão em [protocolo_ir_100k.md](protocolo_ir_100k.md). As tabelas completas, incluindo conservative, estão em [comparison_rankings.csv](../research/ir_100k_results/comparison_rankings.csv). [yearly.csv](../research/ir_100k_results/yearly.csv) discrimina IR devido e efetivamente descontado por ano; [monthly.csv](../research/ir_100k_results/monthly.csv) mostra isenções, ganhos e perdas compensadas. [annual.csv](../research/ir_100k_results/annual.csv) contém retenção, exclusões, entradas financiadas, pesos e custo fiscal. [sensitivities.csv](../research/ir_100k_results/sensitivities.csv) contém todas as sensibilidades nas mesmas políticas. O ledger completo está em `research/ir_100k_results/ledger.json.gz`.\n')
    ranks=tax_ranking_summary(comparison);dump('ranking_tax_effect.csv',ranks)
    section='\n## Efeito do IR sobre o ranking\n\nComparação no universo central, incluindo A, B2 e referências BH. Rank 1 admite empates.\n\n| Formação | Líder sem IR | Líder com IR | Combinações que mudam de posição |\n|---|---|---|---:|\n'
    for r in ranks:section+=f"| {r['formation']} | {r['gross_leader']} | {r['net_leader']} | {r['rank_movements']} |\n"
    section+='\nAs colunas rank_gross, rank_net e rank_change_tax em comparison_rankings.csv registram cada movimento.\n'
    doc.append(section)
    Path('docs').mkdir(exist_ok=True);Path('docs/checkpoint_ir_100k_2026_10_07.md').write_text('\n'.join(doc))
    print('analysis finished',len(comparison),'paired rows',len(sens),'sensitivity runs')
if __name__=='__main__':main()
