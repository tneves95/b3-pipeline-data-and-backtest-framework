# PR #5 — lote 1: seleção, calendário e preços antes dos retornos

Partida: `7588d52dfd6564f6fb2b86737af1eaa8660a043f`. Baseline protegido: PR #4 `8671156586c2d12c3c8c121510db33144199338c`, incluindo a auditoria independente. Nenhuma seleção, documento, resultado ou motor anterior foi modificado. O protocolo foi lido integralmente. Ainda não se calculou a rentabilidade monetária do estudo.

O calendário contém 144 primeiros pregões, julho/2014–junho/2026, identificados na série diária oficial B3/IBOV já congelada. São R$ 360.000 em depósitos, além dos R$ 100.000 iniciais; a formação é 30/06/2014 e o encerramento 30/06/2026. Junho recebe seu aporte no início do mês e sua revisão no último pregão; não existe revisão em junho/2026.

## Ranking independente do filtro B00S

O universo inclui 78 emissores BESST observados no COTAHIST de janeiro–junho/2014, com CNPJ, classificação e capital conhecidos no corte. Registra também emissores sem negócio no dia da formação, units, empresas fora da taxonomia estrita e códigos cuja identidade não pôde ser resolvida. Não se exige aprovação B00S. A classe comprável usa mediana do volume monetário das últimas 126 sessões, sessões, volume total e ticker; os desempates de capitalização usam CNPJ.

| Setor | Primeiro emissor / classe | Capitalização emitida | Segundo emissor / classe | Capitalização emitida |
|---|---|---:|---|---:|
| Bancos | Itaú / ITUB4 | R$ 172,195 bi | Bradesco / BBDC4 | R$ 135,243 bi |
| Energia | Tractebel / TBLE3 | R$ 21,540 bi | Cemig / CMIG4 | R$ 20,183 bi |
| Saneamento | Sabesp / SBSP3 | R$ 16,097 bi | Copasa / CSMG3 | R$ 4,847 bi |
| Seguros | BB Seguridade / BBSE3 | R$ 64,880 bi | Porto Seguro / PSSA3 | R$ 10,300 bi |
| Telecom | Telefônica / VIVT4 | R$ 48,530 bi | TIM / TIMP3 | R$ 31,236 bi |

Os dez líderes têm preços ON/PN observados no fechamento. As quantidades emitidas e seus documentos são publicados por emissor; a dedução máxima de tesouraria fica separada da medida principal. Classes sem cotação não recebem um falso preço observado. A composição provisória tem 10% por origem.

**Ressalva material do ranking:** NET não tem cotação ON em 30/06/2014. Paridade com PN resulta em R$ 23,922 bi; o último negócio ON, em 22/04/2014, resulta em outro cenário, e não numa cotação atual. Dobrar a cotação atribuída à ON pela paridade com PN eleva o cenário a R$ 31,906 bi, acima da TIM. Isso não é um limite matemático. A lista principal fica **condicional a esse cenário documental**, e a lista alternativa substitui TIM por NET. Não se afirma ter demonstrado um ranking exato de classes sem preço.

SulAmérica, Taesa e Alupar possuem documentos históricos primários arquivados demonstrando units com uma ON e duas PN. Sob preços de classes não negativos e a composição da unit, o máximo de capitalização compatível com o preço observado é `unit_price * max(ON, PN/2)`. O limite de SulAmérica fica abaixo de Porto; dobrar simultaneamente os preços imputados às duas classes violaria a cotação da própria unit. Renova e Contax são inventariadas separadamente: a constituição histórica das units ainda precisa de prova primária específica, apesar da baixa capitalização do cenário. O pacote não confunde unit de dois CNPJs do BTG com um único banco. Ausência de negociação no dia da formação impede compra naquele fechamento; não exclui o emissor silenciosamente do inventário.

## Cotações e lacunas

Foram extraídos os registros exatos dos 13 ZIPs COTAHIST B3 2014–2026. Cada registro mantém fator de cotação, ISIN, número da linha, hash dos bytes originais e SHA-256 do ZIP. Os preços em comum conferem com os motores aceitos. A cobertura contém 17.540 verificações de posições na formação, primeiros/últimos pregões mensais e fechamentos de junho.

Há **seis observações sem fechamento exato**, e nenhuma foi preenchida:

- V0: ABCB2 em 01/07/2014 e 02/01/2015, entre criação do direito e primeiro negócio.
- V0 e VVAL: ENBR3 em 31/08/2023 e 01/09/2023, entre fim da negociação e resgate compulsório.

O documento EDP congelado é de 05/09/2023; ele prova R$ 24,23 pagos em 13/09/2023, mas não prova que o valor final estivesse disponível em 01/09. Foi localizado também o comunicado primário de 30/08, que define R$ 23,73 corrigidos pela SELIC. Eventual marcação do recebível exigirá esse documento e a correção histórica disponíveis no corte, sem antecipar o preço final de setembro. Proventos e eventos continuam na cronologia aceita, sem duplicação.

Os testes sintéticos verificam compra proporcional nos déficits sem venda mensal, entrada de terceiro nome, junho sem mudança, vencedoras com N=20 (1,8× e acima de 2×), transição 16→15 e TIR com datas reais. Os testes documentais verificam calendário, total de aportes, origem BH, ausência de alvo XP, universo completo e hashes do ranking. Validação deste checkpoint: **14 testes passaram**. CSVs e `ranking_freeze.json` são a referência primária para o próximo lote.

PR #5 permanece draft; nenhuma operação de merge foi autorizada ou executada.
