# PR #4 — revisão de junho/2021 e retorno até junho/2022

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `b6f4f14` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

| carteira | retorno_pct | vs_IBOV_pp | giro_pct | empresas_finais | maior_peso_final_pct | top5_final_pct |
|---|---|---|---|---|---|---|
| V0 | -3.5526 | 18.7340 | 11.1111 | 23 | 13.9869 | 44.9838 |
| V10 | -3.5219 | 18.7646 | 0.0000 | 11 | 16.6882 | 58.4528 |
| VVAL | -8.8037 | 13.4828 | 9.7917 | 12 | 19.0841 | 65.3328 |
| VQ | -8.4467 | 13.8398 | 1.3905 | 7 | 36.7922 | 90.0398 |
| IBOV | -22.2865 | 0.0000 | ND | ND | ND | ND |

Diferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.

Observações acumuladas desde a formação, sem extrapolar anos ainda não revisados:

| carteira | periodos | acumulado_desde_2014_pct | anos_positivos | anos_acima_IBOV |
|---|---|---|---|---|
| V0 | 8 | 85.9443 | 4 | 5 |
| V10 | 8 | 79.3060 | 3 | 4 |
| VVAL | 8 | 88.0690 | 6 | 5 |
| VQ | 8 | 95.2082 | 5 | 4 |
| IBOV | 8 | 85.3399 | 4 | ND |

## Financiamento da renovação

A [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.

| variant | ticker | reference_weight_pct | executed_weight_pct |
|---|---|---|---|
| VVAL | CSMG3 | 6.6667 | 9.7917 |

VVAL: 10 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Saídas determinadas exclusivamente pelo B00S-base: BRSR6.

VQ: 6 posições anteriores não reprovadas; fator de capital mantido entre 1.01410077 e 1.01410077. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Saídas determinadas exclusivamente pelo B00S-base: IRBR3.

## Composição e contribuição por ação

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp | descendants |
|---|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBAS3 | 4.9341 | 6.0945 | 12.6434 | 0.6238 | BBAS3 |
| VVAL | HOLDING | BBDC4 | 22.4040 | 19.0841 | -22.3174 | -5.0000 | BBDC4 |
| VVAL | HOLDING | BBSE3 | 7.7596 | 10.1954 | 19.8232 | 1.5382 | BBSE3 |
| VVAL | HOLDING | CPLE6 | 3.8235 | 5.7070 | 36.1197 | 1.3811 | CPLE6 |
| VVAL | HOLDING | CSMG3 | 9.7917 | 8.3711 | -22.0348 | -2.1576 | CSMG3 |
| VVAL | HOLDING | ENBR3 | 3.3467 | 4.7065 | 28.2505 | 0.9455 | ENBR3 |
| VVAL | HOLDING | ITUB4 | 6.0187 | 5.6248 | -14.7728 | -0.8891 | ITUB4;XPBR31 |
| VVAL | HOLDING | PSSA3 | 22.0570 | 16.8275 | -30.4255 | -6.7109 | PSSA3 |
| VVAL | HOLDING | SAPR4 | 8.2648 | 8.6136 | -4.9548 | -0.4095 | SAPR4 |
| VVAL | HOLDING | SBSP3 | 8.2210 | 10.6122 | 17.7221 | 1.4569 | SBSP3 |
| VVAL | HOLDING | TBLE3 | 3.3789 | 4.1634 | 12.3679 | 0.4179 | TBLE3 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |
| VQ | HOLDING | ABCB4 | 8.2490 | 9.3848 | 4.1588 | 0.3431 | ABCB4 |
| VQ | HOLDING | BBDC4 | 11.0423 | 9.3694 | -22.3174 | -2.4644 | BBDC4 |
| VQ | HOLDING | BBSE3 | 7.4185 | 9.7091 | 19.8232 | 1.4706 | BBSE3 |
| VQ | HOLDING | ITUB4 | 10.6995 | 9.9602 | -14.7728 | -1.5806 | ITUB4;XPBR31 |
| VQ | HOLDING | PSSA3 | 32.6138 | 24.7844 | -30.4255 | -9.9229 | PSSA3 |
| VQ | HOLDING | TBLE3 | 29.9769 | 36.7922 | 12.3679 | 3.7075 | TBLE3 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | 0.0000 | ND |

Os pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.

## Concentração

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|
| VVAL | 2021-06-30 | AFTER_REVIEW | 11 | 22.4040 | 70.7384 | 0.1378 | {"Bancos": 33.35675703058602, "Energia": 10.549187445478104, "Saneamento": 26.277463503504293, "Seguros": 29.816592020431592} |
| VVAL | 2022-06-30 | PERIOD_END | 12 | 19.0841 | 65.3328 | 0.1144 | {"Bancos": 30.319423605170826, "Energia": 14.576917841914192, "Outros (cisão)": 0.48391255734361055, "Saneamento": 27.596862084967704, "Seguros": 27.022883910603667} |
| VQ | 2021-06-30 | AFTER_REVIEW | 6 | 32.6138 | 92.5815 | 0.2322 | {"Bancos": 29.99077140589621, "Energia": 29.976930899877363, "Seguros": 40.03229769422643} |
| VQ | 2022-06-30 | PERIOD_END | 7 | 36.7922 | 90.0398 | 0.2322 | {"Bancos": 27.857383906104992, "Energia": 36.79218386669748, "Outros (cisão)": 0.8568981388520134, "Seguros": 34.49353408834553} |

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
| CSMG3 | PASS_MATURE | ND | 14.7423 | INDETERMINATE | 4 | 2 | 0 |
| ENBR3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| EQTL3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| ITUB4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 | ND |
| NEOE3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| PSSA3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| SANB4 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| SAPR4 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| SBSP3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| TAEE4 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TBLE3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TRPL4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| VIVT3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |

Canal até P/L 15: CSMG3. Canal de reinvestimento produtivo entre 15 e 25: nenhuma aprovação comprovada neste corte. A classificação do canal de preço não presume que uma empresa deixou de investir.

Um limite inferior de P/L acima de 25 comprova rejeição por preço. Um limite superior até 15 comprova o canal maduro. Pontas desconhecidas continuam ND; o intervalo nunca substitui as exigências cumulativas de reinvestimento.

| ticker | PL | crescimento_real_LPA_pct | payout_medio_pct | retorno_capital_pct | medida | minimo_IPCA_mais_6_pct | decisao |
|---|---|---|---|---|---|---|---|
| EQTL3 | 21.5258 | ND | ND | ND | ROIC_ND | 14.0559 | INDETERMINATE |


[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_2021.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.

## Verificação e reprodução

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Testes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.
