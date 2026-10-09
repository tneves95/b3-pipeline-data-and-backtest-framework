# PR #4 — revisão de junho/2024 e retorno até junho/2025

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `c3e9598` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

| carteira | retorno_pct | vs_IBOV_pp | giro_pct | empresas_finais | maior_peso_final_pct | top5_final_pct |
|---|---|---|---|---|---|---|
| V0 | 37.4777 | 25.4137 | 10.8541 | 23 | 24.6173 | 54.0027 |
| V10 | 45.9123 | 33.8483 | 13.1568 | 11 | 28.1149 | 67.1398 |
| VVAL | 44.4135 | 32.3496 | 12.5268 | 11 | 30.9198 | 76.9419 |
| VQ | 41.2818 | 29.2178 | 0.0000 | 7 | 43.8777 | 93.8992 |
| IBOV | 12.0640 | 0.0000 | ND | ND | ND | ND |

Diferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.

Correção documental posterior ao primeiro cálculo: o commit `20bda6f` replica no campo redundante `missing` a pendência da Cemig já expressa na justificativa original. O [registro da correção](reviews/metadata_correction_2024.json) e o [congelamento original](reviews/decision_freeze_2024_original.json) conservam os hashes anteriores. Nenhuma classificação, critério ou resultado numérico mudou.

Observações acumuladas desde a formação, sem extrapolar anos ainda não revisados:

| carteira | periodos | acumulado_desde_2014_pct | anos_positivos | anos_acima_IBOV |
|---|---|---|---|---|
| V0 | 11 | 295.3256 | 7 | 8 |
| V10 | 11 | 289.4343 | 6 | 7 |
| VVAL | 11 | 324.4926 | 9 | 8 |
| VQ | 11 | 303.4592 | 8 | 7 |
| IBOV | 11 | 161.1609 | 7 | ND |

## Financiamento da renovação

A [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.

Nenhuma nova entrada aprovada neste corte.

VVAL: 11 posições anteriores não reprovadas; fator de capital mantido entre 1.14320767 e 1.14320767. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Saídas determinadas exclusivamente pelo B00S-base: SBSP3.

Linhagens mantidas com B00S-base indeterminado: XPBR31. A continuidade herdada não equivale a aprovação de nova compra.

VQ: 7 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Linhagens mantidas com B00S-base indeterminado: XPBR31. A continuidade herdada não equivale a aprovação de nova compra.

## Composição e contribuição por ação

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp | descendants |
|---|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBAS3 | 8.5368 | 5.1572 | -12.7567 | -1.0890 | BBAS3 |
| VVAL | HOLDING | BBDC4 | 11.6032 | 11.7656 | 46.4347 | 5.3879 | BBDC4 |
| VVAL | HOLDING | BBSE3 | 11.1924 | 9.2878 | 19.8387 | 2.2204 | BBSE3 |
| VVAL | HOLDING | CPLE6 | 5.8755 | 5.8892 | 44.7502 | 2.6293 | CPLE6 |
| VVAL | HOLDING | CSMG3 | 14.3668 | 14.2925 | 43.6662 | 6.2735 | CSMG3 |
| VVAL | HOLDING | ITUB4 | 6.0817 | 5.7160 | 35.7305 | 2.1730 | ITUB4 |
| VVAL | HOLDING | PSSA3 | 23.3988 | 30.9198 | 90.8320 | 21.2536 | PSSA3 |
| VVAL | HOLDING | SANB4 | 4.0889 | 3.2072 | 13.2715 | 0.5427 | SANB4 |
| VVAL | HOLDING | SAPR4 | 10.7695 | 10.6762 | 43.1622 | 4.6483 | SAPR4 |
| VVAL | HOLDING | TBLE3 | 3.7012 | 2.7746 | 8.2608 | 0.3057 | TBLE3 |
| VVAL | HOLDING | XPBR31 | 0.3851 | 0.3138 | 17.6679 | 0.0680 | XPBR31 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |
| VQ | HOLDING | ABCB4 | 10.4748 | 8.1228 | 9.5593 | 1.0013 | ABCB4 |
| VQ | HOLDING | BBDC4 | 5.3696 | 5.5655 | 46.4347 | 2.4934 | BBDC4 |
| VQ | HOLDING | BBSE3 | 10.0467 | 8.5219 | 19.8387 | 1.9931 | BBSE3 |
| VQ | HOLDING | ITUB4 | 10.1511 | 9.7523 | 35.7305 | 3.6270 | ITUB4 |
| VQ | HOLDING | PSSA3 | 32.4847 | 43.8777 | 90.8320 | 29.5065 | PSSA3 |
| VQ | HOLDING | TBLE3 | 30.8302 | 23.6245 | 8.2608 | 2.5468 | TBLE3 |
| VQ | HOLDING | XPBR31 | 0.6428 | 0.5354 | 17.6679 | 0.1136 | XPBR31 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | 0.0000 | ND |

Os pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.

## Concentração

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|
| VVAL | 2024-06-28 | AFTER_REVIEW | 11 | 23.3988 | 71.3308 | 0.1305 | {"Bancos": 30.310644731634405, "Energia": 9.576689296210757, "Outros (cisão)": 0.38512809432079154, "Saneamento": 25.13634544203648, "Seguros": 34.591192435797566} |
| VVAL | 2025-06-30 | PERIOD_END | 11 | 30.9198 | 76.9419 | 0.1611 | {"Bancos": 25.84608661762371, "Energia": 8.66382631367841, "Outros (cisão)": 0.3138017585208636, "Saneamento": 24.968676396188368, "Seguros": 40.20760891398864} |
| VQ | 2024-06-28 | AFTER_REVIEW | 7 | 32.4847 | 93.9876 | 0.2349 | {"Bancos": 25.995504165095763, "Energia": 30.83023886463972, "Outros (cisão)": 0.6428260518306926, "Seguros": 42.53143091843382} |
| VQ | 2025-06-30 | PERIOD_END | 7 | 43.8777 | 93.8992 | 0.2748 | {"Bancos": 23.44055229885881, "Energia": 23.624473017698588, "Outros (cisão)": 0.5353839533260275, "Seguros": 52.399590730116564} |

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
| CSMG3 | PASS_MATURE | ND | 13.5512 | INDETERMINATE | 3 | 3 | 0 |
| ELET3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| EQTL3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| ITUB4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 | ND |
| NEOE3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| PSSA3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| SANB4 | PASS_MATURE | ND | 14.3857 | INDETERMINATE | 5 | 1 | 0 |
| SAPR4 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| TAEE4 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TBLE3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TRPL4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| VIVT3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |

Canal até P/L 15: CSMG3, SANB4. Canal de reinvestimento produtivo entre 15 e 25: nenhuma aprovação comprovada neste corte. A classificação do canal de preço não presume que uma empresa deixou de investir.

Um limite inferior de P/L acima de 25 comprova rejeição por preço. Um limite superior até 15 comprova o canal maduro. Pontas desconhecidas continuam ND; o intervalo nunca substitui as exigências cumulativas de reinvestimento.


[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_2024.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.

## Verificação e reprodução

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Testes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.
