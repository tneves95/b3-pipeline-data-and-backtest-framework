# Checkpoint — B00S V2, PR #4

Protocolo exclusivo: `7fea064`. Base imutável: `8d394e9` (PR #3). Somente retorno total bruto percentual, junho/2014 a junho/2026, com decisões PIT e B2 seletiva. Sem IR, aportes, custos ou patrimônio em reais. PR draft, sem merge.

## Lote 1: V0 e V10 concluídos

O replay das 12 janelas V0 coincide com o controle; os CSVs publicam literalmente seus retornos. A V10 escolhe por mediana de volume financeiro nos 126 pregões, depois sessões, volume total e ticker. Incumbentes PASS/INDETERMINATE ocupam vagas. Apenas FAIL comprovado autoriza saída; novas entradas são autofinanciadas pela função B2 herdada, conservando NAV e proporções dos sobreviventes.

As nove empresas iniciais V10 são BBDC4, ITUB4, CMIG4, TBLE3, CSMG3, SBSP3, PSSA3, TIMP3 e VIVT4. Seguros tem somente PSSA3, com 20%; cada outro setor tem duas posições de 10%. TBLE3 supera CPFE3 pela mediana histórica (24.744.079,5 contra 21.274.561,5), conforme cache congelado. As unidades e os pesos evoluem continuamente.

O spin-off compulsório XPBR31 pertence à vaga econômica herdada ITUB4, mas conta como emissora distinta na concentração. Não é uma nova compra BESST. Por isso o número físico de emissoras pode superar o de vagas voluntárias; ambos estão publicados. Tickers usam os aliases aceitos na etapa 1; direitos, classes e sucessoras acompanham a origem na atribuição.

## Retornos anuais (%)

| year | V0 | V10 | VVAL | VQ | IBOV | R03 B2 | BH padrão |
|---|---|---|---|---|---|---|---|
| 2014.0000 | -1.0459 | -2.1416 | 10.0067 | ND | -0.1643 | -45.0683 | 22.3021 |
| 2015.0000 | 2.0892 | -1.5886 | 9.5427 | ND | -2.9275 | 3.5198 | 11.8038 |
| 2016.0000 | 22.6682 | 18.4664 | 10.0605 | ND | 22.0721 | 33.7289 | 17.1925 |
| 2017.0000 | 10.2022 | 12.0781 | 9.4559 | ND | 15.6797 | 3.8081 | 1.8464 |
| 2018.0000 | 51.6276 | 51.6632 | 73.9026 | ND | 38.7626 | 66.3124 | 40.6323 |
| 2019.0000 | -5.5879 | -2.9562 | -19.6361 | ND | -5.8548 | 17.0398 | 18.9133 |
| 2020.0000 | -1.3833 | -1.2450 | 16.7805 | ND | 33.3971 | 28.4042 | 18.9660 |
| 2021.0000 | -3.5526 | -3.5219 | -5.8404 | ND | -22.2865 | -12.9730 | -11.5850 |
| 2022.0000 | 34.8217 | 29.9839 | 12.0674 | ND | 19.8342 | 45.3435 | 37.3725 |
| 2023.0000 | 14.7043 | 14.5138 | -5.5886 | ND | 4.9282 | 5.1083 | -2.6078 |
| 2024.0000 | 37.4777 | 45.9123 | 21.3616 | ND | 12.0640 | 27.8418 | -0.1868 |
| 2025.0000 | 27.0173 | 24.9935 | 13.8293 | ND | 23.8880 | 46.3224 | 12.6075 |

## Acumulados em cada junho (%)

| closing_year | V0 | V10 | VVAL | VQ | IBOV | R03 B2 | BH padrão |
|---|---|---|---|---|---|---|---|
| 2015.0000 | -1.0459 | -2.1416 | 10.0067 | ND | -0.1643 | -45.0683 | 22.3021 |
| 2016.0000 | 1.0215 | -3.6962 | 20.5043 | ND | -3.0870 | -43.1348 | 36.7384 |
| 2017.0000 | 23.9212 | 14.0876 | 32.6277 | ND | 18.3037 | -23.9549 | 60.2471 |
| 2018.0000 | 36.5639 | 27.8672 | 45.1688 | ND | 36.8534 | -21.0590 | 63.2059 |
| 2019.0000 | 107.0686 | 93.9275 | 152.4523 | ND | 89.9014 | 31.2887 | 129.5202 |
| 2020.0000 | 95.4978 | 88.1946 | 102.8806 | ND | 78.7832 | 53.6600 | 172.9300 |
| 2021.0000 | 92.7934 | 85.8516 | 136.9249 | ND | 138.4915 | 97.3058 | 224.6939 |
| 2022.0000 | 85.9443 | 79.3060 | 123.0875 | ND | 85.3399 | 71.7093 | 187.0781 |
| 2023.0000 | 150.6933 | 133.0689 | 150.0083 | ND | 122.1007 | 149.5683 | 294.3665 |
| 2024.0000 | 187.5561 | 166.8961 | 136.0363 | ND | 133.0463 | 162.3170 | 284.0822 |
| 2025.0000 | 295.3256 | 289.4343 | 186.4574 | ND | 161.1609 | 235.3507 | 283.3649 |
| 2026.0000 | 402.1320 | 386.7677 | 226.0724 | ND | 223.5469 | 390.6934 | 331.6976 |

## Comparação consolidada

| variant | periods | final_pct | cagr_pct | above_ibov_years | annual_close_max_drawdown_pct | annual_population_std_pct | final_rank |
|---|---|---|---|---|---|---|---|
| V0 | 12.0000 | 402.1320 | 14.3935 | 9.0000 | -10.2016 | 18.0736 | 1.0000 |
| V10 | 12.0000 | 386.7677 | 14.0977 | 8.0000 | -7.5397 | 18.5746 | 3.0000 |
| VVAL | 12.0000 | 226.0724 | 10.3510 | 5.0000 | -19.6361 | 21.5913 | ND |
| VQ | 0.0000 | ND | ND | ND | ND | ND | ND |
| IBOV | 12.0000 | 223.5469 | 10.2795 | 0.0000 | -22.2865 | 16.8453 | 5.0000 |
| R03 B2 | 12.0000 | 390.6934 | 14.1741 | 9.0000 | -45.0683 | 28.6511 | 2.0000 |
| BH padrão | 12.0000 | 331.6976 | 12.9618 | 6.0000 | -11.5850 | 14.9152 | 4.0000 |

O drawdown acima usa somente fechamentos anuais; não mede a pior perda intradiária/diária. O desvio é populacional descritivo das 12 observações. O ranking só compara séries completas e compatíveis; nenhum caso com lacuna fundamentalista é declarado vencedor.

## Concentração: formação e encerramento

| variant | year | companies | eligible_lineage_slots | largest_company_pct | top5_pct | issuer_hhi | sector_hhi |
|---|---|---|---|---|---|---|---|
| V0 | 2014.0000 | 20.0000 | 20.0000 | 20.0000 | 60.0000 | 0.0920 | 0.2000 |
| V0 | 2026.0000 | 21.0000 | 20.0000 | 20.2791 | 56.9929 | 0.0962 | 0.2155 |
| V10 | 2014.0000 | 9.0000 | 9.0000 | 20.0000 | 60.0000 | 0.1200 | 0.2000 |
| V10 | 2026.0000 | 11.0000 | 10.0000 | 23.3148 | 70.7243 | 0.1442 | 0.2368 |
| VVAL | 2014.0000 | 2.0000 | 2.0000 | 50.0000 | 100.0000 | 0.5000 | 0.5000 |
| VVAL | 2026.0000 | 2.0000 | 2.0000 | 57.4833 | 100.0000 | 0.5112 | 0.5112 |

## Composição final, junho/2026 (peso físico %)

| variant | ticker | weight_pct |
|---|---|---|
| V0 | ABCB4 | 2.7534 |
| V0 | AXIA7 | 1.1156 |
| V0 | BBAS3 | 2.0839 |
| V0 | BBDC4 | 1.7716 |
| V0 | BBSE3 | 6.9406 |
| V0 | BMGB4 | 7.3595 |
| V0 | CMIG4 | 1.0473 |
| V0 | CPFE3 | 2.2607 |
| V0 | CPLE3 | 3.1554 |
| V0 | CSMG3 | 16.0414 |
| V0 | ELET3 | 4.3540 |
| V0 | EQTL3 | 3.1319 |
| V0 | ITUB4 | 3.4098 |
| V0 | PSSA3 | 20.2791 |
| V0 | SANB4 | 1.8737 |
| V0 | SAPR4 | 6.3722 |
| V0 | TAEE4 | 1.4853 |
| V0 | TBLE3 | 1.1976 |
| V0 | TIMS3 | 4.4636 |
| V0 | TRPL4 | 3.2687 |
| V0 | VIVT3 | 5.5204 |
| V0 | XPBR31 | 0.1143 |
| V10 | BBDC4 | 5.0017 |
| V10 | BBSE3 | 7.8207 |
| V10 | CMIG4 | 5.9137 |
| V10 | CSMG3 | 23.3148 |
| V10 | ITUB4 | 9.6271 |
| V10 | PSSA3 | 22.9018 |
| V10 | SAPR4 | 7.0600 |
| V10 | TBLE3 | 6.7624 |
| V10 | TIMS3 | 5.0409 |
| V10 | VIVT3 | 6.2343 |
| V10 | XPBR31 | 0.3226 |
| VVAL | BBDC4 | 42.5167 |
| VVAL | TBLE3 | 57.4833 |

## Giro unilateral (% do NAV)

| year | V0 | V10 | VVAL | VQ |
|---|---|---|---|---|
| 2015.0000 | 2.4433 | 0.0000 | 0.0000 | ND |
| 2016.0000 | 9.4586 | 7.7538 | 0.0000 | ND |
| 2017.0000 | 10.0000 | 10.0000 | 0.0000 | ND |
| 2018.0000 | 10.0000 | 10.0000 | 0.0000 | ND |
| 2019.0000 | 6.6667 | 0.0000 | 0.0000 | ND |
| 2020.0000 | 10.0000 | 0.0000 | 0.0000 | ND |
| 2021.0000 | 11.1111 | 0.0000 | 0.0000 | ND |
| 2022.0000 | 0.0000 | 0.0000 | 0.0000 | ND |
| 2023.0000 | 0.0000 | 0.0000 | 0.0000 | ND |
| 2024.0000 | 10.8541 | 13.1568 | 0.0000 | ND |
| 2025.0000 | 0.6271 | 0.0000 | 0.0000 | ND |

## Evidência e limitações

O inventário anterior ao cálculo tem 229 decisões empresa/ano e 29 companhias, todas B00S PASS do controle, incluindo cortes 2014, 2017, 2020, 2024 e 2025. `initial_pit_inventory.csv` e `coverage_by_year_sector.csv` mostram documentação, contagem e peso potencial. Lucro consolidado total não substitui lucro atribuível; capital social anterior a bonificação não é denominador validado; ausência documental não reprova qualidade.

As qualificações de seleção e eventos da etapa 1 continuam vigentes. Não foram reabertas pesquisas de proventos, certificados direitos antes incertos ou alterados screeners. A conciliação da V0 não torna a base integralmente certificada PIT. Atribuição inclui linha separada NUMERICAL_RESIDUAL para somar exatamente os decimais publicados, sem alterar retorno de ações. `redemption_transfers.csv` preserva a origem de recursos compulsoriamente transferidos.

## Reprodução e validação do lote 1

`python scripts/b00s_inventory.py`; `python scripts/b00s_variants.py --stage v10`; `python scripts/b00s_report.py`.
Dependências: pandas e `requirements-attribution.txt`. Replay offline, sem SQLite e sem escrita nas pastas protegidas. CSVs são fonte primária; planilha `results/b00s_four_variants.xlsx` contém resumo, retornos, composição, concentração e seleção. Manifesto registra SHA-256 dos insumos e resultados.

Validação inicial: 95 testes passaram (8 do experimento, 64 da atribuição e 23 da continuidade). Proteção SHA-256 dos 271 arquivos herdados verificada antes/depois. Células ND não são retornos zero.


## Lote 2: VVAL executada, cobertura documental restrita

Apenas BBDC4 e TBLE3 tiveram admissão comprovada neste lote, em junho/2014, com pesos de 50% cada. Dos pesos potenciais da B00S-base de 2014, representam 6%; os outros 94% são afetados por indeterminação documental. Bancos e energia são os únicos setores formados. Não há novas admissões comprovadas nos cortes seguintes; incumbentes ficam sob B2, mesmo quando valuation/qualidade atualizados são ND. TBLE3 sai apenas no FAIL da base em 2023; depois a exposição fica integralmente em BBDC4. Esta concentração decorre da cobertura, não demonstra superioridade ou inferioridade da filosofia econômica.

A VVAL restrita acumula **+226,0724%**, CAGR **10,3510%**, e supera o IBOV em **5/12** anos. **Não é uma conclusão sobre a VVAL de universo integral.** P/L normalizado inicial: BBDC4 10,9441 e TBLE3 14,4110. A V2 manteve 15/25, 4%, 20% e prêmio nominal sobre inflação de 6 p.p.; nenhum prêmio de reinvestimento foi concedido sem os quatro requisitos documentados. Bazin 6% e Graham 22,5 são somente diagnósticos separados.

Normalização: mediana de cinco lucros anuais atribuíveis, corrigidos do fim de cada exercício até o IPCA de maio já publicado em junho; não entra IPCA de junho. Originais IBGE e série SGS 433 estão arquivados. Capitalização: capital **emitido** por classe, cada qual a seu preço observado, sem proxy ON/PN; convenção conservadora inclui tesouraria, e não é usada como denominador certificado de LPA. Eventos após o último FRE tornam a capitalização ND até conciliação. O payout FRE é o divulgado sobre lucro ajustado; convenções de reservas e JCP líquido impedem tratá-lo automaticamente como retenção bruta comprovada.

As comparativas conhecidas do Bradesco 2010–2012 mantêm exatamente o lucro atribuível entre entregas sucessivas, inclusive após a ênfase IFRS 11. Na Tractebel, usa-se o lucro de 2012 reapresentado (1.490.454 mil, anteriormente 1.499.497 mil), sem alterar o exercício determinante da mediana. Os pareceres e a decisão estão em `inputs/valuation_perimeter_reviews.json`; a aprovação é exclusiva do valuation de entrada de 2014, não de VQ.

PSSA3 permanece ND: ajustes de abertura 2012 e integração/extraordinários exigem ponte histórica. O relatório recuperado registra ganho COFINS de aproximadamente 702 milhões em 2013, mas sua data de criação não certifica a publicação antes do corte. CSMG3 permanece ND pela ponte dos ajustes contábeis e referência do parecer ao ICMS não provisionado. Nenhuma foi rotulada como empresa ruim.

Extrato dirigido: 134.852 fatos contábeis, 26.671 registros FRE e 2.630 registros de pareceres, 32 arquivos CVM com hashes. Há P/L mecânico calculável em 198/229 decisões, mas só 2 decisões de entrada aprovadas neste lote. As restantes 227 estão indeterminadas. Lucro total consolidado, LPA sem ajustes e ROE de não financeiras não são substitutos dos indicadores exigidos. As subclasses PN são vinculadas ao ID do capital emitido, não a linhas de capital autorizado/subscrito de outra composição.

Reprodução adicional: `python scripts/b00s_fundamentals.py`; `python scripts/b00s_variants.py --stage vval`. As decisões JSON e seu SHA-256 são congelados antes do replay. Treze testes adicionais validam classes, lucro real, canais de preço, seis dimensões não compensatórias e bloqueio de fontes futuras. A proteção complementar inclui 286 arquivos do PR #3, além da lista herdada de 271.

## Sensibilidades e impacto das lacunas

| case | periods | final_pct | difference_pp | entry_decisions_different_from_vval |
|---|---|---|---|---|
| VVAL_12_20 | 12.0000 | 177.2703 | -48.8021 | 1.0000 |
| VVAL_15_25 | 12.0000 | 226.0724 | 0.0000 | 0.0000 |
| VVAL_18_30 | 12.0000 | 226.0724 | 0.0000 | 0.0000 |
| BAZIN_6_DIAGNOSTIC | 0.0000 | ND | ND | 2.0000 |
| GRAHAM_22_5_DIAGNOSTIC | 12.0000 | 177.2703 | -48.8021 | 1.0000 |
| VVAL_ALL_UNKNOWN_INCLUDED | 12.0000 | 402.1320 | 176.0595 | 30.0000 |
| VQ_ALL_UNKNOWN_INCLUDED | 12.0000 | 402.1320 | 0.0000 | 30.0000 |

As faixas 12/20, 15/25 e 18/30 usam a mesma exigência de reinvestimento e a mesma cobertura de perímetro. Na faixa conservadora, TBLE3 não passa sem comprovar reinvestimento; isso altera uma compra inicial. O caso principal não é alterado por estes resultados.

Foram executados 65 cenários previamente simétricos: 52 têm 12 janelas. Além dos sete acima, cada uma das 29 companhias é incluída isoladamente na VVAL quando indeterminada e retirada isoladamente da coorte hipotética VQ que admite todos os indeterminados. `sensitivity_annual_pct.csv`, `sensitivity_attribution.csv` e `sensitivity_reviews.csv` detalham retornos, contribuições e compras. São trajetórias condicionais, não limites matemáticos nem nova estratégia principal.

Em 12 inclusões isoladas VVAL, surge uma única entrada elegível em revisão posterior e nenhum incumbente permanece elegível para nova compra. O alvo de 100% para a entrada, aplicado literalmente ao financiador herdado, zeraria incumbentes não FAIL. O motor **bloqueia essa operação**, registrando companhia e ano; não cria uma regra de financiamento após ver rentabilidades. Esses cenários estão ND por `UNRESOLVED_ENTRY_FUNDING_WOULD_LIQUIDATE_NONFAIL`. O 13º cenário sem trajetória é o diagnóstico Bazin, sem posição inicial comprovada. As quatro séries principais não encontram esse caso de financiamento.
