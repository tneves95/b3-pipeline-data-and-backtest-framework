"""Economic missingness, official calendar and offline artifact invariants."""
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("stage1", ROOT / "scripts/returns_stage1.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_compounding_is_not_arithmetic_sum():
    assert m.chain([.5, -.5]) == [.5, -.25]


def test_unknown_does_not_become_flat_or_restart_cohort():
    assert m.chain([.2, None, .3]) == pytest.approx([.2, None, None])
    assert m.chain([None]*6 + [.3]*6) == [None]*12


def test_total_loss_is_absorbing():
    assert m.chain([.3, -1, .8])[-1] == -1


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.01])
def test_invalid_return_is_rejected(bad):
    with pytest.raises(ValueError):
        m.chain([bad])


def test_calendar_uses_actual_last_june_observation():
    payload = json.loads((m.INPUT / "b3/ibov_2024.json").read_text())
    assert m.june_close(payload, 2024) == ("2024-06-28", 123906.55)


def test_duplicate_calendar_day_is_rejected():
    with pytest.raises(ValueError):
        m.june_close({"results": [{"day": 30, "rateValue6": "100,00"}]*2}, 2025)


def test_incomplete_trajectory_has_no_full_period_statistics():
    r = m.summary([None]*6+[.3]*6, [.1]*12, "2014-06-30", "2026-06-30")
    assert r["observed_intervals"] == 6
    for key in ["total_return_pct", "cagr_pct", "above_ibov_years", "mean_rank", "positive_years"]:
        assert r[key] is None


def test_positive_negative_flat_and_strict_outperformance():
    r = m.summary([.1, -.1, 0]*4, [.1]*12, "2014-06-30", "2026-06-30")
    assert (r["positive_years"],r["negative_years"],r["flat_years"]) == (4,4,4)
    assert r["above_ibov_years"] == 0


def test_original_b3_responses_match_source_hashes():
    sources = json.loads((m.INPUT / "b3/sources.json").read_text())
    assert {s["year"] for s in sources} == set(range(2014,2027))
    for s in sources:
        assert s["url"].startswith("https://sistemaswebb3-listados.b3.com.br/")
        assert hashlib.sha256((m.INPUT / "b3" / s["path"]).read_bytes()).hexdigest() == s["sha256"]


def test_tables_include_ibov_and_do_not_mislabel_legacy_fragments():
    for name in ["annual_returns_pct.csv", "cumulative_returns_pct.csv"]:
        rows = m.read(m.OUTPUT / name)
        assert len(rows) == 12
        assert all(all(n in r for n in m.NAMES) for r in rows)
        assert all(r['R03 B2'] for r in rows[:2])
        assert all(r['R03 B2']=='' for r in rows[2:])
        assert all(all(r[n] == "" for n in m.NAMES[1:-1]) for r in rows)
        assert all(r["IBOV"] for r in rows)


def test_new_segments_chain_from_2014_and_stop_at_first_gap():
    annual=m.read(m.OUTPUT/'annual_returns_pct.csv')
    accumulated=m.read(m.OUTPUT/'cumulative_returns_pct.csv')
    expected=100*((1+float(annual[0]['R03 B2'])/100)*(1+float(annual[1]['R03 B2'])/100)-1)
    assert float(accumulated[1]['R03 B2'])==pytest.approx(expected)
    assert accumulated[2]['R03 B2']=='' and accumulated[-1]['R03 B2']==''


def test_ibov_cumulative_matches_independent_endpoint_ratio():
    rows = m.read(m.OUTPUT / "cumulative_returns_pct.csv")
    assert float(rows[-1]["IBOV"]) == pytest.approx(100*(172024.12/53168.22-1), abs=1e-10)
    stats = m.read(m.OUTPUT / "consolidated_pct.csv")[-1]
    assert stats["positive_years"] == "8" and stats["negative_years"] == "4"
    assert stats["above_ibov_years"] == "" and stats["consistency_rank"] == ""


def test_legacy_comparisons_are_percentage_points_on_identical_dates():
    bench = {r["end"]: r for r in m.read(m.OUTPUT / "annual_returns_pct.csv")}
    for r in m.read(m.OUTPUT / "conditional_legacy_segments_pct.csv"):
        assert bench[r["end"]]["start"] == r["start"]
        assert float(r["IBOV_pct"]) == float(bench[r["end"]]["IBOV"])
        for p in ["R03", "B00S"]:
            assert float(r[p+"_minus_IBOV_pp"]) == pytest.approx(float(r[p+"_inherited_pct"])-float(r["IBOV_pct"]))
        assert r["status"] == "CONDITIONAL_LEGACY_REFERENCE_NOT_VALIDATED_STAGE1"


def test_2009_evidence_selects_earnings_not_bank_jcp_reversals():
    rows = m.read(m.INPUT / "coverage/comparative_2009.csv")
    assert rows
    assert all(r["description"].startswith("Lucro") and "Período" in r["description"] for r in rows)
    assert all(r["filing_date"] <= "2014-06-30" for r in rows if r["available_june_2014"] == "True")


def test_progressive_history_preserves_proportional_threshold():
    rows = m.read(m.INPUT / "coverage/annual_coverage.csv")
    assert [int(r["required_years"]) for r in rows] == [5,6,7,8,9,10,10,10,10,10,10,10]
    assert [int(r["positive_years_threshold"]) for r in rows[:6]] == [4,5,6,7,8,8]


def test_sqlite_integrity_was_verified():
    manifest = json.loads((m.INPUT / "coverage/manifest.json").read_text())
    assert manifest["sqlite_unchanged"] is True
    assert manifest["sqlite_connection"] == "mode=ro; PRAGMA query_only=ON"


def test_full_offline_replay_is_byte_identical():
    paths = list(m.OUTPUT.glob("*")) + [ROOT / "docs/checkpoint_returns_2014_2026_stage1.md"]
    before = {p: p.read_bytes() for p in paths}
    subprocess.run([sys.executable, str(ROOT / "scripts/returns_stage1.py")], cwd=ROOT, check=True, capture_output=True)
    assert all(p.read_bytes() == data for p,data in before.items())
