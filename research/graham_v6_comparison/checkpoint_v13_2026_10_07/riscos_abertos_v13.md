# Riscos abertos e regra de parada — v13

A [retificação do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/1#issuecomment-6047700161) determina concluir a reconstrução dirigida e passar à análise estratégica. A v11.2 continua provisória; os cenários v12 e os limites de sua documentação continuam preservados. Nenhum item abaixo implica certificação ou nova seleção retrospectiva.

| Item | Efeito calculado / evidência | Materialidade e decisão desta rodada |
|---|---|---|
| Quatro grupos Barsi | +2,144873 pp na manutenção B00S/2020, com reconstrução das continuidades TIM/VIVT | Concluído no índice fracionário; impacto conjunto material. As quatro contribuições individuais são menores que 1 pp nessa carteira; não aprofundar centavos. |
| R16 × B00S/2020 | R16 126,853075%; B00S conjunto 124,414052%; limite residual 125,713571% | Folga central 2,439023 pp e folga ao limite 1,139504 pp. Caixa ±20% dos quatro grupos produz B00S de 116,998296% a 132,280035%: há inversão no stress. Superioridade geral inconclusiva. |
| Renovação 2022 | B00S ganha R03 por 2,6805 pp no central; perde por 1,4142 pp no conservador | Composição inverte o vencedor; não declarar liderança robusta. |
| Renovação 2024 | B00S ganha R00 por 0,0871 pp no central; perde por 1,9591 pp no conservador | Margem inferior ao limiar de 1 pp e diferença metodológica demonstrada. Conclusão inconclusiva, sem pesquisa adicional de centavos. |
| TIM no universo de seleção | Zeros/lacunas nos lucros 2021–2024, ausência em 2025, mudança de CNPJ | Estrutural: continuidade da posição foi reconstruída; continuidade de fundamentos não demonstrada. Pode alterar seleção e ranking em novo estudo; não inventar lucros ou ampliar lista congelada. |
| VIVT PN→ON na seleção | Conversão de posição 1:1 documentada; histórico DPS PN transportado para ON na seleção herdada | Risco estrutural de normalização do sinal B06; não corrigido por apenas acertar o retorno. Efeito de nova seleção não calculado. |
| Universo / disponibilidade histórica | 206/206 recebimentos declarados antes do corte; nomes deslistados presentes | Evidência parcial de disponibilidade. Completude do universo e rastreio de todas as observações fundamentais não certificados; efeito não limitado. |
| Preço do sinal e execução | B06 usa o fechamento de formação e compra no mesmo fechamento | Implementação otimista. Nova simulação de execução exigiria política explícita; não alterada nesta rodada. |
| Caixa residual Barsi | 34,7553% do patrimônio final v9 de B00S/2020 ainda aproximado | Não usar cobertura de eventos como certificação. Eventos desconhecidos não têm teto de impacto demonstrado. |
| Reinvestimento ex vs pagamento | Todos os novos proventos seguem o motor bruto/data-ex; há pagamentos posteriores ao corte | Teórico; não comprova dinheiro disponível antes de liquidação/pagamento. Direitos ITSA seguem a política específica v11.2. |
| Restituições de capital VIVT | Manter em caixa reduz B00S manutenção/2020 em 0,3347 pp; remover pagamentos reduz 1,6285 pp | Primeiro é sensibilidade econômica; segundo é atribuição contrafactual, não retorno observado. Outras distribuições extraordinárias do universo não foram catalogadas integralmente. |
| Frações TIM/VIVT | Fatores líquidos 1 e 2 reproduzidos; avisos de leilão existem | Frações teóricas preservadas; leilão real não simulado. Risco operacional para carteira pequena; não presumir preço/data do leilão ou recebimento. |
| PSSA março/2026 | Aviso inicial 0,54228396511 vs B3 0,54231784082; ratificação em imagem | Cenários executados; −0,00001913 pp em B00S manutenção/2020. Provisório, sem necessidade de continuar pesquisa de centavos. |
| 12 pares Graham e quatro divergências B3 v12 | Matrizes, valores e incertezas preservados | Não são prioridade conforme retificação. Não presumir ausência de eventos por retorno do programa sem erro. |
| Concentração de ganhos | CPLE3: 54,9773 pp em R00 manutenção/2020; CSMG3: 124,0809 pp em R03/R16 manutenção/2021 | Dependência de poucos vencedores. Contrafactual de substituir maior contribuidor por caixa é ex post; não novo portfólio investível. |
| Risco diário | 32 trajetórias Graham + seis BOVA repetidas por mecanismo; quatro Graham incompletas; Barsi agregado não estimado | Sem conclusão comparável de volatilidade/drawdown Barsi × Graham; não interpolar caixa anual. |
| Seis coortes sobrepostas | Mesmo término; 2025 tem só um período | Frequências não são amostras independentes nem probabilidade de sucesso. Nenhuma significância estatística estimada. |

`matriz_confianca_materialidade_v13.csv` contém os 96 confrontos numéricos. Os intervalos combinam cenários efetivamente executados, sem probabilidade associada. Não são limites universais de erro. A classificação de liderança compartilhada respeita a identidade de R03/R16 na manutenção de 2021; não considera dois intervalos de erro independentes para a mesma carteira.

**Parada recomendada:** encerrar a auditoria v13 e o estudo exploratório, com as conclusões condicionais do relatório. Não restam decisões necessárias para reproduzir este checkpoint. Certificação integral, refazer o universo/sinais e simular caixa/frações executáveis seriam outra missão com escopo metodológico próprio.
