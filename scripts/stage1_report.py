"""Render the incremental, qualified percentage checkpoint from frozen outputs."""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SEL=ROOT/'research/returns_2014_2026_selection'
def read(name):
    return list(csv.DictReader((SEL/name).open(encoding='utf8')))


def render(annual,accumulated,stats,segments,names,pct,table):
    scenarios=read('r03_selection_scenarios.csv')
    lo=min(float(r['final_pct']) for r in scenarios);hi=max(float(r['final_pct']) for r in scenarios)
    sens=read('continuation_sensitivities.csv');pending=read('continuation_unresolved_selections.csv')
    ranks=list(csv.DictReader((ROOT/'research/returns_2014_2026_results/annual_ranks.csv').open()))
    result=[
      '# Checkpoint — Barsi × Graham, etapa percentual 2014–2026 — 08/10/2026','',
      '**Quatro trajetórias contínuas calculadas: 48 retornos anuais, 48 acumulados e IBOV nas três tabelas. São reconstruções qualificadas, não uma certificação integral das seleções PIT e de todos os direitos.** '
      'Continuação de `5cf7eb4`, na branch `study/returns-2014-2026-stage1`, conforme a '
      '[revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/3#issuecomment-6063812812). '
      'PR #3 permanece draft, sem merge. BH padrão, IBOV, R03 até junho/2016 e B00S até junho/2015 são entradas imutáveis, verificadas por SHA-256.','',
      'Os números centrais usam a regra explícita: nova entrada somente com PASS demonstrado; INDETERMINATE não entra e não autoriza vender posição herdada. '
      'As sensibilidades abaixo mostram que pendências de seleção ainda podem alterar o ranking. Não atribuir ao ranking central uma vitória definitiva de filosofia. '
      'Nenhuma simulação de dinheiro investido, caixa, IR, aportes ou execução operacional foi realizada.','',
      '**Tabela 1 — rentabilidade anual junho→junho (%)**','',
      table(['Período','Início','Fim',*names],[[r['period'],r['start'],r['end'],*[pct(r[n]) for n in names]] for r in annual]),'',
      '[CSV anual](../research/returns_2014_2026_results/annual_returns_pct.csv) · '
      '[excesso anual sobre IBOV, em p.p.](../research/returns_2014_2026_results/annual_excess_pp.csv).','',
      '**Tabela 2 — rentabilidade acumulada desde junho/2014 (%)**','',
      table(['Até',*names],[[r['end'],*[pct(r[n]) for n in names]] for r in accumulated]),'',
      'Encadeamento `100 × (produto(1 + retorno anual decimal) − 1)`. O índice nunca reinicia em 2020. '
      '[CSV acumulado](../research/returns_2014_2026_results/cumulative_returns_pct.csv).','',
      '**Tabela 3 — consolidado até junho/2026, caso central qualificado**','',
      table(['Série','Janelas','Acumulado %','Excesso IBOV p.p.','CAGR %','Acima IBOV','Anos + / −','Pior período','Pior %','Rank final','Rank médio'],[
        [r['portfolio'],f"{r['observed_intervals']}/12",pct(r['total_return_pct']),pct(r['total_return_pct']-stats[-1]['total_return_pct']),
         pct(r['cagr_pct']),'—' if r['portfolio']=='IBOV' else f"{r['above_ibov_years']}/12",
         f"{r['positive_years']} / {r['negative_years']}",r['worst_period'],pct(r['worst_return_pct']),r['final_rank'],pct(r['mean_rank'])] for r in stats]),'',
      'CAGR usa dias efetivos/365,25. Rank anual/final: maior retorno ocupa 1º lugar entre as cinco séries; empates recebem o mesmo posto. '
      'Rank médio é a média dos 12 postos. `consistency_rank` no CSV ordena somente as quatro carteiras pela quantidade de anos estritamente acima do IBOV, '
      'com empates. Essa frequência é diferente do retorno final. '
      '[Consolidado completo, incluindo média, mediana e melhor ano](../research/returns_2014_2026_results/consolidated_pct.csv).','',
      '**Ranking anual do mesmo caso**','',
      table(['Período',*names],[[r['period'],*[r[n] for n in names]] for r in ranks]),'',
      '**Continuidade e composição efetiva**','',
      'R03 parte das posições de junho/2016 do checkpoint aceito, que já carregam a perda de 2014–2015 e a renovação seletiva de 2015. '
      'B00S parte das unidades de junho/2015 aceitas. B2 preserva os pesos relativos dos sobreviventes; somente FAIL vende integralmente. '
      'As saídas financiam as novas entradas; apenas a insuficiência provoca redução proporcional dos sobreviventes. '
      'Excedente das saídas vai aos entrantes na proporção dos alvos; sem entrantes, distribui-se entre os sobreviventes. '
      'Não há reconstrução anual com pesos iguais. Os alvos iguais do R03 e por grupo/nome do B00S dimensionam apenas as entradas.','',
      'B00S BH+entradas significa retenção das empresas e sucessoras, com redistribuição interna para novos PASS. '
      'Não é BH passivo sem transações: as reduções proporcionais financiam entradas sem aporte. '
      'Troca de ticker ou novo CNPJ de uma holding não equivale a reprovação fundamental. TIMS/AESB herdadas ficam retidas quando a classificação é indeterminada; '
      'TRPL4→ISAE4 não sai por liquidez artificialmente truncada do ticker antigo em 2025. '
      'Os alvos 2020–2025 vêm dos screeners congelados; decisões adicionais e ressalvas estão nos livros, sem usar os retornos do legado como novos trechos.','',
      'A entrada demonstrada de IRBR3 em junho/2019 usa lucro e dividendos de 2014 do FRE 73863, recebido em 07/05/2018, junto aos anos seguintes do screener PIT. '
      'O B00S carrega sua queda posterior. LINX3 entra no R03 em 2016 após recuperar 2009 no FRE 25942. '
      'CSAN falha por distribuição zero em 2009; CAML falha por distribuição zero em 2016, provada no original FRE 72320 recebido em março/2018. '
      'BBSE não tem cinco exercícios completos no corte de 2017: 2012 é o período de constituição. '
      '[Resoluções e fontes](../research/returns_2014_2026_selection/continuation_selection_resolutions.json).','',
    ]
    for name,stem in [('R03 B2','r03_continuation'),('B00S B2','b00s_b2_continuation'),('B00S BH+entradas','b00s_bh_continuation')]:
        positions=read(stem+'_positions.csv');rs=[r for r in positions if r['date']=='2026-06-30' and r['phase']=='PERIOD_END']
        top=sorted(rs,key=lambda r:float(r['weight']),reverse=True)[:5]
        result.extend([f"{name}: {len(rs)} posições finais; cinco maiores: "+'; '.join(f"{r['ticker']} {pct(float(r['weight'])*100)}%" for r in top)+'. '
          f'[Composição e unidades em cada junho](../research/returns_2014_2026_selection/{stem}_positions.csv) · '
          f'[revisões B2/entradas](../research/returns_2014_2026_selection/{stem}_reviews.csv) · '
          f'[decisões PASS/FAIL/INDETERMINATE](../research/returns_2014_2026_selection/{stem}_decisions.csv) · '
          f'[livro de eventos](../research/returns_2014_2026_selection/{stem}_ledger.csv).',''])
    result.extend([
      'BH padrão permanece integralmente congelado: CCRO3/WEGE3, ITUB4/BBDC4, HYPE3/RADL3, TBLE3/CMIG4, 12,5% iniciais por nome, '
      'mantendo XPBR31. Preservadas as convenções de capitalização por classe e atividade farmacêutica predominante da Hypermarcas de 2014, '
      'assim como todas as ressalvas de direitos do '
      '[checkpoint aceito](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/blob/5cf7eb4/docs/checkpoint_returns_2014_2026_stage1.md). '
      'Não houve nova investigação nem replay de BH/IBOV.','',
      '**Eventos comuns e convenções do índice**','',
      'Fechamentos nominais COTAHIST têm arquivo, linha e hash de registro. Proventos brutos são reinvestidos no fechamento ex, com unidades fracionárias teóricas. '
      'Eventos simultâneos usam as unidades anteriores: `q nova = q antiga × (fator + provento/P ex)`. '
      'Os eventos bancários/XP de BH são reaproveitados sem modificar suas bases; dividendos PN não são copiados para ON. '
      'Ações de novos subscritores não viram bonificação dos titulares existentes.','',
      'GETI4→TIET11 representa a cesta herdada de 1 ON+4 PN; a unit vira 1 AESB3 em março/2021. '
      'AESB3→AURE3 usa a opção padrão de novembro/2024: 0,67498865568 ação mais 1,18438832610 por ação antiga, '
      'reinvestido teoricamente na sucessora na data ex. Mantêm-se frações; não se presume adesão voluntária a outra opção. '
      'ENBR não é vendida na OPA voluntária: o resgate compulsório de 24,23 em 13/09/2023 redistribui o componente do índice entre os demais ativos. '
      'NEOE recebe o mesmo tratamento no resgate compulsório de 34,02 em 15/05/2026. Os valores unitários são coeficientes do retorno, não capital investido. '
      'Não há saldo ocioso: conserva-se o direito até o evento de resgate, aplicando redistribuição proporcional na data de pagamento.','',
      'CPLE6→CPLE5 em novembro/2025 e depois CPLE3 em dezembro/2025 preserva unidades e incorpora o resgate de 0,7749 na sucessora. '
      'AXIA7 é uma posição distinta, destacada de ELET3/AXIA3 em 22/12/2025; não é aumento da quantidade ON. '
      'Incluídos split Guararapes ×8 em 2019, Copasa ×3 em 2020, Copel ×10 em 2021 e IRB ×3 em 2019/÷30 em 2023. '
      'Light 2021 combina grupamento e desdobramento de efeito líquido 1; o direito LIGT1 de maio/2026 e IRBR1 de julho/2020 são vendidos teoricamente ao primeiro fechamento negociado '
      'e convertidos no próprio ativo. '
      '[Base compartilhada de eventos](../research/returns_2014_2026_selection/continuation_events.csv) · '
      '[correções dirigidas e URLs](../research/returns_2014_2026_selection/continuation_event_resolutions.json).','',
      '**Sensibilidades e limites de interpretação**','',
      f'As 128 combinações de entrada/não entrada dos sete candidatos/anos R03 indeterminados produzem acumulado final entre **{pct(lo)}% e {pct(hi)}%**, '
      f'contra **{pct(stats[0]["total_return_pct"])}%** no caso central e **{pct(stats[-1]["total_return_pct"])}%** no IBOV. '
      'É a amplitude exaustiva dessas decisões de entrada, mantendo todos os demais dados e regras; não é intervalo de confiança nem limite de erros de eventos. '
      'Logo, a incerteza de seleção é material para o ranking, embora não impeça publicar a trajetória condicional. '
      '[128 cenários finais](../research/returns_2014_2026_selection/r03_selection_scenarios.csv) · '
      '[trajetórias anuais dos cenários](../research/returns_2014_2026_selection/r03_selection_scenario_paths.csv).','',
      table(['Estratégia','Junho','Candidato','Tratamento'],[[r['strategy'],r['year'],r['ticker'],r['treatment']] for r in pending]),'',
      'BBDC3/ITUB3: o balanço consolidado não discrimina AC/PC de modo suficiente para F2. Não se substitui o banco por sua holding individual. '
      'SMTO3/2017: o prejuízo de 2009 exige comprovar a exceção de lucro e caixa; não foi inferida aprovação. '
      'IRBR3/2018: falta a evidência de 2013; sua inclusão hipotética está calculada abaixo. '
      'BIDI4/2019: 2015 foi recuperado no FRE 84003, recebido em maio/2019; 2014 continua sem prova. '
      'A entrada hipotética de BIDI4 solicitaria 3,3333% do índice na revisão de 2019; seu caminho completo não foi certificado. O caso central não compra BIDI4. Não se afirma que o efeito final dessa exclusão seja imaterial ou esteja limitado pelos cenários de IRB.','',
      table(['Sensibilidade','Carteira','Acumulado final %','Δ final p.p.','Maior |Δ anual| p.p.'],[
        [r['case'],r['portfolio'],pct(float(r['final_pct'])),pct(float(r['difference_from_base_pp'])),pct(float(r['largest_annual_difference_pp']))] for r in sens]),'',
      'O diagnóstico de FAIL de linhagem mede a distorção de vender TIMS/AESB e ISAE pelo novo CNPJ/ticker; não é a política adotada. '
      'O teste sem direitos omite apenas os direitos documentados nesta continuação. **Não mede direitos ainda não reconciliados.** '
      'Permanecem fora do caso central direitos adicionais negociados de ABCB, AESB, BMGB, CSMG, ENBR, EQTL, TRPL e BBDC. '
      'Sua presença na cotação não é prova suficiente da quantidade de direitos atribuída a cada ação: não se inventou esse fator. '
      'Essa lacuna impede chamar os números de retorno total definitivamente auditado. As datas e exposições identificadas estão em '
      '[inventário de direitos pendentes](../research/returns_2014_2026_selection/continuation_unresolved_rights.csv).','',
      'GETI agosto/2015 usa transcrição histórica de quatro casas decimais; o ITR 51290 foi identificado, mas a recuperação foi interrompida pelo servidor. '
      'TIM 2016/2017 usa a tabela de RI já arquivada, também arredondada. O teste ±0,00005 por ação mede somente arredondamento, não certificação de fonte. '
      'Guararapes/CPFL têm data ex inferida do primeiro pregão após aprovação e conferida contra cotações; os fatores vêm dos FRE. '
      'Limitações herdadas do primeiro período B00S e do BH permanecem visíveis nos respectivos arquivos de evidência.','',
      '**Reprodução incremental offline**','',
      '```bash\npython scripts/stage1_resume.py --freeze-events\npython scripts/stage1_continuation_audit.py\npython scripts/returns_stage1.py\npython -m pytest -q tests/test_returns_stage1.py tests/test_stage1_pit.py tests/test_stage1_continuity.py tests/test_stage1_resume.py\npython scripts/stage1_manifest.py\n```','',
      'O replay lê as posições aceitas e os caches congelados; não baixa dados, não abre o SQLite nem refaz BH/IBOV. '
      'Os CSV de posições contêm unidades adimensionais e cotações usadas no cálculo; não são simulação de valores investidos. '
      'Validação local: **174 testes aprovados** (73 da etapa percentual e 101 das baselines); 4.140 linhas FRE conferidas nos arquivos originais e 12 hashes COTAHIST confirmados. Os hashes das entradas imutáveis são verificados antes/depois. Testes cobrem conservação nas revisões, preservação relativa de sobreviventes, '
      'sucessoras, direitos no mesmo pregão, eventos simultâneos, encadeamento independente e determinismo. '
      '[Registro de validação](../research/returns_2014_2026_results/validation.json) · '
      '[manifesto de entrega](../research/returns_2014_2026_results/delivery_manifest.json). '
      'Os testes demonstram correção da implementação sob os dados e hipóteses publicados; não eliminam as lacunas documentais.',''
    ])
    return result
