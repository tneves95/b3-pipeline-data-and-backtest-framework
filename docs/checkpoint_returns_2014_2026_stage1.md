# Checkpoint — etapa 1 percentual, 2014–2026 — continuação em 08/10/2026

**Avanço publicado: R03 B2 calculado de junho/2014 a junho/2016; o estudo completo das quatro carteiras ainda está pendente.** A continuação aproveita o checkpoint `0a6a20c`, os arquivos CVM/B3 e o SQLite em leitura somente. O IBOV e as referências legadas foram preservados. ND significa não determinado, nunca retorno zero.

R03 B2: **-45,0683% em 2014–2015**, **1,9285% em 2015–2016**, **-44,0090% acumulados até junho/2016**. IBOV nas mesmas duas janelas: -0,1643% e -2,9275%; acumulado -3,0870%. IBOV completo até junho/2026: **223,5469%**. Não há vencedor de 2014–2026 enquanto faltarem as trajetórias completas.

Escopo: [retificação do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/2#issuecomment-6059288518). Somente índices teóricos e rentabilidades percentuais brutas; nenhuma simulação de patrimônio nominal, caixa, aportes ou impostos.

**Tabela 1 — retorno anual junho→junho (%)**

| Período | Início | Fim | R03 B2 | B00S B2 | B00S BH+entradas | BH padrão | IBOV |
|---|---|---|---|---|---|---|---|
| 2014–2015 | 2014-06-30 | 2015-06-30 | -45,0683 | ND | ND | ND | -0,1643 |
| 2015–2016 | 2015-06-30 | 2016-06-30 | 1,9285 | ND | ND | ND | -2,9275 |
| 2016–2017 | 2016-06-30 | 2017-06-30 | ND | ND | ND | ND | 22,0721 |
| 2017–2018 | 2017-06-30 | 2018-06-29 | ND | ND | ND | ND | 15,6797 |
| 2018–2019 | 2018-06-29 | 2019-06-28 | ND | ND | ND | ND | 38,7626 |
| 2019–2020 | 2019-06-28 | 2020-06-30 | ND | ND | ND | ND | -5,8548 |
| 2020–2021 | 2020-06-30 | 2021-06-30 | ND | ND | ND | ND | 33,3971 |
| 2021–2022 | 2021-06-30 | 2022-06-30 | ND | ND | ND | ND | -22,2865 |
| 2022–2023 | 2022-06-30 | 2023-06-30 | ND | ND | ND | ND | 19,8342 |
| 2023–2024 | 2023-06-30 | 2024-06-28 | ND | ND | ND | ND | 4,9282 |
| 2024–2025 | 2024-06-28 | 2025-06-30 | ND | ND | ND | ND | 12,0640 |
| 2025–2026 | 2025-06-30 | 2026-06-30 | ND | ND | ND | ND | 23,8880 |

[Diferenças anuais contra IBOV, em p.p.](../research/returns_2014_2026_results/annual_excess_pp.csv). R03: -44,9041 p.p. e 4,8560 p.p. nas duas janelas calculadas.

**Tabela 2 — retorno acumulado desde junho/2014 (%)**

| Até | R03 B2 | B00S B2 | B00S BH+entradas | BH padrão | IBOV |
|---|---|---|---|---|---|
| 2015-06-30 | -45,0683 | ND | ND | ND | -0,1643 |
| 2016-06-30 | -44,0090 | ND | ND | ND | -3,0870 |
| 2017-06-30 | ND | ND | ND | ND | 18,3037 |
| 2018-06-29 | ND | ND | ND | ND | 36,8534 |
| 2019-06-28 | ND | ND | ND | ND | 89,9014 |
| 2020-06-30 | ND | ND | ND | ND | 78,7832 |
| 2021-06-30 | ND | ND | ND | ND | 138,4915 |
| 2022-06-30 | ND | ND | ND | ND | 85,3399 |
| 2023-06-30 | ND | ND | ND | ND | 122,1007 |
| 2024-06-28 | ND | ND | ND | ND | 133,0463 |
| 2025-06-30 | ND | ND | ND | ND | 161,1609 |
| 2026-06-30 | ND | ND | ND | ND | 223,5469 |

Encadeamento: `100 × (produto(1 + retorno_anual_decimal) − 1)`, índice inicial 1. A ausência de 2016–2017 impede o acumulado posterior do R03; os segmentos legados não reiniciam a trajetória em 2020.

**Tabela 3 — consolidado 2014–2026**

| Série | Janelas calculadas /12 | Acumulado % | CAGR % | Acima IBOV /12 | Pos./neg./zero | Média anual % | Mediana anual % | Melhor ano (%) | Pior ano (%) | Posição média / consistência |
|---|---|---|---|---|---|---|---|---|---|---|
| R03 B2 | 2 | ND | ND | ND | ND | ND | ND | ND | ND | ND / ND |
| B00S B2 | 0 | ND | ND | ND | ND | ND | ND | ND | ND | ND / ND |
| B00S BH+entradas | 0 | ND | ND | ND | ND | ND | ND | ND | ND | ND / ND |
| BH padrão | 0 | ND | ND | ND | ND | ND | ND | ND | ND | ND / ND |
| IBOV | 12 | 223,5469 | 10,2795 | N/A | 8/4/0 | 11,6161 | 13,8719 | 2018–2019 (38,7626) | 2021–2022 (-22,2865) | ND / ND |

CAGR usa dias efetivos/365,25. Estatísticas finais e ranking exigem as 12 janelas comparáveis. Nas duas janelas R03 calculadas houve um ano positivo, um negativo e um acima do IBOV; isso não representa frequência em 12 anos.

**Seleções históricas resolvidas nesta continuação**

No universo de classes ON/PN efetivamente negociadas, com os filtros de liquidez originais, R03/2014–2015 e B00S/2014–2016 não têm candidatos INDETERMINATE. As listas abaixo separam os PASS demonstrados dos candidatos ainda indeterminados; somente as cinco seleções fechadas foram exportadas como estabelecidas. As seleções legadas de 2020–2025 permanecem preservadas e condicionais.

| Junho | R03: PASS | R03: indeterminados | B00S: PASS | B00S: indeterminados |
|---|---|---|---|---|
| 2014 | CMIG3, DIRR3, EZTC3, HBOR3, JHSF3, LPSB3 | Nenhum no universo examinado | ABCB4, BBAS3, BBDC4, BRSR6, CMIG4, COCE5, CPFE3, CPLE6, CSMG3, ENBR3, EQTL3, GETI4, ITUB4, LIGT3, PSSA3, SBSP3, TBLE3, TIMP3, TRPL4, VIVT4 | Nenhum no universo examinado |
| 2015 | ALSC3, DIRR3, DTEX3, EZTC3, GRND3, GUAR3, HBOR3, HGTX3, MILS3 | Nenhum no universo examinado | ABCB4, BBAS3, BBDC4, BRSR6, CMIG4, CPFE3, CPLE6, CSMG3, ENBR3, EQTL3, GETI4, ITUB4, LIGT3, PSSA3, SBSP3, TBLE3, TIMP3, TRPL4, VIVT4 | Nenhum no universo examinado |
| 2016 | ENBR3, ESTC3, EZTC3, GRND3, HGTX3, SEER3, TIMP3 | BBDC3, ITUB3, LINX3 | ABCB4, BBAS3, BBDC4, BRSR6, CMIG4, CPFE3, CPLE6, ENBR3, EQTL3, ITUB4, LIGT3, PSSA3, SBSP3, TBLE3, TIMP3, TRPL4, VIVT4 | Nenhum no universo examinado |
| 2017 | ENBR3, EZTC3 | BBDC3, CSAN3, ITUB3, SMTO3 | ABCB4, BBAS3, BBDC4, BRSR6, CMIG4, CPFE3, CPLE6, EGIE3, ENBR3, EQTL3, ITUB4, PSSA3, SAPR4, SBSP3, TIMP3, TRPL4, VIVT4 | BBSE3 |
| 2018 | ENBR3, EZTC3, GUAR3, SBSP3, SEER3 | BBDC3, CAML3, CSAN3, ITUB3 | ABCB4, BBAS3, BBDC4, BBSE3, BRSR6, CMIG4, CPFE3, CPLE6, EGIE3, ENBR3, EQTL3, ITUB4, PSSA3, SAPR4, SBSP3, TIMP3, TRPL4, VIVT4 | IRBR3 |
| 2019 | ENBR3, GUAR3, SBSP3, VIVT3 | CAML3, CSAN3 | ABCB4, BBAS3, BBDC4, BBSE3, BRSR6, CMIG4, CPFE3, CPLE6, EGIE3, ENBR3, EQTL3, ITUB4, PSSA3, SAPR4, SBSP3, TIMP3, TRPL4, VIVT4 | BIDI4, IRBR3 |

**Seleção inicial e pesos de junho/2014**

| Filosofia | Ação | Setor | Peso % |
|---|---|---|---|
| R03 | CMIG3 | Energia Elétrica | 16,6667 |
| R03 | DIRR3 | Construção Civil, Mat. Constr. e Decoração | 16,6667 |
| R03 | EZTC3 | Construção Civil, Mat. Constr. e Decoração | 16,6667 |
| R03 | HBOR3 | Construção Civil, Mat. Constr. e Decoração | 16,6667 |
| R03 | JHSF3 | Emp. Adm. Part. - Const. Civil, Mat. Const. e Decoração | 16,6667 |
| R03 | LPSB3 | Emp. Adm. Part. - Const. Civil, Mat. Const. e Decoração | 16,6667 |
| B00S | ABCB4 | Bancos | 4,0000 |
| B00S | BBAS3 | Bancos | 4,0000 |
| B00S | BBDC4 | Bancos | 4,0000 |
| B00S | BRSR6 | Bancos | 4,0000 |
| B00S | CMIG4 | Energia | 2,0000 |
| B00S | COCE5 | Energia | 2,0000 |
| B00S | CPFE3 | Energia | 2,0000 |
| B00S | CPLE6 | Energia | 2,0000 |
| B00S | CSMG3 | Saneamento | 10,0000 |
| B00S | ENBR3 | Energia | 2,0000 |
| B00S | EQTL3 | Energia | 2,0000 |
| B00S | GETI4 | Energia | 2,0000 |
| B00S | ITUB4 | Bancos | 4,0000 |
| B00S | LIGT3 | Energia | 2,0000 |
| B00S | PSSA3 | Seguros | 20,0000 |
| B00S | SBSP3 | Saneamento | 10,0000 |
| B00S | TBLE3 | Energia | 2,0000 |
| B00S | TIMP3 | Telecom | 10,0000 |
| B00S | TRPL4 | Energia | 2,0000 |
| B00S | VIVT4 | Telecom | 10,0000 |

R03 começa com seis ações em pesos iguais. B00S começa com vinte ações, 20% por setor BESST e pesos iguais dentro de cada setor. Esse mesmo conjunto inicial se aplica ao B00S B2 e ao B00S BH+entradas. Em junho/2015, R03 conserva DIRR3, EZTC3 e HBOR3; retira CMIG3, JHSF3 e LPSB3; acrescenta ALSC3, DTEX3, GRND3, GUAR3, HGTX3 e MILS3, com nove pesos iguais. [Pesos das seleções fechadas](../research/returns_2014_2026_selection/established_selections.csv), [triagem integral](../research/returns_2014_2026_selection/screening.csv) e [retornos e contribuições por posição](../research/returns_2014_2026_selection/established_segment_positions.csv).

**Proveniência PIT e reparações materiais**

Foram incorporados os originais de BB e Itaú já recuperados e 17 originais CVM adicionais, dos quais se extraíram 1.306 fatos contábeis. Entre os reparos: Copel/2013, Equatorial/2015–2016, Cemig/2015, Light/2015, Engie/2022 e Brasil Pharma/2013. Recebimento, versão, conta, perímetro, exercício, documento e hash acompanham os extratos. O arquivo de Engie usa o XML moderno da CVM; os demais usam o original ENET. FCA e FRE anteriores aos cortes complementam identidade, atividade econômica, capital emitido/integralizado e tesouraria.

O código distingue a conta de lucro das reversões de JCP de bancos e distingue ativo circulante de caixa pelo nome da conta. Colunas comparativas de resultado inteiramente zeradas no ENET permanecem ausentes; não viram prova de prejuízo nem de lucro. O lucro individual publicado pode suprir uma DRE consolidada vazia, com seu perímetro identificado. A falta de um exercício não encobre uma reprovação demonstrável em outro: Brasil Pharma/2013 tem prejuízo publicado e reprova o requisito dos últimos três anos positivos. A constituição de uma companhia depois do primeiro exercício exigido é registrada como histórico insuficiente demonstrado, sem inventar dados de predecessoras.

Para R03, história `max(2009, ano−10)..ano−1`, proporção `ceil(0,8 × n)`, demais restrições de perdas preservadas, e crescimento entre médias de três exercícios. F4 mantém a hierarquia herdada: B3/DFC individual, com DMPL/DVA individual como evidência mais fraca, sem reduzir a exigência de recorrência. F6 usa capital conhecido no corte e distingue o teste com capital bruto da dedução de tesouraria documentada. B00S conserva cinco exercícios e a taxonomia BESST estrita: corretoras, administradoras de benefícios e distribuição de gás não são promovidas a seguradoras ou saneamento.

**Convenção de retorno e cobertura restante**

Fechamento do último pregão de junho em todas as séries; reinvestimento teórico integral de cada distribuição bruta no próprio ativo no fechamento da data-ex. Os dois segmentos novos usam preços nominais e eventos, sem preços ajustados somados novamente a dividendos. Datas-com B3 são convertidas ao pregão seguinte do calendário observado. Não há saldos operacionais. A Cemig tinha somente metade do JCP de dezembro/2014 no SQLite; o aviso oficial confirma duas parcelas de 50%, e o valor integral foi restaurado uma única vez. Histórias B3 sob os ISIN atuais de Dexco e Riachuelo foram associadas aos nomes históricos DTEX3 e GUAR3 pelo mesmo emissor/classe. Os valores são uma reconstrução com as fontes disponíveis, não certificação de completude universal de eventos.

O retorno B00S ainda depende de eventos que não podem ser substituídos por zero: bonificações bancárias históricas, GETI→TIET→AESB→AURE, cisão Itaú/XPart e término de ENBR. Para BH+entradas é necessário manter as sucessoras e os nomes reprovados, com redistribuição interna de pesos somente quando houver novos elegíveis. A OPA voluntária de ENBR usada no legado não comprova sozinha um cash-out compulsório para BH.

O ranking BH padrão avançou para o cruzamento de capital, preços de todas as classes e atividade conhecida em 2014. Os líderes candidatos são CCRO/WEG, Itaú/Bradesco, Tractebel/Cemig e Hypermarcas/Raia Drogasil, mas o ranking ainda requer reconciliação de eventos de capital e classes. O Santander foi retirado do ranking nominal incorreto: o FRE trazia capital anterior ao grupamento 55:1 de junho/2014; um limite superior após a bonificação/grupamento o coloca abaixo dos dois líderes financeiros. Isso é um limite de exclusão documentado, não uma capitalização exata inventada. Hypermarcas é uma candidata de atividade mista, a justificar economicamente no corte; não se usa o perfil atual da Hypera. [Mapa de capitalização e ressalvas](../research/returns_2014_2026_selection/market_cap_2014.csv). As oito ações ainda não foram promovidas a uma carteira BH calculada.

Bebidas, agricultura, joalheria e papel/celulose ficam fora dos quatro grupos. Dados indeterminados continuam explícitos; não há retorno calculado de uma carteira formada pela simples exclusão silenciosa desses candidatos.

**Referências legadas 2020–2026, preservadas e fora da trajetória primária**

| Período | R03 legado % | B00S legado % | IBOV % | R03−IBOV p.p. | B00S−IBOV p.p. |
|---|---|---|---|---|---|
| 2020–2021 | 30,2454 | -1,6977 | 33,3971 | -3,1517 | -35,0948 |
| 2021–2022 | 9,2672 | 3,4824 | -22,2865 | 31,5537 | 25,7690 |
| 2022–2023 | 35,5623 | 31,3704 | 19,8342 | 15,7281 | 11,5361 |
| 2023–2024 | 10,4865 | 13,5131 | 4,9282 | 5,5583 | 8,5849 |
| 2024–2025 | 31,1693 | 37,0723 | 12,0640 | 19,1053 | 25,0084 |
| 2025–2026 | 30,6161 | 26,8307 | 23,8880 | 6,7281 | 2,9428 |

São os mesmos números condicionais do checkpoint anterior, oriundos das baselines v11.2/v12/v13. Não cobrem 2016–2020 nem substituem eventos e seleções da nova trajetória. Nenhum motor fiscal foi executado.

**Reprodução e preservação**

```bash
python scripts/stage1_select.py
python scripts/stage1_segments.py
python scripts/returns_stage1.py
python -m pytest -q tests/test_returns_stage1.py tests/test_stage1_pit.py
```

A reprodução usa os caches incluídos e não precisa de rede nem do SQLite. Os scripts `stage1_pit.py`, `stage1_supplement.py`, `stage1_capital.py` e `stage1_recover.py` servem à coleta incremental, não precisam ser repetidos para continuar. Os originais, hashes e pendências estão em [seleção PIT](../research/returns_2014_2026_selection/). A série IBOV e seus 13 arquivos B3 permanecem idênticos ao checkpoint inicial. A branch e o PR #3 continuam os mesmos; baselines e PR #2 preservados.

Validação local: **137 testes aprovados** (36 da etapa percentual/PIT e 101 das baselines). **54 cotações exatas** de fronteira/reinvestimento conferidas diretamente nos registros COTAHIST de 2014–2016, com arquivo, linha e hash. O replay dos resultados é offline e determinístico. Os testes verificam as invariantes e os segmentos entregues; não certificam as trajetórias ainda ausentes.

**Próxima prioridade:** resolver os candidatos de 2016–2019 listados acima e as continuidades materiais dos vinte nomes B00S iniciais; concluir o ranking de 2014 e então preencher as demais janelas. O pedido de quatro trajetórias completas permanece aberto.
