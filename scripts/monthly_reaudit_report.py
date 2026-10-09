"""Small numerical checkpoints for reaudited maintenance; preserve prior reports."""
from collections import Counter,defaultdict
from datetime import datetime
import argparse
import csv
import hashlib
import json
from pathlib import Path
import xlsxwriter
from run_monthly_reaudited import ROOT,OUT,guard_legacy
from monthly_maintenance_reaudit import guard_prior
from run_monthly_tax import write

MODES=['GROSS','CG_ONLY','CG_PLUS_JCP_CERTIFIED_PARTIAL']
NAMES=['consolidated_policy_corrected','consolidated_tax_corrected','consolidated_income_corrected']


def read(p):
    with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))


def fmt(v,n=2):return f'{float(v):,.{n}f}'.replace(',','X').replace('.',',').replace('X','.')


NOTES='''A auditoria anterior identificou nove saídas sem fundamentação suficiente: TIET11/2016 (classe errada), CPFE3/2020 (lacuna de provento não prova ausência), BRSR6/2021 e SBSP3/2024 (zeros contraditos por DFP PIT). Elas foram anuladas. Os quatro emissores foram revistos nos junhos seguintes com os insumos preservados. TIET11 permaneceu, converteu-se compulsoriamente em AESB3 e depois AURE3; AURE3 teve FAIL comprovado em2025, incluindo uma nova saída na VVAL. Histórico ausente ou zeros de uma sociedade sucessora antes da reorganização não viraram prova de FAIL. CPFE/2020 permanece INDETERMINATE, sem inventar o provento ausente.

Na V10, a permanência de SBSP3 mantém ocupadas as duas vagas de saneamento com SAPR4. CSMG3 não substitui SBSP3 em2024/2025; não se cria uma terceira vaga nem se vende um incumbente. As demais candidatas e a ordem de liquidez PIT congelada são preservadas. Nenhuma venda por valorização, concentração, peso, ausência da lista de compras ou entrada de outra empresa. O marcador de vencedora persiste e2× regula somente novas compras. BH não vende voluntariamente.

Escopo: revisão dos achados e junhos posteriores dessas quatro linhagens; as demais saídas comprovadas pela auditoria anterior são mantidas. O filtro de liquidez de COCE5 é a convenção já codificada, não uma certificação nova de que liquidez deve integrar permanência. CNPJ do sucessor contemporâneo é usado para seus demonstrativos; não se atribui ao antecessor uma história fictícia. Os fatos ausentes permanecem ND. Não é reauditoria integral de todos os emissores.
'''


def gross_checkpoint():
    gross=sorted(read(OUT/(NAMES[0]+'.csv')),key=lambda r:int(r['rank']))
    text='''# Checkpoint bruto após reauditoria de permanência — PR #6

Cinco trajetórias efetivamente recalculadas: R$100.000 iniciais +144 aportes de R$2.500 = R$460.000 externos por carteira. Posição mantida em30/06/2026, sem IR neste checkpoint. Dados/código/checkpoints anteriores preservados; PR #6 draft, sem merge.

| Carteira | Bruto R$ | TIR % a.a. | Δ checkpoint bruto anterior R$ | Δ PR5 original R$ | Maior emissor % | HHI emissores | Vendas voluntárias anteriores → atuais |
|---|---:|---:|---:|---:|---:|---:|---:|
'''
    for r in gross:
        text+=f"| {r['portfolio']} | {fmt(r['final_wealth'])} | {fmt(r['xirr_pct'],4)} | {fmt(r['delta_previous_wealth'])} | {fmt(r['delta_pr5_wealth'])} | {fmt(float(r['maximum_issuer_weight'])*100)} | {fmt(r['issuer_hhi'],6)} | {r['previous_checkpoint_voluntary_sales']} → {r['voluntary_sales']} |\n"
    text+='\nRanking bruto: **'+' > '.join(r['portfolio'] for r in gross)+'**. BESST-10 BH ultrapassa VVAL pela revisão econômica das saídas; isto ocorre antes da tributação.\n\n'+NOTES
    trades=read(OUT/'GROSS/trades.csv');reviews=read(OUT/'maintenance_reviews.csv')
    sales=[]
    for t in trades:
        if t['side']=='SELL':
            p=reviews[int(t['proof_line'])-2]
            sales.append(dict(**t,fail_basis=p['fail_basis'],nonpositive_years=p['nonpositive_years'],issuer_cnpj=p['issuer_cnpj']))
    write(OUT/'gross_sales_substantive_evidence.csv',sales)
    text+='\n| Saída / junho | Carteiras | Fundamentação |\n|---|---|---|\n'
    groups=defaultdict(list)
    for r in sales:groups[r['ticker'],r['date'],r['fail_basis']].append(r['portfolio'])
    for (t,d,b),ps in sorted(groups.items(),key=lambda kv:(kv[0][1],kv[0][0])):text+=f"| {t} / {d[:4]} | {', '.join(sorted(ps))} | {b} |\n"
    text+='''
Mantidos preços e eventos aceitos, inclusive a ressalva NET/TIMP3 da BESST-10 BH. Não houve nova pesquisa de NET, novos proventos ou seleção pelo retorno posterior. Compras fracionárias, ausência de custos e reinvestimento na data-ex são convenções herdadas. Patrimônio e TIR calculáveis; TWR permanece ND onde faltam cotações nas datas de fluxo. Os livros discriminam caixa e compras adiadas.

Reprodução: `python scripts/monthly_maintenance_reaudit.py`, depois `python scripts/run_monthly_reaudited.py --mode GROSS`. Arquivos em `research/monthly_reaudited_2014_2026/GROSS/`, consolidado `consolidated_policy_corrected.csv`, provas `maintenance_reviews.csv` e `maintenance_pit_facts.csv`. Testes: `tests/test_monthly_reaudit.py` e as59 regressões anteriores. O próximo checkpoint aplica CG_ONLY às trajetórias acima e reaproveita a camada fiscal existente.
'''
    (OUT/'checkpoint_gross_comment.md').write_text(text)
    (ROOT/'docs/checkpoint_reauditoria_aportes_bruto_2014_2026.md').write_text(text)
    return gross


def full_checkpoint(gross):
    allrows=[r for name in NAMES for r in read(OUT/(name+'.csv'))]
    for r in allrows:
        r['total_additional_tax_paid_modeled']=float(r['tax_paid'])+float(r['income_withheld'])
        r['full_historical_certified_wealth']='ND'
    write(OUT/'all_reaudited_scenarios.csv',allrows)
    by={(r['mode'],r['portfolio']):r for r in allrows}
    text='''# Checkpoint tributário após reauditoria de permanência — PR #6

15 trajetórias recalculadas mensalmente, comR$100 mil iniciais e144 aportes deR$2.500. Os nove FAIL questionados foram retirados; suas empresas/sucessoras tiveram revisão posterior. Checkpoints anteriores preservados em seus diretórios. PR #6 draft, sem merge.

| Carteira | Bruto R$ | CG_ONLY R$ | JCP sustentado parcial R$ | TIR parcial % a.a. | IR realizações pago R$ | JCP adicional R$ | IR modelado total R$ | Δ parcial anterior R$ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
'''
    ordered=sorted((r for r in allrows if r['mode']==MODES[-1]),key=lambda r:int(r['rank']))
    for r in ordered:
        p=r['portfolio'];g=by['GROSS',p];c=by['CG_ONLY',p]
        text+=f"| {p} | {fmt(g['final_wealth'])} | {fmt(c['final_wealth'])} | {fmt(r['final_wealth'])} | {fmt(r['xirr_pct'],4)} | {fmt(r['tax_paid'])} | {fmt(r['income_withheld'])} | {fmt(r['total_additional_tax_paid_modeled'])} | {fmt(r['delta_previous_wealth'])} |\n"
    text+='\nRankings efetivamente calculados:\n\n'
    for mode in MODES:
        ranked=sorted((r for r in allrows if r['mode']==mode),key=lambda r:int(r['rank']))
        text+='- '+mode+': **'+' > '.join(r['portfolio'] for r in ranked)+'**.\n'
    text+='\nA mudança VVAL/BESST é econômica e já aparece no bruto. O efeito tributário é medido contra esse novo bruto, mantendo o mesmo protocolo fiscal; os reinvestimentos são recalculados e menores. A diferença patrimonial inclui rendimentos posteriores que deixam de ser obtidos e não equivale à soma nominal dos impostos.\n\n'
    text+='| Carteira | TIR bruta % | TIR CG_ONLY % | Queda bruto → parcial R$ | Maior emissor parcial % | HHI parcial | Giro junho acumulado % | Vendas voluntárias |\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
    for r in ordered:
        p=r['portfolio'];g=by['GROSS',p];c=by['CG_ONLY',p]
        text+=f"| {p} | {fmt(g['xirr_pct'],4)} | {fmt(c['xirr_pct'],4)} | {fmt(float(g['final_wealth'])-float(r['final_wealth']))} | {fmt(float(r['maximum_issuer_weight'])*100)} | {fmt(r['issuer_hhi'],6)} | {fmt(float(r['june_turnover_sum'])*100)} | {r['voluntary_sales']} |\n"
    text+='\n'+NOTES
    text+='''
## Liquidação integral separada em30/06/2026

As posições efetivas e custos médios do caso com JCP parcial são liquidados em cópia independente. O imposto incremental é deduzido economicamente, ainda que o DARF vença depois do horizonte; nenhuma dessas vendas ocorre no caso principal de manutenção.

| Carteira | Saída líquida R$ | IR incremental da saída R$ | TIR saída % a.a. | Ranking saída |
|---|---:|---:|---:|---:|
'''
    for r in sorted(ordered,key=lambda r:int(r['liquidation_rank'])):
        text+=f"| {r['portfolio']} | {fmt(r['liquidation_wealth'])} | {fmt(r['liquidation_tax'])} | {fmt(r['liquidation_xirr_pct'],4)} | {r['liquidation_rank']} |\n"
    coverage=[];controls=[]
    for mode in MODES:
        grouped=defaultdict(lambda:dict(events=0,source_amount=0.,additional_withholding=0.))
        envelope=defaultdict(float);divs=defaultdict(float)
        for r in read(OUT/mode/'income.csv'):
            k=r['portfolio'],r['distribution_type'],r['amount_basis'],r['rate_status']
            grouped[k]['events']+=1;grouped[k]['source_amount']+=float(r['source_amount'])
            grouped[k]['additional_withholding']+=float(r['withheld_additional'])
            d=r['source_payment_dates'].split(';')[0] or r['date']
            if d.startswith('2026'):
                k=r['portfolio'],r['issuer'],d[:7];envelope[k]+=float(r['source_amount'])
                if r['distribution_type']=='DIVIDEND':divs[k]+=float(r['source_amount'])
        for (p,t,b,s),v in sorted(grouped.items()):coverage.append(dict(mode=mode,portfolio=p,distribution_type=t,amount_basis=b,rate_status=s,**v))
        for (p,c,m),value in sorted(envelope.items()):controls.append(dict(mode=mode,portfolio=p,issuer=c,month=m,
            known_dividends=divs[p,c,m],all_distributions_cash_envelope=value,threshold=50000,
            threshold_crossed=divs[p,c,m]>50000,envelope_crossed=value>50000,
            date_basis='Known payment date, otherwise ex-date proxy; multiple tranches grouped at first listed payment'))
    write(OUT/'income_coverage.csv',coverage);write(OUT/'dividend_monthly_issuer_2026.csv',controls)
    assert not any(r['envelope_crossed'] for r in controls)
    text+='''
## Limites da camada fiscal e proventos

Custo médio por título, isenção mensal de ações atéR$20mil por CPF alternativo, perdas prospectivas, IRRF como crédito, reserva antes de reinvestir e pagamento posterior de DARF reutilizam o código fiscal anterior. Não há capital externo para pagar imposto. Caixa disponível/restrito/obrigação, operações, pagamentos e imposto anual estão discriminados. Sem obrigação pendente no fim do caso principal.

JCP adicional incide somente sobre valores sustentados como brutos, nas alíquotas já congeladas (15% até2025;17,5% na regra de2026). Valores já líquidos não sofrem segunda retenção. Bruto/líquido ou tipo desconhecidos e tributação integral do BDR continuam ND. Nenhum envelope mensal por pagadora em2026 ultrapassouR$50mil; data de pagamento conhecida é usada, data-ex fica como proxy explícita quando ausente. Não certifica imposto mínimo de altas rendas sem as demais rendas do CPF. Não foram adicionadas novas variantes de JCP.

| Carteira | JCP bruto/líquido desconhecido R$ | Proventos de tipo desconhecido R$ | Distribuições BDR R$ | Maior envelope mensal2026 R$ |
|---|---:|---:|---:|---:|
'''
    for r in ordered:
        p=r['portfolio'];own=[x for x in coverage if x['mode']==MODES[-1] and x['portfolio']==p]
        values=[sum(x['source_amount'] for x in own if x['distribution_type']==t and (t!='JCP' or x['amount_basis']=='UNKNOWN')) for t in ['JCP','UNKNOWN','FOREIGN_BDR_DISTRIBUTION']]
        maximum=max((x['all_distributions_cash_envelope'] for x in controls if x['portfolio']==p and x['mode']==MODES[-1]),default=0.)
        text+=f"| {p} | "+' | '.join(fmt(v) for v in values+[maximum])+' |\n'
    text+='''
Resultados exploratórios condicionados às bases fiscais societárias herdadas: bônus sem custo declarado usa incremento zero; rateio XP por valor relativo; resgates/caixa de conversões conforme enquadramento anterior. `FULL_HISTORICAL_CERTIFIED` permanece ND. Calendário B3 é proxy bancária. Mantidos NET/TIMP3 condicional em BESST-10 BH, pendência BBDC4/2014, datas sem cotação/TWR ND, frações e ausência de custos. Não se inventou provento CPFE/2015 nem dados de pagamento. IBOV é referência bruta, não ETF isento.

## Reprodução e arquivos

```bash
python scripts/monthly_maintenance_reaudit.py
python scripts/run_monthly_reaudited.py --mode GROSS
python scripts/run_monthly_reaudited.py --mode CG_ONLY
python scripts/run_monthly_reaudited.py --mode CG_PLUS_JCP_CERTIFIED_PARTIAL
python scripts/monthly_reaudit_report.py
python -m pytest -q tests/test_monthly_reaudit.py tests/test_monthly_maintenance_fail_audit.py tests/test_monthly_policy_corrected.py tests/test_monthly_tax.py
```

`research/monthly_reaudited_2014_2026/` contém os15 casos e os três modos de trajetória, patrimônio, posições/custos, caixa, aportes, fluxos, operações, revisões, eventos, apuração mensal, imposto anual, pagamentos e liquidação. `maintenance_reviews.csv` e `maintenance_pit_facts.csv` dão a autorização substantiva, não apenas um rótulo FAIL herdado. `gross_sales_substantive_evidence.csv` discrimina as10 saídas reais. Os consolidados comparam cada modo ao checkpoint anterior e ao PR5 original. A planilha exporta os mesmos livros, sem números reconstruídos de logs. Manifestos registram hashes e verificam a preservação dos resultados anteriores. O teste e o replay devem passar antes de encerrar este checkpoint.
'''
    (ROOT/'docs/checkpoint_reauditoria_aportes_tributos_2014_2026.md').write_text(text)
    (OUT/'checkpoint_tax_comment.md').write_text(text)
    workbook=xlsxwriter.Workbook(OUT/'aportes_reauditados_2014_2026.xlsx',{'constant_memory':True,'strings_to_urls':False})
    workbook.set_properties({'title':'Aportes após reauditoria de permanência','author':'Estudo Barsi × Graham','created':datetime(2026,10,9)})
    h=workbook.add_format({'bold':True,'bg_color':'#17365D','font_color':'white'})
    tabs=[('Consolidado',allrows),('Provas permanência',read(OUT/'maintenance_reviews.csv')),
        ('Fatos PIT',read(OUT/'maintenance_pit_facts.csv')),('Saídas brutas',read(OUT/'gross_sales_substantive_evidence.csv')),
        ('Cobertura',coverage),('Dividendos2026',controls)]
    for title,stem in [('Trajetórias','wealth'),('Imposto anual','annual_tax'),('Apuração mensal','monthly_tax'),
        ('Pagamentos','payments'),('Custo operações','tax_trades'),('Proventos','income'),('Posições finais','final_positions'),
        ('Revisões junho','junes'),('Operações','trades'),('Aportes','contributions'),('Liquidação','liquidation_monthly_tax')]:
        tabs.append((title,[dict(mode=m,**r) for m in MODES for r in read(OUT/m/(stem+'.csv'))]))
    for title,data in tabs:
        sheet=workbook.add_worksheet(title);keys=list(dict.fromkeys(k for r in data for k in r))
        sheet.freeze_panes(1,0);sheet.set_column(0,max(0,len(keys)-1),22)
        for j,k in enumerate(keys):sheet.write(0,j,k,h)
        for i,row in enumerate(data,1):
            for j,k in enumerate(keys):
                value=row.get(k,'')
                if value is None or value=='':continue
                try:
                    if k in ['issuer','issuer_cnpj','lineage','ticker','account','document_id','revenue_code','event_id'] or k.endswith('date'):raise ValueError()
                    sheet.write_number(i,j,float(value))
                except (ValueError,TypeError):sheet.write(i,j,str(value))
        if keys:sheet.autofilter(0,0,len(data),len(keys)-1)
    workbook.close()
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='delivery_manifest.json' and p.suffix not in ['.xml','.log']]
    files += [ROOT/'scripts'/f for f in ['monthly_maintenance_reaudit.py','monthly_reaudit_simulate.py','run_monthly_reaudited.py','monthly_reaudit_report.py']]
    files += [ROOT/'tests/test_monthly_reaudit.py',ROOT/'docs/checkpoint_reauditoria_aportes_tributos_2014_2026.md',ROOT/'docs/checkpoint_reauditoria_aportes_bruto_2014_2026.md']
    prices=sorted((ROOT/'research/monthly_contributions_2014_2026/inputs').glob('quotes_*.json.gz'))
    # STUDY is deliberately imported rather than assuming a directory name.
    import monthly_contributions as economic
    prices=sorted((economic.STUDY/'inputs').glob('quotes_*.json.gz'))
    files+=prices
    manifest=dict(scope='15 monthly replayed trajectories; final liquidation independent',
        prior_files_verified=guard_prior(),legacy_files_verified=guard_legacy(),
        prior_head='369be10b98c04147ed10107fbb9bd8a131a87d83',
        files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))})
    (OUT/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--gross-only',action='store_true');args=parser.parse_args()
    guard_prior();guard_legacy();gross=gross_checkpoint()
    if not args.gross_only:full_checkpoint(gross)
    guard_prior();guard_legacy();print('Reaudited numerical checkpoint generated; prior data unchanged',flush=True)


if __name__=='__main__':main()
