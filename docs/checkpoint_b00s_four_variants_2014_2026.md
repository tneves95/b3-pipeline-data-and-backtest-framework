# PR #4 — formação de junho/2014 e primeiro retorno realizado

Protocolo V2 exclusivo no commit `7fea064`; revisão do coordenador [6069878965](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6069878965). PR draft, sem merge. PR #3 preservado integralmente. V0/V10 mantêm retornos, pesos, concentração, giro e atribuição aceitos no commit `3c1dfa5`, comparados literalmente em 11 tabelas.

Este lote fecha a avaliação empresa por empresa dos 20 candidatos de junho/2014 e calcula suas carteiras até junho/2015, antes da próxima seleção. Junho/2015–2025 exige revisão incremental das mudanças materiais; as células futuras VVAL/VQ ficam vazias, não zero. Não se projeta a análise de 2014 por doze anos. O [checkpoint anterior](reviews/checkpoint_before_2014_review_3c1dfa5.md) foi preservado como histórico e não representa o estado documental atual.

Retorno total bruto, sem custos, IR ou aportes; eventos, unidades e linhagens herdados do PR #3, com as mesmas qualificações. Critérios 15/25, LPA real 4%, retenção 20%, retorno econômico acima da inflação + 6 pp e solidez não foram alterados. Não se concedeu prêmio de reinvestimento sem provas. DY 6% e Graham 22,5 são apenas diagnósticos; VQ não usa score.

## Resultado do lote: junho/2014 → junho/2015

| variant | return_pct | vs_ibov_pp | vs_v0_pp | initial_companies | initial_top5_pct | final_largest_pct | final_top5_pct |
|---|---|---|---|---|---|---|---|
| V0 | -1.0459 | -0.8816 | 0.0000 | 20 | 60.0000 | 27.4904 | 58.1866 |
| V10 | -2.1416 | -1.9774 | -1.0958 | 9 | 60.0000 | 27.7982 | 72.6051 |
| VVAL | 0.3028 | 0.4671 | 1.3487 | 10 | 79.1667 | 33.9010 | 79.5784 |
| VQ | 16.5949 | 16.7592 | 17.6407 | 5 | 100.0000 | 38.8852 | 100.0000 |
| IBOV | -0.1643 | 0.0000 | 0.8816 | ND | ND | ND | ND |

Congelamento anterior ao replay: `ee8bf47`; 72 originais arquivados.

Diferenças em pontos percentuais. As carteiras são efetivamente selecionadas com a documentação disponível; não são cenários que aprovam lacunas. Não há revisão intermediária neste primeiro período: giro unilateral de vendas é zero e compras iniciais são formação, não giro. Não se infere superioridade estrutural de uma única janela.

## Composição inicial e atribuição do primeiro período

| variant | row_type | ticker | initial_weight_pct | final_weight_pct | exposure_return_pct | contribution_pp |
|---|---|---|---|---|---|---|
| VVAL | HOLDING | BBDC4 | 25.0000 | 27.5736 | 10.6285 | 2.6571 |
| VVAL | HOLDING | CPFE3 | 4.1667 | 4.1426 | -0.2776 | -0.0116 |
| VVAL | HOLDING | CPLE6 | 4.1667 | 4.5958 | 10.6326 | 0.4430 |
| VVAL | HOLDING | CSMG3 | 12.5000 | 4.2656 | -65.7717 | -8.2215 |
| VVAL | HOLDING | ENBR3 | 4.1667 | 4.6004 | 10.7431 | 0.4476 |
| VVAL | HOLDING | GETI4 | 4.1667 | 4.0397 | -2.7546 | -0.1148 |
| VVAL | HOLDING | LIGT3 | 4.1667 | 3.4299 | -17.4341 | -0.7264 |
| VVAL | HOLDING | PSSA3 | 25.0000 | 33.9010 | 36.0145 | 9.0036 |
| VVAL | HOLDING | SBSP3 | 12.5000 | 8.9076 | -28.5230 | -3.5654 |
| VVAL | HOLDING | TBLE3 | 4.1667 | 4.5439 | 9.3850 | 0.3910 |
| VVAL | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 |
| VQ | HOLDING | ABCB4 | 11.1111 | 8.6922 | -8.7882 | -0.9765 |
| VQ | HOLDING | BBDC4 | 11.1111 | 10.5425 | 10.6285 | 1.1809 |
| VQ | HOLDING | ITUB4 | 11.1111 | 10.6080 | 11.3152 | 1.2572 |
| VQ | HOLDING | PSSA3 | 33.3333 | 38.8852 | 36.0145 | 12.0048 |
| VQ | HOLDING | TBLE3 | 33.3333 | 31.2721 | 9.3850 | 3.1283 |
| VQ | NUMERICAL_RESIDUAL | ND | ND | ND | ND | -0.0000 |

Atribuição em pontos percentuais, incluindo resíduo numérico separado; soma exatamente o retorno publicado. Setores representados têm o mesmo peso na formação e as empresas dividem igualmente seu setor, conforme regra original. Não se usam pesos do B00S-base para simular uma carteira filtrada.

## Concentração no lote

| variant | date | phase | companies | largest_company_pct | top5_pct | issuer_hhi | sector_hhi | sector_weights_pct |
|---|---|---|---|---|---|---|---|---|
| VVAL | 2014-06-30 | AFTER_REVIEW | 10 | 25.0000 | 79.1667 | 0.1667 | 0.2500 | {"Bancos": 25.0, "Energia": 24.999999999999996, "Saneamento": 25.0, "Seguros": 25.0} |
| VVAL | 2015-06-30 | PERIOD_END | 10 | 33.9010 | 79.5784 | 0.2115 | 0.2726 | {"Bancos": 27.573626483773158, "Energia": 25.352150835475346, "Saneamento": 13.173256392547088, "Seguros": 33.90096628820441} |
| VQ | 2014-06-30 | AFTER_REVIEW | 5 | 33.3333 | 100.0000 | 0.2593 | 0.3333 | {"Bancos": 33.33333333333333, "Energia": 33.33333333333333, "Seguros": 33.33333333333333} |
| VQ | 2015-06-30 | PERIOD_END | 5 | 38.8852 | 100.0000 | 0.2789 | 0.3381 | {"Bancos": 29.842696710651673, "Energia": 31.27208288603278, "Seguros": 38.88522040331554} |
## Decisões efetivas antes dos retornos

| ticker | VVAL | PL | PL_max | VQ | SAT | ND |
|---|---|---|---|---|---|---|
| ABCB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| BBAS3 | INDETERMINATE | 4.8474 | ND | INDETERMINATE | 3 | 3 |
| BBDC4 | PASS_MATURE | ND | 14.9427 | QUALIFIED_SATISFACTORY | 6 | 0 |
| BRSR6 | INDETERMINATE | ND | ND | INDETERMINATE | 3 | 3 |
| CMIG4 | INDETERMINATE | 7.2138 | ND | INDETERMINATE | 1 | 5 |
| COCE5 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| CPFE3 | PASS_MATURE | 10.7419 | ND | INDETERMINATE | 3 | 3 |
| CPLE6 | PASS_MATURE | 7.0071 | ND | INDETERMINATE | 2 | 4 |
| CSMG3 | PASS_MATURE | ND | 11.2361 | INDETERMINATE | 4 | 2 |
| ENBR3 | PASS_MATURE | 9.0942 | ND | INDETERMINATE | 3 | 3 |
| EQTL3 | INDETERMINATE | 26.9202 | ND | INDETERMINATE | 2 | 4 |
| GETI4 | PASS_MATURE | 7.3526 | ND | INDETERMINATE | 3 | 3 |
| ITUB4 | INDETERMINATE | ND | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| LIGT3 | PASS_MATURE | 7.2446 | ND | INDETERMINATE | 4 | 2 |
| PSSA3 | PASS_MATURE | 14.1690 | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| SBSP3 | PASS_MATURE | 8.0983 | ND | INDETERMINATE | 3 | 3 |
| TBLE3 | PASS_MATURE | 14.4110 | ND | QUALIFIED_SATISFACTORY | 6 | 0 |
| TIMP3 | INDETERMINATE | 21.1034 | ND | INDETERMINATE | 4 | 2 |
| TRPL4 | INDETERMINATE | ND | ND | INDETERMINATE | 2 | 4 |
| VIVT4 | INDETERMINATE | 12.6388 | ND | INDETERMINATE | 2 | 4 |

[Tabela auditável da formação](../research/b00s_four_variants_2014_2026/results/formation_2014_review.csv): setor, P/L antes/depois, efeito do ajuste, decisões e razões, documentos/datas/páginas e ND específico.

### Cobertura por setor em 2014

| sector | pass_candidates | valuation_approved | valuation_potential_weight_affected_pct | quality_qualified | quality_potential_weight_affected_pct |
|---|---|---|---|---|---|
| Bancos | 5 | 1 | 16.0000 | 3 | 8.0000 |
| Energia | 10 | 6 | 8.0000 | 1 | 18.0000 |
| Saneamento | 2 | 2 | 0 | 0 | 20.0000 |
| Seguros | 1 | 1 | 0 | 1 | 0 |
| Telecom | 2 | 0 | 20.0000 | 0 | 20.0000 |

Admissões VVAL passam de 2 para 10, e VQ de 0 para 5. O peso potencial B00S coberto por admissões VVAL passa de 6% para 56%; na VQ chega a 34%. Esses pesos medem cobertura do universo original, não exposição das carteiras filtradas. Permanecem 44% e 66% do peso-base sem admissão, respectivamente. As 120 dimensões de qualidade têm 71 conclusões satisfatórias e 49 indeterminadas específicas.


[As seis avaliações de cada empresa](dossies_b00s_v2.md) explicam fatos favoráveis, contrapontos, julgamentos, páginas e datas. [Revisão adversarial independente](reviews/adversarial_2014.json) registra contestação de perímetros e reavaliações antes dos retornos. O manifesto conserva o hash dos PDFs originais; o congelamento das fichas precede o replay.

Porto: lucro recorrente atribuível2013 de R$703,5 mi, em vez do lucro contábil R$ 1.405,207 mi; P/L passa de13,7883 para14,1690. O ganho fiscal não é removido pelo valor bruto isolado. Copasa: ganho atuarial 2010 identificado no original; efeitos fiscais/reversões tratados por intervalos conservadores sobre a mesma mediana de cinco lucros reais. Não são uma nova fórmula ou um ponto estimado. TIM: crédito fiscal 2010 retirado, mas sua faixa de preço ainda exige todas as provas de reinvestimento. Vivo: incorporação 2011 e ganhos de torres impedem comparar mecanicamente os cinco exercícios; conflito societário conhecido também é contraponto da governança.

O limite superior do P/L é usado somente para demonstrar que toda a faixa documental cabe no canal maduro. Intervalos que cruzam 15 não recebem aprovação nem migram automaticamente ao canal de reinvestimento. Ajustes de ganhos não autorizam adicionar perdas operacionais, de crédito ou hidrológicas. O cálculo corrige cada exercício apenas pelo IPCA conhecido no corte; capitalização continua por quantidade e preço de cada classe.

## Controles aceitos — doze períodos, até junho/2026

| variant | periods | final_pct | cagr_pct | above_ibov_years | annual_close_max_drawdown_pct | annual_population_std_pct |
|---|---|---|---|---|---|---|
| V0 | 12 | 402.1320 | 14.3935 | 9 | -10.2016 | 18.0736 |
| V10 | 12 | 386.7677 | 14.0977 | 8 | -7.5397 | 18.5746 |
| IBOV | 12 | 223.5469 | 10.2795 | 0 | -22.2865 | 16.8453 |

Drawdown e desvio acima usam fechamentos anuais, não observações diárias. VVAL/VQ ainda não têm resultado de doze períodos validado neste lote.

| year | V0 | V10 | VVAL | VQ | IBOV |
|---|---|---|---|---|---|
| 2014 | -1.0459 | -2.1416 | 0.3028 | 16.5949 | -0.1643 |
| 2015 | 2.0892 | -1.5886 | ND | ND | -2.9275 |
| 2016 | 22.6682 | 18.4664 | ND | ND | 22.0721 |
| 2017 | 10.2022 | 12.0781 | ND | ND | 15.6797 |
| 2018 | 51.6276 | 51.6632 | ND | ND | 38.7626 |
| 2019 | -5.5879 | -2.9562 | ND | ND | -5.8548 |
| 2020 | -1.3833 | -1.2450 | ND | ND | 33.3971 |
| 2021 | -3.5526 | -3.5219 | ND | ND | -22.2865 |
| 2022 | 34.8217 | 29.9839 | ND | ND | 19.8342 |
| 2023 | 14.7043 | 14.5138 | ND | ND | 4.9282 |
| 2024 | 37.4777 | 45.9123 | ND | ND | 12.0640 |
| 2025 | 27.0173 | 24.9935 | ND | ND | 23.8880 |

## Sensibilidades predefinidas no mesmo período

| case | periods | final_pct | difference_pp |
|---|---|---|---|
| VVAL_12_20 | 1 | -23.4828 | -23.7856 |
| VVAL_15_25 | 1 | 0.3028 | 0.0000 |
| VVAL_18_30 | 1 | 0.3028 | 0.0000 |
| BAZIN_6_DIAGNOSTIC | 0 | ND | ND |
| GRAHAM_22_5_DIAGNOSTIC | 1 | -11.7350 | -12.0379 |
| VVAL_ALL_UNKNOWN_INCLUDED | 1 | -1.0459 | -1.3487 |
| VQ_ALL_UNKNOWN_INCLUDED | 1 | -1.0459 | 0.0000 |

São 47 cenários: faixas 12/20, 15/25 e 18/30, dois diagnósticos, inclusões de lacunas e tratamentos simétricos dos 20 emissores deste corte. Cada retirada VQ realmente remove a empresa, inclusive quando já qualificada. Cenários não alteram as decisões principais nem constituem limites de retorno.


## Reprodução e próximo corte

`python scripts/b00s_fundamentals.py`; `python scripts/b00s_sensitivities.py`; `python scripts/b00s_variants.py --stage all`; `python scripts/b00s_report.py`.

Replay offline; PDFs originais, páginas extraídas, datas e hashes arquivados. O coletor online é separado e nunca executado no CI. Testes cobrem fontes posteriores, alteração de originais, medianas/intervalos, preço por classe, reinvestimento, seis dimensões sem compensação, preservação exata V0/V10, atribuição, concentração, continuidade B2 e bloqueio de liquidação de não FAIL. CSVs são fonte da planilha; manifesto confere os hashes. O CI repete a geração e exige ausência de diff.

Próximo lote: junho/2015, reutilizando as vinte teses iniciais e examinando mudanças materiais de lucro/perímetro, crédito/capital, seca/tarifa/concessões, CAPEX e relações com controladores. Só depois dessa revisão será calculada a seleção seguinte; nenhum critério será calibrado ao retorno deste lote.
