# Ponte de eventos Graham — motor original v6

O arquivo `motor_eventos.py` é a cópia **sem alteração** do motor encontrado na
árvore herdada do pacote `Pacote_Barsi_Graham_Retomada_v6_2026-10-05.zip`.
A base `legacy_v6_inputs.json.gz` é um extrato de `apurar_v6.inputs()` do pacote:
96.561 cotações de 77 ativos, calendário de 1.617 sessões, 221 eventos originais
e 25 registros de cobertura. `legacy_v6_selections.csv` são as seleções originais.

## Execução

Na raiz do Codespaces do repositório, com a `.venv` ativada:

```bash
unzip -q Ponte_Eventos_Graham_v6_2026-10-07.zip
python graham_v6_event_bridge/graham_event_resume.py --legacy-only
python graham_v6_event_bridge/graham_event_resume.py
```

O primeiro comando Python confirma **18/18** retornos legados por reprodução
independente; o segundo reutiliza as seleções existentes de
`graham_recalc_returns_2020_2026.py` e os arquivos
`graham_final_2022.csv` a `graham_final_2025.csv`, além de `b3_market_data.sqlite`
e `graham_v6_extra_cash.csv`/`graham_v6_extra_stock.csv` da execução atual.

Escreve apenas novos arquivos na pasta `graham_v6_event_results/`.
Não altera banco SQLite, checkpoints antigos nem scripts anteriores.

A função de complemento entende os campos `event_date` e `stock_actions.ex_date`
extraídos da B3 como **datas-com** nos registros identificados (o nome de uma
coluna não substitui a verificação do fato). Converte à próxima sessão, e
percentuais de BONIFICAÇÃO ao multiplicador de ações. Acrescenta eventos
societários conhecidos que não vieram no CSV, sobretudo bonificações Itaúsa
2021–2024 e desdobramento Sabesp 1:5 de 29/04/2026.

**Limitação:** o cálculo novo é provisório até reconciliação de preços nominais,
possíveis proventos omitidos/duplicados, classes de ações e cobertura documental.
Os retornos não são apresentados como finais por esse script. Ele não calcula
impostos nem custos (mesma convenção de índice teórico bruto v6).

## Fontes de correção societária

- Itaúsa: https://statusinvest.com.br/acoes/itsa3
- Sabesp: https://www.infomoney.com.br/mercados/sabesp-sbsp3-aprova-desdobramento-de-acoes-na-proporcao-de-1-para-5/
- Base histórica e eventos: pacote Retomada v6, com identificação de origem.

As cópias `apurar_v6_original_reference.py` e
`reproduzir_v6_original_reference.py` são **referências de leitura**; estes
scripts antigos dependem da árvore herdada inteira, que não está incluída.
O arquivo executável independente do pacote é `graham_event_resume.py`.
