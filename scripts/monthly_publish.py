"""Write PR #5 CSV/XLSX only; older studies are immutable inputs."""
from __future__ import annotations
from datetime import date
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import statistics

from b00s_variants import read,write,jsonwrite,sha
from stage1_pit import ROOT,OUT
from monthly_inputs import STUDY,START,END,BASELINE
from monthly_contributions import simulate,benchmark,load_quotes,events,frozen_compositions,PORTFOLIOS


def verify_protected():
    manifest=json.loads((STUDY/'inputs/protected_pr3_pr4.json').read_text())
    for r in manifest['files']:
        with (ROOT/r['path']).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=r['sha256']:raise ValueError(('Protected artifact modified',r['path']))
    return len(manifest['files'])


def monthly_returns(result):
    wealth=result['wealth'];portfolio=result['summary']['portfolio']
    previous=next(w['nav'] for w in wealth if w['date']==START)
    cumulative=1.;rows=[];points={r['date']:float(r['close']) for r in read(STUDY/'inputs/ibov_daily.csv')}
    prior_date=START
    for r in result['contributions']:
        month=r['date'][:7]
        last=next(w for w in wealth if w['date'].startswith(month) and w['phase']=='MONTH_END')
        nav=last['nav']
        if portfolio=='IBOV':ret=points[last['date']]/points[prior_date]-1
        else:
            ret=(r['nav_before']/previous)*(nav/r['nav_after'])-1 if all(v is not None for v in [r['nav_before'],r['nav_after'],nav,previous]) else None
        cumulative=cumulative*(1+ret) if ret is not None and cumulative is not None else None
        rows.append(dict(portfolio=portfolio,month=month,date=last['date'],nav=nav,external_capital=last['external_capital'],
            monthly_twr_pct=100*ret if ret is not None else None,cumulative_twr_pct=100*(cumulative-1) if cumulative is not None else None,
            status='EXACT_FLOW_ADJUSTED_TWR' if ret is not None else 'ND_MISSING_EXACT_MARK'))
        previous=nav;prior_date=last['date']
    return rows


def risk_metrics(result):
    monthly=monthly_returns(result)
    returns=[r['monthly_twr_pct']/100 for r in monthly if r['monthly_twr_pct'] is not None]
    all_valid=len(returns)==len(monthly)
    vol=statistics.stdev(returns)*math.sqrt(12)*100 if len(returns)>1 else None
    peak=1.;lowest=0.;index=1.
    if all_valid:
        for r in returns:
            index*=1+r;peak=max(peak,index);lowest=min(lowest,index/peak-1)
    return dict(monthly_volatility_annualized_pct=vol,volatility_valid_months=len(returns),
        volatility_status='ALL_144_MONTHS' if all_valid and len(monthly)==144 else 'AVAILABLE_MONTHS_ONLY',
        maximum_drawdown_pct=100*lowest if all_valid else None,
        drawdown_status='MONTH_END_TWR_INDEX' if all_valid else 'ND_CUMULATIVE_TWR_GAP'),monthly


def union_write(path,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    write(path,[dict.fromkeys(fields,'')|r for r in rows])


def export(results,destination):
    destination.mkdir(parents=True,exist_ok=True)
    ibov=next(r['summary']['final_wealth'] for r in results if r['summary']['portfolio']=='IBOV')
    summaries=[];monthly=[]
    for r in results:
        risk,m=risk_metrics(r);monthly.extend(m)
        summary=r['summary']|risk|dict(wealth_difference_vs_ibov=r['summary']['final_wealth']-ibov,
            wealth_ratio_vs_ibov=r['summary']['final_wealth']/ibov,
            external_contributions_total=r['summary']['external_capital']-100000,
            external_cash_final=0. if r['summary']['cash']==0 else None,
            external_contributions_invested=r['summary']['external_capital']-100000 if r['summary']['cash']==0 else None)
        summaries.append(summary)
    # Legal issuer concentration complements the lineage used for buy targets.
    labels={r['cnpj']:(r['company'],r['sector'])
        for r in reversed(read(ROOT/'research/b00s_four_variants_2014_2026/results/selection_decisions.csv'))}
    labels.update({r['cnpj']:(r['company'],r['block']) for r in read(OUT/'bh_selection_2014.csv')})
    for result,summary in zip(results,summaries):
        issuer_values={};sector_values={}
        for r in result['positions']:
            issuer='XP_INC_BDR' if r['ticker']=='XPBR31' else r['lineage']
            company,sector=labels.get(r['lineage'],(r['ticker'],'Índice'))
            if r['ticker']=='XPBR31':company,sector='XP (cisão compulsória)','Outros (cisão)'
            r.update(company=company,sector=sector,economic_issuer=issuer)
            if r['date']==summary['end'] and r['phase']=='MONTH_END':
                issuer_values[issuer]=issuer_values.get(issuer,0)+r['position_value']
                sector_values[sector]=sector_values.get(sector,0)+r['position_value']
        nav=summary['final_wealth']
        summary.update(economic_issuers_final=len(issuer_values),issuer_hhi=sum((v/nav)**2 for v in issuer_values.values()),
            maximum_issuer_weight=max(issuer_values.values())/nav,
            sector_hhi=sum((v/nav)**2 for v in sector_values.values()),sector_weights=json.dumps({s:v/nav for s,v in sector_values.items()},ensure_ascii=False,sort_keys=True))
    write(destination/'consolidated.csv',summaries)
    names={'contributions':'contributions_ledger','trades':'operations','positions':'monthly_positions',
        'wealth':'monthly_wealth','event_ledger':'internal_events_ledger','junes':'june_reviews','annual':'annual_and_cumulative_returns'}
    for key,name in names.items():
        selected=[r for r in results if key!='contributions' or r['summary']['portfolio']!='IBOV']
        union_write(destination/f'{name}.csv',[row for r in selected for row in r[key]])
    union_write(destination/'benchmark_contributions_ledger.csv',[row for r in results if r['summary']['portfolio']=='IBOV' for row in r['contributions']])
    write(destination/'monthly_returns.csv',monthly)
    flows=[dict(portfolio=r['summary']['portfolio'],date=d,investor_cash_flow=v,
        flow_type='FINAL_NAV' if i==len(r['flows'])-1 else 'INITIAL_CAPITAL' if i==0 else 'MONTHLY_DEPOSIT')
        for r in results for i,(d,v) in enumerate(r['flows'])]
    write(destination/'investor_cash_flows.csv',flows)
    attribution=[]
    for result in results:
        if result['summary']['portfolio']=='IBOV':continue
        final=result['summary']['end']
        positions=[r for r in result['positions'] if r['date']==final and r['phase']=='MONTH_END']
        origins=set(r['lineage'] for r in result['trades'])|{r['lineage'] for r in positions}
        for c in sorted(origins):
            trades=[r for r in result['trades'] if r['lineage']==c]
            bought=math.fsum(r['amount'] for r in trades if r['side']=='BUY')
            sold=math.fsum(r['amount'] for r in trades if r['side']=='SELL')
            proceeds=math.fsum(r.get('compulsory_cash_entitlement',0) for r in result['event_ledger'] if r['lineage']==c)
            value=math.fsum(r['position_value'] for r in positions if r['lineage']==c)
            gain=value+sold+proceeds-bought
            attribution.append(dict(portfolio=result['summary']['portfolio'],lineage=c,
                securities=';'.join(sorted({r['ticker'] for r in positions if r['lineage']==c})),
                total_purchases=bought,total_voluntary_sales=sold,compulsory_cash_proceeds=proceeds,
                final_value=value,economic_gain=gain,gain_contribution_to_total=gain/result['summary']['gain_after_external_capital']))
        actual=math.fsum(r['economic_gain'] for r in attribution if r['portfolio']==result['summary']['portfolio'])
        expected=result['summary']['gain_after_external_capital']-result['summary']['cash']
        if not math.isclose(actual,expected,rel_tol=3e-12,abs_tol=1e-7):raise ValueError(('Monetary attribution mismatch',actual,expected))
    write(destination/'lineage_cash_attribution.csv',attribution)
    return summaries


def sensitivities(results):
    q,_=load_quotes();es=events();cs=frozen_compositions();rows=[]
    main={r['summary']['portfolio']:r['summary'] for r in results}
    cases=[('BBDC4_2014_NOT_ADMITTED','VVAL',dict(initial_exclude_bradesco=True)),
           ('NO_WINNER_PRESERVATION','V0',dict(protect=False))]
    for name,portfolio,kwargs in cases:
        r=simulate(portfolio,q,es,cs,**kwargs);s=r['summary'];base=main[portfolio]
        rows.append(dict(scenario=name,portfolio=portfolio,final_wealth=s['final_wealth'],
            wealth_difference_vs_main=s['final_wealth']-base['final_wealth'],xirr_pct=s['xirr_pct'],
            xirr_difference_pp=s['xirr_pct']-base['xirr_pct'],twr_pct=s['twr_pct'],
            status='CALCULATED_WITH_INHERITED_PRICE_GAPS',reason='Original 2015 PASS allows Bradesco entry in June2015' if name.startswith('BBDC') else 'Full equal weights on composition change; no winner protection or 2/N calendar clipping'))
        export([r,benchmark()],STUDY/'sensitivities'/name)
        print('Sensitivity',name,s['final_wealth'],s['xirr_pct'],flush=True)
    for portfolio in ['VVAL','V10','BH padrão','BESST-10 BH']:
        rows.append(dict(scenario='NO_WINNER_PRESERVATION',portfolio=portfolio,final_wealth=main[portfolio]['final_wealth'],
            wealth_difference_vs_main=0.,xirr_pct=main[portfolio]['xirr_pct'],xirr_difference_pp=0.,twr_pct=main[portfolio]['twr_pct'],
            status='IDENTICAL_RULE_NOT_ACTIVATED',reason='N never exceeds 15, or BH does not voluntarily rebalance'))
    for name,portfolio,reason in [
        ('VVAL_STRICT_MONTHLY_PRICE_GATE','VVAL','The frozen decisions certify June admission gates; an updated documentary normalization for every intra-year month is not available. No unproved monthly approvals or new issuer selection.'),
        ('BESST_NET_REPLACES_TIM','BESST-10 BH','NET missing ON close can change capitalization rank; the inherited event book does not certify its 2014 compulsory exit and successor/cash trajectory. No fabricated final market price.')]:
        rows.append(dict(scenario=name,portfolio=portfolio,final_wealth=None,wealth_difference_vs_main=None,xirr_pct=None,
            xirr_difference_pp=None,twr_pct=None,status='ND',reason=reason))
    write(STUDY/'sensitivities.csv',rows)
    return rows


def workbook(path):
    import xlsxwriter
    w=xlsxwriter.Workbook(path,{'constant_memory':True})
    header=w.add_format({'bold':True,'bg_color':'#183153','font_color':'white','text_wrap':True})
    money=w.add_format({'num_format':'R$ #,##0.00'});number=w.add_format({'num_format':'0.0000'})
    percent=w.add_format({'num_format':'0.00%'});percent_points=w.add_format({'num_format':'0.0000"%"'})
    dt=w.add_format({'num_format':'dd/mm/yyyy'})
    tables=[('Consolidado','consolidated'),('Patrimonio','monthly_wealth'),('Posicoes','monthly_positions'),
        ('Aportes','contributions_ledger'),('IBOV Aportes','benchmark_contributions_ledger'),('Operacoes','operations'),
        ('Eventos','internal_events_ledger'),('Revisoes Junho','june_reviews'),('Retornos anuais','annual_and_cumulative_returns'),
        ('Retornos mensais','monthly_returns'),('Sensibilidades','sensitivities'),('Ranking BESST','besst10_bh_ranking_2014'),
        ('Selecao BESST','besst10_bh_selection_2014'),('Atribuicao R$','lineage_cash_attribution'),('Cobertura precos','quote_coverage')]
    for title,stem in tables:
        rows=read(STUDY/f'{stem}.csv');sheet=w.add_worksheet(title)
        if not rows:continue
        fields=list(rows[0]);sheet.write_row(0,0,fields,header);sheet.freeze_panes(1,1);sheet.autofilter(0,0,len(rows),len(fields)-1)
        sheet.set_row(0,38);sheet.set_column(0,len(fields)-1,18)
        for i,r in enumerate(rows,1):
            for j,key in enumerate(fields):
                value=r[key]
                if value=='':continue
                if key=='date':sheet.write_datetime(i,j,date.fromisoformat(value),dt);continue
                if key in ['cnpj','lineage','capital_docid','sector_docid','quote_line'] or 'sha256' in key:sheet.write_string(i,j,value);continue
                try:v=float(value)
                except ValueError:sheet.write_string(i,j,value);continue
                fmt=percent_points if key.endswith('_pct') else percent if 'weight' in key and 'wealth' not in key else money if any(t in key for t in ['wealth','nav','cash','amount','value','capital','gain','deposit','purchases','sales','proceeds']) and 'ratio' not in key and 'docid' not in key else number
                sheet.write_number(i,j,v,fmt)
    chart_data=w.add_worksheet('Grafico patrimonio');names=['VVAL','V0','V10','BH padrão','BESST-10 BH','IBOV']
    chart_data.write_row(0,0,['date']+names,header)
    wealth=read(STUDY/'monthly_wealth.csv');months=read(STUDY/'contribution_calendar.csv')
    lookup={(r['portfolio'],r['date']):r['nav'] for r in wealth if r['phase']=='MONTH_END'}
    for i,r in enumerate(months,1):
        chart_data.write_datetime(i,0,date.fromisoformat(r['month_end']),dt)
        for j,name in enumerate(names,1):
            v=lookup.get((name,r['month_end']))
            if v:chart_data.write_number(i,j,float(v),money)
    chart=w.add_chart({'type':'line'})
    for j,name in enumerate(names,1):chart.add_series({'name':name,'categories':['Grafico patrimonio',1,0,144,0],
        'values':['Grafico patrimonio',1,j,144,j],'line':{'width':1.5}})
    chart.set_title({'name':'Patrimônio com os mesmos 144 aportes'});chart.set_y_axis({'num_format':'R$ #,##0'});chart.set_x_axis({'date_axis':True});chart.show_blanks_as('gap')
    chart_data.insert_chart('I2',chart,{'x_scale':1.7,'y_scale':1.6})
    notes=w.add_worksheet('Premissas');notes.set_column(0,0,110)
    lines=['R$100.000 iniciais e 144 depósitos de R$2.500 por carteira; total R$460.000.',
        'Sem impostos/custos; frações; proventos na data econômica ex conforme motores aceitos.',
        'V0/VVAL: TWR integral ND onde uma data de aporte carece de marcação exata. Patrimônio e TIR seguem calculáveis.',
        'BESST-10 BH condicional: NET sem cotação ON contemporânea; units/identidades pendentes no inventário.',
        'CSV é a fonte primária; células em branco indicam ND, nunca zero estimado.',
        'Atribuição em reais = valor final + vendas voluntárias + resgates compulsórios − compras.',
        'PRs #3/#4 preservados; consultar docs/estudo_aportes_mensais_cinco_carteiras.md e o protocolo congelado.']
    for i,line in enumerate(lines):notes.write(i,0,line)
    w.close()


def report(summaries,sens):
    def br(v,dec=2):
        if v is None or v=='':return 'ND'
        return f'{float(v):,.{dec}f}'.translate(str.maketrans(',.','.,'))
    order=['VVAL','V0','V10','BH padrão','BESST-10 BH','IBOV'];data={r['portfolio']:r for r in summaries}
    lines=['# Cinco carteiras com aportes mensais — junho/2014 a junho/2026','',
        'As cinco carteiras foram reconstruídas com R$ 100.000 iniciais e 144 aportes de R$ 2.500 no primeiro pregão de cada mês. Cada investidor aplicou R$ 460.000. As seleções PIT e os eventos aceitos dos PRs #3/#4 foram preservados; a ponderação monetária é nova, igual por linhagem. Sem impostos, custos ou ações inteiras; reinvestimento econômico teórico na data ex, sem simular liquidação operacional.','',
        '**Resultado qualificado:** patrimônio final e XIRR são calculáveis nas cinco trajetórias. TWR integral V0/VVAL fica ND nas datas sem marcação exata; BESST-10 BH é condicional à pendência de capitalização NET/ON e às limitações documentais do universo. Estes números não certificam dados herdados nem autorizam mudar decisões fundamentalistas.','',
        '| Métrica | VVAL | V0 | B00S-10 | BH padrão | BESST-10 BH condicional | IBOV com aportes |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for label,key,prefix,suffix in [('Patrimônio final','final_wealth','R$ ',''),('Capital externo','external_capital','R$ ',''),
        ('Ganho acima dos aportes','gain_after_external_capital','R$ ',''),('TIR anual','xirr_pct','','%'),
        ('TWR acumulado','twr_pct','','%'),('CAGR do TWR','twr_cagr_pct','','%'),
        ('Diferença patrimonial vs IBOV','wealth_difference_vs_ibov','R$ ',''),('Caixa final','cash','R$ ','')]:
        values=[br(data[n][key],4 if suffix else 2) for n in order]
        lines.append('| '+label+' | '+' | '.join('ND' if v=='ND' else prefix+v+suffix for v in values)+' |')
    lines+=['','## Composição, pesos e concentração','',
        '| Carteira | Linhagens ativas finais | Maior peso final | HHI de linhagens | Giro acumulado de junho | Vendas voluntárias |',
        '|---|---:|---:|---:|---:|---:|']
    for n in order:
        s=data[n];lines.append(f'| {n} | {s["active_lineages"]} | {br(100*s["maximum_lineage_weight"],4)}% | {br(s["lineage_hhi"],6)} | {br(100*s["june_turnover_sum"],4)}% | {s["voluntary_sales"]} |')
    lines+=['',
        'As classes de uma companhia e seus direitos não multiplicam alvos. XP conserva o valor dentro da origem Itaú e não recebe compras mensais; sucessões de ticker/classes recebem as quantidades aceitas. Os CSVs informam quantidade, cotação nominal, peso da classe, peso da linhagem, alvo, limite e origem de cada preço. O peso de referência orienta compras, sem venda BH ou reset de calendário. O giro soma `min(vendas, compras)/NAV` nas revisões; não soma depósitos ou eventos compulsórios.','',
        'Atribuição monetária: `lineage_cash_attribution.csv` separa compras, vendas, resgates e valor final por origem. A soma do ganho por linhagem reconcilia o patrimônio menos capital externo e caixa, sem tratar proventos como aportes. Essa contribuição em reais não é uma rentabilidade percentual de uma ação comprada em datas diferentes.','',
        '## Sensibilidades e pendências materiais','',
        '| Cenário | Carteira | Patrimônio | Diferença vs principal | TIR anual | Status |',
        '|---|---|---:|---:|---:|---|']
    for r in sens:lines.append(f'| {r["scenario"]} | {r["portfolio"]} | {br(r["final_wealth"])} | {br(r["wealth_difference_vs_main"])} | {br(r["xirr_pct"],4)} | {r["status"]} |')
    lines+=['',
        'Bradesco é excluído apenas na formação de 2014 na sensibilidade obrigatória. A decisão congelada `PASS_MATURE` de junho/2015 permite sua admissão naquele corte, com a mesma cronologia posterior. Não se exclui Bradesco para sempre nem se reescreve o parecer HIGH do PR #4. Os livros completos do cenário estão em `sensitivities/BBDC4_2014_NOT_ADMITTED/`.','',
        'V0 mantém em caixa os depósitos de 01/07/2014 e 02/01/2015, até o mês seguinte, por não haver preço de ABCB2 no fechamento dessas datas. V0 e VVAL mantêm o depósito de 01/09/2023 até outubro, porque ENBR3 não negocia e o preço final do resgate só foi divulgado em 05/09. Os proventos e o principal compulsório continuam no evento aceito. Nenhum preço foi interpolado, carregado indefinidamente ou antecipado. O principal de R$ 24,23 é usado em 13/09/2023, não em agosto. Patrimônio/XIRR não exigem preços nesses cortes sem operação, mas TWR com o fluxo externo exige NAV completo naquele dia; por isso a lacuna não é ocultada.','',
        'TWR anual continua publicado nos períodos com todos os NAV de aporte conhecidos. Volatilidade anualizada usa desvio padrão dos retornos mensais exatamente calculáveis × √12, com contagem explícita. Drawdown usa o índice TWR de fechamento mensal e é ND se sua cadeia tiver lacuna; não confunde perda de mercado com depósitos.','',
        'O BESST principal congela Itaú/Bradesco, Tractebel/Cemig, Sabesp/Copasa, BB Seguridade/Porto, Telefônica/TIM. NET não tem cotação ON contemporânea. Paridade ON/PN e último negócio ON deixam NET abaixo da TIM; um cenário ON=2×PN ultrapassa a TIM. Isso é cenário, não prova ou limite matemático. A alternativa NET→TIM depende de comprovar sua saída compulsória/caixa em 2014–2015 e está ND; o relatório não fabrica sucessor. SulAmérica fica abaixo de Porto sob a restrição de preço da unit documentada; dobrar simultaneamente todas as classes violaria o preço observado. Renova/Contax e o unit de dois CNPJs do BTG têm ressalvas de prova no inventário.','',
        'As normalizações fundamentalistas congeladas cobrem junho, não todos os 144 meses. O diagnóstico de admissão mensal estrita VVAL é ND; o principal aplica a regra autorizada de manutenção dos incumbentes, sem admitir novos emissores fora de junho. Os dois proventos iniciais BBSE reutilizam a transcrição do cache B3; os demais eventos seguem os valores aceitos. A remuneração BBSE antiga não recebeu nova certificação primária neste estudo.','',
        '## Reprodução e checkpoints','',
        '```bash','python scripts/monthly_publish.py --complete','python -m pytest -q tests/test_monthly_contributions.py','```','',
        'Lote 1 `27392d5`: ranking/calendário/preços, antes dos resultados. Lote 2 `7908141`: motor, 24 contribuições e controles completos. O controle sem aportes reproduz o BH legado nos 13 fechamentos de junho; sua ponderação inicial e ausência de revisão são iguais. Não se exige coincidência entre o novo peso igual e a antiga ponderação setorial B2.','',
        'Artefatos principais: `consolidated.csv`, `contributions_ledger.csv` (720 depósitos das cinco carteiras), `benchmark_contributions_ledger.csv` (144 IBOV), `monthly_positions.csv`, `monthly_wealth.csv`, `operations.csv`, `internal_events_ledger.csv`, `june_reviews.csv`, `annual_and_cumulative_returns.csv`, `monthly_returns.csv`, `lineage_cash_attribution.csv`, `sensitivities.csv`, planilha e manifest. CSV é a referência primária. Células vazias documentam ND.','',
        'Os 3.567 arquivos do baseline `8671156`, incluindo auditoria e PR #3, são conferidos por SHA-256. A CI do novo estudo é isolada. O PR #5 permanece draft, sem merge.']
    (ROOT/'docs/estudo_aportes_mensais_cinco_carteiras.md').write_text('\n'.join(lines)+'\n')


def complete(results,summaries):
    sens=sensitivities(results);report(summaries,sens)
    workbook(STUDY/'aportes_mensais_cinco_carteiras.xlsx')
    protected=verify_protected()
    files=[p for p in sorted(STUDY.rglob('*')) if p.is_file() and p.name!='manifest.json']
    jsonwrite(STUDY/'manifest.json',dict(baseline_commit=BASELINE,starting_commit='7588d52dfd6564f6fb2b86737af1eaa8660a043f',
        protected_files_verified=protected,portfolios=list(PORTFOLIOS),monthly_dates=144,
        initial_capital=100000,monthly_contribution=2500,total_external_per_investor=460000,
        principal_contribution_rows=720,benchmark_contribution_rows=144,
        status='NUMERICAL_TRAJECTORIES_COMPLETE_WITH_EXPLICIT_ND_TWR_AND_CONDITIONAL_BESST_RANKING',
        selection_changed=False,older_results_modified=False,pr_draft=True,merged=False,
        sources_and_outputs=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files],
        implementation=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [
            ROOT/'scripts/monthly_contributions.py',ROOT/'scripts/monthly_inputs.py',ROOT/'scripts/monthly_publish.py',
            ROOT/'tests/test_monthly_contributions.py',ROOT/'docs/estudo_aportes_mensais_cinco_carteiras.md']]))
    print('Final artifacts',len(files),'Protected',protected,flush=True)


def run_batch(end,portfolios,destination):
    q,provenance=load_quotes();byday=events();compositions=frozen_compositions();results=[]
    for p in portfolios:
        result=simulate(p,q,byday,compositions,end=end)
        for row in result['positions']+result['trades']:
            source=provenance.get((row['ticker'],row['date']),{})
            row.update(observed_ticker=source.get('ticker',''),isin=source.get('isin_code',''),
                quote_source=source.get('source',''),quotation_factor=source.get('quotation_factor',''),
                zip_sha256=source.get('zip_sha256',''),record_sha256=source.get('record_sha256',''),quote_line=source.get('line',''))
        results.append(result)
        print(json.dumps(result['summary'],ensure_ascii=False),flush=True)
    bench=benchmark(end=end)
    bench_sources={r['date']:r for r in read(STUDY/'inputs/ibov_daily.csv')}
    for row in bench['positions']+bench['trades']:
        source=bench_sources[row['date']]
        row.update(observed_ticker='IBOV',isin='',quote_source=source['source'],quotation_factor=1,
            zip_sha256='',record_sha256=source['source_sha256'],quote_line='')
    results.append(bench);summaries=export(results,destination)
    return results,summaries


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--end',default=END);p.add_argument('--portfolios',nargs='+',default=list(PORTFOLIOS));p.add_argument('--output-dir',type=Path,default=STUDY);p.add_argument('--complete',action='store_true')
    args=p.parse_args();results,summaries=run_batch(args.end,args.portfolios,args.output_dir)
    if args.complete:
        if args.end!=END or set(args.portfolios)!=set(PORTFOLIOS) or args.output_dir!=STUDY:raise ValueError('Complete publication requires all five portfolios through June2026 in the study directory')
        complete(results,summaries)
