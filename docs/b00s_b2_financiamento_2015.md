# Financiamento B2 nas renovações VVAL/VQ a partir de junho/2015

Congelado antes das decisões e retornos novos, conforme [revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/4#issuecomment-6071009589). V0, V10 e a formação de2014 mantêm suas regras e resultados aceitos.

Cada entrada solicita `NAV × 20% / N_setor`. N é a união de linhagens econômicas únicas já mantidas (não FAIL) e candidatas qualificadas no setor. Classes, direitos e sucessoras herdadas contam uma vez para dimensionamento, preservando seus valores físicos no NAV. Não há renormalização das parcelas entre aprovadas nem redistribuição da referência dos setores vazios. A regra de FAIL-base herdada permanece: ausência de status não autoriza venda; o dimensionamento não cria reprovação por linhagem.

Os recursos de saídas FAIL financiam primeiro. Se excederem o pedido, o excedente se distribui às novas entradas proporcionalmente aos pedidos. Se faltarem, vende-se a mesma fração de cada posição sobrevivente para cobrir apenas a diferença. Logo,20% é referência de pedido, não teto final após saídas compulsórias. Sem entrada, só saídas FAIL permitem redistribuição; sem FAIL, nada é reequalizado. Se todas as posições falharem sem destino elegível, há bloqueio explícito, não caixa fictício.

Uma nova empresa num setor com uma incumbente pede10%, ainda que seja a única aprovada. Num setor antes vazio pede20%. Mesmo que os demais setores recebam novas empresas, a presença de uma sobrevivente deixa parte da referência do seu setor reservada; a soma dos pedidos permanece menor que100%. Assim, o financiamento conserva NAV e as sobreviventes continuam positivas. Não há aporte, imposto, custo novo ou uso de rentabilidade futura.

A implementação isolada está em `scripts/b00s_funding.py`; `inputs/funding_policy_2015.json` fixa seu hash e parâmetros. Os testes incluem única entrada, setor antes vazio, várias entradas, status indeterminado, direitos e sucessoras, deduplicação, saídas insuficientes/excedentes, ausência de entrada e ausência de destino. A revisão independente está em `docs/reviews/adversarial_2015.json`.
