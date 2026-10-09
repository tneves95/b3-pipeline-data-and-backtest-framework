"""Portuguese checkpoint/workbook from calculated CSVs; no manual returns."""
from collections import defaultdict
from datetime import datetime
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import xlsxwriter

from monthly_tax_freeze import TAX, POLICY
from monthly_contributions import ROOT


def read(path):
    with path.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))


def fmt(value,precision=2):
    return f'{float(value):,.{precision}f}'.replace(',','X').replace('.',',').replace('X','.')


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def workbook():
    path=TAX/'tributacao_aportes_mensais_cinco_carteiras.xlsx'
    book=xlsxwriter.Workbook(path,{'constant_memory':True,'strings_to_urls':False})
    book.set_properties({'title':'Tributação e aportes mensais — cinco carteiras',
        'author':'Estudo Barsi × Graham','created':datetime(2026,10,9)})
    header=book.add_format({'bold':True,'bg_color':'#17365D','font_color':'white','text_wrap':True})
    numeric=book.add_format({'num_format':'#,##0.00'})
    sheet=book.add_worksheet('Leia primeiro');sheet.set_column(0,0,125)
    notes=[
        'R$100 mil iniciais +144 aportes de R$2.500 =R$460 mil. Cada carteira é um CPF alternativo.',
        'CG_ONLY: IR sobre vendas. CG_PLUS_JCP_CERTIFIED_PARTIAL: retenção adicional somente no JCP de bruto/alíquota sustentados.',
        'Todos os cenários são condicionais em bases societárias. FULL_HISTORICAL_CERTIFIED permanece ND.',
        'O bruto PR5 já contém alguns proventos líquidos. Não foram brutos recompostos nem aplicada dupla retenção.',
        'IRRF dos proventos usa a convenção econômica de reinvestimento na data-ex: não é certificado de pagamento fiscal na data.',
        'Sensibilidades UNKNOWN_GROSS comparam hipóteses explícitas dos JCP restantes e de datas; não são certificação nem intervalos matemáticos.',
        'Patrimônio mantendo: desconta obrigações já realizadas; não desconta IR de valorização não realizada.',
        'Liquidação: vende a carteira tributada em30/06/2026, apura imposto no mês, desconta obrigação de julho.',
        'Caixa restrito integra caixa total; patrimônio econômico deduz a obrigação. IRRF de bolsa é crédito do DARF.',
        'BESST-10 BH mantém TIM no lugar da alternativa NET não certificada; sem nova investigação.',
        'V0/VVAL preservam TWR ND nas datas sem cotação ABCB2/ENBR3; patrimônio e TIR continuam calculáveis.',
        'IBOV é referência bruta não negociável. Nenhuma série BOVA11 com144 aportes foi validada/importada.',
        'Capital próprio de outros rendimentos e tributação mínima de altas rendas não foram inventados.']
    for i,n in enumerate(notes):sheet.write(i,0,n)
    tabs=[('consolidated_tax','Consolidado'),('annual_tax_summary','Imposto anual'),
        ('monthly_taxed_wealth','Patrimônio mensal'),('sensitivities_tax','Sensibilidades'),
        ('monthly_tax_ledger','Apuração mensal'),('tax_payments','Pagamentos DARF'),
        ('tax_trades_basis','Operações e custo'),('cash_dividends_jcp_tax','Dividendos e JCP'),
        ('income_coverage','Cobertura proventos'),('dividend_monthly_issuer_2026','Limiar dividendos 2026'),
        ('tax_events_classification','Eventos e evidências'),('final_liquidation_trades','Liquidação operações'),
        ('final_liquidation_monthly_tax','Liquidação apuração'),('contributions_ledger','Aportes'),
        ('june_tax_reviews','Renovações junho'),('taxed_positions','Posições')]
    for stem,title in tabs:
        p=TAX/(stem+'.csv')
        with p.open(encoding='utf-8-sig') as f:
            reader=csv.DictReader(f);columns=reader.fieldnames;sh=book.add_worksheet(title)
            sh.freeze_panes(1,0);sh.set_row(0,40);sh.set_column(0,len(columns)-1,20)
            for j,key in enumerate(columns):sh.write(0,j,key,header)
            n=0
            for n,row in enumerate(reader,1):
                for j,k in enumerate(columns):
                    value=row[k]
                    if value=='':continue
                    try:
                        if k in ['issuer','lineage','ticker','revenue_code','event_id'] or k.endswith('date'):raise ValueError()
                        sh.write_number(n,j,float(value),numeric)
                    except ValueError:sh.write(n,j,value)
            sh.autofilter(0,0,n,len(columns)-1)
    book.close()


def main():
    rows=read(TAX/'consolidated_tax.csv');sens=read(TAX/'sensitivities_tax.csv')
    cg=sorted([r for r in rows if r['mode']=='CG_ONLY'],key=lambda r:int(r['net_rank']))
    partial={r['portfolio']:r for r in rows if r['mode']=='CG_PLUS_JCP_CERTIFIED_PARTIAL'}
    full={r['portfolio']:r for r in sens if r['sensitivity']=='JCP_UNKNOWN_GROSS_EX_DATE'}
    controls=read(TAX/'dividend_monthly_issuer_2026.csv');coverage=read(TAX/'income_coverage.csv')
    xml=TAX/'tests.xml';test_result={}
    if xml.exists():
        root=ET.parse(xml).getroot();suites=root.findall('testsuite') if root.tag=='testsuites' else [root]
        test_result={k:sum(int(x.get(k,'0')) for x in suites) for k in ['tests','failures','errors','skipped']}
        test_result['passed']=test_result['tests']-test_result['failures']-test_result['errors']-test_result['skipped']
        test_result['status']='PASS' if not test_result['failures'] and not test_result['errors'] else 'FAIL'
        (TAX/'test_results.json').write_text(json.dumps(test_result,indent=2)+'\n')
    # Every tracked PR5 path is protected. The only pre-existing changed path is
    # the coordinator's protocol, already part of PR6 before our execution.
    diff=subprocess.check_output(['git','diff','--name-status',POLICY['baseline_commit']],cwd=ROOT,text=True)
    bad=[line for line in diff.splitlines() if not line.startswith('A\t')
         and line!='M\tdocs/protocolo_tributacao_aportes_mensais_2014_2026.md']
    if bad:raise ValueError(('PROTECTED_BASELINE_CHANGED',bad))
    protected=int(subprocess.check_output(['git','ls-tree','-r','--name-only',POLICY['baseline_commit']],cwd=ROOT,text=True).count('\n'))
    text='''# Tributação dos aportes mensais — checkpoint 2 calculado

Execução no PR #6, branch `scenario/monthly-contributions-tax-2014-2026`, sem merge. Base PR #5 `e3b7c597c83454da34f6461ab68aeb206b0135be` preservada. R$100.000 em30/06/2014 +144 aportes de R$2.500 = **R$460.000 por carteira**, em CPFs alternativos. Não houve nova investigação da NET: BESST-10 BH mantém a composição com TIM e a ressalva `CONDITIONAL_NET_ON`.

**Conclusão econômica:** as trajetórias foram recalculadas, com imposto diminuindo compras posteriores. O ranking continua VVAL, BESST-10 BH, V10, V0 e BH padrão nos casos centrais e nas sensibilidades de JCP calculadas. A incidência sobre ganhos não realizados só entra na liquidação separada.

**Qualificação indispensável:** `CG_ONLY` é numérico e condicional a algumas bases societárias. `CG_PLUS_JCP_CERTIFIED_PARTIAL` significa retenção adicional nos JCP com bruto e alíquota sustentados; não certifica a tributação inteira nem a data real de crédito. `FULL_HISTORICAL_CERTIFIED` permanece **ND** por convenção bruto/líquido, datas, bases societárias e dividendos de BDR ainda não integralmente documentados. O bruto herdado do PR5 já inclui alguns valores líquidos, especialmente JCP mensal do Itaú; não houve recomposição artificial nem dupla retenção.

## Ganhos realizados: primeiro lote e atualização de evidências

O [checkpoint1 foi publicado imediatamente](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/6#issuecomment-6085830523), commit `d34b6da`, após52 testes. No lote2 foram reaproveitados os custos declarados de ITSA/PSSA do PR2 e identificadas restituições de capital de VIVT no livro herdado. Isso atualizou CG_ONLY de V0/V10; não alterou preços, seleções ou o baseline. A política fiscal foi congelada antes dos resultados, e não foi ajustada para obter outro ranking.

|Carteira|Bruto PR5 R$|Líquido CG_ONLY R$|TIR bruta %|TIR líquida %|IR pago R$|Redução patrimonial R$|
|---|---:|---:|---:|---:|---:|---:|
'''
    for r in cg:
        text+='|'+r['portfolio']+'|'+'|'.join(fmt(r[k],4 if 'xirr' in k else 2) for k in ['gross_wealth','final_wealth','gross_xirr_pct','xirr_pct','tax_paid','wealth_reduction'])+'|\n'
    text+='''
IR pago inclui DARFs e IRRF ordinário, com o IRRF creditado uma única vez. A diferença de patrimônio inclui o efeito composto do dinheiro que deixou de ser reinvestido e, portanto, não equivale ao imposto pago. Obrigações finais de manutenção são zero, salvo resíduos numéricos inferiores a um centavo.

## JCP e dividendos: parcela sustentada e hipótese dos valores desconhecidos

|Carteira|Líquido com JCP sustentado R$|TIR %|IR vendas pago R$|JCP adicional modelado R$|Líquido se demais JCP forem brutos R$|TIR nessa hipótese %|
|---|---:|---:|---:|---:|---:|---:|
'''
    for c in cg:
        p=c['portfolio'];r=partial[p];s=full[p]
        text+=f"|{p}|{fmt(r['final_wealth'])}|{fmt(r['xirr_pct'],4)}|{fmt(r['tax_paid'])}|{fmt(r['income_withheld'])}|{fmt(s['final_wealth'])}|{fmt(s['xirr_pct'],4)}|\n"
    text+='''
Os valores de JCP já líquidos são preservados em todos os cenários. JCP comprovadamente bruto usa15% até2025 e17,5% na regra de2026. Quando pagamento e possível crédito atravessam2025/2026 sem prova da data do crédito, o caso parcial fica sem retenção adicional e os cenários de data-ex/data de pagamento medem a diferença. As retenções de proventos são reconhecidas na data-ex econômica, preservando o reinvestimento do PR5: o total é **retenção modelada**, não certificado de recolhimento naquela data. O cenário de valores desconhecidos brutos não é intervalo matemático nem certeza documental.

Dividendos brasileiros de2014–2025 permanecem isentos. O controle de2026 agrega por emissor/CPF/mês, usa pagamento conhecido ou data-ex expressamente marcada como proxy e mostra também um envelope com todos os proventos. Nenhum grupo calculado alcançou R$50 mil; não houve imposto adicional de dividendos pela regra mensal. Maiores envelopes nominais de2026 por carteira no caso parcial:

'''
    for c in cg:
        values=[float(r['all_distributions_cash_envelope']) for r in controls if r['portfolio']==c['portfolio'] and r['mode']=='CG_PLUS_JCP_CERTIFIED_PARTIAL']
        text+=f"- {c['portfolio']}: R$ {fmt(max(values,default=0))}.\n"
    text+='\nMontantes acumulados dos proventos ainda com convenção não certificada (valores de origem, não perda de patrimônio):\n\n|Carteira|JCP bruto/líquido desconhecido R$|Provento sem tipo R$|Distribuição bruta de BDR R$|\n|---|---:|---:|---:|\n'
    for c in cg:
        own=[r for r in coverage if r['portfolio']==c['portfolio'] and r['mode']=='CG_PLUS_JCP_CERTIFIED_PARTIAL']
        values=[sum(float(r['source_amount']) for r in own if r['distribution_type']==typ and (typ!='JCP' or r['amount_basis']=='UNKNOWN')) for typ in ['JCP','UNKNOWN','FOREIGN_BDR_DISTRIBUTION']]
        text+='|'+c['portfolio']+'|'+'|'.join(fmt(v) for v in values)+'|\n'
    text+='''
Esses valores não transformam datas desconhecidas em pagamentos certificados. Dividendos do BDR XPBR31 foram separados de dividendos domésticos: o legado usa valores brutos convertidos por PTAX; eventual imposto/tributo estrangeiro ou crédito fiscal permanece ND, com montantes expostos em `income_coverage.csv`. Tributação mínima de altas rendas não foi inventada sem as demais rendas do CPF.

## Liquidação integral hipotética em30/06/2026

Parte das quantidades e custos realmente remanescentes no cenário com ganhos/JCP sustentados. Deduz a obrigação da venda final, ainda que o DARF vença em julho. Não mistura essa venda com a manutenção.

|Carteira|Mantendo R$|Imposto adicional da liquidação R$|Saída líquida R$|TIR de saída %|Maior emissor %|HHI de emissores|
|---|---:|---:|---:|---:|---:|---:|
'''
    for c in cg:
        r=partial[c['portfolio']]
        text+=f"|{r['portfolio']}|{fmt(r['final_wealth'])}|{fmt(r['liquidation_tax'])}|{fmt(r['liquidation_wealth'])}|{fmt(r['liquidation_xirr_pct'],4)}|{fmt(float(r['maximum_issuer_weight'])*100)}|{fmt(r['issuer_hhi'],6)}|\n"
    text+='''
XPBR31 conta como emissor próprio na concentração, mantendo a linhagem herdada para as decisões. O CSV consolidado inclui concentrações brutas, tributadas, HHI setorial e rankings de manutenção/liquidação. Os dois BH mantêm zero vendas voluntárias. IBOV segue referência bruta de índice, com R$1.051.091,04 e TIR10,7592%; não foi tratado como ETF isento. Não há BOVA11 adicional porque não foi validada neste pacote a cobertura de todos os144 aportes.

## Limitações medidas, sem reabrir a seleção

- Custos declarados de bonificação do Bradesco nos FREs locais e de ITSA/PSSA nos documentos preservados do PR2 são incorporados. Bonificações sem custo fiscal comprovado ficam `UNRESOLVED`: custo incremental zero central e preço ex como sensibilidade explícita. Não se afirma que o custo legal seja zero.
- Cisão XP: alocação proporcional ao valor observado, comparada com custo zero para o filho; resgates ENBR/NEOE: GCAP15% sobre ganho positivo separado, comparado com hipótese de isenção35mil. São enquadramentos condicionais, sem usar a isenção20mil da bolsa indiscriminadamente. Conversões com dinheiro: custo proporcional ao caixa, com sensibilidade de custo zero no caixa.
- Restituições de capital identificadas reduzem o custo herdado; eventual excedente é ganho separado. Reinvestimento recompõe o custo pelo dinheiro efetivamente aplicado. Os eventos não foram removidos nem reescritos.
- VVAL com BBDC4/2014 `NOT_ADMITTED` está calculada separadamente. BESST permanece com TIM. Custos transacionais não foram adicionados: inexistem parâmetros certificados de corretagem/emolumentos no contrato do PR5.
- A reserva mensal inclui eventual imposto caso vendas posteriores façam perder a isenção. O excedente é liberado no fechamento, sem antecipar operações futuras. DARF mínimoR$10 por código, vencimento na última sessão B3 do mês seguinte, proxy do calendário bancário. IRRF excedente ao fim do ano é indicado para DIRPF/restituição pendente, sem criar caixa de restituição não comprovada.
- Reinvestimento na data-ex, financiamento no mesmo fechamento e quantidades fracionadas são convenções herdadas. Datas de crédito/pagamento não documentadas não foram declaradas conhecidas. As faltas de cotação de ABCB2/ENBR3 mantêm TWR ND em V0/VVAL; patrimônio e TIR seguem calculáveis.

`sensitivities_tax.csv` contém todas as hipóteses executadas, com patrimônio, TIR, IR, liquidação e ranking, incluindo as que têm impacto apenas na liquidação. Não há novo seletor de carteira nem otimização fiscal que desloque vendas para outros meses.

## Testes, integridade e reprodução

'''
    text+=f"Replay de imposto zero das cinco carteiras compara o livro inteiro com PR5: patrimônio, calendário, unidades, operações, proventos, posições, aportes, TIR e ausências TWR. Foram protegidos **{protected} arquivos rastreados da base**; a única diferença herdada é o protocolo já editado pelo coordenador no início do PR6. Nenhum PR anterior foi alterado.\n\n"
    if test_result:text+=f"Resultado executado: **{test_result['passed']} testes passaram**, {test_result['failures']} falhas, {test_result['errors']} erros, {test_result['skipped']} ignorados. `test_results.json` vem do XML real do pytest.\n\n"
    text+='''Os testes cobrem custo após3 aportes/venda parcial; agregação19999/20000/20001; perdas comuns/daytrade; IRRF como crédito; DARF futuro/mínimo/insuficiência; direitos; cisão XP; resgate ENBR; bonificação com e sem custo; JCP bruto/líquido15%/17,5%; transição de datas; dividendos49999/50000/50001 e exceção; liquidação independente; e IR de junho reduzindo patrimônio/TWR/compras sem caixa externo.

```bash
python scripts/run_monthly_tax.py --sensitivities
python -m pytest -q tests/test_monthly_tax.py tests/test_monthly_contributions.py tests/test_b00s_*.py tests/test_stage1_*.py tests/test_returns_stage1.py tests/test_graham_maintenance_v11.py tests/test_itsa_rights_v11_2.py tests/test_audit_v12.py tests/test_barsi_v13.py --junitxml=research/monthly_tax_2014_2026/tests.xml
python scripts/monthly_tax_report.py
```

Todas as entradas derivadas, scripts, resultados, planilha e logs de execução estão em diretório persistente dentro de `/workspaces`. Os CSVs são o cálculo, não reconstrução de números de logs. `manifest.json` inclui hashes para conferir integridade. Os caches de eventos/cotações que derivam do SQLite e COTAHIST são os já congelados pelo PR5.

Fontes: [RFB — bolsa](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/bolsa-de-valores), [isenção](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/isencoes), [compensação](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/compensacoes), [IRRF](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/retencoes), [IN1.585](https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=67494), [LC224/2025](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp224.htm), [Lei15.270/2025](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15270.htm), [Itaú — JCP líquido](https://www.itau.com.br/relacoes-com-investidores/informacoes-ao-mercado/dividendos-e-jcp/). Evidências de eventos e suas ressalvas estão nos dois arquivos `inputs/event_tax_evidence*.json` e nas fontes preservadas.
'''
    (ROOT/'docs/estudo_tributacao_aportes_mensais_2014_2026.md').write_text(text)
    comment='''Checkpoint2 **calculado**, na branch solicitada, sem merge. O checkpoint1 (`d34b6da`) foi publicado antes da camada de proventos. Agora há10 trajetórias tributadas centrais,41 sensibilidades, controle IBOV bruto e replay integral das cinco carteiras com imposto zero.

Resultados mantendo as posições em30/06/2026. A coluna com JCP aplica somente os valores brutos/alíquotas sustentados; a data-ex continua sendo a convenção econômica herdada.

|Carteira|CG_ONLY R$|Com JCP sustentado R$|TIR desse caso|IR vendas pago R$|JCP adicional modelado R$|
|---|---:|---:|---:|---:|---:|
'''
    for r in cg:
        p=r['portfolio'];s=partial[p]
        comment+=f"|{p}|{fmt(r['final_wealth'])}|{fmt(s['final_wealth'])}|{fmt(s['xirr_pct'],4)}%|{fmt(s['tax_paid'])}|{fmt(s['income_withheld'])}|\n"
    comment+='\nRanking mantido: **VVAL > BESST-10 BH > V10 > V0 > BH padrão**. Não se tributa a valorização não realizada no caso de manutenção. A liquidação total separada usa as quantidades/custos tributados:\n\n'
    for r in cg:
        s=partial[r['portfolio']];comment+=f"- {r['portfolio']}: saída R$ {fmt(s['liquidation_wealth'])}; IR adicional R$ {fmt(s['liquidation_tax'])}; TIR {fmt(s['liquidation_xirr_pct'],4)}%.\n"
    comment+='\nJCP mensal ITUB de R$0,015 identificado como já líquido: sem dupla retenção. A hipótese dos demais JCP brutos também foi recalculada; preserva o ranking. Nenhum envelope mensal de dividendos/proventos de2026 superou R$50 mil nos agrupamentos calculados. Datas de pagamento desconhecidas continuam marcadas como proxy. Custos de ITSA/PSSA do PR2 foram reutilizados; nada do universo/resultado do PR2 foi importado.\n\n'
    if test_result:comment+=f"**{test_result['passed']} testes passaram**, com {test_result['failures']} falhas e {test_result['errors']} erros; conferência independente do XLSX contra CSV. A CI recalcula tudo. As bases dos PRs anteriores permanecem intactas, incluindo{protected} arquivos rastreados da base.\n\n"
    comment+='''**Limite:** o imposto integral certificado permanece ND. As lacunas de bruto/líquido, crédito, custo de bonificação, XP, resgates/conversões e rendimentos de BDR estão discriminadas e quantificadas. Não se presume aprovação documental nem valores fiscais zero. BESST mantém TIM e sua ressalva; nenhuma nova investigação da NET.

Entregas: `research/monthly_tax_2014_2026/` (CSV, XLSX, política congelada, fontes, manifest e testes) e `docs/estudo_tributacao_aportes_mensais_2014_2026.md`. Os cálculos reduzem o reinvestimento mensal e reservam/pagam DARF; não são dedução retrospectiva do patrimônio final. Tudo permanece em `/workspaces`.
'''
    (TAX/'checkpoint2_comment.md').write_text(comment)
    workbook()
    items=[p for p in TAX.rglob('*') if p.is_file() and p.suffix not in ['.log','.xml'] and p.name!='manifest.json']
    items+=list((ROOT/'scripts').glob('monthly_tax*.py'))+[ROOT/'scripts/run_monthly_tax.py',ROOT/'tests/test_monthly_tax.py',ROOT/'docs/estudo_tributacao_aportes_mensais_2014_2026.md']
    manifest=dict(baseline=POLICY['baseline_commit'],checkpoint=2,protected_baseline_files=protected,
        policy_sha256=digest(TAX/'inputs/tax_policy_freeze.json'),
        files=[dict(path=str(p.relative_to(ROOT)),sha256=digest(p)) for p in sorted(set(items))])
    (TAX/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Report, workbook and manifest produced',test_result,flush=True)


if __name__=='__main__':main()
