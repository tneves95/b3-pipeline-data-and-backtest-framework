"""Purchase-only references; frozen maintenance evidence, never price-driven exits."""
import math
import statistics
from monthly_contributions import ROOT, identities, read

PROOF = ROOT/'research/b00s_four_variants_2014_2026/results/review_ledger.csv'
FAIL_REASON = 'CONFIRMED_MAINTENANCE_FAIL'
BH = {'BH padrão', 'BESST-10 BH'}


def maintenance_evidence():
    meta = identities(); result = {}
    for line, r in enumerate(read(PROOF), 2):
        if r['variant'] not in {'V0', 'V10', 'VVAL'}: continue
        c = meta[r['ticker']]['cnpj']; key = r['variant'], int(r['year']), c
        # FAIL_EXIT is the frozen decision, not absence from a buying list.
        if r['base_status'] == 'FAIL' and r['reason'] == 'FAIL_EXIT':
            result[key] = dict(status='FAIL', reason=FAIL_REASON, source=str(PROOF.relative_to(ROOT)),
                               source_line=line, source_ticker=r['ticker'], source_reason=r['reason'])
    return result


def review_members(portfolio, year, buyers, candidates, evidence):
    if portfolio in BH: return buyers.copy(), {}, set()
    exits = {c:evidence[portfolio,year,c] for c in buyers
             if (portfolio,year,c) in evidence and evidence[portfolio,year,c]['status']=='FAIL'
             and evidence[portfolio,year,c]['reason']==FAIL_REASON}
    desired = {c:t for c,t in buyers.items() if c not in exits}
    entries = set(candidates)-set(buyers)
    desired.update({c:candidates[c] for c in entries})
    return desired, exits, entries


def references(buyers, winners):
    n = len(buyers)
    return {c:(2. if n>15 and c in winners else 1.)/n for c in buyers}


def recognize_winners(buyers, winners, values, nav, trailing):
    kept = set(winners)&set(buyers); n = len(buyers)
    observed = [v for c,v in trailing.items() if c in buyers]
    if n>15 and observed:
        median = statistics.median(observed)
        kept.update(c for c in buyers if values.get(c,0)/nav>=1.5/n
                    and c in trailing and trailing[c]>median)
    return kept


def allocate_cash(values, cash, buyable, nav, refs):
    deficits = {c:max(0.,nav*refs[c]-values.get(c,0.)) for c in sorted(buyable)}
    deficits = {c:v for c,v in deficits.items() if v>1e-10}
    total = math.fsum(deficits.values()); spend = min(max(cash,0.),total)
    if not total or not spend: return {}, cash
    result = {c:v*spend/total for c,v in deficits.items()}
    last = sorted(result)[-1]; result[last] = spend-math.fsum(v for c,v in result.items() if c!=last)
    return result, cash-spend
