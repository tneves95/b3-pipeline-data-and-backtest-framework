# Cinco carteiras com aportes mensais — junho/2014 a junho/2026

As cinco carteiras foram reconstruídas com R$ 100.000 iniciais e 144 aportes de R$ 2.500 no primeiro pregão de cada mês. Cada investidor aplicou R$ 460.000. As seleções PIT e os eventos aceitos dos PRs #3/#4 foram preservados; a ponderação monetária é nova, igual por linhagem. Sem impostos, custos ou ações inteiras; reinvestimento econômico teórico na data ex, sem simular liquidação operacional.

**Resultado qualificado:** patrimônio final e XIRR são calculáveis nas cinco trajetórias. TWR integral V0/VVAL fica ND nas datas sem marcação exata; BESST-10 BH é condicional à pendência de capitalização NET/ON e às limitações documentais do universo. Estes números não certificam dados herdados nem autorizam mudar decisões fundamentalistas.

| Métrica | VVAL | V0 | B00S-10 | BH padrão | BESST-10 BH condicional | IBOV com aportes |
|---|---:|---:|---:|---:|---:|---:|
| Patrimônio final | R$ 1.868.050,85 | R$ 1.645.952,98 | R$ 1.656.388,43 | R$ 1.270.936,41 | R$ 1.767.443,92 | R$ 1.051.091,04 |
| Capital externo | R$ 460.000,00 | R$ 460.000,00 | R$ 460.000,00 | R$ 460.000,00 | R$ 460.000,00 | R$ 460.000,00 |
| Ganho acima dos aportes | R$ 1.408.050,85 | R$ 1.185.952,98 | R$ 1.196.388,43 | R$ 810.936,41 | R$ 1.307.443,92 | R$ 591.091,04 |
| TIR anual | 17,9403% | 16,3675% | 16,4461% | 13,1438% | 17,2527% | 10,7592% |
| TWR acumulado | ND | ND | 427,5029% | 373,6694% | 459,5005% | 223,5469% |
| CAGR do TWR | ND | ND | 14,8644% | 13,8386% | 15,4295% | 10,2795% |
| Diferença patrimonial vs IBOV | R$ 816.959,82 | R$ 594.861,95 | R$ 605.297,40 | R$ 219.845,37 | R$ 716.352,89 | R$ 0,00 |
| Caixa final | R$ 0,00 | R$ 0,00 | R$ 0,00 | R$ 0,00 | R$ 0,00 | R$ 0,00 |

## Composição, pesos e concentração

| Carteira | Linhagens ativas finais | Maior peso final | HHI de linhagens | Giro acumulado de junho | Vendas voluntárias |
|---|---:|---:|---:|---:|---:|
| VVAL | 10 | 19,2891% | 0,112819 | 122,8066% | 45 |
| V0 | 20 | 8,3473% | 0,051881 | 107,6752% | 88 |
| V10 | 10 | 18,4336% | 0,108612 | 59,4742% | 23 |
| BH padrão | 8 | 22,8596% | 0,146260 | 0,0000% | 0 |
| BESST-10 BH | 10 | 22,3390% | 0,119736 | 0,0000% | 0 |
| IBOV | 1 | 100,0000% | 1,000000 | 0,0000% | 0 |

As classes de uma companhia e seus direitos não multiplicam alvos. XP conserva o valor dentro da origem Itaú e não recebe compras mensais; sucessões de ticker/classes recebem as quantidades aceitas. Os CSVs informam quantidade, cotação nominal, peso da classe, peso da linhagem, alvo, limite e origem de cada preço. O peso de referência orienta compras, sem venda BH ou reset de calendário. O giro soma `min(vendas, compras)/NAV` nas revisões; não soma depósitos ou eventos compulsórios.

Atribuição monetária: `lineage_cash_attribution.csv` separa compras, vendas, resgates e valor final por origem. A soma do ganho por linhagem reconcilia o patrimônio menos capital externo e caixa, sem tratar proventos como aportes. Essa contribuição em reais não é uma rentabilidade percentual de uma ação comprada em datas diferentes.

## Sensibilidades e pendências materiais

| Cenário | Carteira | Patrimônio | Diferença vs principal | TIR anual | Status |
|---|---|---:|---:|---:|---|
| BBDC4_2014_NOT_ADMITTED | VVAL | 1.855.145,26 | -12.905,59 | 17,8542 | CALCULATED_WITH_INHERITED_PRICE_GAPS |
| NO_WINNER_PRESERVATION | V0 | 1.665.625,96 | 19.672,98 | 16,5152 | CALCULATED_WITH_INHERITED_PRICE_GAPS |
| NO_WINNER_PRESERVATION | VVAL | 1.868.050,85 | 0,00 | 17,9403 | IDENTICAL_RULE_NOT_ACTIVATED |
| NO_WINNER_PRESERVATION | V10 | 1.656.388,43 | 0,00 | 16,4461 | IDENTICAL_RULE_NOT_ACTIVATED |
| NO_WINNER_PRESERVATION | BH padrão | 1.270.936,41 | 0,00 | 13,1438 | IDENTICAL_RULE_NOT_ACTIVATED |
| NO_WINNER_PRESERVATION | BESST-10 BH | 1.767.443,92 | 0,00 | 17,2527 | IDENTICAL_RULE_NOT_ACTIVATED |
| VVAL_STRICT_MONTHLY_PRICE_GATE | VVAL | ND | ND | ND | ND |
| BESST_NET_REPLACES_TIM | BESST-10 BH | ND | ND | ND | ND |

Bradesco é excluído apenas na formação de 2014 na sensibilidade obrigatória. A decisão congelada `PASS_MATURE` de junho/2015 permite sua admissão naquele corte, com a mesma cronologia posterior. Não se exclui Bradesco para sempre nem se reescreve o parecer HIGH do PR #4. Os livros completos do cenário estão em `sensitivities/BBDC4_2014_NOT_ADMITTED/`.

V0 mantém em caixa os depósitos de 01/07/2014 e 02/01/2015, até o mês seguinte, por não haver preço de ABCB2 no fechamento dessas datas. V0 e VVAL mantêm o depósito de 01/09/2023 até outubro, porque ENBR3 não negocia e o preço final do resgate só foi divulgado em 05/09. Os proventos e o principal compulsório continuam no evento aceito. Nenhum preço foi interpolado, carregado indefinidamente ou antecipado. O principal de R$ 24,23 é usado em 13/09/2023, não em agosto. Patrimônio/XIRR não exigem preços nesses cortes sem operação, mas TWR com o fluxo externo exige NAV completo naquele dia; por isso a lacuna não é ocultada.

TWR anual continua publicado nos períodos com todos os NAV de aporte conhecidos. Volatilidade anualizada usa desvio padrão dos retornos mensais exatamente calculáveis × √12, com contagem explícita. Drawdown usa o índice TWR de fechamento mensal e é ND se sua cadeia tiver lacuna; não confunde perda de mercado com depósitos.

O BESST principal congela Itaú/Bradesco, Tractebel/Cemig, Sabesp/Copasa, BB Seguridade/Porto, Telefônica/TIM. NET não tem cotação ON contemporânea. Paridade ON/PN e último negócio ON deixam NET abaixo da TIM; um cenário ON=2×PN ultrapassa a TIM. Isso é cenário, não prova ou limite matemático. A alternativa NET→TIM depende de comprovar sua saída compulsória/caixa em 2014–2015 e está ND; o relatório não fabrica sucessor. SulAmérica fica abaixo de Porto sob a restrição de preço da unit documentada; dobrar simultaneamente todas as classes violaria o preço observado. Renova/Contax e o unit de dois CNPJs do BTG têm ressalvas de prova no inventário.

As normalizações fundamentalistas congeladas cobrem junho, não todos os 144 meses. O diagnóstico de admissão mensal estrita VVAL é ND; o principal aplica a regra autorizada de manutenção dos incumbentes, sem admitir novos emissores fora de junho. Os dois proventos iniciais BBSE reutilizam a transcrição do cache B3; os demais eventos seguem os valores aceitos. A remuneração BBSE antiga não recebeu nova certificação primária neste estudo.

## Reprodução e checkpoints

```bash
python scripts/monthly_publish.py --complete
python -m pytest -q tests/test_monthly_contributions.py
```

Lote 1 `27392d5`: ranking/calendário/preços, antes dos resultados. Lote 2 `7908141`: motor, 24 contribuições e controles completos. O controle sem aportes reproduz o BH legado nos 13 fechamentos de junho; sua ponderação inicial e ausência de revisão são iguais. Não se exige coincidência entre o novo peso igual e a antiga ponderação setorial B2.

Artefatos principais: `consolidated.csv`, `contributions_ledger.csv` (720 depósitos das cinco carteiras), `benchmark_contributions_ledger.csv` (144 IBOV), `monthly_positions.csv`, `monthly_wealth.csv`, `operations.csv`, `internal_events_ledger.csv`, `june_reviews.csv`, `annual_and_cumulative_returns.csv`, `monthly_returns.csv`, `lineage_cash_attribution.csv`, `sensitivities.csv`, planilha e manifest. CSV é a referência primária. Células vazias documentam ND.

Os 3.567 arquivos do baseline `8671156`, incluindo auditoria e PR #3, são conferidos por SHA-256. A CI do novo estudo é isolada. O PR #5 permanece draft, sem merge.
