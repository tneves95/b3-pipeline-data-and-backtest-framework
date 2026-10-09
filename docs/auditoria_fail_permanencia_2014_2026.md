# Auditoria da fundamentação das vendas por FAIL — PR #6

09/10/2026. Verificação iniciada após a identificação dos zeros de lucro de SBSP3. Foram rastreadas **todas as18 vendas voluntárias** das cinco carteiras, nos modos GROSS, CG_ONLY e CG_PLUS_JCP_CERTIFIED_PARTIAL: **54 registros**, relativos a10 eventos companhia/revisão. As carteiras BH não tiveram vendas voluntárias. Eventos compulsórios e admissões do universo inteiro não integram esta auditoria.

**Conclusão: o problema se repetiu.** Cinco vendas decorrem de zeros de lucro contraditos pelos dados PIT preservados; outras quatro têm fundamentação questionável por ausência de proventos no cache legado ou por uso da liquidez de outro título. A expressão anterior “18 FAILs comprovados” validava apenas o rótulo congelado e precisa ser retificada. Os testes do motor confirmavam que só vendia esse rótulo, sem testar sua fundamentação econômica.

## Ocorrências que afetam as saídas

| Papel / revisão | Carteiras | Vendas por modo | Diagnóstico |
|---|---|---:|---|
| BRSR6 / junho2021 | V0, VVAL | 2 | v9 registrou zero em2019 e2020. DFP consolidada conhecida antes do corte: lucro R$1.269.947.000 e R$619.864.000, respectivamente. Screening B00S PASS. Mesma classe de erro de SBSP3. |
| SBSP3 / junho2024 | V0, V10, VVAL | 3 | v9 registrou zero em2022 e2023. Cache DFP PIT registra lucro R$3.121.267.000 e R$3.523.531.000. Screening B00S PASS. |
| CPFE3 / junho2020 | V0, VVAL | 2 | `cash5=0` porque a série de eventos herdada registra2015 sem provento. Screening B00S PASS e DFC individual registra R$850.000 de dividendos/JCP pagos em2015; DMPL/DVA também têm valores positivos. Ausência no cache não comprova ausência de distribuição. O vínculo entre exercício, declaração, pagamento e data-ex permanece pendente. |
| TIET11 / junho2016 | V0, VVAL | 2 | Status FAIL herdado de TIET4, cuja mediana era R$2.059 e71 sessões. A unit efetivamente mantida TIET11 tinha mediana R$17.226.607 e123 sessões, passando o filtro existente. A seleção excluía units pelo comprimento do ticker e o motor copiou o status de TIET4 para TIET11. |

**Total sob revisão:9 vendas por modo**, sendo V0=4, V10=1 e VVAL=4. Cinco têm contradição direta dos zeros; quatro exigem revisão da evidência de distribuição/representação. Não se converte automaticamente ausência de prova em aprovação documental integral.

## As demais saídas

| Papel / revisão | Carteiras | Vendas por modo | Fundamento observado |
|---|---|---:|---|
| CSMG3 / junho2016 | V0, V10, VVAL | 3 | DFP conhecida até o corte registra prejuízo de R$11.592.000 em2015. |
| LIGT3 / junho2017 | V0, VVAL | 2 | DFP conhecida até o corte registra prejuízo de R$312.937.000 em2016. |
| IRBR3 / junho2021 | V0 | 1 | DFP conhecida até o corte registra prejuízo de R$1.521.263.000 em2020. |
| AURE3 / junho2025 | V0 | 1 | Histórico PIT do emissor atual registra prejuízos em2021/2023, incluindo o exercício2023 que reprova a janela de cinco lucros positivos. CNPJ atual e linhagem econômica antiga são expostos separadamente. |
| COCE5 / junho2015 e junho2021 | V0 | 2 | Medianas R$738.042,50 e R$965.378,50, inferiores ao filtro codificado de R$1 milhão. Lucros e distribuições passam. |

As sete vendas nos quatro primeiros grupos têm falha de lucro identificável nas demonstrações selecionadas. Nas duas de COCE5, o teste confirma a reprovação mecânica de liquidez; não redefine por conta própria quais critérios o coordenador exige para permanência. Não foram interpretadas como zeros falsos. Tampouco se certificou toda a contabilidade, a política de liquidez ou a continuidade de perímetros societários nesta verificação.

## Rastreabilidade e limites

O caminho causal é `stage1_resume.selection` → `b00s_variants.simulate` → `review_ledger.csv` → `monthly_policy_corrected.maintenance_evidence` → venda monetária. Para2020–2025, `stage1_resume.py` sobrescreve o screening com `preselection_pass=0` ou `cash5=0` do legado. A seleção independente já possui tratamento de comparativos DRE vazios e passa SBSP3/BRSR6, mas o override posterior reintroduz as reprovações.

BRSR: DFP100931, recebida15/03/2021, contém os resultados positivos de2019/2020. SBSP: DFP134989, recebida21/03/2024, contém os resultados positivos de2022/2023, com fallback para o individual no comparativo consolidado vazio. CPFE: DFP63488, recebida23/03/2017, documenta o pagamento individual de2015, anterior a junho2020. TIET11: COTAHIST preservado em `cache/market.json.gz`; `stage1_select.run` limita seu universo a tickers de cinco caracteres, e `b00s_variants.simulate` herda explicitamente o status de TIET4.

Os valores de lucro são os totais consolidados/individuais extraídos dos caches, com perímetro, conta e documento registrados; não representam nova certificação do lucro normalizado atribuível à controladora. A comparação é suficiente para demonstrar que não se pode aceitar os zeros do legado automaticamente. Todos os fatos selecionados respeitam `received<=cutoff` e `period_end<=cutoff`. Não foram usados resultados futuros para defender exclusões.

O auditor também distingue o CNPJ de linhagem usado para carregar a posição do CNPJ do emissor observado no período. Essa distinção importa especialmente em TIET/AURE. Não se preenche o histórico financeiro do predecessor com zeros nem se troca silenciosamente a empresa cuja DFP é consultada.

Os CSVs e relatórios econômicos anteriores foram preservados por hash. **Não foi executado recálculo patrimonial nesta auditoria.** Seus patrimônios, impostos e rankings permanecem provisórios e sujeitos às decisões de saída identificadas. A auditoria não mede o retorno contrafactual de manter os papéis, nem soma o valor de venda como se fosse impacto de patrimônio.

## Reprodução e testes

```bash
python scripts/audit_monthly_maintenance_fail.py
python -m pytest -q tests/test_monthly_maintenance_fail_audit.py tests/test_monthly_policy_corrected.py tests/test_monthly_tax.py
```

**59 testes passaram**, sendo10 da auditoria e49 regressões preservadas. Cobrem cada venda em todos os modos, fatos conhecidos no corte, zeros contraditos, distinção entre perda real e lacuna, classe/unit de liquidez, provento do mesmo exercício e integridade dos resultados/fontes anteriores.

Arquivos em `research/monthly_fail_audit_2014_2026/`: `exit_evidence_audit.csv`, `pit_facts.csv`, `actual_security_liquidity.csv`, `sales_audit_all_modes.csv` e `manifest.json`. O manifesto registra hashes dos insumos e dos resultados anteriores preservados. O replay da auditoria é determinístico. Código econômico, composições, resultados e PRs anteriores permanecem preservados; trabalho somente no PR #6 draft, sem merge.
