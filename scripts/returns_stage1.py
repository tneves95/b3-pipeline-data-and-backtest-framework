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
    sources = json.loads((INPUT / "b3/sources.json").read_text())
    closes = []
    for source in sources:
        path = INPUT / "b3" / source["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
        day, level = june_close(json.loads(path.read_text()), source["year"])
        closes.append(dict(year=source["year"], date=day, ibov_points=level, source=source["url"], sha256=source["sha256"]))
    closes.sort(key=lambda r: r["year"])
    assert [r["year"] for r in closes] == list(range(2014, 2027))
    assert closes[-1]["date"] == "2026-06-30"
    write(OUTPUT / "ibov_june_closes.csv", closes)
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
        ('b00s_initial_pct.csv','EXPLORATORY_DIRECTED_EVENTS_WITH_DISCLOSED_RIGHT_ASSUMPTIONS')]:
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
                        "Exploratorio: selecao estabelecida; fontes dirigidas e ressalvas documentadas") if series[n][i] is not None else reasons[n]))
        excess.append(ex)
    write(OUTPUT / "annual_returns_pct.csv", annual)
    write(OUTPUT / "cumulative_returns_pct.csv", accumulated)
    write(OUTPUT / "annual_excess_pp.csv", excess)
    write(OUTPUT / "portfolio_status.csv", statuses)
    stats = [dict(portfolio=n) | summary(series[n], benchmark, closes[0]["date"], closes[-1]["date"], n=="IBOV") for n in NAMES]
    # Rankings require all five comparable trajectories; IBOV alone is not a winner.
    write(OUTPUT / "consolidated_pct.csv", stats)

    # Recompute percentage comparisons for inherited windows; not a new starting cohort.
    graham_path = LEGACY / "execution_v11_2_2026_10_07/direitos_itsa_v11_2/anuais_capital_10000.csv"
    barsi_path = LEGACY / "checkpoint_v13_2026_10_07/comparacao_anuais_manutencao_v13.csv"
    gr = {int(r["year"]): r for r in read(graham_path)}
    br = {int(r["year"]): r for r in read(barsi_path) if r["strategy"] == "B00S" and r["scenario"] == "central"
          and r["mechanism"] == "annual" and r["experiment"] == "v12_plus_v13"}
    assert set(gr) == set(br) == set(range(2020, 2026))
    segments = []
    for y in range(2020, 2026):
        i = y - 2014
        assert gr[y]["start"] == closes[i]["date"] and gr[y]["end"] == closes[i+1]["date"]
        g, b = float(gr[y]["R03"]), float(br[y]["central_return"])
        segments.append(dict(period=f"{y}–{y+1}", start=closes[i]["date"], end=closes[i+1]["date"],
            R03_inherited_pct=100*g, B00S_inherited_pct=100*b, IBOV_pct=100*benchmark[i],
            R03_minus_IBOV_pp=100*(g-benchmark[i]), B00S_minus_IBOV_pp=100*(b-benchmark[i]),
            status="CONDITIONAL_LEGACY_REFERENCE_NOT_VALIDATED_STAGE1",
            R03_source=str(graham_path.relative_to(ROOT)), B00S_source=str(barsi_path.relative_to(ROOT))))
    write(OUTPUT / "conditional_legacy_segments_pct.csv", segments)

    # Existing selections, with known years explicitly scoped and previous history unknown.
    weights = [r for r in read(LEGACY / "execution_v11_2_2026_10_07/carteiras_selecionadas_768_posicoes.csv")
               if (r["strategy"], r["scenario"]) in [("R03", "corrigido"), ("B00S", "central")]]
    write(OUTPUT / "conditional_legacy_weights.csv", weights)
    changes = []
    for strategy in ("R03", "B00S"):
        previous = None
        for y in range(2020,2026):
            current = {r["ticker"] for r in weights if r["strategy"] == strategy and int(r["year"]) == y}
            assert math.isclose(sum(float(r["weight"]) for r in weights if r["strategy"] == strategy and int(r["year"]) == y), 1, abs_tol=1e-12)
            changes.append(dict(year=y, strategy=strategy, members=";".join(sorted(current)),
                additions=None if previous is None else ";".join(sorted(current-previous)),
                removals=None if previous is None else ";".join(sorted(previous-current)),
                status="PREVIOUS_SELECTION_UNKNOWN" if previous is None else "LEGACY_TICKER_DIFF_REQUIRES_ISSUER_CONTINUITY"))
            previous = current
    write(OUTPUT / "conditional_legacy_membership_changes.csv", changes)

    from stage1_report import render
    total = stats[-1]
    report = render(annual, accumulated, stats, segments, NAMES, pct, table)
    (ROOT / "docs/checkpoint_returns_2014_2026_stage1.md").write_text("\n".join(report), encoding="utf-8")
    manifest = dict(status="PARTIAL_NOT_FULL_FOUR_PORTFOLIO_STUDY", dates=[r['date'] for r in closes],
        complete_requested_portfolios=sum(all(r is not None for r in series[n]) for n in NAMES[:-1]),
        full_trajectories_are_qualified_reconstructions=True,
        complete_benchmark_intervals=12, conditional_legacy_portfolio_intervals=12,
        annual_numeric_cells=sum(r is not None for rs in series.values() for r in rs),
        annual_missing_portfolio_cells=sum(r is None for n in NAMES[:-1] for r in series[n]),
        calculated_portfolio_intervals=sum(r is not None for n in NAMES[:-1] for r in series[n]),
        selection_source="research/returns_2014_2026_selection/established_selections.csv",
        baseline_commit="fc62733", monetary_simulation=False, taxes=False, external_contributions=False,
        inputs=[dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                for p in [graham_path,barsi_path]],
        outputs=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUTPUT.glob('*.csv'))])
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps(total,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
