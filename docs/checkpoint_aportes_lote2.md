# PR #5 — lote 2: motor monetário e três carteiras completas

O ranking e as regras foram congelados no lote 1. Este lote reconstrói as quantidades com preços nominais e eventos econômicos sobre as unidades efetivamente detidas. Não multiplica os índices históricos por um capital fictício. Formação igualmente ponderada por CNPJ; aportes nos déficits; mudanças voluntárias somente nas revisões de junho; descendentes não criam novos alvos. Há livros separados de depósitos externos, operações e eventos internos.

O controle sem aportes, com os mesmos oito nomes, pesos iguais e ausência de revisão voluntária, reproduz o motor BH anterior nos **13 fechamentos de junho**. O maior desvio é R$ 0,000000000116, decorrente de ponto flutuante. Os eventos compartilhados entre B00S e BH conservam exatamente tipo, data, quantidade e valor; as fontes antigas permanecem intactas. O benchmark BESST possui dois eventos iniciais BBSE de 2014–2015 não cobertos pelo segmento original: foram derivados do cache B3 já arquivado, com a mesma convenção de recebimento econômico no pregão seguinte. Essa transcrição herda as limitações do cache e não constitui nova certificação dos proventos da companhia.

## Primeiras 24 contribuições, encerramento em junho/2016

Cada investidor aplicou R$ 160.000: R$ 100.000 iniciais mais 24 × R$ 2.500.

| Carteira | Patrimônio | TIR anual | TWR acumulado | Diferença patrimonial vs IBOV |
|---|---:|---:|---:|---:|
| V0 | R$ 183.436,35 | 8,6122% | ND | R$ 24.420,58 |
| BH padrão | R$ 203.605,62 | 15,5787% | 31,8370% | R$ 44.589,85 |
| BESST-10 BH condicional | R$ 167.499,75 | 2,8230% | 0,2923% | R$ 8.483,98 |
| IBOV com aportes | R$ 159.015,77 | −0,3755% | −3,0870% | R$ 0,00 |

O TWR da V0 é ND porque não existe preço dos direitos ABCB2 nas duas datas de aporte 01/07/2014 e 02/01/2015. O dinheiro ficou em caixa e foi reaplicado no aporte seguinte com marcação completa. Patrimônio e TIR usam quantidades e fluxos reais dessa política e continuam calculáveis. Não se imputa preço zero ao direito nem se antecipa sua primeira negociação.

## 144 contribuições, encerramento em junho/2026

Cada investidor aplicou R$ 460.000. Os resultados continuam condicionais aos eventos/proventos qualificados aceitos dos estudos anteriores; o BESST permanece também condicional à pendência NET/ON do ranking.

| Carteira | Patrimônio | TIR anual | TWR acumulado | Maior peso de linhagem | Giro acumulado de junho |
|---|---:|---:|---:|---:|---:|
| V0 | R$ 1.645.952,98 | 16,3675% | ND | 8,3473% | 107,6752% |
| BH padrão | R$ 1.270.936,41 | 13,1438% | 373,6694% | 22,8596% | 0% |
| BESST-10 BH condicional | R$ 1.767.443,92 | 17,2527% | 459,5005% | 22,3390% | 0% |
| IBOV com aportes | R$ 1.051.091,04 | 10,7592% | 223,5469% | Índice | 0% |

O giro é a soma de `min(vendas,compras)/NAV` por revisão; não inclui aportes mensais, formação ou eventos involuntários. Foram processados 1.201 eventos V0, 692 BH e 780 BESST, cada ID econômico uma vez. Não há venda voluntária fora de junho, nenhuma venda voluntária BH e nenhum caixa final. V0 encerra com 20 linhagens, BH com oito, BESST com dez; classes/XP não multiplicam esses números.

Na V0 há também preço ausente do recebível ENBR3 no aporte de 01/09/2023, além do mês anterior sem cotação de encerramento. O valor final de R$ 24,23 provado em 05/09 não foi antecipado para agosto/setembro. O depósito ficou em caixa até o aporte seguinte; o resgate interno foi processado em sua data aceita. Não se fabrica TWR cumulativo para transpor essa lacuna. A volatilidade usa somente meses com retorno exatamente calculável e publica a contagem; drawdown cumulativo com lacuna fica ND.

**Validação:** 22 testes passaram, incluindo fluxos datados, TWR antes/depois de aporte, proteção de vencedoras, ausência de reset em junho sem alteração de nomes, cisão sem novo alvo, resgate interno, preço ausente e reprodução do motor legado sem aportes. Os 3.567 arquivos protegidos seguem inalterados. Os CSVs estão em `research/monthly_contributions_2014_2026/checkpoints/2016/` e `checkpoints/lote2_2026/`.

Próximo lote: V10, VVAL, sensibilidade obrigatória BBDC4/2014, relatório completo, planilha e verificações finais. O PR permanece draft, sem merge e sem mudanças nos critérios.
