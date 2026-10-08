# Checkpoint — atribuição anual realizada 2014–2026

Executada a [retificação prioritária do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/3#issuecomment-6066153641), de 08/10/2026. Base preservada: `cb3db599da85b4ad8bece1d93f1ad583a91ad713`. PR #3 permanece **draft, sem merge**.

**729 posições de início, 48 fechamentos de carteira e 48 conciliações decimais exatas**, de junho/2015 a junho/2026. O maior resíduo numérico explícito é **2,60 × 10⁻¹⁴ p.p.** Não foi alterado nenhum retorno anual, acumulado ou consolidado, nem o IBOV, as seleções ou os livros de eventos. Os 271 arquivos do estado aceito estão protegidos por SHA-256.

[Baixar Excel](../research/returns_2014_2026_results/attribution_2014_2026.xlsx) · [Todas as ações e contribuições](../research/returns_2014_2026_results/annual_holdings_attribution.csv) · [48 conciliações e destaques](../research/returns_2014_2026_results/annual_attribution_summary.csv)

## Leitura e método

Cada ciclo começa nas posições **após a revisão do junho inicial** e termina **antes da revisão do junho final**. A revisão do fechamento pertence ao ciclo seguinte. As saídas no fechamento continuam contribuindo para o ciclo encerrado. O BH padrão usa as posições existentes no início, sem rebalanceamento.

Para cada origem, `contribuição = 100 × (componente final − componente inicial) / índice inicial da carteira`. O retorno bruto da exposição é `100 × (componente final / componente inicial − 1)`. Os componentes e unidades são adimensionais; não há simulação monetária, caixa, IR ou aportes.

Foram reutilizadas literalmente as contribuições prontas de Graham/2014–2016, B00S/2014–2015 e do BH padrão. Para o BH, XPBR31 pertence à exposição ITUB4 no ciclo em que nasce; a partir de junho/2022, já é uma posição de início e recebe linha própria. Não há duplicação de XP entre as duas linhas.

Nas continuações, a atribuição lê os IDs dos eventos do livro existente. Cada origem acompanha seus direitos e sucessoras até o fechamento. A soma das unidades por origem é conferida em **cada data do livro** e no snapshot final `PERIOD_END`. Não são chamados screeners, seleção, renovação B2 ou rotinas de backtest pelo gerador.

**Resgates ENBR/NEOE:** o principal é transferido para uma fração da cesta sobrevivente, mantendo a origem resgatada. O desempenho posterior dessa fração fica na mesma origem até o fim do ciclo. Assim, o capital transferido não vira retorno das ações receptoras. O peso final da linha é o peso dos descendentes dessa origem, podendo representar vários papéis. No junho seguinte, a atribuição recomeça nas posições físicas então existentes.

[Transferências de resgates](../research/returns_2014_2026_results/attribution_redemption_transfers.csv) · [Unidades por origem e evento](../research/returns_2014_2026_results/attribution_event_lineage.csv) · [Descendentes no fechamento](../research/returns_2014_2026_results/attribution_end_lineage.csv)

As contribuições econômicas são preservadas sem ajuste individual. Uma linha `NUMERICAL_RESIDUAL`, sem ticker, peso ou retorno individual, explicita somente o ruído de ponto flutuante. Somadas com `Decimal`, todas as linhas conciliam exatamente com o decimal de `annual_returns_pct.csv`. O Excel apresenta valores numéricos, fórmulas com resultados armazenados e uma coluna textual com a contribuição decimal exata; seu limite de 15 algarismos significativos é documentado.

Os códigos seguem os aliases dos livros congelados, como TBLE3/EGIE3, DXCO3/DTEX3 e ELET3/AXIA3. As limitações históricas de PIT e proventos e as sensibilidades do [checkpoint anterior](checkpoint_returns_2014_2026_stage1.md) permanecem. A conciliação confirma a atribuição ao caso central aceito; não acrescenta certificação às fontes históricas.

## Primeiros fechamentos — todas as ações

Pesos e retornos individuais abaixo têm oito casas para leitura; contribuições e totais mantêm o decimal integral do CSV. As duas carteiras B00S têm as mesmas 20 posições e contribuições neste primeiro ciclo.

### Graham R03 B2 — junho/2014 a junho/2015

| Origem no início | Peso inicial (%) | Retorno bruto (%) | Contribuição (p.p.) | Peso final (%) |
|---|---|---|---|---|
| CMIG3 | 16.66666667 | -16.53167607 | -2.755279344750148 | 25.32489558 |
| DIRR3 | 16.66666667 | -54.00794492 | -9.001324152735933 | 13.95432348 |
| EZTC3 | 16.66666667 | -34.11692355 | -5.686153924250923 | 19.98940380 |
| HBOR3 | 16.66666667 | -66.61093522 | -11.101822536142617 | 10.13048471 |
| JHSF3 | 16.66666667 | -51.23544716 | -8.5392411926035 | 14.79551943 |
| LPSB3 | 16.66666667 | -47.90707079 | -7.984511798242054 | 15.80537299 |
| Resíduo numérico explícito | — | — | 5E-15 | — |
| **Total conciliado** | 100 | — | **-45.06833294872517** | 100 |

**IBOV: -0.16427106267616898%**; diferença da carteira: -44.90406188604900102 p.p.

### B00S B2 e B00S BH+entradas — junho/2014 a junho/2015

| Origem no início | Peso inicial (%) | Retorno bruto (%) | Contribuição (p.p.) | Peso final (%) |
|---|---|---|---|---|
| ABCB4 | 4.00000000 | -8.78818795 | -0.3515275181357226 | 3.68703339 |
| BBAS3 | 4.00000000 | 5.36907336 | 0.2147629343414205 | 4.25930900 |
| BBDC4 | 4.00000000 | 10.62853220 | 0.4251412880901917 | 4.47191085 |
| BRSR6 | 4.00000000 | -11.93643507 | -0.4774574027880382 | 3.55977255 |
| CMIG4 | 2.00000000 | -18.22824135 | -0.3645648269944405 | 1.65272018 |
| COCE5 | 2.00000000 | 20.88866998 | 0.4177733995223455 | 2.44332698 |
| CPFE3 | 2.00000000 | -0.27764574 | -0.005552914816609952 | 2.01552651 |
| CPLE6 | 2.00000000 | 10.63256347 | 0.21265126942930507 | 2.23603690 |
| CSMG3 | 10.00000000 | -65.77173990 | -6.577173990005318 | 3.45900205 |
| ENBR3 | 2.00000000 | 10.74306232 | 0.21486124643701027 | 2.23827024 |
| EQTL3 | 2.00000000 | 43.60057843 | 0.8720115686134247 | 2.90236602 |
| GETI4 | 2.00000000 | -2.75456566 | -0.05509131320539512 | 1.96546454 |
| ITUB4 | 4.00000000 | 11.31519222 | 0.45260768874196766 | 4.49966755 |
| LIGT3 | 2.00000000 | -17.43405473 | -0.3486810946196659 | 1.66877179 |
| PSSA3 | 20.00000000 | 36.01454067 | 7.202908133315466 | 27.49041719 |
| SBSP3 | 10.00000000 | -28.52304792 | -2.8523047919090883 | 7.22323960 |
| TBLE3 | 2.00000000 | 9.38495257 | 0.18769905136925003 | 2.21082097 |
| TIMP3 | 10.00000000 | -19.39467554 | -1.939467553568701 | 8.14572467 |
| TRPL4 | 2.00000000 | 50.56038454 | 1.0112076908507346 | 3.04303331 |
| VIVT4 | 10.00000000 | 7.14345201 | 0.7143452012423696 | 10.82758572 |
| Resíduo numérico explícito | — | — | 1.642E-15 | — |
| **Total conciliado** | 100 | — | **-1.0458519340894923** | 100 |

**IBOV: -0.16427106267616898%**; diferença da carteira: -0.88158087141332332 p.p.

### BH padrão — junho/2014 a junho/2015

| Origem no início | Peso inicial (%) | Retorno bruto (%) | Contribuição (p.p.) | Peso final (%) |
|---|---|---|---|---|
| BBDC4 | 12.50000000 | 10.62853220 | 1.3285665252818517 | 11.30689430 |
| CCRO3 | 12.50000000 | -13.17482792 | -1.6468534904980139 | 8.87404925 |
| CMIG4 | 12.50000000 | -18.22824135 | -2.2785301687152524 | 8.35756033 |
| HYPE3 | 12.50000000 | 17.55844156 | 2.194805194805194 | 12.01517228 |
| ITUB4 | 12.50000000 | 11.31519222 | 1.4143990273186495 | 11.37707504 |
| RADL3 | 12.50000000 | 123.21112679 | 15.401390848254138 | 22.81350541 |
| TBLE3 | 12.50000000 | 9.38495257 | 1.1731190710578099 | 11.17979307 |
| WEGE3 | 12.50000000 | 37.72143622 | 4.715179527555008 | 14.07595032 |
| Resíduo numérico explícito | — | — | -6.8E-15 | — |
| **Total conciliado** | 100 | — | **22.302076535059378** | 100 |

**IBOV: -0.16427106267616898%**; diferença da carteira: 22.46634759773554698 p.p.

## Revisão posterior: junho/2023 a junho/2024

Na B00S B2, **SBSP3**, vendida na revisão de junho/2024, permanece na atribuição do ano encerrado e contribui **+3,146001444859468 p.p.**. **BMGB4 e ELET3**, compradas nessa revisão, não aparecem como origens deste ciclo; passam a contribuir em junho/2024–junho/2025. **ENBR3**, resgatada durante o ciclo, permanece como origem de sua exposição redistribuída.

### B00S B2 — todas as posições do início

| Origem no início | Peso inicial (%) | Retorno bruto (%) | Contribuição (p.p.) | Peso final (%) |
|---|---|---|---|---|
| ABCB4 | 3.06986460 | 25.36418774 | 0.778646219896229 | 3.35515690 |
| AESB3 | 1.45164171 | -6.26634560 | -0.09096488624244754 | 1.18624695 |
| BBAS3 | 4.20768035 | 17.77301563 | 0.7478316856490294 | 4.32024780 |
| BBDC4 | 2.40334565 | -17.91282263 | -0.43050704274878926 | 1.71993360 |
| BBSE3 | 7.56378141 | 17.09345314 | 1.2929114307730245 | 7.72132274 |
| CMIG4 | 1.44500270 | 5.95297374 | 0.08602063139154381 | 1.33475615 |
| CPFE3 | 2.58151428 | 5.62113863 | 0.1451104962321527 | 2.37708931 |
| CPLE6 | 2.60548447 | 15.02445872 | 0.39145993909521154 | 2.61275574 |
| CSMG3 | 8.03968312 | 17.66327217 | 1.4200711116048463 | 8.24707561 |
| ENBR3 | 2.15153905 | 18.06884842 | 0.38875832942958877 | 2.21464787 |
| EQTL3 | 4.65127074 | -3.11883457 | -0.14506543969472968 | 3.92853925 |
| ITUB4 | 3.04324713 | 22.55341878 | 0.6863562688540036 | 3.25149263 |
| NEOE3 | 2.10464747 | -8.21387800 | -0.17287317562563828 | 1.68413346 |
| PSSA3 | 17.33022621 | 14.78145474 | 2.56165954366967 | 17.34187609 |
| SANB4 | 3.42553248 | -5.81739393 | -0.19927671826675072 | 2.81267087 |
| SAPR4 | 6.29871775 | 35.12938456 | 2.2127007819704323 | 7.42031034 |
| SBSP3 | 9.02842400 | 34.84552173 | 3.146001444859468 | 10.61374372 |
| TAEE4 | 2.08868736 | 0.74903713 | 0.015645043909264276 | 1.83457075 |
| TBLE3 | 1.84276625 | 2.44808505 | 0.045112484996704685 | 1.64586503 |
| TIMS3 | 4.48954956 | 16.37554067 | 0.7351880139418309 | 4.55496038 |
| TRPL4 | 4.38607217 | 12.09624276 | 0.5305499377642892 | 4.28634331 |
| VIVT3 | 5.53514105 | 10.46065852 | 0.5790122044768419 | 5.33035880 |
| XPBR31 | 0.25618050 | -7.80744279 | -0.0200011456830893 | 0.20590270 |
| Resíduo numérico explícito | — | — | -2.101E-15 | — |
| **Total conciliado** | 100 | — | **14.704347160252684** | 100 |

**IBOV: 4.928188538958578%**; diferença da carteira: 9.776158621294106 p.p.

Na Graham, a reentrada de **CMIG3** em junho/2024 também só contribui no ciclo seguinte: CMIG3 não é origem no fechamento de junho/2024. O mesmo vale para as novas entradas ALOS3, KLBN3, LREN3, PNVL3 e POMO3; ENAT3, SBSP3 e UNIP3 ainda contribuem no ciclo em que saem.

## Maiores contribuições em cada carteira e fechamento

O Excel sinaliza as três maiores positivas e as três maiores negativas de cada ciclo. A tabela abaixo mostra os extremos; sinal “—” significa que não houve contribuição com aquele sinal. O CSV e as abas mantêm todas as posições.

| Fechamento | Carteira | Maior positiva (p.p.) | Maior negativa (p.p.) | Total (%) | IBOV (%) |
|---|---|---|---|---|---|
| jun/2015 | R03 B2 | — | HBOR3: -11.101823 | -45.068333 | -0.164271 |
| jun/2015 | B00S B2 | PSSA3: +7.202908 | CSMG3: -6.577174 | -1.045852 | -0.164271 |
| jun/2015 | B00S BH+entradas | PSSA3: +7.202908 | CSMG3: -6.577174 | -1.045852 | -0.164271 |
| jun/2015 | BH padrão | RADL3: +15.401391 | CMIG4: -2.278530 | +22.302077 | -0.164271 |
| jun/2016 | R03 B2 | HGTX3: +3.345342 | MILS3: -4.049383 | +3.519818 | -2.927532 |
| jun/2016 | B00S B2 | SBSP3: +5.770780 | PSSA3: -9.248242 | +2.089175 | -2.927532 |
| jun/2016 | B00S BH+entradas | SBSP3: +5.629781 | PSSA3: -9.022277 | +2.162059 | -2.927532 |
| jun/2016 | BH padrão | RADL3: +13.541785 | WEGE3: -3.650415 | +11.803821 | -2.927532 |
| jun/2017 | R03 B2 | SEER3: +12.413589 | YDUQ3: -0.885168 | +33.728852 | +22.072055 |
| jun/2017 | B00S B2 | PSSA3: +3.887705 | CPLE6: -0.222245 | +22.668194 | +22.072055 |
| jun/2017 | B00S BH+entradas | PSSA3: +3.431527 | CPLE6: -0.196167 | +23.279912 | +22.072055 |
| jun/2017 | BH padrão | ITUB4: +4.195046 | TBLE3: -0.685339 | +17.192480 | +22.072055 |
| jun/2018 | R03 B2 | EZTC3: +2.903100 | — | +3.808099 | +15.679737 |
| jun/2018 | B00S B2 | PSSA3: +8.589903 | SBSP3: -2.926227 | +10.202186 | +15.679737 |
| jun/2018 | B00S BH+entradas | PSSA3: +7.393696 | SBSP3: -2.518728 | +8.611488 | +15.679737 |
| jun/2018 | BH padrão | WEGE3: +2.236592 | CCRO3: -3.206706 | +1.846367 | +15.679737 |
| jun/2019 | R03 B2 | SBSP3: +21.593523 | — | +66.312385 | +38.762649 |
| jun/2019 | B00S B2 | SBSP3: +8.045539 | TIMP3: -0.737459 | +51.627626 | +38.762649 |
| jun/2019 | B00S BH+entradas | SBSP3: +7.026563 | TIMP3: -0.644059 | +52.542982 | +38.762649 |
| jun/2019 | BH padrão | BBDC4: +9.014106 | — | +40.632303 | +38.762649 |
| jun/2020 | R03 B2 | VIVT3: +9.299980 | ENBR3: -0.737261 | +17.039783 | -5.854753 |
| jun/2020 | B00S B2 | SAPR4: +2.603894 | IRBR3: -4.420232 | -5.587908 | -5.854753 |
| jun/2020 | B00S BH+entradas | SAPR4: +2.626177 | IRBR3: -4.420232 | -5.836916 | -5.854753 |
| jun/2020 | BH padrão | WEGE3: +16.628381 | BBDC4: -5.405065 | +18.913311 | -5.854753 |
| jun/2021 | R03 B2 | SLCE3: +14.188608 | SBSP3: -5.546914 | +28.404180 | +33.397050 |
| jun/2021 | B00S B2 | PSSA3: +2.016546 | SBSP3: -4.194857 | -1.383317 | +33.397050 |
| jun/2021 | B00S BH+entradas | SANB4: +1.822174 | SBSP3: -3.773158 | -2.196488 | +33.397050 |
| jun/2021 | BH padrão | WEGE3: +8.207411 | CCRO3: -0.258995 | +18.965980 | +33.397050 |
| jun/2022 | R03 B2 | CPLE3: +3.295468 | CSMG3: -17.573512 | -12.973023 | -22.286546 |
| jun/2022 | B00S B2 | SBSP3: +1.280718 | PSSA3: -5.899260 | -3.552551 | -22.286546 |
| jun/2022 | B00S BH+entradas | BBSE3: +1.336543 | PSSA3: -5.471085 | -5.454575 | -22.286546 |
| jun/2022 | BH padrão | CMIG4: +1.321485 | RADL3: -6.019566 | -11.585000 | -22.286546 |
| jun/2023 | R03 B2 | CSMG3: +20.644960 | ENAT3: -1.477316 | +45.343478 | +19.834243 |
| jun/2023 | B00S B2 | PSSA3: +9.378053 | VIVT3: -0.169646 | +34.821690 | +19.834243 |
| jun/2023 | B00S BH+entradas | PSSA3: +8.872352 | VIVT3: -0.160498 | +35.630214 | +19.834243 |
| jun/2023 | BH padrão | RADL3: +15.427767 | — | +37.372535 | +19.834243 |
| jun/2024 | R03 B2 | CSMG3: +4.989802 | DXCO3: -3.370508 | +5.108317 | +4.928189 |
| jun/2024 | B00S B2 | SBSP3: +3.146001 | BBDC4: -0.430507 | +14.704347 | +4.928189 |
| jun/2024 | B00S BH+entradas | SBSP3: +2.958614 | BRSR6: -0.638113 | +12.882097 | +4.928189 |
| jun/2024 | BH padrão | WEGE3: +3.514883 | RADL3: -3.584854 | -2.607804 | +4.928189 |
| jun/2025 | R03 B2 | CSMG3: +9.079926 | DXCO3: -1.175294 | +27.841790 | +12.063971 |
| jun/2025 | B00S B2 | PSSA3: +16.108731 | BBAS3: -0.563604 | +37.477704 | +12.063971 |
| jun/2025 | B00S BH+entradas | PSSA3: +14.521066 | BBAS3: -0.508055 | +40.326362 | +12.063971 |
| jun/2025 | BH padrão | ITUB4: +3.561512 | RADL3: -10.563622 | -0.186757 | +12.063971 |
| jun/2026 | R03 B2 | CSMG3: +29.200547 | TRIS3: -0.669962 | +46.322440 | +23.887952 |
| jun/2026 | B00S B2 | CSMG3: +11.082882 | BBAS3: -0.229459 | +27.017332 | +23.887952 |
| jun/2026 | B00S BH+entradas | CSMG3: +9.837501 | BBAS3: -0.201373 | +25.754963 | +23.887952 |
| jun/2026 | BH padrão | WEGE3: +4.063035 | HYPE3: -1.249856 | +12.607506 | +23.887952 |

## Reprodução e validação

Execute na branch `study/returns-2014-2026-stage1`, a partir da raiz do checkout. O gerador é offline e usa exclusivamente os artefatos já versionados.

```bash
python -m pip install -r requirements-attribution.txt
python scripts/stage1_attribution.py
python -m pytest -q tests/test_stage1_attribution.py
```

Para gerar em outro diretório sem substituir a entrega: `python scripts/stage1_attribution.py --output-dir /tmp/attribution-check`. O arquivo Excel e os cinco CSVs têm reprodução byte a byte.

**137 testes aprovados: 64 de atribuição e 73 de regressão da etapa.** Os testes de atribuição cobrem os 48 somatórios exatos, todas as posições e pesos iniciais, saídas/entradas de fechamento, conservação de principal e desempenho após resgate, conversões, direitos no mesmo dia, cisões, conteúdo e fórmulas do Excel, proibição de executar seleções/backtests e preservação dos 271 arquivos. Os testes de regressão da etapa continuam no CI; há um job separado para a atribuição congelada.

[Manifesto da atribuição](../research/returns_2014_2026_results/attribution_manifest.json) · [Hashes da base preservada](../research/returns_2014_2026_inputs/attribution_frozen_inputs.json) · [Retificação arquivada](../research/returns_2014_2026_inputs/coordinator_attribution_2026_10_08.json)
