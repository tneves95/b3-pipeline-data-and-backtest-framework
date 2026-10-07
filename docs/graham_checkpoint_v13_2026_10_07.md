# Checkpoint v13 — diagnóstico estratégico Barsi × Graham

Missão [v13](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/1#issuecomment-6047655887), subordinada à [retificação de prioridades](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/1#issuecomment-6047700161). Execução local, formação em junho de 2020–2025, término em 30/06/2026. **Baseline v11.2 provisória preservada; v12 integralmente preservada. V13 é checkpoint alternativo, sem promoção de baseline ou certificação integral.**

R03 e B00S apresentam os resultados mais estáveis entre as regras comparadas, sem vencedor universal. No cenário central, ambas superam BOVA11 nas seis formações e nos dois mecanismos. R00 também lidera duas janelas em cada mecanismo, mas perde do benchmark em 2025. As lideranças B00S na renovação de 2022 e 2024 dependem da composição: desaparecem no cenário conservador. A evidência sustenta conclusões descritivas sobre estas carteiras congeladas; não prova superioridade universal de Graham ou Barsi.

A auditoria dirigida termina nesta rodada. Os 12 pares Graham, quatro divergências residuais B3, avisos ALOS/UNIP e refinamentos de centavos permanecem registrados no v12. Não houve nova investigação desses itens. O diagnóstico de seleção abaixo delimita um risco estrutural, sem alterar carteiras retrospectivamente.

## O que foi efetivamente calculado

Foram reconstruídos **38 percursos únicos**, equivalentes a **216 posições/cenários** das 1.212 linhas Barsi: PSSA3, TIMP3→TIMS3, VIVT4→VIVT3 e SAPR4. O catálogo dirigido contém **129 parcelas de caixa e cinco eventos estruturais**. Há 768 resultados de coorte Barsi (6 formações × 4 regras × 2 composições × 2 mecanismos × 8 experimentos), 228 sensibilidades individuais e 576 sensibilidades de carteira. As 250 cotações de eventos/fronteiras coincidem em preço nominal e ISIN com o COTAHIST local. Isso é conciliação com o arquivo B3 preservado, não segunda coleta independente.

O motor v6 permanece byte a byte idêntico (`56672b78…051d11`). Foram mantidos capital inicial R$ 10.000, ausência de aportes, custos e impostos, frações teóricas, caixa bruto reinvestido ao fechamento da data-ex e seleções/pesos originais. Na renovação, o patrimônio resultante financia a próxima carteira. Proventos com pagamento posterior ao corte podem estar reconhecidos/reinvestidos antes dele: **índice teórico por direitos, não trajetória operacional de dinheiro disponível**. A política de venda/liquidação/reinvestimento dos direitos ITSA3 continua exatamente a v11.2.

As alternativas são `v9`, `v12_partial`, quatro substituições isoladas, `v13_four` e `v12_plus_v13`. Esta última reúne as substituições **Barsi** do v12 e v13; os números Graham principais continuam sendo v11.2. O candidato Graham v12 está preservado e entra na matriz de amplitude. BBSE3/SBSP3/CSMG3/ENBR3 e os quatro grupos novos são conjuntos disjuntos. Cada substituição remove a contribuição anterior da própria posição, inclusive seu limite inferior/superior. Não se adicionou uma revisão central sobre um limite que já continha sensibilidade dessa posição.

Referências: [38 percursos](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/ativos_calculados_v13.csv), [1.212 posições reconciliadas](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/alternativas_barsi_v13_por_posicao.csv), [768 coortes](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/comparacao_coortes_v13.csv), [250 preços/ISIN](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/cotacoes_cotahist_v13.csv) e [matriz de fontes](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/matriz_4_ativos_fontes.csv).

## Resultado da reconstrução dirigida

Manutenção iniciada em 2020; contribuição em B00S central com peso inicial de 10% em cada exposição:

| Exposição | Retorno v9 | Retorno por eventos v13 | Revisão da carteira |
|---|---:|---:|---:|
| PSSA3 | 180,933530% | 188,271499% | +0,733797 pp |
| TIMP3→TIMS3 | 124,802439% | 126,040032% | +0,123759 pp |
| VIVT4→VIVT3 | 107,080145% | 111,689209% | +0,460906 pp |
| SAPR4 | 53,482645% | 61,746745% | +0,826410 pp |
| Quatro exposições | — | — | **+2,144873 pp** |

**PSSA3.** A bonificação executada foi de 100%, ex em 21/10/2021, fator 2. O anúncio de intenção de desdobramento 1:3 não foi aplicado. Foram preservadas parcelas distintas omitidas na tabela resumida: complemento/partes de 2021, 2022 e 2025, com as ratificações sem duplicação de totais. Fontes: [bonificação efetiva](https://api.mziq.com/mzfilemanager/v2/d/b77a3922-d280-4451-b3ee-0afec4577834/58c7cb8a-888b-4fff-3949-6efc460cb9e1?origin=2), [intenção não executada como evento](https://api.mziq.com/mzfilemanager/v2/d/b77a3922-d280-4451-b3ee-0afec4577834/c1d8e145-5c3e-3bd0-2c5f-08fe9f98e875?origin=2), [parcelas de 2021](https://api.mziq.com/mzfilemanager/v2/d/b77a3922-d280-4451-b3ee-0afec4577834/493a6ff0-1341-22f7-1a72-d9896b29432f?origin=2), [parcelas de 2022](https://api.mziq.com/mzfilemanager/v2/d/b77a3922-d280-4451-b3ee-0afec4577834/bd82067a-476b-c3a3-b00a-9a8d540f77cb?origin=2), [retificação de 2025](https://api.mziq.com/mzfilemanager/v2/d/b77a3922-d280-4451-b3ee-0afec4577834/c51162ba-772b-3276-e991-5239fc18f0bc?origin=2).

**TIM.** A incorporação elimina TIMP3 e entrega TIMS3 1:1 em 13/10/2020, sem caixa criado e sem preço sintético do predecessor. As três parcelas de dividendos com a mesma data-com de 2024 e 2025 usam a mesma quantidade elegível; duas parcelas de mesmo valor são obrigações distintas. Também foi incorporada a parcela de JCP de setembro/2022 omitida na base resumida. O agrupamento/desdobramento de julho/2025 tem fator líquido 1 no índice fracionário. Fontes: [migração efetiva](https://api.mziq.com/mzfilemanager/v2/d/4c4aa51f-1235-4aa1-8b83-adc92e8dacc3/5e0de946-852c-4d28-ad6e-ef5d86e4fec5?origin=2), [retificação JCP 2022](https://api.mziq.com/mzfilemanager/v2/d/4c4aa51f-1235-4aa1-8b83-adc92e8dacc3/e8292dc6-6925-d665-bf16-5f2fa1b5dd91?origin=2), [parcelas 2024](https://api.mziq.com/mzfilemanager/v2/d/4c4aa51f-1235-4aa1-8b83-adc92e8dacc3/1c513fe5-4ad4-c0cd-56b1-b8cf5e09401c?origin=2), [parcelas 2025](https://api.mziq.com/mzfilemanager/v2/d/4c4aa51f-1235-4aa1-8b83-adc92e8dacc3/762980b9-e792-0a74-6f3f-67a09abe2c68?origin=2).

**Telefônica.** VIVT4 PN converte em VIVT3 ON 1:1 em 23/11/2020. Os proventos anteriores respeitam a classe PN; não se substituiu PN por ON na série anterior à conversão. O fator líquido de abril/2025 é 2. A planilha oficial declara que os valores anteriores ao desdobramento não estão ajustados: foram usados valores brutos nominais. As restituições de capital entram como caixa/reinvestimento, com cenário separado mantendo caixa. Fontes: [DFP 2020, p. 7, hospedada por terceiro](https://s3.glbimg.com/v1/AUTH_63b422c2caee4269b8b34177e8876b93/valorri-uploads/bs/2021/f/6/GkGOxJRVyK8BsXNSui3Q/telefonica-1-.pdf), [DFP 2025, pp. 92–93](https://api.mziq.com/mzfilemanager/v2/d/24165f81-24d6-4648-bf9f-66712905d5a2/197836af-54b5-cff0-af1e-de97ad340f36?origin=2), [planilha oficial de proventos](https://api.mziq.com/mzfilemanager/v2/d/24165f81-24d6-4648-bf9f-66712905d5a2/34b95df5-e8c3-6d48-b667-42e740e0df5e?origin=2).

**SAPR4.** Foi mantida a coluna PN, inclusive o direito formado no fechamento de 30/06/2020 e ex em 01/07/2020. Datas-ex inconsistentes da tabela foram alinhadas ao calendário B3 e à data-com, sem trocar a classe. A ausência de JCP do primeiro semestre de 2026 está expressamente documentada; não foi generalizada para outros eventos. Fontes: [histórico por classe](https://ri.sanepar.com.br/docs/Sanepar-2025-12-18-cW6NmzgB.pdf), [deliberação sobre JCP 1S2026](https://ri.sanepar.com.br/docs/Fato-Relevante-Sanepar-2026-06-24-tkL9PDN6.pdf).

A quantização e o leilão real das sobras de TIM/Telefônica não estão simulados. A manutenção de frações é a convenção herdada do índice e pode divergir da execução de uma carteira pequena. A retificação PSSA de março/2026 está em PDF sem texto extraível: valor B3 0,54231784082 permanece provisório, contra 0,54228396511 do aviso inicial. **Ambos foram simulados**; impacto B00S/2020 de apenas −0,00001913 pp. Nenhuma nova pesquisa de centavos é necessária nesta rodada.

## R16 × B00S: efeito combinado e limites

| Alternativa B00S, manutenção 2020 | Retorno central | Limite superior residual | R16 menos central | R16 menos limite |
|---|---:|---:|---:|---:|
| v9 | 122,996220% | 126,329625% | 3,856854 pp | 0,523449 pp |
| v12_partial | 122,269179% | 124,776158% | 4,583895 pp | 2,076917 pp |
| v13_four | 125,141093% | 127,267038% | 1,711982 pp | -0,413964 pp |
| v12_plus_v13 | 124,414052% | 125,713571% | 2,439023 pp | 1,139504 pp |

R16 v11.2 = **126,853075%**. O limite superior com apenas os quatro grupos v13 ultrapassa R16, mas a combinação com v12 inclui a revisão negativa já documentada de SBSP3. Seu limite fica em 125,713571%, a 1,139504 pp de R16. A antiga sensibilidade v12 de **somente BBSE3**, com distância de 0,126601 pp, continua preservada e não representa a combinação integral.

Esses limites mantêm fixos os eventos substituídos e variam apenas o resíduo v9. Ao estressar também o caixa dos quatro grupos em ±20%, B00S/2020 fica entre **116,998296% e 132,280035%** e pode ultrapassar R16. Esse é um teste determinístico de sensibilidade, não evidência de erro de 20% nem intervalo probabilístico. Eventos desconhecidos e lacunas de seleção não têm máximo documental. Portanto, **R16 supera a alternativa central, mas sua superioridade geral continua inconclusiva**.

A cobertura calculada por eventos em B00S/2020 sobe de **26,3966% a 65,2447% do patrimônio final v9**, incluindo caixa; 34,7553% continua em aproximações. O denominador é o patrimônio da carteira, não contagem de nomes. Sete de 21 posições têm cálculo/âncora de eventos; isso não equivale a certificação integral. Todas as 96 coberturas por composição/ano/mecanismo estão em [cobertura_patrimonial_v13.csv](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/cobertura_patrimonial_v13.csv).

## Seis formações: resultados consolidados

Retornos acumulados em %, cenário central, até 30/06/2026. Graham = baseline v11.2; Barsi = substituições conjuntas v12+v13. Comparar regras **na mesma linha**, pois os horizontes diferem. Os CSVs incluem CAGR por dias efetivos/365,25, limites e composição conservadora.

**Manutenção**

| Formação | R00 | R03 | R16 | B00 | B00S | B06 | B06S | BOVA11 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 149,3140 | 136,3945 | 126,8531 | 114,1563 | 124,4141 | 95,7659 | 81,9798 | 84,5121 |
| 2021 | 182,5356 | 260,9826 | 260,9826 | 142,2059 | 161,4073 | 119,6218 | 119,6218 | 38,7817 |
| 2022 | 118,8876 | 155,8483 | 104,0184 | 140,9704 | 165,5791 | 131,2851 | 128,2138 | 77,9474 |
| 2023 | 117,9074 | 84,5249 | 63,6648 | 77,7940 | 94,2439 | 71,3070 | 74,4361 | 48,0687 |
| 2024 | 71,4701 | 56,3051 | 50,5067 | 59,4419 | 73,8306 | 52,8606 | 56,1409 | 40,4303 |
| 2025 | 18,2664 | 30,6161 | 25,7770 | 24,2836 | 26,8307 | 17,7937 | 19,3133 | 24,4387 |

**Renovação anual**

| Formação | R00 | R03 | R16 | B00 | B00S | B06 | B06S | BOVA11 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 204,1233 | 265,1978 | 248,1894 | 159,8511 | 163,7228 | 115,4303 | 107,2001 | 84,5121 |
| 2021 | 193,1553 | 180,4015 | 143,0250 | 141,4532 | 168,2775 | 117,9122 | 123,1736 | 38,7817 |
| 2022 | 144,8937 | 156,5688 | 122,4305 | 131,8358 | 159,2493 | 99,2704 | 104,0817 | 77,9474 |
| 2023 | 100,4060 | 89,2903 | 75,3646 | 75,1488 | 97,3423 | 58,8590 | 66,0724 | 48,0687 |
| 2024 | 73,7628 | 71,3282 | 60,7421 | 58,4554 | 73,8498 | 46,6822 | 52,8348 | 40,4303 |
| 2025 | 18,2664 | 30,6161 | 25,7770 | 24,2836 | 26,8307 | 17,7937 | 19,3133 | 24,4387 |

Em 2021, R03 e R16 têm pesos coincidentes e empatam na manutenção; não houve desempate artificial. No cenário central, R00, R03 e B00S lideram duas formações cada em cada mecanismo; R16 compartilha também a liderança da manutenção/2021. Contagens incluem empates e podem somar mais de seis.

A reconstrução conjunta muda quatro colocações centrais, correspondentes a **duas trocas de liderança na renovação**: 2022, B00S ultrapassa R03; 2024, B00S ultrapassa R00. Nenhuma ordem central de manutenção mudou frente ao Barsi v9 comparado com Graham v11.2. A mudança de composição para conservadora reverte essas duas lideranças: R03 ganha a renovação/2022 por 1,4142 pp; R00 ganha 2024 por 1,9591 pp. No central, as margens B00S são 2,6805 pp e somente **0,0871 pp**, respectivamente.

Referências: [todos os rankings](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/rankings_v13.csv), [ordens com empates](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/ordem_seis_formacoes.csv), [frequências/CAGR](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/frequencias_estabilidade_v13.csv) e [decisão por mecanismo](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/manter_ou_renovar_v13.csv).

## Quais regras funcionaram, e por quê

**B00S supera B00 nas seis formações e nos dois mecanismos, em ambas as composições.** A ponderação setorial muda o peso das exposições; não cria uma nova lista selecionada. Em 2024, por exemplo, CSMG3 contribui 22,3192 pp à manutenção B00S contra 11,1596 pp em B00. A concentração inicial máxima por setor cai de 45% em B00 para 20% em B00S. Esse resultado depende da trajetória forte de saneamento/seguros/telecom neste recorte; não implica prêmio universal por ponderação setorial.

**O filtro de preço B06 não melhorou o retorno neste recorte central:** B06 fica abaixo de B00 nas seis formações, nos dois mecanismos; B06S fica abaixo de B00S também em 6/6. Na composição conservadora há uma exceção para B06 versus B00 na manutenção/2020. A restrição do universo e do preço-teto muda a exposição aos vencedores posteriores; os dados não permitem atribuir causalidade isolada ao desconto. Ainda há riscos na normalização histórica do DPS usado pelo filtro.

**R03 é mais estável que R00 em colocação, sem vencer sempre.** R03 vence o benchmark 6/6 e fica entre 1º e 3º na renovação; R00 vence o benchmark 5/6 e varia de 1º a 7º. R03 versus R00 se divide 3/3 em cada mecanismo. A ampliação da carteira muda exposições, especialmente CSMG3: na manutenção/2022, sua contribuição a R03 é 47,4899 pp. Não se atribui todo o desempenho ao rótulo Graham.

**R16 não superou R03 em nenhuma formação neste recorte:** perdeu cinco e empatou uma manutenção; perdeu as seis renovações. Os dois usam a lista R03, mas R16 equaliza setores. Essa ponderação reduz o peso de vencedores como CSMG3: em 2022, sua contribuição cai de 47,4899 para 24,6244 pp. A conclusão é descritiva sobre estes pesos e retornos.

**Renovar não domina manter.** Desconsiderando o empate mecânico de 2025, renovar melhora cada regra Graham em quatro de cinco formações. Para R00, a exceção é 2023; para R03/R16, é 2021. B00S central também melhora em quatro de cinco, mas em 2024 o ganho de renovar é só 0,0192 pp. B00 e B06 melhoram com renovação em apenas uma de cinco; B06S em duas. No conservador, B06 e B06S perdem com renovação nas cinco. Custos e impostos ausentes podem afetar as comparações estreitas.

**Concentração e eventos excepcionais importam.** Na manutenção/2020, a maior posição final atribuída à origem é 28,74% em R00 contra 13,49% em B00S; números efetivos iniciais de posições são 6 e 14,06. CPLE3 responde por 54,9773 pp do retorno R00. Em 2021, CSMG3 responde por 124,0809 pp dos 260,9826% de R03/R16. Esses são ganhos de contribuições, não percentuais de carteira.

O contrafactual que mantém em caixa o capital inicialmente destinado ao maior contribuidor remove também suas perdas/ganhos posteriores: R00/2020 passaria de 149,3140% para 94,3366%, enquanto B00S/2020 passaria de 124,4141% para 104,1514%. É uma atribuição ex post, não nova regra selecionável nem previsão. Em R00/2022, SYNE3 contribui 38,5930 pp, com a restituição reinvestida conforme decisão já incorporada na v11.2; a sensibilidade histórica de caixa permanece preservada.

No novo catálogo, remover contrafactualmente as restituições VIVT reduz B00S em 1,6285 pp na manutenção/2020 e 4,0673 pp na renovação/2020. Na renovação/2022 e 2024, o mesmo exercício reduz B00S em 3,9983 e 2,0778 pp, suficientes para inverter aquelas lideranças centrais. Os pagamentos documentados não podem ser omitidos do retorno observado: o exercício demonstra dependência de caixa extraordinário. **Não é um catálogo exaustivo de distribuições extraordinárias de todas as ações.** Manter as restituições em caixa, em vez de reinvestir na data-ex, é uma sensibilidade econômica separada; impacto B00S manutenção/2020 de −0,3347 pp.

Contribuições, concentração inicial/final e sensibilidades estão em [concentracao_manutencao_v13.csv](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/concentracao_manutencao_v13.csv), [contribuicoes_manutencao_v13.csv](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/contribuicoes_manutencao_v13.csv) e [sensibilidades_carteiras_v13.csv](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/sensibilidades_carteiras_v13.csv).

## Confiança, materialidade e estabilidade temporal

A [matriz de 96 conclusões](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/matriz_confianca_materialidade_v13.csv) informa margem sobre benchmark e melhor competidor, amplitude entre alternativas efetivamente testadas, riscos capazes de inverter rankings e o pequeno refinamento PSSA. A amplitude combina versões, composições, limites residuais, caixa ±20% e restituições mantidas em caixa. Não é limite de erro documental nem intervalo de confiança; as alternativas não são observações independentes. Os contrafactuais que eliminam pagamentos/maior contribuidor ficam fora desse envelope.

Entre os cenários testados, a liderança permanece em R00 manutenção/2020 e 2023, R03 renovação/2020, R00 renovação/2021, B00S manutenção/2022 e R03 nas duas versões/2025. R03/R16 compartilham a manutenção/2021. Na manutenção/2022, até a margem mínima B00S para o melhor concorrente é +1,6540 pp dentro desse conjunto. A renovação/2022–2024 e a manutenção/2024 dependem das premissas. Isso não elimina os riscos não quantificados de seleção/completude.

As seis coortes terminam juntas e se sobrepõem. 2025 tem somente um período e manutenção=renovação. Frequências de vitória, CAGR e classificação média são **descritivas**, não seis testes independentes, probabilidade de sucesso, significância estatística ou validação fora da amostra. Não houve otimização retrospectiva para manter uma classificação preferida.

## Disponibilidade histórica e equivalência metodológica

A auditoria limitada leu o universo herdado de **206 registros**. Todos possuem data de recebimento DFP anterior/igual ao corte de disponibilidade declarado: zero recebimentos posteriores no metadado. O universo contém predecessores/deslistados, inclusive TIMP3, VIVT4 e ENBR3. Isso ajuda a afastar uma seleção exclusivamente por sobreviventes atuais, **mas não prova completude de listagens, classes, cinco/dez anos de lucros ou versões documentais disponíveis em cada data**.

O código Barsi usa os cinco anos anteriores (`range(y-5,y)`); a presença de anos futuros no dicionário não implica uso deles no sinal. Entretanto, DPS anuais arredondados, proxies NEOE no cenário central, normalização de classe/quantidade e seleção 2020 forçada para reproduzir v8 permanecem limitações. O cenário conservador é uma composição distinta, não limite inferior do mesmo portfólio. O preço-teto usa o fechamento de formação com execução no mesmo fechamento: hipótese otimista de implementação do sinal.

**Risco estrutural TIM na seleção:** TIMS3 tem lacunas e zeros nos históricos de lucro do universo de 2021–2024, é excluída na pré-seleção e não aparece no arquivo de 2025. A mudança de CNPJ exige continuidade histórica que esse arquivo não demonstra. A conversão de posição TIMP3→TIMS3 foi corrigida no retorno de 2020; isso não repara o universo/sinal de anos seguintes. Também existe risco de transportar o DPS PN de VIVT4 para o histórico ON de VIVT3 usado em seleções posteriores. Esses pontos podem alterar composição e ranking em eventual novo estudo; não se inventou lucro nem se acrescentou TIMS3 retrospectivamente.

Nos scripts Graham examinados, a seleção requer recebimento até a formação e usa versões conhecidas nesse momento; há decisões manuais F6 documentadas. A inspeção de código/metadata não revalida todos os dados de entrada nem demonstra universo completo. Os excertos com SHA e o snapshot Barsi estão em `audit_v13_inputs/selection_audit_evidence.json`, `build_selection_v9_reference.py` e `universe_v9_snapshot.csv`; o resultado está em [disponibilidade_universo_v9_206.csv](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/disponibilidade_universo_v9_206.csv).

A equivalência melhorou nas quatro exposições recalculadas: preço nominal, classe, eventos, pesos e calendário são comparáveis ao motor Graham. **Permanece parcial no total Barsi**, que mistura eventos com aproximações v9 de caixa. Não há justificativa para chamar toda a comparação de integralmente homogênea.

## Risco diário: somente onde há trajetória

Foram calculadas volatilidade diária amostral anualizada por √252 e perda máxima do pico com patrimônio diário por eventos. Há **32 trajetórias Graham completas e 12 recortes BOVA11**; os dois mecanismos do benchmark duplicam as mesmas seis trajetórias para comparação. Quatro manutenções Graham (R03/R16, 2022/2023) têm lacunas e ficam sem métricas. As 48 células Barsi têm risco diário **não estimado**, pois o caixa residual anual não define uma trajetória diária equivalente. Não se interpolou caixa nem se preencheu preço ausente.

| Manutenção 2020 | Volatilidade anualizada | Drawdown máximo |
|---|---:|---:|
| R00 | 18,75% | -18,35% |
| R03 | 18,18% | -18,31% |
| R16 | 19,42% | -20,78% |
| BOVA11 | 18,90% | -26,40% |

Esses números são condicionais à trajetória teórica da baseline; **não estabelecem dominância ajustada a risco sobre Barsi**. As quatro exposições individuais reconstruídas têm trajetórias completas, mas não substituem o risco do portfólio. Fonte: [risco_diario_cobertura_v13.csv](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/risco_diario_cobertura_v13.csv).

## Reprodução, preservação e encerramento

Em checkout com os insumos locais já preparados:

```bash
python scripts/reconstruct_barsi_v13.py --raw-dir /caminho/data/raw
python scripts/analyze_barsi_graham_v13.py
python scripts/audit_selection_v13.py
python -m pytest -q tests/test_graham_maintenance_v11.py tests/test_itsa_rights_v11_2.py tests/test_audit_v12.py tests/test_barsi_v13.py
```

Sem SQLite/COTAHIST, o último comando reexecuta os 38 retornos através do fixture mínimo de cotações nominais/calendário. O fixture não permite reproduzir volatilidade diária completa. Os fatos normalizados são transcrições documentais congeladas com fonte/hash, não um parser universal capaz de certificar publicações ausentes. Foram preservados 100 documentos/catalogues de origem; os dois PDFs DFP Telefônica têm somente páginas extraídas versionadas, explicitamente marcadas, com hash separado do original completo.

Validações locais: **101 testes de checkpoint aprovados; 33 testes do motor original aprovados; 18 paridades v6, 36 regressões v10/v11.1 e 36 regressões econômicas v11.2 aprovadas**. Os 71 arquivos da baseline e os 66 itens do manifesto v12 permanecem idênticos. A reexecução de alertas e comparabilidade v12 produziu **16 arquivos byte a byte idênticos**. A cobertura de 12 pares v12 foi preservada por integridade, sem reabrir pesquisa documental. O novo workflow `.github/workflows/barsi-v13.yml` executa os testes offline; o workflow anterior não foi editado.

Entregáveis adicionais: [integridade das 137 referências](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/integridade_baselines_137.csv), [reexecução v12](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/regressao_v12_reexecucao.csv), [36 regressões v11.2](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/regressao_economica_v11_2_36.csv) e [riscos e materialidade](../research/graham_v6_comparison/checkpoint_v13_2026_10_07/riscos_abertos_v13.md). O manifesto v13 cobre todos os novos arquivos de entrega, exceto ele próprio.

**Recomendação ao coordenador:** encerrar o estudo como exploração histórica reproduzível, mantendo a v11.2 provisória e v12/v13 como alternativas. As conclusões mais úteis são a estabilidade relativa de R03/B00S, a ausência de vantagem observada do filtro B06, a dependência de CSMG3/CPLE3/SBSP3 e a fragilidade das lideranças estreitas. Não é necessário certificar cada centavo para essa leitura. Uma eventual nova etapa deve ter escopo próprio para universo histórico/continuidade dos fundamentos e política executável de caixa/frações; não prolongar esta rodada de auditoria. PR permanece draft, sem merge.
