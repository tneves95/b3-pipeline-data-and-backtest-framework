# Checkpoint — B00S V2, PR #4

Protocolo exclusivo: `7fea064`. Base imutável: `8d394e9` (PR #3). Somente retorno total bruto percentual, junho/2014 a junho/2026, com decisões PIT e B2 seletiva. Sem IR, aportes, custos ou patrimônio em reais. PR draft, sem merge.

## Lote 1: V0 e V10 concluídos

O replay das 12 janelas V0 coincide com o controle; os CSVs publicam literalmente seus retornos. A V10 escolhe por mediana de volume financeiro nos 126 pregões, depois sessões, volume total e ticker. Incumbentes PASS/INDETERMINATE ocupam vagas. Apenas FAIL comprovado autoriza saída; novas entradas são autofinanciadas pela função B2 herdada, conservando NAV e proporções dos sobreviventes.

As nove empresas iniciais V10 são BBDC4, ITUB4, CMIG4, TBLE3, CSMG3, SBSP3, PSSA3, TIMP3 e VIVT4. Seguros tem somente PSSA3, com 20%; cada outro setor tem duas posições de 10%. TBLE3 supera CPFE3 pela mediana histórica (24.744.079,5 contra 21.274.561,5), conforme cache congelado. As unidades e os pesos evoluem continuamente.

O spin-off compulsório XPBR31 pertence à vaga econômica herdada ITUB4, mas conta como emissora distinta na concentração. Não é uma nova compra BESST. Por isso o número físico de emissoras pode superar o de vagas voluntárias; ambos estão publicados. Tickers usam os aliases aceitos na etapa 1; direitos, classes e sucessoras acompanham a origem na atribuição.

## Retornos anuais (%)

| year | V0 | V10 | VVAL | VQ | IBOV | R03 B2 | BH padrão |
|---|---|---|---|---|---|---|---|
| 2014.0000 | -1.0459 | -2.1416 | ND | ND | -0.1643 | -45.0683 | 22.3021 |
| 2015.0000 | 2.0892 | -1.5886 | ND | ND | -2.9275 | 3.5198 | 11.8038 |
| 2016.0000 | 22.6682 | 18.4664 | ND | ND | 22.0721 | 33.7289 | 17.1925 |
| 2017.0000 | 10.2022 | 12.0781 | ND | ND | 15.6797 | 3.8081 | 1.8464 |
| 2018.0000 | 51.6276 | 51.6632 | ND | ND | 38.7626 | 66.3124 | 40.6323 |
| 2019.0000 | -5.5879 | -2.9562 | ND | ND | -5.8548 | 17.0398 | 18.9133 |
| 2020.0000 | -1.3833 | -1.2450 | ND | ND | 33.3971 | 28.4042 | 18.9660 |
| 2021.0000 | -3.5526 | -3.5219 | ND | ND | -22.2865 | -12.9730 | -11.5850 |
| 2022.0000 | 34.8217 | 29.9839 | ND | ND | 19.8342 | 45.3435 | 37.3725 |
| 2023.0000 | 14.7043 | 14.5138 | ND | ND | 4.9282 | 5.1083 | -2.6078 |
| 2024.0000 | 37.4777 | 45.9123 | ND | ND | 12.0640 | 27.8418 | -0.1868 |
| 2025.0000 | 27.0173 | 24.9935 | ND | ND | 23.8880 | 46.3224 | 12.6075 |

## Acumulados em cada junho (%)

| closing_year | V0 | V10 | VVAL | VQ | IBOV | R03 B2 | BH padrão |
|---|---|---|---|---|---|---|---|
| 2015.0000 | -1.0459 | -2.1416 | ND | ND | -0.1643 | -45.0683 | 22.3021 |
| 2016.0000 | 1.0215 | -3.6962 | ND | ND | -3.0870 | -43.1348 | 36.7384 |
| 2017.0000 | 23.9212 | 14.0876 | ND | ND | 18.3037 | -23.9549 | 60.2471 |
| 2018.0000 | 36.5639 | 27.8672 | ND | ND | 36.8534 | -21.0590 | 63.2059 |
| 2019.0000 | 107.0686 | 93.9275 | ND | ND | 89.9014 | 31.2887 | 129.5202 |
| 2020.0000 | 95.4978 | 88.1946 | ND | ND | 78.7832 | 53.6600 | 172.9300 |
| 2021.0000 | 92.7934 | 85.8516 | ND | ND | 138.4915 | 97.3058 | 224.6939 |
| 2022.0000 | 85.9443 | 79.3060 | ND | ND | 85.3399 | 71.7093 | 187.0781 |
| 2023.0000 | 150.6933 | 133.0689 | ND | ND | 122.1007 | 149.5683 | 294.3665 |
| 2024.0000 | 187.5561 | 166.8961 | ND | ND | 133.0463 | 162.3170 | 284.0822 |
| 2025.0000 | 295.3256 | 289.4343 | ND | ND | 161.1609 | 235.3507 | 283.3649 |
| 2026.0000 | 402.1320 | 386.7677 | ND | ND | 223.5469 | 390.6934 | 331.6976 |

## Comparação consolidada

| variant | periods | final_pct | cagr_pct | above_ibov_years | annual_close_max_drawdown_pct | annual_population_std_pct | final_rank |
|---|---|---|---|---|---|---|---|
| V0 | 12.0000 | 402.1320 | 14.3935 | 9.0000 | -10.2016 | 18.0736 | 1.0000 |
| V10 | 12.0000 | 386.7677 | 14.0977 | 8.0000 | -7.5397 | 18.5746 | 3.0000 |
| VVAL | 0.0000 | ND | ND | ND | ND | ND | ND |
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

## Giro unilateral (% do NAV)

| year | V0 | V10 | VVAL | VQ |
|---|---|---|---|---|
| 2015.0000 | 2.4433 | 0.0000 | ND | ND |
| 2016.0000 | 9.4586 | 7.7538 | ND | ND |
| 2017.0000 | 10.0000 | 10.0000 | ND | ND |
| 2018.0000 | 10.0000 | 10.0000 | ND | ND |
| 2019.0000 | 6.6667 | 0.0000 | ND | ND |
| 2020.0000 | 10.0000 | 0.0000 | ND | ND |
| 2021.0000 | 11.1111 | 0.0000 | ND | ND |
| 2022.0000 | 0.0000 | 0.0000 | ND | ND |
| 2023.0000 | 0.0000 | 0.0000 | ND | ND |
| 2024.0000 | 10.8541 | 13.1568 | ND | ND |
| 2025.0000 | 0.6271 | 0.0000 | ND | ND |

## Evidência e limitações

O inventário anterior ao cálculo tem 229 decisões empresa/ano e 29 companhias, todas B00S PASS do controle, incluindo cortes 2014, 2017, 2020, 2024 e 2025. `initial_pit_inventory.csv` e `coverage_by_year_sector.csv` mostram documentação, contagem e peso potencial. Lucro consolidado total não substitui lucro atribuível; capital social anterior a bonificação não é denominador validado; ausência documental não reprova qualidade.

As qualificações de seleção e eventos da etapa 1 continuam vigentes. Não foram reabertas pesquisas de proventos, certificados direitos antes incertos ou alterados screeners. A conciliação da V0 não torna a base integralmente certificada PIT. Atribuição inclui linha separada NUMERICAL_RESIDUAL para somar exatamente os decimais publicados, sem alterar retorno de ações. `redemption_transfers.csv` preserva a origem de recursos compulsoriamente transferidos.

## Reprodução e validação do lote 1

`python scripts/b00s_inventory.py`; `python scripts/b00s_variants.py --stage v10`; `python scripts/b00s_report.py`.
Dependências: pandas e `requirements-attribution.txt`. Replay offline, sem SQLite e sem escrita nas pastas protegidas. CSVs são fonte primária; planilha `results/b00s_four_variants.xlsx` contém resumo, retornos, composição, concentração e seleção. Manifesto registra SHA-256 dos insumos e resultados.

Validação inicial: 95 testes passaram (8 do experimento, 64 da atribuição e 23 da continuidade). Proteção SHA-256 dos 271 arquivos herdados verificada antes/depois. VVAL e VQ continuam em processamento nos próximos lotes deste mesmo PR; células ND neste checkpoint não são retornos zero.
