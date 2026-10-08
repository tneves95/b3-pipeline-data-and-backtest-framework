"""Current checkpoint, retaining the benchmark and marking unresolved paths."""
import csv
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SEL=ROOT/'research/returns_2014_2026_selection'

def read(name):
    return list(csv.DictReader((SEL/name).open(encoding='utf8')))

def render(annual,accumulated,stats,segments,names,pct,table):
    established=read('established_selections.csv');screen=read('screening.csv')
    initial=[r for r in established if r['year']=='2014']
    coverage=[]
    for y in range(2014,2020):
        line=[str(y)]
        for strategy in ['R03','B00S']:
            group=[r for r in screen if r['year']==str(y) and r['strategy']==strategy]
            passed=[r['ticker'] for r in group if r['status']=='PASS']
            pending=[r['ticker'] for r in group if r['status']=='INDETERMINATE']
            line.extend([', '.join(passed),', '.join(pending) or 'Nenhum no universo examinado'])
        coverage.append(line)
    total=stats[-1]
    return [
        '# Checkpoint — etapa 1 percentual, 2014–2026 — continuação em 08/10/2026','',
        '**Avanço publicado: R03 B2 calculado de junho/2014 a junho/2016; o estudo completo das quatro carteiras ainda está pendente.** '
        'A continuação aproveita o checkpoint `0a6a20c`, os arquivos CVM/B3 e o SQLite em leitura somente. '
        'O IBOV e as referências legadas foram preservados. ND significa não determinado, nunca retorno zero.','',
        f"R03 B2: **{pct(annual[0]['R03 B2'])}% em 2014–2015**, **{pct(annual[1]['R03 B2'])}% em 2015–2016**, "
        f"**{pct(accumulated[1]['R03 B2'])}% acumulados até junho/2016**. "
        f"IBOV nas mesmas duas janelas: {pct(annual[0]['IBOV'])}% e {pct(annual[1]['IBOV'])}%; "
        f"acumulado {pct(accumulated[1]['IBOV'])}%. IBOV completo até junho/2026: **{pct(total['total_return_pct'])}%**. "
        'Não há vencedor de 2014–2026 enquanto faltarem as trajetórias completas.','',
        'Escopo: [retificação do coordenador](https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/2#issuecomment-6059288518). '
        'Somente índices teóricos e rentabilidades percentuais brutas; nenhuma simulação de patrimônio nominal, caixa, aportes ou impostos.','',
        '**Tabela 1 — retorno anual junho→junho (%)**','',
        table(['Período','Início','Fim',*names],[[r['period'],r['start'],r['end'],*[pct(r[n]) for n in names]] for r in annual]),'',
        '[Diferenças anuais contra IBOV, em p.p.](../research/returns_2014_2026_results/annual_excess_pp.csv). '
        f"R03: {pct(annual[0]['R03 B2']-annual[0]['IBOV'])} p.p. e {pct(annual[1]['R03 B2']-annual[1]['IBOV'])} p.p. nas duas janelas calculadas.",'',
        '**Tabela 2 — retorno acumulado desde junho/2014 (%)**','',
        table(['Até',*names],[[r['end'],*[pct(r[n]) for n in names]] for r in accumulated]),'',
        'Encadeamento: `100 × (produto(1 + retorno_anual_decimal) − 1)`, índice inicial 1. '
        'A ausência de 2016–2017 impede o acumulado posterior do R03; os segmentos legados não reiniciam a trajetória em 2020.','',
        '**Tabela 3 — consolidado 2014–2026**','',
        table(['Série','Janelas calculadas /12','Acumulado %','CAGR %','Acima IBOV /12','Pos./neg./zero','Média anual %','Mediana anual %','Melhor ano (%)','Pior ano (%)','Posição média / consistência'],
            [[r['portfolio'],r['observed_intervals'],pct(r['total_return_pct']),pct(r['cagr_pct']),'N/A' if r['portfolio']=='IBOV' else 'ND',
              f"{r['positive_years']}/{r['negative_years']}/{r['flat_years']}" if r['positive_years'] is not None else 'ND',
              pct(r['mean_annual_pct']),pct(r['median_annual_pct']),
              f"{r['best_period']} ({pct(r['best_return_pct'])})" if r['best_period'] else 'ND',
              f"{r['worst_period']} ({pct(r['worst_return_pct'])})" if r['worst_period'] else 'ND','ND / ND'] for r in stats]),'',
        'CAGR usa dias efetivos/365,25. Estatísticas finais e ranking exigem as 12 janelas comparáveis. '
        'Nas duas janelas R03 calculadas houve um ano positivo, um negativo e um acima do IBOV; isso não representa frequência em 12 anos.','',
        '**Seleções históricas resolvidas nesta continuação**','',
        'No universo de classes ON/PN efetivamente negociadas, com os filtros de liquidez originais, '
        'R03/2014–2015 e B00S/2014–2016 não têm candidatos INDETERMINATE. '
        'As listas abaixo separam os PASS demonstrados dos candidatos ainda indeterminados; somente as cinco seleções fechadas '
        'foram exportadas como estabelecidas. As seleções legadas de 2020–2025 permanecem preservadas e condicionais.','',
        table(['Junho','R03: PASS','R03: indeterminados','B00S: PASS','B00S: indeterminados'],coverage),'',
        '**Seleção inicial e pesos de junho/2014**','',
        table(['Filosofia','Ação','Setor','Peso %'],[[r['strategy'],r['ticker'],r['sector'],pct(float(r['weight'])*100)] for r in initial]),'',
        'R03 começa com seis ações em pesos iguais. B00S começa com vinte ações, 20% por setor BESST e pesos iguais dentro de cada setor. '
        'Esse mesmo conjunto inicial se aplica ao B00S B2 e ao B00S BH+entradas. '
        'Em junho/2015, R03 conserva DIRR3, EZTC3 e HBOR3; retira CMIG3, JHSF3 e LPSB3; '
        'acrescenta ALSC3, DTEX3, GRND3, GUAR3, HGTX3 e MILS3, com nove pesos iguais. '
        '[Pesos das seleções fechadas](../research/returns_2014_2026_selection/established_selections.csv), '
        '[triagem integral](../research/returns_2014_2026_selection/screening.csv) e '
        '[retornos e contribuições por posição](../research/returns_2014_2026_selection/established_segment_positions.csv).','',
        '**Proveniência PIT e reparações materiais**','',
        'Foram incorporados os originais de BB e Itaú já recuperados e 17 originais CVM adicionais, dos quais se extraíram 1.306 fatos contábeis. '
        'Entre os reparos: Copel/2013, Equatorial/2015–2016, Cemig/2015, Light/2015, Engie/2022 e Brasil Pharma/2013. '
        'Recebimento, versão, conta, perímetro, exercício, documento e hash acompanham os extratos. '
        'O arquivo de Engie usa o XML moderno da CVM; os demais usam o original ENET. '
        'FCA e FRE anteriores aos cortes complementam identidade, atividade econômica, capital emitido/integralizado e tesouraria.','',
        'O código distingue a conta de lucro das reversões de JCP de bancos e distingue ativo circulante de caixa pelo nome da conta. '
        'Colunas comparativas de resultado inteiramente zeradas no ENET permanecem ausentes; não viram prova de prejuízo nem de lucro. '
        'O lucro individual publicado pode suprir uma DRE consolidada vazia, com seu perímetro identificado. '
        'A falta de um exercício não encobre uma reprovação demonstrável em outro: Brasil Pharma/2013 tem prejuízo publicado e reprova o requisito dos últimos três anos positivos. '
        'A constituição de uma companhia depois do primeiro exercício exigido é registrada como histórico insuficiente demonstrado, sem inventar dados de predecessoras.','',
        'Para R03, história `max(2009, ano−10)..ano−1`, proporção `ceil(0,8 × n)`, demais restrições de perdas preservadas, '
        'e crescimento entre médias de três exercícios. F4 mantém a hierarquia herdada: B3/DFC individual, com DMPL/DVA individual como evidência mais fraca, sem reduzir a exigência de recorrência. '
        'F6 usa capital conhecido no corte e distingue o teste com capital bruto da dedução de tesouraria documentada. '
        'B00S conserva cinco exercícios e a taxonomia BESST estrita: corretoras, administradoras de benefícios e distribuição de gás não são promovidas a seguradoras ou saneamento.','',
        '**Convenção de retorno e cobertura restante**','',
        'Fechamento do último pregão de junho em todas as séries; reinvestimento teórico integral de cada distribuição bruta no próprio ativo no fechamento da data-ex. '
        'Os dois segmentos novos usam preços nominais e eventos, sem preços ajustados somados novamente a dividendos. '
        'Datas-com B3 são convertidas ao pregão seguinte do calendário observado. Não há saldos operacionais. '
        'A Cemig tinha somente metade do JCP de dezembro/2014 no SQLite; o aviso oficial confirma duas parcelas de 50%, e o valor integral foi restaurado uma única vez. '
        'Histórias B3 sob os ISIN atuais de Dexco e Riachuelo foram associadas aos nomes históricos DTEX3 e GUAR3 pelo mesmo emissor/classe. '
        'Os valores são uma reconstrução com as fontes disponíveis, não certificação de completude universal de eventos.','',
        'O retorno B00S ainda depende de eventos que não podem ser substituídos por zero: bonificações bancárias históricas, '
        'GETI→TIET→AESB→AURE, cisão Itaú/XPart e término de ENBR. '
        'Para BH+entradas é necessário manter as sucessoras e os nomes reprovados, com redistribuição interna de pesos somente quando houver novos elegíveis. '
        'A OPA voluntária de ENBR usada no legado não comprova sozinha um cash-out compulsório para BH.','',
        'O ranking BH padrão avançou para o cruzamento de capital, preços de todas as classes e atividade conhecida em 2014. '
        'Os líderes candidatos são CCRO/WEG, Itaú/Bradesco, Tractebel/Cemig e Hypermarcas/Raia Drogasil, mas o ranking ainda requer reconciliação de eventos de capital e classes. '
        'O Santander foi retirado do ranking nominal incorreto: o FRE trazia capital anterior ao grupamento 55:1 de junho/2014; '
        'um limite superior após a bonificação/grupamento o coloca abaixo dos dois líderes financeiros. '
        'Isso é um limite de exclusão documentado, não uma capitalização exata inventada. '
        'Hypermarcas é uma candidata de atividade mista, a justificar economicamente no corte; não se usa o perfil atual da Hypera. '
        '[Mapa de capitalização e ressalvas](../research/returns_2014_2026_selection/market_cap_2014.csv). '
        'As oito ações ainda não foram promovidas a uma carteira BH calculada.','',
        'Bebidas, agricultura, joalheria e papel/celulose ficam fora dos quatro grupos. '
        'Dados indeterminados continuam explícitos; não há retorno calculado de uma carteira formada pela simples exclusão silenciosa desses candidatos.','',
        '**Referências legadas 2020–2026, preservadas e fora da trajetória primária**','',
        table(['Período','R03 legado %','B00S legado %','IBOV %','R03−IBOV p.p.','B00S−IBOV p.p.'],
            [[r['period'],*[pct(r[k]) for k in ['R03_inherited_pct','B00S_inherited_pct','IBOV_pct','R03_minus_IBOV_pp','B00S_minus_IBOV_pp']]] for r in segments]),'',
        'São os mesmos números condicionais do checkpoint anterior, oriundos das baselines v11.2/v12/v13. '
        'Não cobrem 2016–2020 nem substituem eventos e seleções da nova trajetória. Nenhum motor fiscal foi executado.','',
        '**Reprodução e preservação**','',
        '```bash\npython scripts/stage1_select.py\npython scripts/stage1_segments.py\npython scripts/returns_stage1.py\n'
        'python -m pytest -q tests/test_returns_stage1.py tests/test_stage1_pit.py\n```','',
        'A reprodução usa os caches incluídos e não precisa de rede nem do SQLite. Os scripts `stage1_pit.py`, '
        '`stage1_supplement.py`, `stage1_capital.py` e `stage1_recover.py` servem à coleta incremental, não precisam ser repetidos para continuar. '
        'Os originais, hashes e pendências estão em [seleção PIT](../research/returns_2014_2026_selection/). '
        'A série IBOV e seus 13 arquivos B3 permanecem idênticos ao checkpoint inicial. '
        'A branch e o PR #3 continuam os mesmos; baselines e PR #2 preservados.','',
        'Validação local: **137 testes aprovados** (36 da etapa percentual/PIT e 101 das baselines). '
        '**54 cotações exatas** de fronteira/reinvestimento conferidas diretamente nos registros COTAHIST de 2014–2016, '
        'com arquivo, linha e hash. O replay dos resultados é offline e determinístico. '
        'Os testes verificam as invariantes e os segmentos entregues; não certificam as trajetórias ainda ausentes.','',
        '**Próxima prioridade:** resolver os candidatos de 2016–2019 listados acima e as continuidades materiais dos vinte nomes B00S iniciais; '
        'concluir o ranking de 2014 e então preencher as demais janelas. O pedido de quatro trajetórias completas permanece aberto.',''
    ]
