# Checkpoint CG_ONLY — política corrigida

Continuação do [checkpoint bruto validado](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/6#issuecomment-6086398679). As cinco trajetórias foram reexecutadas com a mesma regra: venda voluntária somente por FAIL comprovado; nenhum rebalanceamento por peso;144 aportes e R$460.000 externos por carteira.

| Carteira | Bruto corrigido R$ | Líquido CG_ONLY R$ | TIR líquida % a.a. | IR CG pago R$ | Redução patrimonial R$ |
|---|---:|---:|---:|---:|---:|
| VVAL | 1.865.901,69 | 1.824.568,21 | 17,6478 | 20.225,96 | 41.333,48 |
| BESST-10 BH | 1.767.443,92 | 1.767.123,19 | 17,2504 | 81,23 | 320,73 |
| V0 | 1.670.906,27 | 1.639.461,93 | 16,3184 | 17.693,98 | 31.444,34 |
| V10 | 1.619.829,36 | 1.594.196,07 | 15,9701 | 11.047,40 | 25.633,29 |
| BH padrão | 1.270.936,41 | 1.270.555,51 | 13,1400 | 116,41 | 380,90 |

Ranking sem alteração por CG_ONLY: VVAL > BESST-10 BH > V0 > V10 > BH padrão. O ranking já havia mudado pela correção econômica: V0 ultrapassou V10. A redução patrimonial inclui reinvestimentos menores e seus rendimentos posteriores; não equivale ao imposto pago.

CG_ONLY inclui ganho realizado em saídas FAIL e eventos de realização de direitos/resgates/caixa de conversões; por isso BH pode pagar imposto mesmo sem venda voluntária. Não acrescenta IRRF de JCP/dividendos. Mantidos custo médio por título, isenção mensal de ações até R$20.000, perdas prospectivas, categorias separadas, reserva antes das compras e pagamento posterior de DARF. IRRF é crédito, sem segunda cobrança. Caixa restrito, livre e obrigação estão discriminados nas trajetórias. Nenhum aporte extraordinário financia imposto.

## Liquidação integral hipotética em 30/06/2026

Não altera as trajetórias mantidas acima. Usa quantidades/custos remanescentes no cenário tributado; deduz economicamente a obrigação da venda final, mesmo com vencimento posterior.

| Carteira | Patrimônio de saída R$ | IR adicional da liquidação R$ | TIR de saída % a.a. | Obrigação já existente antes da saída R$ |
|---|---:|---:|---:|---:|
| VVAL | 1.708.091,10 | 116.477,11 | 16,8282 | 0,00 |
| BESST-10 BH | 1.636.043,39 | 131.079,80 | 16,2924 | 0,00 |
| V0 | 1.544.450,97 | 95.010,96 | 15,5756 | 0,00 |
| V10 | 1.497.125,18 | 97.070,89 | 15,1881 | 0,00 |
| BH padrão | 1.196.955,81 | 73.599,70 | 12,3927 | 0,00 |

## Validação e limites

45 testes aprovados, incluindo as regras obrigatórias da política corrigida, conciliação real de caixa/reserva/NAV, custo médio removido nas vendas, custo final preservado, impostos anuais versus total e separação da liquidação. Os dados antigos permanecem protegidos por hash. Executar `python scripts/run_monthly_corrected.py --mode CG_ONLY` seguido de `python -m pytest -q tests/test_monthly_policy_corrected.py tests/test_monthly_tax.py`.

Resultado **condicional às bases fiscais societárias herdadas**: custo zero para bonificações sem custo declarado; rateio de custo XP por valor relativo; enquadramento de resgates/parcelas de caixa conforme convenção explícita anterior. Não constitui certificação fiscal integral. Calendário B3 é proxy de dias úteis bancários. Permanecem as ressalvas de seleção/proventos, BESST-10 com TIMP3 condicional à NET, ausência de custos e TWR ND de V0/VVAL. Não houve investigação documental nova.

Arquivos: `research/monthly_policy_corrected_2014_2026/consolidated_tax_corrected.csv` e `CG_ONLY/`: posições/custos finais, operações, caixa, contribuições, apuração mensal, pagamentos, imposto anual, concentração e liquidação. Concentração final (maior emissor/HHI) consta no consolidado. A lógica fiscal do checkpoint anterior foi reutilizada sem editar os legados. PR #6 permanece draft, sem merge.
