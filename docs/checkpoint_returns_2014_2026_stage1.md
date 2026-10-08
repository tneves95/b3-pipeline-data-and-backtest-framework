# Checkpoint — Barsi × Graham, etapa percentual 2014–2026 — 08/10/2026

**Quatro trajetórias contínuas calculadas: 48 retornos anuais, 48 acumulados e IBOV nas três tabelas. São reconstruções qualificadas, não uma certificação integral das seleções PIT e de todos os direitos.** Continuação de `5cf7eb4`, na branch `study/returns-2014-2026-stage1`, conforme a [revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/3#issuecomment-6063812812). PR #3 permanece draft, sem merge. BH padrão, IBOV, R03 até junho/2016 e B00S até junho/2015 são entradas imutáveis, verificadas por SHA-256.

Os números centrais usam a regra explícita: nova entrada somente com PASS demonstrado; INDETERMINATE não entra e não autoriza vender posição herdada. As sensibilidades abaixo mostram que pendências de seleção ainda podem alterar o ranking. Não atribuir ao ranking central uma vitória definitiva de filosofia. Nenhuma simulação de dinheiro investido, caixa, IR, aportes ou execução operacional foi realizada.

**Tabela 1 — rentabilidade anual junho→junho (%)**

| Período | Início | Fim | R03 B2 | B00S B2 | B00S BH+entradas | BH padrão | IBOV |
|---|---|---|---|---|---|---|---|
| 2014–2015 | 2014-06-30 | 2015-06-30 | -45,0683 | -1,0459 | -1,0459 | 22,3021 | -0,1643 |
| 2015–2016 | 2015-06-30 | 2016-06-30 | 3,5198 | 2,0892 | 2,1621 | 11,8038 | -2,9275 |
| 2016–2017 | 2016-06-30 | 2017-06-30 | 33,7289 | 22,6682 | 23,2799 | 17,1925 | 22,0721 |
| 2017–2018 | 2017-06-30 | 2018-06-29 | 3,8081 | 10,2022 | 8,6115 | 1,8464 | 15,6797 |
| 2018–2019 | 2018-06-29 | 2019-06-28 | 66,3124 | 51,6276 | 52,5430 | 40,6323 | 38,7626 |
| 2019–2020 | 2019-06-28 | 2020-06-30 | 17,0398 | -5,5879 | -5,8369 | 18,9133 | -5,8548 |
| 2020–2021 | 2020-06-30 | 2021-06-30 | 28,4042 | -1,3833 | -2,1965 | 18,9660 | 33,3971 |
| 2021–2022 | 2021-06-30 | 2022-06-30 | -12,9730 | -3,5526 | -5,4546 | -11,5850 | -22,2865 |
| 2022–2023 | 2022-06-30 | 2023-06-30 | 45,3435 | 34,8217 | 35,6302 | 37,3725 | 19,8342 |
| 2023–2024 | 2023-06-30 | 2024-06-28 | 5,1083 | 14,7043 | 12,8821 | -2,6078 | 4,9282 |
| 2024–2025 | 2024-06-28 | 2025-06-30 | 27,8418 | 37,4777 | 40,3264 | -0,1868 | 12,0640 |
| 2025–2026 | 2025-06-30 | 2026-06-30 | 46,3224 | 27,0173 | 25,7550 | 12,6075 | 23,8880 |

[CSV anual](../research/returns_2014_2026_results/annual_returns_pct.csv) · [excesso anual sobre IBOV, em p.p.](../research/returns_2014_2026_results/annual_excess_pp.csv).

**Tabela 2 — rentabilidade acumulada desde junho/2014 (%)**

| Até | R03 B2 | B00S B2 | B00S BH+entradas | BH padrão | IBOV |
|---|---|---|---|---|---|
| 2015-06-30 | -45,0683 | -1,0459 | -1,0459 | 22,3021 | -0,1643 |
| 2016-06-30 | -43,1348 | 1,0215 | 1,0936 | 36,7384 | -3,0870 |
| 2017-06-30 | -23,9549 | 23,9212 | 24,6281 | 60,2471 | 18,3037 |
| 2018-06-29 | -21,0590 | 36,5639 | 35,3604 | 63,2059 | 36,8534 |
| 2019-06-28 | 31,2887 | 107,0686 | 106,4828 | 129,5202 | 89,9014 |
| 2020-06-30 | 53,6600 | 95,4978 | 94,4306 | 172,9300 | 78,7832 |
| 2021-06-30 | 97,3058 | 92,7934 | 90,1600 | 224,6939 | 138,4915 |
| 2022-06-30 | 71,7093 | 85,9443 | 79,7875 | 187,0781 | 85,3399 |
| 2023-06-30 | 149,5683 | 150,6933 | 143,8462 | 294,3665 | 122,1007 |
| 2024-06-28 | 162,3170 | 187,5561 | 175,2587 | 284,0822 | 133,0463 |
| 2025-06-30 | 235,3507 | 295,3256 | 286,2606 | 283,3649 | 161,1609 |
| 2026-06-30 | 390,6934 | 402,1320 | 385,7418 | 331,6976 | 223,5469 |

Encadeamento `100 × (produto(1 + retorno anual decimal) − 1)`. O índice nunca reinicia em 2020. [CSV acumulado](../research/returns_2014_2026_results/cumulative_returns_pct.csv).

**Tabela 3 — consolidado até junho/2026, caso central qualificado**

| Série | Janelas | Acumulado % | Excesso IBOV p.p. | CAGR % | Acima IBOV | Anos + / − | Pior período | Pior % | Rank final | Rank médio |
|---|---|---|---|---|---|---|---|---|---|---|
| R03 B2 | 12/12 | 390,6934 | 167,1465 | 14,1741 | 9/12 | 10 / 2 | 2014–2015 | -45,0683 | 2 | 2,4167 |
| B00S B2 | 12/12 | 402,1320 | 178,5851 | 14,3935 | 9/12 | 8 / 4 | 2019–2020 | -5,5879 | 1 | 2,6667 |
| B00S BH+entradas | 12/12 | 385,7418 | 162,1950 | 14,0776 | 9/12 | 8 / 4 | 2019–2020 | -5,8369 | 3 | 2,7500 |
| BH padrão | 12/12 | 331,6976 | 108,1507 | 12,9618 | 6/12 | 9 / 3 | 2021–2022 | -11,5850 | 4 | 3,3333 |
| IBOV | 12/12 | 223,5469 | 0,0000 | 10,2795 | — | 8 / 4 | 2021–2022 | -22,2865 | 5 | 3,7500 |

CAGR usa dias efetivos/365,25. Rank anual/final: maior retorno ocupa 1º lugar entre as cinco séries; empates recebem o mesmo posto. Rank médio é a média dos 12 postos. `consistency_rank` no CSV ordena somente as quatro carteiras pela quantidade de anos estritamente acima do IBOV, com empates. Essa frequência é diferente do retorno final. [Consolidado completo, incluindo média, mediana e melhor ano](../research/returns_2014_2026_results/consolidated_pct.csv).

**Ranking anual do mesmo caso**

| Período | R03 B2 | B00S B2 | B00S BH+entradas | BH padrão | IBOV |
|---|---|---|---|---|---|
| 2014–2015 | 5 | 3 | 3 | 1 | 2 |
| 2015–2016 | 2 | 4 | 3 | 1 | 5 |
| 2016–2017 | 1 | 3 | 2 | 5 | 4 |
| 2017–2018 | 4 | 2 | 3 | 5 | 1 |
| 2018–2019 | 1 | 3 | 2 | 4 | 5 |
| 2019–2020 | 2 | 3 | 4 | 1 | 5 |
| 2020–2021 | 2 | 4 | 5 | 3 | 1 |
| 2021–2022 | 4 | 1 | 2 | 3 | 5 |
| 2022–2023 | 1 | 4 | 3 | 2 | 5 |
| 2023–2024 | 3 | 1 | 2 | 5 | 4 |
| 2024–2025 | 3 | 2 | 1 | 5 | 4 |
| 2025–2026 | 1 | 2 | 3 | 5 | 4 |

**Continuidade e composição efetiva**

R03 parte das posições de junho/2016 do checkpoint aceito, que já carregam a perda de 2014–2015 e a renovação seletiva de 2015. B00S parte das unidades de junho/2015 aceitas. B2 preserva os pesos relativos dos sobreviventes; somente FAIL vende integralmente. As saídas financiam as novas entradas; apenas a insuficiência provoca redução proporcional dos sobreviventes. Excedente das saídas vai aos entrantes na proporção dos alvos; sem entrantes, distribui-se entre os sobreviventes. Não há reconstrução anual com pesos iguais. Os alvos iguais do R03 e por grupo/nome do B00S dimensionam apenas as entradas.

B00S BH+entradas significa retenção das empresas e sucessoras, com redistribuição interna para novos PASS. Não é BH passivo sem transações: as reduções proporcionais financiam entradas sem aporte. Troca de ticker ou novo CNPJ de uma holding não equivale a reprovação fundamental. TIMS/AESB herdadas ficam retidas quando a classificação é indeterminada; TRPL4→ISAE4 não sai por liquidez artificialmente truncada do ticker antigo em 2025. Os alvos 2020–2025 vêm dos screeners congelados; decisões adicionais e ressalvas estão nos livros, sem usar os retornos do legado como novos trechos.

A entrada demonstrada de IRBR3 em junho/2019 usa lucro e dividendos de 2014 do FRE 73863, recebido em 07/05/2018, junto aos anos seguintes do screener PIT. O B00S carrega sua queda posterior. LINX3 entra no R03 em 2016 após recuperar 2009 no FRE 25942. CSAN falha por distribuição zero em 2009; CAML falha por distribuição zero em 2016, provada no original FRE 72320 recebido em março/2018. BBSE não tem cinco exercícios completos no corte de 2017: 2012 é o período de constituição. [Resoluções e fontes](../research/returns_2014_2026_selection/continuation_selection_resolutions.json).

R03 B2: 13 posições finais; cinco maiores: CSMG3 35,9264%; UGPA3 8,5556%; SBSP3 7,1050%; FLRY3 6,9197%; POMO3 6,6822%. [Composição e unidades em cada junho](../research/returns_2014_2026_selection/r03_continuation_positions.csv) · [revisões B2/entradas](../research/returns_2014_2026_selection/r03_continuation_reviews.csv) · [decisões PASS/FAIL/INDETERMINATE](../research/returns_2014_2026_selection/r03_continuation_decisions.csv) · [livro de eventos](../research/returns_2014_2026_selection/r03_continuation_ledger.csv).

B00S B2: 22 posições finais; cinco maiores: PSSA3 20,2791%; CSMG3 16,0414%; BMGB4 7,3595%; BBSE3 6,9406%; SAPR4 6,3722%. [Composição e unidades em cada junho](../research/returns_2014_2026_selection/b00s_b2_continuation_positions.csv) · [revisões B2/entradas](../research/returns_2014_2026_selection/b00s_b2_continuation_reviews.csv) · [decisões PASS/FAIL/INDETERMINATE](../research/returns_2014_2026_selection/b00s_b2_continuation_decisions.csv) · [livro de eventos](../research/returns_2014_2026_selection/b00s_b2_continuation_ledger.csv).

B00S BH+entradas: 28 posições finais; cinco maiores: PSSA3 17,9685%; CSMG3 14,3760%; SBSP3 12,2131%; BBSE3 7,0417%; SAPR4 6,5596%. [Composição e unidades em cada junho](../research/returns_2014_2026_selection/b00s_bh_continuation_positions.csv) · [revisões B2/entradas](../research/returns_2014_2026_selection/b00s_bh_continuation_reviews.csv) · [decisões PASS/FAIL/INDETERMINATE](../research/returns_2014_2026_selection/b00s_bh_continuation_decisions.csv) · [livro de eventos](../research/returns_2014_2026_selection/b00s_bh_continuation_ledger.csv).

BH padrão permanece integralmente congelado: CCRO3/WEGE3, ITUB4/BBDC4, HYPE3/RADL3, TBLE3/CMIG4, 12,5% iniciais por nome, mantendo XPBR31. Preservadas as convenções de capitalização por classe e atividade farmacêutica predominante da Hypermarcas de 2014, assim como todas as ressalvas de direitos do [checkpoint aceito](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/blob/5cf7eb4/docs/checkpoint_returns_2014_2026_stage1.md). Não houve nova investigação nem replay de BH/IBOV.

**Eventos comuns e convenções do índice**

Fechamentos nominais COTAHIST têm arquivo, linha e hash de registro. Proventos brutos são reinvestidos no fechamento ex, com unidades fracionárias teóricas. Eventos simultâneos usam as unidades anteriores: `q nova = q antiga × (fator + provento/P ex)`. Os eventos bancários/XP de BH são reaproveitados sem modificar suas bases; dividendos PN não são copiados para ON. Ações de novos subscritores não viram bonificação dos titulares existentes.

GETI4→TIET11 representa a cesta herdada de 1 ON+4 PN; a unit vira 1 AESB3 em março/2021. AESB3→AURE3 usa a opção padrão de novembro/2024: 0,67498865568 ação mais 1,18438832610 por ação antiga, reinvestido teoricamente na sucessora na data ex. Mantêm-se frações; não se presume adesão voluntária a outra opção. ENBR não é vendida na OPA voluntária: o resgate compulsório de 24,23 em 13/09/2023 redistribui o componente do índice entre os demais ativos. NEOE recebe o mesmo tratamento no resgate compulsório de 34,02 em 15/05/2026. Os valores unitários são coeficientes do retorno, não capital investido. Não há saldo ocioso: conserva-se o direito até o evento de resgate, aplicando redistribuição proporcional na data de pagamento.

CPLE6→CPLE5 em novembro/2025 e depois CPLE3 em dezembro/2025 preserva unidades e incorpora o resgate de 0,7749 na sucessora. AXIA7 é uma posição distinta, destacada de ELET3/AXIA3 em 22/12/2025; não é aumento da quantidade ON. Incluídos split Guararapes ×8 em 2019, Copasa ×3 em 2020, Copel ×10 em 2021 e IRB ×3 em 2019/÷30 em 2023. Light 2021 combina grupamento e desdobramento de efeito líquido 1; o direito LIGT1 de maio/2026 e IRBR1 de julho/2020 são vendidos teoricamente ao primeiro fechamento negociado e convertidos no próprio ativo. [Base compartilhada de eventos](../research/returns_2014_2026_selection/continuation_events.csv) · [correções dirigidas e URLs](../research/returns_2014_2026_selection/continuation_event_resolutions.json).

**Sensibilidades e limites de interpretação**

As 128 combinações de entrada/não entrada dos sete candidatos/anos R03 indeterminados produzem acumulado final entre **374,6190% e 440,8770%**, contra **390,6934%** no caso central e **223,5469%** no IBOV. É a amplitude exaustiva dessas decisões de entrada, mantendo todos os demais dados e regras; não é intervalo de confiança nem limite de erros de eventos. Logo, a incerteza de seleção é material para o ranking, embora não impeça publicar a trajetória condicional. [128 cenários finais](../research/returns_2014_2026_selection/r03_selection_scenarios.csv) · [trajetórias anuais dos cenários](../research/returns_2014_2026_selection/r03_selection_scenario_paths.csv).

| Estratégia | Junho | Candidato | Tratamento |
|---|---|---|---|
| R03 | 2016 | BBDC3 | NO_NEW_ENTRY; INHERITED_POSITION_RETAINED |
| R03 | 2016 | ITUB3 | NO_NEW_ENTRY; INHERITED_POSITION_RETAINED |
| R03 | 2017 | BBDC3 | NO_NEW_ENTRY; INHERITED_POSITION_RETAINED |
| R03 | 2017 | ITUB3 | NO_NEW_ENTRY; INHERITED_POSITION_RETAINED |
| R03 | 2017 | SMTO3 | NO_NEW_ENTRY; INHERITED_POSITION_RETAINED |
| R03 | 2018 | BBDC3 | NO_NEW_ENTRY; INHERITED_POSITION_RETAINED |
| R03 | 2018 | ITUB3 | NO_NEW_ENTRY; INHERITED_POSITION_RETAINED |
| B00S | 2018 | IRBR3 | NO_NEW_ENTRY; INHERITED_POSITION_RETAINED |
| B00S | 2019 | BIDI4 | NO_NEW_ENTRY; INHERITED_POSITION_RETAINED |

BBDC3/ITUB3: o balanço consolidado não discrimina AC/PC de modo suficiente para F2. Não se substitui o banco por sua holding individual. SMTO3/2017: o prejuízo de 2009 exige comprovar a exceção de lucro e caixa; não foi inferida aprovação. IRBR3/2018: falta a evidência de 2013; sua inclusão hipotética está calculada abaixo. BIDI4/2019: 2015 foi recuperado no FRE 84003, recebido em maio/2019; 2014 continua sem prova. A entrada hipotética de BIDI4 solicitaria 3,3333% do índice na revisão de 2019; seu caminho completo não foi certificado. O caso central não compra BIDI4. Não se afirma que o efeito final dessa exclusão seja imaterial ou esteja limitado pelos cenários de IRB.

| Sensibilidade | Carteira | Acumulado final % | Δ final p.p. | Maior |Δ anual| p.p. |
|---|---|---|---|---|
| IRBR3_PASS_2018_UNPROVED_FY2013 | B00S B2 | 407,7023 | 5,5704 | 3,9964 |
| OMIT_DOCUMENTED_RIGHTS_AFTER_ACCEPTED_PREFIX | B00S B2 | 401,4350 | -0,6970 | 0,1146 |
| GETI_TIM_ROUNDING_-1 | B00S B2 | 402,1315 | -0,0005 | 0,0001 |
| GETI_TIM_ROUNDING_+1 | B00S B2 | 402,1325 | 0,0005 | 0,0001 |
| IRBR3_PASS_2018_UNPROVED_FY2013 | B00S BH+entradas | 389,7307 | 3,9889 | 3,9625 |
| OMIT_DOCUMENTED_RIGHTS_AFTER_ACCEPTED_PREFIX | B00S BH+entradas | 385,4736 | -0,2682 | 0,1177 |
| GETI_TIM_ROUNDING_-1 | B00S BH+entradas | 385,7414 | -0,0004 | 0,0001 |
| GETI_TIM_ROUNDING_+1 | B00S BH+entradas | 385,7422 | 0,0004 | 0,0001 |
| DIAGNOSTIC_FALSE_FAIL_NEW_CNPJ_OR_RENAMED_TICKER | B00S B2 | 416,7496 | 14,6176 | 2,6028 |
| OMIT_DOCUMENTED_RIGHTS_AFTER_ACCEPTED_PREFIX | R03 B2 | 390,4895 | -0,2039 | 0,0307 |

O diagnóstico de FAIL de linhagem mede a distorção de vender TIMS/AESB e ISAE pelo novo CNPJ/ticker; não é a política adotada. O teste sem direitos omite apenas os direitos documentados nesta continuação. **Não mede direitos ainda não reconciliados.** Permanecem fora do caso central direitos adicionais negociados de ABCB, AESB, BMGB, CSMG, ENBR, EQTL, TRPL e BBDC. Sua presença na cotação não é prova suficiente da quantidade de direitos atribuída a cada ação: não se inventou esse fator. Essa lacuna impede chamar os números de retorno total definitivamente auditado. As datas e exposições identificadas estão em [inventário de direitos pendentes](../research/returns_2014_2026_selection/continuation_unresolved_rights.csv).

GETI agosto/2015 usa transcrição histórica de quatro casas decimais; o ITR 51290 foi identificado, mas a recuperação foi interrompida pelo servidor. TIM 2016/2017 usa a tabela de RI já arquivada, também arredondada. O teste ±0,00005 por ação mede somente arredondamento, não certificação de fonte. Guararapes/CPFL têm data ex inferida do primeiro pregão após aprovação e conferida contra cotações; os fatores vêm dos FRE. Limitações herdadas do primeiro período B00S e do BH permanecem visíveis nos respectivos arquivos de evidência.

**Reprodução incremental offline**

```bash
python scripts/stage1_resume.py --freeze-events
python scripts/stage1_continuation_audit.py
python scripts/returns_stage1.py
python -m pytest -q tests/test_returns_stage1.py tests/test_stage1_pit.py tests/test_stage1_continuity.py tests/test_stage1_resume.py
python scripts/stage1_manifest.py
```

O replay lê as posições aceitas e os caches congelados; não baixa dados, não abre o SQLite nem refaz BH/IBOV. Os CSV de posições contêm unidades adimensionais e cotações usadas no cálculo; não são simulação de valores investidos. Validação local: **174 testes aprovados** (73 da etapa percentual e 101 das baselines); 4.140 linhas FRE conferidas nos arquivos originais e 12 hashes COTAHIST confirmados. Os hashes das entradas imutáveis são verificados antes/depois. Testes cobrem conservação nas revisões, preservação relativa de sobreviventes, sucessoras, direitos no mesmo pregão, eventos simultâneos, encadeamento independente e determinismo. [Registro de validação](../research/returns_2014_2026_results/validation.json) · [manifesto de entrega](../research/returns_2014_2026_results/delivery_manifest.json). Os testes demonstram correção da implementação sob os dados e hipóteses publicados; não eliminam as lacunas documentais.
