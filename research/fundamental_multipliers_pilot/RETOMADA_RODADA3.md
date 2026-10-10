# Retomada após expiração da janela do Codespace

O Codespace permanece existente. Os originais e evidências continuam em `/workspaces`; não foi feita cópia das bases. Esta nota substitui as instruções de próxima etapa do documento antigo `RETOMADA.md`, preservado como checkpoint histórico. A trava de 95% da segunda rodada foi substituída, com autorização do usuário, pelo protocolo exploratório desta rodada.

PR [#8](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/8), branch `study/fundamentals-multipliers-pilot-20261009`, **draft, sem merge**. Não publicar a branch `local/fundamentals-multipliers-evidence-20261009` nem o commit privado `cc069eef1cceef5a4f43f929d1bb5b72f4ca3c34`. Não alterar checkpoints Graham/Barsi nem fontes originais.

## Conferência inicial

```bash
cd /workspaces/b3-pipeline-data-and-backtest-framework/returns_2014_2026_stage1
git status --short
../.venv/bin/python -m research.fundamental_multipliers_pilot.round3.checkpoint verify
../.venv/bin/python research/fundamental_multipliers_pilot/recovery/verify_checkpoint.py
```

O segundo verificador confere os 413 arquivos anteriores. Sua última mensagem descreve a situação antiga; o relatório atual é [RODADA3.md](RODADA3.md). O inventário novo, o HEAD salvo e os arquivos necessários à retomada ficam em `local_only/session_recovery_round3_20261010/`. Se um hash falhar, verificar a causa antes de recalcular ou publicar.

## Estado disponível

- [Protocolo congelado](protocol_round3.json), módulo `round3/` e testes sintéticos da terceira rodada. Não otimizar filtros na amostra OOS.
- Evidências anteriores: `local_only/data/` e `local_only/round2/`, preservadas byte a byte.
- Resultado detalhado: `local_only/round3/analysis_panel.csv`, `return_estimates_A_B_C.csv`, eventos, proveniência contábil e verificações amostrais. **Esses arquivos são privados e não devem ser adicionados ao Git.**
- Resultados publicáveis: `published_round3/`; auditoria: `publication_review_round3.json`.
- Um único PDF primário dirigido para resolver grupamento omitido: `local_only/round3/gpc_itr_201606.pdf`, 960.704 bytes, SHA-256 `3a73dce8d37e1050e2699cf261a8ce8d0394584c9246704a966e4a406f5528cb`. Não repetir o download quando o hash conferir.

## Reproduzir offline

```bash
../.venv/bin/python -m pytest -q tests/test_fundamental_multipliers_audit.py tests/test_fundamental_multipliers_publication.py tests/test_fundamental_multipliers_returns.py tests/test_fundamental_multipliers_round2_publication.py tests/test_fundamental_multipliers_round3.py
OPENBLAS_NUM_THREADS=1 ../.venv/bin/python -m research.fundamental_multipliers_pilot.round3.run --output /tmp/fundamentals-round3-reproduction
../.venv/bin/python -m research.fundamental_multipliers_pilot.round3.publication --local /tmp/fundamentals-round3-reproduction --public /tmp/fundamentals-round3-publication
```

O processamento consulta o SQLite original e o overlay em modo somente leitura. Não baixa fontes e não copia bases. O ambiente registrado está em `round3/requirements.txt`. O resultado exploratório não autoriza declarar poder preditivo geral: cobertura de dificuldades/saídas, controles setoriais, sensibilidade e validação temporal continuam limitando as conclusões.

## Próximo trabalho objetivo

Seguir a ordem de [impedimentos e suficiência](published_round3/sufficiency.csv) e a seção final do relatório: linhagens econômicas de saídas, direitos materiais, fatores/datas de capital divergentes, capital histórico para valuation e mais períodos independentes. Reutilizar originais e resoluções auditadas antes de qualquer coleta dirigida. Não reabrir uma exigência de precisão contábil absoluta para cada companhia.

Antes de publicar qualquer continuação, conferir novamente os arquivos e seus tamanhos. Publicar apenas código, testes, documentação, manifestos e estatísticas agregadas autorizadas. Preservar o draft e não fazer merge.
