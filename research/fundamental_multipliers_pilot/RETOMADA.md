# Retomada do PR #8 em outra sessão

Checkpoint preparado em 10/10/2026 para o encerramento da janela de 12 horas, com o mesmo Codespace preservado. **Continuar no PR #8, mantê-lo draft e não fazer merge.** Não é necessário refazer a coleta ou o inventário concluídos.

## Estado remoto e contexto

- Repositório: `tneves95/b3-pipeline-data-and-backtest-framework`.
- PR: <https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/8>.
- Branch: `study/fundamentals-multipliers-pilot-20261009`.
- Commit da análise concluída: `5626c2855755f126fab99c4fcf94d354bc431bb8`, já publicado. O checkpoint de retomada é acrescentado depois dele.
- Base do PR: `study/returns-2014-2026-stage1`, commit `8d394e9ab563daebe43603a3e85f35f43c1402bc`.
- Branch somente local: `local/fundamentals-multipliers-evidence-20261009`, commit `cc069eef1cceef5a4f43f929d1bb5b72f4ca3c34`. **Não publicar essa branch ou esse commit:** contém evidências granulares que foram excluídas da publicação.

O estudo procura relações históricas entre fundamentos disponíveis na formação e retornos futuros de três/cinco anos, incluindo empresas em dificuldade, extintas e perdas graves. O protocolo está congelado em [protocol.json](protocol.json). A tarefa original e as instruções de continuidade também foram salvas no checkpoint local. Os estudos Graham/Barsi são evidência qualificada, com seleções e resultados preservados.

## Trabalho concluído

O [relatório da segunda rodada](RODADA2.md) e o [manifesto público](published_round2/manifest.json) descrevem a execução aceita:

- `outcome_readiness()` corrigida: última negociação até a data-alvo, ISIN histórico e calendário observado; a ordem das linhas dos ZIPs não determina o corte. Os casos anômalos de 2018/2019 foram corrigidos e têm regressões.
- Camada independente com 66.518 negociações de ações recuperadas e 7.497 de direitos; SQLite original inalterado.
- 85/85 observações de balanços anuais exigidos recuperadas: 12 de originais anteriormente locais e 73 por IDs CVM exatos. **Não baixar esses documentos novamente.** Valores contábeis ausentes continuam nulos.
- 24 retornos totais **nominais** certificados: 15 de três anos e nove de cinco anos, em três companhias. Há uma trajetória certificada com patrimônio inferior à metade do inicial. Escopos: janelas específicas de Bradesco PN, Cemig PN e IRB; 272 linhas FRE reutilizadas foram verificadas contra originais locais.
- Matriz completa mapeada: 5.176 observações, com 24 certificadas, 3.574 não certificadas e 1.578 censuradas, sendo 955 econômicas e 623 por horizonte ainda não vencido.
- 94 observações título/data com identidade pendente, conservadas separadamente em 188 observações título/horizonte. Não são 94 companhias distintas.
- Lucro positivo, margem EBIT, conversão em caixa e liquidez já calculados. Cobertura certificada de 0,527% dos horizontes completos, concentrada em três companhias: **nenhuma estimação preditiva foi executada**.
- 32 testes passaram; sete agregados públicos reproduzidos byte a byte; publicação auditada; checkpoints anteriores e 14 MB de evidências preservados.

Os 3.025 registros do livro econômico não são um certificado universal. Não promover os livros antigos integralmente a certificados nem interpretar zero eventos ignorados como prova de completude.

## Arquivos que permanecem no workspace

Todos os caminhos abaixo são relativos à raiz Git deste projeto, salvo indicação contrária:

| Local | Conteúdo e uso |
|---|---|
| `research/fundamental_multipliers_pilot/local_only/data/` | 21 arquivos do inventário preliminar, 14.696.806 bytes; não sobrescrever |
| `research/fundamental_multipliers_pilot/local_only/round2/` | 176 artefatos da segunda rodada, 28.853.656 bytes, mais `round2_manifest.json`; checkpoint fechado |
| `local_only/round2/return_certification_matrix.csv` | Matriz individual completa, mantida somente local |
| `local_only/round2/certified_event_ledger.csv` e `certified_endpoint_holdings.csv` | Prova de eventos aplicados e posições finais dos certificados |
| `local_only/round2/quote_overlay.sqlite` | Camada diferencial; consulta conjunta com a base original |
| `local_only/round2/originals/` e `sources/` | Extratos financeiros recuperados, catálogos primários e manifestos; não recolher novamente |
| `research/fundamental_multipliers_pilot/local_only/session_recovery_20261010/` | Contexto local, solicitação original e inventário verificável para a próxima sessão |
| `research/returns_2014_2026_selection/` | Evidência anterior reutilizada: originais, caches de eventos, catálogos e verificações FRE |
| `research/returns_2014_2026_inputs/cvm_recovery/` | Extratos financeiros anteriores reutilizados |
| Diretório pai da raiz Git: `b3_market_data.sqlite`, `data/raw/`, `data/cvm/` | Base original e ZIPs; permanecem no workspace, sem cópia ou nova coleta |

SHA-256 exigido para o SQLite: `0ab5d487ec8e6efe7c995a7bec5f0ae4e6602fc734dfbd4bc96e7cc4c82c3211`. Abrir somente leitura, sem WAL não vazio. O inventário de entradas anteriores é `research/returns_2014_2026_selection/continuation_immutable_inputs.json`, com 22 hashes.

O diretório `local_only/` é ignorado pelo Git. Os dados continuam disponíveis ao reabrir o mesmo Codespace: [persistência ao parar e iniciar](https://docs.github.com/en/codespaces/developing-in-a-codespace/stopping-and-starting-a-codespace). Uma exclusão ou um Codespace inteiramente novo exigiria cópia privada externa; esse cenário não foi solicitado nesta sessão. O contexto e os agregados estão também no remoto.

## Primeiros comandos da próxima sessão

Na raiz Git, `returns_2014_2026_stage1`:

```bash
git status --short
git branch --show-current
git log -3 --oneline
python research/fundamental_multipliers_pilot/recovery/verify_checkpoint.py
```

O verificador usa apenas a biblioteca padrão, não baixa nada e não altera dados. Confere os hashes dos arquivos e fontes salvos no inventário local. Se um arquivo faltar ou divergir, investigar a causa antes de recalcular. Não substituir um checkpoint aceito por uma execução parcial.

O ambiente testado fica em `../.venv`; as versões estão em [requirements.txt](requirements.txt). Se necessário, conferir os testes relevantes:

```bash
../.venv/bin/python -m pytest -q \
  tests/test_fundamental_multipliers_audit.py \
  tests/test_fundamental_multipliers_returns.py \
  tests/test_fundamental_multipliers_publication.py \
  tests/test_fundamental_multipliers_round2_publication.py
```

Para conferir novamente a publicação sem recalcular ou recolher fontes, exportar a um diretório temporário novo:

```bash
../.venv/bin/python -m research.fundamental_multipliers_pilot.publish_round2 \
  --output /tmp/b3-pr8-aggregate-verification
```

Não executar `audit` ou `round2` sobre os diretórios aceitos: os comandos recusam sobrescrever manifestos fechados. Novos cálculos usam outro diretório e mantêm a proveniência do checkpoint anterior. Há arquivos locais de outras tarefas, `.pr4-state/` e `.pr5-work`, que não foram alterados por esta investigação.

## Próximo trabalho autorizado

Continuar a ordem documentada em [RODADA2.md](RODADA2.md), sem escolher casos em função do retorno:

1. Resolver as 94 identidades históricas elegíveis, incluindo títulos extintos e conflitos de companhia/classe.
2. Reconciliar as 955 censuras econômicas: direitos e sucessão Americanas; datas ex e direito Light; caixa IRB fora do escopo certificado; saídas com resgate/conversão, incluindo ENBR. Priorizar os 164 horizontes com eventos materiais já identificados. As causas se sobrepõem.
3. Ampliar catálogos completos de eventos para coortes/setores representativos, incluindo empresas em dificuldade. Os 4.487 impedimentos de catálogo são a maior barreira quantitativa. Reutilizar primeiro os originais auditados locais.
4. Certificar IPCA e Ibovespa nas mesmas datas efetivas; os certificados atuais são nominais.
5. Quando houver cobertura suficiente e representativa, executar os quatro indicadores simples e filtros congelados sem esperar indicadores complexos. Manter dependência por companhia/tempo, cortes temporais e multiplicidade previstos no protocolo.

A trava desta rodada exige pelo menos 95% de certificação no total e em cada coorte/horizonte completo, 100 companhias distintas, nenhuma censura econômica conhecida nem identidade elegível pendente. Isso é uma condição operacional necessária; não substitui auditorias ou inferência do protocolo. Não estimar relações preditivas numa subamostra de sobreviventes ou excluir perdas graves para ultrapassar a trava.

## Limites de publicação

A autorização existente permite publicar código, testes, documentação, agregados e evidência cuja redistribuição seja permitida, após auditoria de arquivos e tamanhos. **Não publicar preços, volumes, retornos ou eventos individuais B3, bases originais, credenciais, arquivos pessoais ou material desnecessário.** Não fazer push de todas as branches/tags. Não fazer merge.

Os exportadores usam listas exatas de colunas e hashes. Auditar novos arquivos e histórico antes de qualquer push. Os registros anteriores `publication_review.json` e `publication_review_round2.json` descrevem seus respectivos commits e devem permanecer preservados.

Mensagem curta para iniciar a próxima sessão: **“Retome o PR #8 lendo `research/fundamental_multipliers_pilot/RETOMADA.md` e verificando o checkpoint local; mantenha draft, sem merge.”**
