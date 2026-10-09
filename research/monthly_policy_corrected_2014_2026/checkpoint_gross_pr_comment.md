# Checkpoint corrigido — aportes sem vendas de rebalanceamento

Decisão: [retificação do coordenador no PR #6](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/6#issuecomment-6086144108).

Calculadas as cinco carteiras, 30/06/2014–30/06/2026, R$100.000 iniciais +144 aportes de R$2.500 = R$460.000. Resultado abaixo mantém os ativos no encerramento, sem imposto adicional. O bruto conserva os valores de proventos aceitos na base, inclusive os já líquidos na origem.

| Carteira | Patrimônio corrigido R$ | TIR % a.a. | Diferença PR5 R$ | Maior emissor % | HHI emissores | Vendas PR5 → corrigido |
|---|---:|---:|---:|---:|---:|---:|
| VVAL | 1.865.901,69 | 17,9260 | -2.149,17 | 18,36 | 0,1166 | 45 → 6 |
| BESST-10 BH | 1.767.443,92 | 17,2527 | 0,00 | 22,34 | 0,1194 | 0 → 0 |
| V0 | 1.670.906,27 | 16,5546 | 24.953,29 | 12,70 | 0,0614 | 88 → 10 |
| V10 | 1.619.829,36 | 16,1685 | -36.559,07 | 15,08 | 0,1033 | 23 → 2 |
| BH padrão | 1.270.936,41 | 13,1438 | 0,00 | 22,86 | 0,1450 | 0 → 0 |

V0 ultrapassa V10 no ranking corrigido. As duas carteiras BH reproduzem exatamente os patrimônios e TIRs do PR #5. Todas as 18 vendas voluntárias têm `CONFIRMED_MAINTENANCE_FAIL`, prova `FAIL_EXIT` + `base_status=FAIL` no livro congelado do PR #4 e data de junho. Direitos, resgates e conversões compulsórias permanecem separados no livro de eventos e no livro fiscal.

## Política executada

- PASS, INDETERMINATE e ausência da lista de compras não autorizam vendas. A evidência congelada de saída é reutilizada, sem nova coleta PIT.
- Entradas atualizam N e recebem apenas caixa disponível. Quando não há caixa, permanecem elegíveis sem posição até um aporte posterior.
- A identificação objetiva de vencedora em junho usa peso >=1,5/N e retorno PIT dos últimos 12 meses acima da mediana. O marcador persiste após diluição. Com N>15, sua referência para novas compras é2/N; com N<=15, retorna temporariamente a1/N sem apagar o marcador. Nunca se vende pelo peso.
- Os aportes são distribuídos proporcionalmente aos déficits positivos dessas referências. Referências podem somar mais de100%; compras nunca excedem o caixa.
- Para entrada ainda não financiada, uma unidade nominal existe somente no livro sombra de retorno PIT. Não cria ação nem caixa na carteira real.

## Reprodução e verificações

Executar `python scripts/run_monthly_corrected.py --mode GROSS` e `python -m pytest -q tests/test_monthly_policy_corrected.py tests/test_monthly_tax.py`.

43 testes aprovados: cenários sintéticos obrigatórios, dados calculados, 144 aportes, caixa não negativo, custo médio/isencão/perdas/IRRF/DARF, eventos fiscais e proteção dos hashes legados. Os testes sintéticos passam por execução do motor para vencedora acima de2×, entrada sem dinheiro e saída exclusivamente FAIL; cobrem também retomada de compras após diluição e suspensão/restauração da referência quando N cruza15.

Os arquivos novos ficam em `research/monthly_policy_corrected_2014_2026/`. O arquivo `consolidated_policy_corrected.csv` é o resumo; `GROSS/` contém operações, posições, revisões, fluxos, eventos e trajetórias. `policy_freeze.json` registra a regra e hashes de evidências. Os arquivos antigos de PR5 e PR6 são legados preservados; `research/monthly_tax_2014_2026/LEGACY_ONLY.json` identifica seus hashes. A lógica fiscal existente é importada sem alterações.

## Limitações preservadas

BESST-10 BH mantém TIMP3 no cenário condicional de NET, sem nova investigação. Mantidas as bases provisórias de seleção/proventos e a pendência BBDC4/2014. TWR permanece ND nas datas de fluxo sem marcação exata (V0 e VVAL); patrimônio final e TIR são calculáveis. Compras fracionárias teóricas, sem custos, reinvestimentos de proventos na convenção data-ex do legado. XP é contado como emissor distinto na concentração e não pode ser vendido somente por FAIL do pai. Nenhuma certificação documental adicional é presumida.

A tributação da política antiga está suspensa. O próximo checkpoint aplica CG_ONLY sobre este motor corrigido, com reserva e pagamento do imposto reduzindo as compras. JCP/dividendos adicionais somente após esta validação bruta.
