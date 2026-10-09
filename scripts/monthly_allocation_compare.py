"""Sensitivity: buy underweights versus naturally drifted weights, no rebalance sales.

Isolated from PR #6's frozen engine and result files. The natural-weight allocator
is injected solely for this run and restored even on failure.
"""
from __future__ import annotations

from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

import monthly_contributions as original
import monthly_corrected_simulate as engine
from monthly_policy_corrected import FAIL_REASON, maintenance_evidence
from monthly_tax_accounting import Fiscal

ROOT = original.ROOT
PARENT = ROOT / 'research/monthly_policy_corrected_2014_2026'
OUT = ROOT / 'research/monthly_allocation_comparison_2014_2026'
LEGACY = ROOT / 'research/monthly_tax_2014_2026'

MODES = {
    'GROSS': 'consolidated_policy_corrected.csv',
    'CG_ONLY': 'consolidated_tax_corrected.csv',
    'CG_PLUS_JCP_CERTIFIED_PARTIAL': 'consolidated_income_corrected.csv',
}


def read_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        raise ValueError('No records for ' + str(path))
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NaturalWeightAllocator:
    """Allocate all investible cash pro rata by pre-purchase current market value.

    Exceptional bootstrap for an eligible entrant with ZERO physical position:
    up to 1/N of that tranche is seeded for each buyable zero-weight entrant.
    Remainder is allocated proportional to existing eligible, priced positions.
    Thereafter the entrant competes on its *actual* market weight, never 1/N.
    If none of the incumbents is buyable, unallocated cash is retained.
    This applies to cash from monthly deposits, FAIL exits and compulsory
    corporate events, matching the base engine's deployment calendar.
    """

    def __init__(self):
        self.seed_value = 0.
        self.seed_events = 0
        self.allocations = 0
        self.retained_value = 0.

    def __call__(self, values, cash, buyable, nav, refs):
        if cash <= 1e-10:
            return {}, max(0., cash)
        eligible = sorted(set(buyable) & set(refs))
        zeros = [c for c in eligible if values.get(c, 0.) <= 1e-10]
        funded = [c for c in eligible if values.get(c, 0.) > 1e-10]
        n = len(refs)
        if n <= 0:
            return {}, cash
        alloc = {}
        if zeros:
            seed_each = cash / n
            for c in zeros:
                alloc[c] = seed_each
            self.seed_value += math.fsum(alloc.values())
            self.seed_events += 1
        remainder = max(0., cash - math.fsum(alloc.values()))
        existing = math.fsum(values[c] for c in funded)
        if existing > 0:
            for c in funded:
                alloc[c] = remainder * values[c] / existing
        elif len(zeros) == n:
            # All positions are newly eligible and unfunded; neutral initial split.
            for c in zeros:
                alloc[c] = cash / n
        else:
            self.retained_value += remainder
        if alloc:
            spent = math.fsum(alloc.values())
            # Keep exact available-cash conservation, including floating point.
            last = sorted(alloc)[-1]
            alloc[last] += min(cash, spent) - math.fsum(alloc.values())
            if spent > cash + 1e-8:
                raise AssertionError(('overspend', spent, cash))
        self.allocations += 1
        spent = math.fsum(alloc.values())
        return alloc, max(0., cash - spent)


def unit_test_policy():
    a = NaturalWeightAllocator()
    r, left = a({'a': 30, 'b': 70}, 1000, {'a', 'b'}, 100, {'a': .5, 'b': .5})
    assert math.isclose(r['a'], 300.) and math.isclose(r['b'], 700.) and left < 1e-8
    r, left = a({'a': 100, 'b': 300, 'new': 0}, 900,
                {'a', 'b', 'new'}, 400, {'a': 1/3, 'b': 1/3, 'new': 1/3})
    assert math.isclose(r['new'], 300.) and math.isclose(r['a'], 150.)
    assert math.isclose(r['b'], 450.) and left < 1e-8
    r, left = a({'a': 100, 'b': 300, 'new': 0}, 900,
                {'a', 'b'}, 400, {'a': 1/3, 'b': 1/3, 'new': 1/3})
    assert 'new' not in r and math.isclose(r['a'], 225.) and math.isclose(r['b'], 675.)
    r, left = a({'a': 0, 'b': 0}, 100, {'a', 'b'}, 100, {'a': .5, 'b': .5})
    assert math.isclose(r['a'], 50.) and math.isclose(r['b'], 50.) and left < 1e-8
    r, left = a({'a': 0}, 0, {'a'}, 100, {'a': 1.})
    assert not r and not left


def main():
    unit_test_policy()
    OUT.mkdir(parents=True, exist_ok=True)
    before = {}
    for label, name in MODES.items():
        before[label] = {r['portfolio']: r for r in read_csv(PARENT / name)}
    # Evidence, quotes and selection are exactly those frozen for PR #6.
    evidence = maintenance_evidence()
    ev = json.loads((LEGACY / 'inputs/event_tax_evidence_stage2.json').read_text())
    quotes, _ = original.load_quotes()
    events = original.events()
    compositions = original.frozen_compositions()
    sessions = [r['date'] for r in original.read(original.STUDY/'inputs/ibov_daily.csv')]
    meta = original.identities()

    parent_annual = {}
    parent_month = {}
    for mode in MODES:
        parent_annual[mode] = {(r['portfolio'], r['date']):r for r in
                                read_csv(PARENT / mode / 'annual.csv')}
        parent_month[mode] = {(r['portfolio'], r['date']):r for r in
                               read_csv(PARENT / mode / 'wealth.csv')
                               if r['phase']=='MONTH_END'}

    old_allocator = engine.allocate_cash
    all_rows, annually, monthly = [], [], []
    try:
        for mode in MODES:
            for portfolio in original.PORTFOLIOS:
                allocator = NaturalWeightAllocator()
                engine.allocate_cash = allocator
                fiscal = Fiscal(portfolio, ev, sessions, enabled=mode!='GROSS',
                    income_mode='CERTIFIED_PARTIAL'
                    if mode=='CG_PLUS_JCP_CERTIFIED_PARTIAL' else 'NONE')
                run = engine.simulate(portfolio, quote=quotes, byday=events,
                    compositions=compositions, evidence=evidence, fiscal=fiscal)
                summary = run['summary']
                base = before[mode][portfolio]
                assert summary['external_contributions'] == 144
                assert math.isclose(summary['external_capital'], 460000, abs_tol=1e-6)
                assert all(t['reason']==FAIL_REASON and t.get('maintenance_status')=='FAIL'
                           for t in run['trades'] if t['side']=='SELL')
                assert (portfolio not in {'BH padrão','BESST-10 BH'}
                        or not any(t['side']=='SELL' for t in run['trades']))
                assert all(t['side']!='SELL' or t['date'][5:7]=='06'
                           for t in run['trades'])
                assert summary['voluntary_sales']==int(base['voluntary_sales'])

                byissuer=defaultdict(float)
                for c, units in run['book'].items():
                    for ticker, qty in units.items():
                        issuer = 'XP_SPINOFF' if ticker == 'XPBR31' else meta.get(
                            ticker, {}).get('cnpj', c)
                        byissuer[issuer] += qty * quotes[ticker, original.END]
                natural_issuer_max = max(byissuer.values())/summary['final_wealth']
                natural_hhi = math.fsum((v/summary['final_wealth'])**2
                                         for v in byissuer.values())
                # Compare to the exact published output for the same fiscal mode.
                wealth_base = float(base['final_wealth'])
                xirr_base = float(base['xirr_pct'])
                row=dict(mode=mode,portfolio=portfolio,
                    deficits_wealth=wealth_base,natural_wealth=summary['final_wealth'],
                    natural_minus_deficits_R=summary['final_wealth']-wealth_base,
                    natural_minus_deficits_pct=100*(summary['final_wealth']/wealth_base-1),
                    deficits_xirr_pct=xirr_base,natural_xirr_pct=summary['xirr_pct'],
                    natural_minus_deficits_xirr_pp=summary['xirr_pct']-xirr_base,
                    deficits_max_issuer_weight_pct=100*float(base['maximum_issuer_weight']),
                    natural_max_issuer_weight_pct=100*natural_issuer_max,
                    deficits_issuer_hhi=float(base['issuer_hhi']),
                    natural_issuer_hhi=natural_hhi,
                    deficits_tax_paid=float(base['tax_paid']),
                    natural_tax_paid=summary['tax_paid'],
                    deficits_income_withheld=float(base['income_withheld']),
                    natural_income_withheld=summary['income_withheld'],
                    deficits_cash=float(base['cash']), natural_cash=summary['cash'],
                    voluntary_sales=summary['voluntary_sales'],
                    natural_unfunded_entry_seed_R=allocator.seed_value,
                    natural_seed_operations=allocator.seed_events,
                    natural_cash_retained_on_unbuyable=allocator.retained_value,
                    capital_applied=summary['external_capital'],
                    qualification='CONDITIONAL_FROZEN_PIT_PARTIAL_INCOME_COVERAGE')
                all_rows.append(row)
                for annual in run['annual']:
                    b=parent_annual[mode].get((portfolio,annual['date']))
                    if b:
                        annually.append(dict(mode=mode,portfolio=portfolio,date=annual['date'],
                            deficits_nav=b['nav'],natural_nav=annual['nav'],
                            difference_R=(float(annual['nav'])-float(b['nav']))
                            if annual['nav'] is not None and b['nav'] else '',
                            natural_annual_twr_pct=annual['twr_pct'],
                            deficits_annual_twr_pct=b['twr_pct']))
                for current in run['wealth']:
                    if current['phase'] != 'MONTH_END': continue
                    b=parent_month[mode].get((portfolio,current['date']))
                    if b:
                        n=current['nav']
                        d=float(b['nav']) if b['nav'] else None
                        monthly.append(dict(mode=mode,portfolio=portfolio,date=current['date'],
                            deficits_nav=d if d is not None else '',
                            natural_nav=n if n is not None else '',
                            natural_minus_deficits_R=n-d if n is not None and d is not None else '',
                            natural_max_lineage=current['maximum_lineage_weight']))
                print('COMPARE', mode, portfolio,
                    f"deficits={wealth_base:.2f}",f"natural={summary['final_wealth']:.2f}",
                    f"delta={row['natural_minus_deficits_R']:.2f}",
                    f"TIR_delta_pp={row['natural_minus_deficits_xirr_pp']:.6f}",
                    f"max_issuer_natural={100*natural_issuer_max:.3f}%",
                    f"sales={summary['voluntary_sales']}", flush=True)
    finally:
        engine.allocate_cash = old_allocator

    assert len(all_rows) == 15 and len(annually) >= 170 and len(monthly) >= 1900
    write_csv(OUT/'allocation_comparison.csv', all_rows)
    write_csv(OUT/'annual_comparison.csv', annually)
    write_csv(OUT/'monthly_comparison.csv', monthly)
    checks = dict(
        policy='Natural = current market weights of eligible invested lineages, prior to cash; zero entrants funded with up to 1/N of available tranche',
        comparator='Deficits to 1/N or qualified winner 2/N; PR6 frozen corrected main scenario',
        no_rebalance_sales='Mandatory: voluntary sells only verified FAIL in June',
        initial=100000, months=144, deposit=2500, total_external=460000,
        seed_rule='For an eligible zero position, allocate 1/N of each buyable cash tranche; then proportionally to positive weights. No incumbent liquidation.',
        all_free_cash='Monthly deposits, compulsory redemptions, and June proceeds from real FAIL exits treated with same alternative purchase rule',
        fixed_selection='PR4 B2 candidates and FAIL evidence; all historic PIT evidence unchanged',
        gross_already_accepted_as_frozen='Preserved original PR6 outputs; experimental file does not replace these',
        modes=list(MODES), rows=len(all_rows), annual_rows=len(annually),
        monthly_rows=len(monthly),
        baseline_sha256={mode:sha256(PARENT/name) for mode,name in MODES.items()},
        limitations=['BESST-10 BH conditional NET/TIMP3',
                    'BBDC4 2014 eligibility documentary uncertainty',
                    'Fractional theoretical purchases, transaction costs excluded',
                    'Taxation of ambiguous provents not certified',
                    'Two missing exact TWR flow-date valuations for V0/VVAL plus 2014-07-01'],
    )
    (OUT/'methodology.json').write_text(
        json.dumps(checks, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    # Last three lines are short, machine-readable tables for GitHub Actions logs.
    for mode in MODES:
        print('SUMMARY',mode)
        for r in sorted((x for x in all_rows if x['mode']==mode),
                        key=lambda x:-x['natural_wealth']):
            print(r['portfolio'],
                'deficit',f"{r['deficits_wealth']:.2f}",
                'natural',f"{r['natural_wealth']:.2f}",
                'R',f"{r['natural_minus_deficits_R']:+.2f}",
                'pp',f"{r['natural_minus_deficits_xirr_pp']:+.6f}",
                'max_nat',f"{r['natural_max_issuer_weight_pct']:.3f}",
                flush=True)


if __name__ == '__main__':
    main()
