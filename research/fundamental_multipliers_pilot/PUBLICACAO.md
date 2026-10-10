# Auditoria dos arquivos para publicação pública

A publicação contém o código da investigação, testes, protocolo, relatório e medidas agregadas de cobertura. Os aproximadamente 14 MB do inventário detalhado permanecem em `local_only/data`, no armazenamento persistente do workspace. Esse diretório é ignorado pelo Git. O commit original com as evidências permanece somente na branch local `local/fundamentals-multipliers-evidence-20261009`.

## Decisões por conteúdo

| Conteúdo | Decisão | Fundamentação |
|---|---|---|
| Scripts, testes e protocolo | Publicar | Implementação da investigação; testes usam dados sintéticos e não contêm arquivos de mercado |
| Relatório e gráfico de cobertura | Publicar | Análises e contagens próprias; o relatório público não contém exemplos de preços B3 |
| Contagens por ano, indicador, BDI e tipo de evento | Publicar | Não contêm ticker, ISIN, CNPJ, preço, volume financeiro ou valores de eventos individuais |
| Hashes, nomes relativos e tamanhos das fontes | Publicar | Permitem conferir a reprodução sem copiar os arquivos de origem |
| Cotações de formação e amostras de valuation | Manter local | Contêm preços e volumes individuais; a permissão de redistribuição desse material B3 não foi confirmada |
| Painéis por companhia ou título, com dados contábeis e cotações | Manter local | Misturam fontes e incluem dados de mercado individuais |
| Cobertura por ticker e eventos individuais | Manter local | Detalhamento desnecessário à reprodução pública; a publicação usa agregados |
| Versões CVM e cobertura individual por companhia | Manter local | O código e os hashes reproduzem a extração; não é necessário publicar o inventário completo |
| Manifesto completo do ambiente local | Manter local | O manifesto público preserva somente resultados, fontes relativas, tamanhos e hashes necessários |

As decisões e tamanhos dos 21 arquivos originais de evidência constam de [publication_inventory.csv](published/publication_inventory.csv). Os tamanhos e hashes dos arquivos incluídos na branch pública constam de [publication_review.json](publication_review.json). O inventário anterior contava o PNG junto aos CSVs: são 18 CSVs e um gráfico, e a contagem pública foi corrigida sem alterar os registros locais preservados.

## Fontes e atribuição

As informações CVM foram acessadas pelo [Portal de Dados Abertos da CVM](https://dados.cvm.gov.br/). Os conjuntos [DFP](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp), [ITR](https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr) e [FRE](https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre) identificam a [Open Database License ODbL](https://opendatacommons.org/licenses/odbl/1-0/) em seus metadados. A atribuição segue os [termos de uso do portal](https://dados.cvm.gov.br/about). As contagens de cobertura, os gráficos e as análises são produzidos pelo código desta investigação; não constituem uma certificação da CVM sobre as conclusões.

Fonte de preços locais: B3, arquivos COTAHIST de [cotações históricas](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/). Os arquivos B3 e SQLite não estão incluídos nesta publicação. A disponibilidade para download não foi usada como prova de permissão para redistribuir cotações, séries ou eventos. Nesta entrega, são publicados somente resultados próprios de contagem e cobertura, sem observações individuais de preço ou volume que permitam reconstruir a série de origem. Não se concede licença sobre os dados B3.

## Verificações antes da publicação

O exportador verifica os hashes das evidências locais e usa listas exatas de colunas permitidas. Não copia diretórios inteiros. Ele rejeita campos adicionais em agregados e arquivos não auditados no diretório público. As fontes no manifesto público têm nomes relativos; caminhos do ambiente e espaço livre dos discos foram retirados.

Os arquivos incluídos foram verificados quanto a tamanho, conteúdo, chaves privadas, padrões de tokens e credenciais. Bases SQLite, ZIPs históricos, arquivos pessoais, painéis individuais e caches não fazem parte do novo commit. O relatório e seus links foram conferidos contra os agregados e a documentação pública. Os testes preservam a interpretação de datas, versões, denominadores e faltas e verificam as restrições do exportador.

Para impedir divulgação pelo histórico Git, a branch pública foi criada diretamente de `8d394e9ab563daebe43603a3e85f35f43c1402bc`, sem incluir o commit local das evidências. O diff acrescenta somente arquivos da investigação e seus testes; nenhum checkpoint, seleção, livro de eventos ou resultado anterior é alterado. O PR permanece draft e não autoriza merge.
