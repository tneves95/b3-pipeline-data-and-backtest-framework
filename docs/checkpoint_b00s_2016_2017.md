# PR #4 — revisão de junho/2016 e retorno até junho/2017

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `267e313` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

| carteira | retorno_pct | vs_IBOV_pp | giro_pct | empresas_finais | maior_peso_final_pct | top5_final_pct |
|---|---|---|---|---|---|---|
| V0 | 22.6682 | 0.5961 | 9.4586 | 17 | 19.8651 | 57.2482 |
| V10 | 18.4664 | -3.6057 | 7.7538 | 8 | 20.6611 | 74.9628 |
| VVAL | 28.0603 | 5.9883 | 11.3590 | 11 | 24.4721 | 76.5917 |
| VQ | 15.2029 | -6.8692 | 0.0000 | 5 | 31.2961 | 100.0000 |
| IBOV | 22.0721 | 0.0000 | ND | ND | ND | ND |

Diferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.

Observações acumuladas desde a formação, sem extrapolar anos ainda não revisados:

| carteira | periodos | acumulado_desde_2014_pct | anos_positivos | anos_acima_IBOV |
|---|---|---|---|---|
| V0 | 3 | 23.9212 | 2 | 2 |
| V10 | 3 | 14.0876 | 1 | 1 |
| VVAL | 3 | 28.9516 | 3 | 3 |
| VQ | 3 | 27.3926 | 2 | 1 |
| IBOV | 3 | 18.3037 | 1 | ND |

## Financiamento da renovação

A [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.

| variant | ticker | reference_weight_pct | executed_weight_pct |
|---|---|---|---|
| VVAL | BRSR6 | 5.0000 | 11.3590 |

VVAL: 10 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Saídas determinadas exclusivamente pelo B00S-base: CSMG3, TIET11.

VQ: 5 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

## Composição e contribuição por ação

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp | descendants |
|---|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBAS3 | 5.0634 | 6.3634 | 60.9405 | 3.0857 | BBAS3 |
| VVAL | HOLDING | BBDC4 | 24.5088 | 24.4721 | 27.8685 | 6.8303 | BBDC4 |
| VVAL | HOLDING | BRSR6 | 11.3590 | 14.3216 | 61.4611 | 6.9813 | BRSR6 |
| VVAL | HOLDING | CPFE3 | 3.9615 | 4.0173 | 29.8659 | 1.1831 | CPFE3 |
| VVAL | HOLDING | CPLE6 | 3.4640 | 2.4273 | -10.2652 | -0.3556 | CPLE6 |
| VVAL | HOLDING | ENBR3 | 4.9494 | 4.1903 | 8.4183 | 0.4167 | ENBR3 |
| VVAL | HOLDING | ITUB4 | 6.8204 | 7.4637 | 40.1388 | 2.7376 | ITUB4 |
| VVAL | HOLDING | LIGT3 | 1.9710 | 3.0606 | 98.8465 | 1.9483 | LIGT3 |
| VVAL | HOLDING | PSSA3 | 19.6611 | 18.2674 | 18.9825 | 3.7322 | PSSA3 |
| VVAL | HOLDING | SBSP3 | 13.6833 | 12.0669 | 12.9330 | 1.7697 | SBSP3 |
| VVAL | HOLDING | TBLE3 | 4.5581 | 3.3494 | -5.8983 | -0.2689 | TBLE3 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | 0.0000 | ND |
| VQ | HOLDING | ABCB4 | 11.2095 | 13.5788 | 39.5524 | 4.4336 | ABCB4 |
| VQ | HOLDING | BBDC4 | 11.4451 | 12.7034 | 27.8685 | 3.1896 | BBDC4 |
| VQ | HOLDING | ITUB4 | 11.4876 | 13.9741 | 40.1388 | 4.6110 | ITUB4 |
| VQ | HOLDING | PSSA3 | 27.5439 | 28.4476 | 18.9825 | 5.2285 | PSSA3 |
| VQ | HOLDING | TBLE3 | 38.3139 | 31.2961 | -5.8983 | -2.2599 | TBLE3 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -5E-16 | ND |

Os pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.

## Concentração

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|
| VVAL | 2016-06-30 | AFTER_REVIEW | 11 | 24.5088 | 76.0325 | 0.1453 | {"Bancos": 47.75157386699591, "Energia": 18.90409478129173, "Saneamento": 13.68325308169736, "Seguros": 19.661078270015} |
| VVAL | 2017-06-30 | PERIOD_END | 11 | 24.4721 | 76.5917 | 0.1440 | {"Bancos": 52.6208465421617, "Energia": 17.044892530770973, "Saneamento": 12.066899587570237, "Seguros": 18.267361339497096} |
| VQ | 2016-06-30 | AFTER_REVIEW | 5 | 38.3139 | 100.0000 | 0.2615 | {"Bancos": 34.14222750559575, "Energia": 38.313893846038034, "Seguros": 27.54387864836622} |
| VQ | 2017-06-30 | PERIOD_END | 5 | 31.2961 | 100.0000 | 0.2330 | {"Bancos": 40.25631981064674, "Energia": 31.296119370520024, "Seguros": 28.44756081883324} |

## Decisões de entrada anteriores aos retornos

| ticker | VVAL | PL | PL_max | VQ | dimensoes_satisfatorias | dimensoes_ND |
|---|---|---|---|---|---|---|
| ABCB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| BBAS3 | PASS_MATURE | ND | 9.4184 | INDETERMINATE | 3 | 3 |
| BBDC4 | PASS_MATURE | ND | 13.5026 | INDETERMINATE | 5 | 1 |
| BRSR6 | PASS_MATURE | ND | 11.8392 | INDETERMINATE | 3 | 3 |
| CMIG4 | INDETERMINATE | ND | ND | INDETERMINATE | 1 | 5 |
| CPFE3 | INDETERMINATE | ND | 18.2460 | INDETERMINATE | 3 | 3 |
| CPLE6 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| ENBR3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| EQTL3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| ITUB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| LIGT3 | PASS_MATURE | ND | 5.6721 | INDETERMINATE | 3 | 3 |
| PSSA3 | PASS_MATURE | ND | 10.0328 | QUALIFIED_SATISFACTORY | 6 | 0 |
| SBSP3 | PASS_MATURE | ND | 11.8280 | INDETERMINATE | 2 | 4 |
| TBLE3 | PASS_MATURE | ND | 14.7413 | QUALIFIED_SATISFACTORY | 6 | 0 |
| TIMP3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 |
| TRPL4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| VIVT4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |

Canal até P/L 15: BBAS3, BBDC4, BRSR6, LIGT3, PSSA3, SBSP3, TBLE3. Canal de reinvestimento produtivo entre 15 e 25: nenhuma aprovação comprovada neste corte. A classificação do canal de preço não presume que uma empresa deixou de investir.


[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_2016.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.

## Verificação e reprodução

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Testes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.
