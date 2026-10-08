# Protocolo e limites do checkpoint tributário

A decisão vigente é a [decisão final do coordenador no PR #1](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/1#issuecomment-6049367960). A implementação está na branch `scenario/ir-100k-a-b2`, baseada em `fc62733d131819dfabd33a2960586bbc9ae90512`. As versões v11.2, v12, v13, seus manifestos e o motor v6 não foram alterados. O resultado é uma simulação econômica executada, com partes fiscais explicitamente provisórias.

## Capital, universo e execução

Cada carteira começa com **R$ 100.000**, sem aportes, corretagem, emolumentos ou impostos sobre movimentação. São seis formações independentes, 2020–2025. As sete regras são R00, R03, R16, B00, B00S, B06 e B06S. Mantêm-se os universos Barsi `central` e `conservative` que já existiam na v13. Eles não são novas políticas. Há apenas **A e B2**, mais as referências BH das quatro regras Barsi e do BOVA11.

O sinal utiliza o fechamento de junho. A compra inicial ocorre no primeiro pregão seguinte; cada renovação vende no primeiro pregão seguinte ao sinal e compra no segundo pregão depois da venda, com preços nominais exatos dessas datas. Até liquidar, a receita fica em conta a receber e não financia compras. Nenhum preço obrigatório foi preenchido por carregamento do último valor. O extrato portátil contém 60 códigos e 75 mil cotações, provenientes do SQLite local aberto em modo somente leitura, complementadas pelas cotações nominais congeladas; a comparação encontrou **zero divergências** entre os pontos comuns.

A venda final ocorre no fechamento de **30/06/2026**. O patrimônio final já deduz integralmente o imposto dessa venda, embora a liquidação financeira e o recolhimento de junho ocorram em julho. O programa também executa esses movimentos até 31/07, sem nova exposição, e verifica que o caixa final coincide com o patrimônio líquido na data de corte.

Preserva-se a convenção de ações fracionárias do índice herdado. Ela não corresponde à execução de quantidades inteiras por uma corretora. Preços de fechamento são referências de execução sem spread ou impacto de mercado. Não se calculou volatilidade/drawdown a partir dos proventos agregados.

## A e B2

**A:** liquida toda a posição, reserva o imposto e recompõe a lista anual congelada. **B2:** vende as posições com reprovação fundamental documentada, retém as demais e vende somente frações necessárias para financiar novos selecionados. A união de sobreviventes e entrantes define os pesos-alvo: iguais por empresa em R00/R03/B00/B06; iguais por setor e, dentro dele, por empresa em R16/B00S/B06S.

O financiamento dos entrantes usa caixa livre e receitas de exclusões, líquidos de imposto. Se faltar dinheiro, vende primeiro as posições sobreviventes acima do peso-alvo, proporcionalmente ao excesso; depois, se necessário, vende proporcionalmente o saldo dos sobreviventes. O algoritmo busca a primeira solução viável, examinando a descontinuidade da isenção de R$ 20 mil. O teste de cinco posições iguais e um sexto entrante exige R$ 16.666,67 de vendas, não um novo aporte. Nenhuma posição elegível é integralmente liquidada para corrigir drift.

A decisão de venda usa apenas os preços disponíveis na data de venda. Na compra, após D+2, os preços então disponíveis podem produzir drift. Não há nova venda para eliminar esse drift. Entrantes têm prioridade; caixa residual só compra sobreviventes presentes na lista de compras do ano. Isso impede novas compras de empresas `INDETERMINATE` ou de B06 acima do teto. Sem déficit cuja compra seja permitida, o caixa permanece sem remuneração.

**B06/B06S:** o teto de yield de 6% limita compras novas; a permanência usa os filtros fundamentais B00. Não se implementou B1 nem saída compulsória pela simples ausência da lista de compras.

## Elegibilidade PIT

O arquivo `eligibility_evidence.json.gz` guarda os campos dos screeners históricos. Seleções corrigidas congeladas constituem PASS. Reprovações explícitas de escala, liquidez/endividamento, lucros, crescimento ou valuation com dados suficientes constituem FAIL. Em particular, F6 de 2021 é considerado com o capital resolvido e o valor calculado de P/L × P/VP; a ausência de um sufixo `_final` naquele arquivo não converte uma reprovação comprovada em lacuna.

Ausência de histórico de dividendos não é prova de distribuição zero. Lacunas e sucessores sem screener próprio ficam **INDETERMINATE**. A hipótese central mantém essas posições e sua base fiscal, sem autorizar novas compras delas. A sensibilidade `indeterminate_exit` vende essas posições na renovação, **sem reclassificá-las como FAIL**. Renomeações documentadas TRPL/ISAE e ELET/AXIA conservam a identidade; a elegibilidade de uma companhia resultante de combinação de negócios não é inventada a partir da antiga.

A base permite o diagnóstico econômico, mas a classificação setorial herdada e a cobertura integral de demonstrações PIT não foram recertificadas nesta missão.

## Apuração fiscal

O investidor simulado é uma pessoa física residente no Brasil, com uma carteira isolada e sem operações externas à simulação. O custo médio é calculado por posição; compras e reinvestimentos somam custo, vendas baixam o custo proporcional e conversões transferem a base. Não há imposto sobre valorização não realizada.

Aplicam-se 15% às operações comuns tributáveis. A isenção mensal de ações considera a soma das vendas ordinárias, até R$ 20 mil, e não se estende a BOVA11 ou direitos. Prejuízos são transportados prospectivamente; ganhos isentos não consomem esse saldo. ETF e direitos integram o conjunto comum tributável. Operações intradiárias oriundas do reinvestimento no mesmo fechamento de uma venda são casadas separadamente: todas tiveram ganho efetivamente zero nesta execução, sem lançar a compra nova no custo médio das ações antigas vendidas. O motor também separa a alíquota e o saldo de perdas de day trade. Fontes: [Receita — tributação em bolsa](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/bolsa-de-valores), [isenções](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/isencoes) e [compensações](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/compensacoes).

O imposto é reservado imediatamente após a apuração, antes das compras; o recolhimento é debitado no último pregão do mês seguinte. Essa data usa o calendário B3 como aproximação do calendário bancário. Não se debita IRRF novamente: a antecipação está contida no imposto total reservado. A planilha anual distingue competência e pagamento. Ganhos de resgates fora de bolsa são segregados e não compensam prejuízos comuns.

O cenário central é **IR_SOMENTE_VENDAS**. Os proventos continuam brutos, pela convenção do estudo, e não são indevidamente tratados como ganho de alienação. Uma coluna adicional desconta JCP identificados, usando 15% até 2025 e 17,5% em 2026. A **data-ex é proxy da data de crédito tributável** nessa coluna; não se afirma pagamento efetivo nessa data. Fluxos de competência 2025 pagos em 2026 exigiriam conciliação individual para uma declaração fiscal. A sensibilidade adicional atribui JCP a todo fluxo v9 sem classificação comprovada, como estresse, não como fato. Fontes: [Lei 9.249](https://www.planalto.gov.br/ccivil_03/leis/l9249.htm) e [LC 224/2025](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp224.htm).

O maior fluxo mensal modelado por ativo ficou abaixo de R$ 12 mil, sem atingir R$ 50 mil. Não se calculam tributos dependentes de outras rendas e operações pessoais não informadas. A nova regra de dividendos de 2026 não foi aplicada retroativamente. Fonte: [Lei 15.270/2025](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15270.htm).

## Eventos, direitos e bases provisórias

O adaptador chama o motor v6 original para os direitos aos proventos e as transformações de quantidades/caixa; adiciona a contabilidade fiscal, as ordens e a liquidação sem modificar esse motor. Reutiliza os 498 eventos Graham v11.2, os eventos nominais das quatro famílias reconstruídas em v13, BBSE3 documental v12 e os eventos herdados v8/v9 para os demais componentes Barsi. Não altera nenhum evento histórico congelado. Para os ativos Barsi ainda agregados, o dinheiro estimado do intervalo é reconhecido em um **balde contábil no final de junho**, ou antes da saída do código, e reinvestido uma vez. A data desse balde **não é uma data-ex ou pagamento documental**. Essa limitação afeta composição, reinvestimento e custo fiscal; o efeito foi calculado com ±20% desse caixa.

O reinvestimento dos eventos individuais preserva a hipótese ex-close, inclusive restituições de capital SYNE3. Portanto, D+2 realista para vendas não transforma os proventos em fluxos bancários inteiramente documentados. O caixa de proventos é aplicado uma vez e não reaparece como financiamento livre. Pagamentos posteriores ao corte podem estar antecipados pela convenção herdada.

Desdobramentos preservam o custo. Bonificações ITSA3 e PSSA3 usam o custo unitário declarado pelo emissor; outras bonificações sem valor fiscal comprovado recebem **adição zero de custo como proxy central**, nunca rotulada como custo legal certificado. A coluna `bonus_market_proxy` usa o preço nominal da ação no evento para mostrar sensibilidade do resultado à base faltante. Esse preço não é apresentado como custo atribuído pelo emissor. Fonte normativa: [Perguntas e Respostas IRPF 2026](https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/perguntas-e-respostas/dirpf/p-r-irpf-2026-v1-00-2026-04-23.pdf), itens de bonificações e desdobramentos; fontes dos custos efetivamente conhecidos em `structural_sources.json`.

A cadeia CPLE6→CPLE5→CPLE3, AESB3→AURE3, TRPL4→ISAE4, ELET3→AXIA3 e o resgate NEOE3 foram tratados explicitamente com preços nominais. O resgate NEOE3 usa R$ 34,02, com caixa em 15/05/2026. A alocação de custo nas parcelas em dinheiro de AES/Auren e CPLE7 continua provisória: a hipótese central preserva a base na ação sucessora e atribui base zero à parcela em dinheiro. O imposto separado dessas parcelas e do resgate NEOE3 é 15% dos ganhos positivos, sem conceder uma isenção fora de bolsa não certificada. `gcap_zero_bound` mede o efeito de zerar esse imposto; não afirma que a isenção é juridicamente devida. Falta documentação específica de alocação e enquadramento para transformar esses valores em apuração fiscal definitiva.

Foi necessário incluir a **bonificação em AXIA7**: 0,2628378881074 por AXIA3 com posição em 19/12/2025, entrega em 26/12, custo atribuído R$ 49,44. Ela afeta 112 caminhos principais e sua ausência excluiria uma posição real da liquidação final. A fonte é o aviso do emissor e o OC059/2025 da B3; a cotação SQLite de 30/06/2026 é R$ 53,01. Não se creditou o resgate PNR de AXIA5/6 às ações ON. É uma correção material restrita ao novo cenário, sem reabrir v13. Frações societárias permanecem na convenção fracionária do estudo.

Os direitos ITSA3 são inteiros, calculados por data-com em cada trajetória; não se escalou a carteira de R$ 10 mil. Venda comprovada em 24/08/2023 e 10/03/2025, liquidação em 28/08/2023 e 12/03/2025, reinvestimento líquido em ITSA3. Lotes de 100 usam ITSA1; sobras usam ITSA1F, cada qual com seu preço, quantidade e número de negócios COTAHIST. Em 2023 os fechamentos são diferentes: R$ 2,88 no padrão e R$ 3,30 no fracionário. Em 2025, R$ 2,55 em ambos. Um teste de 139 direitos verifica 100 padrão + 39 fracionários, sem presumir igualdade de preços. A base fiscal dos direitos recebidos gratuitamente é zero; vendas de direitos não usam a isenção de ações. Os arquivos históricos de prova e seus hashes estão preservados em `rights_quotes.json` e no checkpoint v11.2.

## Validação e comparação com o estudo anterior

O comparador independente executou o **motor v6 original e o adaptador novo**, com R$ 100 mil efetivos, direitos inteiros, sem imposto e sem a defasagem operacional, nas 18 combinações Graham de formação/regra. A diferença máxima foi inferior a R$ 0,000001. Também há paridade de trajetórias individuais com os eventos originais, testes de direito padrão/fracionário, imposto mensal, perda, isenção, base, caixa bloqueado, B2 mínimo e replay offline de todos os 372 resultados.

O BOVA11 mecânico no fechamento original reproduz R$ 184.512,1153 bruto, IR de R$ 12.676,8173 e R$ 171.835,2980 líquido. Com a compra operacional em D+1, resulta em **R$ 170.041,5408 líquido**. Confundir esses dois valores apagaria o efeito da data de execução.

Barsi não recebe uma calibração artificial para coincidir com os retornos agregados v13. `mechanical_bridge.csv` separa a mudança de data operacional da diferença residual do modelo contábil e dos eventos materiais acima. Barsi e Graham conservam níveis diferentes de cobertura documental; os rankings não equivalem a uma certificação de superioridade estatística.

As sete sensibilidades são alterações isoladas de hipóteses **nas mesmas políticas**, não carteiras novas: saída de INDETERMINATE, custo de bonificação nominal, imposto de resgates zerado, JCP identificado líquido, JCP desconhecido tratado como tributável, caixa v9 −20% e +20%. A faixa `one_at_a_time_min/max` agrega somente esses ensaios, não todas as combinações possíveis nem um limite matemático/jurídico da incerteza.

## Reprodução

Da raiz da branch, com Python 3 e as dependências da CI:

```bash
python scripts/simulate_ir_100k.py
python scripts/analyze_ir_100k.py
python scripts/validate_ir_100k.py
python -m pytest -q tests/test_graham_maintenance_v11.py tests/test_itsa_rights_v11_2.py tests/test_audit_v12.py tests/test_barsi_v13.py tests/test_ir_100k.py
```

O replay usa somente arquivos versionados. A extração original `python scripts/prepare_ir_100k.py` requer os CSVs do Codespaces, SQLite e COTAHIST locais; não baixa dados nem grava no banco. Os arquivos de entrada, sua procedência e os hashes estão em `research/ir_100k_inputs/`. As definições arquivadas v9 são lidas apenas para os dicionários literais necessários; o pipeline v9 não é reexecutado. Resultados, ledgers e sensibilidades estão em `research/ir_100k_results/`. A CI executa sem banco e sem consultas financeiras externas.

O arquivo `realized_sales.csv` detalha cada alienação por competência e ticker, separando quantidade, preço, receita, custo baixado, ganho, regime e motivo. Os 92 registros de direitos ITSA3 das trajetórias principais variam de 11 a 43 direitos; o caso de lote padrão é coberto pelo teste específico de 139 direitos.
