# PR #4 — revisão de junho/2023 e retorno até junho/2024

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `c140e72` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

| carteira | retorno_pct | vs_IBOV_pp | giro_pct | empresas_finais | maior_peso_final_pct | top5_final_pct |
|---|---|---|---|---|---|---|
| V0 | 14.7043 | 9.7762 | 0.0000 | 22 | 17.7346 | 52.5072 |
| V10 | 14.5138 | 9.5856 | 0.0000 | 11 | 21.4970 | 64.4812 |
| VVAL | 13.8588 | 8.9306 | 0.0000 | 12 | 20.4677 | 65.5017 |
| VQ | 10.0690 | 5.1408 | 0.0000 | 7 | 32.4847 | 93.9876 |
| IBOV | 4.9282 | 0.0000 | ND | ND | ND | ND |

Diferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.

Observações acumuladas desde a formação, sem extrapolar anos ainda não revisados:

| carteira | periodos | acumulado_desde_2014_pct | anos_positivos | anos_acima_IBOV |
|---|---|---|---|---|
| V0 | 10 | 187.5561 | 6 | 7 |
| V10 | 10 | 166.8961 | 5 | 6 |
| VVAL | 10 | 193.9424 | 8 | 7 |
| VQ | 10 | 185.5706 | 7 | 6 |
| IBOV | 10 | 133.0463 | 6 | ND |

## Financiamento da renovação

A [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.

Nenhuma nova entrada aprovada neste corte.

VVAL: 13 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Linhagens mantidas com B00S-base indeterminado: XPBR31. A continuidade herdada não equivale a aprovação de nova compra.

VQ: 7 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Linhagens mantidas com B00S-base indeterminado: XPBR31. A continuidade herdada não equivale a aprovação de nova compra.

## Composição e contribuição por ação

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp | descendants |
|---|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBAS3 | 6.9173 | 7.1551 | 17.7730 | 1.2294 | BBAS3 |
| VVAL | HOLDING | BBDC4 | 13.4893 | 9.7252 | -17.9128 | -2.4163 | BBDC4 |
| VVAL | HOLDING | BBSE3 | 9.1217 | 9.3809 | 17.0935 | 1.5592 | BBSE3 |
| VVAL | HOLDING | CPLE6 | 4.8746 | 4.9245 | 15.0245 | 0.7324 | CPLE6 |
| VVAL | HOLDING | CSMG3 | 11.6522 | 12.0415 | 17.6633 | 2.0582 | CSMG3 |
| VVAL | HOLDING | ENBR3 | 4.0253 | 4.1824 | 18.3028 | 0.7367 | BBAS3;BBDC4;BBSE3;CPLE6;CSMG3;ITUB4;PSSA3;SANB4;SAPR4;SBSP3;TBLE3;XPBR31 |
| VVAL | HOLDING | ITUB4 | 4.7357 | 5.0974 | 22.5534 | 1.0681 | ITUB4 |
| VVAL | HOLDING | PSSA3 | 19.4540 | 19.6116 | 14.7815 | 2.8756 | PSSA3 |
| VVAL | HOLDING | SANB4 | 4.1431 | 3.4271 | -5.8174 | -0.2410 | SANB4 |
| VVAL | HOLDING | SAPR4 | 7.6056 | 9.0264 | 35.1294 | 2.6718 | SAPR4 |
| VVAL | HOLDING | SBSP3 | 10.1348 | 12.0029 | 34.8455 | 3.5315 | SBSP3 |
| VVAL | HOLDING | TBLE3 | 3.4477 | 3.1021 | 2.4481 | 0.0844 | TBLE3 |
| VVAL | HOLDING | XPBR31 | 0.3987 | 0.3228 | -7.8074 | -0.0311 | XPBR31 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |
| VQ | HOLDING | ABCB4 | 9.1968 | 10.4748 | 25.3642 | 2.3327 | ABCB4 |
| VQ | HOLDING | BBDC4 | 7.2000 | 5.3696 | -17.9128 | -1.2897 | BBDC4 |
| VQ | HOLDING | BBSE3 | 9.4440 | 10.0467 | 17.0935 | 1.6143 | BBSE3 |
| VQ | HOLDING | ITUB4 | 9.1170 | 10.1511 | 22.5534 | 2.0562 | ITUB4 |
| VQ | HOLDING | PSSA3 | 31.1510 | 32.4847 | 14.7815 | 4.6046 | PSSA3 |
| VQ | HOLDING | TBLE3 | 33.1236 | 30.8302 | 2.4481 | 0.8109 | TBLE3 |
| VQ | HOLDING | XPBR31 | 0.7675 | 0.6428 | -7.8074 | -0.0599 | XPBR31 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | 0.0000 | ND |

Os pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.

## Concentração

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|
| VVAL | 2023-06-30 | AFTER_REVIEW | 13 | 19.4540 | 63.8521 | 0.1079 | {"Bancos": 29.28543009370382, "Energia": 12.347621255466597, "Outros (cisão)": 0.3986538699216036, "Saneamento": 29.39258810450133, "Seguros": 28.575706676406654} |
| VVAL | 2024-06-28 | PERIOD_END | 12 | 20.4677 | 65.5017 | 0.1155 | {"Bancos": 26.51368210495874, "Energia": 8.377033806631323, "Outros (cisão)": 0.3368837566115152, "Saneamento": 34.51438741275958, "Seguros": 30.25801291903883} |
| VQ | 2023-06-30 | AFTER_REVIEW | 7 | 33.1236 | 92.0325 | 0.2377 | {"Bancos": 25.513829946707673, "Energia": 33.12364939401225, "Outros (cisão)": 0.7674723575413114, "Seguros": 40.59504830173877} |
| VQ | 2024-06-28 | PERIOD_END | 7 | 32.4847 | 93.9876 | 0.2349 | {"Bancos": 25.995504165095763, "Energia": 30.83023886463972, "Outros (cisão)": 0.6428260518306926, "Seguros": 42.53143091843382} |

## Decisões de entrada anteriores aos retornos

| ticker | VVAL | PL | PL_max | VQ | dimensoes_satisfatorias | dimensoes_ND | PL_min |
|---|---|---|---|---|---|---|---|
| ABCB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BBAS3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| BBDC4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BBSE3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| CMIG4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| CPFE3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| CPLE6 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| CSMG3 | PASS_MATURE | ND | 14.2585 | INDETERMINATE | 3 | 3 | 0 |
| ENBR3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| EQTL3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| ITUB4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 | ND |
| NEOE3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| PSSA3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| SANB4 | PASS_MATURE | ND | 11.2985 | INDETERMINATE | 5 | 1 | 0 |
| SAPR4 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| SBSP3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| TAEE4 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TRPL4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| VIVT3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |

Canal até P/L 15: CSMG3, SANB4. Canal de reinvestimento produtivo entre 15 e 25: nenhuma aprovação comprovada neste corte. A classificação do canal de preço não presume que uma empresa deixou de investir.

Um limite inferior de P/L acima de 25 comprova rejeição por preço. Um limite superior até 15 comprova o canal maduro. Pontas desconhecidas continuam ND; o intervalo nunca substitui as exigências cumulativas de reinvestimento.


[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_2023.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.

## Verificação e reprodução

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Testes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.

### Posição anterior fora do universo de novas compras: TBLE3

| variant | ticker | base_status | before | after |
|---|---|---|---|---|
| VVAL | TBLE3 | PASS | 0.0890 | 0.0890 |
| VQ | TBLE3 | PASS | 0.8594 | 0.8594 |

Qualidade atual: **INDETERMINATE**. Revisão incremental de junho/2023: preserva os dossiês e decisões2022 e investiga mudanças materiais e pontes econômicas pendentes antes de consultar retornos2023–24. TBLEtemstatusbasePASS, mas estáfora do universo original de novascompras desteano; ficha apenas acompanha exposição herdada. A ficha atualiza o acompanhamento da posição; não altera o status B00S-base nem autoriza uma venda extraordinária. A decisão de entrada de anos anteriores permanece congelada.
