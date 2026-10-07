#!/usr/bin/env python3
"""Sell documented ITSA3 rights and reinvest after D+2, using the original v6 engine.

The cash-flow adapter maps the proven sale proceeds to a dated CASH event at
reinvestment. It does not value untraded rights or unsettled receivables. Only
post-settlement June endpoints are reported; do not use its interim NAV for risk.
Entitlements are integer, so simulations use actual allocated capital and renewal
rolls the actual wealth forward, rather than chaining fixed-capital annual returns.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import zipfile
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from scripts import graham_corrected_maintenance_v11 as m
from scripts.audit_graham_v11_sources import digest
from motor_eventos import MissingData

CAPITAL = 10000.0
RULES = ("R00", "R03", "R16")
SETTLEMENT_SOURCE = "https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/direitos-de-subscricao.htm"
TIMING_SOURCE = "https://www.b3.com.br/lumis/portal/file/fileDownload.jsp?fileId=8AE490CA6F165E34016F19E813424E03"


def parse_quote(line):
    if line[:2] != b"01":
        return None
    factor = int(line[210:217])
    if factor <= 0:
        raise ValueError("Nonpositive COTAHIST quotation factor")
    day = line[2:10].decode()
    return {"date": f"{day[:4]}-{day[4:6]}-{day[6:]}",
            "ticker": line[12:24].decode().strip(), "market": line[24:27].decode(),
            "specification": line[39:49].decode().strip(), "isin": line[230:242].decode().strip(),
            "close": int(line[108:121]) / 100 / factor,
            "trades": int(line[147:152]), "quantity": int(line[152:170]),
            "volume": int(line[170:188]) / 100, "quotation_factor": factor,
            "record_sha256": hashlib.sha256(line).hexdigest()}


def traded(row):
    return row["trades"] > 0 and row["quantity"] > 0 and row["volume"] > 0 and row["close"] > 0


def collect_quotes(raw_dir, events):
    quotes, archives = [], []
    names = {b"ITSA1", b"ITSA1F", b"ITSA3"}
    for year in sorted({int(e["record_date"][:4]) for e in events}):
        path = raw_dir / f"COTAHIST_A{year}.ZIP"
        archive_hash = digest(path)
        archives.append({"file": path.name, "sha256": archive_hash, "bytes": path.stat().st_size,
                         "source_url": f"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/{path.name}",
                         "provenance": "preexisting local B3 archive; no independent redownload"})
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if member.endswith("/"):
                    continue
                with archive.open(member) as handle:
                    for number, line in enumerate(handle, 1):
                        if line[:2] != b"01" or line[12:24].strip() not in names or line[24:27] not in (b"010", b"020"):
                            continue
                        row = parse_quote(line)
                        row.update(file=path.name, member=member, line=number, file_sha256=archive_hash)
                        quotes.append(row)
        print(f"Rights evidence: COTAHIST {year} read", flush=True)
    return quotes, archives


def execution_evidence(event, quotes, book):
    """Missing/ambiguous evidence blocks this event, never supplies a guessed price."""
    if not event.get("source_url") or not event.get("source_sha256") or event.get("share_class") != "ON":
        raise ValueError("Unverified entitlement source or class")
    if not Decimal(event["rights_per_share"]).is_finite() or not 0 < Decimal(event["rights_per_share"]) < 1:
        raise ValueError("Unverified entitlement ratio")
    candidates = [r for r in quotes if r["ticker"] == event["fractional_ticker"]
                  and r["market"] == "020" and r["isin"] == event["rights_isin"]
                  and r["specification"].startswith("DIR ORD") and traded(r)
                  and event["available_from"] <= r["date"] <= event["exercise_deadline_issuer"]]
    if not candidates:
        raise ValueError("No proven, negotiable ON-right trade within documentary window")
    first = min(r["date"] for r in candidates)
    sales = [r for r in candidates if r["date"] == first]
    if len(sales) != 1:
        raise ValueError("Ambiguous first-session rights quote")
    settlement = book.next_session(book.next_session(first))
    buys = [r for r in quotes if r["ticker"] == event["parent"] and r["market"] == "010"
            and r["date"] >= settlement and traded(r)]
    if not buys:
        raise ValueError("No proven ITSA3 quote after settlement")
    buydate = min(r["date"] for r in buys)
    buys = [r for r in buys if r["date"] == buydate]
    if len(buys) != 1 or not math.isclose(book.exact(event["parent"], buydate), buys[0]["close"], abs_tol=1e-10):
        raise ValueError("Ambiguous or divergent reinvestment quote")
    return dict(event, sale_date=first, sale_price=sales[0]["close"], sale_quote=sales[0],
                settlement_date=settlement, reinvest_date=buydate, reinvest_price=buys[0]["close"],
                reinvest_quote=buys[0], settlement_source=SETTLEMENT_SOURCE, timing_source=TIMING_SOURCE,
                status="DOCUMENTED_SIMULATION_INPUT")


def integer_rights(quantity, ratio):
    return int((Decimal(str(quantity)) * Decimal(ratio)).to_integral_value(rounding=ROUND_FLOOR))


def simulate(book, events, coverage, start, end, weights, capital, rights):
    engine = m.Engine(book, events, coverage)
    state = engine.initialize(start, weights, capital=capital)
    audit = []
    for right in sorted(rights, key=lambda r: r["record_date"]):
        if not start <= right["record_date"] < right["reinvest_date"] <= end:
            continue
        engine.advance(state, right["record_date"])
        q = state.snapshots[right["record_date"]].get("ITSA3", 0.0)
        n = integer_rights(q, right["rights_per_share"])
        # All studied allocations are below one standard lot. Do not extrapolate
        # a fractional-market close to an unreviewed large trade.
        if n >= 100 or n > right["sale_quote"]["quantity"]:
            raise ValueError("Rights size outside verified fractional-market execution scope")
        proceeds = n * right["sale_price"]
        event_id = right["event_id"] + "_SALE_PROCEEDS"
        if n:
            cash = m.Event(event_id, right["reinvest_date"], "CASH", "ITSA3", right["source_url"],
                           record_date=right["record_date"], amount=proceeds / q, reinvest="ITSA3",
                           note=f"Rights sale, NOT dividend. {n} {right['fractional_ticker']} sold {right['sale_date']}; "
                                f"D+2 settlement {right['settlement_date']}; cash-flow adapter; no external cash")
            engine = m.Engine(book, engine.events + [cash], coverage)
        if q:
            audit.append({"event_id": event_id, "record_date": right["record_date"], "eligible_itsa3": q,
                          "rights_per_share": right["rights_per_share"], "rights_sold": n,
                          "fraction_discarded": float(Decimal(str(q)) * Decimal(right["rights_per_share"])) - n,
                          "ticker_sold": right["fractional_ticker"], "sale_date": right["sale_date"],
                          "sale_price": right["sale_price"], "gross_proceeds": proceeds,
                          "costs": 0.0, "taxes": 0.0, "net_proceeds": proceeds,
                          "settlement_date": right["settlement_date"], "reinvest_date": right["reinvest_date"],
                          "reinvest_price": right["reinvest_price"], "itsa3_bought": proceeds / right["reinvest_price"],
                          "source_url": right["source_url"]})
    engine.advance(state, end)
    for row in audit:
        if not row["rights_sold"]:
            continue
        ledger = [r for r in state.ledger if r["event_id"] == row["event_id"]]
        assert len(ledger) == 1
        assert math.isclose(ledger[0]["details"]["cash_credit"], row["net_proceeds"], abs_tol=1e-9)
        assert math.isclose(ledger[0]["details"]["shares_bought"], row["itsa3_bought"], abs_tol=1e-9)
    return state, engine.result(state, require_complete=False), audit


def weights_for(spec, rule):
    if rule == "R16":
        return m.selections_source.sector_weights(spec["R03"], spec["sectors"])
    return m.selections_source.equal_weights(spec[rule])


def dump(out, name, rows, fields=None):
    m.write_csv(out / name, rows, fields or list(rows[0]))


def main(raw_dir, out):
    if out.exists():
        raise FileExistsError(f"Choose a new output destination: {out}")
    work = Path("graham_v6_event_results")
    baseline_dir = work / "manutencao_documental_v11_1"
    event_file = baseline_dir / "eventos_utilizados.json"
    events = [m.Event(**r) for r in json.loads(event_file.read_text())]
    facts_path = Path("research/graham_v6_comparison/itsa_rights_verified_2026_10_07.json")
    facts = json.loads(facts_path.read_text())
    book, _, coverage = m.bridge.load_legacy()
    selections = m.selections_source.load_corrected()
    tickers = {t for s in selections.values() for t in s["R00"] + s["R03"]}
    tickers |= {e.asset for e in events} | {a for e in events for a, _ in e.legs}
    book = m.bridge.expand_with_sqlite(book, tickers | {"BOVA11"})
    quotes, archives = collect_quotes(raw_dir, facts)
    rights, pending = [], []
    for fact in facts:
        try:
            rights.append(execution_evidence(fact, quotes, book))
        except (ValueError, MissingData) as exc:
            pending.append({"event_id": fact["event_id"], "status": "PENDING_DOCUMENTARY_EVIDENCE", "reason": str(exc)})
    base_cohorts = {(int(r["start_year"]), r["rule"]): r for r in m.read_csv(baseline_dir / "graham_18_coortes.csv")}
    annual_ref = {int(r["year"]): r for r in m.read_csv(work / "graham_corrigido_anuais_eventos.csv")}
    cohorts, positions, finals, paths, annuals, impact, ledger, checks, renewal_paths = [], [], [], [], [], [], [], [], []
    event_impacts = []
    for year, (start, first_end) in m.bridge.WINDOWS.items():
        annual_row = dict(year=year, start=start, end=first_end, BOVA11=annual_ref[year]["BOVA11"])
        for rule in RULES:
            w = weights_for(selections[year], rule)
            first_state, first_result, _ = simulate(book, events, coverage, start, first_end, w, CAPITAL, rights)
            annual_row[rule] = first_result["return"]
            _, first_old, _ = simulate(book, events, coverage, start, first_end, w, CAPITAL, [])
            assert math.isclose(first_old["return"], float(annual_ref[year][rule]), abs_tol=1e-8)
            state, result, audit = simulate(book, events, coverage, start, m.END, w, CAPITAL, rights)
            _, old, _ = simulate(book, events, coverage, start, m.END, w, CAPITAL, [])
            assert math.isclose(old["return"], float(base_cohorts[(year, rule)]["maintain_return"]), abs_tol=1e-8)
            ledger.extend(dict(mechanism="maintain", start_year=year, rule=rule, **r) for r in audit)
            navs = {r["date"]: r for r in state.nav}
            previous = CAPITAL
            for period in range(year, 2026):
                day = m.bridge.WINDOWS[period][1]
                nav = navs[day]["nav"]
                paths.append(dict(start_year=year, rule=rule, period_year=period, end=day,
                                  nav=nav, cash=navs[day]["cash"], period_return=nav/previous-1,
                                  cumulative_return=nav/CAPITAL-1))
                previous = nav
            assert math.isclose(navs[first_end]["nav"]/CAPITAL-1, first_result["return"], abs_tol=1e-9)
            checks.append(dict(start_year=year, rule=rule, old_reference="OK", first_year_v11_2="OK"))
            contribution = 0.0
            allocated = defaultdict(float)
            for ticker, weight in sorted(w.items()):
                pos, r, _ = simulate(book, events, coverage, start, m.END, {ticker: 1.0}, CAPITAL*weight, rights)
                _, before, _ = simulate(book, events, coverage, start, m.END, {ticker: 1.0}, CAPITAL*weight, [])
                contribution += weight*r["return"]
                allocated["CASH"] += r["cash"]
                for t, q in r["holdings"].items():
                    allocated[t] += q
                positions.append(dict(start_year=year, rule=rule, ticker=ticker, weight=weight,
                                      initial_capital_allocated=CAPITAL*weight, return_before=before["return"],
                                      **{"return": r["return"]}, contribution=weight*r["return"],
                                      asset_delta_pp=100*(r["return"]-before["return"]),
                                      portfolio_delta_pp=100*weight*(r["return"]-before["return"]),
                                      cash_final_allocated=r["cash"], final_assets_allocated=json.dumps(r["holdings"], sort_keys=True),
                                      status="PROVISIONAL_RIGHTS_MONETIZED"))
                if ticker == "ITSA3":
                    previous_rights_return = before["return"]
                    for i, right in enumerate(rights):
                        _, marginal, _ = simulate(book, events, coverage, start, m.END,
                                                  {ticker: 1.0}, CAPITAL*weight, rights[:i+1])
                        delta = marginal["return"] - previous_rights_return
                        event_impacts.append(dict(start_year=year, rule=rule, ticker=ticker,
                                                  event_id=right["event_id"], weight=weight,
                                                  initial_capital_allocated=CAPITAL*weight,
                                                  asset_delta_pp=100*delta, portfolio_delta_pp=100*weight*delta,
                                                  final_wealth_delta=CAPITAL*weight*delta,
                                                  attribution="sequential: 2023 versus none; 2025 after 2023"))
                        previous_rights_return = marginal["return"]
                    assert math.isclose(previous_rights_return, r["return"], abs_tol=1e-9)
            assert math.isclose(contribution, result["return"], abs_tol=1e-9)
            for ticker, quantity in dict(state.holdings, CASH=state.cash).items():
                assert math.isclose(allocated.pop(ticker, 0), quantity, abs_tol=1e-8)
                price = 1.0 if ticker == "CASH" else book.exact(ticker, m.END)
                finals.append(dict(start_year=year, rule=rule, asset=ticker, quantity=quantity,
                                   price=price, value=quantity*price, final_weight=quantity*price/result["final_value"]))
            assert not allocated
            # Integer rights break scale invariance: carry actual capital into
            # each renewal year, using the same selections, not normalized factors.
            capital = CAPITAL
            for period in range(year, 2026):
                a, b = m.bridge.WINDOWS[period]
                pw = weights_for(selections[period], rule)
                _, rr, aa = simulate(book, events, coverage, a, b, pw, capital, rights)
                renewal_paths.append(dict(start_year=year, rule=rule, period_year=period,
                                          start=a, end=b, initial_value=capital, final_value=rr["final_value"],
                                          period_return=rr["return"]))
                ledger.extend(dict(mechanism="renew", start_year=year, rule=rule, period_year=period, **r) for r in aa)
                capital = rr["final_value"]
            renew = capital/CAPITAL-1
            duration = (date.fromisoformat(m.END)-date.fromisoformat(start)).days/365.25
            old_renew = float(base_cohorts[(year, rule)]["renew_return"])
            cohorts.append(dict(start_year=year, rule=rule, start=start, end=m.END, n=len(w),
                                maintain_return=result["return"], maintain_cagr=(1+result["return"])**(1/duration)-1,
                                renew_return=renew, renew_cagr=(1+renew)**(1/duration)-1,
                                renew_minus_maintain_pp=100*(renew-result["return"]),
                                bova_return=book.exact("BOVA11", m.END)/book.exact("BOVA11", start)-1,
                                multiasset_delta=result["return"]-contribution, status="PROVISIONAL_RIGHTS_MONETIZED"))
            for mechanism, before, after in [("maintain", old["return"], result["return"]), ("renew", old_renew, renew)]:
                impact.append(dict(start_year=year, rule=rule, mechanism=mechanism,
                                   without_rights=before, with_rights=after, delta_pp=100*(after-before)))
            print(f"{year} {rule}: maintain {result['return']:+.8%}; rights {100*(result['return']-old['return']):+.6f} pp", flush=True)
        annuals.append(annual_row)
    assert len(cohorts) == 18 and len(positions) == 162 and len(paths) == 63 and len(renewal_paths) == 63
    comparison = m.read_csv(work / "comparacao_documental_v11_1/comparacao_72_cenarios.csv")
    index = {(r["start_year"], r["rule"]): r for r in cohorts}
    for row in comparison:
        if row["family"] != "Graham":
            continue
        r = index[(int(row["start_year"]), row["strategy"])]
        for key, src in [("maintain", "maintain_return"), ("renew", "renew_return"),
                         ("maintain_cagr", "maintain_cagr"), ("renew_cagr", "renew_cagr"),
                         ("renew_minus_maintain_pp", "renew_minus_maintain_pp")]:
            row[key] = r[src]
        row["status"] = "PROVISORIO_V11_2_DIREITOS_INTEIROS"
    out.mkdir(parents=True)
    for name, rows in [("graham_18_coortes.csv", cohorts), ("graham_posicoes.csv", positions),
                       ("posicoes_finais_carteira.csv", finals), ("trajetoria_anual_manutencao.csv", paths),
                       ("trajetoria_renovacao_capital_efetivo.csv", renewal_paths), ("anuais_capital_10000.csv", annuals),
                       ("impacto_direitos_36_resultados.csv", impact), ("operacoes_direitos.csv", ledger),
                       ("impacto_por_evento_manutencao.csv", event_impacts),
                       ("paridade_primeiro_ano.csv", checks), ("comparacao_72_cenarios.csv", comparison)]:
        dump(out, name, rows, list(dict.fromkeys(k for r in rows for k in r)))
    dump(out, "erros_execucao.csv", [], ["status", "detail"])
    dump(out, "pendencias_direitos.csv", pending, ["event_id", "status", "reason"])
    selected_quotes = [r for r in quotes if r["ticker"] in ("ITSA1", "ITSA1F")]
    selected_quotes += [r["reinvest_quote"] for r in rights]
    dump(out, "cotacoes_B3_direitos.csv", selected_quotes)
    manifest = {"method_version": "v11.2_rights_integer", "certified": False,
                "rights_evidence": rights, "pending_rights": pending, "raw_archives": archives,
                "fact_file_sha256": digest(facts_path), "baseline_events_sha256": digest(event_file),
                "baseline_preserved": str(baseline_dir), "engine_unchanged_sha256": digest(Path("graham_v6_event_bridge/motor_eventos.py")),
                "capital": CAPITAL, "cohorts": 18, "positions": 162, "comparison_rows": 72,
                "first_year_parity": "18/18", "baseline_v11_1_parity": "18/18",
                "renewal": "actual wealth rolled forward; do not chain normalized annual returns with integer entitlements",
                "execution": "First traded fractional-right session close; D+2, reinvest at ITSA3 close on first quoted session on/after settlement",
                "operating_assumption": "Normal D+2 settlement and participant credit before the closing trade; B3 clearing credits by 15:50; no margin, costs or taxes",
                "units": "Only rights entitlements are truncated per issuer notice; original fractional ITSA3 index units are retained",
                "nav_limitation": "Adapter posts sale cash only at reinvestment; no valuation of rights/receivables between ex-date and settlement; June endpoints unaffected",
                "user_authorization": "Sell first proven trade and reinvest after settlement; preserve no-monetization sensitivity"}
    (out/"manifesto_direitos.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({"cohorts": 18, "positions": 162, "rights_documented": len(rights), "rights_pending": len(pending)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("graham_v6_event_results/direitos_itsa_v11_2"))
    args = parser.parse_args()
    main(args.raw_dir, args.out)
