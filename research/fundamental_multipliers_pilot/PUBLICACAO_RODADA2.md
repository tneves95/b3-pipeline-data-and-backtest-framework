# Auditoria de publicação da segunda rodada

Esta atualização do PR #8 publica scripts, testes sintéticos, documentação e resultados próprios agregados. A branch continua draft, sem merge. O escopo segue a autorização do usuário: dados B3 individuais e material com redistribuição incerta ficam locais.

| Conteúdo | Decisão |
|---|---|
| Código, dependências, testes e relatório da execução | Publicar |
| Contagens de certificação, censura, causas e disponibilidade por coorte | Publicar |
| Contagens da reconstrução por ano | Publicar |
| Nomes relativos, tamanhos, hashes e URLs oficiais de proveniência | Publicar |
| SQLite original e camada diferencial de cotações | Manter local |
| Matriz individual de retornos, indicadores e identidades históricas | Manter local |
| Livros de eventos, posições finais e preços de reinvestimento | Manter local |
| Extratos financeiros, respostas CVM e cópias dos catálogos de RI | Manter local |

Os sete arquivos em [published_round2](published_round2/) contêm contagens e manifestos. O exportador aceita esquemas exatos e verifica hashes de todos os 176 artefatos locais. Nenhuma cotação, volume, retorno individual, ISIN, CNPJ ou valor de evento individual é exportado. O inventário local público informa somente arquivo, bytes, hash e decisão `LOCAL_ONLY`.

As respostas integrais dos 73 documentos CVM exigidos foram temporárias. Permanecem apenas ZIPs financeiros compactos e manifestos locais. A camada de 74.015 registros de negociação é diferencial; não duplica a base de 634 MB. Os 14 MB do checkpoint anterior, a branch local de evidências e os checkpoints dos estudos anteriores foram preservados.

A [atribuição e delimitação de direitos da primeira publicação](PUBLICACAO.md) continua aplicável. Fontes novas dirigidas: catálogos oficiais IRB e Light e documento oficial da oferta IRB. Seus URLs e hashes constam do [manifesto público](published_round2/manifest.json); as cópias estão no diretório ignorado `local_only/round2`.

A auditoria anterior permanece intacta. O arquivo [publication_review_round2.json](publication_review_round2.json) registra os arquivos alterados/acrescentados nesta atualização, seus tamanhos e hashes, o commit anterior, verificações de conteúdo e a reprodução da exportação. O próprio arquivo de auditoria não inclui seu hash, evitando autorreferência.

Antes do push foram conferidos o inventário exato de arquivos, tamanhos, colunas públicas, padrões de credenciais, ausência de bases/caches individuais e o histórico Git. A exportação foi reproduzida byte a byte em diretório temporário. O commit local antigo com evidências granulares não é ancestral da branch pública e não é enviado ao remoto.
