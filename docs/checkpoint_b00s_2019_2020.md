# PR #4 — revisão de junho/2019 e retorno até junho/2020

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `b13546c` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

| carteira | retorno_pct | vs_IBOV_pp | giro_pct | empresas_finais | maior_peso_final_pct | top5_final_pct |
|---|---|---|---|---|---|---|
| V0 | -5.5879 | 0.2668 | 6.6667 | 19 | 19.6738 | 58.7870 |
| V10 | -2.9562 | 2.8985 | 0.0000 | 10 | 20.5486 | 65.1858 |
| VVAL | -12.2250 | -6.3702 | 0.0000 | 12 | 19.5932 | 69.2118 |
| VQ | -13.5248 | -7.6700 | 6.6667 | 7 | 32.2582 | 90.0067 |
| IBOV | -5.8548 | 0.0000 | ND | ND | ND | ND |

Diferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.

Observações acumuladas desde a formação, sem extrapolar anos ainda não revisados:

| carteira | periodos | acumulado_desde_2014_pct | anos_positivos | anos_acima_IBOV |
|---|---|---|---|---|
| V0 | 6 | 95.4978 | 4 | 4 |
| V10 | 6 | 88.1946 | 3 | 3 |
| VVAL | 6 | 103.4669 | 5 | 4 |
| VQ | 6 | 98.2816 | 4 | 3 |
| IBOV | 6 | 78.7832 | 3 | ND |

## Financiamento da renovação

A [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.

| variant | ticker | reference_weight_pct | executed_weight_pct |
|---|---|---|---|
| VQ | IRBR3 | 6.6667 | 6.6667 |

VVAL: 12 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

VQ: 6 posições anteriores não reprovadas; fator de capital mantido entre 0.93333333 e 0.93333333. Nenhuma posição não FAIL foi liquidada pelo financiamento.

## Composição e contribuição por ação

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp | descendants |
|---|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBAS3 | 6.4831 | 4.5874 | -37.8911 | -2.4565 | BBAS3 |
| VVAL | HOLDING | BBDC4 | 21.6003 | 15.7780 | -35.8844 | -7.7511 | BBDC4 |
| VVAL | HOLDING | BBSE3 | 8.5136 | 8.6205 | -11.1230 | -0.9470 | BBSE3 |
| VVAL | HOLDING | BRSR6 | 13.6473 | 9.3449 | -39.8968 | -5.4448 | BRSR6 |
| VVAL | HOLDING | CPFE3 | 2.2028 | 2.5286 | 0.7558 | 0.0166 | CPFE3 |
| VVAL | HOLDING | CPLE6 | 2.4440 | 3.6131 | 29.7601 | 0.7273 | CPLE6 |
| VVAL | HOLDING | ENBR3 | 2.8583 | 3.0931 | -5.0135 | -0.1433 | ENBR3 |
| VVAL | HOLDING | ITUB4 | 5.8396 | 4.9580 | -25.4773 | -1.4878 | ITUB4 |
| VVAL | HOLDING | PSSA3 | 16.8399 | 19.5932 | 2.1262 | 0.3581 | PSSA3 |
| VVAL | HOLDING | SAPR4 | 7.7666 | 11.8028 | 33.3910 | 2.5933 | SAPR4 |
| VVAL | HOLDING | SBSP3 | 8.8323 | 12.6929 | 26.1406 | 2.3088 | SBSP3 |
| VVAL | HOLDING | TBLE3 | 2.9722 | 3.3876 | 0.0448 | 0.0013 | TBLE3 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | 0.0000 | ND |
| VQ | HOLDING | ABCB4 | 8.2783 | 7.3955 | -22.7461 | -1.8830 | ABCB4 |
| VQ | HOLDING | BBDC4 | 11.2578 | 8.3469 | -35.8844 | -4.0398 | BBDC4 |
| VQ | HOLDING | BBSE3 | 8.6069 | 8.8459 | -11.1230 | -0.9573 | BBSE3 |
| VQ | HOLDING | IRBR3 | 6.6667 | 2.5978 | -66.3035 | -4.4202 | IRBR3 |
| VQ | HOLDING | ITUB4 | 10.9775 | 9.4602 | -25.4773 | -2.7968 | ITUB4 |
| VQ | HOLDING | PSSA3 | 26.3301 | 31.0955 | 2.1262 | 0.5598 | PSSA3 |
| VQ | HOLDING | TBLE3 | 27.8829 | 32.2582 | 0.0448 | 0.0125 | TBLE3 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |

Os pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.

## Concentração

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|
| VVAL | 2019-06-28 | AFTER_REVIEW | 12 | 21.6003 | 69.4334 | 0.1251 | {"Bancos": 47.57031676172146, "Energia": 10.47728294009968, "Saneamento": 16.598918037446193, "Seguros": 25.353482260732672} |
| VVAL | 2020-06-30 | PERIOD_END | 12 | 19.5932 | 69.2118 | 0.1181 | {"Bancos": 34.668235568970175, "Energia": 12.622402103549856, "Saneamento": 24.49567228786151, "Seguros": 28.21369003961845} |
| VQ | 2019-06-28 | AFTER_REVIEW | 7 | 27.8829 | 85.0551 | 0.1905 | {"Bancos": 30.51348693188532, "Energia": 27.882892515058376, "Seguros": 41.603620553056295} |
| VQ | 2020-06-30 | PERIOD_END | 7 | 32.2582 | 90.0067 | 0.2306 | {"Bancos": 25.20254864939502, "Energia": 32.25823456047121, "Seguros": 42.53921679013378} |

## Decisões de entrada anteriores aos retornos

| ticker | VVAL | PL | PL_max | VQ | dimensoes_satisfatorias | dimensoes_ND | PL_min |
|---|---|---|---|---|---|---|---|
| ABCB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BBAS3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| BBDC4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 | ND |
| BBSE3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BRSR6 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| CMIG4 | INDETERMINATE | ND | ND | INDETERMINATE | 1 | 5 | ND |
| CPFE3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| CPLE6 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| ENBR3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| EQTL3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| IRBR3 | REJECTED_PRICE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | 25.5860 |
| ITUB4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 | ND |
| PSSA3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| SAPR4 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| SBSP3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| TBLE3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TIMP3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TRPL4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| VIVT4 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |

Canal até P/L 15: nenhuma nova aprovação comprovada neste corte. Canal de reinvestimento produtivo entre 15 e 25: nenhuma aprovação comprovada neste corte. A classificação do canal de preço não presume que uma empresa deixou de investir.

Um limite inferior de P/L acima de 25 comprova rejeição por preço. Um limite superior até 15 comprova o canal maduro. Pontas desconhecidas continuam ND; o intervalo nunca substitui as exigências cumulativas de reinvestimento.

| ticker | PL | crescimento_real_LPA_pct | payout_medio_pct | retorno_capital_pct | medida | minimo_IPCA_mais_6_pct | decisao |
|---|---|---|---|---|---|---|---|
| EQTL3 | 19.7416 | ND | ND | ND | ROIC_ND | 10.6584 | INDETERMINATE |
| TBLE3 | 19.9791 | ND | ND | ND | ROIC_ND | 10.6584 | INDETERMINATE |
| VIVT4 | 16.3721 | ND | ND | ND | ROIC_ND | 10.6584 | INDETERMINATE |


[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_2019.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.

## Verificação e reprodução

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Testes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.
