"""Frozen PR4 entry sizing after June2014; no price or future return inputs."""
import math

SECTORS=frozenset(['Bancos','Energia','Saneamento','Seguros','Telecom'])
SECTOR_REFERENCE=.20

def reference_entries(holdings,status,qualified,metadata):
    """Count unique economic lineages, including retained ND incumbents.

    Physical rights/successors share their already accepted lineage metadata.
    Their values remain in NAV; counting them never creates another entry slot.
    The base-status exit decision remains the inherited physical-position rule.
    """
    survivors={t for t in holdings if status.get(t)!='FAIL'}
    retained={metadata[t]['cnpj'] for t in survivors}
    failed_lineages={metadata[t]['cnpj'] for t in holdings if status.get(t)=='FAIL'}
    occupied={s:set() for s in SECTORS}
    for t in survivors|set(qualified):
        m=metadata[t]
        if m['sector'] not in SECTORS:raise ValueError('Unknown BESST sector')
        occupied[m['sector']].add(m['cnpj'])
    entries={};seen=set()
    for t in sorted(qualified):
        m=metadata[t]
        if m['cnpj'] in retained:continue
        if m['cnpj'] in failed_lineages:raise ValueError('Conflicting FAIL and PASS in the same economic lineage')
        if t in holdings:raise ValueError('A FAIL holding cannot also be qualified for entry')
        if status.get(t)!='PASS':raise ValueError('Only base PASS may enter')
        if m['cnpj'] in seen:raise ValueError('Two classes cannot create two entry slots')
        seen.add(m['cnpj'])
        entries[t]=SECTOR_REFERENCE/len(occupied[m['sector']])
    if survivors and math.fsum(entries.values())>=1:
        raise ValueError('Entry requests cannot exhaust retained NAV')
    return entries

def renew_reference_entries(holdings,status,entries):
    """The inherited B2 funding order with partial, unnormalised requests.

    FAIL releases fund first. Surplus releases go to entries in request ratios.
    A shortfall reduces every surviving physical exposure in equal proportion.
    No entries means unchanged survivors unless FAIL proceeds require allocation.
    """
    if not holdings or any(not math.isfinite(v) or v<=0 for v in holdings.values()):
        raise ValueError('Positive finite index holdings required')
    if any(t in holdings or status.get(t)!='PASS' or not math.isfinite(w) or w<=0 for t,w in entries.items()):
        raise ValueError('Entries must be new base PASS names with positive finite requests')
    nav=math.fsum(holdings.values());exits={t for t in holdings if status.get(t)=='FAIL'}
    survivors={t:v for t,v in holdings.items() if t not in exits}
    released=math.fsum(holdings[t] for t in exits);survnav=math.fsum(survivors.values());after=survivors.copy()
    if entries:
        total=math.fsum(entries.values())
        if total>1 or survivors and total>=1:raise ValueError('Entry requests cannot exhaust retained NAV')
        allocated=max(released,nav*total);sale=allocated-released
        if sale:
            if not survnav:raise ValueError('No surviving allocation to finance entries')
            after={t:v*(1-sale/survnav) for t,v in survivors.items()}
        after.update({t:allocated*w/total for t,w in entries.items()})
    elif released:
        if not survivors:raise ValueError('All holdings FAIL without an eligible destination')
        after={t:v*nav/survnav for t,v in survivors.items()}
    if any(after[t]<=0 for t in survivors):raise ValueError('A retained holding was liquidated')
    if not math.isclose(math.fsum(after.values()),nav,rel_tol=1e-12,abs_tol=1e-14):raise ValueError('Review must conserve NAV')
    ledger=[dict(ticker=t,before=holdings.get(t,0.),after=after.get(t,0.),change=after.get(t,0.)-holdings.get(t,0.),
                 reason='FAIL_EXIT' if t in exits else 'PASS_ENTRY' if t in entries else
                 'ENTRY_FINANCING' if after[t]<holdings[t] else 'EXIT_REDISTRIBUTION' if after[t]>holdings[t] else 'PRESERVED')
            for t in sorted(holdings.keys()|after.keys())]
    return after,ledger
