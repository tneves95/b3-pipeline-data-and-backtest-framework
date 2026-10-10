# Segunda rodada: continuidade corrigida e primeiros retornos certificados

Execução de 10/10/2026 no PR #8, mantido draft e sem merge. O resultado passou de **zero para 24 trajetórias com retorno total nominal certificado: 15 de três anos e nove de cinco anos**, em três companhias. Uma das trajetórias certificadas termina com patrimônio inferior à metade do inicial. Não foram estimadas correlações, quantis preditivos, filtros vencedores ou carteiras.

O denominador continua sendo o universo histórico candidato: 2.588 observações companhia/data, 399 companhias e dois horizontes, totalizando **5.176 observações de retorno mapeadas**. Há ainda **94 observações de títulos elegíveis com identidade de companhia ausente ou ambígua**, preservadas separadamente em 188 observações título/horizonte. Elas não foram descartadas nem contadas como 94 companhias distintas.

## Correção e reconstrução executadas

`outcome_readiness()` usava a última cotação do primeiro semestre do ano de saída, mesmo quando ela ocorria depois do vencimento. Agora seleciona a última negociação com **data menor ou igual à data-alvo**, usando o ISIN histórico e o calendário observado nos originais. Mudança de ticker com o mesmo ISIN preserva a identidade; outro ISIN exige prova de conversão econômica. Amostras agregadas sem data de corte exata não servem para provar continuidade.

Nas coortes de 2018 e 2019, a disponibilidade próxima ao vencimento de três anos passou, respectivamente, de **1 para 205** e de **5 para 199**. Isso corrige a aferição de disponibilidade, sem transformar as observações em retornos certificados. O limiar diagnóstico de dez dias permanece o do protocolo; a certificação exige cotação no pregão de vencimento, sem preencher suspensões com preço antigo. Vencimentos em dias sem pregão usam a sessão efetivamente anterior à data-alvo.

Também foi detectada desordem cronológica dentro de arquivos originais de 2020 e 2022. A extração calcula o máximo de data admissível, independentemente da posição da linha. Testes cobrem essa condição, vencimentos em fins de semana, datas posteriores ao vencimento, mudança de ticker, reciclagem de ticker e troca de ISIN.

Foi criada `quote_overlay.sqlite`, exclusivamente local, com **74.015 registros diferenciais**: **66.518 negociações de ações ausentes do SQLite** e **7.497 negociações de direitos**. A comparação percorreu 1.064.168 registros originais de ações de 2014 a 2026; não encontrou divergências de identidade, fechamento ou fator de cotação nos registros existentes. A camada tem 17.678.336 bytes e consulta a base original em modo somente leitura, sem duplicá-la.

As negociações de AMER3 e de outras empresas em dificuldade foram reconstruídas a partir dos ZIPs locais, incluindo os BDI excluídos pelo parser anterior. O [layout oficial B3](https://www.b3.com.br/data/files/33/67/B9/50/D84057102C784E47AC094EA8/SeriesHistoricas_Layout.pdf) distingue, entre outros, o BDI de recuperação judicial. Recuperar preços não resolve automaticamente direitos de subscrição, trocas de ações ou sucessão econômica; essas pendências permanecem explícitas na matriz.

## Balanços e indicadores simples

Foram recuperadas **85 de 85 observações** cujo balanço anual exigido estava identificado, mas sem valores: 12 a partir dos originais já locais e 73 por solicitação dirigida aos IDs exatos da CVM. As 11 falhas iniciais foram resolvidas em uma única tentativa adicional dirigida. Não foram baixadas novas bases B3 nem arquivos anuais CVM indiscriminadamente.

A recuperação confere CNPJ, referência anual, versão, recebimento, escala monetária e hash. Não utiliza valores comparativos de documento posterior nem substitui a primeira versão por uma revisão futura. Cada observação usa um único perímetro contábil, consolidado quando disponível. Os oito campos não são obrigatoriamente preenchidos: os originais fornecem lucro e receita em 84 observações, EBIT em 77, FCO em 84, ativo e passivo circulantes em 80, patrimônio e ativo total em 85. As faltas restantes continuam nulas.

As respostas dos documentos exigidos somaram aproximadamente 757 MB, incluindo falhas e tentativas adicionais; ficaram temporariamente em `/tmp`. Retiveram-se apenas extratos financeiros e manifestos: os 73 ZIPs financeiros novos somam **3.236.740 bytes**, com hashes das respostas e membros de origem. Anexos integrais embutidos foram removidos. Os limites e as tentativas estão registrados localmente.

Os quatro indicadores simples foram calculados sem aguardar valuation, ROIC ou séries complexas:

| Indicador | Disponível em observações companhia/data, de 2.588 | Retorno certificado e indicador disponível, nos dois horizontes |
|---|---:|---:|
| Lucro anual positivo | 2.511 | 24 |
| Margem EBIT sobre receita positiva | 2.101 | 10 |
| FCO sobre lucro positivo | 1.532 | 10 |
| Ativo circulante sobre passivo circulante positivo | 2.146 | 10 |

Lucro não positivo não gera conversão em caixa aparentemente barata; denominadores inválidos e valores ausentes ficam explícitos. Bancos, seguradoras e setor desconhecido não entram nos três indicadores que exigem comparabilidade operacional. A [cobertura por coorte](published_round2/simple_indicator_coverage.csv) repete o painel para cada horizonte; por isso suas contagens não devem ser somadas como novas observações companhia/data.

## Reconciliação econômica e escopos certificados

Foram confrontadas **272 linhas de evidência FRE reutilizada com os arquivos originais locais**. O livro independente contém 3.025 registros econômicos, incluindo evidência reaproveitada com suas qualificações. A existência desses registros não certifica todo o livro.

| Escopo | Evidência que permite certificar a janela | Limite preservado |
|---|---|---|
| Bradesco PN, 2017 a junho de 2026 | Extração independente das tabelas históricas de caixa e bonificação do RI; calendário de direitos e verificação FRE | Caixa anterior a 2017 não coberto pela tabela revista |
| Cemig PN, junho de 2014 a dezembro de 2022 | Catálogo histórico com datas ex, valores brutos e bonificações; direito de 2017 e liquidação previamente auditados | Proventos posteriores ao catálogo não foram presumidos completos |
| IRB, formações a partir de junho de 2021 e vencimentos até 2025 | Catálogo primário sem novos direitos a caixa nessa janela; oferta pública de 2022 sem direito destacável de preferência; grupamento de 2023 reconciliado | Parcelas, cancelamentos e diferenças de caixa fora da janela continuam pendentes |
| Americanas | Preços e negociações de direitos recuperados | Direitos de 2022/2024 e linhagem BTOW/LAME/AMER ainda impedem certificação |
| Light | Evento de capital de 2021 reconciliado como neutro na quantidade líquida | Conflito de datas ex de caixa e direito de 2026 impedem certificação |

Fontes primárias: [remuneração Bradesco](https://www.bradescori.com.br/informacoes-ao-mercado/remuneracao-aos-acionistas/), [histórico Cemig](https://api.mziq.com/mzfilemanager/v2/d/716a131f-9624-452c-9088-0cd6983c1349/a2eb9f5f-37e1-8913-c1eb-c4281b5e23b2?origin=2), [caixa IRB](https://ri.irbre.com/servicos-aos-investidores/historico-de-dividendos-e-remuneracao-aos-acionistas/), [capital IRB](https://ri.irbre.com/servicos-aos-investidores/recompra-de-acoes-desdobramentos-e-subscricao/), [oferta IRB de 2022](https://api.mziq.com/mzfilemanager/v2/d/0d797649-90df-4c56-aa01-6ee9c8a13d75/815cf4c8-5e02-116d-7f9e-ac7f924bd297?origin=2) e [caixa Light](https://ri.light.com.br/divulgacoes-e-resultados/dividendos-e-jscp/). Cópias e hashes permanecem locais ou em manifestos; nenhum catálogo de eventos individuais B3 é publicado.

O retorno segue o protocolo congelado: caixa bruto reinvestido fracionariamente no fechamento da data ex, direitos destacados sem aporte novo e proventos simultâneos calculados sobre a quantidade com direito. Conversões preservam suas pernas econômicas; resgate compulsório deixa caixa nominal até o vencimento. Desaparecimento sem prova não equivale a perda total, aquisição não equivale a fracasso e ausência de eventos ignorados não constitui certificado. Os certificados vinculam companhia, classe, ISIN e janela, e têm livros locais de eventos aplicados e posições finais.

## Matriz final e impedimentos

**24 certificados, 3.574 não certificados e 1.578 censurados**, dos quais **955 por continuidade/eventos econômicos pendentes** e **623 por horizonte ainda não vencido**. Dos 4.553 horizontes calendariamente completos, apenas **0,527%** estão certificados. O calendário observado nos originais desta rodada termina em setembro de 2026.

| Coorte | Companhia/data | Certificados 3a | Não certificados 3a | Censurados 3a | Certificados 5a | Não certificados 5a | Censurados 5a |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2014 | 233 | 1 | 204 | 28 | 1 | 187 | 45 |
| 2015 | 230 | 1 | 196 | 33 | 1 | 180 | 49 |
| 2016 | 222 | 1 | 192 | 29 | 1 | 170 | 51 |
| 2017 | 233 | 2 | 198 | 33 | 2 | 171 | 60 |
| 2018 | 240 | 2 | 200 | 38 | 1 | 171 | 68 |
| 2019 | 241 | 2 | 191 | 48 | 1 | 173 | 67 |
| 2020 | 262 | 1 | 210 | 51 | 1 | 182 | 79 |
| 2021 | 304 | 2 | 249 | 53 | 1 | 206 | 97 |
| 2022 | 318 | 2 | 258 | 58 | 0 | 0 | 318 |
| 2023 | 305 | 1 | 236 | 68 | 0 | 0 | 305 |

As 94 observações de títulos com identidade pendente aparecem em coluna própria no [CSV da matriz](published_round2/return_coverage_by_cohort.csv). A [matriz de causas](published_round2/remaining_causes_by_cohort.csv) distingue `MAPPED_COMPANY_OBSERVATION` de `UNRESOLVED_SECURITY_OBSERVATION`. As contagens de causas se sobrepõem e não devem ser somadas como exclusões distintas:

| Causa remanescente | Observações de retorno atingidas |
|---|---:|
| Catálogo completo de eventos ainda não reconciliado | 4.487 |
| Saída/suspensão exige linhagem econômica | 849 |
| Evento material ignorado ainda sem resolução | 164 |
| Horizonte não vencido | 623 |
| Escopos de caixa ainda incompletos: Light / Cemig / IRB / Bradesco | 18 / 8 / 8 / 6 |
| Americanas: direitos e sucessão | 2 |
| Identidade de formação ausente/conflitante, unidade título/horizonte | 188 |

Os quatro indicadores já têm valores calculados, mas **as relações preditivas permanecem suspensas**. A amostra certificada tem apenas três companhias, setores concentrados e continuidade econômica pendente no universo. Esta rodada adota uma trava operacional explícita: cobertura certificada de pelo menos 95% no total e em cada coorte/horizonte completo, pelo menos 100 companhias distintas, nenhuma censura econômica conhecida nem identidade elegível pendente. Esses requisitos são verificáveis antes de estimar filtros; não foram otimizados em função de correlações. Seu cumprimento será necessário, mas não dispensará as demais auditorias e condições de inferência do protocolo.

Ordem objetiva de resolução:

1. Resolver as 94 identidades históricas elegíveis e os conflitos de companhia/classe, preservando títulos extintos e sem usar o cadastro atual como identidade histórica.
2. Tratar as 955 trajetórias com censura econômica: começar pelos direitos e sucessões Americanas, datas ex e direito Light, parcelas/cancelamentos IRB fora do escopo, e saídas com resgate/conversão documentados. ENBR exige conferir o caixa compulsório e o catálogo completo até a saída. Priorizar os 164 horizontes afetados por eventos materiais já identificados; não apagar perdas para liberar estimação.
3. Ampliar catálogos completos de caixa e capital usando primeiro os originais já auditados. Os 4.487 impedimentos de catálogo são a maior barreira quantitativa; a expansão precisa cobrir companhias em dificuldade e extintas, setores e todas as coortes, evitando selecionar somente casos fáceis ou sobreviventes.
4. Certificar também IPCA e Ibovespa nas mesmas datas efetivas. Os 24 certificados atuais são nominais; retornos reais e relativos ainda não têm certificado. A recuperação adicional de indicadores complexos não bloqueia o início dos quatro testes simples quando as condições de cobertura forem satisfeitas.
5. Aplicar então os testes individuais e filtros simples congelados, com dependência por companhia/tempo, cortes temporais e multiplicidade previstos no protocolo. Os 623 horizontes não vencidos aguardam observação e não são falhas econômicas.

## Reprodução, publicação e preservação

Os 14 MB anteriores, suas 18 tabelas detalhadas, gráfico e manifestos continuam intactos. O SHA-256 do SQLite antes/depois permanece `0ab5d487ec8e6efe7c995a7bec5f0ae4e6602fc734dfbd4bc96e7cc4c82c3211`. Foram revalidados os 22 hashes do inventário de entradas imutáveis da continuação anterior. Nenhuma seleção ou resultado Graham/Barsi foi alterado.

A execução final registra 176 arquivos locais de evidência, com 28.853.656 bytes, além do manifesto da rodada. A publicação inclui somente sete arquivos agregados e manifestos de proveniência, código, documentação e testes. Trajetórias, preços, posições, eventos e originais permanecem locais e ignorados pelo Git; consulte a [auditoria de publicação](PUBLICACAO_RODADA2.md).

O ambiente testado está em [requirements.txt](requirements.txt). Para conferir esta execução sem coletar nada novamente:

```bash
python -m research.fundamental_multipliers_pilot.publish_round2
python -m pytest -q tests/test_fundamental_multipliers_audit.py \
  tests/test_fundamental_multipliers_returns.py \
  tests/test_fundamental_multipliers_publication.py \
  tests/test_fundamental_multipliers_round2_publication.py
```

Para reproduzir outra execução, use um diretório novo. Requer os originais locais licenciados, o inventário preliminar verificado e os arquivos dos estudos anteriores referenciados nos manifestos:

```bash
RUN=research/fundamental_multipliers_pilot/local_only/reproduction_round2
python -m research.fundamental_multipliers_pilot.filings --output "$RUN"
# Opcional, somente os IDs identificados como ausentes; não baixa bases anuais.
python -m research.fundamental_multipliers_pilot.fetch_filings --output "$RUN" \
  --max-documents 73
python -m research.fundamental_multipliers_pilot.fetch_sources --output "$RUN/sources"
python -m research.fundamental_multipliers_pilot.round2 --output "$RUN" --build-overlay
python -m research.fundamental_multipliers_pilot.publish_round2 --local "$RUN" \
  --output /tmp/b3-fundamentals-round2-aggregate-reproduction
```

A coleta é opt-in e limitada. Se houver falhas, `filings` pode atualizar a lista antes de uma tentativa dirigida aos mesmos documentos, sempre antes de fechar o manifesto. Depois de fechado, os comandos de cálculo/coleta recusam sobrescrever o checkpoint. A exportação verifica todos os hashes e os esquemas públicos. **32 testes passaram**, incluindo regressões econômicas e a trava que impede usar somente sobreviventes, mesmo com alta cobertura aparente.
