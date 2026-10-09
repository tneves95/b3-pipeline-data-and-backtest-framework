"""Report and workbook from corrected calculations; never touch legacy artifacts."""
from collections import defaultdict
from datetime import datetime
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import xlsxwriter
from run_monthly_corrected import ROOT,OUT,write,guard_legacy

MODES=['GROSS','CG_ONLY','CG_PLUS_JCP_CERTIFIED_PARTIAL']

def read(p):
    with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def fmt(v,n=2):return f'{float(v):,.{n}f}'.replace(',','X').replace('.',',').replace('X','.')

def merged(stem):
    return [dict(mode=m,**r) for m in MODES for r in read(OUT/m/(stem+'.csv'))]

def main():
    protected=guard_legacy()
    summaries=[r for name in ['consolidated_policy_corrected','consolidated_tax_corrected','consolidated_income_corrected'] for r in read(OUT/(name+'.csv'))]
    for r in summaries:
        r['total_additional_tax_paid_modeled']=float(r['tax_paid'])+float(r['income_withheld'])
        r['full_historical_certified_wealth']='ND'
    write(OUT/'all_corrected_scenarios.csv',summaries)
    coverage=[];controls=[]
    for m in MODES:
        income=read(OUT/m/'income.csv');kinds=defaultdict(lambda:dict(events=0,source_amount=0.,additional_withholding=0.))
        envelope=defaultdict(float);divs=defaultdict(float)
        for r in income:
            k=(r['portfolio'],r['distribution_type'],r['amount_basis'],r['rate_status'])
            kinds[k]['events']+=1;kinds[k]['source_amount']+=float(r['source_amount'])
            kinds[k]['additional_withholding']+=float(r['withheld_additional'])
            d=r['source_payment_dates'].split(';')[0] or r['date']
            if d.startswith('2026'):
                k=(r['portfolio'],r['issuer'],d[:7]);envelope[k]+=float(r['source_amount'])
                if r['distribution_type']=='DIVIDEND':divs[k]+=float(r['source_amount'])
        for (p,t,b,s),values in sorted(kinds.items()):
            coverage.append(dict(mode=m,portfolio=p,distribution_type=t,amount_basis=b,rate_status=s,**values))
        for (p,c,month),value in sorted(envelope.items()):
            known=divs[p,c,month]
            controls.append(dict(mode=m,portfolio=p,issuer=c,month=month,known_dividends=known,
                all_distributions_cash_envelope=value,threshold=50000,threshold_crossed=known>50000,
                envelope_crossed=value>50000,within_horizon=month<='2026-06',
                date_basis='Known payment date, otherwise ex-date proxy; multiple tranches grouped at first listed payment'))
    write(OUT/'income_coverage_corrected.csv',coverage);write(OUT/'dividend_monthly_issuer_2026_corrected.csv',controls)
    gross={r['portfolio']:r for r in summaries if r['mode']=='GROSS'}
    cg={r['portfolio']:r for r in summaries if r['mode']=='CG_ONLY'}
    partial=sorted([r for r in summaries if r['mode']==MODES[-1]],key=lambda r:int(r['rank']))
    text='''# Checkpoint tributário da política corrigida — 2014–2026

PR #6 draft, sem merge. Foram calculadas cinco trajetórias brutas, cinco CG_ONLY e cinco com retenção adicional de JCP sustentado. R$100 mil iniciais +144 aportes de R$2.500 = R$460 mil por carteira. Cada carteira representa um CPF alternativo.

[Checkpoint bruto publicado](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/6#issuecomment-6086398679) e [checkpoint CG_ONLY publicado](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/6#issuecomment-6086435184). O baseline bruto foi validado antes da camada de proventos. A regra vigente é a [retificação do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/6#issuecomment-6086144108).

## Patrimônios mantendo os ativos em 30/06/2026

| Carteira | Bruto corrigido R$ | CG_ONLY R$ | Com JCP sustentado R$ | TIR desse caso % a.a. | IR de realizações pago R$ | JCP adicional modelado R$ |
|---|---:|---:|---:|---:|---:|---:|
'''
    for r in partial:
        p=r['portfolio']
        text+=f"| {p} | {fmt(gross[p]['final_wealth'])} | {fmt(cg[p]['final_wealth'])} | {fmt(r['final_wealth'])} | {fmt(r['xirr_pct'],4)} | {fmt(r['tax_paid'])} | {fmt(r['income_withheld'])} |\n"
    text+='''
O ranking nos três cenários corrigidos é **VVAL > BESST-10 BH > V0 > V10 > BH padrão**. A inversão V0/V10 veio da correção econômica, não do imposto. Os impostos reduzem os reinvestimentos ao longo da trajetória. A diferença entre patrimônios inclui esse efeito composto e não corresponde à soma de DARFs.

Não há vendas voluntárias por peso, valorização ou saída da lista de compras. Há18 vendas com prova FAIL: V0=10, V10=2, VVAL=6; BH=0. Novas entradas são financiadas com caixa/saídas FAIL/aportes futuros. A referência2× apenas regula novas compras de vencedoras, com marcador persistente; não dispara venda. Eventos compulsórios continuam discriminados.

## Liquidação integral hipotética — cenário com JCP sustentado

O caso principal mantém os ativos. Aqui a venda final usa as quantidades e custos efetivos do caso tributado e deduz a obrigação de imposto, inclusive se o pagamento vencer depois de junho.

| Carteira | Saída líquida R$ | IR adicional da liquidação R$ | TIR de saída % a.a. | Maior emissor % | HHI emissores |
|---|---:|---:|---:|---:|---:|
'''
    for r in partial:text+=f"| {r['portfolio']} | {fmt(r['liquidation_wealth'])} | {fmt(r['liquidation_tax'])} | {fmt(r['liquidation_xirr_pct'],4)} | {fmt(float(r['maximum_issuer_weight'])*100)} | {fmt(r['issuer_hhi'],6)} |\n"
    text+='''
## Cobertura de JCP/dividendos e limites

A retenção adicional de JCP foi aplicada somente aos valores identificados como brutos e com alíquota sustentada no cache preservado (15% até2025;17,5% na regra de2026). JCP mensal do Itaú já líquido é preservado, sem segunda retenção. Não recompusemos proventos brutos artificialmente. Pagamento/crédito em transição de alíquota sem prova suficiente permanece pendente; o reinvestimento na data-ex continua sendo uma convenção econômica, não comprovação de recolhimento fiscal nessa data.

`CG_PLUS_JCP_CERTIFIED_PARTIAL` descreve **apenas a parcela adicional sustentada**. Não certifica a tributação integral: bruto/líquido desconhecido, data de crédito, valores sem tipo e rendimentos do BDR continuam com cobertura exposta. `FULL_HISTORICAL_CERTIFIED` permanece ND. Montantes abaixo são somas nominais dos proventos de origem do caso parcial, não estimativas de imposto ou perda de patrimônio:

| Carteira | JCP com bruto/líquido desconhecido R$ | Provento sem tipo R$ | Distribuição de BDR R$ | Maior envelope mensal de2026 R$ |
|---|---:|---:|---:|---:|
'''
    for r in partial:
        p=r['portfolio'];own=[x for x in coverage if x['mode']==MODES[-1] and x['portfolio']==p]
        values=[sum(x['source_amount'] for x in own if x['distribution_type']==t and (t!='JCP' or x['amount_basis']=='UNKNOWN')) for t in ['JCP','UNKNOWN','FOREIGN_BDR_DISTRIBUTION']]
        maximum=max((x['all_distributions_cash_envelope'] for x in controls if x['portfolio']==p and x['mode']==MODES[-1]),default=0.)
        text+=f"| {p} | "+' | '.join(fmt(v) for v in values+[maximum])+' |\n'
    assert not any(x['envelope_crossed'] for x in controls)
    text+='''
Nenhum agrupamento calculado de2026 ultrapassou R$50 mil por pagadora/mês, mesmo no envelope de todos os proventos; não houve imposto adicional de dividendos domésticos nessa regra. O controle usa pagamento conhecido ou data-ex como proxy explícita. Não certifica datas desconhecidas nem a tributação mínima de altas rendas sem as demais rendas do CPF. BDR não foi classificado como dividendo doméstico isento; sua tributação integral permanece ND.

CG_ONLY também é condicional às bases fiscais societárias herdadas: bonificação sem custo declarado usa incremento zero, rateio de XP é por valor relativo, resgates e parcelas de caixa usam os enquadramentos preservados. Custos declarados já disponíveis de ITSA/PSSA e Bradesco foram reutilizados. Não houve nova pesquisa documental nem novas variantes. As sensibilidades anteriores permanecem exclusivamente legadas, sem validade numérica presumida para as trajetórias corrigidas.

BESST-10 BH mantém TIMP3 e a ressalva de NET; mantida a pendência BBDC4/2014. V0/VVAL conservam TWR ND nas datas de fluxo sem cotação exata. As TIRs usam todos os fluxos efetivos e a marcação final. Sem custos operacionais; frações teóricas e mesma convenção de eventos. XP conta como emissor próprio na concentração. IBOV permanece referência bruta (R$1.051.091,04; TIR10,7592%), não ETF isento; não foi inventada trajetória BOVA11.

## Arquivos e reprodução

Tudo está em `research/monthly_policy_corrected_2014_2026/`, separado dos legados. `consolidated_policy_corrected.csv`, `consolidated_tax_corrected.csv` e `consolidated_income_corrected.csv` contêm as comparações. `all_corrected_scenarios.csv` reúne os15 casos. Subdiretórios por modo contêm trajetórias, operações, custo médio, posições, impostos mensais/anuais, pagamentos, eventos, caixa, fluxos e liquidação. `income_coverage_corrected.csv` e `dividend_monthly_issuer_2026_corrected.csv` expõem a cobertura. A planilha reúne os mesmos CSVs.

```bash
python scripts/run_monthly_corrected.py --mode GROSS
python scripts/run_monthly_corrected.py --mode CG_ONLY
python scripts/run_monthly_corrected.py --mode CG_PLUS_JCP_CERTIFIED_PARTIAL
python scripts/monthly_corrected_report.py
python -m pytest -q tests/test_monthly_policy_corrected.py tests/test_monthly_tax.py
```

49 testes passaram: política corrigida, cenários fiscais sintéticos, conciliação dos resultados reais, ausência de dupla retenção e leitura independente da planilha comparada aos CSVs.

Os CSVs vêm das execuções, não de reconstrução de logs. O replay bruto e CG_ONLY foi conferido byte a byte antes da publicação dos checkpoints. O conjunto fiscal reutiliza custo médio, isenção mensal20mil, compensação prospectiva de prejuízos, distinção daytrade, crédito IRRF, reserva, DARF mínimo e pagamento em sessão B3 como proxy bancária. Todos os dias de eventos verificam unidades reais versus fiscais e caixa disponível não negativo. A liquidação final usa cópia independente, sem alterar a manutenção.

As versões anteriores e os checkpoints PR5/PR6 foram preservados. `LEGACY_ONLY.json` protege os arquivos legados por hash, e nenhum arquivo da base PR5 foi reescrito para acomodar a correção. O PR #6 continua draft, sem merge.

Referências legais e documentos fiscais já preservados: `docs/protocolo_tributacao_aportes_mensais_2014_2026.md` e `research/monthly_tax_2014_2026/inputs/`. A retificação mais recente prevalece quanto à regra econômica.
'''
    (ROOT/'docs/tributacao_politica_corrigida_2014_2026.md').write_text(text)
    (OUT/'checkpoint_income_pr_comment.md').write_text(text)
    book=xlsxwriter.Workbook(OUT/'aportes_politica_corrigida_2014_2026.xlsx',{'constant_memory':True,'strings_to_urls':False})
    book.set_properties({'title':'Aportes — política corrigida','created':datetime(2026,10,9),'author':'Estudo Barsi × Graham'})
    h=book.add_format({'bold':True,'bg_color':'#17365D','font_color':'white'});num=book.add_format({'num_format':'#,##0.0000'})
    note=book.add_worksheet('Leia primeiro');note.set_column(0,0,120)
    notes=['Somente FAIL comprovado autoriza venda voluntária; 2× é referência de compra, nunca teto.',
           'R$100.000 iniciais +144 aportes de2500 = R$460.000. Cada carteira é um CPF alternativo.',
           'Bruto corrigido, CG_ONLY e JCP sustentado parcial. Tributos reduzem os reinvestimentos.',
           'Imposto integral certificado permanece ND: bruto/líquido, crédito, BDR e bases societárias incompletos.',
           'Liquidação integral é cenário separado. BESST mantém TIM e ressalva NET.',
           'Consulte docs/tributacao_politica_corrigida_2014_2026.md para cobertura e convenções.']
    for i,n in enumerate(notes):note.write(i,0,n)
    tabs=[('Consolidado',summaries),('Cobertura proventos',coverage),('Dividendos 2026',controls)]
    tabs += [(title,merged(stem)) for title,stem in [('Trajetórias','wealth'),('Imposto anual','annual_tax'),
        ('Apuração mensal','monthly_tax'),('Pagamentos','payments'),('Custo operações','tax_trades'),('Proventos','income'),
        ('Posições finais','final_positions'),('Revisões junho','junes'),('Operações','trades'),('Aportes','contributions'),
        ('Eventos fiscais','tax_events'),('Liquidação operações','liquidation_trades'),('Liquidação apuração','liquidation_monthly_tax')]]
    for title,data in tabs:
        sheet=book.add_worksheet(title);keys=list(dict.fromkeys(k for r in data for k in r))
        sheet.freeze_panes(1,0);sheet.set_column(0,max(0,len(keys)-1),22)
        for j,k in enumerate(keys):sheet.write(0,j,k,h)
        for i,row in enumerate(data,1):
            for j,k in enumerate(keys):
                value=row.get(k,'')
                if value is None or value=='':continue
                try:
                    if k in ['issuer','lineage','ticker','revenue_code','event_id'] or k.endswith('date'):raise ValueError()
                    sheet.write_number(i,j,float(value),num)
                except (ValueError,TypeError):sheet.write(i,j,str(value))
        if keys:sheet.autofilter(0,0,len(data),len(keys)-1)
    book.close()
    # Protect every PR5 tracked file; protocol amendment is inherited from PR6.
    base='e3b7c597c83454da34f6461ab68aeb206b0135be'
    diff=subprocess.check_output(['git','diff','--name-status',base],cwd=ROOT,text=True)
    bad=[r for r in diff.splitlines() if not r.startswith('A\t') and r!='M\tdocs/protocolo_tributacao_aportes_mensais_2014_2026.md']
    assert not bad,bad
    assert guard_legacy()==protected
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ['delivery_manifest.json'] and p.suffix not in ['.xml','.log']]
    files+=list((ROOT/'scripts').glob('*corrected*.py'))+[ROOT/'tests/test_monthly_policy_corrected.py',ROOT/'docs/tributacao_politica_corrigida_2014_2026.md']
    manifest=dict(legacy_files_verified=protected,baseline_commit=base,
        files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)})
    (OUT/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print('Corrected report/workbook generated; legacy hashes and PR5 tracked files protected',protected,flush=True)

if __name__=='__main__':main()
