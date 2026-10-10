"""Reproduce the preliminary audit without downloads or source database writes.

Usage: python -m research.fundamental_multipliers_pilot.audit --source-root ...
All reusable evidence is persisted locally under --output. Temporary SQLite sorting
uses --scratch. No existing discovery engine or backtest is invoked.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
METRICS = [
    "revenue", "net_income", "ebitda", "total_assets", "current_assets",
    "current_liabilities", "operating_cash_flow", "financial_debt", "capital_social",
    "equity", "net_debt", "shares_outstanding", "shares_on", "shares_pn", "net_income_ttm",
]
INDICATORS = [
    "roe_end_equity_proxy", "operating_margin", "ocf_to_positive_income",
    "income_positive", "current_ratio", "financial_debt_assets",
]
SECURITY = re.compile(r"^[A-Z]{4}(?:[3-8]|11)$")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def guard_space(output: Path, scratch: Path, minimum_bytes: int = 1 << 30) -> None:
    for path in (output, scratch):
        if shutil.disk_usage(path).free < minimum_bytes:
            raise RuntimeError(f"Less than {minimum_bytes} free bytes at {path}; stopped")


def save(frame: pd.DataFrame, output: Path, name: str) -> None:
    frame.to_csv(output / name, index=False, float_format="%.12g")


def choose_known_filing(metadata: pd.DataFrame, cutoff: str, period: str) -> pd.Series | None:
    """No substitution of an older version when the latest known filing is absent."""
    valid_receipt = metadata.received.fillna("").str.fullmatch(r"\d{4}-\d{2}-\d{2}")
    known = metadata[valid_receipt & (metadata.period_end == period) & (metadata.received < cutoff)]
    if known.empty:
        return None
    return known.sort_values(["received", "version", "docid"]).iloc[-1]


def ratio(numerator, denominator, *, require_positive_numerator=False):
    if pd.isna(numerator) or pd.isna(denominator):
        return math.nan, "MISSING_INPUT"
    if denominator <= 0:
        return math.nan, "NONPOSITIVE_DENOMINATOR"
    if require_positive_numerator and numerator <= 0:
        return math.nan, "NONPOSITIVE_NUMERATOR"
    return numerator / denominator, "AVAILABLE_DIAGNOSTIC"


def read_metadata(source: Path, manifest: list[dict]) -> pd.DataFrame:
    records = []
    for path in sorted((source / "data/cvm").glob("*.zip")):
        match = re.fullmatch(r"(dfp|itr|fre)_cia_aberta_(\d{4})\.zip", path.name)
        if not match:
            continue
        doc, year = match.groups()
        manifest.append({"path": str(path.relative_to(source)), "bytes": path.stat().st_size,
                         "sha256": sha256(path), "role": "filing_metadata"})
        with zipfile.ZipFile(path) as z:
            name = f"{doc}_cia_aberta_{year}.csv"
            with z.open(name) as stream:
                reader = csv.DictReader(io.TextIOWrapper(stream, encoding="latin-1"), delimiter=";")
                for row in reader:
                    cnpj = re.sub(r"\D", "", row["CNPJ_CIA"])
                    records.append({"cnpj": cnpj, "doc_type": doc.upper(),
                                    "period_end": row["DT_REFER"], "version": int(row["VERSAO"]),
                                    "received": row.get("DT_RECEB", ""), "docid": row.get("ID_DOC", ""),
                                    "source": name, "name": row["DENOM_CIA"]})
    return pd.DataFrame(records).drop_duplicates(["cnpj", "doc_type", "period_end", "version", "received"])


def audit_versions(meta: pd.DataFrame, funds: pd.DataFrame, output: Path):
    stored = funds.rename(columns={"filing_version": "version"})[
        ["cnpj", "doc_type", "period_end", "version", "filing_date", "filing_id"]
    ]
    detail = meta.merge(stored, on=["cnpj", "doc_type", "period_end", "version"], how="left")
    detail["stored"] = detail.filing_id.notna()
    detail["receipt_matches"] = detail.stored & detail.received.eq(detail.filing_date)
    detail["year"] = detail.period_end.str[:4].astype(int)
    summary = detail.groupby(["year", "doc_type"]).agg(
        known_versions=("version", "size"), stored_known_versions=("stored", "sum"),
        receipt_matches=("receipt_matches", "sum"), companies=("cnpj", "nunique"),
    ).reset_index()
    summary["missing_known_versions"] = summary.known_versions - summary.stored_known_versions
    save(summary, output, "filing_versions_by_year.csv")
    # Annual detail is compact enough to keep, including the rejected original IDs.
    save(detail[detail.doc_type == "DFP"], output, "annual_filing_versions.csv")
    periods = detail.groupby(["cnpj", "doc_type", "period_end"]).agg(
        known_versions=("version", "size"), stored_versions=("stored", "sum"),
        first_received=("received", "min"), last_received=("received", "max"),
    ).reset_index()
    save(periods, output, "filing_period_coverage.csv")
    return detail


def audit_raw_prices(source: Path, output: Path, scratch: Path, sources: list[dict]):
    """Stream original quotes, including BDI 08, with constant-sized per-year state."""
    annual, june = [], []
    for year in range(2014, 2027):
        guard_space(output, scratch)
        path = source / "data/raw" / f"COTAHIST_A{year}.ZIP"
        if not path.exists():
            raise FileNotFoundError(path)
        sources.append({"path": str(path.relative_to(source)), "bytes": path.stat().st_size,
                        "sha256": sha256(path), "role": "original_equity_prices"})
        stats = {}
        half = {}
        with zipfile.ZipFile(path) as z:
            with z.open(next(n for n in z.namelist() if not n.endswith("/"))) as stream:
                for lineno, raw in enumerate(stream, 1):
                    # Fixed offsets are bytes in latin-1. Only regular cash-market equities/units.
                    if raw[:2] != b"01" or raw[24:27] != b"010":
                        continue
                    ticker = raw[12:24].decode("latin-1").strip()
                    isin = raw[230:242].decode("latin-1").strip()
                    if not SECURITY.fullmatch(ticker) or not (isin[6:8] == "AC" or isin[6:10] == "CDAM"):
                        continue
                    ymd = raw[2:10].decode("ascii")
                    date = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:8]}"
                    bdi = raw[10:12].decode("ascii")
                    key = ticker, isin, bdi
                    item = stats.setdefault(key, {"year": year, "ticker": ticker, "isin": isin,
                                                  "bdi": bdi, "rows": 0, "first_date": date,
                                                  "last_date": date})
                    item["rows"] += 1
                    item["first_date"] = min(item["first_date"], date)
                    item["last_date"] = max(item["last_date"], date)
                    if date[5:7] > "06":
                        continue
                    factor = int(raw[210:217]) or 1
                    close = int(raw[108:121]) / 100 / factor
                    volume = int(raw[170:188]) / 100
                    hkey = ticker, isin
                    h = half.setdefault(hkey, {"year": year, "ticker": ticker, "isin": isin,
                                               "sessions_h1": 0, "volume_h1": 0., "date": ""})
                    h["sessions_h1"] += 1
                    h["volume_h1"] += volume
                    if date > h["date"]:
                        h.update(date=date, close=close, quotation_factor=factor, bdi=bdi,
                                 raw_line=lineno, raw_sha256=hashlib.sha256(raw).hexdigest(),
                                 source_file=str(path.relative_to(source)))
        annual.extend(stats.values())
        june.extend(half.values())
        print(f"Original quotes {year}: {len(stats)} security and BDI groups", flush=True)
    raw = pd.DataFrame(annual)
    quotes = pd.DataFrame(june)
    save(raw, output, "raw_quote_coverage.csv")
    save(quotes, output, "raw_formation_quotes.csv")
    return raw, quotes


def resolve_company(ticker, isin, cutoff, isinmap, tickermap):
    """Detect disagreement; mappings themselves still lack receipt provenance."""
    a = isinmap[isinmap.isin_code == isin]
    b = tickermap[(tickermap.ticker == ticker) &
                  (tickermap.start_date.isna() | (tickermap.start_date <= cutoff)) &
                  (tickermap.end_date.isna() | (tickermap.end_date >= cutoff))]
    candidates = set(a.cnpj) | set(b.cnpj)
    if len(candidates) == 1:
        return next(iter(candidates)), "UNIQUE_MAP_RECEIPT_UNAUDITED"
    return None, "AMBIGUOUS_MAP" if candidates else "MISSING_MAP"


def make_panel(quotes, meta, funds, isinmap, tickermap, companies, sectors, output):
    annual = meta[meta.doc_type == "DFP"]
    by_company = dict(tuple(annual.groupby("cnpj")))
    fund_index = {r.filing_id: r for r in funds.itertuples()}
    names = companies.set_index("cnpj").company_name.to_dict()
    cohort_dates = quotes.groupby("year").date.max().to_dict()
    rows = []
    for q in quotes.itertuples():
        if q.year > 2023:
            continue
        cutoff = cohort_dates[q.year]
        quote_age = (pd.Timestamp(cutoff) - pd.Timestamp(q.date)).days
        if quote_age > 10 or q.sessions_h1 < 60:
            continue
        cnpj, identity_status = resolve_company(q.ticker, q.isin, cutoff, isinmap, tickermap)
        period = f"{q.year-1}-12-31"
        cm = by_company.get(cnpj, pd.DataFrame(columns=annual.columns))
        known = choose_known_filing(cm, cutoff, period)
        record = {"year": q.year, "formation_date": cutoff, "ticker": q.ticker, "isin": q.isin,
                  "cnpj": cnpj, "company": names.get(cnpj), "identity_status": identity_status,
                  "quote_date": q.date, "raw_close": q.close, "quote_bdi": q.bdi,
                  "sessions_h1": q.sessions_h1, "financial_volume_h1": q.volume_h1,
                  "source_quote_file": q.source_file, "source_quote_line": q.raw_line,
                  "source_quote_sha256": q.raw_sha256, "requested_period": period}
        sector_rows = sectors[(sectors.cnpj == cnpj) & (sectors.sector_received < cutoff)]
        sr = sector_rows.sort_values("sector_received").iloc[-1] if len(sector_rows) else None
        record["sector"] = sr.sector if sr is not None else None
        record["sector_received"] = sr.sector_received if sr is not None else None
        record["sector_docid"] = sr.sector_docid if sr is not None else None
        record["financial_sector"] = (sr is not None and sr.block == "Financeiro")
        record["sector_status"] = "KNOWN_AT_CUTOFF_CACHE_UNAUDITED" if sr is not None else "MISSING_SECTOR"
        f = None
        if known is None:
            record["statement_status"] = "NO_PRIOR_ANNUAL_KNOWN"
        else:
            fid = f"{cnpj}_DFP_{period}_{known.version}"
            f = fund_index.get(fid)
            record.update(required_filing_id=fid, required_version=known.version,
                          required_received=known.received, required_docid=known.docid)
            if f is None:
                record["statement_status"] = "KNOWN_FILING_VALUE_MISSING"
            elif f.filing_date != known.received:
                record["statement_status"] = "RECEIPT_MISMATCH"
                f = None
            else:
                record["statement_status"] = "AVAILABLE_AT_CUTOFF"
        for metric in METRICS:
            record["raw_" + metric] = getattr(f, metric) if f is not None else math.nan
        if f is not None:
            ni, eq, rev = f.net_income, f.equity, f.revenue
            record["income_status"] = "MISSING" if pd.isna(ni) else ("POSITIVE" if ni > 0 else "NONPOSITIVE")
            record["equity_status"] = "MISSING" if pd.isna(eq) else ("POSITIVE" if eq > 0 else "NONPOSITIVE")
            specs = {"roe_end_equity_proxy": (ni, eq), "operating_margin": (f.ebitda, rev),
                     "ocf_to_positive_income": (f.operating_cash_flow, ni),
                     "current_ratio": (f.current_assets, f.current_liabilities),
                     "financial_debt_assets": (f.financial_debt, f.total_assets)}
            for name, (num, den) in specs.items():
                value, status = ratio(num, den)
                if name != "roe_end_equity_proxy" and (record["financial_sector"] or sr is None):
                    value, status = math.nan, "FINANCIAL_OR_UNKNOWN_SECTOR"
                record[name], record[name + "_status"] = value, status
            record["income_positive"] = (float(ni > 0) if pd.notna(ni) else math.nan)
            record["income_positive_status"] = "AVAILABLE_DIAGNOSTIC" if pd.notna(ni) else "MISSING_INPUT"
        else:
            record.update(income_status="MISSING", equity_status="MISSING")
            for name in INDICATORS:
                record[name], record[name + "_status"] = math.nan, record["statement_status"]
        record["predictive_ready"] = False
        record["material_gate"] = "TOTAL_RETURN_AND_CONTINUITY_UNCERTIFIED"
        rows.append(record)
    panel = pd.DataFrame(rows)
    # A company may have ON, PN and unit quotes. Select only by information at formation.
    mapped = panel[panel.cnpj.notna()].sort_values(
        ["year", "cnpj", "financial_volume_h1", "ticker"], ascending=[True, True, False, True])
    chosen = mapped.drop_duplicates(["year", "cnpj"])
    panel["company_representative"] = panel.index.isin(chosen.index)
    save(panel, output, "panel_security_date_diagnostic.csv")
    save(panel[panel.company_representative], output, "panel_company_date_diagnostic.csv")
    save(panel[(panel.statement_status != "AVAILABLE_AT_CUTOFF") |
               (panel.identity_status != "UNIQUE_MAP_RECEIPT_UNAUDITED")], output, "panel_material_gaps.csv")
    coverage = []
    for year, group in panel[panel.company_representative].groupby("year"):
        for name in INDICATORS:
            coverage.append({"formation_year": year, "indicator": name, "companies": len(group),
                             "available_diagnostic": int(group[name].notna().sum()),
                             "missing_or_inapplicable": int(group[name].isna().sum()),
                             "predictive_certified": 0})
    save(pd.DataFrame(coverage), output, "indicator_coverage_by_cohort.csv")
    return panel


def outcome_readiness(panel, quotes, skipped, output, last_observation):
    endpoints = {(r.year, r.ticker, r.isin): r for r in quotes.itertuples()}
    rows = []
    for p in panel[panel.company_representative].itertuples():
        for horizon in [3, 5]:
            target = pd.Timestamp(p.formation_date) + pd.DateOffset(years=horizon)
            complete = target <= pd.Timestamp(last_observation)
            end = endpoints.get((p.year + horizon, p.ticker, p.isin))
            # Only count skipped events in the economic observation window; a count of zero is not certification.
            ev = skipped[(skipped.isin_code == p.isin) & (skipped.event_date > p.formation_date) &
                         (skipped.event_date <= target.strftime("%Y-%m-%d"))]
            rows.append({"cnpj": p.cnpj, "ticker": p.ticker, "isin": p.isin,
                         "formation_date": p.formation_date, "horizon_years": horizon,
                         "calendar_endpoint": target.strftime("%Y-%m-%d"),
                         "calendar_complete": complete,
                         "last_h1_same_security_quote": end.date if end is not None else None,
                         "same_security_near_endpoint": bool(end is not None and 0 <= (target-pd.Timestamp(end.date)).days <= 10),
                         "skipped_events_in_window": len(ev),
                         "status": "TOTAL_RETURN_UNCERTIFIED" if complete else "INCOMPLETE_HORIZON",
                         "nominal_total_return": math.nan, "real_total_return": math.nan,
                         "relative_ibov_return": math.nan,
                         "economic_exit_class": "UNCLASSIFIED_REQUIRES_EVENT_LINEAGE"})
    result = pd.DataFrame(rows)
    save(result, output, "outcome_readiness.csv")
    return result


def plot_coverage(panel, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    group = panel[panel.company_representative].groupby("year")
    matrix = pd.DataFrame({name: group[name].count() / group.size() for name in INDICATORS}).T * 100
    labels = ["ROE com PL final", "Margem EBIT", "FCO / lucro positivo",
              "Sinal do lucro", "Liquidez corrente", "Dívida financeira / ativos"]
    fig, ax = plt.subplots(figsize=(11, 4.4))
    ax.imshow(matrix.values, vmin=0, vmax=100, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(matrix.columns)), matrix.columns)
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(matrix.columns)):
            value = matrix.iloc[i, j]
            ax.text(j, i, f"{value:.0f}%", ha="center", va="center", color="white" if value > 65 else "black")
    ax.set_title("Cobertura diagnóstica dos indicadores por coorte")
    ax.set_xlabel("Ano de formação em junho")
    fig.text(0.01, 0.01, "Denominador: companhias mapeadas com histórico mínimo. Inclui ausências e inaplicabilidade setorial.\n"
             "Valores disponíveis não certificam indicadores ou retornos para inferência preditiva.", fontsize=9)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(output / "diagnostic_coverage.png", dpi=160)
    plt.close(fig)


def run(source: Path, output: Path, scratch: Path):
    output.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    guard_space(output, scratch)
    os.environ["SQLITE_TMPDIR"] = str(scratch)
    os.environ["TMPDIR"] = str(scratch)
    os.environ["MPLCONFIGDIR"] = str(scratch / "matplotlib")
    tempfile.tempdir = str(scratch)
    db = source / "b3_market_data.sqlite"
    # immutable is safe only for this frozen database with an empty WAL.
    wal = Path(str(db) + "-wal")
    if wal.exists() and wal.stat().st_size:
        raise RuntimeError("Nonempty WAL: use a consistent read-only snapshot before auditing")
    before = sha256(db)
    sources = [{"path": "b3_market_data.sqlite", "bytes": db.stat().st_size,
                "sha256": before, "role": "read_only_database"}]
    conn = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA temp_store=FILE")
    tables = pd.DataFrame([{"table": name, "rows": conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]}
                           for name, in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")])
    save(tables, output, "database_tables.csv")
    funds = pd.read_sql_query("SELECT * FROM fundamentals_pit", conn)
    companies = pd.read_sql_query("SELECT * FROM cvm_companies", conn)
    isinmap = pd.read_sql_query("SELECT * FROM company_isin_map", conn)
    tickermap = pd.read_sql_query("SELECT * FROM company_tickers_pit", conn)
    skipped = pd.read_sql_query("SELECT * FROM skipped_events", conn)
    save(skipped, output, "unhandled_events.csv")
    meta = read_metadata(source, sources)
    detail = audit_versions(meta, funds, output)
    annual = funds[funds.doc_type == "DFP"].copy()
    annual = annual.sort_values(["filing_date", "filing_version"]).drop_duplicates(["cnpj", "period_end"], keep="last")
    cols = ["cnpj", "ticker", "fiscal_year", "period_end", "filing_id", "filing_date", "filing_version"]
    coverage = annual[cols].copy()
    for metric in METRICS:
        coverage[metric + "_present"] = annual[metric].notna()
    coverage["stored_ebitda_is_ebit_proxy"] = annual.ebitda.notna()
    save(coverage, output, "raw_coverage_company_year.csv")
    annual_summary = []
    for (year, doc), group in funds.groupby(["fiscal_year", "doc_type"]):
        for metric in METRICS:
            annual_summary.append({"fiscal_year": int(year), "doc_type": doc, "metric": metric,
                                   "rows": len(group), "companies": group.cnpj.nunique(),
                                   "nonmissing_rows": group[metric].notna().sum(),
                                   "companies_with_metric": group.loc[group[metric].notna(), "cnpj"].nunique()})
    save(pd.DataFrame(annual_summary), output, "raw_coverage_year_indicator.csv")
    prices = pd.read_sql_query("""SELECT substr(date,1,4) year,ticker,isin_code isin,
                              count(*) db_rows,min(date) db_first_date,max(date) db_last_date,
                              sum(close!=adj_close) adjusted_diff_rows
                              FROM prices WHERE date >= '2014-01-01'
                              GROUP BY substr(date,1,4),ticker,isin_code""", conn)
    prices["year"] = prices.year.astype(int)
    save(prices, output, "database_quote_coverage.csv")
    raw, quotes = audit_raw_prices(source, output, scratch, sources)
    combined = raw.groupby(["year", "ticker", "isin"]).agg(
        raw_rows=("rows", "sum"), raw_first_date=("first_date", "min"), raw_last_date=("last_date", "max"),
    ).reset_index().merge(prices, how="left", on=["year", "ticker", "isin"])
    combined["db_rows"] = combined.db_rows.fillna(0).astype(int)
    combined["missing_db_rows"] = (combined.raw_rows - combined.db_rows).clip(lower=0)
    save(combined, output, "raw_vs_database_quotes.csv")
    sectors_path = ROOT / "research/returns_2014_2026_selection/identity_sector.csv"
    sectors = pd.read_csv(sectors_path, dtype={"cnpj": str, "sector_docid": str})
    sectors = sectors[["cnpj", "sector", "sector_received", "sector_docid", "block"]].drop_duplicates()
    sources.append({"path": str(sectors_path.relative_to(ROOT)), "bytes": sectors_path.stat().st_size,
                    "sha256": sha256(sectors_path), "role": "sector_cache_receipt_filtered_not_recertified"})
    panel = make_panel(quotes, meta, funds, isinmap, tickermap, companies, sectors, output)
    outcomes = outcome_readiness(panel, quotes, skipped, output, str(raw.last_date.max()))
    plot_coverage(panel, output)
    # Explicitly demonstrate classes and adjusted price valuation distortion on June snapshots.
    sql_samples = []
    for ticker in ["PETR3", "PETR4", "ITUB3", "ITUB4", "MGLU3", "ALUP11", "AMER3", "ENBR3"]:
        sql_samples.extend(conn.execute("""SELECT ticker,date,close,adj_close,isin_code
                          FROM prices WHERE ticker=? AND date IN ('2014-06-30','2020-06-30','2023-06-30')""",
                                        (ticker,)).fetchall())
    sample = pd.DataFrame(sql_samples, columns=["ticker", "date", "raw_close", "adj_close", "isin"])
    sample["adjusted_to_raw_price"] = sample.adj_close / sample.raw_close
    save(sample, output, "valuation_price_audit_samples.csv")
    save(companies[companies.ticker.isin(["AMER", "ENBR", "IRBR", "OGXP", "OIBR", "BHIA", "ITUB", "PETR"])],
         output, "continuity_company_samples.csv")
    conn.close()
    after = sha256(db)
    if before != after:
        raise RuntimeError("Source database changed during audit")
    protocol = json.loads((HERE / "protocol.json").read_text())
    report = {
        "stage": "PRELIMINARY_INVENTORY_COMPLETE_PREDICTIVE_PILOT_BLOCKED",
        "source_sqlite_unchanged": before == after, "sqlite_sha256": before,
        "protocol_sha256": sha256(HERE / "protocol.json"),
        "audit_code_sha256": sha256(Path(__file__)),
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_root": str(source), "scratch": str(scratch),
        "storage_free_bytes": {"persistent": shutil.disk_usage(output).free, "scratch": shutil.disk_usage(scratch).free},
        "tables": tables.set_index("table").rows.to_dict(),
        "known_metadata_versions": len(meta), "metadata_versions_without_stored_values": int((~detail.stored).sum()),
        "dfp_missing_versions": int(((detail.doc_type == "DFP") & ~detail.stored).sum()),
        "missing_original_quote_rows": int(combined.missing_db_rows.sum()),
        "non_bdi02_original_quote_rows": int(raw.loc[raw.bdi != "02", "rows"].sum()),
        "panel_security_rows": len(panel), "panel_company_rows": int(panel.company_representative.sum()),
        "panel_companies": int(panel.loc[panel.company_representative, "cnpj"].nunique()),
        "diagnostic_statements_available": int(((panel.statement_status == "AVAILABLE_AT_CUTOFF") & panel.company_representative).sum()),
        "outcome_readiness_rows": len(outcomes), "certified_outcomes": 0,
        "calendar_complete_outcomes": int(outcomes.calendar_complete.sum()),
        "predictive_estimates_computed": False, "economic_simulations_computed": False,
        "reason": "Distressed price omissions, filing version gaps, unhandled economic continuity and uncertified total return prevent defensible predictive inference",
        "sources": sources,
        "outputs": [],
    }
    for path in sorted(p for p in output.iterdir() if p.suffix in {".csv", ".png"}):
        report["outputs"].append({"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    (output / "manifest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ["sources", "outputs", "tables"]}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT.parent)
    parser.add_argument("--output", type=Path, default=HERE / "local_only" / "data")
    parser.add_argument("--scratch", type=Path, default=Path("/tmp/b3-fundamental-multipliers-audit"))
    args = parser.parse_args()
    run(args.source_root.resolve(), args.output.resolve(), args.scratch.resolve())


if __name__ == "__main__":
    main()
