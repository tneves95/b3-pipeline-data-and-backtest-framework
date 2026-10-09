# PR #4 — revisão de junho/2022 e retorno até junho/2023

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `fbb18fa` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

| carteira | retorno_pct | vs_IBOV_pp | giro_pct | empresas_finais | maior_peso_final_pct | top5_final_pct |
|---|---|---|---|---|---|---|
| V0 | 34.8217 | 14.9874 | 0.0000 | 23 | 17.3302 | 48.2608 |
| V10 | 29.9839 | 10.1496 | 0.0000 | 11 | 21.4469 | 62.7773 |
| VVAL | 37.2708 | 17.4366 | 5.0000 | 13 | 19.4540 | 63.8521 |
| VQ | 32.9077 | 13.0735 | 0.0000 | 7 | 33.1236 | 92.0325 |
| IBOV | 19.8342 | 0.0000 | ND | ND | ND | ND |

Diferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.

Observações acumuladas desde a formação, sem extrapolar anos ainda não revisados:

| carteira | periodos | acumulado_desde_2014_pct | anos_positivos | anos_acima_IBOV |
|---|---|---|---|---|
| V0 | 9 | 150.6933 | 5 | 6 |
| V10 | 9 | 133.0689 | 4 | 5 |
| VVAL | 9 | 158.1639 | 7 | 6 |
| VQ | 9 | 159.4468 | 6 | 5 |
| IBOV | 9 | 122.1007 | 5 | ND |

## Financiamento da renovação

A [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.

| variant | ticker | reference_weight_pct | executed_weight_pct |
|---|---|---|---|
| VVAL | SANB4 | 5.0000 | 5.0000 |

VVAL: 12 posições anteriores não reprovadas; fator de capital mantido entre 0.95000000 e 0.95000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Linhagens mantidas com B00S-base indeterminado: XPBR31. A continuidade herdada não equivale a aprovação de nova compra.

VQ: 7 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Linhagens mantidas com B00S-base indeterminado: XPBR31. A continuidade herdada não equivale a aprovação de nova compra.

## Composição e contribuição por ação

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp | descendants |
|---|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBAS3 | 5.7898 | 6.9173 | 64.0032 | 3.7056 | BBAS3 |
| VVAL | HOLDING | BBDC4 | 18.1299 | 13.4893 | 2.1348 | 0.3870 | BBDC4 |
| VVAL | HOLDING | BBSE3 | 9.6856 | 9.1217 | 29.2788 | 2.8358 | BBSE3 |
| VVAL | HOLDING | CPLE6 | 5.4217 | 4.8746 | 23.4203 | 1.2698 | CPLE6 |
| VVAL | HOLDING | CSMG3 | 7.9525 | 11.6522 | 101.1315 | 8.0425 | CSMG3 |
| VVAL | HOLDING | ENBR3 | 4.4712 | 4.0253 | 23.5826 | 1.0544 | ENBR3 |
| VVAL | HOLDING | ITUB4 | 4.8838 | 4.7357 | 33.1090 | 1.6170 | ITUB4 |
| VVAL | HOLDING | PSSA3 | 15.9861 | 19.4540 | 67.0491 | 10.7185 | PSSA3 |
| VVAL | HOLDING | SANB4 | 5.0000 | 4.1431 | 13.7454 | 0.6873 | SANB4 |
| VVAL | HOLDING | SAPR4 | 8.1829 | 7.6056 | 27.5861 | 2.2573 | SAPR4 |
| VVAL | HOLDING | SBSP3 | 10.0816 | 10.1348 | 37.9958 | 3.8306 | SBSP3 |
| VVAL | HOLDING | TBLE3 | 3.9552 | 3.4477 | 19.6556 | 0.7774 | TBLE3 |
| VVAL | HOLDING | XPBR31 | 0.4597 | 0.3987 | 19.0375 | 0.0875 | XPBR31 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |
| VQ | HOLDING | ABCB4 | 9.3848 | 9.1968 | 30.2454 | 2.8385 | ABCB4 |
| VQ | HOLDING | BBDC4 | 9.3694 | 7.2000 | 2.1348 | 0.2000 | BBDC4 |
| VQ | HOLDING | BBSE3 | 9.7091 | 9.4440 | 29.2788 | 2.8427 | BBSE3 |
| VQ | HOLDING | ITUB4 | 9.1033 | 9.1170 | 33.1090 | 3.0140 | ITUB4 |
| VQ | HOLDING | PSSA3 | 24.7844 | 31.1510 | 67.0491 | 16.6177 | PSSA3 |
| VQ | HOLDING | TBLE3 | 36.7922 | 33.1236 | 19.6556 | 7.2317 | TBLE3 |
| VQ | HOLDING | XPBR31 | 0.8569 | 0.7675 | 19.0375 | 0.1631 | XPBR31 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |

Os pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.

## Concentração

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|
| VVAL | 2022-06-30 | AFTER_REVIEW | 13 | 18.1299 | 62.0661 | 0.1058 | {"Bancos": 33.80345242491228, "Energia": 13.84807194981848, "Outros (cisão)": 0.45971692947642995, "Saneamento": 26.21701898071932, "Seguros": 25.671739715073482} |
| VVAL | 2023-06-30 | PERIOD_END | 13 | 19.4540 | 63.8521 | 0.1079 | {"Bancos": 29.28543009370382, "Energia": 12.347621255466597, "Outros (cisão)": 0.3986538699216036, "Saneamento": 29.39258810450133, "Seguros": 28.575706676406654} |
| VQ | 2022-06-30 | AFTER_REVIEW | 7 | 36.7922 | 90.0398 | 0.2322 | {"Bancos": 27.857383906104992, "Energia": 36.79218386669748, "Outros (cisão)": 0.8568981388520134, "Seguros": 34.49353408834553} |
| VQ | 2023-06-30 | PERIOD_END | 7 | 33.1236 | 92.0325 | 0.2377 | {"Bancos": 25.513829946707673, "Energia": 33.12364939401225, "Outros (cisão)": 0.7674723575413114, "Seguros": 40.59504830173877} |

## Decisões de entrada anteriores aos retornos

| ticker | VVAL | PL | PL_max | VQ | dimensoes_satisfatorias | dimensoes_ND | PL_min |
|---|---|---|---|---|---|---|---|
| ABCB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BBAS3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| BBDC4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BBSE3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| CMIG4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| CPFE3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| CPLE6 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| CSMG3 | PASS_MATURE | ND | 9.8128 | INDETERMINATE | 3 | 3 | 0 |
| ENBR3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| EQTL3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| ITUB4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 | ND |
| NEOE3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| PSSA3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| SANB4 | PASS_MATURE | ND | 11.1063 | INDETERMINATE | 5 | 1 | 0 |
| SAPR4 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| SBSP3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| TAEE4 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TBLE3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TRPL4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| VIVT3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |

Canal até P/L 15: CSMG3, SANB4. Canal de reinvestimento produtivo entre 15 e 25: nenhuma aprovação comprovada neste corte. A classificação do canal de preço não presume que uma empresa deixou de investir.

Um limite inferior de P/L acima de 25 comprova rejeição por preço. Um limite superior até 15 comprova o canal maduro. Pontas desconhecidas continuam ND; o intervalo nunca substitui as exigências cumulativas de reinvestimento.


[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_2022.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.

## Verificação e reprodução

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Testes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.
