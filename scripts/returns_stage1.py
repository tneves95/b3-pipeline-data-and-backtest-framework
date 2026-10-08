#!/usr/bin/env python3
"""Percentage-only checkpoint; never bridge a missing selection or return with zero."""
import csv
import hashlib
import json
import math
import statistics
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "research/returns_2014_2026_inputs"
OUTPUT = ROOT / "research/returns_2014_2026_results"
LEGACY = ROOT / "research/graham_v6_comparison"
NAMES = ("R03 B2", "B00S B2", "B00S BH+entradas", "BH padrão", "IBOV")


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def validate_return(value):
    if value is not None and (not math.isfinite(value) or value < -1):
        raise ValueError("Return must be finite and at least -100%, or explicitly missing")


def chain(returns):
    """Decimals in/out. Unknown intervals invalidate all later accumulation."""
    factor = 1.0
    result = []
    for r in returns:
        validate_return(r)
        factor = None if factor is None or r is None else factor * (1 + r)
        result.append(None if factor is None else factor - 1)
    return result


def june_close(payload, year):
    observations = []
    for row in payload["results"]:
        value = row.get("rateValue6")
        if value is None or value == "":
            continue
        day = date(year, 6, int(row["day"]))
        level = float(str(value).replace(".", "").replace(",", "."))
        if not math.isfinite(level) or level <= 0:
            raise ValueError("Invalid official IBOV level")
        observations.append((day.isoformat(), level))
    if not observations or len({d for d, _ in observations}) != len(observations):
        raise ValueError("Empty or duplicate June observations")
    return max(observations)


def summary(returns, benchmark, start, end, is_benchmark=False):
    if len(returns) != 12 or len(benchmark) != 12:
        raise ValueError("The study requires exactly 12 intervals")
    for r in returns + benchmark:
        validate_return(r)
    result = dict(observed_intervals=sum(r is not None for r in returns), required_intervals=12,
                  total_return_pct=None, cagr_pct=None, above_ibov_years=None,
                  positive_years=None, negative_years=None, flat_years=None,
                  mean_annual_pct=None, median_annual_pct=None, best_period=None,
                  best_return_pct=None, worst_period=None, worst_return_pct=None,
                  mean_rank=None, consistency_rank=None, final_rank=None)
    if any(r is None for r in returns) or any(r is None for r in benchmark):
        return result
    total = chain(returns)[-1]
    years = (date.fromisoformat(end) - date.fromisoformat(start)).days / 365.25
    best, worst = max(range(12), key=returns.__getitem__), min(range(12), key=returns.__getitem__)
    result.update(total_return_pct=100*total, cagr_pct=100*((1+total)**(1/years)-1),
                  above_ibov_years=None if is_benchmark else sum(r > b for r, b in zip(returns, benchmark)),
                  positive_years=sum(r > 0 for r in returns), negative_years=sum(r < 0 for r in returns),
                  flat_years=sum(r == 0 for r in returns), mean_annual_pct=100*statistics.mean(returns),
                  median_annual_pct=100*statistics.median(returns),
                  best_period=f"{2014+best}–{2015+best}", best_return_pct=100*returns[best],
                  worst_period=f"{2014+worst}–{2015+worst}", worst_return_pct=100*returns[worst])
    return result


def pct(value):
    return "ND" if value is None else f"{value:.4f}".replace(".", ",")


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "---|"*len(headers)] +
                      ["| " + " | ".join(str(x) for x in row) + " |" for row in rows])


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # Accepted benchmark is read verbatim; no recollection or recomputation of closes.
    from stage1_continuation_audit import verify_frozen
    verify_frozen()
    closes = read(OUTPUT / "ibov_june_closes.csv")
    for r in closes:
        r['year'] = int(r['year']); r['ibov_points'] = float(r['ibov_points'])
    assert [r['year'] for r in closes] == list(range(2014, 2027))
    benchmark = [b["ibov_points"]/a["ibov_points"]-1 for a, b in zip(closes, closes[1:])]
    series = {name: [None]*12 for name in NAMES[:-1]} | {"IBOV": benchmark}
    established = read(ROOT / "research/returns_2014_2026_selection/established_segments_pct.csv")
    for r in established:
        i = int(r["year"]) - 2014
        assert r["start"] == closes[i]["date"] and r["end"] == closes[i+1]["date"]
        assert r["selection"] == "ESTABLISHED_IN_SCREENED_ON_UNIVERSE"
        assert r["return_status"] == "GROSS_NOMINAL_B3_WITH_DIRECTED_CORRECTION"
        series[r["portfolio"]][i] = float(r["return_pct"]) / 100
    calculation_status = {(r['portfolio'], int(r['year'])):r['return_status'] for r in established}
    for filename, expected in [
        ('bh_annual_pct.csv','GROSS_CONTINUOUS_OWNED_RIGHTS'),
        ('b00s_initial_pct.csv','EXPLORATORY_DIRECTED_EVENTS_WITH_DISCLOSED_RIGHT_ASSUMPTIONS'),
        *[(stem+'_pct.csv','CONTINUOUS_QUALIFIED_RECONSTRUCTION') for stem in
          ('r03_continuation','b00s_b2_continuation','b00s_bh_continuation')]]:
        for r in read(ROOT/'research/returns_2014_2026_selection'/filename):
            i=int(r['year'])-2014
            assert r['start']==closes[i]['date'] and r['end']==closes[i+1]['date']
            assert r['return_status']==expected and series[r['portfolio']][i] is None
            series[r['portfolio']][i]=float(r['return_pct'])/100
            calculation_status[r['portfolio'],int(r['year'])]=expected
    cumulative = {name: chain(values) for name, values in series.items()}
    annual, accumulated, excess, statuses = [], [], [], []
    reasons = {
        "R03 B2": "Selecoes 2014–2015 calculadas; candidatos PIT indeterminados desde 2016; legado posterior preservado como condicional",
        "B00S B2": "2014–2015 exploratorio calculado; demais retornos exigem continuidade B2 e eventos/sucessoras",
        "B00S BH+entradas": "2014–2015 exploratorio calculado; uniao posterior e eventos/sucessoras pendentes",
        "BH padrão": "12 intervalos calculados com convencoes explicitas de classes no ranking e reinvestimento bruto",
    }
    for i in range(12):
        base = dict(period=f"{2014+i}–{2015+i}", start=closes[i]["date"], end=closes[i+1]["date"])
        annual.append(base | {n: None if series[n][i] is None else 100*series[n][i] for n in NAMES})
        accumulated.append(base | {n: None if cumulative[n][i] is None else 100*cumulative[n][i] for n in NAMES})
        ex = base | {"IBOV_pct": benchmark[i]*100}
        for n in NAMES[:-1]:
            ex[n+"_minus_IBOV_pp"] = None if series[n][i] is None else 100*(series[n][i]-benchmark[i])
            statuses.append(base | dict(portfolio=n, status=calculation_status.get((n,2014+i),'PENDING_SELECTION_OR_EVENTS'),
                reason=("Ranking 2014 com convencoes de classes explicitadas; eventos e direitos continuos" if n=='BH padrão' else
                        "Reconstrucao qualificada: sem nova entrada INDETERMINATE; continuidade, fontes e sensibilidades publicadas") if series[n][i] is not None else reasons[n]))
        excess.append(ex)
    write(OUTPUT / "annual_returns_pct.csv", annual)
    write(OUTPUT / "cumulative_returns_pct.csv", accumulated)
    write(OUTPUT / "annual_excess_pp.csv", excess)
    write(OUTPUT / "portfolio_status.csv", statuses)
    stats = [dict(portfolio=n) | summary(series[n], benchmark, closes[0]["date"], closes[-1]["date"], n=="IBOV") for n in NAMES]
    ranks=[]
    for row in annual:
        ordered=sorted(NAMES,key=lambda n:row[n],reverse=True)
        ranks.append({k:row[k] for k in ('period','start','end')} |
                     {n:1+sum(row[u]>row[n] for u in ordered) for n in NAMES})
    write(OUTPUT/'annual_ranks.csv',ranks)
    for r in stats:
        n=r['portfolio']
        r['mean_rank']=statistics.mean(row[n] for row in ranks)
        r['final_rank']=1+sum(other['total_return_pct']>r['total_return_pct'] for other in stats)
        if n!='IBOV':
            r['consistency_rank']=1+sum(other['above_ibov_years']>r['above_ibov_years']
                for other in stats if other['portfolio']!='IBOV')
    write(OUTPUT / "consolidated_pct.csv", stats)

    # Accepted legacy artifacts remain references and are never rewritten.
    segments=read(OUTPUT/'conditional_legacy_segments_pct.csv')
    for r in segments:
        for k in ('R03_inherited_pct','B00S_inherited_pct','IBOV_pct'):
            r[k]=float(r[k])

    from stage1_report import render
    total = stats[-1]
    report = render(annual, accumulated, stats, segments, NAMES, pct, table)
    (ROOT / "docs/checkpoint_returns_2014_2026_stage1.md").write_text("\n".join(report), encoding="utf-8")
    manifest = dict(status="FOUR_CONTINUOUS_QUALIFIED_RECONSTRUCTIONS_NOT_FULL_PIT_CERTIFICATION", dates=[r['date'] for r in closes],
        complete_requested_portfolios=sum(all(r is not None for r in series[n]) for n in NAMES[:-1]),
        full_trajectories_are_qualified_reconstructions=True,
        complete_benchmark_intervals=12, conditional_legacy_portfolio_intervals=12,
        annual_numeric_cells=sum(r is not None for rs in series.values() for r in rs),
        annual_missing_portfolio_cells=sum(r is None for n in NAMES[:-1] for r in series[n]),
        calculated_portfolio_intervals=sum(r is not None for n in NAMES[:-1] for r in series[n]),
        selection_source="research/returns_2014_2026_selection/established_selections.csv",
        baseline_commit="5cf7eb4", monetary_simulation=False, taxes=False, external_contributions=False,
        inputs=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                for p in [ROOT/"research/returns_2014_2026_selection/continuation_immutable_inputs.json",
                          ROOT/"research/returns_2014_2026_selection/continuation_selection_resolutions.json",
                          ROOT/"research/returns_2014_2026_selection/cache/continuation_events.json.gz"]],
        outputs=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUTPUT.glob('*.csv'))])
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps(total,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
