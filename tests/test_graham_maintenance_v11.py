"""Regression checks against the supplied, unchanged v6 event engine."""
import pytest

from scripts import graham_corrected_maintenance_v11 as maintenance
from scripts import compare_maintenance_graham_barsi_v11 as comparison
from scripts import audit_graham_v11_sources as sources
from scripts.graham_v11_documentary_sensitivity import documented_events
from motor_eventos import MissingData


def test_sparse_intermediate_quotes_do_not_abort_valuation():
    # Regression: PriceBook and Engine must agree on the exception type.
    book = maintenance.bridge.PriceBook(
        {"UNIP3": {"2025-05-13": 51, "2025-05-15": 51.6}},
        ["2025-05-13", "2025-05-14", "2025-05-15"],
    )
    result = maintenance.safe_result(
        maintenance.Engine(book, []), "2025-05-13", "2025-05-15", "UNIP3"
    )
    assert result["return"] == pytest.approx(51.6 / 51 - 1)
    assert result["daily_missing"] == 1
    assert "2025-05-14" not in book.prices["UNIP3"]


@pytest.mark.parametrize("missing", ["entry", "exit", "reinvestment"])
def test_missing_required_price_still_fails(missing):
    prices = {"2025-05-13": 51, "2025-05-14": 51.2, "2025-05-15": 51.6}
    prices.pop({"entry": "2025-05-13", "exit": "2025-05-15",
                "reinvestment": "2025-05-14"}[missing])
    book = maintenance.bridge.PriceBook({"UNIP3": prices},
                                       ["2025-05-13", "2025-05-14", "2025-05-15"])
    event = maintenance.Event("div", "2025-05-14", "CASH", "UNIP3", "test",
                              record_date="2025-05-13", amount=1)
    with pytest.raises(MissingData):
        maintenance.safe_result(maintenance.Engine(book, [event]),
                                "2025-05-13", "2025-05-15", "UNIP3")


def test_distinct_same_record_date_payments_use_same_entitlement():
    book = maintenance.bridge.PriceBook({"AAA3": {"2025-01-02": 10, "2025-01-03": 10}},
                                       ["2025-01-02", "2025-01-03"])
    events = [maintenance.Event(str(i), "2025-01-03", "CASH", "AAA3", "test",
                                 record_date="2025-01-02", amount=amount)
              for i, amount in enumerate([1, 2])]
    result = maintenance.safe_result(maintenance.Engine(book, events),
                                     "2025-01-02", "2025-01-03", "AAA3")
    assert result["return"] == pytest.approx(.3)  # not (1.1 * 1.2) - 1
    assert result["holdings"]["AAA3"] == pytest.approx(1300)


def test_cash_out_and_successor_are_preserved():
    book = maintenance.bridge.PriceBook(
        {"AAA3": {"2025-01-02": 10}, "BBB3": {"2025-01-03": 12, "2025-01-06": 13}},
        ["2025-01-02", "2025-01-03", "2025-01-06"])
    event = maintenance.Event("merge", "2025-01-03", "MERGER", "AAA3", "test",
                              amount=2, legs=(("BBB3", 2),))
    result = maintenance.safe_result(maintenance.Engine(book, [event]),
                                     "2025-01-02", "2025-01-06", "AAA3")
    assert result["holdings"] == {"BBB3": 2000}
    assert result["cash"] == 2000
    assert result["return"] == pytest.approx(1.8)


def test_protected_period_uses_ex_date_and_open_start():
    protection = {"AAA3": [("2024-06-28", "2025-06-30", 2024)]}
    assert maintenance.protected(protection, "AAA3", "2024-06-28") == []
    assert maintenance.protected(protection, "AAA3", "2025-06-30") == [2024]
    assert maintenance.protected(protection, "AAA3", "2025-07-01") == []


def test_comparison_rejects_duplicate_scenario_even_if_count_matches():
    with pytest.raises(RuntimeError):
        comparison.expected_set([{"year": "2020"}, {"year": "2020"}], ("year",),
                                {("2020",), ("2021",)}, "fixture")


@pytest.mark.parametrize("bad", ["", "nan", "inf"])
def test_comparison_rejects_missing_or_nonfinite_returns(bad):
    with pytest.raises(RuntimeError):
        comparison.val(bad, "fixture")


def test_documentary_audit_does_not_hide_an_extra_tranche():
    rows = [{"ticker":"UNIP3","date":"2025-12-05","date_basis":"com",
             "kind":"CASH_DIVIDEND","amount":v} for v in (.40579937466,5.48220258487)]
    events = [{"asset":"UNIP3","kind":"CASH","record_date":"2025-12-05",
               "date":"2025-12-08","amount":.40579937466,"event_id":"one"}]
    result = sources.reconcile_cash(rows,events)
    assert [r["status"] for r in result] == ["VALOR_DATA_PRESENTES","AUSENTE_NO_MOTOR"]


def test_documentary_audit_flags_capital_repayments_for_economic_review():
    row = {"ticker":"SYNE3","date":"2025-09-18","date_basis":"ex",
           "kind":"CAPITAL_REDUCTION","amount":2.1618867296481}
    assert sources.reconcile_cash([row],[])[0]["status"] == "TRATAMENTO_ECONOMICO_PENDENTE"


def test_documentary_audit_flags_repeated_table_row():
    row = {"ticker":"ITSA3","date":"2025-02-28","date_basis":"com","kind":"JCP","amount":.0235295}
    result = sources.reconcile_cash([row,row],[])
    assert result[1]["status"] == "REPETICAO_TABELA_RI_REVISAR"


@pytest.mark.parametrize("policy", ["KEEP_CASH", "REINVEST"])
def test_documented_amendments_preserve_distinct_cash_and_do_not_mutate_baseline(policy):
    calendar = ["2024-12-06","2024-12-09","2024-12-10","2025-12-05","2025-12-08","2025-12-12","2025-12-15"]
    book = maintenance.bridge.PriceBook({},calendar)
    events = [maintenance.Event("guess","2024-12-10","SPLIT","SYNE3","DETECTED",factor=2),
              maintenance.Event("unip","2025-12-08","CASH","UNIP3","B3",record_date="2025-12-05",amount=.40579937466),
              maintenance.Event("syn","2025-12-15","CASH","SYNE3","B3",record_date="2025-12-12",amount=.0585805792)]
    evidence = [{"ticker":t,"kind":k,"date":d,"date_basis":b,"amount":a,
                 "source_url":"https://example.test/official","payment_date":"2025-12-19","evidence_id":str(i)}
                for i,(t,k,d,b,a) in enumerate([
                    ("SYNE3","CAPITAL_REDUCTION","2024-12-09","ex",3.66865626849375),
                    ("UNIP3","CASH_DIVIDEND","2025-12-05","com",5.48220258487),
                    ("SYNE3","CASH_DIVIDEND","2025-12-15","ex",.419275002113572)])]
    revised,audit = documented_events(events,evidence,book,policy)
    assert len(events) == 3 and events[0].kind == "SPLIT"
    assert len(revised) == 4 and all(e.kind == "CASH" for e in revised)
    assert sorted(e.amount for e in revised if e.asset == "UNIP3") == [.40579937466,5.48220258487]
    capital = next(e for e in revised if e.date == "2024-12-09")
    assert capital.reinvest == ("KEEP_CASH" if policy == "KEEP_CASH" else "")
    assert {r["action"] for r in audit} == {"REMOVE","ADD","REPLACE"}


def test_documented_amendments_reject_unknown_policy():
    with pytest.raises(ValueError):
        documented_events([],[],None,"UNKNOWN")
