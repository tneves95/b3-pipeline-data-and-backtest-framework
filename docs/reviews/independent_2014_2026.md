# Parecer independente — decisões B 00 S V2 de 2014–2026

Checkpoint de auditoria sobre o baseline `229e60035d89c524eb274a1adb28207d67011087`, conforme a [revisão do coordenador de 09/10/2026](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6081269068). A certificação metodológica final permanece pendente. Este documento acrescenta juízos de auditoria; não altera decisões, critérios, originais, carteiras ou resultados congelados. PR #4 permanece draft, sem merge.

## Independência e alcance

Três agentes novos, com `fork_turns=none`, examinaram pacotes separados de decisões e fontes históricas. Não receberam tabelas de retornos futuros, comentários contendo rentabilidades, pareceres anteriores ou contexto de implementação da agente executora. O revisor dos casos materiais selou 2014 antes de abrir 2025. Foram fornecidos oito casos, 137 seções originais em 123 pares documento/grupo distintos, com recibos e hashes; isso descreve o pacote, não uma alegação de leitura integral de todas as páginas.

A amostra é dirigida pelo coordenador, não aleatória: IRB 2019; Porto 2014/2025; Bradesco 2014; Copasa 2014/2025; TIM 2014; Sabesp 2014. A triagem dos 229 registros quantifica cobertura e coerência; não certifica todos os respectivos originais. Os revisores declaram seu escopo efetivo nos pareceres e logs. Há separação de contexto e restrição de leitura por instrução, em filesystem compartilhado; não se declara isolamento de sistema operacional ou auditoria humana externa. A raiz, que conhecia os resultados, conserva os pareceres selados sem reescrever julgamentos para obter um resultado desejado.

`PASS` significa decisão examinada sustentada, inclusive um ND corretamente mantido; `ISSUE`, problema demonstrado de fundamentação/cobertura/implementação; `UNRESOLVED`, questão material ainda sem prova suficiente. Esses rótulos de auditoria não substituem categorias V2. A materialidade é a capacidade de afetar fundamento, admissão ou financiamento segundo as regras existentes; as distâncias aos limiares abaixo não criam filtros novos.

## Decisões e efeitos potenciais

| Caso | Decisão congelada VVAL / VQ | Parecer | Severidade e impacto potencial |
|---|---|---|---|
| IRBR3/2019 | REJECTED_PRICE / QUALIFIED_SATISFACTORY | PASS; pendência documental pontual LOW | Suporta admissão VQ e exclusão por preço; riscos econômicos detalhados, sem reclassificação retrospectiva |
| PSSA3/2014 | PASS_MATURE / QUALIFIED_SATISFACTORY | PASS | LOW; P/L 14,1690, folga real R$ 40,273 milhões até 15; afeta setor inteiro na formação |
| BBDC4/2014 | PASS_MATURE / QUALIFIED_SATISFACTORY | UNRESOLVED para VVAL; VQ sustentada com ressalva | HIGH; ponte BRGAAP→IFRS insuficiente e 25% da formação VVAL potencialmente dependentes |
| CSMG3/2014 | PASS_MATURE / INDETERMINATE | PASS | MEDIUM; P/L máximo 11,2361; ND específico de economia/alocação, sem rejeição estrutural comprovada |
| PSSA3/2025 | INDETERMINATE / QUALIFIED_SATISFACTORY | PASS com limites e clarificações | MEDIUM; prêmio continua sem prova cumulativa; separar capital regulado e holding |
| CSMG3/2025 | INDETERMINATE / INDETERMINATE | PASS com limites | MEDIUM; P/L máximo 17,1542 não comprova 15; CAPEX e obrigação BH pendentes |
| TIMP3/2014 | INDETERMINATE / INDETERMINATE | ND geral sustentado; ISSUE/UNRESOLVED específicos | MEDIUM; ROIC diagnóstico e justificativa de governança exigem revisão, sem abrir admissão atual |
| SBSP3/2014 | PASS_MATURE / INDETERMINATE | PASS | MEDIUM; P/L 8,0983 e ND econômico documentado; eventual qualificação abriria saneamento VQ |

Os pesos da formação 2014 abaixo são obtidos exclusivamente das decisões e da regra setorial original, sem rentabilidades: Bradesco 25% VVAL/11,1111% VQ; Porto 25% VVAL/33,3333% VQ; Copasa 12,5% VVAL. A eventual contestação de uma admissão inicial afeta também a composição e redistribuição entre setores. Nenhum efeito em retorno, ranking ou carteira alternativa foi calculado nesta etapa. Nos cortes posteriores, ND no filtro de compra mantém incumbentes conforme B2; uma revisão de parecer não autoriza venda retroativa.

### IRBR3/2019 — decisões corroboradas, contrapontos aprofundados

O novo revisor sustentou as seis dimensões SAT com prova afirmativa de franquia, resultado, auditoria atuarial, capital e fiscalização. Contrapôs a expansão exterior e os riscos de estimativas/cedentes relacionados. Não encontrou prova PIT de fragilidade estrutural ou lacuna material suficiente para obrigar ND/rejeição. A margem bruta externa caiu 48,4% em 2018, embora a margem total e a externa corrente continuassem positivas; os recebimentos não demonstram conversão da mesma coorte estimada. Os cálculos e as páginas originais estão no [parecer selado](independent_audit_20261009/irbr_2019/first_opinion.md).

A rejeição por preço foi reproduzida pela mesma mediana de cinco exercícios: teto real R$ 1.201,127 milhões; capital ON sem tesouraria R$ 30.575,917 milhões; P/L mínimo 25,456017, acima 25. A folga é 1,824%; uma despesa extraordinária elegível adicional de aproximadamente R$ 20,660 milhões nominais 2017 poderia começar a invalidar essa prova, se demonstrada e ainda não devolvida no teto. Isso não constitui erro identificado. A PN especial não recebeu cotação ON. Fontes 67429/412 pp 28–31/85–88,71429/412 pp 21–23/74–76,82684/193 p 58; recebimentos 31/07/2017,08/02/2018 e 06/05/2019.

Permanece sem ponte a diferença de provisões entre narrativa do auditor e DFPv4: R$ 17,142 milhões, 0,195% das provisões e 0,829% do excedente prudencial de dezembro. `UNRESOLVED/LOW` documental, sem efeito demonstrado sobre admissão. Fontes 81090/1654 unidade 2 e 81090/412 pp 5/54, recebidas 08/03/2019. Os retornos ou fatos posteriores não integraram o julgamento. A revisão anterior de 2019 foi verificada por bytes e cronologia Git e permanece preservada; seus metadados antigos, isoladamente, não permitem reconstruir todo o acesso do antigo agente.

### Bradesco/2014 — pendência material do piso de lucro

O [parecer 2014 selado](independent_audit_20261009/material_cases/material_review_2014_sealed.md) registra: a aritmética do limite superior 14,942658 confere, mas a folga do piso real é só R$ 34,599 milhões, equivalente a R$ 29,870 milhões nominais 2011, ou 0,3823%. O original BRGAAP registra crédito e provisão de R$ 2.911,634 milhões neutralizados nesse perímetro; falta ponte quantitativa para o lucro atribuível IFRS que sustenta o piso. A publicação de 08/02/2012 exclui explicitamente as demonstrações IFRS e declara qualitativamente diferenças não significativas. Os demonstrativos IFRS examinados não individualizam a mesma neutralização. Isso deixa `UNRESOLVED/HIGH` a certificação de nova compra VVAL, sem comprovar preço verdadeiro acima 15 nem negócio ruim.

Pendência dirigida: reconciliar lançamentos 2011 por entidade/evento entre BRGAAP e IFRS, tributação, minoritários e reapresentações, com fontes divulgadas até 30/06/2014. Fonte externa pp 25/28–29,15827/412 pp 81/84/116–118/125 (30/03/2012),25736/412 pp 83/128–129 (28/03/2013),35965/412 pp 88/117 (31/03/2014). Não remover perdas para fabricar piso. A questão atinge 25% da formação VVAL; o parecer de VQ satisfatória permanece sustentado com ressalva sobre normalização exata.

### Porto e Copasa/2025 — ND sustentados e limites atuais

[Revisão independente 2025](independent_audit_20261009/material_cases/material_review_2025.md): Porto mantém VVAL ND e VQ satisfatória; Copasa mantém ND nas duas variantes. O revisor recompôs os fatores IPCA, capital por ações emitidas/cotações próprias, âncora da mediana Porto R$ 2.214.889.406,24 e piso de mediana Copasa R$ 620.003.211,01. O preço Porto 16,1144 não autoriza prêmio sem CAGR/payout certificados; o limite Copasa 17,1542 não demonstra preço efetivo acima 15.

Clarificação rastreada do capital Porto (147187/192 p 29, recebido 09/05/2025): o total PLA 11,401 bi / requerido 7,330 bi / suficiência 4,071 bi está correto como agregado do gráfico. A parcela excedente nas reguladas é R$ 667 milhões em seguros mais R$ 499 milhões em financeiras = R$ 1,166 bilhão; R$ 2,905 bilhões pertencem à holding, sem requerimento próprio mostrado. Não descrever os R$ 4,071 bilhões inteiros como excedente já localizado nas operadoras reguladas. A decomposição mantém suficiência positiva e não altera a decisão congelada. A mudança de estimativa de comissões na saúde acrescenta R$ 19,3 milhões ao lucro do 1T25 e exige ressalva de comparabilidade, junto à piora do resultado técnico de seguros.

Copasa: o auditor Grant Thornton apresenta opinião sem modificação, com ênfase material na obrigação judicial final de repavimentação BH, cujo custo/escopo não era confiavelmente estimável. A recuperação tarifária esperada não é reembolso garantido. A conclusão VQ ND continua sustentada por economia de CAPEX/alocação sem prova suficiente; transparência e comitê de auditoria atuais não eliminam o risco econômico. Fonte 145717/1654 unidades 1–2, recebido 24/03/2025;145717/412 pp 23–24/38–39/50/64–67;147606/192 e 193, recebido 14/05/2025. Os pisos conservadores não são lucros recorrentes pontuais. Fontes de governança e qualidade têm limites registrados, incluindo ausência de anexo independente de auditor 2024 Porto no pacote.

## Reinvestidoras — zero observado não é zero econômico

[Inventário completo](independent_audit_20261009/channels_b2/premium_inventory.csv): quatro P/L pontuais tratados como certificados no baseline, dois intervalos que intersectam 15–25 e 15 números somente mecânicos. A nova auditoria não transforma essas categorias do baseline em certificação geral. Os intervalos CPFL 2016 [9,704719;18,245959] e Copasa 2025 [0;17,154231] também cruzam 15; podem depender de fechar a via madura. O limite inferior 0 de Copasa exprime ausência de teto de lucro, não estimativa de preço zero.

| Ponto na faixa 15–25 | P/L baseline | Condição necessária / prova faltante |
|---|---:|---|
| TIM 2014 |21,103353|CAGR, normalização do capital/NOPAT e payout ainda não integralmente certificados; diagnóstico ROIC abaixo do mínimo|
| Porto 2015 |16,517408|ROE 13,9771% abaixo 14,4731%: falha necessária na prova congelada|
| TIM 2015 |15,218968|ROIC 11,5188% abaixo 14,4731%: falha necessária na prova congelada|
| Porto 2025 |16,114371|CAGR real por ação 0,5872%–4,8648% cruza 4%; payout normalizado pendente|

Cobertura pontual: CAGR ajustado 0/229; payout 9/229; retorno mediano do capital 79/229; solidez explicitamente registrada 1/229. Há provas por limites, como Porto 2025, portanto zero pontos não significa ausência de qualquer análise de crescimento. As duas falhas necessárias 2015 foram conferidas como inferência sobre a prova congelada; não se reauditaram seus PDFs neste novo lote. O canal pontual existe no código, mas a cobertura cumulativa não permite admissão observada.

Limitações antes de eventual primeira admissão: `bounded_valuation` não recebe provas cumulativas do prêmio e só retorna madura/preço/ND; não há ponte específica de payout normalizado em `calculate_metrics`, cujo valor-base vem do FRE. Não foi demonstrada admissão errada atual por esses limites. Não alterar 15/25,4%,20%,IPCA+6 pp nem solidez.

## VQ — ausência de rejeições e assimetria de cobertura

São 48 QUALIFIED_SATISFACTORY e 181 ND (79,04%), zero HIGH e zero REJECTED_EVIDENCED. Todas as 229 fichas estão ASSESSED. Os principais ND de dimensão são alocação 166, economia do capital 157 e governança 116. A categoria de rejeição é alcançável no código; nenhuma entrada traz a combinação de classificação e prova material exigida. O zero não prova erro nem demonstra que nenhum negócio mereceria rejeição após investigação.

| Setor | ND / decisões | Parcela ND |
|---|---:|---:|
| Bancos |40/63|63,49%|
| Energia |96/100|96,00%|
| Saneamento |26/26|100,00%|
| Seguros |0/21|0,00%|
| Telecom |19/19|100,00%|

A [distribuição por setor/ano](independent_audit_20261009/channels_b2/vq_coverage_sector_year.csv) concilia os 229 registros. A triagem textual dos 527 ND de dimensão separa 458 com algum alerta econômico e 69 lacunas sem adverso adicional; não são 458 falhas estruturais certificadas. Confirmação fundamentalista própria se restringe à amostra. Nenhuma reprovação deve ser fabricada para corrigir a distribuição. Os resultados VQ continuam condicionais à prova documental, aos setores efetivamente admitidos e ao drift B2.

TIMP 2014: ROIC diagnóstico pela convenção congelada 11,802479%, abaixo do mínimo 12,375074%; confirmar normalização do capital tributário e NOPAT antes de converter ND em rejeição necessária VVAL. Payout diagnóstico reconstruível 54,56%, portanto falta de preenchimento não demonstra inexistência de retenção. Governança SAT convive com justificativa de conflito material não resolvido; explicitar mitigação ou revisar a dimensão em ato separado. A admissão atual já é bloqueada por outras dimensões ND. Sabesp 2014: ND fundamentado pelo choque hídrico, tarifa/CAPEX e conflito econômico com o controlador, sem prova de falha estrutural necessária. Referências detalhadas e contrapontos no [parecer dos canais](independent_audit_20261009/channels_b2/first_opinion.md). O [adendo de reextração direta](independent_audit_20261009/channels_b2/direct_reextraction_addendum.md) conferiu 15 páginas críticas em cinco PDFs e resolveu a limitação técnica inicialmente declarada, sem divergência de números nem alteração dos juízos.

## B2, verificações e próximos atos

`PASS` para o financiamento ativo nos 18 cenários sintéticos independentes: conserva NAV, mantém incumbentes não FAIL positivos, não compra classe duplicada e não vende por ND no filtro novo. O exemplo com a função genérica antiga que zerava sobrevivente identifica risco de regressão de roteamento, não erro demonstrado no callsite atual. Mapeamentos reais de CNPJ/linhagem não foram reauditados nessa amostra; permanece o limite dos eventos aceitos do PR#3. [Casos e resultados](independent_audit_20261009/channels_b2/b2_synthetic_tests.json).

Verificações locais aprovadas:3.497 arquivos preexistentes byte-idênticos, incluindo os 840 arquivos do PR #3; protocolo V2 idêntico a `7fea064`; todos os 137 originais transportados com hash correto e recebimento pré-corte;45 arquivos de pareceres/anexos selados preservados. Inventários conciliados em 229 decisões,60 células setor/ano e 360 contagens de dimensão por setor/ano.18 testes sintéticos B2 passaram;15 páginas críticas dos dois ND foram reextraídas diretamente sem diferença numérica. Nenhum backtest foi regenerado nesta auditoria. O baseline já tinha 222 testes e CI verde; não se declara essa suíte como uma nova execução local deste lote.

Os pareceres iniciais, adendos, cálculos e logs originais são conservados com hashes em [sealed_reports.json](independent_audit_20261009/sealed_reports.json). Inventários maiores foram apenas comprimidos sem alteração de conteúdo. [Manifesto cego](independent_audit_20261009/blind_packet_manifest.json) e [método/cronologia](independent_audit_20261009/review_method.json) documentam fontes, complementos pontuais e limites da independência.

O gate permanece aberto para a ponte IFRS Bradesco e as limitações materiais de cobertura. Priorizar essas pendências dirigidas e a prova cumulativa dos pontos de prêmio, sem nova campanha ampla nem reescrita do baseline. Qualquer retificação ou cenário que afete seleção exige ato rastreado e separado; não foi executado neste checkpoint. O estudo de coortes adicionais permanece posterior ao gate: os 12 ciclos da formação 2014 não são 12 formações independentes.
