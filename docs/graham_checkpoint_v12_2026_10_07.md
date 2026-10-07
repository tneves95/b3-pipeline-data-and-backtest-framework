# Checkpoint v12 — auditoria dos alertas e comparabilidade

**A baseline continua sendo a v11.2 provisória.** Este checkpoint executa a [missão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/1#issuecomment-6047125391) e acrescenta cenários separados. Não substitui v10/v11.1/v11.2, não altera seleções nem o motor v6 e não certifica o estudo. Corte econômico: 30/06/2026; capital inicial: R$ 10.000 por carteira. PR #1 permanece em rascunho.

Resultados e matrizes: [checkpoint_v12_2026_10_07](../research/graham_v6_comparison/checkpoint_v12_2026_10_07/). Fontes originais comprimidas, fatos e referências: [audit_v12_inputs](../research/graham_v6_comparison/audit_v12_inputs/). `*_pp` significa pontos percentuais; retornos sem esse sufixo são frações.

## 45/45 alertas classificados e quantificados

| Classificação principal | Quantidade | Decisão no cenário separado |
|---|---:|---|
| Sem exposição econômica Graham | 18 | Preservar: 14 TGMA3, três GRND3 anteriores à formação e um DXCO3 |
| Mesmo evento/agregação | 11 | Preservar: dez CMIG3 e um CPLE3 |
| Parcela adicional confirmada com exposição | 9 | Adicionar oito JCP GRND3 e um JCP SLCE3 |
| Diferença documental | 7 | Substituir três valores CPLE3; manter quatro divergências abertas |

A classificação econômica anterior à triagem por exposição também está no CSV. Assim, uma parcela de GRND3 pode estar documentalmente confirmada e continuar sem efeito porque seu direito antecede a formação. Exposição foi verificada nas quantidades da data-com, por carteira, mecanismo e janela; não apenas na lista de tickers.

As dez linhas CMIG3 são metades de totais já presentes. Os avisos confirmam duas parcelas iguais, incluindo pagamentos após o corte; a convenção legada reconhece o direito integral na ex. Não se adicionou a metade novamente. O total de abril/2025 tem diferença residual de arredondamento de R$ 0,00000000080 por ação no legado, preservada e explicitada. Na Copel, R$ 0,19041222 é a soma de R$ 0,15395195 e R$ 0,03646027 já lançados. Nenhuma razão observada foi automaticamente convertida por 0,85.

O [histórico oficial da Grendene](https://ri.grendene.com.br/PT/Informacoes-Financeiras/Historico-de-Dividendos) confirma os oito JCP brutos distintos dos dividendos da mesma data. Afetam a manutenção formada em 2022, sem exposição na renovação quando esses direitos ocorreram. O [aviso da SLC](https://api.mziq.com/mzfilemanager/v2/d/a975c39b-3eca-4ad8-9330-2c0a0b8d1060/3b6ef6ae-acf9-230a-eb06-847e55ee90b9?origin=1) confirma JCP bruto de R$ 0,04529051, ex em 15/12/2025, pagamento em 23/12/2025, distinto do dividendo. Afeta manutenções R03/R16 de 2020, 2023 e 2024.

Os [avisos retificadores da Copel de abril/2025](https://api.mziq.com/mzfilemanager/v2/d/16a31b1b-5ecd-4214-a2e0-308a2393e330/c71f7177-6e9c-6fa9-8329-b3a4e5668038?origin=1) e [janeiro/2026](https://api.mziq.com/mzfilemanager/v2/d/16a31b1b-5ecd-4214-a2e0-308a2393e330/9e7c31ff-8290-49b4-d586-e043b31e16dc?origin=2) prevalecem sobre a tabela de RI desatualizada. Foram substituídos R$ 0,39745756 por 0,39850301; 0,45460171311 por 0,45453469202; e 0,37041621069 por 0,37036160091. São revisões por ações em tesouraria, não novos pagamentos.

| Formação / manutenção | Baseline v11.2 | Cenário documental v12 | Efeito |
|---|---:|---:|---:|
| 2020 R00 | 149,3139690% | 149,3203313% | +0,0063624 pp |
| 2020 R03 | 136,3945229% | 136,4464114% | +0,0518886 pp |
| 2020 R16 | 126,8530747% | 126,9170618% | +0,0639872 pp |
| 2022 R00 | 118,8875956% | 119,8512383% | +0,9636427 pp |
| 2022 R03 | 155,8483440% | 156,4678286% | +0,6194846 pp |
| 2022 R16 | 104,0184411% | 104,9806008% | +0,9621597 pp |

As 36 carteiras/mecanismos foram recalculadas. Na renovação 2020 os efeitos são +0,004727 pp, +0,002914 pp e +0,002339 pp em R00/R03/R16. **Nenhuma mudança nos 96 lugares dos rankings centrais.** O efeito conjunto foi recalculado: somar efeitos isolados subestima a interação dos oito reinvestimentos GRND3. Em R00/2022, a soma isolada é 0,921215 pp, enquanto o efeito conjunto é 0,963643 pp.

As quatro divergências mantidas são ENAT3/2023, ITSA3/2021, PNVL3/2024 e SLCE3/2020. Valores próximos sugerem revisões/arredondamento, mas isso não autoriza um novo direito. A tabela atual da Panvel confirma o valor legado da quarta parcela, sem resolver a origem da versão B3. Foram simuladas separadamente a substituição pela versão B3 e a hipótese não comprovada de adicionar integralmente a linha. Os maiores efeitos absolutos dessas hipóteses são, respectivamente por ativo, 0,395179 pp, 0,071506 pp, 0,179036 pp e 0,600309 pp; nenhuma muda o ranking isoladamente. **Esses extremos pertencem apenas aos cenários executados. Não limitam eventos desconhecidos e não são correções aceitas.**

Os arquivos obrigatórios são [matriz_45_alertas_classificados.csv](../research/graham_v6_comparison/checkpoint_v12_2026_10_07/matriz_45_alertas_classificados.csv) e [impacto_alertas_por_carteira.csv](../research/graham_v6_comparison/checkpoint_v12_2026_10_07/impacto_alertas_por_carteira.csv), com 1.620 combinações alerta/carteira/mecanismo. Identificam ISIN B3, eventos legados, com/ex, pagamento disponível, tipo, valores, fonte, hash da linha local e do documento quando coletado. A base B3 local não conserva identificador documental nem pagamento: essa limitação permanece explícita.

## Comparabilidade Barsi por posição e ano

O diagnóstico cobre **1.212 registros**: 606 anuais e 606 de manutenção, com pesos, retornos v9, cobertura, referência e hash. Há 1.044 registros com aproximação de caixa v9, 100 anuais de 2020 apoiados no motor v8 e 68 com checkpoints v6. Reproduzir um checkpoint ou calcular por eventos não prova completude dos documentos.

O aprofundamento foi limitado a **BBSE3**, com 12 direitos nominais reconstruídos da [tabela oficial](https://www.bbseguridaderi.com.br/servicos-aos-acionistas/dividendos-e-recompras), e ao reaproveitamento das mesmas classes **SBSP3, CSMG3 e ENBR3** já calculadas no Graham. Isso oferece alternativas a 184 registros, sem reconstruir indiscriminadamente o BESST. Não foram usados SAPR3 no lugar de SAPR4, CPLE3 no lugar de CPLE6 ou classes ON no lugar de PN.

As alternativas usam as mesmas datas de junho, preços nominais, motor v6, proventos brutos e reinvestimento na ex, sem custos/impostos. BBSE3 usa a coluna nominal; a atualização monetária posterior da tabela é preservada como evidência, sem antecipá-la na ex. A completude de eventos estruturais ainda não está certificada. As demais posições mantêm os valores v9: o resultado combinado é uma **comparação parcial de método**, não uma nova família Barsi integralmente comparável.

| Estratégia, formação 2020 | Efeito da substituição parcial na manutenção | Efeito na renovação |
|---|---:|---:|
| B00 | −0,346210 pp | +0,579536 pp |
| B00S | −0,727041 pp | +1,073311 pp |
| B06 | +1,256444 pp | +1,289541 pp |
| B06S | +1,759022 pp | +2,109425 pp |

BBSE3, isoladamente, passa de +132,1172% a +140,9123% na manutenção 2020: **+0,879511 pp em B00S**, com peso inicial de 10%. SBSP3 produz −1,606552 pp nessa carteira; ENBR3 coincide com a âncora herdada. A substituição parcial conjunta também conserva os rankings centrais.

A folga baseline R16 frente ao limite superior v9 de B00S é **0,523449 pp**. Ao substituir somente BBSE3 no limite superior, removendo a contribuição superior antiga dessa posição, B00S chega a **126,726474%** e a folga cai a **0,126601 pp**. Não se somou a revisão central ao limite antigo, o que contaria duas vezes a sensibilidade de caixa da BBSE3. Esse exercício é deliberadamente isolado; a alternativa conjunta inclui também a revisão negativa da SBSP3.

O menor conjunto aritmético capaz de inverter o confronto pode conter **uma posição de 10%**, caso sua revisão exceda **5,234492 pp acima do próprio limite superior v9**, mantendo os demais limites. Isso identifica materialidade, não demonstra um erro. Após BBSE3, o patamar residual equivalente é 1,266009 pp em outra posição de 10%. As maiores exposições ainda aproximadas são PSSA3, TIMP3→TIMS3, VIVT4→VIVT3 e SAPR4. Priorizar a auditoria individual delas; sem limites documentados para os demais erros, não existe conjunto mínimo comprovadamente suficiente para certificar toda a ordem.

**Os envelopes v9 são sensibilidades determinísticas de caixa, não intervalos de confiança. Não há superioridade robusta ou certificada de R16.**

| Manutenção 2020 central | Patrimônio final v9 com cálculo por eventos disponível após esta rodada | Antes: somente âncoras integrais herdadas |
|---|---:|---:|
| B00 | 16,0830% | 3,7967% |
| B00S | 26,3966% | 1,6962% |
| B06 | 17,2105% | 0% |
| B06S | 26,1325% | 0% |

O denominador é o patrimônio final **v9 da própria carteira**, incluindo caixa, atribuído por `peso × (1 + retorno)`. Em B00S, 22,2222% do capital inicial corresponde às posições recalculadas/ancoradas; 10,4090% do patrimônio final está associado ao catálogo de caixa BBSE3 agora confrontado com RI. **Certificação documental integral: 0%.** Os 96 recortes de cobertura estão no CSV; o fato de o primeiro ano 2020 ter cálculo herdado por eventos não torna sua manutenção de seis anos integralmente verificada.

## Matriz dos 12 ativo/ano

| Ativo / formação | Caixa conhecido e confrontado na janela | Avanço / lacuna |
|---|---:|---|
| ITSA3 2022 | 11/11 | HTML original coletado; direitos e bonificações preservados |
| ITSA3 2023 | 11/11 | Mesmo avanço; direitos 2023 reutilizados da v11.2 |
| ITSA3 2024 | 10/10 | Mesmo avanço; direitos 2025 reutilizados da v11.2 |
| ITSA3 2025 | 9/9 | HTML original, incluindo bruto/líquido e bonificação |
| UNIP3 2022 | 5/5 | Transcrição anterior; download original ainda HTTP 403 |
| UNIP3 2023 | 3/3 | Mesma limitação; bonificação já corroborada na v11 |
| SBSP3 2025 | 2/2 | Dois avisos finais originais confirmam valores nominais pré-split |
| TGMA3 2025 | 5/5 | Três avisos originais; tabela dev de RI tem inconsistências |
| CSAN3 2022 | 1/1 | Aviso confirma 0,42857979, com 18/05/2023, ex 19/05, paga 31/05 |
| SYNE3 2022 | 0 eventos listados | HTML original; ausência na tabela não prova ausência de todos os eventos |
| ALOS3 2024 | 0/11 nesta rodada de documentos | Avisos completos e revisão janeiro/2025 pendentes |
| ALOS3 2025 | 2/13 | Duas parcelas novembro/2025 confirmadas em cópia de aviso do emissor |

Há **66 fatos de caixa confrontados**, incluindo fatos de manutenção UNIP3 posteriores às duas janelas acima; todos presentes no baseline. Nove pares avançaram em evidência original ou cópia identificada de aviso; os dois UNIP3 e ALOS3/2024 continuam sem esse avanço. **Zero dos 12 foi promovido a certificação integral.**

As ausências documentadas têm escopo limitado: a [RCA Tegma de novembro/2025](https://api.mziq.com/mzfilemanager/v2/d/280684e0-28e0-4165-99c5-8a10de86a40c/7541b117-5d33-59c7-4aab-6e748f64d486?origin=1) aumenta capital sem emitir ações, portanto não cria bonificação; o [release 2T26](https://ri.tegma.com.br/earnings-release-do-2t26/) informa ausência de JCP em abril/2026, sem provar ausência de outras distribuições. Os [avisos finais da Sabesp](https://api.mziq.com/mzfilemanager/v2/d/9e47ee51-f833-4a23-af98-2bac9e54e0b3/142bd0a4-e609-f77a-b3ed-19d0971f8757?origin=2), [JCP março/2026](https://api.mziq.com/mzfilemanager/v2/d/9e47ee51-f833-4a23-af98-2bac9e54e0b3/c8a6ae39-9a72-cdf9-6499-56018a5000ad?origin=2), o [aviso Cosan](https://api.mziq.com/mzfilemanager/v2/d/6aa68515-2422-4cc4-bafa-8870ccdfedb0/f210a29b-f6a2-d5d4-afbb-54282dbaff89?origin=1) e a [cópia do aviso ALLOS](https://investidor10.com.br/acoes/link_comunicado/ALOS3/26681/) estão identificados no manifesto.

O impacto de correção documental nova nesses 12 pares é zero: os valores confrontados já estão na baseline. Isso **não** significa risco zero. O cenário de remover apenas os eventos de caixa conhecidos ainda sem corroboração nesta matriz chega a 0,564822 pp em ALOS3/2024 e 0,873541 pp em ALOS3/2025. Não é estimativa provável de erro nem limite para eventos desconhecidos. Onde não há catálogo completo, o impacto máximo geral permanece **não limitado documentalmente**, em vez de receber um número inventado.

## Evidência, testes e reprodução

Foram registrados 33 acessos, com 30 originais/cópias de emissor coletados e armazenados comprimidos. O SHA-256 principal refere-se aos bytes descomprimidos recebidos; outro hash verifica o arquivo gzip. As três falhas de coleta permanecem registradas. Cópias hospedadas em terceiros são diferenciadas das fontes diretamente hospedadas pelo emissor. Os 45 registros B3 locais foram confrontados com o alerta e preservados como fatos estruturados, sem chamar sua transcrição de documento original.

Foram conferidas mais **48 cotações nominais** contra COTAHIST local, incluindo BBSE3 e preços de reinvestimento dos documentos novos: 48/48 coincidentes. Isso verifica a ingestão a partir de arquivos existentes; **não houve nova coleta independente da B3**. Os dados volumosos permanecem locais.

Validação executada:

- 50 testes atuais: 34 anteriores e 16 novos; 33 testes originais do motor, executados separadamente contra o motor preservado.
- Paridade v6 18/18; v10 anual 18/18; v11.1 manutenção 18/18; v11.2 manutenção/renovação 36/36.
- 45/45 alertas, 1.620 combinações de impacto, 36 cenários conjuntos; nenhuma alteração das seleções, do motor ou dos 71 artefatos da baseline v11.2.
- 1.212 posições Barsi; pesos e contribuições reproduzem os 96 agregados anuais/manutenção da v9; renovação encadeada nas mesmas datas.
- CI adicionada para testes sintéticos e integridade dos artefatos. A execução econômica completa usa os arquivos locais; o job GitHub não alega acesso ao SQLite/COTAHIST.

Os comandos abaixo devem ser executados na raiz, com ambiente contendo `pandas`, `pytest` e `beautifulsoup4`, SQLite nominal disponível e o pacote v9 já reproduzido pelo auditor existente. Escolha destino novo para preservar checkpoints:

```bash
python scripts/audit_alerts_v12.py --out /tmp/checkpoint-v12-reproduzido
python scripts/audit_barsi_comparability_v12.py --out /tmp/checkpoint-v12-reproduzido
python scripts/update_documentary_matrix_v12.py --out /tmp/checkpoint-v12-reproduzido
python scripts/verify_checkpoint_v12.py --out /tmp/checkpoint-v12-reproduzido --raw-dir data/raw
python -m pytest -q tests/test_graham_maintenance_v11.py tests/test_itsa_rights_v11_2.py tests/test_audit_v12.py
```

Os testes de artefatos verificam o checkpoint versionado. Os quatro comandos anteriores recalculam o destino informado. Os documentos comprimidos possibilitam rever a transcrição sem depender de uma tabela de RI que venha a mudar.

**CHECKPOINT — Barsi × Graham**

- Etapa concluída: 45/45 alertas classificados e quantificados; diagnóstico Barsi por posição/ano e alternativas dirigidas; matriz 12/12 atualizada. Baseline v11.2 provisória preservada.
- Arquivos alterados: quatro scripts de auditoria/validação, testes, CI, relatório, documentos com hashes e CSVs em `checkpoint_v12_2026_10_07`.
- Testes executados e resultado: 50 atuais + 33 herdados aprovados; paridades v6/v10/v11.1 18/18 cada e v11.2 36/36; 48 cotações adicionais coincidentes.
- Resultados numéricos novos: nove parcelas adicionais confirmadas e três substituições documentadas em cenário separado; maior efeito conjunto +0,963643 pp em R00/2022; rankings centrais preservados. BBSE3 acrescenta +0,879511 pp a B00S/2020; distância de R16 ao limite parcialmente revisto cai a 0,126601 pp. Cobertura por cálculo de eventos no patrimônio Barsi 2020: B00 16,0830%, B00S 26,3966%, B06 17,2105%, B06S 26,1325%; nenhuma certificação integral.
- Pendências identificadas: quatro diferenças nominais dos 45; documentos individuais dos alertas sem exposição; comparabilidade Barsi ainda parcial; todos os 12 pares sem fechamento integral, com avanço em nove. UNIP3/originais e ALOS3/avisos completos permanecem prioridades documentais.
- Decisões metodológicas necessárias: nenhuma nova política aplicada à baseline; cenários são auditáveis e separados. Não inferir superioridade robusta nem intervalo de confiança dos envelopes v9.
- Commit/branch/PR: branch `audit/graham-v6-coverage-7`, PR #1 em rascunho; commits desta entrega constam no histórico do PR.
- Próxima etapa recomendada: auditar PSSA3, TIMP3→TIMS3, VIVT4→VIVT3 e SAPR4 por materialidade; completar os avisos ALLOS e catálogos estruturais dos 12 pares, preservando as versões atuais.
