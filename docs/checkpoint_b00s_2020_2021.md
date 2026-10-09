# PR #4 — revisão de junho/2020 e retorno até junho/2021

Protocolo V2 `7fea064`, critérios 15/25 e exigências de reinvestimento preservados. [Revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). PR draft, sem merge, impostos, custos ou aportes. Retorno total bruto com os eventos e qualificações herdados do PR #3.

As seleções, retornos, fontes e documentos aceitos de junho/2014–junho/2015 permanecem protegidos por comparação literal e hashes. Os 840 arquivos do PR #3 e as 11 tabelas de V0/V10 também permanecem protegidos. Decisões deste corte congeladas em `d6b9eed` antes do replay; critérios não foram ajustados após os resultados.

## Resultado do período

| carteira | retorno_pct | vs_IBOV_pp | giro_pct | empresas_finais | maior_peso_final_pct | top5_final_pct |
|---|---|---|---|---|---|---|
| V0 | -1.3833 | -34.7804 | 10.0000 | 22 | 20.2774 | 47.9112 |
| V10 | -1.2450 | -34.6420 | 0.0000 | 10 | 23.1413 | 65.5419 |
| VVAL | 1.3553 | -32.0418 | 2.5286 | 11 | 22.4040 | 70.7384 |
| VQ | 7.5330 | -25.8641 | 0.0000 | 7 | 32.1604 | 91.2942 |
| IBOV | 33.3971 | 0.0000 | ND | ND | ND | ND |

Diferenças em pontos percentuais. Resultados das carteiras efetivamente selecionadas, condicionados à evidência disponível e às qualificações dos eventos herdados; uma janela não demonstra superioridade estrutural.

Observações acumuladas desde a formação, sem extrapolar anos ainda não revisados:

| carteira | periodos | acumulado_desde_2014_pct | anos_positivos | anos_acima_IBOV |
|---|---|---|---|---|
| V0 | 7 | 92.7934 | 4 | 4 |
| V10 | 7 | 85.8516 | 3 | 3 |
| VVAL | 7 | 106.2245 | 6 | 4 |
| VQ | 7 | 113.2181 | 5 | 3 |
| IBOV | 7 | 138.4915 | 4 | ND |

## Financiamento da renovação

A [regra B2 congelada](b00s_b2_financiamento_2015.md) pede 20% por setor, divididos pela união de linhagens mantidas e candidatas qualificadas. Setores vazios não redistribuem seus 20%. Saídas B00S FAIL financiam primeiro; somente a diferença reduz proporcionalmente todas as sobreviventes. A perda do filtro de entrada de valuation ou qualidade não autoriza venda.

Nenhuma nova entrada aprovada neste corte.

VVAL: 11 posições anteriores não reprovadas; fator de capital mantido entre 1.02594165 e 1.02594165. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Saídas determinadas exclusivamente pelo B00S-base: CPFE3.

VQ: 7 posições anteriores não reprovadas; fator de capital mantido entre 1.00000000 e 1.00000000. Nenhuma posição não FAIL foi liquidada pelo financiamento.

Linhagens mantidas com B00S-base indeterminado: IRBR3. A continuidade herdada não equivale a aprovação de nova compra.

## Composição e contribuição por ação

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp | descendants |
|---|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBAS3 | 4.7064 | 4.9341 | 6.2591 | 0.2946 | BBAS3 |
| VVAL | HOLDING | BBDC4 | 16.1873 | 22.4040 | 40.2801 | 6.5203 | BBDC4 |
| VVAL | HOLDING | BBSE3 | 8.8441 | 7.7596 | -11.0734 | -0.9793 | BBSE3 |
| VVAL | HOLDING | BRSR6 | 9.5873 | 9.7917 | 3.5163 | 0.3371 | BRSR6 |
| VVAL | HOLDING | CPLE6 | 3.7068 | 3.8235 | 4.5468 | 0.1685 | CPLE6 |
| VVAL | HOLDING | ENBR3 | 3.1733 | 3.3467 | 6.8924 | 0.2187 | ENBR3 |
| VVAL | HOLDING | ITUB4 | 5.0866 | 6.0187 | 19.9287 | 1.0137 | ITUB4 |
| VVAL | HOLDING | PSSA3 | 20.1015 | 22.0570 | 11.2153 | 2.2544 | PSSA3 |
| VVAL | HOLDING | SAPR4 | 12.1090 | 8.2648 | -30.8219 | -3.7322 | SAPR4 |
| VVAL | HOLDING | SBSP3 | 13.0221 | 8.2210 | -36.0135 | -4.6897 | SBSP3 |
| VVAL | HOLDING | TBLE3 | 3.4755 | 3.3789 | -1.4612 | -0.0508 | TBLE3 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 | ND |
| VQ | HOLDING | ABCB4 | 7.3955 | 8.1343 | 18.2756 | 1.3516 | ABCB4 |
| VQ | HOLDING | BBDC4 | 8.3469 | 10.8888 | 40.2801 | 3.3621 | BBDC4 |
| VQ | HOLDING | BBSE3 | 8.8459 | 7.3153 | -11.0734 | -0.9795 | BBSE3 |
| VQ | HOLDING | IRBR3 | 2.5978 | 1.3905 | -42.4426 | -1.1026 | IRBR3 |
| VQ | HOLDING | ITUB4 | 9.4602 | 10.5507 | 19.9287 | 1.8853 | ITUB4 |
| VQ | HOLDING | PSSA3 | 31.0955 | 32.1604 | 11.2153 | 3.4875 | PSSA3 |
| VQ | HOLDING | TBLE3 | 32.2582 | 29.5601 | -1.4612 | -0.4714 | TBLE3 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | 0.0000 | ND |

Os pesos são os econômicos reais após a renovação. Cada retorno individual inclui proventos e sucessores atribuíveis à exposição de origem. O resíduo numérico está separado; a soma das contribuições reconcilia exatamente o retorno anual.

## Concentração

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|
| VVAL | 2020-06-30 | AFTER_REVIEW | 11 | 20.1015 | 71.0072 | 0.1236 | {"Bancos": 35.56758678623818, "Energia": 10.355683081354725, "Saneamento": 25.131130433577027, "Seguros": 28.945599698830065} |
| VVAL | 2021-06-30 | PERIOD_END | 11 | 22.4040 | 70.7384 | 0.1378 | {"Bancos": 43.14845866577528, "Energia": 10.549187445478104, "Saneamento": 16.485761868315034, "Seguros": 29.816592020431592} |
| VQ | 2020-06-30 | AFTER_REVIEW | 7 | 32.2582 | 90.0067 | 0.2306 | {"Bancos": 25.20254864939502, "Energia": 32.25823456047121, "Seguros": 42.53921679013378} |
| VQ | 2021-06-30 | PERIOD_END | 7 | 32.1604 | 91.2942 | 0.2260 | {"Bancos": 29.573758630379015, "Energia": 29.56011057248868, "Seguros": 40.8661307971323} |

## Decisões de entrada anteriores aos retornos

| ticker | VVAL | PL | PL_max | VQ | dimensoes_satisfatorias | dimensoes_ND | PL_min |
|---|---|---|---|---|---|---|---|
| ABCB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BBAS3 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| BBDC4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BBSE3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| BRSR6 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| CMIG4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| COCE5 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| CPLE6 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| ENBR3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| EQTL3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| ITUB4 | INDETERMINATE | ND | ND | INDETERMINATE | 5 | 1 | ND |
| NEOE3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| PSSA3 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 | ND |
| SANB4 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| SAPR4 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |
| SBSP3 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| TBLE3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TIET4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| TIMP3 | INDETERMINATE | ND | ND | INDETERMINATE | 4 | 2 | ND |
| TRPL4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 | ND |
| VIVT4 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 | ND |

Canal até P/L 15: nenhuma nova aprovação comprovada neste corte. Canal de reinvestimento produtivo entre 15 e 25: nenhuma aprovação comprovada neste corte. A classificação do canal de preço não presume que uma empresa deixou de investir.

Um limite inferior de P/L acima de 25 comprova rejeição por preço. Um limite superior até 15 comprova o canal maduro. Pontas desconhecidas continuam ND; o intervalo nunca substitui as exigências cumulativas de reinvestimento.

| ticker | PL | crescimento_real_LPA_pct | payout_medio_pct | retorno_capital_pct | medida | minimo_IPCA_mais_6_pct | decisao |
|---|---|---|---|---|---|---|---|
| TBLE3 | 15.8666 | ND | 71.0000 | ND | ROIC_ND | 7.8775 | INDETERMINATE |
| TIET4 | 19.5814 | ND | ND | ND | ROIC_ND | 7.8775 | INDETERMINATE |
| VIVT4 | 16.3538 | ND | ND | ND | ROIC_ND | 7.8775 | INDETERMINATE |


[Análises incrementais das seis dimensões, fontes e contrapontos](dossies_b00s_2020.md). Intervalos certificam somente o limite de admissão; capital, lucro ou P/L pontual não certificados ficam ND. Os critérios de crescimento real, retenção, ROIC/ROE e solidez são cumulativos: uma reprovação comprovada impede o prêmio, mesmo que outra condição ainda esteja pendente.

## Verificação e reprodução

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Testes verificam preservação histórica, ausência de fontes futuras, intervalos econômicos, financiamento B2, unidades, pesos, giro, atribuição anual e composta, planilha e hashes. O replay offline precisa produzir ausência de diff. Sensibilidades predefinidas continuam separadas das decisões principais nos CSVs e na planilha.

### Posição anterior fora do universo de novas compras: IRBR3

| variant | ticker | base_status | before | after |
|---|---|---|---|---|
| VQ | IRBR3 | INDETERMINATE | 0.0515 | 0.0515 |

Qualidade atual: **REJECTED_EVIDENCED**. Atualização material de posição retida, com fatos divulgados até 30/06/2020, inclusive DFP 94457 e ITR 94455 recebidos nessa data. O juízo de 2019 permanece intacto porque essas revelações não estavam disponíveis naquele corte. Reprovação de qualidade em 2020 não determina venda na carteira principal: a regra B2 exige FAIL comprovado da base. Não se presume retorno posterior nem se executa sensibilidade de saída estrutural. A ficha atualiza o acompanhamento da posição; não altera o status B00S-base nem autoriza uma venda extraordinária. A decisão de entrada de anos anteriores permanece congelada.
