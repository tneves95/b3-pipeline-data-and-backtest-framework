#!/usr/bin/env python3
"""Attribute frozen cb3db59 returns. No screening, renewal or backtest is run.

Each source is a security actually held at the opening June. Corporate descendants
keep that source until the closing June. Redemption transfers preserve their
source and subsequently earn the returns of the receiving securities.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, localcontext
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math

from stage1_pit import ROOT, OUT, DATES, gzread
from stage1_resume import event_day, prices

RESULT = ROOT / 'research/returns_2014_2026_results'
INPUT = ROOT / 'research/returns_2014_2026_inputs'
PORTFOLIOS = ('R03 B2', 'B00S B2', 'B00S BH+entradas', 'BH padrão')
STEMS = dict(zip(PORTFOLIOS[:3], ('r03_continuation', 'b00s_b2_continuation', 'b00s_bh_continuation')))
LIMITATION = 'Caso central qualificado cb3db59; limitações PIT/proventos herdadas, sem nova certificação'


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader(); w.writerows(rows)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen():
    manifest = json.loads((INPUT / 'attribution_frozen_inputs.json').read_text())
    for r in manifest['files']:
        if sha(ROOT / r['path']) != r['sha256']:
            raise ValueError(('Frozen backtest input/output changed', r['path']))
    return len(manifest['files'])


def aggregate(sleeves):
    by_ticker = defaultdict(list)
    for units in sleeves.values():
        for t, q in units.items():
            by_ticker[t].append(q)
    return {t: math.fsum(qs) for t, qs in by_ticker.items()}


def assert_units(actual, expected):
    if actual.keys() != expected.keys():
        raise ValueError(('Security set differs from frozen book', actual.keys(), expected.keys()))
    for t, q in expected.items():
        if not math.isclose(actual[t], q, rel_tol=3e-12, abs_tol=1e-15):
            raise ValueError(('Units differ from frozen book', t, actual[t], q))


def attribute_day(sleeves, events, quote, day):
    """Linear event attribution, with explicit conserved redemption transfers.

    Ordinary operations reuse the accepted entitlement function. A redemption
    allocates its source units into the *whole portfolio's* surviving basket;
    it never boosts the pre-existing sources of the recipient securities.
    All values in transfer records are dimensionless index components.
    """
    if len({e['id'] for e in events}) != len(events):
        raise ValueError('Duplicate event identity')
    before = {o: u.copy() for o, u in sleeves.items()}
    ordinary = [e for e in events if e['kind'] not in ('CONVERSION', 'REDEMPTION')]
    after = {o: event_day(u, ordinary, quote, day) for o, u in before.items()}
    transfers = []
    for e in events:
        t = e['ticker']
        if not any(t in u for u in before.values()):
            continue
        if e['kind'] == 'CONVERSION':
            for origin, u in after.items():
                if t not in before[origin]:
                    continue
                q = u.pop(t)
                for child, ratio in e['legs']:
                    u[child] = u.get(child, 0) + q * ratio
                if e.get('amount'):
                    child = e['legs'][0][0]
                    u[child] += before[origin][t] * e['amount'] / quote[child, day]
        elif e['kind'] == 'REDEMPTION':
            basket = {s: q for s, q in aggregate(after).items() if s != t}
            nav = math.fsum(q * quote[s, day] for s, q in basket.items())
            if nav <= 0:
                raise ValueError('Redemption without surviving basket')
            for origin, u in after.items():
                q = u.pop(t, 0)
                if not q:
                    continue
                principal = q * e['amount']
                for child, quantity in sorted(basket.items()):
                    added = principal * quantity / nav
                    u[child] = u.get(child, 0) + added
                    transfers.append(dict(date=day, event_id=e['id'], origin_ticker=origin,
                        redeemed_ticker=t, recipient_ticker=child, recipient_weight=quantity*quote[child, day]/nav,
                        redeemed_index_component=principal, transferred_index_component=added*quote[child, day],
                        added_index_units=added, source=e['source']))
    return after, transfers


def continue_attribution(left, right, ledger, events, quote, start, end):
    """Read the frozen day's event IDs and validate against every ledger change."""
    sleeves = {r['ticker']: {r['ticker']: float(r['units'])} for r in left}
    physical = aggregate(sleeves)
    bydate = defaultdict(list)
    for r in ledger:
        if start < r['date'] <= end:
            bydate[r['date']].append(r)
    flows, transfers = [], []
    seen = {t: set() for t in sleeves}
    related = {t: set() for t in sleeves}
    for day, changes in sorted(bydate.items()):
        ids = changes[0]['event_ids'].split(';')
        if any(r['event_ids'].split(';') != ids for r in changes):
            raise ValueError('Inconsistent event IDs on a frozen ledger date')
        day_events = [events[i] for i in ids]
        before = {o: u.copy() for o, u in sleeves.items()}
        sleeves, moved = attribute_day(sleeves, day_events, quote, day)
        transfers.extend(moved)
        for r in changes:
            t = r['ticker']
            if not math.isclose(physical.get(t, 0), float(r['units_before']), rel_tol=3e-12, abs_tol=1e-15):
                raise ValueError(('Ledger pre-event discrepancy', day, t))
            if float(r['units_after']):
                physical[t] = float(r['units_after'])
            else:
                physical.pop(t, None)
        assert_units(aggregate(sleeves), physical)
        for origin, u in sleeves.items():
            relevant = [e for e in day_events if e['ticker'] in before[origin]
                        or (e['kind'] == 'RIGHT_REINVEST' and e['ticker'] in
                            {x.get('successor') for x in day_events if x['ticker'] in before[origin]})]
            seen[origin].update(e['id'] for e in relevant)
            for e in relevant:
                related[origin].update([e['successor']] if e.get('successor') else [])
                related[origin].update(t for t, _ in e.get('legs', []))
            related[origin].update(t for t in u if t != origin)
            for t in sorted(before[origin].keys() | u.keys()):
                a, b = before[origin].get(t, 0), u.get(t, 0)
                if a != b:
                    flows.append(dict(date=day, origin_ticker=origin, ticker=t,
                        index_units_before=a, index_units_after=b,
                        event_ids=';'.join(e['id'] for e in relevant)))
    assert_units(aggregate(sleeves), {r['ticker']: float(r['units']) for r in right})
    return sleeves, flows, transfers, seen, related


def base_row(portfolio, year, ticker, left, right, nav0, nav1, source,
             weight=None, ret=None, contribution=None, related=(), events=(), status=''):
    return dict(closing_june=f'jun/{year+1}', cycle=f'jun/{year} a jun/{year+1}',
        start=DATES[year], end=DATES[year+1], portfolio=portfolio, row_type='HOLDING',
        start_ticker=ticker, related_securities=';'.join(sorted(set(related))),
        start_weight_pct=100*left/nav0 if weight is None else 100*float(weight),
        exposure_return_pct=100*(right/left-1) if ret is None else ret,
        contribution_pp=100*(right-left)/nav0 if contribution is None else contribution,
        end_weight_before_review_pct=100*right/nav1, status=status or 'POSIÇÃO DO INÍCIO; eventos do livro herdado',
        largest_contributor='', start_index_component=left, end_index_component=right,
        start_index_total=nav0, end_index_total=nav1, position_source=source,
        start_phase='AFTER_REVIEW' if year > 2014 and portfolio != 'BH padrão' else 'INITIAL_OR_UNREBALANCED',
        end_phase='BEFORE_CLOSING_REVIEW', event_ids=';'.join(sorted(events)), limitation=LIMITATION)


def build():
    verify_frozen()
    annual = read(RESULT / 'annual_returns_pct.csv')
    statuses = {(r['portfolio'], r['start']): r['status'] for r in read(RESULT/'portfolio_status.csv')}
    rows, flows, transfers, endpoints = [], [], [], []
    established = read(OUT/'established_segment_positions.csv')
    established_events = {(r['year'], r['ticker']): r['events']
                          for r in gzread(OUT/'cache/established_segments.json.gz')}
    # The two already-attributed R03 cycles are imported, not replayed.
    for year in (2014, 2015):
        selected = [r for r in established if int(r['year']) == year]
        nav0 = math.fsum(float(r['index_start']) for r in selected)
        nav1 = math.fsum(float(r['index_end']) for r in selected)
        for r in selected:
            rows.append(base_row('R03 B2', year, r['ticker'], float(r['index_start']), float(r['index_end']),
                nav0, nav1, 'established_segment_positions.csv', weight=r['weight'],
                ret=r['return_pct'], contribution=r['contribution_pp'],
                events=[e['id'] for e in established_events[year, r['ticker']]], status='ATRIBUIÇÃO PRONTA REUTILIZADA'))
    initial = read(OUT/'b00s_initial_positions.csv')
    initial_contrib = read(OUT/'b00s_initial_contributions.csv')
    initial_events = gzread(OUT/'cache/b00s_initial_events.json.gz')
    for p in PORTFOLIOS[1:3]:
        for r in initial_contrib:
            a, b = [x for x in initial if x['ticker'] == r['ticker']]
            related = {e['successor'] for e in initial_events if e['ticker'] == r['ticker'] and e.get('successor')}
            owned = related | {r['ticker']}
            rows.append(base_row(p, 2014, r['ticker'], float(a['index_component']), float(b['index_component']),
                float(a['index_total']), float(b['index_total']), 'b00s_initial_contributions.csv;b00s_initial_positions.csv',
                weight=r['weight'], ret=r['return_pct'], contribution=r['contribution_pp'],
                related=related, events=[e['id'] for e in initial_events if e['ticker'] in owned],
                status='ATRIBUIÇÃO PRONTA REUTILIZADA; direitos incluídos no ciclo original'))
    # BH needs no event replay: the existing issuer attribution groups ITUB/XP in
    # the creation cycle. Once XP is held at the start, give it its own row.
    bh = read(OUT/'bh_june_positions.csv')
    bh_attribution = read(OUT/'bh_issuer_annual_pct.csv')
    bh_events = gzread(OUT/'cache/bh_owned_events.json.gz')
    for year in range(2014, 2026):
        left = [r for r in bh if r['date'] == DATES[year]]
        right = {r['ticker']: r for r in bh if r['date'] == DATES[year+1]}
        nav0, nav1 = float(left[0]['index_total']), float(next(iter(right.values()))['index_total'])
        for a in left:
            t = a['ticker']
            owned = {t, 'XPBR31'} if t == 'ITUB4' and year == 2021 else {t}
            b = math.fsum(float(right[u]['index_component']) for u in owned)
            prior = next((r for r in bh_attribution if int(r['year']) == year and r['original_issuer_ticker'] == t), None)
            reuse = prior if year <= 2021 or t not in ('ITUB4', 'XPBR31') else None
            ev = [e for e in bh_events if DATES[year] < e['ex_date'] <= DATES[year+1] and e['ticker'] in owned]
            related = {e['successor'] for e in ev if e.get('successor')} | (owned-{t})
            rows.append(base_row('BH padrão', year, t, float(a['index_component']), b, nav0, nav1,
                'bh_issuer_annual_pct.csv;bh_june_positions.csv', weight=a['weight'],
                ret=reuse['return_pct'] if reuse else None, contribution=reuse['contribution_pp'] if reuse else None,
                related=related, events=[e['id'] for e in ev],
                status='BH sem rebalanceamento; XP separado quando já detido no início' if year >= 2022 else
                       'ATRIBUIÇÃO PRONTA REUTILIZADA; descendente no ciclo pertence à origem'))
    quote, _ = prices()
    events = {e['id']: e for e in gzread(OUT/'cache/continuation_events.json.gz')}
    for p, stem in STEMS.items():
        positions = read(OUT/f'{stem}_positions.csv')
        ledger = read(OUT/f'{stem}_ledger.csv')
        reviews = read(OUT/f'{stem}_reviews.csv')
        for year in range(2016 if p == 'R03 B2' else 2015, 2026):
            start, end = DATES[year], DATES[year+1]
            left = [r for r in positions if r['date'] == start and r['phase'] == 'AFTER_REVIEW']
            right = [r for r in positions if r['date'] == end and r['phase'] == 'PERIOD_END']
            sleeves, f, moved, seen, related = continue_attribution(left, right, ledger, events, quote, start, end)
            prefix = dict(portfolio=p, closing_june=f'jun/{year+1}', start=start, end=end)
            flows.extend(prefix | r for r in f)
            transfers.extend(prefix | r for r in moved)
            nav0, nav1 = float(left[0]['index_total']), float(right[0]['index_total'])
            sold = {r['ticker'] for r in reviews if r['date'] == end and float(r['after']) == 0}
            for a in left:
                t = a['ticker']
                value = math.fsum(q*quote[u, end] for u, q in sleeves[t].items())
                kinds = sorted({events[i]['kind'] for i in seen[t]})
                status = '; '.join(kinds) or 'SEM EVENTO NO CICLO'
                if t in sold:
                    status += '; SAÍDA NA REVISÃO FINAL: contribui integralmente neste ciclo'
                if any(r['origin_ticker'] == t for r in moved):
                    status += '; resgate: principal e retorno posterior preservados na origem'
                rows.append(base_row(p, year, t, float(a['index_component']), value, nav0, nav1,
                    f'{stem}_positions.csv;{stem}_ledger.csv', weight=a['weight'], related=related[t], events=seen[t], status=status))
                endpoints.extend(prefix | dict(origin_ticker=t, end_ticker=u, index_units=q,
                    nominal_close=quote[u, end], index_component=q*quote[u, end]) for u, q in sorted(sleeves[t].items()))
    # Decimal residuals expose binary floating-point noise rather than altering
    # any security's economic return or the previously published annual series.
    final, summaries = [], []
    with localcontext() as ctx:
        ctx.prec = 50
        for year, published in zip(range(2014, 2026), annual):
            for p in PORTFOLIOS:
                group = sorted([r for r in rows if r['portfolio'] == p and r['start'] == DATES[year]], key=lambda r: r['start_ticker'])
                positive = sorted([r for r in group if Decimal(str(r['contribution_pp'])) > 0], key=lambda r: Decimal(str(r['contribution_pp'])), reverse=True)
                negative = sorted([r for r in group if Decimal(str(r['contribution_pp'])) < 0], key=lambda r: Decimal(str(r['contribution_pp'])))
                for sign, ranked in [('POSITIVA', positive), ('NEGATIVA', negative)]:
                    for rank, r in enumerate(ranked[:3], 1):
                        r['largest_contributor'] = f'{sign} {rank}'
                total = sum((Decimal(str(r['contribution_pp'])) for r in group), Decimal(0))
                target = Decimal(published[p]); residual = target-total
                if abs(residual) > Decimal('1e-9'):
                    raise ValueError(('Material attribution residual', p, year, residual))
                residual_row = {k: '' for k in group[0]}
                residual_row.update({k: group[0][k] for k in ('closing_june', 'cycle', 'start', 'end', 'portfolio')})
                residual_row.update(row_type='NUMERICAL_RESIDUAL', contribution_pp=str(residual),
                    status='Resíduo explícito de ponto flutuante; não é ação, retorno econômico ou provento',
                    position_source='annual_returns_pct.csv menos soma decimal das contribuições', limitation=LIMITATION)
                final.extend(group + [residual_row])
                summaries.append(dict(closing_june=f'jun/{year+1}', cycle=group[0]['cycle'], start=DATES[year], end=DATES[year+1],
                    portfolio=p, holdings=len(group), published_return_pct=published[p], holdings_contribution_pp=str(total),
                    numerical_residual_pp=str(residual), reconciled_contribution_pp=str(total+residual),
                    reconciliation_difference_pp=str(total+residual-target), IBOV_pct=published['IBOV'],
                    excess_vs_IBOV_pp=str(target-Decimal(published['IBOV'])),
                    largest_positive_ticker=positive[0]['start_ticker'] if positive else '',
                    largest_positive_contribution_pp=positive[0]['contribution_pp'] if positive else '',
                    largest_negative_ticker=negative[0]['start_ticker'] if negative else '',
                    largest_negative_contribution_pp=negative[0]['contribution_pp'] if negative else '',
                    inherited_return_status=statuses[p, DATES[year]], limitation=LIMITATION))
    return final, summaries, flows, transfers, endpoints


def main(output_dir=RESULT):
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, summaries, flows, transfers, endpoints = build()
    for name, data in [('annual_holdings_attribution', rows), ('annual_attribution_summary', summaries),
                       ('attribution_event_lineage', flows), ('attribution_redemption_transfers', transfers),
                       ('attribution_end_lineage', endpoints)]:
        write(output_dir/f'{name}.csv', data)
    from stage1_attribution_excel import workbook
    workbook(output_dir/'attribution_2014_2026.xlsx', rows, summaries, transfers)
    manifest = dict(baseline_commit='cb3db599da85b4ad8bece1d93f1ad583a91ad713',
        coordinator='https://github.com/tneves95/b3-pipeline-data-and-backtest-framework/pull/3#issuecomment-6066153641',
        frozen_files_verified=verify_frozen(), reconciliations=len(summaries),
        holding_rows=sum(r['row_type']=='HOLDING' for r in rows),
        max_abs_numerical_residual_pp=str(max(abs(Decimal(r['numerical_residual_pp'])) for r in summaries)),
        max_reconciliation_difference_pp='0', backtests_reexecuted=False,
        methodology='Opening physical security origins; conserved corporate descendants and redemption transfers; explicit numerical residual',
        implementation=[dict(path=p, sha256=sha(ROOT/p)) for p in [
            'scripts/stage1_attribution.py', 'scripts/stage1_attribution_excel.py',
            'tests/test_stage1_attribution.py', 'requirements-attribution.txt',
            'docs/checkpoint_attribution_2014_2026.md',
            'research/returns_2014_2026_inputs/attribution_frozen_inputs.json',
            'research/returns_2014_2026_inputs/coordinator_attribution_2026_10_08.json']],
        outputs=[dict(path=p.name, sha256=sha(p)) for p in sorted(output_dir.iterdir())
                 if p.name.startswith(('annual_holdings_attribution.', 'annual_attribution_summary.', 'attribution_'))
                 and p.name != 'attribution_manifest.json'])
    (output_dir/'attribution_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k != 'outputs'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=RESULT)
    main(parser.parse_args().output_dir)
