# Indicadores fundamentalistas: primeiros resultados empíricos

**Nenhum indicador ou combinação demonstrou poder preditivo confiável para o universo histórico nesta rodada.** Foram executadas as análises, com retornos aproximados utilizáveis e critérios congelados. Há sinais condicionais de proteção contra perdas em lucro, caixa e dividendos; eles não sobrevivem conjuntamente às exigências de representatividade, controles, sensibilidade e validação. Isso não prova que os indicadores sejam economicamente inúteis.

A reconstrução passou de **24 trajetórias certificadas para 2.568 trajetórias A/B**, em 4.553 janelas calendariamente completas. São **1.603 de três anos, em 306 companhias**, e **965 de cinco anos, em 230 companhias**. Os 24 certificados continuam A; as 2.544 novas estimativas são B. Não houve simulação de carteira nem alteração de Graham/Barsi. O PR #8 permanece draft, sem merge.

## O que mudou no cálculo

Não se exige mais catálogo integralmente conciliado de cada emissor para a exploração. O [protocolo da rodada](protocol_round3.json), congelado em 10/10/2026 às 02:31 UTC antes das relações indicador/retorno, define suficiência, filtros, cortes temporais e sensibilidades. A trava anterior de 95% foi expressamente substituída por autorização do usuário. Os arquivos anteriores permanecem intactos.

- **A:** escopos documentais previamente reconciliados, 24 janelas. **B:** preços brutos, identidade de classe histórica, calendário observado e livro econômico em escala, sem divergência material conhecida. **C:** identidade, continuidade ou evento potencialmente material ainda pendente. C permanece no denominador e não recebe retorno confiável.
- O livro usa os originais locais, o overlay independente da segunda rodada, FRE e eventos já auditados. Caixa bruto é reinvestido fracionariamente no fechamento ex; conversões preservam suas pernas, direitos não exigem aporte novo e resgate deixa caixa nominal até o vencimento. Ausência de cotação não vira perda total nem último preço mantido indefinidamente.
- Vencimentos usam o último pregão até a data-alvo, com até cinco pregões de defasagem de cotação. Uma classe não é substituída por outro ISIN sem linhagem econômica. Riscos são aplicados apenas durante a posse da respectiva classe, inclusive sucessores.
- Fatores inferidos exclusivamente de preços não corrigem retornos. Assim, quedas verdadeiras não são transformadas em falsos desdobramentos. Quebras ascendentes restauradas e sem mecânica documental ficam C.

`adj_close` foi confrontado com cálculos independentes e rejeitado como método geral. Entre os 24 certificados, 12 comparações excederam 15% de diferença relativa de patrimônio. No conjunto B com comparador disponível, isso ocorreu em **108/1.497 janelas de três anos e 121/899 de cinco anos**. Há erros de mecânica muito superiores a diferenças de centavos. O comparador ajustado não entra nos retornos usados nem em valuation.

A revisão encontrou duas falhas de implementação: representações arredondadas do mesmo grupamento podiam duplicar a quantidade; aprovação de bonificação podia ser confundida com a data de direito. Foram corrigidas e verificadas contra os certificados. Para associar bonificações, a aprovação pode anteceder a data oficial em até 90 pregões; a janela curta de dez pregões fica para os demais mecanismos. Essa correção documental, posterior ao congelamento inicial, não altera filtros, limiares ou partições estatísticas.

Também foi identificado um grupamento omitido de **61 ações para uma** da GPC, documentado no [ITR de junho de 2016, nota 18.1](https://mz-filemanager.s3.amazonaws.com/ca373d40-8cff-414f-a58e-e8d4ab5fe28f/central-de-resultados/3a73dce8d37e1050e2699cf261a8ce8d0394584c9246704a966e4a406f5528cb/itr_2t16.pdf). Corrigi-lo remove falsas multiplicadoras e conserva a companhia na análise. Foi o único documento novo: **960.704 bytes**, com hash, mantido localmente. Nenhuma nova base B3 foi baixada. O ITR posterior serve à mecânica do retorno realizado, nunca aos fundamentos conhecidos na seleção.

## Verificação e limites de confiabilidade

As **24 referências documentais** coincidem com o novo motor após as correções. Uma amostra determinística de **334 janelas, 143 companhias, 41 setores e dez coortes** inclui 123 janelas com BDI de dificuldade e 31 com saída/suspensão original resolvida. Em 301 janelas de classe contínua, uma fórmula escalar independente reproduz a contabilidade do motor; as demais usam trajetórias com múltiplas pernas, cobertas também pelos testes sintéticos.

Essa fórmula usa os mesmos insumos: verifica implementação e consistência, **não prova completude documental de 143 emissores**. As referências com fontes plenamente reconciliadas cobrem só três companhias. B é estimativa, não certificação integral. As faixas de ±15% e ±30% de patrimônio são hipóteses de sensibilidade, não intervalos de confiança nem limites de erro comprovados.

Janelas próximas de 0,5x, 3x ou do Ibovespa são explicitamente ambíguas sob a faixa B de 15%; a [matriz de limiares](published_round3/threshold_uncertainty.csv) separa classificações robustas à faixa, possíveis e ambíguas. As frequências centrais abaixo devem ser lidas junto às frequências inferior/superior dos [cenários](published_round3/filter_sensitivity.csv). Não se escolheu a classificação mais favorável.

Essa faixa deixa 98/101 janelas potencialmente ambíguas como multiplicadoras e 104/42 como grandes perdas, respectivamente em três/cinco anos. Elas continuam B com classificação condicionada à hipótese, em vez de serem apagadas ou classificadas convenientemente.

## Cobertura histórica

O universo mapeado permanece **2.588 companhia/data, 399 companhias e 5.176 horizontes**. Há ainda 94 títulos/data elegíveis com identidade pendente, ou 188 títulos/horizonte, preservados [separadamente](published_round3/unresolved_identity_coverage.csv). Eles não foram contados como 94 companhias nem apagados. Os limites estatísticos para C referem-se ao universo mapeado; resolver as identidades poderá ampliar esses limites.

| Coorte | A/B 3a | C 3a | A/B 5a | C 5a | Tempo 5a |
|---|---:|---:|---:|---:|---:|
| 2014 | 136 | 97 | 110 | 123 | 0 |
| 2015 | 134 | 96 | 107 | 123 | 0 |
| 2016 | 135 | 87 | 107 | 115 | 0 |
| 2017 | 143 | 90 | 117 | 116 | 0 |
| 2018 | 150 | 90 | 117 | 123 | 0 |
| 2019 | 149 | 92 | 120 | 121 | 0 |
| 2020 | 166 | 96 | 138 | 124 | 0 |
| 2021 | 198 | 106 | 149 | 155 | 0 |
| 2022 | 205 | 113 | 0 | 0 | 318 |
| 2023 | 187 | 118 | 0 | 0 | 305 |

Além das 2.568 janelas A/B, há **1.985 C com horizonte completo** e **623 censuradas por tempo**, nas coortes 2022/2023 de cinco anos. Aquisições não são rotuladas como falência. A situação econômica abaixo é uma auditoria da trajetória, não um indicador conhecido na seleção.

| Estado da trajetória | A/B 3a / completas | A/B 5a / completas |
|---|---:|---:|
| BDI histórico de dificuldade | 78/248 (31.5%) | 45/225 (20.0%) |
| Saída/suspensão da classe original, sem BDI de dificuldade | 14/345 (4.1%) | 17/403 (4.2%) |
| Demais trajetórias | 1511/1995 (75.7%) | 903/1337 (67.5%) |

Em três anos, todas as dez coortes têm pelo menos metade das janelas A/B; em cinco anos, só duas das oito completas. Os três tercis de ativo contábil superam 40% em ambos os horizontes. **Porte é aqui ativo contábil, não capitalização de mercado inventada.** Entre setores com pelo menos 50 janelas, setor desconhecido fica abaixo do piso em três anos; bancos e setor desconhecido, em cinco anos.

O maior problema é econômico: a diferença de cobertura entre demais trajetórias e saídas/suspensões chega a **71,7 pontos percentuais em três anos e 63,3 em cinco**. A [avaliação congelada de suficiência](published_round3/sufficiency.csv) reprova representatividade nos dois horizontes. Portanto, as estatísticas seguintes são **associações condicionais à parte observável**, não estimativas preditivas para o universo nem conclusões obtidas supondo sobrevivência dos casos ausentes.

## Indicadores, desenho e inferência

Foram calculados 12 indicadores com alguma cobertura: lucro positivo, margem EBIT, FCO/lucro positivo, liquidez, dívida financeira/ativo, ROE sobre patrimônio médio, FCO/ativo, margem líquida, crescimento anual/trienal de receita, consistência de lucro em três exercícios e dividend yield aproximado. [Cobertura por indicador/coorte](published_round3/indicator_coverage.csv) e [estratificação financeira](published_round3/financial_stratification.csv) são publicadas.

Os 85 balanços recuperados na segunda rodada foram reutilizados. Valores anuais e históricos exigem referência, versão e recebimento exatos, estritamente anteriores à seleção; uma versão ausente não é substituída por revisão futura nem por comparativo posterior. Dados ausentes e denominadores inválidos não viram zero.

Bancos/seguradoras ficam fora dos índices industriais. ROE usa lucro total anual/patrimônio total médio positivo, como aproximação contábil; não equivale a ROE atribuível nem retorno sobre capital prudencial. Dividend yield é caixa bruto com direito ex nos 12 meses anteriores, dividido pelo preço bruto contemporâneo, com quantidade normalizada; não é payout exato. Receita cresce nominalmente. Não foram calculados retornos reais por IPCA nesta rodada; retornos nominais e relativos ao Ibovespa são distintos.

**P/L, P/VP e payout não têm capital por classe/tesouraria suficientemente compatível com a data para estimação nesta execução. EV/EBITDA não é calculado com EBIT renomeado. ROIC não é preenchido sem NOPAT e capital investido consistentes.** Esses indicadores não foram declarados irrelevantes: faltam insumos adequados.

Os filtros e combinações foram congelados antes da análise. Para uma combinação AND, uma condição observada falsa reprova a companhia mesmo se outra razão for indefinida: lucro negativo não desaparece de “lucro positivo + caixa”. Os campos `feature_known_n`/`feature_coverage` nos filtros representam a decisão conhecida do predicado, inclusive essas reprovações. A cobertura numérica de cada indicador está em arquivo próprio.

A análise executa Spearman dentro de coorte, ponderando coortes igualmente, quintis sem romper empates artificiais, contrastes dos filtros, comparação com o universo de decisão conhecido e controles coorte/setor quando há pelo menos cinco selecionadas e cinco rejeitadas na célula. `sector_matched_n` informa o suporte; célula sem suporte tem resultado nulo, não um controle inventado. Não se controla por capitalização histórica incompatível.

Os intervalos e p-valores exploratórios usam **999 reamostragens por companhia**, preservando suas janelas sobrepostas. São condicionais ao calendário observado; há poucos blocos temporais independentes de três/cinco anos para confirmação geral. BH e BY abrangem conjuntamente **448 comparações declaradas**; testes sem suporte entram como p=1 na família, mantendo resultados próprios ausentes. Nenhum teste passa FDR de 5% nesta rodada. A [documentação SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html) distingue a condição de dependência de BH da correção BY.

A resolução Monte Carlo mínima é p=0,001; as associações usam postos calculados dentro do universo observado. O menor q é 0,0747 por BH e 0,4990 por BY. Esses valores não provam ausência de efeito nem potência suficiente, especialmente com perda de cobertura e poucos períodos independentes.

Desenvolvimento de três anos: 2014–2016; purga: 2017–2019; avaliação reservada: 2020–2023. Em cinco anos: desenvolvimento 2014–2015, purga 2016–2020 e avaliação 2021. Não se ajustaram limiares ou combinações aos resultados reservados. **Uma única coorte de cinco anos não valida estabilidade temporal.** O [Ibovespa é índice de retorno total](https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/ibovespa.htm); o cálculo usa os JSONs diários locais e a data efetiva anterior ou igual ao vencimento.

## Resultados dos filtros

Avaliação reservada **2020–2023, horizonte de três anos, A+B**. Retornos são acumulados nominais brutos; porcentagens não são anualizadas. Cada linha compara um universo de decisão conhecido próprio, portanto suas médias não devem ser comparadas como se a cobertura fosse idêntica. Multiplicadora significa patrimônio ≥3x; grande perda, ≤0,5x. “Bombas evitadas” divide perdas rejeitadas por todas as perdas observáveis; “multiplicadoras excluídas” usa denominador análogo. Não representa falências documentalmente confirmadas.

| Filtro | A/B com decisão | Selecionadas | Média | Mediana | ≥3x | ≤0,5x | Bombas evitadas | Multiplicadoras excluídas |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Lucro positivo | 737 | 611 | 32.8% | 14.8% | 4.9% | 13.3% | 35.7% | 16.7% |
| FCO/lucro ≥1, lucro positivo | 549 | 305 | 36.0% | 16.4% | 5.6% | 11.1% | 54.1% | 39.3% |
| Margem EBIT positiva | 664 | 597 | 30.4% | 9.2% | 5.2% | 14.7% | 24.1% | 8.8% |
| Liquidez ≥1 | 666 | 569 | 30.6% | 9.3% | 5.4% | 16.2% | 20.7% | 8.8% |
| Dívida/ativo ≤40% | 636 | 484 | 32.8% | 9.8% | 5.6% | 16.5% | 27.3% | 20.6% |
| ROE médio ≥15% | 662 | 281 | 29.2% | 20.5% | 2.8% | 10.3% | 70.7% | 74.2% |
| FCO/ativo positivo | 666 | 555 | 31.1% | 9.3% | 5.0% | 14.6% | 30.2% | 17.6% |
| Receita anual crescente | 722 | 563 | 29.1% | 7.9% | 5.0% | 15.5% | 29.3% | 22.2% |
| Lucro positivo em três exercícios | 695 | 473 | 34.2% | 20.8% | 4.0% | 11.6% | 50.0% | 45.7% |
| Dividend yield aproximado ≥4% | 699 | 224 | 43.1% | 29.0% | 4.9% | 5.4% | 89.2% | 68.6% |

O decil superior por coorte é uma medida separada: `top_decile_winners_excluded` nos CSVs. Por exemplo, o filtro de dividendos exclui **70,8%** dessas vencedoras observáveis na avaliação reservada, mas também rejeita 68,0% do universo: o excesso é 2,8 pontos, e para multiplicadoras ≥3x apenas 0,6 ponto. Evitar muitas bombas por selecionar pouco não basta: os arquivos apresentam esse excesso de bombas/vencedoras excluídas em relação à fração simplesmente rejeitada.

Combinações operacionais na mesma avaliação reservada:

| Combinação | A/B com decisão | Selecionadas | Média | Mediana | Média menos universo | Diferença setorial/coorte contra rejeitadas |
|---|---:|---:|---:|---:|---:|---:|
| Lucro + caixa | 675 | 305 | 36.0% | 16.4% | +8.7 pp | +14.1 pp |
| Margem + caixa | 611 | 303 | 36.2% | 16.4% | +8.1 pp | +13.6 pp |
| Lucro + liquidez | 675 | 496 | 32.9% | 12.7% | +5.7 pp | +9.3 pp |
| ROE + dívida baixa | 652 | 189 | 26.0% | 8.6% | -2.4 pp | +17.0 pp |
| Receita crescente + caixa | 608 | 247 | 36.1% | 15.6% | +7.2 pp | +18.7 pp |
| Lucro + caixa + liquidez | 675 | 268 | 37.8% | 17.0% | +10.6 pp | +11.8 pp |
| ROE + dívida baixa + caixa | 672 | 79 | 30.7% | 9.0% | +1.3 pp | +53.8 pp |

Os [resultados completos](published_round3/filter_results.csv) incluem desenvolvimento, coortes de purga apenas descritivas, todo o histórico e avaliação reservada. [Quintis](published_round3/indicator_quintiles.csv), [associações individuais](published_round3/indicator_results.csv), [coortes](published_round3/filter_cohorts.csv) e [influência/estabilidade](published_round3/filter_stability.csv) estão disponíveis, incluindo fracassos e resultados nulos. Combinações com valuation não são operacionais; rejeições conhecidas por outra condição não fabricam aprovação com múltiplo ausente.

## O que parece útil, o que falhou e o que permanece inconclusivo

**Lucro positivo:** na avaliação de três anos, retorno médio de 32,8%, contra 28,6% no universo comparável, e 35,7% das grandes perdas observáveis rejeitadas. No histórico completo, porém, média selecionada de 56,6% fica abaixo de 61,3% do universo. O filtro pode ajudar na proteção condicional, mas exclui recuperações vencedoras e não seleciona multiplicadoras de forma persistente.

**Caixa:** FCO/lucro positivo melhora a mediana e reduz perdas na parte observável. Sua associação relativa ao mercado muda de −0,024 no desenvolvimento para +0,120 na avaliação, sem persistência demonstrada. A combinação lucro+caixa+liquidez apresenta média de **37,8% contra 27,2%**, evita 73,9% das perdas e exclui 52,9% das multiplicadoras observáveis na avaliação. Ela merece aprofundamento como filtro de risco, **não classificação de preditor promissor já validado**: o controle setorial muda entre períodos e o efeito não resiste à sensibilidade adversa.

**Dividend yield ≥4%:** há o sinal condicional mais consistente de mediana e proteção; a associação relativa é +0,174 no desenvolvimento e +0,202 na avaliação. Contudo, o ganho contra rejeitadas do mesmo setor/coorte na avaliação é **−3,4 pontos percentuais**, com suporte em apenas parte da amostra. A seleção perde muitas grandes vencedoras. Não passa multiplicidade, sensibilidade adversa nem controle dos casos ausentes; mereceria auditoria dirigida de caixa/capital e concentração setorial antes de nova conclusão.

**ROE alto:** seleciona menos perdas, mas exclui 74,2% das multiplicadoras na avaliação e não melhora a média comparável. **Liquidez isolada e baixo endividamento** mostram associações individuais pequenas e instáveis; a razão de liquidez tem Spearman relativo +0,015 na avaliação. **Crescimento de receita** não apresenta vantagem estável: a associação anual relativa é −0,131 na avaliação. **FCO/ativo** muda de sinal entre períodos. Esses resultados não justificam usar isoladamente tais indicadores para selecionar vencedoras; também não demonstram irrelevância universal.

Em cinco anos, a única avaliação reservada (2021) mostra médias condicionais de 32,7% para lucro positivo, 41,8% para caixa, 73,7% para dividendos e 42,3% para lucro+caixa+liquidez. Os universos têm apenas 146/108/135/139 janelas com decisões/retornos disponíveis; suporte amostral e temporal não permite chamar isso de validação.

## Sensibilidade e próximos impedimentos

O [limite conservador de grandes perdas](published_round3/filter_missing_bounds.csv) permite que o efeito de lucro positivo vá de **−28,0 a +59,2 pontos percentuais**; para lucro+caixa+liquidez, de **−24,0 a +46,1**, no histórico de três anos. Os casos C conhecidos podem inverter a vantagem. Não foi imputado zero como retorno observado.

Sob estresse adverso B de 15% — patrimônio selecionado reduzido e rejeitado aumentado — a diferença média entre selecionadas/rejeitadas da combinação lucro+caixa+liquidez passa de **+5,9 para −42,6 pontos percentuais** no histórico de três anos. Essa hipótese é deliberadamente adversa; não estima erro provável. A e B separados, faixas de 15/30%, hipótese C=0 explicitamente fictícia, fases temporais sem sobreposição e retirada de uma companhia inteira estão registrados. A isolada tem apenas três companhias e não valida a representatividade de B.

Assim, **nenhum filtro foi promovido a simulação, recomendação de investimento ou conclusão efetivamente validada**. O avanço desta rodada são os retornos escaláveis, resultados empíricos reproduzíveis e uma demonstração quantitativa de por que sinais aparentes ainda não bastam.

Ordem de resolução, sem baixar bases indiscriminadamente:

1. **Saídas e sucessores:** 833 janelas atingidas por ausência de classe próxima ao vencimento; usar documentos e relações CVM/B3 já locais. Não distinguir fracasso de aquisição pelo desaparecimento do ticker. Resolver também as 94 identidades elegíveis, sem presumir companhias distintas.
2. **Direitos de subscrição:** 749 janelas com entitlement não reconciliado; cruzar aumentos FRE com cotações de direitos restauradas. Documentar proporção e liquidação ou limitar economicamente seu efeito. Não aportar capital novo nem bloquear resíduos comprovadamente pequenos.
3. **Capital e datas materiais:** 250 janelas com data ex documental pendente, 239 com quebra ascendente restaurada, 199 com fator detectado sem corroboração e 153 com contradição de fator oficial. As causas se sobrepõem. Priorizar casos que possam mudar perda/multiplicadora ou os controles, mantendo quedas reais.
4. **Valuation compatível:** quantidade histórica de cada classe menos tesouraria, composição de units e preços brutos na seleção. EBITDA verdadeiro e NOPAT são recuperação distinta. Indicadores já utilizáveis continuam disponíveis, sem aguardar esses campos.
5. **Validação temporal:** acrescentar períodos realmente independentes quando disponíveis e preservar a reserva atual. Não escolher novos filtros com base nesta avaliação.

## Preservação, publicação e reprodução

Os **413 arquivos/fontes dos checkpoints anteriores** foram verificados antes e depois. O SQLite continua com SHA-256 `0ab5d487ec8e6efe7c995a7bec5f0ae4e6602fc734dfbd4bc96e7cc4c82c3211`. Os 14 MB anteriores e o overlay permanecem locais. O código novo está em `round3/`; nenhuma base volumosa foi copiada. Os testes cobrem calendário/identidade, perdas reais, mecânica simultânea, grupamentos, versões históricas, combinações com campos ausentes, reamostragem por companhia e limites de classificação/publicação.

Só estatísticas agregadas, código, testes, documentação e manifestos são publicados. Células de retorno com menos de cinco janelas ou três emissores são suprimidas na publicação, mantendo contagens e todos os cálculos locais. [Auditoria de publicação](PUBLICACAO_RODADA3.md) e [retomada após expiração da janela](RETOMADA_RODADA3.md) registram arquivos, tamanhos e comandos offline. A expiração da janela não exige copiar as bases para outro serviço.
