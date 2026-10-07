"""Entitlements and settlement must be evidenced before generating any proceeds."""
import copy

import pytest

from scripts import simulate_itsa_rights_v11_2 as rights


@pytest.fixture
def fixture():
    days = ["2023-08-17", "2023-08-18", "2023-08-21", "2023-08-22", "2023-08-23",
            "2023-08-24", "2023-08-25", "2023-08-28", "2023-08-29"]
    book = rights.m.bridge.PriceBook({"ITSA3": {d: 10.0 for d in days}}, days)
    event = dict(event_id="R", parent="ITSA3", share_class="ON", rights_ticker="ITSA1",
                 fractional_ticker="ITSA1F", rights_isin="RIGHT2023", record_date=days[0],
                 ex_date=days[1], rights_per_share="0.01390757436", available_from="2023-08-24",
                 exercise_deadline_issuer="2023-09-22", source_url="official", source_sha256="sha")
    quote = dict(ticker="ITSA1F", market="020", isin="RIGHT2023", specification="DIR ORD N1",
                 date="2023-08-24", close=3.3, trades=381, quantity=4181, volume=13797.3)
    buy = dict(ticker="ITSA3", market="010", isin="SHARE", specification="ON N1",
               date="2023-08-28", close=10.0, trades=100, quantity=10000, volume=100000)
    return book, event, quote, buy


def test_first_proven_trade_and_d2_skip_weekend(fixture):
    book, event, quote, buy = fixture
    future = dict(quote, date="2023-08-25", close=50)
    premature = dict(quote, date="2023-08-18", close=1)
    x = rights.execution_evidence(event, [future, premature, buy, quote], book)
    assert x["sale_date"] == "2023-08-24"
    assert x["sale_price"] == 3.3
    assert x["settlement_date"] == "2023-08-28"
    assert x["reinvest_date"] == "2023-08-28"


@pytest.mark.parametrize("bad", [{"trades": 0}, {"quantity": 0}, {"volume": 0},
                                  {"close": 0}, {"isin": "PREFERRED"}, {"market": "010"},
                                  {"specification": "DIR PREF"}])
def test_missing_or_wrong_trade_is_not_invented(fixture, bad):
    book, event, quote, buy = fixture
    with pytest.raises(ValueError, match="No proven"):
        rights.execution_evidence(event, [dict(quote, **bad), buy], book)


def test_missing_reinvestment_quote_cannot_use_presettlement_price(fixture):
    book, event, quote, buy = fixture
    with pytest.raises(ValueError, match="No proven ITSA3"):
        rights.execution_evidence(event, [quote, dict(buy, date="2023-08-25")], book)


def test_mismatching_buy_price_is_blocked(fixture):
    book, event, quote, buy = fixture
    with pytest.raises(ValueError, match="divergent"):
        rights.execution_evidence(event, [quote, dict(buy, close=9)], book)


def test_duplicate_first_quote_is_blocked(fixture):
    book, event, quote, buy = fixture
    with pytest.raises(ValueError, match="Ambiguous first"):
        rights.execution_evidence(event, [quote, dict(quote), buy], book)


def test_no_documentary_source_is_blocked(fixture):
    book, event, quote, buy = fixture
    with pytest.raises(ValueError, match="Unverified"):
        rights.execution_evidence(dict(event, source_sha256=""), [quote, buy], book)


def test_entitlement_uses_record_snapshot_and_no_early_reinvestment(fixture):
    book, event, quote, buy = fixture
    verified = rights.execution_evidence(event, [quote, buy], book)
    dividend = rights.m.Event("DIV", "2023-08-18", "CASH", "ITSA3", "test",
                              record_date="2023-08-17", amount=10)
    original = copy.deepcopy(verified)
    state, result, audit = rights.simulate(book, [dividend], [], "2023-08-17", "2023-08-29",
                                           {"ITSA3": 1}, 10000, [verified])
    assert audit[0]["eligible_itsa3"] == 1000
    assert audit[0]["rights_sold"] == 13  # not 27 after the dividend
    assert audit[0]["net_proceeds"] == pytest.approx(42.9)
    assert state.snapshots["2023-08-25"]["ITSA3"] == 2000
    assert state.snapshots["2023-08-28"]["ITSA3"] == pytest.approx(2004.29)
    assert result["final_value"] == pytest.approx(20042.9)
    assert verified == original


def test_actual_allocated_capital_required_for_integer_rights(fixture):
    book, event, quote, buy = fixture
    verified = rights.execution_evidence(event, [quote, buy], book)
    _, large, a = rights.simulate(book, [], [], "2023-08-17", "2023-08-29", {"ITSA3": 1}, 10000, [verified])
    _, small, b = rights.simulate(book, [], [], "2023-08-17", "2023-08-29", {"ITSA3": 1}, 1000, [verified])
    assert a[0]["rights_sold"] == 13
    assert b[0]["rights_sold"] == 1
    assert small["final_value"] == pytest.approx(1003.3)
    assert small["final_value"] != pytest.approx(large["final_value"] / 10)


def test_no_entitlement_for_position_formed_after_record_date(fixture):
    book, event, quote, buy = fixture
    verified = rights.execution_evidence(event, [quote, buy], book)
    _, result, audit = rights.simulate(book, [], [], "2023-08-18", "2023-08-29", {"ITSA3": 1}, 10000, [verified])
    assert result["return"] == 0
    assert not audit


def test_no_rights_monetization_sensitivity_is_unchanged(fixture):
    book, _, _, _ = fixture
    _, result, audit = rights.simulate(book, [], [], "2023-08-17", "2023-08-29", {"ITSA3": 1}, 10000, [])
    assert result["final_value"] == 10000
    assert not audit


def test_fractional_entitlements_are_discarded():
    assert rights.integer_rights(1000, "0.013766678") == 13
    assert rights.integer_rights(50, "0.01390757436") == 0
    assert rights.integer_rights(100, "0.01") == 1
