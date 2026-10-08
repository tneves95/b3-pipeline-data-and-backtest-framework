# Checkpoint — etapa 1 percentual, 2014–2026 — 08/10/2026

**Entrega parcial: a comparação completa das quatro carteiras ainda não foi calculada.** A série oficial do IBOV foi calculada nas 12 janelas; seleções históricas insuficientemente estabelecidas impedem atribuir retornos às quatro trajetórias desde 2014. ND significa não determinado, nunca retorno zero. Não há vencedor nem ranking de consistência das quatro carteiras neste checkpoint.

IBOV: **223,5469% acumulados**, **10,2795% a.a.**, 8 anos positivos e 4 negativos. Fechamentos: 2014-06-30 (53168.22 pontos) e 2026-06-30 (172024.12 pontos).

Escopo: [retificação do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/2#issuecomment-6059288518). Esta entrega usa apenas percentuais/pontos de índice. Não executa simulação nominal, fiscal, de caixa, aportes ou liquidação. A autorização para registrar bloqueios e resultados parciais está na própria retificação.

**Tabela 1 — retorno anual junho→junho (%)**

| Período | Início | Fim | R03 B2 | B00S B2 | B00S BH+entradas | BH padrão | IBOV |
|---|---|---|---|---|---|---|---|
| 2014–2015 | 2014-06-30 | 2015-06-30 | ND | ND | ND | ND | -0,1643 |
| 2015–2016 | 2015-06-30 | 2016-06-30 | ND | ND | ND | ND | -2,9275 |
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

Diferenças contra IBOV em p.p.: [matriz completa](../research/returns_2014_2026_results/annual_excess_pp.csv). As 48 diferenças das trajetórias pedidas são ND, pois os retornos das carteiras ainda não estão estabelecidos.

**Tabela 2 — retorno acumulado desde junho/2014 (%)**

| Até | R03 B2 | B00S B2 | B00S BH+entradas | BH padrão | IBOV |
|---|---|---|---|---|---|
| 2015-06-30 | ND | ND | ND | ND | -0,1643 |
| 2016-06-30 | ND | ND | ND | ND | -3,0870 |
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

Encadeamento: `100 × (produto(1 + retorno_anual_decimal) − 1)`. Índice inicial 1; qualquer intervalo ausente invalida o acumulado posterior. Não se reinicia a carteira em 2020.

**Tabela 3 — consolidado 2014–2026**

| Série | Acumulado % | CAGR % | Acima IBOV /12 | Pos./neg./zero | Média anual % | Mediana anual % | Melhor ano (%) | Pior ano (%) | Posição média / consistência |
|---|---|---|---|---|---|---|---|---|---|
| R03 B2 | ND | ND | ND | ND | ND | ND | ND | ND | ND / ND |
| B00S B2 | ND | ND | ND | ND | ND | ND | ND | ND | ND / ND |
| B00S BH+entradas | ND | ND | ND | ND | ND | ND | ND | ND | ND / ND |
| BH padrão | ND | ND | ND | ND | ND | ND | ND | ND | ND / ND |
| IBOV | 223,5469 | 10,2795 | N/A | 8/4/0 | 11,6161 | 13,8719 | 2018–2019 (38,7626) | 2021–2022 (-22,2865) | ND / ND |

CAGR usa dias efetivos/365,25. Ranking anual, posição média e consistência exigem as cinco séries comparáveis; não se atribui primeiro lugar ao único índice disponível. Quando houver cobertura completa, posição anual usa média dos postos empatados; consistência ordena a menor posição anual média, com empate preservado. As 12 janelas pertencem à mesma trajetória e não constituem 12 experimentos independentes.

**Segmentos herdados 2020–2026 — referências condicionais, fora das três tabelas primárias**

| Período | R03 legado % | B00S legado % | IBOV % | R03−IBOV p.p. | B00S−IBOV p.p. |
|---|---|---|---|---|---|
| 2020–2021 | 30,2454 | -1,6977 | 33,3971 | -3,1517 | -35,0948 |
| 2021–2022 | 9,2672 | 3,4824 | -22,2865 | 31,5537 | 25,7690 |
| 2022–2023 | 35,5623 | 31,3704 | 19,8342 | 15,7281 | 11,5361 |
| 2023–2024 | 10,4865 | 13,5131 | 4,9282 | 5,5583 | 8,5849 |
| 2024–2025 | 31,1693 | 37,0723 | 12,0640 | 19,1053 | 25,0084 |
| 2025–2026 | 30,6161 | 26,8307 | 23,8880 | 6,7281 | 2,9428 |

Esses percentuais reutilizam as seleções/retornos congelados v11.2 e v12+v13 e recalculam somente a comparação com IBOV oficial nas mesmas datas. Não são novas coortes, não reconstituem 2014 e não comprovam as seleções PIT da nova missão. A renovação anual com pesos fixados pode servir de referência ao B2 teórico, condicional à elegibilidade. B00S ainda combina eventos com aproximações de proventos; o legado contém exceções de continuidade e riscos de classe/normalização. Não promovemos esses números ao novo índice homogêneo. Nenhuma rotina fiscal ou de capital nominal foi executada; os arquivos de origem são apenas lidos.

[Nomes e pesos herdados](../research/returns_2014_2026_results/conditional_legacy_weights.csv) e [mudanças entre listas](../research/returns_2014_2026_results/conditional_legacy_membership_changes.csv) estão marcados como condicionais. A lista anterior a 2020 é desconhecida; trocas de ticker precisam de continuidade por emissor e não são automaticamente entradas/saídas econômicas. Seleção inicial/2014 e movimentos 2015–2019/BH+entradas/BH padrão permanecem não determinados.

**Cobertura, recuperação seletiva e limites**

O SQLite foi aberto em leitura somente; seu SHA-256 permaneceu idêntico antes/depois. Existem COTAHIST anuais 1994–2026, DFP desde 2010, mapeamentos PIT e eventos históricos. A presença dos arquivos não demonstra universo completo nem integridade de cada sucessão societária. `IBOV11` no banco é um ticker e não foi tratado como o índice IBOV. Foram coletadas 13 respostas anuais diretamente da B3, com URL, data e hash.

Há 970 registros de lucro comparativo de 2009 nas DFP 2010, dos quais 967 com recebimento até junho/2014; são registros por perímetro, não companhias únicas. Portanto, não se declarou 2009 inexistente. Na fotografia original do SQLite e comparativos, 233 de 284 classes cotadas examinadas em junho/2014 têm cobertura de lucro 2009–2013; 51 ficam indeterminadas, incluindo 25 sem identidade única no mapeamento usado. Essa triagem cobre tickers com quatro letras e finais 3–6, não um censo de todas as classes/units. Ter série de lucro não é passar nos filtros.

Entre 3776 versões DFP 2010–2013 com metadados conhecidos até o corte, 1205 não têm linhas da DRE individual dessa versão no ZIP local. Essa contagem inclui versões substituídas e não equivale ao número de lacunas indispensáveis. O arquivo de cobertura identifica ticker/exercício e as datas posteriores para distinguir faltas materiais.

A coleta seletiva recuperou os originais CVM 35587 (BB, DFP 2013), 24646 (Itaú, DFP 2012, com comparativos) e 39471 (WEG, FRE 2014); a CVM respondeu com arquivos ZIP. Os extratos/XML e hashes ficam na entrega. Foram extraídas 12 observações de lucro individual/consolidado nos XML originais, respeitando as contas específicas do plano bancário. Esses documentos permitem reparar parte das lacunas; a fotografia da cobertura original não inclui essa reparação e não deve ser lida como prova de indisponibilidade na CVM. A reconciliação integral desses originais com os filtros e demais emissores não foi concluída.

Capital: 524 de 573 linhas de capital emitido no FRE rotulado 2014 não satisfazem recebimento/aprovação até junho/2014. Arquivos anteriores contêm evidência admissível para 500 emissores, inclusive vários líderes; portanto, o ranking das oito maiores não é considerado impossível. Ele permanece não estabelecido: falta reconciliar capital vigente de todas as classes, identidades históricas, preços e taxonomia do universo comparável. Não usamos capital posterior nem escolhemos os maiores de hoje.

Pendências específicas: seleção R03 completa de 2014–2019 com filtros/triagem de perdas; universo BESST e recorrência de proventos conhecida em cada junho; predecessores/deslistados (por exemplo TBLE3, ALLL3 e BICB4 não resolvidos no mapeamento examinado); ranking por companhia de 2014; trajetórias de eventos homogêneas para as posições que essas seleções determinarem. Não são pendências de imposto, caixa ou financiamento.

**Convenções fixadas para a primeira etapa**

Índices de retorno total bruto, base 1 no último pregão de junho/2014, observados nos fechamentos oficiais de cada junho até 30/06/2026. Reinvestimento teórico integral dos proventos brutos no próprio ativo no fechamento da data-ex, incorporando conversões, desdobramentos e sucessoras uma única vez; preços nominais+eventos, ou série de retorno total validada, sem misturar dividendos adicionais com preços já ajustados. Nenhum saldo operacional é modelado. Os segmentos herdados acima não foram convertidos retroativamente a essa convenção uniforme.

B2: conjunto elegível de cada junho; pesos iguais R03 e iguais por setor/depois por emissor B00S. Ausência de prova permanece INDETERMINATE, não FAIL. BH B00S: união dos nomes detidos com novos elegíveis; quando houver entradas, redistribuição interna aos pesos B00S no conjunto ampliado, preservando o nível do índice; sem entradas, pesos oscilam sem rebalanceamento discricionário. Essa regra de retenção+adições não é BH passivo estrito. BH padrão: dois maiores emissores de 2014 por grupo, 12,5% cada, sem novas líderes. Capitalização agrega classes sem contar units em duplicidade; classe de investimento escolhida pela liquidez conhecida na formação. Nenhuma dessas regras autoriza inventar a seleção faltante.

Taxonomia: bens industriais (máquinas/equipamentos, material de transporte e serviços industriais); financeiro (bancos, seguros, intermediação e holdings de atividade financeira); utilidades públicas (energia, água/saneamento e gás canalizado); saúde (medicamentos, distribuição de medicamentos, serviços hospitalares, diagnósticos e operadoras de saúde). Holdings diversificadas exigem classificação econômica documentada. Bebidas, agricultura, joalheria e papel/celulose ficam fora desses quatro grupos.

Histórico: `max(2009, ano−10)..ano−1`, com 5/6/7/8/9/10 exercícios em 2014/15/16/17/18/19 e dez móveis depois. Para o requisito proporcional 8/10: `ceil(0,8 × n)` anos positivos, preservando demais restrições da regra. Filtros próprios de três/cinco anos e demais limites não são afrouxados.

**Reprodução e fontes**

```bash
python scripts/returns_stage1.py
python -m pytest -q tests/test_returns_stage1.py
# Apenas para repetir a auditoria no acervo local, sem o modificar:
python scripts/audit_stage1_coverage.py --data-root /caminho/do/acervo
```

O cálculo percentual e seus testes são offline. `scripts/fetch_ibov_stage1.py` refaz somente a coleta B3 e deve ser usado explicitamente, pois atualiza o snapshot. Manifestos e CSVs estão em [insumos](../research/returns_2014_2026_inputs/) e [resultados](../research/returns_2014_2026_results/). O workflow independente verifica reprodução offline. A branch parte de `fc62733`, sem alterar arquivos das baselines v11.2/v12/v13 ou do PR #2.

Validação local desta entrega: **18 testes da etapa percentual e 101 testes das baselines aprovados**. O replay percentual reproduziu os arquivos byte a byte. Esses testes verificam os cálculos e a preservação dos dados; não suprem as seleções históricas ainda não determinadas.

Fontes oficiais: [evolução diária IBOV/B3](https://sistemaswebb3-listados.b3.com.br/indexStatisticsPage/daily-evolution/IBOVESPA?language=pt-br), [metodologia B3 — índice de retorno total](https://www.b3.com.br/data/files/9C/15/76/F6/3F6947102255C247AC094EA8/IBOV-Metodologia-pt-br__Novo_.pdf), [DFP/CVM](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp).

**Estado final: checkpoint parcial publicado para revisão; pedido de quatro trajetórias completas ainda pendente. Não houve início da etapa fiscal/operacional, merge ou promoção de baseline.**
