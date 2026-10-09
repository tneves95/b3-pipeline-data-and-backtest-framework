# PR #4 — revisão de junho/2025 e retorno até junho/2026

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `06a0033` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

| carteira | retorno_pct | vs_IBOV_pp | giro_pct | empresas_finais | maior_peso_final_pct | top5_final_pct |
|---|---|---|---|---|---|---|
| V0 | 27.0173 | 3.1294 | 0.6271 | 21 | 20.2791 | 56.9929 |
| V10 | 24.9935 | 1.1056 | 0.0000 | 11 | 23.3148 | 70.7243 |
| VVAL | 26.3199 | 2.4319 | 0.0000 | 11 | 25.4532 | 78.8485 |
| VQ | 11.2327 | -12.6553 | 0.0000 | 7 | 40.1635 | 93.7750 |
| IBOV | 23.8880 | 0.0000 | ND | ND | ND | ND |

Diferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.

Observações acumuladas desde a formação, sem extrapolar anos ainda não revisados:

| carteira | periodos | acumulado_desde_2014_pct | anos_positivos | anos_acima_IBOV |
|---|---|---|---|---|
| V0 | 12 | 402.1320 | 8 | 9 |
| V10 | 12 | 386.7677 | 7 | 8 |
| VVAL | 12 | 436.2185 | 10 | 9 |
| VQ | 12 | 348.7784 | 9 | 7 |
| IBOV | 12 | 223.5469 | 8 | ND |

## Financiamento da renovação

A [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.

Nenhuma nova entrada aprovada neste corte.

VVAL: 11 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Linhagens mantidas com B00S-base indeterminado: XPBR31. A continuidade herdada não equivale a aprovação de nova compra.

VQ: 7 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Linhagens mantidas com B00S-base indeterminado: XPBR31. A continuidade herdada não equivale a aprovação de nova compra.

## Composição e contribuição por ação

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp | descendants |
|---|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBAS3 | 5.1572 | 3.7506 | -8.1328 | -0.4194 | BBAS3 |
| VVAL | HOLDING | BBDC4 | 11.7656 | 10.8859 | 16.8748 | 1.9854 | BBDC4 |
| VVAL | HOLDING | BBSE3 | 9.2878 | 9.1637 | 24.6320 | 2.2878 | BBSE3 |
| VVAL | HOLDING | CPLE6 | 5.8892 | 6.4630 | 38.6274 | 2.2748 | CPLE3 |
| VVAL | HOLDING | CSMG3 | 14.2925 | 25.4532 | 124.9603 | 17.8599 | CSMG3 |
| VVAL | HOLDING | ITUB4 | 5.7160 | 5.8092 | 28.3785 | 1.6221 | ITUB4 |
| VVAL | HOLDING | PSSA3 | 30.9198 | 24.9221 | 1.8169 | 0.5618 | PSSA3 |
| VVAL | HOLDING | SANB4 | 3.2072 | 2.4810 | -2.2835 | -0.0732 | SANB4 |
| VVAL | HOLDING | SAPR4 | 10.6762 | 8.4236 | -0.3321 | -0.0355 | SAPR4 |
| VVAL | HOLDING | TBLE3 | 2.7746 | 2.4530 | 11.6769 | 0.3240 | TBLE3 |
| VVAL | HOLDING | XPBR31 | 0.3138 | 0.1947 | -21.6310 | -0.0679 | XPBR31 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |
| VQ | HOLDING | ABCB4 | 8.1228 | 9.0888 | 24.4601 | 1.9869 | ABCB4 |
| VQ | HOLDING | BBDC4 | 5.5655 | 5.8478 | 16.8748 | 0.9392 | BBDC4 |
| VQ | HOLDING | BBSE3 | 8.5219 | 9.5485 | 24.6320 | 2.0991 | BBSE3 |
| VQ | HOLDING | ITUB4 | 9.7523 | 11.2555 | 28.3785 | 2.7675 | ITUB4 |
| VQ | HOLDING | PSSA3 | 43.8777 | 40.1635 | 1.8169 | 0.7972 | PSSA3 |
| VQ | HOLDING | TBLE3 | 23.6245 | 23.7188 | 11.6769 | 2.7586 | TBLE3 |
| VQ | HOLDING | XPBR31 | 0.5354 | 0.3772 | -21.6310 | -0.1158 | XPBR31 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |

Os pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.

## Concentração

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|
| VVAL | 2025-06-30 | AFTER_REVIEW | 11 | 30.9198 | 76.9419 | 0.1611 | {"Bancos": 25.84608661762371, "Energia": 8.66382631367841, "Outros (cisão)": 0.3138017585208636, "Saneamento": 24.968676396188368, "Seguros": 40.20760891398864} |
| VVAL | 2026-06-30 | PERIOD_END | 11 | 25.4532 | 78.8485 | 0.1644 | {"Bancos": 22.926697610392953, "Energia": 8.91598513737545, "Outros (cisão)": 0.1946828795505754, "Saneamento": 33.87682710982342, "Seguros": 34.085807262857614} |
| VQ | 2025-06-30 | AFTER_REVIEW | 7 | 43.8777 | 93.8992 | 0.2748 | {"Bancos": 23.44055229885881, "Energia": 23.624473017698588, "Outros (cisão)": 0.5353839533260275, "Seguros": 52.399590730116564} |
| VQ | 2026-06-30 | PERIOD_END | 7 | 40.1635 | 93.7750 | 0.2510 | {"Bancos": 26.19203956620113, "Energia": 23.718823917887043, "Outros (cisão)": 0.3772046704515737, "Seguros": 49.71193184546026} |

## Decisões de entrada anteriores aos retornos

| ticker | VVAL | PL | PL_max | VQ | dimensoes_satisfatorias | dimensoes_ND | PL_min |
|---|---|---|---|---|---|---|---|
| ABCB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BBAS3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| BBDC4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BBSE3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BMGB4 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| CMIG4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| CPFE3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| CPLE6 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| CSMG3 | INDETERMINATE | ND | 17.1542 | INDETERMINATE | 4 | 2 | 0 |
| ELET3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| EQTL3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| ITUB4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 | ND |
| NEOE3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| PSSA3 | INDETERMINATE | 16.1144 | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| SANB4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 | ND |
| SAPR4 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| TAEE4 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TBLE3 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 | ND |
| VIVT3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |

Canal até P/L 15: nenhuma nova aprovação comprovada neste corte. Canal de reinvestimento produtivo entre 15 e 25: nenhuma aprovação comprovada neste corte. A classificação do canal de preço não presume que uma empresa deixou de investir.

Um limite inferior de P/L acima de 25 comprova rejeição por preço. Um limite superior até 15 comprova o canal maduro. Pontas desconhecidas continuam ND; o intervalo nunca substitui as exigências cumulativas de reinvestimento.

| ticker | PL | crescimento_real_LPA_pct | payout_medio_pct | retorno_capital_pct | medida | minimo_IPCA_mais_6_pct | decisao |
|---|---|---|---|---|---|---|---|
| EQTL3 | 15.6076 | ND | ND | ND | ROIC_ND | 11.3196 | INDETERMINATE |
| PSSA3 | 16.1144 | ND | ND | 19.7609 | ROE_PARENT_AVERAGE_EQUITY | 11.3196 | INDETERMINATE |
| VIVT3 | 17.6731 | ND | ND | ND | ROIC_ND | 11.3196 | INDETERMINATE |


[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_2025.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.

## Verificação e reprodução

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Testes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.
