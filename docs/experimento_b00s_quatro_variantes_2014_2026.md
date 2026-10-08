# Experimento controlado — quatro versões da B00S (junho/2014–junho/2026)

**Estado:** especificação autorizada pelo usuário em 08/10/2026; resultados **ainda não calculados**. Trabalho isolado na branch `study/b00s-four-variants-2014-2026` a partir do checkpoint de atribuição do PR #3, commit `8d394e9ab563daebe43603a3e85f35f43c1402bc`. Não modificar, sobrescrever ou recalcular indiscriminadamente arquivos históricos do PR #3. PR deste experimento permanece draft, sem merge.

## Pergunta

Dada a mesma filosofia BESST, exigir concentração intencional em poucas ações, preço-teto ou qualidade financeira adicional melhora os **retornos ajustados pelo risco**, a consistência e a operacionalidade contra a B00S B2 original? Não escolher regras com conhecimento dos resultados futuros.

## Políticas obrigatórias comparadas

Todas compartilham a **mesma base B00S** de liquidez, empresa/ISIN, grupos BESST (bancos, energia elétrica, saneamento, seguros, telecomunicações), cinco exercícios históricos de lucro positivo e distribuições comprovadas, tratamento estritamente PIT, fechamento do último pregão de junho, **B2 de renovação seletiva com continuidade real dos pesos/ações**, eventos societários, proventos brutos reinvestidos, mesmo universo de negociação e dados de fonte congelados. Período de uma formação em junho/2014 e 12 janelas até junho/2026; preservação das referências originais `B00S B2`, `IBOV`, `R03 B2` e `BH padrão`.

### V0 — B00S atual, controle imutável

Todas as empresas que passam na B00S original, sem limite de quantidade, mesmo algoritmo B2 e ponderação setorial da etapa percentual. **As 12 rentabilidades existentes NÃO podem mudar; +402,1319722398% acumulados até junho/2026**. É uma referência, não uma nova simulação alternativa.

### V10 — B00S-10, máximo de duas empresas por setor BESST

Aplicar primeiro todos os filtros originais B00S e depois limitar a **até duas companhias distintas por setor**, total máximo de 10 companhias (poderá haver menos; na formação 2014 havia só uma seguradora elegível, portanto não inventar décima ação). Para escolher as duas na formação e preencher vagas posteriores, ordenar pela **maior liquidez histórica disponível em junho**: mediana de volume financeiro negociado nos mesmos 126 pregões pré-corte usados na regra B00S. Desempates: número de pregões com negócios, volume acumulado no semestre, ticker lexicográfico. Usar um único papel da companhia por CNPJ conforme o screener de B00S, sem somar ações de uma holding como candidaturas independentes.

Na revisão B2, **não vender incumbente que ainda é B00S PASS somente porque outra companhia se tornou mais líquida**. Incumbentes PASS ou INDETERMINATE mantidos ocupam suas vagas; vender apenas FAIL comprovado, e preencher vagas então abertas pela ordenação PIT. Se uma sucessão/troca de ticker mantém exposição econômica, não computá-la como vaga nova. Não forçar concentração em dez nomes se algum setor tiver apenas um ou nenhum nome.

### V06 — B00S + valuation, preço-teto de renda de 6%

Mesma B00S original, sem limite de nomes; **somente autorizar compras novas** quando o preço de fechamento no junho de seleção não exceder um preço-teto retrospectivo:

`DPA_normalizado_medio_5_exercicios / preço_de_mercado_no_corte >= 0.06`

DPA = dividendos e JCP brutos por ação da classe elegível, efetivamente conhecidos até a data de seleção, devidamente ajustados por splits, grupamentos, bonificações e alteração de unidade de negociação para a classe/corte de junho. Não misturar DPA de uma classe com cotação de outra nem contar eventos duas vezes. Calcular média de cinco exercícios completos, com proveniência e ausência explícita. **Reusar e confrontar a regra histórica B06S / script `build_selection.py` do pacote v9 disponível no Codespace**; se houver diferenças na convenção v9, publicar ponte e sensibilidade em vez de afirmar identidade metodológica.

Valuation é **limite de aquisição**: uma posição previamente comprada não é vendida exclusivamente porque o preço subiu acima do teto. Saídas continuam regidas por FAIL comprovado da B00S. Não empregar DY futuro, lucros pós-formação, proventos anunciados posteriormente ou preço máximo conhecido ex post. Sem dados suficientes para um candidato, tratar compra como `INDETERMINATE`, preservar o universo do controle e quantificar a exposição de entradas hipotéticas.

### VQ — B00S + qualidade financeira, filtros adicionais de compra

Mesma B00S original, sem limite de nomes. Exigir **para novas entradas**, com dados publicados até junho da formação:
1. Mediana do **ROE dos três exercícios completos mais recentes >= 10%**, obtida com lucro líquido e patrimônio líquido de perímetro compatível; patrimônio positivo em todos os três. Para contas dos bancos/seguradoras respeitar o plano contábil e o perímetro; não aplicar conceitos não comparáveis de AC/PC ou dívida líquida industrial aos bancos.
2. **Cobertura de distribuições nos cinco exercícios completos**: soma dos dividendos/JCP atribuídos aos acionistas da companhia <= soma dos lucros líquidos positivos comparáveis nos mesmos cinco exercícios, avaliando os valores em unidades monetárias e perímetro compatíveis. Separar direitos de classe das distribuições totais. Se o dado do total distribuído for insuficiente, marcar `INDETERMINATE`, sem supor payout zero.
3. **Atividades não financeiras (energia, saneamento, telecom)**: fluxo de caixa operacional positivo em pelo menos três dos cinco exercícios completos anteriores. Bancos e seguradoras ficam isentos apenas desse teste de CFO, que não é comparável entre instituições financeiras e indústrias.

São limiares ex ante para um **ensaio exploratório**, não uma alegação de regras originais de Barsi nem otimização retroativa. Se gerarem poucos nomes, documentar o resultado (não relaxar limiares em resposta à rentabilidade). Possível sensibilidade adicional de ROE 8%/12% só **depois** de publicar o caso primário, sem escolher a melhor parametrização por retorno.

A elegibilidade B00S original é independente desses filtros; **não vender uma posição herdada somente por reprovação posterior do filtro adicional de qualidade**, mas sinalizar deterioração. Venda compulsória apenas por FAIL B00S ou evento societário. Isso permite isolar o efeito de compras novas de qualidade, sem confundir com política de saída.

## Regras comuns de peso e implementação

- Formação inicial: distribuir 20% do índice entre cada um dos cinco setores **que tenham pelo menos uma companhia elegível**; quando algum setor estiver vazio, redistribuir seus 20% em pesos iguais entre os **demais setores elegíveis**, registrando a ausência. Dentro do setor, distribuir igualmente entre as empresas elegíveis. No controle preservar literalmente a regra existente.
- Renovação B2: usar pesos econômicos herdados, vender somente FAIL demonstrado no universo de base, financiar apenas compras novas com vendas e frações proporcionais necessárias, conservar NAV nas revisões, nunca equalizar a cada junho. No V10 a alocação de vagas é limitada; para V06/VQ o alvo de entradas usa os setores efetivamente elegíveis **para compra**, sem vender posições mantidas para forçar os mesmos pesos de formação.
- Se as condições de entrada não permitirem nenhum novo nome, manter as posições existentes. Se **não houver nenhuma posição elegível na formação inicial**, não inventar ações nem um rendimento de caixa: informar série não formada/ND e cenário explícito de ausência de investimento. Não substituir séries ND por 0%.
- Tratamento de ações que mudam ticker, classes, cisões, bonificações, direitos, OPA/resgate, proventos e reinvestimento deve reaproveitar os eventos aceitos do PR #3. Mantêm-se qualificados os mesmos limites documentais, não se refinam eventos irrelevantes.
- **Somente retorno total bruto percentual teórico**, sem patrimônio em reais, impostos, custos, aportes nem fluxo operacional de liquidação. Não usar informações futuras para seleção, desempate ou tratamento retrospectivo de dados ausentes.

## Entregas numéricas obrigatórias

1. `research/b00s_four_variants_2014_2026/results/annual_returns_pct.csv`: 12 períodos, V0/V10/V06/VQ e IBOV, opcional R03 e BH padrão como referências **congeladas**.
2. `cumulative_returns_pct.csv`: acumulado desde formação 2014 em cada junho; `consolidated_pct.csv`: retorno final, CAGR, média e mediana anuais, anos positivos/negativos, anos superiores ao IBOV, pior/melhor ano, desvio-padrão descritivo anual, maior drawdown entre **fechamentos anuais** (não diário), ranking final e consistência, mais rótulo de cobertura/limitações. Comparar diferença em p.p. vs B00S original e IBOV.
3. `holdings_by_june.csv`: para cada versão em cada junho, ticker, companhia, setor, status PIT, posição efetiva, peso inicial/final, retorno do papel no ciclo, contribuição p.p. e status de direitos/sucessoras. As contribuições do início de cada ciclo devem somar exatamente o retorno anual de cada versão.
4. `selection_decisions.csv`: todos os candidatos PASS no controle em cada junho, destino em V10/V06/VQ, razões de inclusão/exclusão/indeterminação, liquidez/ranking, DPA/preço-teto/DY ex ante, ROE/payout/CFO, documento e data de recebimento. **Nunca escolher por desempenho futuro**.
5. `turnover_by_year.csv` e `risk_concentration.csv`: giro unilateral em cada revisão, número de companhias, setores presentes, maior peso, participação das cinco maiores, concentração por empresa e setor; para avaliar se a redução de nomes melhora ou piora concentração.
6. `docs/checkpoint_b00s_four_variants_2014_2026.md`: resumo executivo, três tabelas lado a lado, metodologia, dados/limitações, decisões qualitativas, 2014 e 2026 detalhados; caso V06 ou VQ não seja comprovável, **não declarar vencedora**; comparar somente coortes compatíveis e apresentar resultados condicionais com rastreabilidade.
7. Planilha Excel compacta com resumos, 12 períodos, composições e rankings; manter os CSVs como fonte primária auditável.

## Validação e limite de esforço

- Reusar os screeners PIT e `stage1_resume.py`, `stage1_continuity.py`, `stage1_buyhold.py`, `stage1_attribution.py`, `cache/*.json.gz`, originais e trilhas do PR #3. Ler SQLite somente se indispensável e em `mode=ro`; preferir replay offline dos caches.
- Preservar SHA-256 de IBOV, Graham R03, BH padrão, B00S original, todos os artefatos do PR #3. O programa deste experimento não deve escrever ou modificar caminhos de `research/returns_2014_2026_*` nem `docs/checkpoint_returns_2014_2026_stage1.md`.
- Testes de formação inicial, duas empresas no máximo por setor V10, desempates PIT, preço-teto bruto ajustado sem look-ahead, ausência de venda somente por preço/qualidade, bancos vs não financeiros, filas sem dados, peso total = 100%, conservação de NAV, direitos sem dupla contagem, contribuições = retorno do índice, IBOV idêntico e reprodutibilidade offline.
- Priorizar **resultados de 12 janelas para as quatro estratégias** em vez de nova auditoria documental ampla. Não relaxar filtros depois de observar resultados. As lacunas capazes de mudar o ranking devem gerar sensibilidades, não preenchimento silencioso.
- Trabalho separado do PR #3, **sem merge**, sem executar etapa fiscal. Caso seja necessária alteração de política por indisponibilidade comprovada dos indicadores, registrar objeção com contagem exata dos nomes afetados antes de mudar a regra.
