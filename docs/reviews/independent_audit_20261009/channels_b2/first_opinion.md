# Primeiro parecer independente — canais de admissão e B2

Conclusão: **ISSUE / cobertura materialmente incompleta**, com **PASS no financiamento B2 ativo testado**. A ausência de PASS_REINVESTOR não demonstra ausência econômica de reinvestidoras. A ausência de REJECTED_EVIDENCED VQ também não demonstra que todos os negócios sejam bons. O pacote tem 229 decisões, 181 ND VQ e nenhuma prova pontual de CAGR real ajustado de LPA. Não recomendo conceder prêmios ou substituir ND por rejeição para produzir uma contagem diferente.

Este é o parecer integral inicial, preservado antes de feedback substantivo do coordenador. Os complementos de transporte disponibilizados durante a revisão foram apenas documentos/setores, IPCA até maio/2014 e registros do pregão do corte. Nenhum resultado de carteira, retorno futuro, notícia, GitHub, checkpoint ou caminho .pr4-work foi acessado. Há log explícito em `scope_access_log.json` e complemento em `scope_access_supplement.json`.

A revisão das 229 decisões é **triagem da coerência, metadados PIT, números e fundamentações congeladas**, não reauditoria dos 229 conjuntos de originais. Os juízos documentais próprios aprofundados limitam-se a TIMP3/2014 e SBSP3/2014. Foram verificados os hashes descomprimidos de 11 PDFs desses casos e lidas suas páginas textuais transportadas; 59 páginas referenciadas constam do anexo. `pdftotext` e bibliotecas PDF não estavam instalados: não houve reextração independente nem inspeção visual. Essa limitação não está escondida por um rótulo PASS.

Os metadados de recebimento, período e corte das 229 decisões não apresentaram referência posterior ao respectivo corte na verificação recursiva. Documentos de 2025 são usados apenas no julgamento de 2025. A conferência não valida a autenticidade de cada fonte sistêmica fora dos dois casos autorizados.

## Canal de reinvestimento

O gate pontual tem um caminho explícito para PASS_REINVESTOR: P/L na faixa, CAGR >=4%, payout <=80%, mediana ROIC/ROE >=IPCA conhecido+6 p.p. e solidez verdadeira. Uma falha necessária demonstrada basta para REJECTED_REINVESTMENT; um campo ausente não basta. A implementação não torna o canal pontual logicamente impossível, mas sua cobertura efetiva o torna inacessível neste conjunto congelado.

| Indicador preenchido | Decisões /229 | Limitação |
|---|---:|---|
| CAGR real de LPA ajustado | 0 | Nenhuma aprovação pontual de crescimento |
| Payout médio | 9 | Valores FRE; recorrência/reservas não certificadas automaticamente |
| Retorno mediano do capital | 79 | Predominam ROE de financeiras; ROIC não substituído por ROE |
| Solidez explícita | 1 | PSSA3/2025; não supre LPA/payout |

O inventário de candidatos à faixa de prêmio tem **21 companhia/cortes**: quatro pontos certificados no pacote, dois intervalos que intersectam a faixa e 15 P/L apenas mecânicos. São dois conjuntos conceitualmente diferentes: números calculáveis e preço econômico certificado. Não promover a faixa mecânica sem resolver o perímetro.

| Corte e companhia | Preço no pacote | CAGR / payout / retorno / solidez | Juízo de entrada |
|---|---:|---|---|
| TIMP3/2014 | 21,103353, ponto | ND / ND / ND / ND | ND congelado; ROIC diagnóstico adicional abaixo do mínimo, descrito adiante |
| PSSA3/2015 | 16,517408, ponto | ND / ND / **FAIL ROE** / ND | Reprova condição necessária; não precisa presumir falha do CAGR |
| TIMP3/2015 | 15,218968, ponto | ND / ND / **FAIL ROIC** / ND | Reprova condição necessária; pendências não viram aprovações |
| PSSA3/2025 | 16,114371, ponto | Intervalo cruza4% / ND / suficiente / PASS | ND; pode mudar admissão ao fechar as pontas e payout |
| CPFE3/2016 | [9,704719;18,245959] | ND / ND / ND / ND | Cruza15; pode admitir pela via madura se estreitar o limite |
| CSMG3/2025 | [0;17,154231] | ND / ND / ND / ND | Cruza15; o limite inferior0 é falta de teto de lucro, não preço zero |

Os outros 15 números mecânicos são CPFE3/2017, TRPL4/2017, VIVT4/2017, CPFE3/2018, TIMP3/2018, VIVT4/2018, EQTL3/2019, TBLE3/2019, VIVT4/2019, TBLE3/2020, TIET4/2020, VIVT4/2020, EQTL3/2021, EQTL3/2025 e VIVT3/2025. Inventário completo com cada indicador, fonte, recebimento, página, hash e motivo: `premium_inventory.json` e CSV correspondente.

PSSA3/2015: ROE13,9771473% <14,4730892%, diferença **−0,495942 p.p.**. A ponte congelada também documenta dois limites superiores anuais de13,9787038% e13,7219145%, ambos menores que o mínimo, inclusive após ajuste favorável do patrimônio. TIMP3/2015: ROIC11,5187974% <14,4730892%, diferença **−2,954292 p.p.**. São rejeições do requisito de preço com reinvestimento; não são REJECTED_EVIDENCED VQ. Não revalidei seus PDFs de2015, fora do escopo: o parecer confere a inferência da prova transportada.

PSSA3/2025 é especialmente material: intervalo de CAGR0,587165%–4,864760% atravessa4%. Os ROEs inferiores documentados e capital prudencial são suficientes nas respectivas condições, mas não removem essa incerteza e a falta de payout normalizado. Exigir mais lucro agregado, repetir aprovação de solidez ou usar um extremo favorável não fecha a prova.

Há duas limitações de implementação a explicitar antes de um futuro PASS_REINVESTOR. `bounded_valuation` só devolve PASS_MATURE/REJECTED_PRICE/ND, mesmo se a faixa inteira coubesse no prêmio; não recebe as provas de reinvestimento. Além disso, `calculate_metrics` suporta LPA, ROIC e solidez, mas não fornece ponte específica de payout normalizado; o valor-base é a média de percentuais FRE. Não constatei admissão errada atual, pois todas as provas pontuais de LPA faltam. Estes pontos não autorizam relaxamento nem mudança retrospectiva de regra.

## VQ: cobertura e natureza do ND

VQ tem **48 QUALIFIED_SATISFACTORY, 181 INDETERMINATE (79,04%), zero HIGH e zero REJECTED_EVIDENCED**. As 229 fichas estão ASSESSED, portanto o ND não é simplesmente ausência de criação da ficha. A economia do capital, alocação e governança respondem por grande parte das lacunas.

| Dimensão | ND /229 | Contrário com alerta econômico* | Lacuna sem alerta adverso adicional* |
|---|---:|---:|---:|
| Durabilidade | 6 | 6 | 0 |
| Economia do capital | 157 | 137 | 20 |
| Confiabilidade | 10 | 10 | 0 |
| Resiliência | 72 | 66 | 6 |
| Alocação | 166 | 143 | 23 |
| Governança | 116 | 96 | 20 |
| Total de dimensão/corte | 527 | 458 | 69 |

\* **Triagem interpretativa dos textos congelados**, não 458 falhas estruturais certificadas. “Alerta” identifica dívida/obrigações, queda/perda, choque, concessão ou conflito concreto, ainda com prova insuficiente da qualidade. “Lacuna” identifica pedido de demonstração/recorrência/comutatividade sem resultado adverso adicional estabelecido. Alguns casos dependem de pendência herdada e não de evento novo. Todos os527 continuam ND; não se contam como rejeições e os números não são um score. A classificação individual, seus motivos originais, revisão anual e fontes estão em `vq_dimension_inventory.csv`. Não há revisão de originais229 suficiente para certificar que **nenhum** alerta justificaria rejeição após investigação adicional.

| Ano | Bancos ND/total | Energia | Saneamento | Seguros | Telecom | ND total |
|---|---:|---:|---:|---:|---:|---:|
|2014|2/5|9/10|2/2|0/1|2/2|15/20|
|2015|2/5|8/9|2/2|0/1|2/2|14/19|
|2016|3/5|7/8|1/1|0/1|2/2|13/17|
|2017|4/5|6/7|2/2|0/1|2/2|14/17|
|2018|4/5|7/7|2/2|0/2|2/2|15/18|
|2019|4/5|7/7|2/2|0/3|2/2|15/19|
|2020|4/6|9/9|2/2|0/2|2/2|17/21|
|2021|3/5|9/9|3/3|0/2|1/1|16/20|
|2022|3/5|9/9|3/3|0/2|1/1|16/20|
|2023|3/5|8/8|3/3|0/2|1/1|15/19|
|2024|4/6|9/9|2/2|0/2|1/1|16/20|
|2025|4/6|8/8|2/2|0/2|1/1|15/19|

Totais: Bancos40/63 ND; Energia96/100; Saneamento26/26; Seguros0/21; Telecom19/19. O desequilíbrio setorial exige apresentar VQ como seleção condicionada à prova histórica e investigar possíveis exigências assimétricas, sobretudo retorno incremental e conflitos não resolvidos. O fato de Seguros ter21/21 aprovadas não demonstra automaticamente igual completude de prova em outros setores. O gate aceita REJECTED_EVIDENCED quando uma dimensão traz a marca e prova material; a ausência da categoria nas entradas, e não um ramo ausente do código, explica o zero.

Há textos contrários antigos preservados junto de revisões anuais mais atuais. Exemplo: descrições de seca/estrutura societária2014 reaparecem em cortes posteriores; devem ser lidas como antecedente histórico com a revisão corrente, nunca como certificação de que aquela observação pontual continua atual. Isso limita a legibilidade de contagens de alertas e recomenda campos de fato histórico/revisão efetiva separados, sem reescrever a evidência antiga.

## Juízo próprio TIMP3/2014

Preço/normalização reproduzidos com inflação conhecida: capitalização2.417.632.647 ×R$12,92 =R$31.235.813.799,24; mediana real R$1.480.135.108,02; P/L21,103353. O crédito fiscal extraordinário2010 deR$1.435,245mi, identificado em14958/g412 pp60–61, é deduzido deR$2.211,715mi: lucro ajustadoR$776,470mi. A mediana passa ao exercício2011. Não há escolha de preço posterior.

Fontes favoráveis próprias: 34545/g1653 pp38–39 mostram EBITR$2.439mi, investimentoR$3.871mi e caixa operacional livre positivoR$2.216mi, rede/escala73milhões de clientes e27,1% do mercado. 37056/g192 pp20–21 mostra dívida principalmente longa, hedge integral da parcela cambial e FCL negativo sazonal com FISTEL adicional. O FCL de um trimestre não demonstra falha estrutural. 34545/g1653 pp42–45 documenta conversão PN→ON0,8406, capital votante único, tag along, dois conselheiros independentes de nove e controlador67%.

Contrapontos materiais: 34545/g412 p24 mostra prejuízo InteligR$118,678mi; pp28–29, goodwill FiberR$1.159,648mi e testes apoiados em expectativas/sinergias. Ausência de impairment não certifica retorno incremental. O LPA2009 não está conciliado de modo suficiente com a conversão/classes para fechar CAGR real. A ponte integral de retorno sobre o capital adquirido continua pendente.

**ISSUE adicional de cobertura ROIC:** os próprios extratos2010–13 permitem aplicar a fórmula congelada de NOPAT/capital médio, sem dados2014/2015. Os retornos diagnósticos são11,802479%,11,518797% e12,346311%; mediana11,802479% <IPCA6,375074%+6pp=12,375074%. Omitir leases adicionais positivos favorece o retorno. Isso sugere **reprovação necessária VVAL pela mesma convenção**, em vez de simplesmente ROIC ausente. Não formalizo a troca antes de confirmar a normalização integral do capital econômico/tributário e NOPAT; ajustar patrimônio/ativo fiscal pode modificar a razão. A limitação não é preenchida por prova de outro corte. `case_calculations.json` contém todas as contas, IDs e datas usados. Impacto atual: pode mudar ND para REJECTED_REINVESTMENT, mas não abre compra nem rebaixa VQ automaticamente.

**Payout não é economicamente inexistente:** os quatro anos FRE podem ser completados documentalmente com2013: mínimoR$357,583mi (34545/g412 p59) e complementoR$485,722mi aprovado em10/04/2014 (37056/g193 p76). O diagnóstico de distribuições/lucros atribuíveis ajustados dá média54,559487%, abaixo80%. Isso não certifica todos os tratamentos de reservas/competência, mas demonstra que pelo menos parte do ND é transporte/conciliação, não ausência de retenção. Não aprovo o prêmio enquanto faltam as demais provas.

Governança merece objeção específica: 37056/g193 pp65–66 e a fonte cruzada36939/g193 pp3–5 documentam restrições ANATEL/CADE e medida de alienação ainda pendente; a fonte do grupo concorrente registra multaR$15mi sobre Telefónica e aprovações não obtidas. A sanção não prova abuso pela TIM. Porém a ficha chama o conflito “material, unresolved” e marca SAT: essa combinação exige explicitar por que as salvaguardas resolvem suficientemente o alerta segundo o protocolo, que veta alerta material não resolvido. Meu juízo conserva VQ ND e deixa essa dimensão **UNRESOLVED**; não converte o conflito em culpa provada. Atualmente não muda admissão, pois economia/alocação já são ND.

Principais originais:14958 recebido13/03/2012;34545 recebido13/02/2014;37056 recebido08/05/2014;36939 recebido08/05/2014. Hashes e recibos integrais constam de `original_receipts_hashes.json`. Exemplos:34545/g412 `156496399624cf2801d00a75d761378e5be1842d613d92d01fc66e648b81a95f`;37056/g193 `3758fd225f726bbc71e532f6e30a5fe28bd36560b1e7ba68219e9d8f9052f045`.

## Juízo próprio SBSP3/2014

Preço/normalização reproduzidos:683.509.869 ×R$23,55 =R$16.096.657.414,95; mediana realR$1.987.670.589,45; P/L8,098252. PASS_MATURE VVAL é compatível com a prova congelada; não exige dividend yield ou reinvestimento adicional.

Fontes favoráveis próprias:35848/g1653 pp10,39 mostram crescimento operacional multianual, menores perdas e EBITDA/resultado operacional crescente; não confundir EBITDA com ROIC. 35848/g412 pp21–22 explica CPC33 sem ajuste de DRE/DCF. 37910/g193 pp11,31–32 mostra caixaR$1.982,472mi, cronograma e covenants cumpridos. Os R$5.820mi contratados e não utilizados são vinculados a obras, não caixa livre. O diagnóstico de distribuição dos cinco lucros atribuíveis é31,459542%; baixo payout não é motivo de rejeição.

Alertas conhecidos:35848/g1653 pp16–17 e37910/g193 pp51–53 documentam vazão33→27,9m³/s, bônus30% após corte20% do consumo e postergação da revisão tarifária. O desconto sobre volume já reduzido implica, para o consumidor elegível com redução exata20%, fatura relativa0,8×0,7=56% da anterior; não se extrapola isso para toda receita. A empresa declarou não conseguir estimar precisamente o efeito. A revisão futura permitida não quantifica a ponte de volume/custo/retorno no corte. SãoLourenço traz compromisso de serviço25anos/R$6bi e investimentoR$2,21bi da SPE: entrega física futura e financiamento da SPE não demonstram capital gratuito para Sabesp.

Governança é material e específica:35848/g412 pp43–45 documenta negativa de reembolso pelo controlador, propostas não concluídas e ação judicial. R$1.412,479mi não reconhecidos incluem716,196mi controversos e696,283mi de reservatórios cuja transferência tinha risco jurídico provável. A obrigação atuarialR$1.780,268mi está reconhecida; não há ocultação contábil demonstrada. Salvaguardas formais e transparência não encerram o conflito econômico. Ao mesmo tempo, não estabelecem expropriação abusiva provada ou falha estrutural necessária.

Meu juízo: **VQ ND material sustentado** em economia, alocação e governança; resiliência SAT no corte é defensável com a liquidez/vencimentos observados. Aprovação requer ponte proporcional do choque já conhecido e dos compromissos, além de resolver ou limitar economicamente o conflito controlador/minoritário. Não exige certeza sobre toda chuva futura. Os originais não sustentam REJECTED_EVIDENCED automático por seca, payout baixo, expansão ou capital público.

Originais35848 recebido28/03/2014;37910 recebido15/05/2014. Hash35848/g412 `f78d1d7fb5802fe611f272ec3b3fc1413d1ec2d0e2f7c7e539df7e8bb22ab631`;37910/g193 `55420f288272c1d9cebd592e9860685f08042ace51fdc0bf9e0be24324d468a9`. Páginas, recibos e hashes restantes estão no anexo.

Em materialidade de admissão, a base2014 tem dois nomes Telecom e dois Saneamento: cada caso representa10% na referência setorial da base, calculada apenas pela regra do protocolo. Uma aprovação nova de VQ em cada setor poderia abrir dois setores inteiros da formação. Não estimei peso herdado, patrimônio real, retorno ou efeito em ranking.

## B2 — 18 exemplos sintéticos, nenhuma série real

O código ativo usa `reference_entries`/`renew_reference_entries`. O denominador é a união de linhagens únicas mantidas não FAIL e candidatas qualificadas, com referência20% por setor e sem normalizar pedidos. CNPJ equivalente impede compra de segunda classe; direitos/sucessoras compartilham a linhagem sintética e continuam fisicamente no NAV. A saída permanece por FAIL do ticker/posição herdada; não se cria FAIL por falta de qualidade ou preço.

| Exemplo (NAV sintético100) | Resultado |
|---|---|
| A100, entra C de setor vazio | A80/C20 |
| A100 ND, entra B do mesmo setor | A90/B10 |
| A95/D5 FAIL, entra C | A80/C20 |
| A50/D50 FAIL, entra C | A50/C50; saída excedente financia entrada |
| A60+direitoA10+D30, entram B/C | A42+direitoA7+D21+B10+C20 |
| Candidata de segunda classe/mesmo CNPJ já mantido | Sem compra nova nem dupla vaga |
| Nova base FAIL ou ND; duas classes novas; FAIL/PASS na mesma linhagem | Bloqueio explícito |
| Filtro de compra ND, base dos incumbentes PASS | Posições preservadas |
| Sem entrada, há FAIL | Só redistribuição compulsória proporcional |
| Todas FAIL, nenhum destino | Bloqueio; não inventa caixa |

PASS: conservação de NAV, financiamento sem aporte, redução proporcional apenas da diferença, incumbentes positivos, manutenção ND/ausência de status, representação CNPJ no callsite, ausência de venda forçada por filtro de qualidade. Registro completo em `b2_synthetic_tests.json`. Hash do código ativo confere com a política congelada: `a0aea3e0ce6ec2df8086d5bb795db81dee9f9181bf3a4a3b9c01b53ff06feafb`.

ISSUE de regressão potencial: `stage1_continuity.renew_b2` com A100 PASS e alvo novoC=1 produz A0/C100. A função genérica não protege esse sobrevivente. O callsite atual VVAL/VQ passa pelo financiamento corrigido e inclui verificação positiva; logo o exemplo não prova erro em negociação ativa atual. Deve permanecer coberto para impedir roteamento futuro incorreto. O teste sintético torna o problema concreto sem simular nenhuma série.

UNRESOLVED: `identities()` real e a construção da linhagem econômica não foram transportados no escopo. Os testes provam comportamento quando CNPJ/setor/linhagem já estão corretos; não certificam os mapeamentos reais, cisões, novos CNPJs ou reconciliação de status físico. Tampouco confirmam data de congelamento por GitHub: a política e o hash foram conferidos localmente, sem abrir o link.

Os arquivos de código e decisões originais foram preservados. O primeiro parecer, JSON correspondente e artefatos têm selamento em `first_opinion_lock.json`; qualquer resposta posterior deve ir a arquivo novo.
