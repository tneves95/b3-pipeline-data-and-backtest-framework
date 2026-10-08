# Checkpoint — IR R$ 100 mil, A × B2

Execução no Codespaces, 07/10/2026 (America/Sao_Paulo; UTC 08/10). Baseline v11.2 provisória, v12 e v13 preservadas. Sem merge.

**372 simulações principais calculadas**, sem falha operacional: seis formações, sete regras A/B2 com e sem IR, quatro referências Barsi buy and hold, BOVA11, e os universos Barsi central/conservative já existentes. As políticas são somente A e B2; BH é referência. Resultados monetários abaixo arredondados ao real; CSVs conservam precisão para reprodução.

**Status: checkpoint econômico provisório.** O cálculo foi executado; os resultados Barsi conservam proventos agregados v9, e custos fiscais de algumas bonificações ainda são aproximações. A faixa de hipóteses calculada não é intervalo de confiança nem certificação fiscal.

**Conclusão econômica:** no universo central, B2 supera A nas três regras Graham nas cinco formações que têm renovação; em 2025 há empate. Isso não implica pagar menos imposto nominal: R03/2020 B2 termina com R$ 328.364, contra R$ 324.308 de A, apesar de pagar R$ 25.378 de IR, contra R$ 25.118. Da vantagem de R$ 4.056, R$ 3.194 vêm da carteira/execução sem IR e R$ 862 da diferença de efeito fiscal acumulado.

A vantagem Graham não é universal sobre Barsi: B00S buy and hold lidera as formações centrais de 2022 e 2024; B00S B2 lidera 2023. R03 B2 lidera 2020, R00 B2 lidera 2021, e R03 A/B2 empatam na liderança de 2025. Em 2020 B00S BH termina em R$ 225.397 e BOVA11 em R$ 170.042. Barsi manter continua competitivo, principalmente nas formações intermediárias. Essas comparações respeitam o mesmo capital e a saída final tributada, mas conservam as limitações documentais descritas no protocolo.

**Sensibilidade da decisão A/B2:** a direção da vantagem Graham central permanece em todos os testes isolados calculados. Entre as regras Barsi, a escolha A/B2 muda em B00/2020, B06/2020, B06S/2020, B00S/2021, B06S/2024. Essas preferências não são robustas às hipóteses pendentes. A faixa considera alterações isoladas, sem afirmar robustez a todas as combinações de erros. Veja [paired_robustness.csv](../research/ir_100k_results/paired_robustness.csv).


## Formação 2020

Patrimônio final em 30/06/2026, capital inicial R$ 100.000. Universo central.

| Regra / política | Sem IR (R$) | Com IR (R$) | Retorno líquido | IR pago (R$) | Giro anual acumulado | Rank líquido |
|---|---:|---:|---:|---:|---:|---:|
| R00 A | 301,430 | 275,536 | 175.54% | 18,268 | 5.00× | 6 |
| R00 B2 | 307,542 | 282,367 | 182.37% | 19,209 | 2.61× | 5 |
| R03 A | 363,745 | 324,308 | 224.31% | 25,118 | 5.00× | 2 |
| R03 B2 | 366,939 | 328,364 | 228.36% | 25,378 | 2.64× | 1 |
| R16 A | 336,685 | 303,690 | 203.69% | 21,279 | 5.00× | 4 |
| R16 B2 | 348,500 | 314,198 | 214.20% | 22,780 | 2.55× | 3 |
| B00 A | 266,893 | 248,399 | 148.40% | 13,925 | 4.95× | 9 |
| B00 B2 | 255,090 | 242,509 | 142.51% | 12,532 | 0.28× | 10 |
| B00 BH | 218,474 | 209,846 | 109.85% | 8,628 | 0.00× | 16 |
| B00S A | 276,207 | 255,672 | 155.67% | 15,725 | 4.98× | 7 |
| B00S B2 | 266,792 | 252,569 | 152.57% | 14,200 | 0.31× | 8 |
| B00S BH | 236,007 | 225,397 | 125.40% | 10,610 | 0.00× | 11 |
| B06 A | 225,811 | 215,191 | 115.19% | 8,353 | 5.00× | 13 |
| B06 B2 | 222,466 | 213,132 | 113.13% | 9,079 | 0.88× | 14 |
| B06 BH | 214,815 | 207,894 | 107.89% | 6,921 | 0.00× | 17 |
| B06S A | 228,348 | 218,406 | 118.41% | 7,988 | 5.00× | 12 |
| B06S B2 | 221,540 | 212,440 | 112.44% | 9,085 | 0.63× | 15 |
| B06S BH | 209,829 | 203,809 | 103.81% | 6,020 | 0.00× | 18 |
| BOVA11 BH | 182,402 | 170,042 | 70.04% | 12,360 | 0.00× | 19 |

## Formação 2021

Patrimônio final em 30/06/2026, capital inicial R$ 100.000. Universo central.

| Regra / política | Sem IR (R$) | Com IR (R$) | Retorno líquido | IR pago (R$) | Giro anual acumulado | Rank líquido |
|---|---:|---:|---:|---:|---:|---:|
| R00 A | 296,901 | 270,314 | 170.31% | 18,400 | 4.00× | 2 |
| R00 B2 | 301,299 | 276,659 | 176.66% | 19,250 | 2.06× | 1 |
| R03 A | 287,404 | 263,097 | 163.10% | 17,724 | 4.00× | 6 |
| R03 B2 | 289,093 | 266,303 | 166.30% | 17,904 | 1.88× | 3 |
| R16 A | 266,024 | 246,364 | 146.36% | 14,608 | 4.00× | 11 |
| R16 B2 | 274,563 | 254,917 | 154.92% | 15,808 | 1.78× | 8 |
| B00 A | 256,245 | 238,015 | 138.02% | 13,628 | 3.95× | 16 |
| B00 B2 | 256,478 | 243,632 | 143.63% | 12,795 | 0.11× | 13 |
| B00 BH | 252,963 | 238,940 | 138.94% | 14,023 | 0.00× | 15 |
| B00S A | 287,827 | 263,619 | 163.62% | 17,715 | 3.98× | 5 |
| B00S B2 | 279,111 | 263,638 | 163.64% | 15,450 | 0.11× | 4 |
| B00S BH | 279,225 | 262,064 | 162.06% | 17,161 | 0.00× | 7 |
| B06 A | 234,511 | 220,983 | 120.98% | 10,057 | 4.00× | 18 |
| B06 B2 | 255,089 | 240,130 | 140.13% | 13,152 | 0.97× | 14 |
| B06 BH | 257,506 | 246,862 | 146.86% | 10,644 | 0.00× | 9 |
| B06S A | 250,752 | 235,377 | 135.38% | 11,109 | 4.00× | 17 |
| B06S B2 | 260,206 | 244,862 | 144.86% | 14,446 | 0.77× | 12 |
| B06S BH | 257,506 | 246,862 | 146.86% | 10,644 | 0.00× | 9 |
| BOVA11 BH | 140,023 | 134,020 | 34.02% | 6,003 | 0.00× | 19 |

## Formação 2022

Patrimônio final em 30/06/2026, capital inicial R$ 100.000. Universo central.

| Regra / política | Sem IR (R$) | Com IR (R$) | Retorno líquido | IR pago (R$) | Giro anual acumulado | Rank líquido |
|---|---:|---:|---:|---:|---:|---:|
| R00 A | 243,198 | 223,929 | 123.93% | 14,076 | 3.00× | 11 |
| R00 B2 | 248,383 | 230,354 | 130.35% | 14,948 | 1.39× | 7 |
| R03 A | 253,778 | 232,920 | 132.92% | 15,337 | 3.00× | 6 |
| R03 B2 | 256,985 | 237,341 | 137.34% | 15,717 | 1.16× | 4 |
| R16 A | 235,384 | 218,535 | 118.54% | 12,635 | 3.00× | 13 |
| R16 B2 | 244,449 | 227,367 | 127.37% | 13,863 | 1.10× | 10 |
| B00 A | 234,724 | 217,995 | 118.00% | 12,500 | 2.95× | 14 |
| B00 B2 | 246,997 | 233,136 | 133.14% | 13,823 | 0.10× | 5 |
| B00 BH | 243,753 | 229,039 | 129.04% | 14,714 | 0.00× | 8 |
| B00S A | 265,551 | 242,803 | 142.80% | 16,539 | 2.98× | 3 |
| B00S B2 | 270,717 | 253,945 | 153.94% | 16,755 | 0.10× | 2 |
| B00S BH | 272,888 | 254,563 | 154.56% | 18,325 | 0.00× | 1 |
| B06 A | 205,181 | 194,510 | 94.51% | 8,210 | 3.00× | 18 |
| B06 B2 | 225,480 | 213,190 | 113.19% | 11,184 | 0.47× | 16 |
| B06 BH | 241,782 | 228,426 | 128.43% | 13,317 | 0.00× | 9 |
| B06S A | 218,892 | 206,778 | 106.78% | 9,082 | 3.00× | 17 |
| B06S B2 | 229,561 | 216,779 | 116.78% | 12,240 | 0.26× | 15 |
| B06S BH | 235,825 | 222,625 | 122.63% | 13,169 | 0.00× | 12 |
| BOVA11 BH | 176,775 | 165,259 | 65.26% | 11,516 | 0.00× | 19 |

## Formação 2023

Patrimônio final em 30/06/2026, capital inicial R$ 100.000. Universo central.

| Regra / política | Sem IR (R$) | Com IR (R$) | Retorno líquido | IR pago (R$) | Giro anual acumulado | Rank líquido |
|---|---:|---:|---:|---:|---:|---:|
| R00 A | 199,039 | 186,977 | 86.98% | 9,730 | 2.00× | 5 |
| R00 B2 | 201,794 | 189,955 | 89.96% | 10,145 | 0.89× | 2 |
| R03 A | 188,590 | 178,134 | 78.13% | 8,811 | 2.00× | 8 |
| R03 B2 | 190,302 | 180,051 | 80.05% | 8,924 | 0.72× | 6 |
| R16 A | 184,097 | 174,634 | 74.63% | 7,920 | 2.00× | 9 |
| R16 B2 | 189,881 | 179,841 | 79.84% | 8,644 | 0.68× | 7 |
| B00 A | 177,962 | 169,768 | 69.77% | 7,021 | 1.95× | 14 |
| B00 B2 | 181,449 | 174,133 | 74.13% | 7,286 | 0.14× | 10 |
| B00 BH | 181,350 | 173,239 | 73.24% | 8,111 | 0.00× | 11 |
| B00S A | 201,669 | 189,300 | 89.30% | 10,236 | 1.98× | 4 |
| B00S B2 | 200,695 | 190,777 | 90.78% | 9,902 | 0.10× | 1 |
| B00S BH | 200,194 | 189,661 | 89.66% | 10,533 | 0.00× | 3 |
| B06 A | 161,450 | 156,314 | 56.31% | 4,474 | 2.00× | 18 |
| B06 B2 | 165,816 | 160,298 | 60.30% | 5,364 | 0.64× | 17 |
| B06 BH | 171,925 | 164,872 | 64.87% | 7,053 | 0.00× | 16 |
| B06S A | 176,825 | 170,079 | 70.08% | 5,653 | 2.00× | 13 |
| B06S B2 | 177,861 | 171,300 | 71.30% | 6,405 | 0.58× | 12 |
| B06S BH | 175,195 | 167,423 | 67.42% | 7,772 | 0.00× | 15 |
| BOVA11 BH | 145,808 | 138,937 | 38.94% | 6,871 | 0.00× | 19 |

## Formação 2024

Patrimônio final em 30/06/2026, capital inicial R$ 100.000. Universo central.

| Regra / política | Sem IR (R$) | Com IR (R$) | Retorno líquido | IR pago (R$) | Giro anual acumulado | Rank líquido |
|---|---:|---:|---:|---:|---:|---:|
| R00 A | 174,938 | 166,555 | 66.55% | 7,391 | 1.00× | 5 |
| R00 B2 | 175,203 | 167,329 | 67.33% | 7,473 | 0.38× | 4 |
| R03 A | 171,215 | 162,575 | 62.57% | 7,552 | 1.00× | 8 |
| R03 B2 | 172,063 | 164,082 | 64.08% | 7,758 | 0.31× | 6 |
| R16 A | 165,358 | 157,958 | 57.96% | 6,502 | 1.00× | 10 |
| R16 B2 | 171,647 | 163,819 | 63.82% | 7,542 | 0.35× | 7 |
| B00 A | 161,282 | 154,520 | 54.52% | 5,978 | 1.00× | 15 |
| B00 B2 | 163,461 | 157,036 | 57.04% | 6,400 | 0.04× | 14 |
| B00 BH | 164,088 | 157,554 | 57.55% | 6,510 | 0.00× | 11 |
| B00S A | 176,925 | 167,468 | 67.47% | 8,224 | 1.00× | 3 |
| B00S B2 | 179,764 | 170,928 | 70.93% | 8,825 | 0.02× | 2 |
| B00S BH | 179,963 | 171,087 | 71.09% | 8,865 | 0.00× | 1 |
| B06 A | 150,005 | 145,643 | 45.64% | 3,904 | 1.00× | 18 |
| B06 B2 | 152,148 | 147,677 | 47.68% | 4,471 | 0.10× | 17 |
| B06 BH | 156,472 | 151,424 | 51.42% | 5,048 | 0.00× | 16 |
| B06S A | 162,589 | 157,124 | 57.12% | 4,759 | 1.00× | 12 |
| B06S B2 | 162,359 | 157,066 | 57.07% | 5,293 | 0.06× | 13 |
| B06S BH | 165,017 | 159,359 | 59.36% | 5,657 | 0.00× | 9 |
| BOVA11 BH | 139,618 | 133,676 | 33.68% | 5,943 | 0.00× | 19 |

## Formação 2025

Patrimônio final em 30/06/2026, capital inicial R$ 100.000. Universo central.

| Regra / política | Sem IR (R$) | Com IR (R$) | Retorno líquido | IR pago (R$) | Giro anual acumulado | Rank líquido |
|---|---:|---:|---:|---:|---:|---:|
| R00 A | 117,738 | 116,464 | 16.46% | 1,274 | 0.00× | 18 |
| R00 B2 | 117,738 | 116,464 | 16.46% | 1,274 | 0.00× | 18 |
| R03 A | 130,026 | 126,948 | 26.95% | 3,078 | 0.00× | 1 |
| R03 B2 | 130,026 | 126,948 | 26.95% | 3,078 | 0.00× | 1 |
| R16 A | 126,163 | 123,746 | 23.75% | 2,417 | 0.00× | 9 |
| R16 B2 | 126,163 | 123,746 | 23.75% | 2,417 | 0.00× | 9 |
| B00 A | 126,720 | 124,133 | 24.13% | 2,567 | 0.00× | 6 |
| B00 B2 | 126,720 | 124,133 | 24.13% | 2,567 | 0.00× | 6 |
| B00 BH | 126,720 | 124,133 | 24.13% | 2,567 | 0.00× | 6 |
| B00S A | 128,790 | 125,776 | 25.78% | 3,005 | 0.00× | 3 |
| B00S B2 | 128,790 | 125,776 | 25.78% | 3,005 | 0.00× | 3 |
| B00S BH | 128,790 | 125,776 | 25.78% | 3,005 | 0.00× | 3 |
| B06 A | 119,241 | 117,997 | 18.00% | 1,244 | 0.00× | 15 |
| B06 B2 | 119,241 | 117,997 | 18.00% | 1,244 | 0.00× | 15 |
| B06 BH | 119,241 | 117,997 | 18.00% | 1,244 | 0.00× | 15 |
| B06S A | 123,497 | 122,127 | 22.13% | 1,370 | 0.00× | 11 |
| B06S B2 | 123,497 | 122,127 | 22.13% | 1,370 | 0.00× | 11 |
| B06S BH | 123,497 | 122,127 | 22.13% | 1,370 | 0.00× | 11 |
| BOVA11 BH | 123,828 | 120,254 | 20.25% | 3,574 | 0.00× | 14 |

## Decomposição de R03

Valores em reais; diferença positiva favorece B2. O efeito fiscal inclui o reinvestimento do imposto e as mudanças de quantidades necessárias para financiá-lo. A diferença líquida não é sinônimo de economia de imposto.

| Formação | A líquido | B2 líquido | B00S BH líquido | Efeito carteira/executar B2−A sem IR | Diferença dos efeitos fiscais | B2−A líquido |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | 324,308 | 328,364 | 225,397 | 3,194 | 862 | 4,056 |
| 2021 | 263,097 | 266,303 | 262,064 | 1,689 | 1,517 | 3,206 |
| 2022 | 232,920 | 237,341 | 254,563 | 3,208 | 1,213 | 4,420 |
| 2023 | 178,134 | 180,051 | 189,661 | 1,713 | 205 | 1,918 |
| 2024 | 162,575 | 164,082 | 171,087 | 848 | 659 | 1,507 |
| 2025 | 126,948 | 126,948 | 125,776 | 0 | 0 | 0 |

## Vencedor A × B2 por formação

| Regra | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| R00 | B2 | B2 | B2 | B2 | B2 | TIE |
| R03 | B2 | B2 | B2 | B2 | B2 | TIE |
| R16 | B2 | B2 | B2 | B2 | B2 | TIE |
| B00 | A | B2 | B2 | B2 | B2 | TIE |
| B00S | A | B2 | B2 | B2 | B2 | TIE |
| B06 | A | B2 | B2 | B2 | B2 | TIE |
| B06S | A | B2 | B2 | B2 | A | TIE |

## Hipóteses e arquivos

O protocolo, as limitações, as fontes e os comandos estão em [protocolo_ir_100k.md](protocolo_ir_100k.md). As tabelas completas, incluindo conservative, estão em [comparison_rankings.csv](../research/ir_100k_results/comparison_rankings.csv). [yearly.csv](../research/ir_100k_results/yearly.csv) discrimina IR devido e efetivamente descontado por ano; [monthly.csv](../research/ir_100k_results/monthly.csv) mostra isenções, ganhos e perdas compensadas. [annual.csv](../research/ir_100k_results/annual.csv) contém retenção, exclusões, entradas financiadas, pesos e custo fiscal. [sensitivities.csv](../research/ir_100k_results/sensitivities.csv) contém todas as sensibilidades nas mesmas políticas. O ledger completo está em `research/ir_100k_results/ledger.json.gz`.

## Efeito do IR sobre o ranking

Comparação dentro do universo central, incluindo A, B2 e referências BH. Rank 1 admite empates.

| Formação | Líder sem IR | Líder com IR | Combinações que mudam de posição |
|---|---|---|---:|
| 2020 | R03 B2 | R03 B2 | 2 |
| 2021 | R00 B2 | R00 B2 | 11 |
| 2022 | B00S BH | B00S BH | 7 |
| 2023 | R00 B2 | B00S B2 | 7 |
| 2024 | B00S BH | B00S BH | 5 |
| 2025 | R03 A = R03 B2 | R03 A = R03 B2 | 4 |

As colunas `rank_gross`, `rank_net` e `rank_change_tax` em `comparison_rankings.csv` registram cada movimento. Ganhar posições após IR não significa maior retorno absoluto: todos os patrimônios líquidos permanecem sujeitos ao efeito fiscal indicado.
