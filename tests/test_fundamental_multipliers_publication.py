"""Prevent private evidence from entering the public research package."""
import json
from pathlib import Path

import pandas as pd
import pytest

from research.fundamental_multipliers_pilot.audit import sha256
from research.fundamental_multipliers_pilot.publication import (
    AGGREGATE_SCHEMAS,
    DERIVED_SCHEMAS,
    SUMMARY_KEYS,
    export_public,
)


@pytest.fixture
def local_inventory(tmp_path):
    local = tmp_path / "local"
    local.mkdir()
    for name, columns in AGGREGATE_SCHEMAS.items():
        pd.DataFrame([{key: "test" if key in {"table", "doc_type", "metric", "indicator"} else 1
                       for key in columns}]).to_csv(local / name, index=False)
    pd.DataFrame([{"year": 2020, "ticker": "AAAA3", "raw_rows": 250, "db_rows": 200,
                   "missing_db_rows": 50}]).to_csv(local / "raw_vs_database_quotes.csv", index=False)
    pd.DataFrame([{"year": 2020, "bdi": "08", "ticker": "AAAA3", "rows": 50}]).to_csv(
        local / "raw_quote_coverage.csv", index=False)
    pd.DataFrame([{"year": 2020, "cnpj": "00000000000000", "ticker": "AAAA3", "raw_close": 1234.56,
                   "financial_volume_h1": 99999, "statement_status": "AVAILABLE_AT_CUTOFF",
                   "sector_status": "KNOWN_AT_CUTOFF_CACHE_UNAUDITED", "income_status": "POSITIVE",
                   "equity_status": "POSITIVE"}]).to_csv(local / "panel_company_date_diagnostic.csv", index=False)
    pd.DataFrame([{"formation_date": "2020-06-30", "horizon_years": 3, "calendar_complete": True,
                   "same_security_near_endpoint": True, "nominal_total_return": None}]).to_csv(
        local / "outcome_readiness.csv", index=False)
    pd.DataFrame([{"label": "INCORPORACAO", "isin_code": "BRAAAAACNOR1", "factor": 999}]).to_csv(
        local / "unhandled_events.csv", index=False)
    (local / "diagnostic_coverage.png").write_bytes(b"synthetic aggregate graphic")
    (local / "validation.json").write_text(json.dumps({"tests_passed": 8}))
    manifest = {key: 0 for key in SUMMARY_KEYS}
    manifest.update(audit_code_sha256="0" * 64, sources=[{
        "path": "data/raw/COTAHIST_A2020.ZIP", "bytes": 100, "sha256": "0" * 64, "role": "original_equity_prices"}],
        source_root="/private/host/location", scratch="/private/cache", storage_free_bytes={"private": 1})
    update_manifest(local, manifest)
    return local


def update_manifest(local, manifest=None):
    if manifest is None:
        manifest = json.loads((local / "manifest.json").read_text())
    manifest["outputs"] = [
        {"file": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)}
        for p in sorted(local.iterdir()) if p.suffix in {".csv", ".png"}
    ]
    (local / "manifest.json").write_text(json.dumps(manifest))


def test_public_export_contains_counts_without_company_ids_quotes_or_host_paths(local_inventory, tmp_path):
    public = tmp_path / "public"
    summary = export_public(local_inventory, public)
    for name, columns in {**AGGREGATE_SCHEMAS, **DERIVED_SCHEMAS}.items():
        frame = pd.read_csv(public / name)
        assert list(frame.columns) == columns
        assert not set(frame.columns) & {"ticker", "cnpj", "isin", "raw_close", "close", "volume", "factor"}
    assert pd.read_csv(public / "quote_coverage_by_year.csv").missing_db_rows.sum() == 50
    assert not (public / "panel_company_date_diagnostic.csv").exists()
    assert not (public / "raw_formation_quotes.csv").exists()
    assert "source_root" not in summary and "scratch" not in summary and "storage_free_bytes" not in summary
    assert "1234.56" not in (public / "manifest.json").read_text()
    assert (local_inventory / "panel_company_date_diagnostic.csv").exists()


def test_tampered_local_evidence_is_rejected_before_any_export(local_inventory, tmp_path):
    with (local_inventory / "panel_company_date_diagnostic.csv").open("a") as stream:
        stream.write("tampered\n")
    with pytest.raises(ValueError, match="does not match"):
        export_public(local_inventory, tmp_path / "public")
    assert not (tmp_path / "public").exists()


def test_new_columns_cannot_be_copied_even_with_an_updated_local_manifest(local_inventory, tmp_path):
    path = local_inventory / "database_tables.csv"
    frame = pd.read_csv(path)
    frame["raw_close"] = 1234.56
    frame.to_csv(path, index=False)
    update_manifest(local_inventory)
    with pytest.raises(ValueError, match="Unreviewed aggregate schema"):
        export_public(local_inventory, tmp_path / "public")


def test_public_folder_with_unreviewed_files_is_rejected(local_inventory, tmp_path):
    public = tmp_path / "public"
    public.mkdir()
    (public / "quotes.csv").write_text("raw_close\n1234.56\n")
    with pytest.raises(ValueError, match="Unreviewed files"):
        export_public(local_inventory, public)
