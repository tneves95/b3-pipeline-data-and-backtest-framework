"""Deterministic Excel presentation of the frozen-return attribution CSVs."""
from datetime import datetime

import xlsxwriter

SHEETS = {'R03 B2': 'Graham R03 B2', 'B00S B2': 'Barsi B00S B2',
          'B00S BH+entradas': 'Barsi B00S BH entradas', 'BH padrão': 'BH Padrao'}


def workbook(path, rows, summaries, transfers):
    book = xlsxwriter.Workbook(path, {'strings_to_urls': False})
    book.set_properties({'title': 'Atribuição anual realizada 2014–2026', 'author': 'B3 research',
                         'created': datetime(2026, 10, 8), 'comments': 'Base imutável cb3db59'})
    book.set_calc_mode('auto')
    title = book.add_format({'bold': True, 'font_size': 16, 'font_color': '#17365D'})
    note = book.add_format({'text_wrap': True, 'valign': 'top', 'font_color': '#444444'})
    pct = book.add_format({'num_format': '0.000000"%"'})
    pp = book.add_format({'num_format': '0.000000" p.p."'})
    small = book.add_format({'num_format': '0.000000000000000E+00'})
    total = book.add_format({'bold': True, 'bg_color': '#DCE6F1', 'num_format': '0.000000'})
    summary = book.add_worksheet('Resumo 12 anos')
    summary.write(0, 0, 'Atribuição do retorno realizado — junho/2015 a junho/2026', title)
    summary.merge_range(1, 0, 2, 8,
        'Base cb3db59 preservada. Cada ciclo usa as posições após a revisão do junho inicial e antes da revisão do junho final. '
        'Retornos em %, contribuições em p.p.; os CSVs conservam a precisão decimal original. Caso central qualificado.', note)
    columns = ['Fechamento', 'Ciclo', *SHEETS, 'IBOV (%)', 'Conciliações exatas', 'Maior resíduo numérico (p.p.)']
    data = []
    for y in range(2015, 2027):
        group = [r for r in summaries if r['closing_june'] == f'jun/{y}']
        data.append([f'jun/{y}', group[0]['cycle'],
                     *[float(next(r for r in group if r['portfolio']==p)['published_return_pct']) for p in SHEETS],
                     float(group[0]['IBOV_pct']), '4 / 4', max(abs(float(r['numerical_residual_pp'])) for r in group)])
    summary.add_table(4, 0, 16, len(columns)-1, {'name': 'ResumoAnual', 'data': data,
        'columns': [{'header': h} for h in columns], 'style': 'Table Style Medium 2'})
    summary.set_column(0, 0, 15); summary.set_column(1, 1, 24)
    summary.set_column(2, 6, 21, pct); summary.set_column(7, 7, 22); summary.set_column(8, 8, 30, small)
    summary.freeze_panes(5, 2)
    summary.merge_range(19, 0, 21, 8,
        'Abra a aba da carteira e filtre por fechamento ou ticker. As três maiores contribuições positivas e negativas '
        'estão sinalizadas em cada ano. IBOV aparece apenas nos totais. O peso final refere-se à exposição de origem '
        'e seus descendentes; resgates mantêm a atribuição dos recursos e do desempenho posterior na origem resgatada.', note)
    headers = ['Fechamento', 'Ciclo anterior', 'Ticker no início (livro)', 'Sucessor / cisão / direito',
               'Peso inicial (%)', 'Retorno bruto da exposição (%)', 'Contribuição (p.p.)',
               'Peso final pré-revisão (%)', 'Evento / status / limitação', 'Destaque no ano',
               'IBOV anual (%) — total', 'Tipo de linha', 'Contribuição decimal exata (texto)',
               'Retorno publicado (%) — total', 'Diferença de conciliação (p.p.)', 'Fonte de posições']
    for p, sheet in SHEETS.items():
        ws = book.add_worksheet(sheet)
        ws.write(0, 0, p + ' — atribuição realizada', title)
        ws.merge_range(1, 0, 2, 15,
            'Ações compradas apenas no junho de fechamento pertencem ao ciclo seguinte. '
            'NUMERICAL_RESIDUAL é apenas ponto flutuante, sem retorno individual. '
            'Limitações de seleção PIT e proventos do caso central permanecem. Códigos seguem os aliases dos livros congelados.', note)
        line = 5
        for s in [r for r in summaries if r['portfolio'] == p]:
            start = line
            for r in [r for r in rows if r['portfolio'] == p and r['end'] == s['end']]:
                data = [r['closing_june'], r['cycle'], r['start_ticker'], r['related_securities'],
                        r['start_weight_pct'], r['exposure_return_pct'], r['contribution_pp'],
                        r['end_weight_before_review_pct'], r['status'], r['largest_contributor'], '',
                        r['row_type'], str(r['contribution_pp']), '', '', r['position_source']]
                for col, value in enumerate(data):
                    if col in (4, 5, 6, 7) and value != '':
                        ws.write_number(line, col, float(value), pp if col == 6 else pct)
                    else:
                        ws.write(line, col, value)
                if r['row_type'] == 'NUMERICAL_RESIDUAL':
                    ws.write_number(line, 6, float(r['contribution_pp']), small)
                line += 1
            ws.write_row(line, 0, [s['closing_june'], s['cycle'], 'TOTAL DA CARTEIRA'])
            ws.write_formula(line, 6, f'=SUM(G{start+1}:G{line})', total, float(s['published_return_pct']))
            ws.write_number(line, 10, float(s['IBOV_pct']), pct)
            ws.write(line, 11, 'TOTAL'); ws.write_string(line, 12, s['published_return_pct'])
            ws.write_number(line, 13, float(s['published_return_pct']), pct)
            ws.write_formula(line, 14, f'=G{line+1}-N{line+1}', small, 0)
            ws.write(line, 8, 'Conciliação decimal exata nos CSVs; Excel usa até 15 algarismos significativos.')
            line += 1
        ws.add_table(4, 0, line-1, 15, {'columns': [{'header': h} for h in headers], 'style': 'Table Style Medium 2'})
        ws.set_column(0, 0, 14); ws.set_column(1, 1, 24); ws.set_column(2, 2, 23)
        ws.set_column(3, 3, 30); ws.set_column(4, 7, 23); ws.set_column(8, 8, 65)
        ws.set_column(9, 11, 23); ws.set_column(12, 12, 34); ws.set_column(13, 14, 27)
        ws.set_column(15, 15, 48)
        ws.freeze_panes(5, 3)
        ws.conditional_format(5, 6, line-1, 6, {'type': 'cell', 'criteria': '>', 'value': 0,
            'format': book.add_format({'font_color': '#006100'})})
        ws.conditional_format(5, 6, line-1, 6, {'type': 'cell', 'criteria': '<', 'value': 0,
            'format': book.add_format({'font_color': '#9C0006'})})
    check = book.add_worksheet('Conciliacao 48 totais')
    check.add_table(0, 0, len(summaries), 12, {'name': 'Conciliacoes', 'style': 'Table Style Medium 2',
        'columns': [{'header': h} for h in ['Fechamento', 'Carteira', 'Ações iniciais', 'Retorno publicado (%)',
            'Contribuições das ações (p.p.)', 'Resíduo numérico (p.p.)', 'Soma conciliada (p.p.)', 'Diferença (p.p.)',
            'IBOV (%)', 'Maior positiva', 'Contribuição positiva (p.p.)', 'Maior negativa', 'Contribuição negativa (p.p.)']],
        'data': [[r['closing_june'], r['portfolio'], r['holdings'], float(r['published_return_pct']),
            float(r['holdings_contribution_pp']), float(r['numerical_residual_pp']), float(r['reconciled_contribution_pp']),
            float(r['reconciliation_difference_pp']), float(r['IBOV_pct']), r['largest_positive_ticker'],
            float(r['largest_positive_contribution_pp']) if r['largest_positive_ticker'] else '', r['largest_negative_ticker'],
            float(r['largest_negative_contribution_pp']) if r['largest_negative_ticker'] else ''] for r in summaries]})
    check.freeze_panes(1, 2); check.set_column(0, 12, 26); check.set_column(5, 5, 30, small)
    movement = book.add_worksheet('Transferencias resgates')
    keys = list(transfers[0])
    movement.add_table(0, 0, len(transfers), len(keys)-1, {'name': 'Transferencias',
        'columns': [{'header': k} for k in keys], 'data': [list(r.values()) for r in transfers], 'style': 'Table Style Medium 2'})
    movement.freeze_panes(1, 4); movement.set_column(0, len(keys)-1, 25)
    methods = book.add_worksheet('Leia-me')
    notes = [
        ('Escopo', 'Atribuição realizada das quatro carteiras congeladas em cb3db59. Nenhum backtest, seleção ou revisão executado pelo gerador de atribuição.'),
        ('Fronteira temporal', 'Após a revisão do junho inicial até antes da revisão do junho final, nas datas efetivas de pregão dos CSVs.'),
        ('Contribuição', '100 × (componente final da exposição de origem − componente inicial) / índice inicial da carteira. Retorno da exposição = 100 × (final/inicial − 1).'),
        ('Unidades', 'Componentes e unidades de índice são adimensionais. Não representam dinheiro, caixa, aportes ou impostos.'),
        ('Cisões, direitos e sucessões', 'Durante o ciclo permanecem na origem que adquiriu o direito. Se o descendente já está fisicamente na carteira no junho inicial seguinte, passa a ter linha própria.'),
        ('Resgates compulsórios', 'Principal transferido não é rendimento. A origem resgatada passa a acompanhar uma fração da cesta sobrevivente; o retorno subsequente permanece nessa origem até o fim do ciclo.'),
        ('Peso final', 'Peso dos descendentes da exposição inicial antes da revisão. Em resgate pode ser uma cesta de vários papéis, detalhada em attribution_end_lineage.csv.'),
        ('Eventos', 'Somente eventos do livro congelado. attribution_event_lineage.csv detalha unidades por origem e data. Não há novas pesquisas ou alterações nos proventos.'),
        ('Precisão', 'Os CSVs conciliam exatamente com os decimais originais. Resíduo numérico explícito de ponto flutuante limitado a 1e-9 p.p.; valores efetivos no resumo. Excel usa até 15 algarismos significativos.'),
        ('Aliases', 'Tickers seguem os livros: EGIE3/TBLE3, DTEX3/DXCO3, RIAA3/GUAR3, ESTC3/YDUQ3, ISAE4/TRPL4, AXIA3/ELET3, MOTV3/CCRO3. São continuidades de identidade, não novas compras.'),
        ('Limitações', 'Caso central qualificado, sem certificação PIT ou de total return plena. Mantidas as limitações históricas e sensibilidades publicadas no checkpoint cb3db59.'),
        ('Reprodução', 'python -m pip install XlsxWriter==3.2.5; python scripts/stage1_attribution.py. O manifesto verifica 271 arquivos congelados e documenta hashes dos novos artefatos.'),
        ('Coordenador', 'https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/3#issuecomment-6066153641'),
    ]
    for i, (key, value) in enumerate(notes):
        methods.write(i, 0, key); methods.write(i, 1, value, note); methods.set_row(i, 60)
    methods.set_column(0, 0, 26); methods.set_column(1, 1, 115)
    book.close()
