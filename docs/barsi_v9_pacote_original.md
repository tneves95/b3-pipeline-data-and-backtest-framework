# Pacote-fonte Barsi × Graham v9 (06/10/2026)

**Estado:** localizado no acervo de arquivos da conversa do ChatGPT; **NÃO** existe uma cópia do ZIP completo no repositório GitHub nem no Codespaces até o usuário carregá-lo.

## Arquivo completo (para reprodução)

- Nome: `Pacote_Barsi_Graham_Comparacao_Final_v9_2026-10-06.zip`
- Tamanho: 77.377.186 bytes (~73,8 MiB)
- SHA-256: `52911a31c01f5466e0d161d1d21ea8bbab1aa5aad3454bd0b943c1122df307a9`
- Local original de extração do ChatGPT: `/mnt/data/files/Pacote_Barsi_Graham_Comparacao_Final_v9_2026-10-06.zip`
- O caminho acima **não é caminho do Codespaces**. Baixar o ZIP no ChatGPT e fazer upload ao Codespaces.
- Destino sugerido no Codespaces (ignorado pelo `.gitignore` em vigor): `data/barsi_v9/Pacote_Barsi_Graham_Comparacao_Final_v9_2026-10-06.zip`

## Arquivo leve (para inspeção rápida, sem motor herdado)

- Nome: `Barsi_Graham_v9_Auditoria_Leve_2026-10-07.zip`
- Tamanho: 124.873 bytes
- SHA-256: `ac6eb7a469e1480710c0d469d05de83ee6d04ca66f4c682e3f8cf7bcf59b3253`
- Contém os 43 arquivos da v9 **exceto o ZIP herdado v8**. Permite verificar posições, pesos, contribuições e código dos cálculos v9; **não reproduz sozinho os cálculos**, pois falta o histórico herdado.

## Estrutura relevante interna do ZIP completo

Após extrair, diretório-raiz: `Barsi_Graham_Comparacao_Final_v9/`.

| Caminho interno | Utilidade |
| --- | --- |
| `dados/selection_rows.json` | Triagem e escolhas do BESST por ano |
| `resultados/final_selection_by_year.csv` | Carteiras selecionadas por ano e cenário (48 linhas) |
| `resultados/besst_individual_annual.csv` | 606 linhas: ano, ticker, carteira, cenário, peso, retorno anual, limites de sensibilidade |
| `resultados/besst_maintenance_holdings.csv` | 606 linhas: ano de formação, ticker, peso, retorno até 2026, caixa, posição final |
| `resultados/besst_annual.csv` | 48 carteiras anuais |
| `resultados/besst_renewal.csv` | Renovação e acumulados |
| `scripts/build_selection.py` | Seleção BESST (inclusões/exclusões, normalização DPS e teto de 6%) |
| `scripts/compute_besst.py` | Retorno por ativo e composição das carteiras |
| `scripts/compute_maintenance.py` | Manutenção por coorte |
| `scripts/consolidate_v9.py` | Relatórios finais e consolidação |
| `scripts/reproduzir_v9.py` | Reproduz resultados e compara SHA-256 |
| `herdado_v8/Pacote_Barsi_Graham_Retomada_v8_2026-10-05.zip` | ZIP v8 aninhado; contém dados e herança v7/v6/v5, incluindo motor de eventos anterior |

**Atenção:** para apurar contribuição individual, multiplicar `weight * return`; preservar a unidade de retorno decimal (por exemplo, `0.20` representa 20%). A integridade interna da v9 segue critérios próprios da versão, que **não são automaticamente equivalentes ao novo Graham corrigido**.

## Instruções para Codex após upload

Na raiz do repositório:

```bash
mkdir -p data/barsi_v9/unpacked
sha256sum data/barsi_v9/Pacote_Barsi_Graham_Comparacao_Final_v9_2026-10-06.zip
# Conferir com hash acima antes de continuar.
unzip -q data/barsi_v9/Pacote_Barsi_Graham_Comparacao_Final_v9_2026-10-06.zip -d data/barsi_v9/unpacked
python data/barsi_v9/unpacked/Barsi_Graham_Comparacao_Final_v9/scripts/reproduzir_v9.py
```

A reprodução pode requerer dependências Python do ambiente. Se falhar, registrar exceção; não substituir a versão v9 por uma aproximação.

**Metodologia:** o `LEIA_ME.md` do pacote informa retorno bruto, proventos pelo direito, sem impostos/custos; BESST 2020–2021 é event-level exato e 2021–2026 opera em precisão material, com alguns checkpoints exatos herdados e cenários central/conservador. As faixas NÃO são intervalos de confiança estatísticos. Não classificar os resultados v9 como plenamente certificados por ter reproduzido os hashes.
