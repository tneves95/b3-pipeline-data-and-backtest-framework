#!/usr/bin/env python3
"""Read-only, point-in-time preflight. Missing evidence is never a failed filter."""
import argparse
import csv
import hashlib
import json
import math
import re
import sqlite3
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/returns_2014_2026_inputs/coverage"


def cnpj(value):
    return re.sub(r"\D", "", str(value)).zfill(14)


def dump(name, rows):
    if not rows:
        raise ValueError(f"Empty evidence: {name}")
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def read(z, name):
    return pd.read_csv(z.open(name), sep=";", encoding="latin-1", dtype=str, keep_default_na=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", required=True, type=Path)
    args = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    root = args.data_root.resolve()
    db = root / "b3_market_data.sqlite"
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    con = sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    con.row_factory = sqlite3.Row
    dates = {}
    for y in range(2014, 2027):
        data = json.loads((ROOT / f"research/returns_2014_2026_inputs/b3/ibov_{y}.json").read_text())
        days = [int(r["day"]) for r in data["results"] if r.get("rateValue6")]
        dates[y] = f"{y}-06-{max(days):02d}"
    q = ",".join("?" for _ in dates)
    prices = [dict(r) for r in con.execute(f"SELECT ticker,isin_code,date,close,adj_close FROM prices WHERE date IN ({q})", list(dates.values()))]
    dump("june_quotes.csv", prices)
    print("June quotes", len(prices), flush=True)
    mapping = [dict(r) for r in con.execute("SELECT * FROM company_tickers_pit")]
    isin = [dict(r) for r in con.execute("SELECT * FROM company_isin_map")]
    fundamentals = [dict(r) for r in con.execute("SELECT * FROM fundamentals_pit WHERE doc_type='DFP'")]
    by_cnpj = defaultdict(list)
    for r in fundamentals:
        by_cnpj[cnpj(r["cnpj"])].append(r)
    ticker_map = defaultdict(list)
    isin_map = defaultdict(list)
    for r in mapping:
        ticker_map[r["ticker"]].append(r)
    for r in isin:
        isin_map[r["isin_code"]].append(r)

    # The 2009 comparative exists in DFP 2010; use the actual version receipt.
    comparative = []
    with zipfile.ZipFile(root / "data/cvm/dfp_cia_aberta_2010.zip") as z:
        meta = read(z, "dfp_cia_aberta_2010.csv")
        for perimeter in ("con", "ind"):
            d = read(z, f"dfp_cia_aberta_DRE_{perimeter}_2010.csv")
            # Bank and corporate charts use different net-income codes.
            # Follow cvm_parser's existing description-based selection.
            d = d[d.CD_CONTA.str.fullmatch(r"3\.\d{2}") & d.DS_CONTA.str.strip().str.startswith("Lucro")
                  & d.DS_CONTA.str.contains("Período")
                  & (d.DT_INI_EXERC == "2009-01-01") & (d.DT_FIM_EXERC == "2009-12-31")]
            d = d.merge(meta[["CNPJ_CIA", "DT_REFER", "VERSAO", "DT_RECEB", "ID_DOC", "LINK_DOC"]], on=["CNPJ_CIA", "DT_REFER", "VERSAO"], how="left", validate="many_to_one")
            for r in d.to_dict("records"):
                receipt = r["DT_RECEB"] if isinstance(r["DT_RECEB"], str) else ""
                comparative.append(dict(cnpj=cnpj(r["CNPJ_CIA"]), company=r["DENOM_CIA"], perimeter=perimeter,
                    fiscal_year=2009, filing_date=receipt, version=r["VERSAO"], document_id=r["ID_DOC"],
                    account=r["CD_CONTA"], description=r["DS_CONTA"],
                    net_income_statement_units=r["VL_CONTA"], scale=r["ESCALA_MOEDA"],
                    available_june_2014=bool(receipt and receipt <= dates[2014]), source=r["LINK_DOC"]))
    dump("comparative_2009.csv", comparative)
    comp_map = defaultdict(list)
    for r in comparative:
        comp_map[r["cnpj"]].append(r)

    evidence, summary = [], []
    for year in range(2014, 2026):
        cutoff = dates[year]
        start = max(2009, year - 10)
        rows = []
        for px in prices:
            if px["date"] != cutoff or not re.fullmatch(r"[A-Z]{4}[3-6]", px["ticker"]):
                continue
            identities = {cnpj(r["cnpj"]) for r in ticker_map[px["ticker"]]
                          if (not r["start_date"] or r["start_date"] <= cutoff)
                          and (not r["end_date"] or r["end_date"] >= cutoff)}
            identity_source = "company_tickers_pit"
            if not identities:
                # Contemporary quote anchors the security, but this mapping is not PIT proof.
                identities = {cnpj(r["cnpj"]) for r in isin_map[px["isin_code"]]}
                identity_source = "ISIN_crosswalk_requires_historical_confirmation"
            ident = next(iter(identities)) if len(identities) == 1 else ""
            available = {r["fiscal_year"] for r in by_cnpj[ident] if r["filing_date"] <= cutoff and r["net_income"] is not None}
            has2009 = any(r["filing_date"] and r["filing_date"] <= cutoff for r in comp_map[ident])
            if has2009:
                available.add(2009)
            missing = [y for y in range(start, year) if y not in available]
            latest_rows = [r for r in by_cnpj[ident] if r["fiscal_year"] == year - 1]
            late = [r["filing_date"] for r in latest_rows if r["filing_date"] > cutoff]
            row = dict(year=year, cutoff=cutoff, ticker=px["ticker"], isin=px["isin_code"], cnpj=ident,
                identity_source=identity_source, identity_count=len(identities), history_start=start,
                required_years=year-start, positive_years_threshold=math.ceil(.8*(year-start)),
                missing_earnings_years=";".join(map(str, missing)),
                earnings_coverage_status="AVAILABLE_NOT_ELIGIBILITY" if ident and not missing else "INDETERMINATE",
                latest_fy_late_receipts=";".join(sorted(late)),
                available_2009_comparative=has2009,
                selection_status="NOT_ESTABLISHED")
            rows.append(row)
        evidence.extend(rows)
        summary.append(dict(year=year, cutoff=cutoff, quoted_share_classes=len(rows),
            mapped_unique=sum(r["identity_count"] == 1 for r in rows),
            earnings_complete=sum(r["earnings_coverage_status"] == "AVAILABLE_NOT_ELIGIBILITY" for r in rows),
            earnings_indeterminate=sum(r["earnings_coverage_status"] == "INDETERMINATE" for r in rows),
            latest_fy_has_late_receipt=sum(bool(r["latest_fy_late_receipts"]) for r in rows),
            history_start=start, required_years=year-start, positive_years_threshold=math.ceil(.8*(year-start))))
        print("Coverage", year, summary[-1], flush=True)
    dump("earnings_by_security_and_cutoff.csv", evidence)
    dump("annual_coverage.csv", summary)

    # Quantify overwritten DFP versions, distinguishing available metadata from contents.
    versions = []
    for year in range(2010, 2014):
        with zipfile.ZipFile(root / f"data/cvm/dfp_cia_aberta_{year}.zip") as z:
            meta = read(z, f"dfp_cia_aberta_{year}.csv")
            dre = read(z, f"dfp_cia_aberta_DRE_ind_{year}.csv")
            actual = set(zip(dre.CNPJ_CIA, dre.DT_REFER, dre.VERSAO))
            known = meta[meta.DT_RECEB <= dates[2014]]
            for r in known.to_dict("records"):
                versions.append(dict(fiscal_file=year, cnpj=cnpj(r["CNPJ_CIA"]), company=r["DENOM_CIA"],
                    reference=r["DT_REFER"], version=r["VERSAO"], received=r["DT_RECEB"],
                    document_id=r["ID_DOC"], statement_rows_present=(r["CNPJ_CIA"], r["DT_REFER"], r["VERSAO"]) in actual,
                    source=r["LINK_DOC"]))
    dump("dfp_known_versions_2014.csv", versions)

    capital = []
    for year in range(2010, 2015):
        with zipfile.ZipFile(root / f"data/cvm/fre_cia_aberta_{year}.zip") as z:
            meta = read(z, f"fre_cia_aberta_{year}.csv")
            d = read(z, f"fre_cia_aberta_capital_social_{year}.csv")
            d = d[d.Tipo_Capital == "Capital Emitido"]
            d = d.merge(meta[["ID_DOC", "DT_RECEB", "LINK_DOC"]], left_on="ID_Documento", right_on="ID_DOC", how="left", validate="many_to_one")
            for r in d.to_dict("records"):
                receipt = r["DT_RECEB"] if isinstance(r["DT_RECEB"], str) else ""
                approved = r["Data_Autorizacao_Aprovacao"]
                capital.append(dict(file_year=year, cnpj=cnpj(r["CNPJ_Companhia"]), company=r["Nome_Companhia"],
                    document_id=r["ID_Documento"], received=receipt, approved=approved,
                    ordinary_shares=r["Quantidade_Acoes_Ordinarias"], preferred_shares=r["Quantidade_Acoes_Preferenciais"],
                    available_june_2014=bool(receipt and receipt <= dates[2014] and (not approved or approved <= dates[2014])),
                    source=r["LINK_DOC"]))
    dump("capital_versions_2010_2014.csv", capital)
    event_summary = []
    for table, field in [("corporate_actions", "event_date"), ("stock_actions", "ex_date"), ("detected_splits", "ex_date")]:
        for row in con.execute(f"SELECT substr({field},1,4) year, count(*) n,count(distinct isin_code) securities FROM {table} WHERE {field}>='2009-01-01' AND {field}<='2026-06-30' GROUP BY 1"):
            event_summary.append(dict(table=table, **dict(row)))
    dump("events_coverage.csv", event_summary)
    con.close()
    after = hashlib.sha256(db.read_bytes()).hexdigest()
    if before != after:
        raise RuntimeError("Source SQLite changed during audit")
    files = [root / f"data/cvm/{typ}_cia_aberta_{y}.zip" for typ, ys in [("dfp", range(2010,2014)), ("fre", range(2010,2015))] for y in ys]
    manifest = dict(sqlite_sha256=before, sqlite_unchanged=before == after,
        sqlite_connection="mode=ro; PRAGMA query_only=ON", cutoff=dates[2014],
        comparative_2009_records=len(comparative), comparative_2009_available=sum(r["available_june_2014"] for r in comparative),
        dfp_known_versions=len(versions), dfp_known_versions_without_statement=sum(not r["statement_rows_present"] for r in versions),
        source_archives=[dict(path=str(f.relative_to(root)), sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files])
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
