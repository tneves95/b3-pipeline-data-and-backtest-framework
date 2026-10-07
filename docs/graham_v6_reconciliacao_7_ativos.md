# Graham corrigido × BESST v9 — trilha de conciliação

Corte: 30/06/2026. Atualizado em 07/10/2026. **Esta trilha não promove nenhum ativo a `RECONCILED`.**

## Escopo das 12 combinações ativo/ano

| Ano formação | Ativo | Fonte documental principal | Ponto que permanece a conferir |
| --- | --- | --- | --- |
| 2022 | ITSA3 | [Itaúsa RI — remuneração e bonificações](https://ri.itausa.com.br/informacoes-financeiras/remuneracao-aos-acionistas/) | Completar confronto por data-com/valor e preço nominal B3 |
| 2023 | ITSA3 | [Itaúsa RI](https://ri.itausa.com.br/informacoes-financeiras/remuneracao-aos-acionistas/) | Bonificação 2023 e sequência nominal |
| 2024 | ITSA3 | [Itaúsa RI](https://ri.itausa.com.br/informacoes-financeiras/remuneracao-aos-acionistas/) | Bonificação 2024 e sequência nominal |
| 2025 | ITSA3 | [Itaúsa RI](https://ri.itausa.com.br/informacoes-financeiras/remuneracao-aos-acionistas/) | Bonificação 2025 e sequência nominal |
| 2022 | UNIP3 | [Unipar RI — proventos e bonificações](https://ri.unipar.com/informacoes-aos-investidores/proventos-e-bonificacoes/) | Separar pagamentos da mesma data-com sem eliminar tranches |
| 2023 | UNIP3 | [Unipar RI](https://ri.unipar.com/informacoes-aos-investidores/proventos-e-bonificacoes/) | Bonificação de 10% em abril/2024 |
| 2022 | CSAN3 | [Cosan RI — histórico de dividendos](https://www.cosan.com.br/relacoes-com-investidores/outras-informacoes-para-investidores/dividendos/) | R$ 0,42858 bruto em maio/2023 e preços |
| 2022 | SYNE3 | [SYN RI — política/histórico](https://ri.syn.com.br/governanca-corporativa/politica-de-dividendos-e-historico/) | Confirmar ausência de *qualquer* evento de caixa ou estrutura em 30/06/22–30/06/23 (não apenas dividendos) |
| 2024 | ALOS3 | [ALLOS RI — avisos e comunicados](https://ri.allos.com.br/servicos-aos-investidores/comunicados-e-fatos-relevantes/) | Duas tranches de dividendos em jan/2025; demais valores |
| 2025 | ALOS3 | [ALLOS RI](https://ri.allos.com.br/servicos-aos-investidores/comunicados-e-fatos-relevantes/) | Duas tranches de dividendos em nov/2025; demais valores |
| 2025 | TGMA3 | [Tegma RI — aviso de novembro](https://ri.tegma.com.br/noticias/aviso-aos-acionistas-pagamento-de-dividendos-e-juros-sobre-capital-proprio-2/) | Conferir fechamento nominal independentemente do SQLite |
| 2025 | SBSP3 | [Sabesp RI / SEC — bonificação dez/2025](https://www.sec.gov/Archives/edgar/data/1170858/000129281425004333/sbs20251219_6k.htm), [B3 mar/2026](https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/Detail?agencia=18&dataNoticia=2026-03-20+18%3A04%3A41&idNoticia=3287363), [SEC — desdobramento](https://www.sec.gov/Archives/edgar/data/1170858/000129281426002627/sbs20260428_6k.htm) | Verificar sequência 2 bonificações + split 1:5 + 2 JCP nas respectivas datas-com |

## Fatos corroborados e ressalvas

- UNIP3: o RI lista **duas parcelas distintas** com data-com 20/04/2023, e duas em 19/03/2024. Eventos de mesma classe e data não devem ser agregados antes de conferir separadamente os valores.
- ALOS3: os dois dividendos em 23/01/2025 e os dois em 18/11/2025 devem permanecer como tranches distintas.
- CSAN3: valor de 2023 da base B3 (R$ 0,428579...) é consistente com R$ 0,43 arredondado pelo RI da Cosan; evitar substituição por valor arredondado.
- SYNE3: ausência de proventos na janela não se confunde com ausência de outros eventos societários (redução de capital, incorporação etc.).
- TGMA3: alguns números da página-resumo de dividendos do RI não coincidem com o **aviso específico**. O comunicado de novembro confirma R$ 0,79 em dividendos e R$ 0,18 em JCP com data-com **06/11/2025**; os valores da base coincidem. O documento societário de agosto/2025 confirma R$ 1,21 + R$ 0,14, data-com 07/08/2025. Dar preferência às deliberações e avisos específicos.
- SBSP3: [SEC de dezembro/2025](https://www.sec.gov/Archives/edgar/data/1170858/000129281426000919/sbsfs4q25_6k.htm) confirma JCP de R$ 2,643892990/ação e [aviso de março/2026](https://investidor10.com.br/acoes/link_comunicado/SBSP3/37526/) confirma R$ 0,83342453884/ação. Bonificações (dez/2025 2,9646975%; mar/2026 0,160980322%) e desdobramento 1:5 com data-com 28/04/2026 devem seguir critérios da quantidade em circulação. Não tratar data de pagamento como data-ex.

## Interpretação do teste já executado

- Paridade legada **18/18**; cinco registros TGMA3 coincidem com o manifesto de evidências codificado no script; 24 cotações-limite existem; oito eventos estruturais não produziram alertas mecânicos acima da tolerância configurada.
- A verificação de preço usa a mesma base SQLite do retorno; por isso **não é validação independente da origem B3**.
- A ausência de alerta de descontinuidade de preço de 20% não comprova, sozinha, que todo evento ou provento foi capturado.
- Retornos Graham v6 corrigidos e seleções atualizadas são **provisórios**; as faixas BESST v9 correspondem a sensibilidade determinística e precisão material, não a preços/apuração documental exatos.
- O estudo é teórico, bruto, com reinvestimento na data-ex e quantidades fracionárias. Não equiparar a resultado líquido de uma pessoa física, especialmente porque JCP e suas regras de tributação variam no período.

## Próximo aceite de cobertura

Cada uma das 12 combinações exige: (1) cotações nominais nas duas pontas e nas datas-ex, conferidas contra a fonte original; (2) proventos completos com data-com, tipo, valor e todas as tranches; (3) eventos de quantidade completos com fator na convenção correta; (4) fonte/evidência e exceções registradas; (5) ausência de duplicidade com v6; (6) eventual marcação `RECONCILED` apenas depois de cumprir os itens anteriores.

Consolidação atualizada para **renovação anual**: `python scripts/compare_graham_corrected_barsi_v9.py`. A manutenção de posições Graham da v9 NÃO foi recalculada com a seleção corrigida e não deve ser confundida com os novos retornos de renovação.
