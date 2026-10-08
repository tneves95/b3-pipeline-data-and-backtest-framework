"""Continuous, dimensionless portfolio accounting for the percentage study."""
from __future__ import annotations
import math


def renew_b2(holdings, status, targets):
    """Selective renewal in index units, with no annual reset.

    New names request their philosophy's target fraction of current NAV.
    FAIL positions fund these entries first; only a shortfall reduces all
    survivors by the same fraction. Surplus exit proceeds go to the entrants
    in their relative target proportions. With exits but no entrants, the
    compulsory redistribution is proportional to surviving holdings.
    INDETERMINATE or absent status never authorizes an exit.
    """
    if not holdings or any(not math.isfinite(v) or v <= 0 for v in holdings.values()):
        raise ValueError('Positive finite index holdings required')
    if any(not math.isfinite(v) or v <= 0 for v in targets.values()):
        raise ValueError('Positive finite target weights required')
    if targets and not math.isclose(math.fsum(targets.values()), 1, abs_tol=1e-12):
        raise ValueError('Target weights must sum to one')
    if any(status.get(t) != 'PASS' for t in targets):
        raise ValueError('Only PASS names may be purchased as entrants')
    nav = math.fsum(holdings.values())
    exits = {t for t in holdings if status.get(t) == 'FAIL'}
    survivors = {t: v for t, v in holdings.items() if t not in exits}
    entries = {t: w for t, w in targets.items() if t not in holdings}
    released = math.fsum(holdings[t] for t in exits)
    old_survivor_nav = math.fsum(survivors.values())
    after = survivors.copy()
    if entries:
        requested = nav * math.fsum(entries.values())
        allocated = max(released, requested)
        if allocated > nav + 1e-12:
            raise ValueError('Unfunded entry weights')
        sale = allocated - released
        if sale:
            if not old_survivor_nav: raise ValueError('No surviving allocation to finance entries')
            after = {t: v * (1 - sale / old_survivor_nav) for t, v in survivors.items()}
        total_entry_weight = math.fsum(entries.values())
        after.update({t: allocated * w / total_entry_weight for t, w in entries.items()})
    elif released:
        if not survivors: raise ValueError('All holdings FAIL without an eligible destination')
        after = {t: v * nav / old_survivor_nav for t, v in survivors.items()}
    if not math.isclose(math.fsum(after.values()), nav, rel_tol=1e-12, abs_tol=1e-14):
        raise ValueError('Review must conserve the index level')
    ledger = [dict(ticker=t, before=holdings.get(t, 0.), after=after.get(t, 0.),
                   change=after.get(t, 0.)-holdings.get(t, 0.),
                   reason='FAIL_EXIT' if t in exits else 'PASS_ENTRY' if t in entries else
                   'ENTRY_FINANCING' if after[t] < holdings[t] else
                   'EXIT_REDISTRIBUTION' if after[t] > holdings[t] else 'PRESERVED')
              for t in sorted(holdings.keys() | after.keys())]
    return after, ledger


def advance(holdings, factors):
    if holdings.keys() != factors.keys():
        raise ValueError('Every held right needs exactly one return factor')
    if any(not math.isfinite(f) or f < 0 for f in factors.values()):
        raise ValueError('Invalid factor')
    return {t: v * factors[t] for t, v in holdings.items()}
