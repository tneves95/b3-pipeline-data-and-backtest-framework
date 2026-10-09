# Tributação dos aportes mensais — checkpoint 1

PR #6, baseline PR #5 `e3b7c597c83454da34f6461ab68aeb206b0135be`. Cálculo efetivamente executado: R$100.000 em 30/06/2014 e 144 aportes de R$2.500, total R$460.000 por CPF alternativo. Composição BESST-10 BH congelada com TIM, ressalva `CONDITIONAL_NET_ON` mantida.

**Escopo deste checkpoint:** `CG_ONLY`, ganhos realizados nas vendas. Valores condicionais aos custos fiscais não comprovados de algumas bonificações, à alocação de custo de XPBR31 e ao enquadramento dos resgates/conversões com dinheiro. Não são uma certificação de todos os tributos. A camada de JCP/dividendos será entregue em checkpoint seguinte.

| Carteira | Bruto PR5 R$ | Líquido mantendo R$ | TIR líquida a.a. | IR pago R$ | Líquido liquidando em jun/2026 R$ |
|---|---:|---:|---:|---:|---:|
| VVAL | 1.868.050,85 | 1.799.503,81 | 17,48% | 28.059,08 | 1.691.591,67 |
| BESST-10 BH | 1.767.443,92 | 1.767.123,19 | 17,25% | 81,23 | 1.635.362,03 |
| V10 | 1.656.388,43 | 1.618.970,82 | 16,16% | 15.053,44 | 1.519.980,26 |
| V0 | 1.645.952,98 | 1.581.459,89 | 15,87% | 26.687,97 | 1.500.321,59 |
| BH padrão | 1.270.936,41 | 1.270.555,51 | 13,14% | 116,41 | 1.196.955,81 |

O ranking deste cenário permanece **VVAL, BESST-10 BH, V10, V0, BH padrão**. O IR pago soma DARFs e IRRF; IRRF utilizado é crédito, sem cobrança duplicada. A diferença entre bruto e líquido inclui o rendimento que o imposto deixou de gerar nas compras posteriores. Não equivale à soma dos impostos pagos.

A simulação separa o custo por ação/classe, perdas comuns e day trade, isenção mensal agregada de R$20 mil e operações sem essa isenção. Mantém caixa restrito até o pagamento do DARF, com mínimo de R$10 por código. Reservas conservadoras de eventual perda da isenção são liberadas ao fechar o mês. O calendário de pregões é uma aproximação do calendário bancário. Créditos IRRF não consumidos no ano são destinados à DIRPF/restituição pendente; não geram caixa artificial.

Reutiliza `monthly_contributions.process_events` e suas seleções, calendário, preços e reinvestimento na data-ex. Os aportes deficitários e o orçamento de compras de junho usam somente o caixa após reserva fiscal. Os dois BH continuam sem vendas voluntárias; a pequena tributação é decorrente da monetização de direitos. A liquidação final é uma cópia independente do estado fiscal real, deduzindo a obrigação de junho mesmo quando o DARF vence em julho.

As datas sem cotação de ABCB2/ENBR3 continuam produzindo TWR `ND` em V0 e VVAL. Patrimônio e TIR continuam calculáveis. IBOV permanece referência bruta de índice, não ativo isento negociável.

Custos declarados identificados sem novos downloads: FREs locais de bonificações do Bradesco. Demais custos não comprovados permanecem `UNRESOLVED`: custo incremental zero central e sensibilidade a preço ex; isso é hipótese, não declaração de que o custo legal seja zero. A cisão XP usa alocação de custo por valor relativo na data-ex, condicional. Resgates usam GCAP 15% separado, sem compensação de perdas da bolsa; classificação legal ainda condicional. Compensações em dinheiro nas conversões têm custo proporcional ao valor recebido. Não houve investigação adicional da NET.

Reprodução: `python scripts/run_monthly_tax.py`; testes: `python -m pytest -q tests/test_monthly_tax.py tests/test_monthly_contributions.py`. A política já foi congelada em `research/monthly_tax_2014_2026/inputs/tax_policy_freeze.json`, antes do cálculo monetário. `validation.json` registra replay integral com imposto zero das cinco carteiras: operações, unidades, posições, eventos, aportes, patrimônio, TIR e TWR. Os números brutos do protocolo foram reproduzidos.

Fontes fiscais: [RFB — bolsa de valores](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/bolsa-de-valores), [isenções](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/isencoes), [compensações](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/compensacoes), [retenções](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/retencoes), [IN RFB 1.585](https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=67494). Regras futuras de proventos: [LC 224/2025](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp224.htm), [Lei 15.270/2025](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15270.htm).

Validação do checkpoint: **52 testes passaram** (fiscal + PR5, 32,70s). PR #5 confirmado em `e3b7c597c83454da34f6461ab68aeb206b0135be`; nenhum arquivo rastreado herdado foi modificado.
