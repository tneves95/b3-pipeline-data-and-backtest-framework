# PR #5 — lote 3: cinco trajetórias, sensibilidades e publicação

Foram concluídas as cinco reconstruções monetárias até 30/06/2026, com 144 aportes por carteira e benchmark nas mesmas datas. Cada investidor aplicou R$ 460.000. O protocolo e as seleções/eventos congelados continuam inalterados. Não há renovação em junho/2026, imposto, custo, aporte adicional ou merge.

| Carteira | Patrimônio final | TIR anual | TWR acumulado |
|---|---:|---:|---:|
| VVAL | R$ 1.868.050,85 | 17,9403% | ND |
| V0 | R$ 1.645.952,98 | 16,3675% | ND |
| B00S-10 | R$ 1.656.388,43 | 16,4461% | 427,5029% |
| BH padrão | R$ 1.270.936,41 | 13,1438% | 373,6694% |
| BESST-10 BH condicional | R$ 1.767.443,92 | 17,2527% | 459,5005% |
| IBOV com aportes | R$ 1.051.091,04 | 10,7592% | 223,5469% |

O resultado é qualificado: TWR integral V0/VVAL permanece ND nas datas históricas sem preço/valor comprovado antes do aporte. São três períodos anuais com TWR ND: V0 2014–2015 e 2023–2024; VVAL 2023–2024. Os demais 69 retornos anuais, incluindo benchmark, são publicados. Patrimônio e TIR dessas duas carteiras são calculáveis: o dinheiro fica em caixa quando não é possível marcar integralmente a carteira, reaplicando no aporte seguinte. O principal de resgate EDP só entra em sua data aceita. Não se antecipou o comunicado de 05/09 para a marcação de 01/09.

O BESST permanece condicional à falta de preço ON contemporâneo da NET e às ressalvas documentais do inventário; sua alternativa NET em lugar de TIM é ND por ausência de trajetória compulsória certificada no livro herdado. Há números para a lista explicitamente congelada, sem apresentá-la como ranking integralmente certificado. Os valores de proventos reutilizados conservam a qualificação original.

**Sensibilidades:** exclusão de BBDC4 somente em 2014, seguida da admissão permitida pelo PASS de junho/2015, produz R$ 1.855.145,26 e TIR 17,8542%: −R$ 12.905,59 / −0,0861 ponto percentual ante a VVAL principal. V0 sem preservação de vencedoras produz R$ 1.665.625,96 e TIR 16,5152%: +R$ 19.672,98. Esses cenários têm livros completos separados e não alteram o caso principal. O gate VVAL mensal estrito fica ND por falta de atualização documental mensal certificada.

**Artefatos:** CSVs auditáveis, evolução mensal, pesos de linhagens e classes, concentração por emissor/setor, operações, revisão de junho, eventos internos, atribuição do ganho em reais por origem, sensibilidades e planilha de 17 abas com gráfico. `contributions_ledger.csv` tem 720 depósitos das cinco carteiras; o livro IBOV tem 144. Atribuição reconcilia integralmente o ganho final menos capital externo e caixa. Os totais de vendas/compras/giro em `june_reviews.csv` são informações do corte repetidas nas linhas por origem; para agregar, usar uma linha por carteira/data ou o livro de operações. O consolidado já soma os cortes uma única vez.

**Validação:** 32 testes novos passaram; 222 testes de regressão dos motores antigos passaram. O BH sem aportes reproduz o motor anterior nos 13 fechamentos de junho. Os três controles publicados no lote 2 mantêm exatamente patrimônio, TIR/TWR, concentração, giro e quantidade de eventos. Os 3.567 arquivos protegidos do baseline PR #4/auditoria/PR #3 conservam seus SHA-256. As cópias originais dos PRs #3 e #4 seguem com árvores de trabalho sem alteração de arquivos rastreados. A planilha foi reaberta e conferida: 720 linhas de depósitos principais e 144 do benchmark, com ND como células vazias.

Não se alterou a tolerância de vencedoras depois de observar o cenário alternativo. O cálculo de retorno da companhia usado nessa tolerância exclui financiamento recebido do resgate de outra origem; essa conferência da atribuição não alterou nenhuma preservação ou patrimônio do controle publicado. O ranking prévio tem trava de hashes e não é reeleito ao executar novamente a preparação.

O relatório principal é `docs/estudo_aportes_mensais_cinco_carteiras.md`. O PR #5 permanece draft, sem merge. As pendências são documentais e de marcação, explicitamente isoladas nos campos ND; não foram preenchidas por estimativa.
