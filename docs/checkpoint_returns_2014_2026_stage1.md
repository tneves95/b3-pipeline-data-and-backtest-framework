# Checkpoint — Barsi × Graham, etapa percentual 2014–2026 — 08/10/2026

**B2 corrigido; uma trajetória de 12 anos calculada (BH padrão); primeiro ano das duas variantes B00S calculado. O estudo das quatro trajetórias permanece parcial.** Continuação do commit `1ceab3f`, na mesma branch e no PR #3 draft, conforme a [última revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/3#issuecomment-6062365631). IBOV e referências legadas preservados. Nenhum motor de dinheiro, caixa, aportes, execução D+1 ou IR foi executado.

BH padrão: **331,6976%** acumulados, **12,9618%** a.a., acima do IBOV em **6/12** janelas. IBOV: **223,5469%**, CAGR **10,2795%**. São reconstruções brutas sob as convenções abaixo, com ressalvas explícitas de classes no ranking e de eventos. Não equivalem a uma certificação integral de todas as fontes.

R03 B2: -45,0683% em 2014–2015 e **3,5198%** em 2015–2016; acumulado **-43,1348%** até junho/2016, ante -3,0870% do IBOV. B00S inicial: **-1,0459%** nas duas variantes, ante -0,1643% do IBOV. B00S é exploratório: algumas provas de direitos dependem de transcrições e uma data de destacamento inferida; veja o inventário de evidências.

**Rentabilidade anual junho→junho (%)**

| Período | Início | Fim | R03 B2 | B00S B2 | B00S BH+entradas | BH padrão | IBOV |
|---|---|---|---|---|---|---|---|
| 2014–2015 | 2014-06-30 | 2015-06-30 | -45,0683 | -1,0459 | -1,0459 | 22,3021 | -0,1643 |
| 2015–2016 | 2015-06-30 | 2016-06-30 | 3,5198 | ND | ND | 11,8038 | -2,9275 |
| 2016–2017 | 2016-06-30 | 2017-06-30 | ND | ND | ND | 17,1925 | 22,0721 |
| 2017–2018 | 2017-06-30 | 2018-06-29 | ND | ND | ND | 1,8464 | 15,6797 |
| 2018–2019 | 2018-06-29 | 2019-06-28 | ND | ND | ND | 40,6323 | 38,7626 |
| 2019–2020 | 2019-06-28 | 2020-06-30 | ND | ND | ND | 18,9133 | -5,8548 |
| 2020–2021 | 2020-06-30 | 2021-06-30 | ND | ND | ND | 18,9660 | 33,3971 |
| 2021–2022 | 2021-06-30 | 2022-06-30 | ND | ND | ND | -11,5850 | -22,2865 |
| 2022–2023 | 2022-06-30 | 2023-06-30 | ND | ND | ND | 37,3725 | 19,8342 |
| 2023–2024 | 2023-06-30 | 2024-06-28 | ND | ND | ND | -2,6078 | 4,9282 |
| 2024–2025 | 2024-06-28 | 2025-06-30 | ND | ND | ND | -0,1868 | 12,0640 |
| 2025–2026 | 2025-06-30 | 2026-06-30 | ND | ND | ND | 12,6075 | 23,8880 |

ND significa não determinado; nunca zero. [Diferenças anuais contra IBOV, em p.p.](../research/returns_2014_2026_results/annual_excess_pp.csv).

**Rentabilidade acumulada desde junho/2014 (%)**

| Até | R03 B2 | B00S B2 | B00S BH+entradas | BH padrão | IBOV |
|---|---|---|---|---|---|
| 2015-06-30 | -45,0683 | -1,0459 | -1,0459 | 22,3021 | -0,1643 |
| 2016-06-30 | -43,1348 | ND | ND | 36,7384 | -3,0870 |
| 2017-06-30 | ND | ND | ND | 60,2471 | 18,3037 |
| 2018-06-29 | ND | ND | ND | 63,2059 | 36,8534 |
| 2019-06-28 | ND | ND | ND | 129,5202 | 89,9014 |
| 2020-06-30 | ND | ND | ND | 172,9300 | 78,7832 |
| 2021-06-30 | ND | ND | ND | 224,6939 | 138,4915 |
| 2022-06-30 | ND | ND | ND | 187,0781 | 85,3399 |
| 2023-06-30 | ND | ND | ND | 294,3665 | 122,1007 |
| 2024-06-28 | ND | ND | ND | 284,0822 | 133,0463 |
| 2025-06-30 | ND | ND | ND | 283,3649 | 161,1609 |
| 2026-06-30 | ND | ND | ND | 331,6976 | 223,5469 |

Encadeamento: `100 × (produto(1 + retorno_anual_decimal) − 1)`. Uma janela ausente interrompe todo acumulado posterior. As referências legadas de 2020 não completam nem reiniciam as carteiras formadas em 2014.

**Consolidado até junho/2026**

| Série | Janelas /12 | Acumulado % | CAGR % | Acima IBOV /12 | Anos + / − / = | Média anual % | Mediana anual % | Melhor período (%) | Pior período (%) |
|---|---|---|---|---|---|---|---|---|---|
| R03 B2 | 2 | ND | ND | ND | ND | ND | ND | ND | ND |
| B00S B2 | 1 | ND | ND | ND | ND | ND | ND | ND | ND |
| B00S BH+entradas | 1 | ND | ND | ND | ND | ND | ND | ND | ND |
| BH padrão | 12 | 331,6976 | 12,9618 | 6 | 9 / 3 / 0 | 13,9381 | 14,9000 | 2018–2019 (40,6323) | 2021–2022 (-11,5850) |
| IBOV | 12 | 223,5469 | 10,2795 | N/A | 8 / 4 / 0 | 11,6161 | 13,8719 | 2018–2019 (38,7626) | 2021–2022 (-22,2865) |

CAGR por dias efetivos/365,25. Ranking entre as quatro carteiras e posição média permanecem ND enquanto faltarem trajetórias comparáveis.

**B2: continuidade e renovação seletiva**

Na revisão de junho/2015, DIRR3, EZTC3 e HBOR3 carregam as participações vindas de 2014. CMIG3, JHSF3 e LPSB3 saem por FAIL. ALSC3, DTEX3, GRND3, GUAR3, HGTX3 e MILS3 entram. A regra operacional reserva aos entrantes sua fração-alvo da filosofia (seis vezes 1/9 nesta revisão), financiada primeiro pelas saídas FAIL; somente a insuficiência reduz proporcionalmente os sobreviventes. Se as saídas excederem a necessidade, o excedente se distribui aos entrantes na proporção-alvo. Sem entrantes, saídas se redistribuem proporcionalmente aos sobreviventes; sem entradas/saídas, nada muda. Ausência no screener ou INDETERMINATE não autoriza saída. A regra é comum às duas filosofias e não restabelece pesos iguais dos sobreviventes.

Índice antes/depois da revisão: `0.549316670513` / `0.549316670513`. [Livro da revisão](../research/returns_2014_2026_selection/b2_reviews.csv) e [pesos efetivos, retornos e contribuições](../research/returns_2014_2026_selection/established_segment_positions.csv). Os pesos de `established_selections.csv` são alvos da seleção, não pesos executados de B2. O resultado antigo **+1,9285%** foi preservado como [diagnóstico da seleção anual com pesos iguais](../research/returns_2014_2026_selection/annual_selection_diagnostic_pct.csv), separado da trajetória B2.

**Concentração inicial R03:** cinco das seis empresas são de construção/imobiliárias; as seis posições perderam entre aproximadamente 16,53% e 66,61%. A perda de 45,0683% é mantida como resultado exploratório. Não foi imposta diversificação retrospectiva.

**BH padrão: escolha em 2014 e continuidade**

| Bloco | Empresa/classe | Capitalização no corte (bilhões) | Peso inicial % |
|---|---|---|---|
| Bens industriais | CCRO3 | 31,7806 | 12,5000 |
| Bens industriais | WEGE3 | 22,8350 | 12,5000 |
| Financeiro | ITUB4 | 172,1948 | 12,5000 |
| Financeiro | BBDC4 | 135,2428 | 12,5000 |
| Saúde | HYPE3 | 12,1679 | 12,5000 |
| Saúde | RADL3 | 6,0262 | 12,5000 |
| Utilidades públicas | TBLE3 | 21,5405 | 12,5000 |
| Utilidades públicas | CMIG4 | 20,1831 | 12,5000 |

Capitalização serve somente à seleção; não representa dinheiro investido. Uma companhia aparece uma única vez; somam-se ON e PN. Capital/documento/recebimento e preços por classe estão no [ranking reproduzível](../research/returns_2014_2026_selection/bh_ranking_2014.csv). A classe mais líquida representa a companhia na carteira, com 12,5% inicial por companhia. Os oito líderes têm preços contemporâneos de suas classes relevantes. Para concorrentes sem negócio ON no corte, usa-se a última cotação anterior; para ON sem cotação observada, PN é uma aproximação explicitamente identificada. Duplicar o preço dessas ON no teste de sensibilidade não altera os oito nomes; isso não constitui limite matemático de avaliação. O ranking é condicionado a essas convenções, não uma capitalização exata inventada para classes não cotadas. Para Santander mantém-se o limite de exclusão após o grupamento 55:1 e a bonificação já documentados. A aproximação por classe PN agregada dos concorrentes com múltiplas preferenciais permanece indicada na base herdada.

Hypermarcas entra em saúde por atividade predominante conhecida no corte: o release de 21/02/2014 informa receita total de 4,2587 bilhões em 2013 e cerca de 2,3 bilhões em Farma (aproximadamente 54%). [Release original recuperado](../research/returns_2014_2026_selection/originals/hypera_2013_release.pdf.gz). Era um negócio misto; a classificação econômica por predominância não usa o perfil posterior da Hypera e difere da rubrica genérica Comércio do FCA. Bebidas, agricultura, joalheria e papel/celulose continuam fora dos quatro blocos.

Após a formação, não há recomposição anual de pesos. TBLE3→EGIE3 e CCRO3→MOTV3 são continuidades 1:1. As bonificações e desdobramentos alteram unidades do índice; a cisão Itaú/XPart gera XPBR31 (1/43,3128323 por ITUB4), mantida até 2026. O direito CMIG2 de 2017 é destacado e convertido no próprio ativo ao primeiro fechamento negociado, sem aporte. [Posições em cada junho](../research/returns_2014_2026_selection/bh_june_positions.csv), [retornos e contribuições anuais por companhia](../research/returns_2014_2026_selection/bh_issuer_annual_pct.csv), [eventos e fontes](../research/returns_2014_2026_selection/bh_owned_events.csv), [movimentações de unidades](../research/returns_2014_2026_selection/bh_event_ledger.csv).

Fechamentos nominais vêm diretamente dos COTAHIST locais, com linha/hash de registro e hash do arquivo. Proventos brutos são reinvestidos teoricamente no próprio ativo no fechamento da data-ex. Bonificação e distribuição simultâneas respeitam a posição anterior: `q_nova = q_antiga × (F + D/P_ex)`. As correções incluem bonificações antigas de WEG, Itaú, Bradesco, Cemig, Engie e Raia, o JCP Cemig dezembro/2014 integral e duas parcelas de JCP Bradesco na mesma data-com que a chave única do SQLite não preserva. Ações resultantes de ofertas públicas, opções a empregados e incorporação de outras companhias não viram bonificação do titular existente.

XP usa proventos brutos anunciados em USD, convertidos pela PTAX venda na data-ex e reinvestidos em XPBR31. É uma convenção de índice bruto em BRL, sem custos de depositário, retenções ou simulação da liquidação efetiva do BDR. O primeiro anúncio de 2023 informa valor arredondado de USD 0,58; a precisão publicada é mantida. [Mapa de fontes e convenções](../research/returns_2014_2026_selection/bh_evidence.json).

**B00S inicial: resultado efetivo e ressalvas**

Mantidos os 20 nomes e os pesos de 2014: cinco bancos a 4%, dez elétricas a 2%, CSMG3/SBSP3 a 10%, PSSA3 a 20%, TIMP3/VIVT4 a 10%. O primeiro período é comum às variantes B2 e BH+entradas. Foram incorporados os proventos CVM da AES Tietê, a ata TIM com valor/data-com exatos, o dividendo Light, a bonificação CPFL e os direitos ABCB2/TRPL2, além dos eventos bancários e Cemig compartilhados com BH. GETI4 permanece inteira até o fim desta janela; não foi antecipada a cadeia societária posterior.

[Evidências e pendências pontuais](../research/returns_2014_2026_selection/b00s_initial_evidence.json), [posições](../research/returns_2014_2026_selection/b00s_initial_positions.csv), [retornos e contribuições dos 20 nomes](../research/returns_2014_2026_selection/b00s_initial_contributions.csv), [eventos](../research/returns_2014_2026_selection/b00s_initial_events.csv) e [sensibilidade à omissão de direitos](../research/returns_2014_2026_selection/b00s_initial_sensitivity.csv). Datas-com GETI e os direitos ABCB têm corroboração histórica secundária; o destacamento TRPL é inferido. Essas limitações estão no status do resultado, não ocultas como eventos de valor zero.

**Seleções PIT e trabalho ainda necessário**

Preservadas as seleções fechadas R03 2014–2015 e B00S 2014–2016, os 1.306 fatos recuperados e os documentos CVM já publicados. A enumeração anual de nomes PASS não substitui os pesos herdados nem autoriza vender sucessoras por troca de ticker.

| Junho | R03 indeterminados | B00S indeterminados |
|---|---|---|
| 2016 | BBDC3, ITUB3, LINX3 | Nenhum |
| 2017 | BBDC3, CSAN3, ITUB3, SMTO3 | BBSE3 |
| 2018 | BBDC3, CAML3, CSAN3, ITUB3 | IRBR3 |
| 2019 | CAML3, CSAN3 | BIDI4, IRBR3 |

Próximas extensões: B00S 2015–2016 com GETI→TIET e renovação seletiva; resolver candidatos PIT 2016–2019 por impacto; depois aplicar as fontes congeladas 2020–2025 à trajetória contínua. Para BH+entradas, manter sucessoras e nomes que deixem de passar; a OPA voluntária ENBR do legado não comprova cash-out compulsório. As outras três trajetórias até 2026 continuam abertas.

**Referências legadas preservadas, fora das trajetórias primárias**

| Período | R03 legado % | B00S legado % | IBOV % |
|---|---|---|---|
| 2020–2021 | 30,2454 | -1,6977 | 33,3971 |
| 2021–2022 | 9,2672 | 3,4824 | -22,2865 |
| 2022–2023 | 35,5623 | 31,3704 | 19,8342 |
| 2023–2024 | 10,4865 | 13,5131 | 4,9282 |
| 2024–2025 | 31,1693 | 37,0723 | 12,0640 |
| 2025–2026 | 30,6161 | 26,8307 | 23,8880 |

**Reprodução offline**

```bash
python scripts/stage1_bh_selection.py
python scripts/stage1_segments.py
python scripts/stage1_buyhold.py
python scripts/stage1_b00s_initial.py
python scripts/returns_stage1.py
python -m pytest -q tests/test_returns_stage1.py tests/test_stage1_pit.py tests/test_stage1_continuity.py
```

Não é necessário refazer a seleção PIT, baixar fontes ou abrir o SQLite para reproduzir os resultados. As opções de coleta são separadas do replay. `stage1_manifest.py` registra os hashes de fontes e entregáveis. Testes verificam conservação nas revisões B2, ausência de giro indevido, direitos e sucessoras, reinvestimento sem dupla contagem, identidade do encadeamento, IBOV preservado e reprodução determinística. As baselines v11–v13 continuam protegidas por seus testes. Validação local: **160 testes aprovados**, 59 da etapa percentual/PIT/continuidade e 101 das baselines. [Registro de validação](../research/returns_2014_2026_results/validation.json). Os testes validam a implementação e os artefatos; não eliminam as ressalvas documentais expostas.
