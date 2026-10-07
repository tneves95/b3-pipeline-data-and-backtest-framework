# ITSA3 — monetização documentada dos direitos, v11.2

Execução de 07/10/2026, até 30/06/2026. Política solicitada pelo usuário: vender os direitos na primeira sessão efetivamente negociável, reinvestir após liquidação, sem custos ou impostos, preservando o cenário sem monetização.

**Os dois eventos têm evidência suficiente para esta simulação.** A certificação integral do histórico das sete estratégias continua pendente.

## Documentos, instrumentos e execução

| Campo | 2023 | 2025 |
|---|---|---|
| Ação de origem / classe | ITSA3 / ordinária | ITSA3 / ordinária |
| Data-com | 17/08/2023 | 17/02/2025 |
| Data-ex | 18/08/2023 | 18/02/2025 |
| Direitos por ação | 0,01390757436 | 0,013766678 |
| Início documentado do período | 24/08/2023 | 10/03/2025 |
| Prazo final no emissor para exercício | 22/09/2023 | 11/04/2025 |
| Código / mercado fracionário | ITSA1 / ITSA1F | ITSA1 / ITSA1F |
| ISIN do direito | BRITSAD21OR3 | BRITSAD22OR1 |
| Primeira negociação comprovada | 24/08/2023 | 10/03/2025 |
| Fechamento ITSA1F utilizado | R$ 3,30 | R$ 2,55 |
| Negócios / quantidade negociada ITSA1F no dia | 381 / 4.181 | 272 / 2.829 |
| Liquidação D+2 | 28/08/2023 | 12/03/2025 |
| Reinvestimento em ITSA3, fechamento | 28/08/2023, R$ 9,59 | 12/03/2025, R$ 9,25 |

As proporções, datas, espécie e descarte de frações constam dos avisos de [2023, páginas 6 e 8](https://api.mziq.com/mzfilemanager/v2/d/afd9200b-9b01-4d1c-bdd9-9b2c1e9b3b4d/fac6b435-abe5-4eeb-8f00-eaea34902bd1?origin=1) e [2025, páginas 7 e 8](https://api.mziq.com/mzfilemanager/v2/d/afd9200b-9b01-4d1c-bdd9-9b2c1e9b3b4d/8df7a32b-5a88-1114-6f2f-89c9b9013c73?origin=1). Os PDFs foram baixados do RI e seus hashes registrados em [itsa_rights_verified_2026_10_07.json](../research/graham_v6_comparison/itsa_rights_verified_2026_10_07.json). Os preços de subscrição de R$ 6,50/R$ 6,70 não são preços de venda dos direitos.

A identificação ON e os códigos são corroborados pelo COTAHIST, que informa `DIR ORD N1`, ISIN, mercado, negócios, quantidade e volume. A [B3 especifica o sufixo 1 para direitos ordinários, a negociação fracionária e a liquidação em D+2](https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/direitos-de-subscricao.htm). A [página da chamada de capital de 2025](https://ri.itausa.com.br/servicos-aos-investidores/chamada-de-capital/) também identifica ITSA1.

Foram varridos integralmente os COTAHIST de 2023 e 2025 e ordenados por data: a ordem física do arquivo de 2025 não é cronológica. A seleção exige data dentro da janela documental, classe/ISIN corretos, preço positivo, negócios, quantidade e volume positivos. As linhas e arquivos têm hashes no CSV de evidências. No mercado padrão, ITSA1 fechou a R$ 2,88 em 2023; esse preço não foi usado para os pequenos lotes desta simulação. Todas as vendas calculadas contêm de zero a quatro direitos inteiros.

A compra ocorre no fechamento de D+2, após a liquidação normal. A hipótese operacional é crédito pelo participante antes desse fechamento; a [grade publicada da B3 encerra os créditos da câmara às 15h50](https://www.b3.com.br/lumis/portal/file/fileDownload.jsp?fileId=8AE490CA6F165E34016F19E813424E03). Não se antecipa o recebível, não se usa margem e não se presume rendimento do caixa. Trata-se de simulação de execução ao fechamento, não de comprovante de crédito de uma conta real.

## Quantidade e uso do motor

Para cada carteira de R$ 10.000 iniciais, captura-se a quantidade efetiva de ITSA3 no fechamento da data-com. Os direitos são `floor(quantidade × proporção)`, como determina o aviso. Compras por proventos posteriores à data-com não aumentam essa quantidade. O líquido é igual ao bruto na convenção de custos e impostos zerados.

As quantidades de ITSA3 continuam fracionárias, conforme o índice teórico herdado; somente a atribuição dos direitos é truncada. Portanto, esta revisão não representa uma carteira inteiramente executável em lotes reais. O valor do impacto depende do capital inicial. Cada posição é calculada com o capital efetivamente alocado, e a renovação transporta o patrimônio efetivo entre anos; multiplicar retornos anuais normalizados para R$ 10.000 daria um resultado diferente.

O motor v6 permanece inalterado. Um adaptador registra o produto documentado da venda como fluxo de caixa de reinvestimento, com quantidade elegível congelada na data-com. O livro auxiliar separa venda, liquidação, recebimento e compra; não classifica o recebimento como dividendo. Não há marcação dos direitos ou recebíveis no NAV intermediário entre a data-ex e o reinvestimento. Por isso, esse NAV não é apropriado para medir risco diário. Todos os pontos anuais publicados são posteriores à liquidação e conciliam integralmente.

## Impactos até junho de 2026

Formação em junho de 2020:

| Regra | Manutenção sem direitos | Com direitos | Impacto | Renovação com direitos | Impacto na renovação |
|---|---:|---:|---:|---:|---:|
| R00 | +149,0467% | +149,3140% | +0,2673 pp | +204,1233% | +0,1436 pp |
| R03 | +136,2394% | +136,3945% | +0,1551 pp | +265,1978% | +0,2111 pp |
| R16 | +126,6287% | +126,8531% | +0,2243 pp | +248,1894% | +0,4000 pp |

Os efeitos são positivos e pequenos nesta apuração. Não mudam a ordenação central das sete estratégias em 2020. As formações de 2021 e 2025 não têm impacto na manutenção, por ausência de posição elegível nos eventos. Isso não elimina as outras pendências documentais.

Em [direitos_itsa_v11_2](../research/graham_v6_comparison/execution_v11_2_2026_10_07/direitos_itsa_v11_2/):

- `operacoes_direitos.csv`: 40 registros de exposição por mecanismo/coorte, incluindo direitos vendidos, líquido, data de liquidação, preço e ações compradas.
- `graham_posicoes.csv`: 162 posições com retorno anterior, novo, contribuição e impacto individual e na carteira.
- `impacto_por_evento_manutencao.csv`: atribuição sequencial por evento; 2023 contra ausência de monetização e 2025 sobre o cenário com 2023. As parcelas somam o impacto total.
- `impacto_direitos_36_resultados.csv`: manutenção e renovação das 18 carteiras contra a versão anterior.
- `anuais_capital_10000.csv`: janelas individuais; para renovação acumulada usar `trajetoria_renovacao_capital_efetivo.csv`.
- `comparacao_72_cenarios.csv`: comparação atualizada. Barsi/BOVA11 preservados.

A sensibilidade anterior está integralmente preservada em `manutencao_documental_v11_1` e `comparacao_documental_v11_1`, no mesmo snapshot. A revisão das restituições SYNE3 e parcelas UNIP3 permanece aplicada em ambos os cenários.

## Validação e reprodução

Foram aprovados 17 testes específicos dos direitos e 17 testes anteriores, além dos 33 testes originais do motor já executados. Os testes incluem ausência de negociação, ISIN/classe incorretos, preço divergente, duplicidade, bloqueio antes da liquidação, atribuição por data-com, descarte de frações e efeito do capital alocado.

18/18 manutenções sem direitos reproduzem v11.1; 18/18 primeiros anos sem direitos reproduzem v10; 18/18 primeiros anos com direitos reproduzem os anuais recalculados. Quantidades, caixa, pesos e contribuições das 18 carteiras conciliam. Duas execuções independentes produziram arquivos comuns idênticos. Nenhuma cobertura geral foi promovida a certificada.

Após os comandos do [relatório de execução](graham_v11_execucao_2026_10_07.md):

```bash
python -m pytest -q tests/test_itsa_rights_v11_2.py tests/test_graham_maintenance_v11.py
python scripts/simulate_itsa_rights_v11_2.py --raw-dir data/raw
python scripts/validate_graham_v11_outputs.py --graham-dir graham_v6_event_results/direitos_itsa_v11_2 --comparison-dir graham_v6_event_results/direitos_itsa_v11_2
```

O simulador exige destino novo. Evidência ausente ou ambígua fica registrada em `pendencias_direitos.csv`; não é substituída por estimativa. Nesta execução, os dois eventos passaram e esse arquivo não contém pendências.
