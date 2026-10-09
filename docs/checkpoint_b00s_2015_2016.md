# PR #4 — revisão de junho/2015 e retorno até junho/2016

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `00d94e4` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

| carteira | retorno_pct | vs_IBOV_pp | giro_pct | empresas_finais | maior_peso_final_pct | top5_final_pct |
|---|---|---|---|---|---|---|
| V0 | 2.0892 | 5.0167 | 2.4433 | 19 | 18.5433 | 56.1570 |
| V10 | -1.5886 | 1.3389 | 0.0000 | 9 | 18.9764 | 69.0807 |
| VVAL | 0.3919 | 3.3194 | 13.3333 | 12 | 24.5088 | 72.7071 |
| VQ | -5.1579 | -2.2303 | 0.0000 | 5 | 38.3139 | 100.0000 |
| IBOV | -2.9275 | 0.0000 | ND | ND | ND | ND |

Diferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.

Observações acumuladas desde a formação, sem extrapolar anos ainda não revisados:

| carteira | periodos | acumulado_desde_2014_pct | anos_positivos | anos_acima_IBOV |
|---|---|---|---|---|
| V0 | 2 | 1.0215 | 1 | 1 |
| V10 | 2 | -3.6962 | 0 | 1 |
| VVAL | 2 | 0.6959 | 2 | 2 |
| VQ | 2 | 10.5811 | 1 | 1 |
| IBOV | 2 | -3.0870 | 0 | ND |

## Financiamento da renovação

A [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.

| variant | ticker | reference_weight_pct | executed_weight_pct |
|---|---|---|---|
| VVAL | BBAS3 | 6.6667 | 6.6667 |
| VVAL | ITUB4 | 6.6667 | 6.6667 |

VVAL: 10 posições anteriores não reprovadas; fator de capital mantido entre 0.86666667 e 0.86666667. Nenhuma posição não FAIL foi liquidada pelo financiamento.

VQ: 5 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

## Composição e contribuição por ação

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp | descendants |
|---|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBAS3 | 6.6667 | 5.0634 | -23.7516 | -1.5834 | BBAS3 |
| VVAL | HOLDING | BBDC4 | 23.8971 | 24.5088 | 2.9616 | 0.7077 | BBDC4 |
| VVAL | HOLDING | CPFE3 | 3.5902 | 3.9615 | 10.7732 | 0.3868 | CPFE3 |
| VVAL | HOLDING | CPLE6 | 3.9830 | 3.4640 | -12.6894 | -0.5054 | CPLE6 |
| VVAL | HOLDING | CSMG3 | 3.6969 | 8.0336 | 118.1593 | 4.3682 | CSMG3 |
| VVAL | HOLDING | ENBR3 | 3.9870 | 4.9494 | 24.6264 | 0.9819 | ENBR3 |
| VVAL | HOLDING | GETI4 | 3.5010 | 3.3254 | -4.6447 | -0.1626 | TIET11 |
| VVAL | HOLDING | ITUB4 | 6.6667 | 6.8204 | 2.7067 | 0.1804 | ITUB4 |
| VVAL | HOLDING | LIGT3 | 2.9725 | 1.9710 | -33.4318 | -0.9938 | LIGT3 |
| VVAL | HOLDING | PSSA3 | 29.3808 | 19.6611 | -32.8197 | -9.6427 | PSSA3 |
| VVAL | HOLDING | SBSP3 | 7.7200 | 13.6833 | 77.9398 | 6.0169 | SBSP3 |
| VVAL | HOLDING | TBLE3 | 3.9381 | 4.5581 | 16.1986 | 0.6379 | TBLE3 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -4E-17 | ND |
| VQ | HOLDING | ABCB4 | 8.6922 | 11.2095 | 22.3092 | 1.9392 | ABCB4 |
| VQ | HOLDING | BBDC4 | 10.5425 | 11.4451 | 2.9616 | 0.3122 | BBDC4 |
| VQ | HOLDING | ITUB4 | 10.6080 | 11.4876 | 2.7067 | 0.2871 | ITUB4 |
| VQ | HOLDING | PSSA3 | 38.8852 | 27.5439 | -32.8197 | -12.7620 | PSSA3 |
| VQ | HOLDING | TBLE3 | 31.2721 | 38.3139 | 16.1986 | 5.0656 | TBLE3 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |

Os pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.

## Concentração

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|
| VVAL | 2015-06-30 | AFTER_REVIEW | 12 | 29.3808 | 74.3313 | 0.1678 | {"Bancos": 37.23047628593673, "Energia": 21.971864057411967, "Saneamento": 11.416822206874144, "Seguros": 29.380837449777157} |
| VVAL | 2016-06-30 | PERIOD_END | 12 | 24.5088 | 72.7071 | 0.1399 | {"Bancos": 36.39260773898121, "Energia": 22.22948906395564, "Saneamento": 21.716824927048155, "Seguros": 19.661078270015} |
| VQ | 2015-06-30 | AFTER_REVIEW | 5 | 38.8852 | 100.0000 | 0.2789 | {"Bancos": 29.842696710651673, "Energia": 31.27208288603278, "Seguros": 38.88522040331554} |
| VQ | 2016-06-30 | PERIOD_END | 5 | 38.3139 | 100.0000 | 0.2615 | {"Bancos": 34.14222750559575, "Energia": 38.313893846038034, "Seguros": 27.54387864836622} |

## Decisões de entrada anteriores aos retornos

| ticker | VVAL | PL | PL_max | VQ | dimensoes_satisfatorias | dimensoes_ND |
|---|---|---|---|---|---|---|
| ABCB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| BBAS3 | PASS_MATURE | ND | 14.5686 | INDETERMINATE | 3 | 3 |
| BBDC4 | PASS_MATURE | ND | 14.5224 | QUALIFIED_SATISFACTORY | 6 | 0 |
| BRSR6 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| CMIG4 | INDETERMINATE | ND | ND | INDETERMINATE | 1 | 5 |
| CPFE3 | PASS_MATURE | ND | 13.6894 | INDETERMINATE | 3 | 3 |
| CPLE6 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| CSMG3 | PASS_MATURE | ND | 3.5065 | INDETERMINATE | 3 | 3 |
| ENBR3 | PASS_MATURE | ND | 13.0191 | INDETERMINATE | 3 | 3 |
| EQTL3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| GETI4 | PASS_MATURE | ND | 6.5819 | INDETERMINATE | 2 | 4 |
| ITUB4 | PASS_MATURE | ND | 13.7063 | QUALIFIED_SATISFACTORY | 6 | 0 |
| LIGT3 | PASS_MATURE | ND | 8.0353 | INDETERMINATE | 4 | 2 |
| PSSA3 | REJECTED_REINVESTMENT | 16.5174 | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| SBSP3 | PASS_MATURE | 5.2307 | ND | INDETERMINATE | 2 | 4 |
| TBLE3 | PASS_MATURE | 13.7644 | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| TIMP3 | REJECTED_REINVESTMENT | 15.2190 | ND | INDETERMINATE | 4 | 2 |
| TRPL4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| VIVT4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |

Canal até P/L 15: BBAS3, BBDC4, CPFE3, CSMG3, ENBR3, GETI4, ITUB4, LIGT3, SBSP3, TBLE3. Canal de reinvestimento produtivo entre 15 e 25: nenhuma aprovação comprovada neste corte. A classificação do canal de preço não presume que uma empresa deixou de investir.

| ticker | PL | crescimento_real_LPA_pct | payout_medio_pct | retorno_capital_pct | medida | minimo_IPCA_mais_6_pct | decisao |
|---|---|---|---|---|---|---|---|
| PSSA3 | 16.5174 | ND | ND | 13.9771 | ROE_PARENT_AVERAGE_EQUITY | 14.4731 | REJECTED_REINVESTMENT |
| TIMP3 | 15.2190 | ND | ND | 11.5188 | ROIC_NOPAT_AVERAGE_EQUITY_PLUS_INTEREST_DEBT_LESS_CASH | 14.4731 | REJECTED_REINVESTMENT |


[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_2015.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.

## Verificação e reprodução

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Testes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.
