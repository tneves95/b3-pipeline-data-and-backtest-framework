# Checkpoint bruto após reauditoria de permanência — PR #6

Cinco trajetórias efetivamente recalculadas: R$100.000 iniciais +144 aportes de R$2.500 = R$460.000 externos por carteira. Posição mantida em30/06/2026, sem IR neste checkpoint. Dados/código/checkpoints anteriores preservados; PR #6 draft, sem merge.

| Carteira | Bruto R$ | TIR % a.a. | Δ checkpoint bruto anterior R$ | Δ PR5 original R$ | Maior emissor % | HHI emissores | Vendas voluntárias anteriores → atuais |
|---|---:|---:|---:|---:|---:|---:|---:|
| BESST-10 BH | 1.767.443,92 | 17,2527 | 0,00 | 0,00 | 22,34 | 0,119365 | 0 → 0 |
| VVAL | 1.687.498,78 | 16,6774 | -178.402,91 | -180.552,07 | 16,65 | 0,092083 | 6 → 3 |
| V0 | 1.646.488,20 | 16,3716 | -24.418,07 | 535,22 | 11,88 | 0,060207 | 10 → 6 |
| V10 | 1.553.810,51 | 15,6508 | -66.018,86 | -102.577,93 | 14,96 | 0,103628 | 2 → 1 |
| BH padrão | 1.270.936,41 | 13,1438 | 0,00 | 0,00 | 22,86 | 0,145011 | 0 → 0 |

Ranking bruto: **BESST-10 BH > VVAL > V0 > V10 > BH padrão**. BESST-10 BH ultrapassa VVAL pela revisão econômica das saídas; isto ocorre antes da tributação.

A auditoria anterior identificou nove saídas sem fundamentação suficiente: TIET11/2016 (classe errada), CPFE3/2020 (lacuna de provento não prova ausência), BRSR6/2021 e SBSP3/2024 (zeros contraditos por DFP PIT). Elas foram anuladas. Os quatro emissores foram revistos nos junhos seguintes com os insumos preservados. TIET11 permaneceu, converteu-se compulsoriamente em AESB3 e depois AURE3; AURE3 teve FAIL comprovado em2025, incluindo uma nova saída na VVAL. Histórico ausente ou zeros de uma sociedade sucessora antes da reorganização não viraram prova de FAIL. CPFE/2020 permanece INDETERMINATE, sem inventar o provento ausente.

Na V10, a permanência de SBSP3 mantém ocupadas as duas vagas de saneamento com SAPR4. CSMG3 não substitui SBSP3 em2024/2025; não se cria uma terceira vaga nem se vende um incumbente. As demais candidatas e a ordem de liquidez PIT congelada são preservadas. Nenhuma venda por valorização, concentração, peso, ausência da lista de compras ou entrada de outra empresa. O marcador de vencedora persiste e2× regula somente novas compras. BH não vende voluntariamente.

Escopo: revisão dos achados e junhos posteriores dessas quatro linhagens; as demais saídas comprovadas pela auditoria anterior são mantidas. O filtro de liquidez de COCE5 é a convenção já codificada, não uma certificação nova de que liquidez deve integrar permanência. CNPJ do sucessor contemporâneo é usado para seus demonstrativos; não se atribui ao antecessor uma história fictícia. Os fatos ausentes permanecem ND. Não é reauditoria integral de todos os emissores.

| Saída / junho | Carteiras | Fundamentação |
|---|---|---|
| COCE5 / 2015 | V0 | LIQUIDITY_FILTER_MATCHES |
| CSMG3 / 2016 | V0, V10, VVAL | NONPOSITIVE_PROFIT_DOCUMENTED |
| LIGT3 / 2017 | V0, VVAL | NONPOSITIVE_PROFIT_DOCUMENTED |
| COCE5 / 2021 | V0 | LIQUIDITY_FILTER_MATCHES |
| IRBR3 / 2021 | V0 | NONPOSITIVE_PROFIT_DOCUMENTED |
| AURE3 / 2025 | V0, VVAL | NONPOSITIVE_PROFIT_DOCUMENTED |

Mantidos preços e eventos aceitos, inclusive a ressalva NET/TIMP3 da BESST-10 BH. Não houve nova pesquisa de NET, novos proventos ou seleção pelo retorno posterior. Compras fracionárias, ausência de custos e reinvestimento na data-ex são convenções herdadas. Patrimônio e TIR calculáveis; TWR permanece ND onde faltam cotações nas datas de fluxo. Os livros discriminam caixa e compras adiadas.

Reprodução: `python scripts/monthly_maintenance_reaudit.py`, depois `python scripts/run_monthly_reaudited.py --mode GROSS`. Arquivos em `research/monthly_reaudited_2014_2026/GROSS/`, consolidado `consolidated_policy_corrected.csv`, provas `maintenance_reviews.csv` e `maintenance_pit_facts.csv`. Testes: `tests/test_monthly_reaudit.py` e as59 regressões anteriores. O próximo checkpoint aplica CG_ONLY às trajetórias acima e reaproveita a camada fiscal existente.
