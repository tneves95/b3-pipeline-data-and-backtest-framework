# PR #4 — revisão de junho/2017 e retorno até junho/2018

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `2986ca2` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

| carteira | retorno_pct | vs_IBOV_pp | giro_pct | empresas_finais | maior_peso_final_pct | top5_final_pct |
|---|---|---|---|---|---|---|
| V0 | 10.2022 | -5.4776 | 10.0000 | 17 | 24.3487 | 58.7974 |
| V10 | 12.0781 | -3.6016 | 10.0000 | 9 | 24.4032 | 70.7568 |
| VVAL | 10.0646 | -5.6151 | 10.0000 | 11 | 22.6643 | 75.3000 |
| VQ | 19.3692 | 3.6895 | 0.0000 | 5 | 35.0530 | 100.0000 |
| IBOV | 15.6797 | 0.0000 | ND | ND | ND | ND |

Diferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.

Observações acumuladas desde a formação, sem extrapolar anos ainda não revisados:

| carteira | periodos | acumulado_desde_2014_pct | anos_positivos | anos_acima_IBOV |
|---|---|---|---|---|
| V0 | 4 | 36.5639 | 3 | 2 |
| V10 | 4 | 27.8672 | 2 | 1 |
| VVAL | 4 | 41.9300 | 4 | 3 |
| VQ | 4 | 52.0675 | 3 | 2 |
| IBOV | 4 | 36.8534 | 2 | ND |

## Financiamento da renovação

A [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.

| variant | ticker | reference_weight_pct | executed_weight_pct |
|---|---|---|---|
| VVAL | SAPR4 | 10.0000 | 10.0000 |

VVAL: 10 posições anteriores não reprovadas; fator de capital mantido entre 0.92841463 e 0.92841463. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Saídas determinadas exclusivamente pelo B00S-base: LIGT3.

VQ: 5 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

## Composição e contribuição por ação

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp | descendants |
|---|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBAS3 | 5.9079 | 5.9439 | 10.7361 | 0.6343 | BBAS3 |
| VVAL | HOLDING | BBDC4 | 22.7203 | 22.5177 | 9.0833 | 2.0637 | BBDC4 |
| VVAL | HOLDING | BRSR6 | 13.2964 | 14.4664 | 19.7499 | 2.6260 | BRSR6 |
| VVAL | HOLDING | CPFE3 | 3.7297 | 2.8015 | -17.3271 | -0.6463 | CPFE3 |
| VVAL | HOLDING | CPLE6 | 2.2535 | 1.9149 | -6.4730 | -0.1459 | CPLE6 |
| VVAL | HOLDING | ENBR3 | 3.8903 | 3.6085 | 2.0924 | 0.0814 | ENBR3 |
| VVAL | HOLDING | ITUB4 | 6.9294 | 7.3258 | 16.3608 | 1.1337 | ITUB4 |
| VVAL | HOLDING | PSSA3 | 16.9597 | 22.6643 | 47.0863 | 7.9857 | PSSA3 |
| VVAL | HOLDING | SAPR4 | 10.0000 | 7.9445 | -12.5588 | -1.2559 | SAPR4 |
| VVAL | HOLDING | SBSP3 | 11.2031 | 7.7070 | -24.2826 | -2.7204 | SBSP3 |
| VVAL | HOLDING | TBLE3 | 3.1097 | 3.1053 | 9.9096 | 0.3082 | TBLE3 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | 0.0000 | ND |
| VQ | HOLDING | ABCB4 | 13.5788 | 10.9003 | -4.1766 | -0.5671 | ABCB4 |
| VQ | HOLDING | BBDC4 | 12.7034 | 11.6087 | 9.0833 | 1.1539 | BBDC4 |
| VQ | HOLDING | ITUB4 | 13.9741 | 13.6219 | 16.3608 | 2.2863 | ITUB4 |
| VQ | HOLDING | PSSA3 | 28.4476 | 35.0530 | 47.0863 | 13.3949 | PSSA3 |
| VQ | HOLDING | TBLE3 | 31.2961 | 28.8160 | 9.9096 | 3.1013 | TBLE3 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |

Os pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.

## Concentração

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|
| VVAL | 2017-06-30 | AFTER_REVIEW | 11 | 22.7203 | 74.1794 | 0.1333 | {"Bancos": 48.853963965160816, "Energia": 12.983264288980964, "Saneamento": 21.20308615996949, "Seguros": 16.959685585888735} |
| VVAL | 2018-06-29 | PERIOD_END | 11 | 22.6643 | 75.3000 | 0.1476 | {"Bancos": 50.25386729831912, "Energia": 11.430277666788658, "Saneamento": 15.651549200638403, "Seguros": 22.66430583425382} |
| VQ | 2017-06-30 | AFTER_REVIEW | 5 | 31.2961 | 100.0000 | 0.2330 | {"Bancos": 40.25631981064674, "Energia": 31.296119370520024, "Seguros": 28.44756081883324} |
| VQ | 2018-06-29 | PERIOD_END | 5 | 35.0530 | 100.0000 | 0.2498 | {"Bancos": 36.131037945097674, "Energia": 28.81598910125312, "Seguros": 35.05297295364921} |

## Decisões de entrada anteriores aos retornos

| ticker | VVAL | PL | PL_max | VQ | dimensoes_satisfatorias | dimensoes_ND |
|---|---|---|---|---|---|---|
| ABCB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| BBAS3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| BBDC4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 |
| BRSR6 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| CMIG4 | INDETERMINATE | ND | ND | INDETERMINATE | 1 | 5 |
| CPFE3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| CPLE6 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| ENBR3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| EQTL3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| ITUB4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 |
| PSSA3 | PASS_MATURE | ND | 11.0818 | QUALIFIED_SATISFACTORY | 6 | 0 |
| SAPR4 | PASS_MATURE | ND | 13.4836 | INDETERMINATE | 3 | 3 |
| SBSP3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| TBLE3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| TIMP3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 |
| TRPL4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| VIVT4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |

Canal até P/L 15: PSSA3, SAPR4. Canal de reinvestimento produtivo entre 15 e 25: nenhuma aprovação comprovada neste corte. A classificação do canal de preço não presume que uma empresa deixou de investir.

| ticker | PL | crescimento_real_LPA_pct | payout_medio_pct | retorno_capital_pct | medida | minimo_IPCA_mais_6_pct | decisao |
|---|---|---|---|---|---|---|---|
| CPFE3 | 23.8304 | ND | ND | ND | ROIC_ND | 9.5971 | INDETERMINATE |
| TRPL4 | 18.8277 | ND | 50.3186 | ND | ROIC_ND | 9.5971 | INDETERMINATE |
| VIVT4 | 15.0557 | ND | ND | ND | ROIC_ND | 9.5971 | INDETERMINATE |


[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_2017.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.

## Verificação e reprodução

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Testes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.
