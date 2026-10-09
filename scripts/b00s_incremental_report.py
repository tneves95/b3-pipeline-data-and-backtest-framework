"""Append chronological checkpoints without rewriting accepted 2014 documents."""
from b00s_variants import *
from b00s_report import table

def references(section):
    return '; '.join(f"[{e['docid']}/g{e['group']}, páginas {','.join(map(str,e['pages']))}]({e['url']}) (disponível {e['received']})" for e in section['evidence'])

def main():
    verify_accepted_initial()
    verify_decision_freeze()
    allfacts=json.loads((INPUT/'fundamental_decisions.json').read_text())
    annual=read(RESULT/'annual_returns_pct.csv');hold=read(RESULT/'holdings_by_june.csv')
    risk=read(RESULT/'risk_concentration.csv');turn=read(RESULT/'turnover_by_year.csv')
    funding=read(RESULT/'entry_funding_requests.csv') if (RESULT/'entry_funding_requests.csv').exists() else []
    ledger=read(RESULT/'review_ledger.csv')
    for year in range(2015,reviewed_through()+1):
        facts=[r for r in allfacts if r['year']==year]
        a=next(r for r in annual if r['year']==str(year))
        summary=[]
        for v in ['V0','V10','VVAL','VQ','IBOV']:
            rr=[r for r in risk if r['variant']==v and r['date']==DATES[year+1] and r['phase']=='PERIOD_END']
            tt=[r for r in turn if r['variant']==v and r['year']==str(year)]
            summary.append(dict(carteira=v,retorno_pct=float(a[v]),vs_IBOV_pp=float(a[v])-float(a['IBOV']),
                giro_pct=tt[0]['one_way_turnover_pct'] if tt else '',
                empresas_finais=rr[0]['companies'] if rr else '',maior_peso_final_pct=rr[0]['largest_company_pct'] if rr else '',
                top5_final_pct=rr[0]['top5_pct'] if rr else ''))
        freeze=json.loads((INPUT/'decision_freezes'/f'{year}.json').read_text())
        text=f'''# PR #4 — revisão de junho/{year} e retorno até junho/{year+1}

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `{freeze['decision_commit'][:7]}` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

'''+table(summary,list(summary[0]))
        text+='\n\nDiferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.\n'
        cumulative=next(r for r in read(RESULT/'cumulative_returns_pct.csv') if r['closing_year']==str(year+1))
        observed=[]
        for v in ['V0','V10','VVAL','VQ','IBOV']:
            periods=[a for a in annual if 2014<=int(a['year'])<=year and a[v]!='']
            observed.append(dict(carteira=v,periodos=len(periods),acumulado_desde_2014_pct=cumulative[v],
                anos_positivos=sum(float(a[v])>0 for a in periods),anos_acima_IBOV=sum(float(a[v])>float(a['IBOV']) for a in periods) if v!='IBOV' else ''))
        text+='\nObservações acumuladas desde a formação, sem extrapolar anos ainda não revisados:\n\n'+table(observed,list(observed[0]))+'\n'
        text+='\n## Financiamento da renovação\n\nA [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.\n'
        req=[r for r in funding if r['year']==str(year)]
        text+='\n'+(table(req,['variant','ticker','reference_weight_pct','executed_weight_pct']) if req else 'Nenhuma nova entrada aprovada neste corte.')+'\n'
        for v in ['VVAL','VQ']:
            rs=[r for r in ledger if r['variant']==v and r['year']==str(year)]
            kept=[r for r in rs if float(r['before'])>0 and r['base_status']!='FAIL']
            ratios=[float(r['after'])/float(r['before']) for r in kept]
            text+=f"\n{v}: {len(kept)} posições anteriores não reprovadas; fator de capital mantido entre {min(ratios):.8f} e {max(ratios):.8f}. Nenhuma posição não FAIL foi liquidada pelo financiamento.\n" if ratios else ''
        text+='\n## Composição e contribuição por ação\n\n'+table([r for r in hold if r['year']==str(year) and r['variant'] in ['VVAL','VQ']],['variant','row_type','ticker','initial_weight_pct','final_weight_pct','exposure_return_pct','contribution_pp','descendants'])
        text+='\n\nOs pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.\n'
        text+='\n## Concentração\n\n'+table([r for r in risk if r['variant'] in ['VVAL','VQ'] and ((r['date']==DATES[year] and r['phase']=='AFTER_REVIEW') or (r['date']==DATES[year+1] and r['phase']=='PERIOD_END'))],['variant','date','phase','companies','largest_company_pct','top5_pct','issuer_hhi','sector_weights_pct'])
        decisions=[]
        for f in facts:
            dims=f['documentary_assessment']['dimensions'];iv=f['normalized_pe_interval']
            comparable=f['documentary_assessment']['valuation']['status']=='COMPARABLE'
            decisions.append(dict(ticker=f['ticker'],VVAL=f['valuation_status'],PL=f['normalized_pe'] if comparable else '',PL_max=iv['upper'] if iv else '',
                VQ=f['quality_category'],dimensoes_satisfatorias=sum(d['status'] in ['SATISFACTORY','HIGH'] for d in dims.values()),
                dimensoes_ND=sum(d['status']=='INDETERMINATE' for d in dims.values())))
        text+='\n\n## Decisões de entrada anteriores aos retornos\n\n'+table(decisions,list(decisions[0]))
        mature=[f['ticker'] for f in facts if f['valuation_status']=='PASS_MATURE']
        productive=[f['ticker'] for f in facts if f['valuation_status']=='PASS_REINVESTOR']
        text+='\n\nCanal até P/L 15: '+', '.join(mature)+'. Canal de reinvestimento produtivo entre 15 e 25: '+(', '.join(productive) if productive else 'nenhuma aprovação comprovada neste corte')+'. A classificação do canal de preço não presume que uma empresa deixou de investir.\n'
        premium=[]
        for f in facts:
            if f['normalized_pe'] is not None and 15<f['normalized_pe']<=25:
                premium.append(dict(ticker=f['ticker'],PL=f['normalized_pe'],crescimento_real_LPA_pct=100*f['real_eps_cagr'] if f['real_eps_cagr'] is not None else 'ND',
                    payout_medio_pct=100*f['average_payout'] if f['average_payout'] is not None else 'ND',
                    retorno_capital_pct=100*f['return_on_capital_median'] if f['return_on_capital_median'] is not None else 'ND',
                    medida=f['return_on_capital_kind'],minimo_IPCA_mais_6_pct=100*(f['inflation_reference']+.06),decisao=f['valuation_status']))
        if premium:text+='\n'+table(premium,list(premium[0]))+'\n'
        text+=f'\n\n[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_{year}.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.\n'
        text+='\n## Verificação e reprodução\n\n`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.\n\nTestes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.\n'
        (ROOT/f'docs/checkpoint_b00s_{year}_{year+1}.md').write_text('\n'.join(line.rstrip() for line in text.splitlines())+'\n')
        dossier=f'# Revisão fundamentalista e de valuation — junho/{year}\n\nReutiliza o [dossiê aceito de 2014](dossies_b00s_v2.md). Atualizações abaixo distinguem fatos novos, julgamentos e pendências. Seis dimensões não compensatórias; sem score e sem aprovação por ausência de informação. A decisão de entrada é separada da manutenção B2.\n'
        for f in facts:
            r=f['documentary_assessment'];dossier+=f"\n## {f['ticker']}\n\nVVAL: **{f['valuation_status']}**; VQ: **{f['quality_category']}**.\n\n{r['incremental_review']['reason']}\n\nValuation: {r['valuation']['reason']}\n\n"
            if f['normalized_pe_interval']:dossier+=f"P/L por intervalo: {f['normalized_pe_interval']}. Não representa um ponto estimado.\n\n"
            for k,d in r['dimensions'].items():
                dossier+=f"**{k} — {d['status']}.** {d['reason']}\n\nContraponto anterior reavaliado: {d['contrary_evidence']}\n\n"
                if d.get('missing'):dossier+='Pendência específica: '+d['missing']+'\n\n'
            dossier+='Fontes da atualização: '+references(r['incremental_review'])+'.\n\nFontes do valuation: '+references(r['valuation'])+'.\n'
            if r.get('economic_metrics'):
                dossier+='\nProva econômica:\n\n```json\n'+json.dumps(r['economic_metrics'],ensure_ascii=False,indent=2)+'\n```\n'
        (ROOT/f'docs/dossies_b00s_{year}.md').write_text('\n'.join(line.rstrip() for line in dossier.splitlines())+'\n')
    verify_accepted_initial()

if __name__=='__main__':main()
