Retificação da fundamentação das saídas do checkpoint corrigido: **o rótulo `FAIL_EXIT` congelado não basta para comprovar FAIL econômico**. Foram verificadas todas as18 vendas voluntárias em cada modo (54 registros em GROSS, CG_ONLY e JCP parcial), com dados já preservados e disponíveis antes dos respectivos cortes.

| Papel / junho | Carteiras afetadas | Achado |
|---|---|---|
| BRSR6 /2021 | V0, VVAL | Mesmo problema de SBSP3: zeros de2019/2020 no v9 contraditos por lucros positivos nas DFPs PIT; screening PASS. |
| SBSP3 /2024 | V0, V10, VVAL | Zeros de2022/2023 contraditos por lucros positivos nas DFPs PIT; screening PASS. |
| CPFE3 /2020 | V0, VVAL | Cache sem provento em2015 virou `cash5=0`, mas DFC individual informa pagamento de R$850mil; screening PASS. Falta conciliar exercício/pagamento/data-ex. |
| TIET11 /2016 | V0, VVAL | Unit liquidada por herdar baixa liquidez de TIET4. TIET11 tinha mediana de R$17,23milhões e123 sessões, passando o filtro. |

**9 das18 vendas por modo estão sob revisão:**5 por zeros de lucro contraditos e4 por distribuição/representação questionável. As demais:7 por prejuízos documentados (CSMG3, LIGT3, IRBR3, AURE3) e2 de COCE5 pelo filtro mecânico de liquidez. O enquadramento desse filtro como permanência não foi redefinido nesta auditoria.

Os59 testes passaram (10 auditoria +49 regressões), com cobertura de todas as vendas, cutoff PIT, classes/units e hashes anteriores. Resultados anteriores preservados; **não houve recálculo patrimonial nesta verificação**, e os patrimônios/impostos/rankings continuam provisórios. Não se estimou retorno contrafactual a partir dos valores vendidos.

Auditoria reproduzível: `scripts/audit_monthly_maintenance_fail.py`, `tests/test_monthly_maintenance_fail_audit.py`, `research/monthly_fail_audit_2014_2026/` e `docs/auditoria_fail_permanencia_2014_2026.md`. PR #6 draft, sem merge; nenhuma nova investigação de NET ou reescrita dos PRs anteriores.
