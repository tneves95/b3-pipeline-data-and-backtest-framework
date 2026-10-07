#!/usr/bin/env python3
"""Quantify documented discrepancies using the SAME v6 engine, without replacing v11.

Scenarios are proposals for coordinator review, not new certified results.
No selection, annual reference, database, or engine file is edited.
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict, replace
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from scripts import graham_corrected_maintenance_v11 as maintenance

SYN_STRUCTURAL_SOURCES = {
    "2024-12-09": "https://api.mziq.com/mzfilemanager/v2/d/9ceaac6b-8c40-4396-9c2d-44bd2d41ef3e/a49ef94c-4c46-8535-8039-a6382fc769c0?origin=1",
    "2025-09-18": "https://api.mziq.com/mzfilemanager/v2/d/9ceaac6b-8c40-4396-9c2d-44bd2d41ef3e/59c6fc07-5e89-271e-4618-ce94371d4b8f?origin=1",
}


def documented_events(baseline, evidence, book, capital_policy):
    if capital_policy not in ("KEEP_CASH", "REINVEST"):
        raise ValueError("Invalid capital policy")
    events = list(baseline)
    audit = []
    guessed = [e for e in events if e.asset == "SYNE3" and e.kind == "SPLIT"
               and e.date == "2024-12-10" and e.source == "DETECTED"]
    if len(guessed) != 1:
        raise RuntimeError("Expected one original detected SYNE3 split")
    events.remove(guessed[0])
    audit.append(dict(action="REMOVE", event_id=guessed[0].event_id, asset="SYNE3", date="2024-12-10",
                      old_value=2, new_value="", source=SYN_STRUCTURAL_SOURCES["2024-12-09"],
                      reason="Capital repayment without cancellation; detected price jump is not proof of split"))
    for row in evidence:
        ticker, kind, day, amount = row["ticker"], row["kind"], row["date"], float(row["amount"])
        if ticker not in ("UNIP3", "SYNE3"):
            continue
        exdate = day if row["date_basis"] == "ex" else book.next_session(day)
        dc = book.previous_session(exdate) if row["date_basis"] == "ex" else day
        same = [e for e in events if e.asset == ticker and e.kind == "CASH" and e.date == exdate]
        if any(math.isclose(e.amount, amount, rel_tol=5e-6, abs_tol=5e-7) for e in same):
            continue
        if ticker == "UNIP3" and day not in ("2024-11-19", "2025-08-12", "2025-12-05"):
            raise RuntimeError(f"Unreviewed Unipar discrepancy: {row}")
        source = row["source_url"]
        if kind == "CAPITAL_REDUCTION":
            source += " ; " + SYN_STRUCTURAL_SOURCES[day]
        event = maintenance.Event("documentary_" + row["evidence_id"], exdate, "CASH", ticker,
                                  source, record_date=dc, amount=amount,
                                  reinvest="KEEP_CASH" if kind == "CAPITAL_REDUCTION" and capital_policy == "KEEP_CASH" else "",
                                  note=f"{kind}; payment={row['payment_date']}; scenario={capital_policy}; not certified")
        if ticker == "SYNE3" and day == "2025-12-15":
            if len(same) != 1:
                raise RuntimeError("Ambiguous SYN dividend replacement")
            events.remove(same[0])
            audit.append(dict(action="REPLACE", event_id=same[0].event_id, asset=ticker, date=exdate,
                              old_value=same[0].amount, new_value=amount, source=source,
                              reason="Nominal RI dividend differs from local B3 cash value"))
        else:
            audit.append(dict(action="ADD", event_id=event.event_id, asset=ticker, date=exdate,
                              old_value="", new_value=amount, source=source,
                              reason="Distinct documented tranche" if kind != "CAPITAL_REDUCTION" else "Capital repayment scenario"))
        events.append(event)
    return events, audit


def main():
    root = Path.cwd()
    work = root / "graham_v6_event_results"
    out = work / "sensibilidade_documental_v11"
    baseline = [maintenance.Event(**e) for e in json.loads(
        (work / "manutencao_corrigida_v11/eventos_utilizados.json").read_text())]
    evidence = maintenance.read_csv(root / "research/graham_v6_comparison/ri_events_verified_2026_10_07.csv")
    book, _, coverage = maintenance.bridge.load_legacy()
    selected = maintenance.selections_source.load_corrected()
    names = {t for s in selected.values() for t in s["R03"] + s["R00"]}
    names |= {e.asset for e in baseline} | {a for e in baseline for a, _ in e.legs}
    book = maintenance.bridge.expand_with_sqlite(book, names | {"BOVA11"})
    reference = {(r["start_year"],r["rule"]): float(r["maintain_return"]) for r in maintenance.read_csv(
        work / "manutencao_corrigida_v11/graham_18_coortes.csv")}
    annual = {int(r["year"]): r for r in maintenance.read_csv(work / "graham_corrigido_anuais_eventos.csv")}
    records, positions, amendments, checks = [], [], [], []
    out.mkdir(parents=True, exist_ok=True)
    for policy in ("KEEP_CASH", "REINVEST"):
        events, audit = documented_events(baseline, evidence, book, policy)
        amendments.extend(dict(scenario=policy, **r) for r in audit)
        engine = maintenance.Engine(book, events, coverage)
        for year, spec in selected.items():
            start, first_end = maintenance.bridge.WINDOWS[year]
            weights = {"R00": maintenance.selections_source.equal_weights(spec["R00"]),
                       "R03": maintenance.selections_source.equal_weights(spec["R03"]),
                       "R16": maintenance.selections_source.sector_weights(spec["R03"],spec["sectors"])}
            for rule, w in weights.items():
                state = engine.initialize(start, w)
                engine.advance(state, first_end)
                first = engine.result(state, require_complete=False)["return"]
                if not math.isclose(first, float(annual[year][rule]), abs_tol=1e-8, rel_tol=1e-9):
                    raise RuntimeError(f"Annual result changed: {year}/{rule}")
                checks.append(dict(scenario=policy, year=year, rule=rule, status="OK"))
                engine.advance(state, maintenance.END)
                result = engine.result(state, require_complete=False)
                pieces = []
                for ticker, weight in w.items():
                    pos = maintenance.safe_result(engine,start,maintenance.END,ticker)
                    pieces.append(weight*pos["return"])
                    positions.append(dict(scenario=policy,start_year=year,rule=rule,ticker=ticker,
                        initial_weight=weight,asset_return=pos["return"],contribution=weight*pos["return"],
                        cash_allocated=weight*pos["cash"],final_assets_allocated=json.dumps(
                            {t:q*weight for t,q in pos["holdings"].items()},sort_keys=True)))
                if not math.isclose(sum(pieces),result["return"],abs_tol=1e-8,rel_tol=1e-10):
                    raise RuntimeError("Position contribution mismatch")
                old = reference[(str(year),rule)]
                records.append(dict(scenario=policy,start_year=year,rule=rule,start=start,end=maintenance.END,
                    baseline_return=old,scenario_return=result["return"],delta_pp=100*(result["return"]-old),
                    cash_final=result["cash"],status="PROPOSTA_DOCUMENTAL_NAO_CERTIFICADA"))
        (out / ("eventos_"+policy+".json")).write_text(json.dumps([asdict(e) for e in events],ensure_ascii=False,indent=2))
    for name, rows in [("coortes_36_cenarios.csv",records),("posicoes_324_cenarios.csv",positions),
                       ("alteracoes_rastreaveis.csv",amendments),("paridade_anual_36.csv",checks)]:
        maintenance.write_csv(out/name,rows,list(rows[0]))
    summary = {"certified":False,"annual_parity":"36/36","cohorts":36,"positions":len(positions),
               "choices_for_coordinator":["Destino das restituições de capital: manter caixa ou reinvestir na data-ex",
                  "Direitos de subscrição ITSA3 de 2023 e 2025 ainda sem política/valorização"],
               "unchanged":"Motor, seleção, referência anual e execução v11 preservados"}
    (out/"manifesto.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False))
    for r in records:
        if abs(r["delta_pp"])>1e-8: print(r)


if __name__ == "__main__":
    main()
