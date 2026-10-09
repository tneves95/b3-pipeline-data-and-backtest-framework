# PR #4 — revisão de junho/2018 e retorno até junho/2019

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `63aa3aa` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

| carteira | retorno_pct | vs_IBOV_pp | giro_pct | empresas_finais | maior_peso_final_pct | top5_final_pct |
|---|---|---|---|---|---|---|
| V0 | 51.6276 | 12.8650 | 10.0000 | 18 | 19.4869 | 54.4588 |
| V10 | 51.6632 | 12.9006 | 10.0000 | 10 | 19.5260 | 64.8398 |
| VVAL | 63.3235 | 24.5608 | 10.0000 | 12 | 21.6003 | 69.4334 |
| VQ | 50.7837 | 12.0210 | 10.0000 | 6 | 29.8745 | 91.1304 |
| IBOV | 38.7626 | 0.0000 | ND | ND | ND | ND |

Diferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.

Observações acumuladas desde a formação, sem extrapolar anos ainda não revisados:

| carteira | periodos | acumulado_desde_2014_pct | anos_positivos | anos_acima_IBOV |
|---|---|---|---|---|
| V0 | 5 | 107.0686 | 4 | 3 |
| V10 | 5 | 93.9275 | 3 | 2 |
| VVAL | 5 | 131.8051 | 5 | 4 |
| VQ | 5 | 129.2930 | 4 | 3 |
| IBOV | 5 | 89.9014 | 3 | ND |

## Financiamento da renovação

A [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.

| variant | ticker | reference_weight_pct | executed_weight_pct |
|---|---|---|---|
| VVAL | BBSE3 | 10.0000 | 10.0000 |
| VQ | BBSE3 | 10.0000 | 10.0000 |

VVAL: 11 posições anteriores não reprovadas; fator de capital mantido entre 0.90000000 e 0.90000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

VQ: 5 posições anteriores não reprovadas; fator de capital mantido entre 0.90000000 e 0.90000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

## Composição e contribuição por ação

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp | descendants |
|---|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBAS3 | 5.3496 | 6.4831 | 97.9308 | 5.2389 | BBAS3 |
| VVAL | HOLDING | BBDC4 | 20.2659 | 21.6003 | 74.0771 | 15.0124 | BBDC4 |
| VVAL | HOLDING | BBSE3 | 10.0000 | 8.5136 | 39.0472 | 3.9047 | BBSE3 |
| VVAL | HOLDING | BRSR6 | 13.0198 | 13.6473 | 71.1950 | 9.2694 | BRSR6 |
| VVAL | HOLDING | CPFE3 | 2.5214 | 2.2028 | 42.6880 | 1.0763 | CPFE3 |
| VVAL | HOLDING | CPLE6 | 1.7235 | 2.4440 | 131.6105 | 2.2682 | CPLE6 |
| VVAL | HOLDING | ENBR3 | 3.2477 | 2.8583 | 43.7404 | 1.4206 | ENBR3 |
| VVAL | HOLDING | ITUB4 | 6.5932 | 5.8396 | 44.6566 | 2.9443 | ITUB4 |
| VVAL | HOLDING | PSSA3 | 20.3979 | 16.8399 | 34.8350 | 7.1056 | PSSA3 |
| VVAL | HOLDING | SAPR4 | 7.1501 | 7.7666 | 77.4057 | 5.5346 | SAPR4 |
| VVAL | HOLDING | SBSP3 | 6.9363 | 8.8323 | 107.9676 | 7.4890 | SBSP3 |
| VVAL | HOLDING | TBLE3 | 2.7947 | 2.9722 | 73.6918 | 2.0595 | TBLE3 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |
| VQ | HOLDING | ABCB4 | 9.8103 | 8.8696 | 36.3244 | 3.5635 | ABCB4 |
| VQ | HOLDING | BBDC4 | 10.4479 | 12.0619 | 74.0771 | 7.7395 | BBDC4 |
| VQ | HOLDING | BBSE3 | 10.0000 | 9.2216 | 39.0472 | 3.9047 | BBSE3 |
| VQ | HOLDING | ITUB4 | 12.2597 | 11.7616 | 44.6566 | 5.4748 | ITUB4 |
| VQ | HOLDING | PSSA3 | 31.5477 | 28.2108 | 34.8350 | 10.9896 | PSSA3 |
| VQ | HOLDING | TBLE3 | 25.9344 | 29.8745 | 73.6918 | 19.1115 | TBLE3 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | 0.0000 | ND |

Os pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.

## Concentração

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|
| VVAL | 2018-06-29 | AFTER_REVIEW | 12 | 20.3979 | 70.8337 | 0.1295 | {"Bancos": 45.22848056848721, "Energia": 10.287249900109794, "Saneamento": 14.086394280574567, "Seguros": 30.39787525082844} |
| VVAL | 2019-06-28 | PERIOD_END | 12 | 21.6003 | 69.4334 | 0.1251 | {"Bancos": 47.57031676172146, "Energia": 10.47728294009968, "Saneamento": 16.598918037446193, "Seguros": 25.353482260732672} |
| VQ | 2018-06-29 | AFTER_REVIEW | 6 | 31.5477 | 90.1897 | 0.2124 | {"Bancos": 32.51793415058791, "Energia": 25.934390191127804, "Seguros": 41.54767565828429} |
| VQ | 2019-06-28 | PERIOD_END | 6 | 29.8745 | 91.1304 | 0.2136 | {"Bancos": 32.69302171273427, "Energia": 29.874527694705407, "Seguros": 37.432450592560315} |

## Decisões de entrada anteriores aos retornos

| ticker | VVAL | PL | PL_max | VQ | dimensoes_satisfatorias | dimensoes_ND |
|---|---|---|---|---|---|---|
| ABCB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| BBAS3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| BBDC4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 |
| BBSE3 | PASS_MATURE | ND | 14.9468 | QUALIFIED_SATISFACTORY | 6 | 0 |
| BRSR6 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| CMIG4 | INDETERMINATE | ND | ND | INDETERMINATE | 1 | 5 |
| CPFE3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| CPLE6 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| ENBR3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| EQTL3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| ITUB4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 |
| PSSA3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| SAPR4 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| SBSP3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| TBLE3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 |
| TIMP3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 |
| TRPL4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| VIVT4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |

Canal até P/L 15: BBSE3. Canal de reinvestimento produtivo entre 15 e 25: nenhuma aprovação comprovada neste corte. A classificação do canal de preço não presume que uma empresa deixou de investir.

| ticker | PL | crescimento_real_LPA_pct | payout_medio_pct | retorno_capital_pct | medida | minimo_IPCA_mais_6_pct | decisao |
|---|---|---|---|---|---|---|---|
| CPFE3 | 18.9389 | ND | ND | ND | ROIC_ND | 8.8549 | INDETERMINATE |
| TIMP3 | 16.8160 | ND | ND | ND | ROIC_ND | 8.8549 | INDETERMINATE |
| VIVT4 | 16.1279 | ND | ND | ND | ROIC_ND | 8.8549 | INDETERMINATE |


[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_2018.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.

## Verificação e reprodução

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Testes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.
