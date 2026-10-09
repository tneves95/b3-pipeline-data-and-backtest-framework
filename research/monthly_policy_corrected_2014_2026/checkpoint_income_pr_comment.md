# Checkpoint tributário da política corrigida — 2014–2026

PR #6 draft, sem merge. Foram calculadas cinco trajetórias brutas, cinco CG_ONLY e cinco com retenção adicional de JCP sustentado. R$100 mil iniciais +144 aportes de R$2.500 = R$460 mil por carteira. Cada carteira representa um CPF alternativo.

[Checkpoint bruto publicado](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/6#issuecomment-6086398679) e [checkpoint CG_ONLY publicado](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/6#issuecomment-6086435184). O baseline bruto foi validado antes da camada de proventos. A regra vigente é a [retificação do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/6#issuecomment-6086144108).

## Patrimônios mantendo os ativos em 30/06/2026

| Carteira | Bruto corrigido R$ | CG_ONLY R$ | Com JCP sustentado R$ | TIR desse caso % a.a. | IR de realizações pago R$ | JCP adicional modelado R$ |
|---|---:|---:|---:|---:|---:|---:|
| VVAL | 1.865.901,69 | 1.824.568,21 | 1.815.067,32 | 17,5830 | 20.218,02 | 4.648,74 |
| BESST-10 BH | 1.767.443,92 | 1.767.123,19 | 1.755.973,98 | 17,1718 | 81,23 | 5.775,29 |
| V0 | 1.670.906,27 | 1.639.461,93 | 1.629.310,58 | 16,2411 | 17.675,39 | 5.335,26 |
| V10 | 1.619.829,36 | 1.594.196,07 | 1.576.815,21 | 15,8337 | 11.031,01 | 8.944,33 |
| BH padrão | 1.270.936,41 | 1.270.555,51 | 1.270.555,51 | 13,1400 | 116,41 | 0,00 |

O ranking nos três cenários corrigidos é **VVAL > BESST-10 BH > V0 > V10 > BH padrão**. A inversão V0/V10 veio da correção econômica, não do imposto. Os impostos reduzem os reinvestimentos ao longo da trajetória. A diferença entre patrimônios inclui esse efeito composto e não corresponde à soma de DARFs.

Não há vendas voluntárias por peso, valorização ou saída da lista de compras. Há18 vendas com prova FAIL: V0=10, V10=2, VVAL=6; BH=0. Novas entradas são financiadas com caixa/saídas FAIL/aportes futuros. A referência2× apenas regula novas compras de vencedoras, com marcador persistente; não dispara venda. Eventos compulsórios continuam discriminados.

## Liquidação integral hipotética — cenário com JCP sustentado

O caso principal mantém os ativos. Aqui a venda final usa as quantidades e custos efetivos do caso tributado e deduz a obrigação de imposto, inclusive se o pagamento vencer depois de junho.

| Carteira | Saída líquida R$ | IR adicional da liquidação R$ | TIR de saída % a.a. | Maior emissor % | HHI emissores |
|---|---:|---:|---:|---:|---:|
| VVAL | 1.699.107,81 | 115.959,51 | 16,7627 | 18,36 | 0,117062 |
| BESST-10 BH | 1.625.465,97 | 130.508,02 | 16,2117 | 22,47 | 0,119755 |
| V0 | 1.534.797,11 | 94.513,47 | 15,4975 | 12,87 | 0,061719 |
| V10 | 1.480.632,51 | 96.182,70 | 15,0501 | 14,79 | 0,102959 |
| BH padrão | 1.196.955,81 | 73.599,70 | 12,3927 | 22,86 | 0,145004 |

## Cobertura de JCP/dividendos e limites

A retenção adicional de JCP foi aplicada somente aos valores identificados como brutos e com alíquota sustentada no cache preservado (15% até2025;17,5% na regra de2026). JCP mensal do Itaú já líquido é preservado, sem segunda retenção. Não recompusemos proventos brutos artificialmente. Pagamento/crédito em transição de alíquota sem prova suficiente permanece pendente; o reinvestimento na data-ex continua sendo uma convenção econômica, não comprovação de recolhimento fiscal nessa data.

`CG_PLUS_JCP_CERTIFIED_PARTIAL` descreve **apenas a parcela adicional sustentada**. Não certifica a tributação integral: bruto/líquido desconhecido, data de crédito, valores sem tipo e rendimentos do BDR continuam com cobertura exposta. `FULL_HISTORICAL_CERTIFIED` permanece ND. Montantes abaixo são somas nominais dos proventos de origem do caso parcial, não estimativas de imposto ou perda de patrimônio:

| Carteira | JCP com bruto/líquido desconhecido R$ | Provento sem tipo R$ | Distribuição de BDR R$ | Maior envelope mensal de2026 R$ |
|---|---:|---:|---:|---:|
| VVAL | 216.056,45 | 1.650,69 | 539,31 | 9.867,83 |
| BESST-10 BH | 146.213,98 | 40.929,54 | 527,46 | 8.956,92 |
| V0 | 192.949,18 | 27.409,02 | 278,45 | 6.189,10 |
| V10 | 122.335,47 | 34.340,46 | 545,05 | 9.510,86 |
| BH padrão | 140.011,25 | 38.285,68 | 712,91 | 2.880,55 |

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
