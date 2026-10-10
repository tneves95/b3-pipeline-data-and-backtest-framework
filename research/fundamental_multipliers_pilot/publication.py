"""Export only aggregate counts and provenance from an audited local inventory.

No security prices, volumes, company panels or individual events are copied.
Usage: python -m research.fundamental_multipliers_pilot.publication
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .audit import HERE, sha256

# Exact column allowlists prevent an expanded local file from publishing new fields.
AGGREGATE_SCHEMAS = {
    "database_tables.csv": ["table", "rows"],
    "filing_versions_by_year.csv": ["year", "doc_type", "known_versions", "stored_known_versions",
                                    "receipt_matches", "companies", "missing_known_versions"],
    "indicator_coverage_by_cohort.csv": ["formation_year", "indicator", "companies", "available_diagnostic",
                                         "missing_or_inapplicable", "predictive_certified"],
    "raw_coverage_year_indicator.csv": ["fiscal_year", "doc_type", "metric", "rows", "companies",
                                        "nonmissing_rows", "companies_with_metric"],
}
DERIVED_SCHEMAS = {
    "quote_coverage_by_year.csv": ["year", "security_groups", "raw_rows", "db_rows", "missing_db_rows"],
    "quotes_by_bdi_year.csv": ["year", "bdi", "security_groups", "rows"],
    "panel_coverage_by_cohort.csv": ["year", "companies", "statements_available", "known_filing_values_missing",
                                      "no_prior_annual_known", "missing_sector", "positive_income",
                                      "nonpositive_income", "nonpositive_equity"],
    "outcome_readiness_by_cohort.csv": ["formation_year", "horizon_years", "observations", "calendar_complete",
                                         "same_security_near_endpoint", "certified_total_returns"],
    "unhandled_events_by_type.csv": ["label", "events"],
}
SUMMARY_KEYS = [
    "stage", "source_sqlite_unchanged", "sqlite_sha256", "protocol_sha256", "base_commit", "tables",
    "known_metadata_versions", "metadata_versions_without_stored_values", "dfp_missing_versions",
    "missing_original_quote_rows", "non_bdi02_original_quote_rows", "panel_security_rows",
    "panel_company_rows", "panel_companies", "diagnostic_statements_available", "outcome_readiness_rows",
    "certified_outcomes", "calendar_complete_outcomes", "predictive_estimates_computed",
    "economic_simulations_computed", "reason",
]


def load_verified(local: Path):
    manifest_path = local / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for item in manifest["outputs"]:
        name = item["file"]
        if Path(name).name != name or not name.endswith((".csv", ".png")):
            raise ValueError(f"Invalid evidence filename: {name}")
        path = local / name
        if path.is_symlink() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"Local evidence does not match audited manifest: {name}")
    return manifest


def export_public(local: Path, output: Path):
    if output.resolve() == local.resolve() or local.resolve() in output.resolve().parents:
        raise ValueError("Public output must be separate from local evidence")
    manifest = load_verified(local)
    frames = {}
    for name, schema in AGGREGATE_SCHEMAS.items():
        frame = pd.read_csv(local / name)
        if list(frame.columns) != schema:
            raise ValueError(f"Unreviewed aggregate schema: {name}")
        frames[name] = frame

    quotes = pd.read_csv(local / "raw_vs_database_quotes.csv")
    frames["quote_coverage_by_year.csv"] = quotes.groupby("year").agg(
        security_groups=("ticker", "size"), raw_rows=("raw_rows", "sum"), db_rows=("db_rows", "sum"),
        missing_db_rows=("missing_db_rows", "sum")).reset_index()
    bdi = pd.read_csv(local / "raw_quote_coverage.csv", dtype={"bdi": str})
    frames["quotes_by_bdi_year.csv"] = bdi.groupby(["year", "bdi"]).agg(
        security_groups=("ticker", "size"), rows=("rows", "sum")).reset_index()
    panel = pd.read_csv(local / "panel_company_date_diagnostic.csv", dtype={"cnpj": str})
    panel_rows = []
    for year, group in panel.groupby("year"):
        panel_rows.append({
            "year": year, "companies": len(group),
            "statements_available": int(group.statement_status.eq("AVAILABLE_AT_CUTOFF").sum()),
            "known_filing_values_missing": int(group.statement_status.eq("KNOWN_FILING_VALUE_MISSING").sum()),
            "no_prior_annual_known": int(group.statement_status.eq("NO_PRIOR_ANNUAL_KNOWN").sum()),
            "missing_sector": int(group.sector_status.eq("MISSING_SECTOR").sum()),
            "positive_income": int(group.income_status.eq("POSITIVE").sum()),
            "nonpositive_income": int(group.income_status.eq("NONPOSITIVE").sum()),
            "nonpositive_equity": int(group.equity_status.eq("NONPOSITIVE").sum()),
        })
    frames["panel_coverage_by_cohort.csv"] = pd.DataFrame(panel_rows, columns=DERIVED_SCHEMAS["panel_coverage_by_cohort.csv"])
    outcomes = pd.read_csv(local / "outcome_readiness.csv")
    outcomes["formation_year"] = outcomes.formation_date.str[:4].astype(int)
    outcomes["certified_total_returns"] = outcomes.nominal_total_return.notna().astype(int)
    frames["outcome_readiness_by_cohort.csv"] = outcomes.groupby(["formation_year", "horizon_years"]).agg(
        observations=("formation_date", "size"), calendar_complete=("calendar_complete", "sum"),
        same_security_near_endpoint=("same_security_near_endpoint", "sum"),
        certified_total_returns=("certified_total_returns", "sum")).reset_index()
    events = pd.read_csv(local / "unhandled_events.csv")
    frames["unhandled_events_by_type.csv"] = events.groupby("label").size().reset_index(name="events")
    for name, schema in DERIVED_SCHEMAS.items():
        if list(frames[name].columns) != schema:
            raise ValueError(f"Unreviewed derived schema: {name}")

    allowed = set(frames) | {"manifest.json", "diagnostic_coverage.png", "publication_inventory.csv"}
    output.mkdir(parents=True, exist_ok=True)
    extras = {p.name for p in output.iterdir()} - allowed
    if extras:
        raise ValueError(f"Unreviewed files in public output: {sorted(extras)}")
    for name, frame in frames.items():
        frame.to_csv(output / name, index=False)
    (output / "diagnostic_coverage.png").write_bytes((local / "diagnostic_coverage.png").read_bytes())

    inventory = []
    for path in sorted(local.iterdir()):
        if path.suffix not in {".csv", ".json", ".png"}:
            raise ValueError(f"Unexpected local artifact: {path.name}")
        is_aggregate = path.name in AGGREGATE_SCHEMAS or path.name == "diagnostic_coverage.png"
        inventory.append({
            "file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path),
            "decision": "PUBLISH_AGGREGATE" if is_aggregate else "KEEP_LOCAL",
            "reason": "Aggregate counts or coverage figure" if is_aggregate else "Granular evidence or full local provenance; unnecessary for public reproduction",
        })
    pd.DataFrame(inventory).to_csv(output / "publication_inventory.csv", index=False)
    summary = {key: manifest[key] for key in SUMMARY_KEYS}
    summary["local_audit_code_sha256"] = manifest["audit_code_sha256"]
    summary["published_audit_code_sha256"] = sha256(HERE / "audit.py")
    summary["publication_code_sha256"] = sha256(Path(__file__))
    summary["local_manifest_sha256"] = sha256(local / "manifest.json")
    summary["publication_scope"] = "Aggregate coverage counts, source hashes and sizes; no quotes, financial values, company panels or individual events"
    summary["sources"] = []
    for item in manifest["sources"]:
        if Path(item["path"]).is_absolute() or ".." in Path(item["path"]).parts:
            raise ValueError("Source manifest contains a nonrelative path")
        summary["sources"].append({key: item[key] for key in ["path", "bytes", "sha256", "role"]})
    summary["local_validation"] = json.loads((local / "validation.json").read_text())
    csv_count = sum(item["file"].endswith(".csv") for item in manifest["outputs"])
    summary["local_validation"]["csv_count_verified_against_manifest"] = csv_count
    if "reproduction_identical_csv_files" in summary["local_validation"]:
        summary["local_validation"]["reproduction_identical_csv_files"] = csv_count
        summary["local_validation"]["counter_correction"] = "Original local counter included the coverage PNG; local evidence record remains preserved"
    summary["outputs"] = [
        {"file": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)}
        for p in sorted(output.iterdir()) if p.name != "manifest.json"
    ]
    (output / "manifest.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", type=Path, default=HERE / "local_only" / "data")
    parser.add_argument("--output", type=Path, default=HERE / "published")
    args = parser.parse_args()
    result = export_public(args.local, args.output)
    print(json.dumps({"published_files": len(result["outputs"]) + 1,
                      "published_bytes": sum(p.stat().st_size for p in args.output.iterdir()),
                      "local_evidence_preserved": True}, indent=2))


if __name__ == "__main__":
    main()
