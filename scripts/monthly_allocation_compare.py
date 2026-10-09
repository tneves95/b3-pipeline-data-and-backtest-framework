"""Sensitivity: buy underweights versus naturally drifted weights, with winners shielded.

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
from monthly_policy_corrected import (FAIL_REASON, maintenance_evidence,
    review_members as base_review_members,
    recognize_winners as base_recognize_winners)
from monthly_tax_accounting import Fiscal

original_allocator = engine.allocate_cash

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




class WinnerShield:
    """Keep prior objectively flagged winners forever; FAIL suspends NEW purchases.

    A flagged winner is still owned after a later documented FAIL, but ceases
    to be among active buy candidates. If eligibility later returns, its
    winner marker is restored. This stronger hold rule is applied in BOTH
    contribution strategies, never retroactively to the frozen PR6 files.
    """

    def __init__(self):
        self.winners = set()
        self.first_recognized = {}
        self.prevented_sales = []
        self.current_year = 2014

    def review_members(self, portfolio, year, buyers, candidates, evidence):
        self.current_year = year
        desired, exits, entries = base_review_members(
            portfolio, year, buyers, candidates, evidence)
        for c in sorted(set(exits) & self.winners):
            self.prevented_sales.append(dict(portfolio=portfolio,year=year,
                lineage=c,ticker=exits[c].get('source_ticker',''),
                proof=exits[c].get('source',''),
                rule='WINNER_HOLD_STOP_NEW_BUYS_ON_FAIL'))
            # Important: DO NOT restore 'c' to desired. It is held in the book
            # and NAV, while new purchases are suspended on documented FAIL.
            del exits[c]
        return desired, exits, entries

    def recognize_winners(self, buyers, winners, values, nav, trailing):
        eligible_prior=(set(winners)|self.winners) & set(buyers)
        recognized=base_recognize_winners(
            buyers, eligible_prior, values, nav, trailing)
        for c in recognized:
            self.winners.add(c)
            self.first_recognized.setdefault(c,self.current_year)
        return recognized

    def check_sales(self, trades):
        for t in trades:
            if t['side'] != 'SELL':
                continue
            assert t['reason'] == FAIL_REASON
            assert t.get('maintenance_status') == 'FAIL'
            assert t['date'][5:7] == '06'
            start=self.first_recognized.get(t['lineage'])
            if start is not None:
                assert int(t['date'][:4])<=start, (
                    'SALE OF PREVIOUSLY RECOGNIZED WINNER', t, start)

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



def unit_test_winner_shield():
    a='winner'; b='ordinary'
    shield=WinnerShield()
    shield.winners.add(a)
    shield.first_recognized[a]=2016
    cand={}
    ev={('V0', 2024, a):dict(status='FAIL',reason=FAIL_REASON,source='synthetic',
            source_line=1,source_ticker='WIN3'),
        ('V0', 2024, b):dict(status='FAIL',reason=FAIL_REASON,source='synthetic',
            source_line=2,source_ticker='LOSS3')}
    desired, exits, entries=shield.review_members('V0',2024,
        {a:'WIN3',b:'LOSS3'},cand,ev)
    assert a not in exits and b in exits and a not in desired
    assert len(shield.prevented_sales)==1
    # Former winner is reactivated if again eligible, marker must persist.
    assert a in shield.recognize_winners(
        {a:'WIN3'},set(),{a:10},100,{a:0.})  # restoration from history


def simulate_mode(portfolio, mode, policy, quote, evday, comps, evidence, tax_ev, sessions):
    shield=WinnerShield()
    allocator=NaturalWeightAllocator() if policy=='NATURAL' else original_allocator
    former=(engine.allocate_cash, engine.review_members, engine.recognize_winners)
    try:
        engine.allocate_cash=allocator
        engine.review_members=shield.review_members
        engine.recognize_winners=shield.recognize_winners
        fiscal=Fiscal(portfolio, tax_ev, sessions, enabled=mode!='GROSS',
                      income_mode=('CERTIFIED_PARTIAL'
                                   if mode=='CG_PLUS_JCP_CERTIFIED_PARTIAL' else 'NONE'))
        run=engine.simulate(portfolio,quote=quote,byday=evday,
                            compositions=comps,evidence=evidence,fiscal=fiscal)
    finally:
        engine.allocate_cash, engine.review_members, engine.recognize_winners=former
    shield.check_sales(run['trades'])
    assert run['summary']['external_contributions']==144
    assert math.isclose(run['summary']['external_capital'],460000.,abs_tol=1e-6)
    assert portfolio not in {'BH padrão','BESST-10 BH'} or not any(
        t['side']=='SELL' for t in run['trades'])
    return run, shield, allocator


def issuer_concentration(book,quote,meta,nav):
    issuer=defaultdict(float)
    for c, units in book.items():
        for ticker,qty in units.items():
            ident='XP_SPINOFF' if ticker=='XPBR31' else meta.get(ticker,{}).get('cnpj',c)
            issuer[ident]+=qty*quote[ticker,original.END]
    weights=[v/nav for v in issuer.values()]
    return 100*max(weights),math.fsum(x*x for x in weights)


def main():
    unit_test_policy()
    unit_test_winner_shield()
    OUT.mkdir(parents=True,exist_ok=True)
    baseline={mode:{r['portfolio']:r for r in read_csv(PARENT/name)}
              for mode,name in MODES.items()}
    evidence=maintenance_evidence()
    tax_ev=json.loads((LEGACY/'inputs/event_tax_evidence_stage2.json').read_text())
    quote,_=original.load_quotes()
    evday=original.events()
    comps=original.frozen_compositions()
    sessions=[r['date'] for r in original.read(original.STUDY/'inputs/ibov_daily.csv')]
    meta=original.identities()

    parent_annual={}
    parent_month={}
    for mode in MODES:
        parent_annual[mode]={(r['portfolio'],r['date']):r
                 for r in read_csv(PARENT/mode/'annual.csv')}
        parent_month[mode]={(r['portfolio'],r['date']):r
                 for r in read_csv(PARENT/mode/'wealth.csv') if r['phase']=='MONTH_END'}

    all_rows, annually, monthly, sale_shields, final_positions=[],[],[],[],[]
    for mode in MODES:
        for portfolio in original.PORTFOLIOS:
            runs={}
            for policy in ('DEFICITS_PROTECTED','NATURAL'):
                run, shield, allocator=simulate_mode(
                    portfolio,mode,policy,quote,evday,comps,evidence,tax_ev,sessions)
                runs[policy]=(run,shield,allocator)
                for prevented in shield.prevented_sales:
                    sale_shields.append(dict(mode=mode,policy=policy,**prevented))
            deficits,dshield,_=runs['DEFICITS_PROTECTED']
            natural,nshield,nalloc=runs['NATURAL']
            ds=deficits['summary']; ns=natural['summary']
            past=baseline[mode][portfolio]
            dm,dh=issuer_concentration(deficits['book'],quote,meta,ds['final_wealth'])
            nm,nh=issuer_concentration(natural['book'],quote,meta,ns['final_wealth'])
            row=dict(mode=mode,portfolio=portfolio,
                pr6_frozen_wealth=float(past['final_wealth']),
                protected_deficits_wealth=ds['final_wealth'],
                protected_natural_wealth=ns['final_wealth'],
                protected_vs_frozen_deficits_R=ds['final_wealth']-float(past['final_wealth']),
                natural_minus_deficits_R=ns['final_wealth']-ds['final_wealth'],
                natural_minus_deficits_pct=100*(ns['final_wealth']/ds['final_wealth']-1),
                pr6_frozen_xirr_pct=float(past['xirr_pct']),
                protected_deficits_xirr_pct=ds['xirr_pct'],
                protected_natural_xirr_pct=ns['xirr_pct'],
                natural_minus_deficits_xirr_pp=ns['xirr_pct']-ds['xirr_pct'],
                protected_deficits_max_issuer_pct=dm,
                protected_natural_max_issuer_pct=nm,
                protected_deficits_issuer_hhi=dh,protected_natural_issuer_hhi=nh,
                protected_deficits_CG_paid=ds['tax_paid'],
                protected_natural_CG_paid=ns['tax_paid'],
                protected_deficits_income_withheld=ds['income_withheld'],
                protected_natural_income_withheld=ns['income_withheld'],
                protected_deficits_cash=ds['cash'],protected_natural_cash=ns['cash'],
                frozen_PR6_sales=int(past['voluntary_sales']),
                protected_deficits_sales=ds['voluntary_sales'],
                protected_natural_sales=ns['voluntary_sales'],
                deficits_winner_sales_blocked=len(dshield.prevented_sales),
                natural_winner_sales_blocked=len(nshield.prevented_sales),
                natural_entrant_seed_R=nalloc.seed_value,
                natural_entrant_seed_events=nalloc.seed_events,
                natural_unbuyable_cash_R=nalloc.retained_value,
                total_external=ds['external_capital'],
                qualification='CONDITIONAL_FROZEN_PIT_WINNERS_SHIELDED_TAX_PARTIAL')
            all_rows.append(row)
            for policy,(run,shield,_) in runs.items():
                s=run['summary']
                for c, units in run['book'].items():
                    for ticker,q in units.items():
                        final_positions.append(dict(mode=mode,policy=policy,portfolio=portfolio,
                            lineage=c,ticker=ticker,quantity=q,close=quote[ticker,original.END],
                            market_value=q*quote[ticker,original.END],
                            is_still_buyable=c in {x['lineage'] for x in run['positions']
                                if x['date']==original.END and x['monthly_buy_target']}))
            # Same dates, holdings and purchases policy only differs.
            da={r['date']:r for r in deficits['annual']}
            na={r['date']:r for r in natural['annual']}
            for d in sorted(set(da)&set(na)):
                a,b=da[d],na[d]
                prior=parent_annual[mode].get((portfolio,d))
                annually.append(dict(mode=mode,portfolio=portfolio,date=d,
                    frozen_PR6_nav=prior['nav'] if prior else '',
                    protected_deficits_nav=a['nav'],protected_natural_nav=b['nav'],
                    natural_minus_deficits_R=float(b['nav'])-float(a['nav']),
                    deficits_annual_twr_pct=a['twr_pct'],
                    natural_annual_twr_pct=b['twr_pct']))
            dmth={(r['date']):r for r in deficits['wealth'] if r['phase']=='MONTH_END'}
            nmth={(r['date']):r for r in natural['wealth'] if r['phase']=='MONTH_END'}
            for d in sorted(set(dmth)&set(nmth)):
                a,b=dmth[d],nmth[d]
                prior=parent_month[mode].get((portfolio,d))
                p=float(prior['nav']) if prior and prior['nav'] else ''
                va=a['nav'];vb=b['nav']
                monthly.append(dict(mode=mode,portfolio=portfolio,date=d,
                    frozen_PR6_nav=p,
                    protected_deficits_nav=va if va is not None else '',
                    protected_natural_nav=vb if vb is not None else '',
                    natural_minus_deficits_R=vb-va if va is not None and vb is not None else '',
                    deficits_max_lineage=a['maximum_lineage_weight'],
                    natural_max_lineage=b['maximum_lineage_weight']))
            print('COMPARE',mode,portfolio,
                f"DEFICIT {ds['final_wealth']:.2f}",
                f"NATURAL {ns['final_wealth']:.2f}",
                f"DELTA {row['natural_minus_deficits_R']:+.2f}",
                f"TIR_DELTA_PP {row['natural_minus_deficits_xirr_pp']:+.6f}",
                f"WINNERS_BLOCKED {len(dshield.prevented_sales)}/{len(nshield.prevented_sales)}",
                f"SALES {ds['voluntary_sales']}/{ns['voluntary_sales']}",flush=True)

    assert len(all_rows)==15
    assert len(annually)>=150
    assert len(monthly)>=1700
    write_csv(OUT/'allocation_comparison.csv',all_rows)
    write_csv(OUT/'annual_comparison.csv',annually)
    write_csv(OUT/'monthly_comparison.csv',monthly)
    write_csv(OUT/'winner_sales_prevented.csv',sale_shields if sale_shields else
        [dict(mode='',policy='',portfolio='',year='',lineage='',ticker='',proof='',rule='NONE')])
    write_csv(OUT/'final_positions.csv',final_positions)
    metadata=dict(
        modes=list(MODES),
        strategies=['DEFICITS_PROTECTED','NATURAL'],
        policy='Both methods protect previously recognized winners forever, even if future FAIL. New purchases suspended on FAIL.',
        voluntary_sales='Only nonwinner CONFIRMED_MAINTENANCE_FAIL at June reviews.',
        winner_marker='Previously recognized June winners persist after removal from buying universe and after dilution.',
        deficit_rule='PR6 1/N and qualified winner 2/N, waterfill on deficits; NEVER sell by weight.',
        natural_rule='Allocate all available cash proportionally to actually invested eligible market values. For zero-weight entrants, seed up to cash/N per tranche, thereafter follow natural market weight.',
        entry_without_sale='Never sell to finance admission; seed uses only available cash.',
        corporate_event_rule='Same frozen tax/economic treatment in both.',
        share_fractions='Theoretical, costs excluded.',
        capital_initial=100000,capital_monthly=2500,months=144,
        rows=len(all_rows),annual_rows=len(annually),monthly_rows=len(monthly),
        baseline_sha256={mode:sha256(PARENT/name) for mode,name in MODES.items()},
        caveats=['Earlier PR6 results intentionally unchanged and NOT the correct comparator once former winner retention is required.',
            'Not every appreciated share qualifies objectively as winner; criterion frozen.',
            'BESST-10 BH remains conditional for NET/TIMP3.',
            'Historical tax and provent documentation partial, BBDC4/2014 eligibility unresolved.',
            'TWR is ND for known missing flow-date quotations.'])
    (OUT/'methodology.json').write_text(
        json.dumps(metadata,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    for mode in MODES:
        print('SUMMARY',mode)
        for r in sorted((v for v in all_rows if v['mode']==mode),
                        key=lambda r:-r['protected_deficits_wealth']):
            print(r['portfolio'],
                'deficit',f"{r['protected_deficits_wealth']:.2f}",
                'natural',f"{r['protected_natural_wealth']:.2f}",
                'R',f"{r['natural_minus_deficits_R']:+.2f}",
                'pp',f"{r['natural_minus_deficits_xirr_pp']:+.6f}",
                'maxD',f"{r['protected_deficits_max_issuer_pct']:.3f}",
                'maxN',f"{r['protected_natural_max_issuer_pct']:.3f}",
                'keep',r['deficits_winner_sales_blocked'],
                '/',r['natural_winner_sales_blocked'],flush=True)


if __name__=='__main__':
    main()
