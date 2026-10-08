"""Reproducible checkpoint with numerical trajectories and explicit qualifications."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SEL=ROOT/'research/returns_2014_2026_selection'
def read(name):
    return list(csv.DictReader((SEL/name).open(encoding='utf8')))

def render(annual,accumulated,stats,segments,names,pct,table):
    screen=read('screening.csv');bh=stats[3];ibov=stats[4]
    selection=read('bh_selection_2014.csv');reviews=read('b2_reviews.csv')
    before=sum(float(r['before']) for r in reviews);after=sum(float(r['after']) for r in reviews)
    initial=[r for r in read('established_selections.csv') if r['year']=='2014']
    coverage=[]
    for y in range(2016,2020):
        line=[y]
        for s in ['R03','B00S']:
            line.append(', '.join(r['ticker'] for r in screen if r['year']==str(y) and r['strategy']==s and r['status']=='INDETERMINATE') or 'Nenhum')
        coverage.append(line)
    return [
      '# Checkpoint — Barsi × Graham, etapa percentual 2014–2026 — 08/10/2026','',
      '**B2 corrigido; uma trajetória de 12 anos calculada (BH padrão); primeiro ano das duas variantes B00S calculado. O estudo das quatro trajetórias permanece parcial.** '
      'Continuação do commit `1ceab3f`, na mesma branch e no PR #3 draft, conforme a '
      '[última revisão do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/3#issuecomment-6062365631). '
      'IBOV e referências legadas preservados. Nenhum motor de dinheiro, caixa, aportes, execução D+1 ou IR foi executado.','',
      f"BH padrão: **{pct(bh['total_return_pct'])}%** acumulados, **{pct(bh['cagr_pct'])}%** a.a., acima do IBOV em **{bh['above_ibov_years']}/12** janelas. "
      f"IBOV: **{pct(ibov['total_return_pct'])}%**, CAGR **{pct(ibov['cagr_pct'])}%**. "
      'São reconstruções brutas sob as convenções abaixo, com ressalvas explícitas de classes no ranking e de eventos. Não equivalem a uma certificação integral de todas as fontes.','',
      f"R03 B2: {pct(annual[0]['R03 B2'])}% em 2014–2015 e **{pct(annual[1]['R03 B2'])}%** em 2015–2016; "
      f"acumulado **{pct(accumulated[1]['R03 B2'])}%** até junho/2016, ante {pct(accumulated[1]['IBOV'])}% do IBOV. "
      f"B00S inicial: **{pct(annual[0]['B00S B2'])}%** nas duas variantes, ante {pct(annual[0]['IBOV'])}% do IBOV. "
      'B00S é exploratório: algumas provas de direitos dependem de transcrições e uma data de destacamento inferida; veja o inventário de evidências.','',
      '**Rentabilidade anual junho→junho (%)**','',
      table(['Período','Início','Fim',*names],[[r['period'],r['start'],r['end'],*[pct(r[n]) for n in names]] for r in annual]),'',
      'ND significa não determinado; nunca zero. [Diferenças anuais contra IBOV, em p.p.](../research/returns_2014_2026_results/annual_excess_pp.csv).','',
      '**Rentabilidade acumulada desde junho/2014 (%)**','',
      table(['Até',*names],[[r['end'],*[pct(r[n]) for n in names]] for r in accumulated]),'',
      'Encadeamento: `100 × (produto(1 + retorno_anual_decimal) − 1)`. Uma janela ausente interrompe todo acumulado posterior. '
      'As referências legadas de 2020 não completam nem reiniciam as carteiras formadas em 2014.','',
      '**Consolidado até junho/2026**','',
      table(['Série','Janelas /12','Acumulado %','CAGR %','Acima IBOV /12','Anos + / − / =','Média anual %','Mediana anual %','Melhor período (%)','Pior período (%)'],[
        [r['portfolio'],r['observed_intervals'],pct(r['total_return_pct']),pct(r['cagr_pct']),
         'N/A' if r['portfolio']=='IBOV' else ('ND' if r['above_ibov_years'] is None else r['above_ibov_years']),
         'ND' if r['positive_years'] is None else f"{r['positive_years']} / {r['negative_years']} / {r['flat_years']}",
         pct(r['mean_annual_pct']),pct(r['median_annual_pct']),
         f"{r['best_period']} ({pct(r['best_return_pct'])})" if r['best_period'] else 'ND',
         f"{r['worst_period']} ({pct(r['worst_return_pct'])})" if r['worst_period'] else 'ND'] for r in stats]),'',
      'CAGR por dias efetivos/365,25. Ranking entre as quatro carteiras e posição média permanecem ND enquanto faltarem trajetórias comparáveis.','',
      '**B2: continuidade e renovação seletiva**','',
      'Na revisão de junho/2015, DIRR3, EZTC3 e HBOR3 carregam as participações vindas de 2014. '
      'CMIG3, JHSF3 e LPSB3 saem por FAIL. ALSC3, DTEX3, GRND3, GUAR3, HGTX3 e MILS3 entram. '
      'A regra operacional reserva aos entrantes sua fração-alvo da filosofia (seis vezes 1/9 nesta revisão), '
      'financiada primeiro pelas saídas FAIL; somente a insuficiência reduz proporcionalmente os sobreviventes. '
      'Se as saídas excederem a necessidade, o excedente se distribui aos entrantes na proporção-alvo. '
      'Sem entrantes, saídas se redistribuem proporcionalmente aos sobreviventes; sem entradas/saídas, nada muda. '
      'Ausência no screener ou INDETERMINATE não autoriza saída. A regra é comum às duas filosofias e não restabelece pesos iguais dos sobreviventes.','',
      f"Índice antes/depois da revisão: `{before:.12f}` / `{after:.12f}`. "
      '[Livro da revisão](../research/returns_2014_2026_selection/b2_reviews.csv) e '
      '[pesos efetivos, retornos e contribuições](../research/returns_2014_2026_selection/established_segment_positions.csv). '
      'Os pesos de `established_selections.csv` são alvos da seleção, não pesos executados de B2. '
      'O resultado antigo **+1,9285%** foi preservado como '
      '[diagnóstico da seleção anual com pesos iguais](../research/returns_2014_2026_selection/annual_selection_diagnostic_pct.csv), separado da trajetória B2.','',
      '**Concentração inicial R03:** cinco das seis empresas são de construção/imobiliárias; as seis posições perderam entre aproximadamente 16,53% e 66,61%. '
      'A perda de 45,0683% é mantida como resultado exploratório. Não foi imposta diversificação retrospectiva.','',
      '**BH padrão: escolha em 2014 e continuidade**','',
      table(['Bloco','Empresa/classe','Capitalização no corte (bilhões)','Peso inicial %'],[
        [r['block'],r['ticker'],pct(float(r['ranking_capitalization'])/1e9),pct(float(r['initial_weight'])*100)] for r in selection]),'',
      'Capitalização serve somente à seleção; não representa dinheiro investido. Uma companhia aparece uma única vez; somam-se ON e PN. '
      'Capital/documento/recebimento e preços por classe estão no '
      '[ranking reproduzível](../research/returns_2014_2026_selection/bh_ranking_2014.csv). '
      'A classe mais líquida representa a companhia na carteira, com 12,5% inicial por companhia. '
      'Os oito líderes têm preços contemporâneos de suas classes relevantes. Para concorrentes sem negócio ON no corte, '
      'usa-se a última cotação anterior; para ON sem cotação observada, PN é uma aproximação explicitamente identificada. '
      'Duplicar o preço dessas ON no teste de sensibilidade não altera os oito nomes; isso não constitui limite matemático de avaliação. '
      'O ranking é condicionado a essas convenções, não uma capitalização exata inventada para classes não cotadas. '
      'Para Santander mantém-se o limite de exclusão após o grupamento 55:1 e a bonificação já documentados. '
      'A aproximação por classe PN agregada dos concorrentes com múltiplas preferenciais permanece indicada na base herdada.','',
      'Hypermarcas entra em saúde por atividade predominante conhecida no corte: o release de 21/02/2014 informa receita total de 4,2587 bilhões '
      'em 2013 e cerca de 2,3 bilhões em Farma (aproximadamente 54%). '
      '[Release original recuperado](../research/returns_2014_2026_selection/originals/hypera_2013_release.pdf.gz). '
      'Era um negócio misto; a classificação econômica por predominância não usa o perfil posterior da Hypera e difere da rubrica genérica Comércio do FCA. '
      'Bebidas, agricultura, joalheria e papel/celulose continuam fora dos quatro blocos.','',
      'Após a formação, não há recomposição anual de pesos. TBLE3→EGIE3 e CCRO3→MOTV3 são continuidades 1:1. '
      'As bonificações e desdobramentos alteram unidades do índice; a cisão Itaú/XPart gera XPBR31 (1/43,3128323 por ITUB4), mantida até 2026. '
      'O direito CMIG2 de 2017 é destacado e convertido no próprio ativo ao primeiro fechamento negociado, sem aporte. '
      '[Posições em cada junho](../research/returns_2014_2026_selection/bh_june_positions.csv), '
      '[retornos e contribuições anuais por companhia](../research/returns_2014_2026_selection/bh_issuer_annual_pct.csv), '
      '[eventos e fontes](../research/returns_2014_2026_selection/bh_owned_events.csv), '
      '[movimentações de unidades](../research/returns_2014_2026_selection/bh_event_ledger.csv).','',
      'Fechamentos nominais vêm diretamente dos COTAHIST locais, com linha/hash de registro e hash do arquivo. '
      'Proventos brutos são reinvestidos teoricamente no próprio ativo no fechamento da data-ex. '
      'Bonificação e distribuição simultâneas respeitam a posição anterior: `q_nova = q_antiga × (F + D/P_ex)`. '
      'As correções incluem bonificações antigas de WEG, Itaú, Bradesco, Cemig, Engie e Raia, o JCP Cemig dezembro/2014 integral '
      'e duas parcelas de JCP Bradesco na mesma data-com que a chave única do SQLite não preserva. '
      'Ações resultantes de ofertas públicas, opções a empregados e incorporação de outras companhias não viram bonificação do titular existente.','',
      'XP usa proventos brutos anunciados em USD, convertidos pela PTAX venda na data-ex e reinvestidos em XPBR31. '
      'É uma convenção de índice bruto em BRL, sem custos de depositário, retenções ou simulação da liquidação efetiva do BDR. '
      'O primeiro anúncio de 2023 informa valor arredondado de USD 0,58; a precisão publicada é mantida. '
      '[Mapa de fontes e convenções](../research/returns_2014_2026_selection/bh_evidence.json).','',
      '**B00S inicial: resultado efetivo e ressalvas**','',
      'Mantidos os 20 nomes e os pesos de 2014: cinco bancos a 4%, dez elétricas a 2%, CSMG3/SBSP3 a 10%, PSSA3 a 20%, TIMP3/VIVT4 a 10%. '
      'O primeiro período é comum às variantes B2 e BH+entradas. Foram incorporados os proventos CVM da AES Tietê, a ata TIM com valor/data-com exatos, '
      'o dividendo Light, a bonificação CPFL e os direitos ABCB2/TRPL2, além dos eventos bancários e Cemig compartilhados com BH. '
      'GETI4 permanece inteira até o fim desta janela; não foi antecipada a cadeia societária posterior.','',
      '[Evidências e pendências pontuais](../research/returns_2014_2026_selection/b00s_initial_evidence.json), '
      '[posições](../research/returns_2014_2026_selection/b00s_initial_positions.csv), '
      '[retornos e contribuições dos 20 nomes](../research/returns_2014_2026_selection/b00s_initial_contributions.csv), '
      '[eventos](../research/returns_2014_2026_selection/b00s_initial_events.csv) e '
      '[sensibilidade à omissão de direitos](../research/returns_2014_2026_selection/b00s_initial_sensitivity.csv). '
      'Datas-com GETI e os direitos ABCB têm corroboração histórica secundária; o destacamento TRPL é inferido. '
      'Essas limitações estão no status do resultado, não ocultas como eventos de valor zero.','',
      '**Seleções PIT e trabalho ainda necessário**','',
      'Preservadas as seleções fechadas R03 2014–2015 e B00S 2014–2016, os 1.306 fatos recuperados e os documentos CVM já publicados. '
      'A enumeração anual de nomes PASS não substitui os pesos herdados nem autoriza vender sucessoras por troca de ticker.','',
      table(['Junho','R03 indeterminados','B00S indeterminados'],coverage),'',
      'Próximas extensões: B00S 2015–2016 com GETI→TIET e renovação seletiva; resolver candidatos PIT 2016–2019 por impacto; '
      'depois aplicar as fontes congeladas 2020–2025 à trajetória contínua. Para BH+entradas, manter sucessoras e nomes que deixem de passar; '
      'a OPA voluntária ENBR do legado não comprova cash-out compulsório. As outras três trajetórias até 2026 continuam abertas.','',
      '**Referências legadas preservadas, fora das trajetórias primárias**','',
      table(['Período','R03 legado %','B00S legado %','IBOV %'],[[r['period'],pct(r['R03_inherited_pct']),pct(r['B00S_inherited_pct']),pct(r['IBOV_pct'])] for r in segments]),'',
      '**Reprodução offline**','',
      '```bash\npython scripts/stage1_bh_selection.py\npython scripts/stage1_segments.py\npython scripts/stage1_buyhold.py\npython scripts/stage1_b00s_initial.py\npython scripts/returns_stage1.py\npython -m pytest -q tests/test_returns_stage1.py tests/test_stage1_pit.py tests/test_stage1_continuity.py\n```','',
      'Não é necessário refazer a seleção PIT, baixar fontes ou abrir o SQLite para reproduzir os resultados. '
      'As opções de coleta são separadas do replay. `stage1_manifest.py` registra os hashes de fontes e entregáveis. '
      'Testes verificam conservação nas revisões B2, ausência de giro indevido, direitos e sucessoras, reinvestimento sem dupla contagem, '
      'identidade do encadeamento, IBOV preservado e reprodução determinística. As baselines v11–v13 continuam protegidas por seus testes. '
      'Validação local: **160 testes aprovados**, 59 da etapa percentual/PIT/continuidade e 101 das baselines. '
      '[Registro de validação](../research/returns_2014_2026_results/validation.json). '
      'Os testes validam a implementação e os artefatos; não eliminam as ressalvas documentais expostas.',''
    ]
