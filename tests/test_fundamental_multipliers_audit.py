"""Material safeguards for the independent audit, including observed regressions."""
import hashlib
import math
import zipfile

import pandas as pd
import pytest

from research.fundamental_multipliers_pilot.audit import (
    audit_raw_prices,
    choose_known_filing,
    ratio,
    resolve_company,
    outcome_readiness,
)


def test_latest_public_filing_does_not_fall_back_to_a_stored_old_version():
    # IRB 2019: version 5 was public only in February 2021. Original versions
    # were already public in 2020 and must be required even if their values are absent.
    meta = pd.DataFrame([
        {"period_end": "2019-12-31", "received": "2020-02-18", "version": 1, "docid": "1"},
        {"period_end": "2019-12-31", "received": "2020-06-30", "version": 3, "docid": "3"},
        {"period_end": "2019-12-31", "received": "2021-02-18", "version": 5, "docid": "5"},
    ])
    assert choose_known_filing(meta, "2020-06-30", "2019-12-31").version == 1
    assert choose_known_filing(meta, "2020-07-01", "2019-12-31").version == 3
    assert choose_known_filing(meta, "2021-06-30", "2019-12-31").version == 5
    assert choose_known_filing(meta, "2019-06-30", "2019-12-31") is None


def test_unknown_receipt_never_becomes_available_by_string_comparison():
    meta = pd.DataFrame([
        {"period_end": "2019-12-31", "received": "", "version": 1, "docid": "1"},
        {"period_end": "2019-12-31", "received": None, "version": 2, "docid": "2"},
    ])
    assert choose_known_filing(meta, "2020-06-30", "2019-12-31") is None


@pytest.mark.parametrize("numerator,denominator", [(-10., -20.), (10., 0.), (10., -1.)])
def test_negative_or_zero_equity_does_not_create_apparent_high_roe(numerator, denominator):
    value, status = ratio(numerator, denominator)
    assert math.isnan(value)
    assert status == "NONPOSITIVE_DENOMINATOR"


def test_missing_financial_value_is_not_zero():
    value, status = ratio(float("nan"), 100.)
    assert math.isnan(value)
    assert status == "MISSING_INPUT"
    # Losses remain economically meaningful where the denominator is positive.
    assert ratio(-10., 100.)[0] == -0.1


def test_identity_conflicts_are_not_resolved_by_ticker_root():
    isinmap = pd.DataFrame([{"isin_code": "BRAMERACNOR6", "cnpj": "001"}])
    tickermap = pd.DataFrame([{"ticker": "AMER3", "cnpj": "002", "start_date": "2020-01-01", "end_date": None}])
    assert resolve_company("AMER3", "BRAMERACNOR6", "2021-06-30", isinmap, tickermap) == (None, "AMBIGUOUS_MAP")


def record(year, bdi):
    line = bytearray(b" " * 245)
    for start, end, value in [
        (0, 2, b"01"), (2, 10, f"{year}0630".encode()), (10, 12, bdi.encode()),
        (12, 24, b"AMER3       "), (24, 27, b"010"),
        (108, 121, b"0000000002500"), (170, 188, b"000000000000100000"),
        (210, 217, b"0000005"), (230, 242, b"BRAMERACNOR6"),
    ]:
        line[start:end] = value
    return bytes(line) + b"\n"


def test_original_quotes_include_distressed_bdi_and_normalize_quotation_factor(tmp_path):
    # AMER's switch to BDI 08 must not silently truncate its history.
    source = tmp_path / "source"
    (source / "data/raw").mkdir(parents=True)
    output = tmp_path / "output"
    output.mkdir()
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    for year in range(2014, 2027):
        with zipfile.ZipFile(source / "data/raw" / f"COTAHIST_A{year}.ZIP", "w") as z:
            z.writestr(f"COTAHIST_A{year}.TXT", record(year, "08"))
    raw, quotes = audit_raw_prices(source, output, scratch, [])
    assert len(raw) == 13
    assert set(raw.bdi) == {"08"}
    assert (quotes.close == 5.).all()
    assert quotes.iloc[0].raw_sha256 == hashlib.sha256(record(2014, "08")).hexdigest()
    assert (output / "raw_formation_quotes.csv").exists()


@pytest.mark.parametrize("formation,target,earlier,later", [
    ("2018-06-29", "2021-06-29", "2021-06-29", "2021-06-30"),
    ("2019-06-28", "2022-06-28", "2022-06-28", "2022-06-30"),
    ("2017-06-30", "2020-06-30", "2020-06-30", "2020-07-01"),
])
def test_readiness_never_uses_a_post_maturity_quote(tmp_path, formation, target, earlier, later):
    panel = pd.DataFrame([dict(year=int(formation[:4]), formation_date=formation,
        cnpj="001", ticker="OLD3", isin="ISIN_A", company_representative=True)])
    quotes = pd.DataFrame([
        dict(ticker="OLD3", isin="ISIN_A", date=earlier),
        dict(ticker="OLD3", isin="ISIN_A", date=later)])
    skipped = pd.DataFrame(columns=["isin_code", "event_date"])
    result = outcome_readiness(panel, quotes, skipped, tmp_path, "2026-10-01",
                               calendar=[formation, earlier, later])
    row = result[result.horizon_years == 3].iloc[0]
    assert row.last_available_same_security_quote == target
    assert row.same_security_near_endpoint
    assert row.quote_age_sessions == 0


def test_readiness_weekend_and_ticker_rename_preserve_isin_without_reusing_ticker(tmp_path):
    panel = pd.DataFrame([dict(year=2018, formation_date="2018-06-29", cnpj="001",
                              ticker="OLD3", isin="ISIN_A", company_representative=True)])
    quotes = pd.DataFrame([
        dict(ticker="NEW3", isin="ISIN_A", date="2023-06-28"),
        dict(ticker="OLD3", isin="ISIN_B", date="2023-06-29"),
        dict(ticker="NEW3", isin="ISIN_A", date="2023-06-30")])
    result = outcome_readiness(panel, quotes, pd.DataFrame(columns=["isin_code", "event_date"]),
        tmp_path, "2026-10-01", calendar=["2018-06-29", "2021-06-28", "2021-06-30",
        "2023-06-28", "2023-06-29", "2023-06-30"])
    row = result[result.horizon_years == 5].iloc[0]
    assert row.last_available_same_security_quote == "2023-06-28"
    assert row.endpoint_observed_ticker == "NEW3"
    assert row.quote_age_sessions == 1
    weekend = panel.copy(); weekend.formation_date = "2016-06-30"; weekend.year = 2016
    weekend_quotes = pd.DataFrame([dict(ticker="OLD3", isin="ISIN_A", date="2019-06-28")])
    row = outcome_readiness(weekend, weekend_quotes, pd.DataFrame(columns=["isin_code", "event_date"]),
        tmp_path, "2026-10-01", calendar=["2016-06-30", "2019-06-28", "2019-07-01"]).iloc[0]
    assert row.endpoint_session_date == "2019-06-28"
    assert row.quote_age_sessions == 0


def test_readiness_requires_calendar_and_exact_snapshot_cutoff(tmp_path):
    panel = pd.DataFrame([dict(year=2018, formation_date="2018-06-29", cnpj="001",
        ticker="OLD3", isin="ISIN_A", company_representative=True)])
    quotes = pd.DataFrame([dict(ticker="OLD3", isin="ISIN_A", date="2021-06-28", cutoff="2021-06-30")])
    skipped = pd.DataFrame(columns=["isin_code", "event_date"])
    with pytest.raises(ValueError, match="calendar"):
        outcome_readiness(panel, quotes, skipped, tmp_path, "2026-10-01")
    result = outcome_readiness(panel, quotes, skipped, tmp_path, "2026-10-01",
                               calendar=["2018-06-29", "2021-06-28", "2021-06-30"])
    assert not result.iloc[0].same_security_near_endpoint
