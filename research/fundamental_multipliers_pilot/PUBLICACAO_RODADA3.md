# Auditoria da publicação da terceira rodada

Escopo autorizado: atualizar a branch do PR #8 e mantê-lo draft, sem merge. Publicam-se código, testes sintéticos, documentação, resultados estatísticos próprios agregados e manifestos. A publicação não contém registros individuais de negociação, trajetórias individuais, catálogos de eventos B3, originais CVM/RI, credenciais ou arquivos pessoais.

## Arquivos e tamanhos

Os **16 arquivos de `published_round3/` somam 384.431 bytes**, conferidos antes do push. A lista individual, tamanho e SHA-256 estão em [publication_review_round3.json](publication_review_round3.json). O maior agregado tem 96.498 bytes. Além deles, entram somente `round3/`, `protocol_round3.json`, o teste sintético da rodada e os três documentos desta rodada. O inventário do conjunto adicionado ao Git é conferido novamente antes da publicação.

Os agregados incluem cobertura por coorte/setor/porte/situação econômica, causas, suficiência, indicadores, filtros, combinações, partições temporais, sensibilidades, classificações ambíguas e verificações do cálculo. Há schemas exatos e rejeição de colunas de preços, volume, ticker, ISIN e CNPJ nas tabelas. Identificadores individuais também são rejeitados quando disfarçados como rótulos de dimensão. Resumos de retorno com menos de cinco janelas ou três emissores são suprimidos; contagens permanecem. Nenhuma companhia desaparece do cálculo local por essa supressão editorial.

Os scripts contêm definições e referências documentais necessárias à reprodução, inclusive a mecânica de capital obtida do ITR primário; não contêm cotações históricas extraídas. Os testes usam dados sintéticos. Manifestos de fonte publicam nomes, tamanhos e hashes, sem conteúdo das bases.

## Evidências que ficam locais

- Os 14 MB da primeira rodada, os dados e originais da segunda, o overlay de cotações e todos os checkpoints anteriores.
- `local_only/round3/`: painel contábil/estatístico por companhia, preços consultados, livro de eventos, estimativas individuais A/B/C, proveniência detalhada e amostra de validação.
- O único PDF novo dirigido, 960.704 bytes, preservado localmente. Nenhuma cópia integral ou extrato do PDF é publicado.
- Inventários de retomada em `local_only/session_recovery_round3_20261010/`. Não há cópia da base SQLite nem pacote duplicado de originais.

Esses materiais não entram no staging. A branch privada `local/fundamentals-multipliers-evidence-20261009` permanece local. Não será feito push desse ref nem inclusão do commit privado na história pública.

## Conferências executadas

**52 testes passaram**, incluindo as regressões de continuidade da segunda rodada e as novas de perdas reais, grupamentos, proventos simultâneos, conversões, versões de balanços, decisões com campos indefinidos, reamostragem por companhia, ambiguidade dos limiares e bloqueio de dados individuais na publicação.

O cálculo completo é offline e verifica os 413 artefatos/fontes anteriores antes e depois. O SQLite original continua imutável e com o hash registrado no relatório. Estatísticas podem ser refeitas a partir do painel salvo; publicação em `/tmp` permite comparar os agregados sem alterar a revisão canônica.

Nenhuma inferência ampla é autorizada pelos números publicados: o [relatório](RODADA3.md) distingue associação condicional, representatividade insuficiente e validação. O [roteiro de retomada](RETOMADA_RODADA3.md) contém comandos e estado necessário após a expiração da janela do Codespace.
