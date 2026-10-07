#!/usr/bin/env python3
"""Graham corrigido: manutenção sem rebalancear, por eventos, até 30/06/2026.

Usar na raiz do Codespaces:
    python scripts/graham_corrected_maintenance_v11.py

Lê o motor v6, as seleções corrigidas e o banco local. NÃO altera o SQLite,
os eventos CSV, a seleção Graham ou os resultados v10 de renovação anual.
Os eventos B3 não conciliados são suplementação PROVISÓRIA; NÃO promovem
qualquer período a RECONCILED. Registra explicitamente lacunas e conflitos.
"""
from __future__ import annotations

import csv
import argparse
import hashlib
import json
import math
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from dataclasses import asdict
from pathlib import Path

ROOT = Path.cwd()
END = "2026-06-30"
sys.path.insert(0, str(ROOT))
from graham_v6_event_bridge import graham_event_resume as bridge  # noqa: E402
import graham_recalc_returns_2020_2026 as selections_source  # noqa: E402

# The bridge loads motor_eventos as a top-level module. Loading it again via
# the package path creates distinct MissingData classes: Engine.value would
# then fail to catch PriceBook.exact's exception on an untraded interim day.
# Reuse the very same engine/types as the bridge, without changing v6.
Engine, Event = bridge.Engine, bridge.Event


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        wr = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)


def audit_row(ticker, com, kind, amount, source, status, detail=""):
    return {"ticker": ticker, "date_com": com, "kind": kind, "amount_or_multiplier": amount,
            "source": source, "status": status, "detail": detail}


def event_key(ticker, com, typ, amount):
    return (ticker, com, typ, round(float(amount), 11))


def build_protected_periods(sels):
    protection = defaultdict(list)
    for year, spec in sels.items():
        start, end = bridge.WINDOWS[year]
        for ticker in set(spec["R00"]) | set(spec["R03"]):
            protection[ticker].append((start, end, year))
    return protection


def protected(protection, ticker, exdate):
    return [year for start, end, year in protection.get(ticker, ())
            if start < exdate <= end]


def supplement_b3(con, calendar, tickers, existing, protection):
    """Usa linhas históricas SQLite apenas em intervalos fora dos anos já fechados.

    Para datas com pagamento já contabilizado, NÃO assume que um segundo
    valor diferente seja uma tranche adicional: coloca em revisão documental.
    Para eventos em ano já fechado pelo v10, registra possível lacuna sem
    alterar o resultado anual certificado pelo teste de paridade.
    """
    extra = []
    audit = []
    alerts = []
    duplicates = set()
    existing_cash = defaultdict(list)
    existing_stock = defaultdict(list)
    for e in existing:
        if e.kind == "CASH":
            dc = e.record_date or e.date
            existing_cash[(e.asset, dc)].append(e)
        if e.kind in {"BONUS", "SPLIT"}:
            existing_stock[(e.asset, e.date, e.kind)].append(e)

    for ticker in sorted(tickers):
        isins = [r[0] for r in con.execute(
            "SELECT DISTINCT isin_code FROM prices WHERE ticker=? "
            "AND date BETWEEN '2020-06-30' AND ? AND isin_code IS NOT NULL",
            (ticker, END)) if r[0]]
        if not isins:
            audit.append(audit_row(ticker, "", "IDENTIDADE", "", "SQLite",
                                   "SEM_ISIN_SQLITE", "Usar prova da base v6/sucessor"))
            continue
        marks = ",".join("?" * len(isins))
        money = con.execute(
            f"SELECT isin_code,event_date,event_type,value,source FROM corporate_actions "
            f"WHERE isin_code IN ({marks}) AND event_date>? AND event_date<=? "
            "AND event_type IN ('CASH_DIVIDEND','JCP') ORDER BY event_date,event_type,value",
            isins + ["2020-06-30", END]).fetchall()
        for isin, dc, typ, raw, source in money:
            try:
                amount = float(raw)
            except (TypeError, ValueError):
                continue
            if amount <= 0 or not math.isfinite(amount):
                alerts.append(audit_row(ticker, dc, typ, raw, source, "VALOR_INVALIDO"))
                continue
            k = event_key(ticker, dc, typ, amount)
            if k in duplicates:
                audit.append(audit_row(ticker, dc, typ, amount, source, "REPETICAO_IDENTICA_B3"))
                continue
            duplicates.add(k)
            exdate = bridge.next_trade(calendar, dc)
            if exdate is None or exdate > END:
                audit.append(audit_row(ticker, dc, typ, amount, source, "EX_FORA_DO_CORTE"))
                continue
            same = existing_cash.get((ticker, dc), [])
            if any(math.isclose(e.amount, amount, rel_tol=5e-6, abs_tol=5e-7)
                   for e in same):
                audit.append(audit_row(ticker, dc, typ, amount, source, "PRESENTE_NO_MOTOR"))
                continue
            if same:
                # Proventos múltiplos na mesma data podem ser legítimos;
                # sem documento individual, duplicação não pode ser presumida.
                row = audit_row(ticker, dc, typ, amount, source,
                                "TRANCHE_OU_DIVERGENCIA_REVISAR",
                                f"Já há {len(same)} pagamento(s) nesta data-com")
                alerts.append(row)
                audit.append(row)
                continue
            years = protected(protection, ticker, exdate)
            if years:
                row = audit_row(ticker, dc, typ, amount, source,
                                "LACUNA_POTENCIAL_ANUAL_V10",
                                "Ano(s) corrigido(s): " + ",".join(map(str, years)))
                alerts.append(row)
                audit.append(row)
                continue
            eid = "maintenance_b3_" + hashlib.sha256("|".join(map(str, k)).encode()).hexdigest()[:22]
            new = Event(eid, exdate, "CASH", ticker, source or "B3_SQLITE",
                        record_date=dc, amount=amount,
                        note=f"Complemento manutenção fora das janelas anuais; tipo={typ}; ISIN={isin}")
            extra.append(new)
            existing_cash[(ticker, dc)].append(new)
            audit.append(audit_row(ticker, dc, typ, amount, source, "ADICIONADO_MANTER_PROVISORIO"))
        stock = con.execute(
            f"SELECT isin_code,ex_date,action_type,factor,source FROM stock_actions "
            f"WHERE isin_code IN ({marks}) AND ex_date>? AND ex_date<=? "
            "ORDER BY ex_date,action_type,factor",
            isins + ["2020-06-30", END]).fetchall()
        for isin, dc, typ, raw, source in stock:
            mapping = {
                "BONUS_SHARES": "BONUS", "STOCK_SPLIT": "SPLIT",
                "REVERSE_SPLIT": "SPLIT", "SPLIT": "SPLIT",
            }
            kind = mapping.get(typ)
            if not kind:
                row = audit_row(ticker, dc, typ, raw, source, "ESTRUTURA_DESCONHECIDA")
                alerts.append(row); audit.append(row)
                continue
            try:
                val = float(raw)
                mult = (1 + val / 100) if kind == "BONUS" else val
            except (TypeError, ValueError):
                mult = float("nan")
            if not math.isfinite(mult) or mult <= 0:
                row = audit_row(ticker, dc, typ, raw, source, "FATOR_INVALIDO")
                alerts.append(row); audit.append(row)
                continue
            k = event_key(ticker, dc, typ, mult)
            if k in duplicates:
                audit.append(audit_row(ticker, dc, typ, mult, source, "REPETICAO_IDENTICA_B3"))
                continue
            duplicates.add(k)
            exdate = bridge.next_trade(calendar, dc)
            if exdate is None or exdate > END:
                audit.append(audit_row(ticker, dc, kind, mult, source, "EX_FORA_DO_CORTE"))
                continue
            same = existing_stock[(ticker, exdate, kind)]
            if any(math.isclose(e.factor, mult, rel_tol=1e-7, abs_tol=1e-8) for e in same):
                audit.append(audit_row(ticker, dc, kind, mult, source, "PRESENTE_NO_MOTOR"))
                continue
            if same:
                row = audit_row(ticker, dc, kind, mult, source,
                                "FATOR_ESTRUTURAL_DIVERGENTE_REVISAR",
                                f"Já há {len(same)} evento(s) desta classe")
                alerts.append(row); audit.append(row)
                continue
            years = protected(protection, ticker, exdate)
            if years:
                row = audit_row(ticker, dc, kind, mult, source,
                                "LACUNA_POTENCIAL_ANUAL_V10",
                                "Ano(s): " + ",".join(map(str, years)))
                alerts.append(row); audit.append(row)
                continue
            eid = "maintenance_stock_" + hashlib.sha256("|".join(map(str, k)).encode()).hexdigest()[:22]
            new = Event(eid, exdate, kind, ticker, source or "B3_SQLITE",
                        factor=mult, note=f"Data-com={dc}; tipo B3={typ}; ISIN={isin}; provisorio")
            extra.append(new)
            existing_stock[(ticker, exdate, kind)].append(new)
            audit.append(audit_row(ticker, dc, kind, mult, source, "ADICIONADO_MANTER_PROVISORIO"))
            if source != "B3":
                row = audit_row(ticker, dc, kind, mult, source,
                                "ESTRUTURA_ESTIMADA_SEM_DOCUMENTO",
                                "Preservada somente para reproduzir v11; origem não é documento B3. Ver cenário documental.")
                alerts.append(row)
                audit.append(row)

        unknown = con.execute(
            f"SELECT event_date,event_type,source FROM corporate_actions "
            f"WHERE isin_code IN ({marks}) AND event_date>? AND event_date<=? "
            "AND event_type NOT IN ('CASH_DIVIDEND','JCP',"
            "'BONUS_SHARES','STOCK_SPLIT','REVERSE_SPLIT','SPLIT')",
            isins + ["2020-06-30", END]).fetchall()
        for dc, typ, source in unknown:
            row = audit_row(ticker, dc, typ, "", source, "EVENTO_FORA_ESCOPO_VERIFICAR")
            audit.append(row)
            alerts.append(row)
    return extra, audit, alerts


def number(v, label):
    try:
        f = float(v)
    except (ValueError, TypeError):
        raise ValueError(f"{label}: valor inválido {v!r}")
    if not math.isfinite(f):
        raise ValueError(f"{label}: não finito {v!r}")
    return f


def safe_result(engine, date0, end, ticker):
    state = engine.initialize(date0, {ticker: 1.0})
    engine.advance(state, end)
    value = engine.result(state, require_complete=False)
    value["cash_out"] = state.cash
    value["events_applied"] = len([x for x in state.ledger if x.get("kind") != "BUY_INITIAL"])
    return value


def run(out=None, documentary_policy=None):
    suffix = "manutencao_documental_v11_1" if documentary_policy else "manutencao_corrigida_v11"
    out = out or ROOT / "graham_v6_event_results" / suffix
    input_dir = ROOT / "graham_v6_event_results"
    original_annual = read_csv(input_dir / "graham_corrigido_anuais_eventos.csv")
    assert len(original_annual) == 6 and {int(x["year"]) for x in original_annual} == set(bridge.WINDOWS)
    corrected = selections_source.load_corrected()

    book, legacy_events, coverage = bridge.load_legacy()
    parity = bridge.legacy_parity(book, legacy_events)
    if len(parity) != 18 or any(r["status"] != "OK" for r in parity):
        raise RuntimeError("Paridade v6 original diferente de 18/18: interrompido")
    pre_extra, pre_audit, pre_issues = bridge.load_extra_events(book.calendar, legacy_events)
    if pre_issues:
        raise RuntimeError(f"{len(pre_issues)} problemas na extração original: interrompido")
    selected = {t for s in corrected.values() for t in s["R03"] + s["R00"]}
    successors = {a for e in legacy_events for a, _ in e.legs}
    all_tickers = selected | successors | {e.asset for e in legacy_events + pre_extra}
    # A precedência de preço nominal da base v6 é preservada.
    extended_book = bridge.expand_with_sqlite(book, all_tickers | {"BOVA11"})
    protections = build_protected_periods(corrected)
    db = ROOT / "b3_market_data.sqlite"
    with sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True) as con:
        full_extra, b3_audit, alerts = supplement_b3(
            con, extended_book.calendar, selected | successors,
            legacy_events + pre_extra, protections
        )

    events = legacy_events + pre_extra + full_extra
    amendments = []
    if documentary_policy:
        from scripts.graham_v11_documentary_sensitivity import documented_events
        evidence = read_csv(ROOT / "research/graham_v6_comparison/ri_events_verified_2026_10_07.csv")
        events, amendments = documented_events(events, evidence, extended_book, documentary_policy)
        # This diagnosed source is removed explicitly in the amendment ledger.
        alerts = [r for r in alerts if not (r["ticker"] == "SYNE3" and
                  r["status"] == "ESTRUTURA_ESTIMADA_SEM_DOCUMENTO")]
    engine = Engine(extended_book, events, coverage)
    yearly = []
    holdings = []
    failures = []
    first_year_rows = []
    final_positions = []
    annual_path = []
    # Blindagem: primeiros 12 meses de manutenção devem ser exatamente a
    # mesma carteira/mesmos eventos da renovação anual já apurada na v10.
    first_year_ok = 0
    annual_lookup = {int(r["year"]): r for r in original_annual}
    for year, (start, first_end) in bridge.WINDOWS.items():
        s = corrected[year]
        weights = {
            "R00": selections_source.equal_weights(s["R00"]),
            "R03": selections_source.equal_weights(s["R03"]),
            "R16": selections_source.sector_weights(s["R03"], s["sectors"]),
        }
        for rule, w in weights.items():
            ref = number(annual_lookup[year][rule], f"v10 {year} {rule}")
            state_first = engine.initialize(start, w)
            engine.advance(state_first, first_end)
            got = engine.result(state_first, require_complete=False)["return"]
            if not math.isclose(got, ref, abs_tol=1e-8, rel_tol=1e-9):
                raise RuntimeError(
                    f"1º ano divergente: {year} {rule}; manutenção={got:.10f} vs v10={ref:.10f}"
                )
            first_year_ok += 1
            first_year_rows.append({"start_year": year, "rule": rule, "start": start,
                                   "end": first_end, "maintenance": got, "annual_v10": ref,
                                   "delta": got - ref, "status": "OK"})
            pieces = []
            for ticker, weight in sorted(w.items()):
                try:
                    res = safe_result(engine, start, END, ticker)
                except Exception as e:
                    failures.append({"year": year, "rule": rule, "ticker": ticker,
                                     "status": type(e).__name__, "detail": str(e)})
                    holdings.append({
                        "start_year": year, "rule": rule, "ticker": ticker,
                        "weight": weight, "return": "", "contribution": "",
                        "cash_final": "", "final_assets": "",
                        "gaps": "", "events_applied": "", "status": "INCOMPLETO"})
                    continue
                ret = res["return"]
                pieces.append(weight * ret)
                gaps = res["coverage_gaps"]
                holdings.append({
                    "start_year": year, "rule": rule, "ticker": ticker,
                    "weight": weight, "return": ret, "contribution": weight * ret,
                    "initial_capital_standalone": res["initial_value"],
                    "initial_capital_allocated": weight * res["initial_value"],
                    "cash_final": res["cash"], "final_assets": json.dumps(
                        res["holdings"], ensure_ascii=False, sort_keys=True),
                    "cash_final_allocated": weight * res["cash"],
                    "final_assets_allocated": json.dumps(
                        {t: weight * q for t, q in res["holdings"].items()}, sort_keys=True),
                    "gaps": json.dumps(gaps, ensure_ascii=False, sort_keys=True),
                    "events_applied": res["events_applied"],
                    "daily_missing": res["daily_missing"],
                    "status": "PROVISORIO_COBERTURA" if gaps else "COBERTURA_V6"})
            if len(pieces) != len(w):
                result = ""
                status = "INCOMPLETO"
                diff = ""
            else:
                result = sum(pieces)
                # Invariante: carteira multiativo equivale à soma das posições.
                try:
                    state_full = engine.initialize(start, w)
                    previous_value = state_full.initial_value
                    for period in range(year, 2026):
                        period_end = bridge.WINDOWS[period][1]
                        engine.advance(state_full, period_end)
                        nav = engine.value(state_full, period_end)["nav"]
                        annual_path.append({"start_year": year, "rule": rule,
                                            "period_year": period, "end": period_end,
                                            "nav": nav, "cash": state_full.cash,
                                            "period_return": nav / previous_value - 1,
                                            "cumulative_return": nav / state_full.initial_value - 1})
                        previous_value = nav
                    direct = engine.result(state_full, require_complete=False)["return"]
                    diff = direct - result
                    if not math.isclose(direct, result, abs_tol=1e-8, rel_tol=1e-10):
                        failures.append({"year": year, "rule": rule, "ticker": "CARTEIRA",
                                         "status": "DIVERGENCIA_MULTIATIVO",
                                         "detail": f"agregado={result}; direto={direct}"})
                    final_nav = engine.value(state_full, END)["nav"]
                    for asset, quantity in sorted(state_full.holdings.items()):
                        price = extended_book.exact(asset, END)
                        final_positions.append({"start_year": year, "rule": rule,
                                                "asset": asset, "quantity": quantity,
                                                "price": price, "value": quantity * price,
                                                "final_weight": quantity * price / final_nav})
                    final_positions.append({"start_year": year, "rule": rule,
                                            "asset": "CASH", "quantity": state_full.cash,
                                            "price": 1, "value": state_full.cash,
                                            "final_weight": state_full.cash / final_nav})
                except Exception as ex:
                    diff = ""
                    failures.append({"year": year, "rule": rule, "ticker": "CARTEIRA",
                                     "status": type(ex).__name__, "detail": str(ex)})
                cohort = [r for r in holdings if r["start_year"] == year and r["rule"] == rule]
                status = ("CALCULADO_PROVISORIO" if all(r["status"] != "INCOMPLETO" for r in cohort)
                          else "INCOMPLETO")
            years_elapsed = (date.fromisoformat(END) - date.fromisoformat(start)).days / 365.25
            benchmark = extended_book.exact("BOVA11", END) / extended_book.exact("BOVA11", start) - 1
            rolling = math.prod(1 + number(annual_lookup[y][rule], f"{y} {rule}")
                                for y in range(year, 2026)) - 1
            yearly.append({
                "start_year": year, "start": start, "end": END, "rule": rule,
                "n": len(w), "maintain_return": result,
                "maintain_cagr": (1 + result) ** (1 / years_elapsed) - 1 if result != "" else "",
                "renew_return": rolling,
                "renew_minus_maintain_pp": 100 * (rolling - result) if result != "" else "",
                "bova_return": benchmark,
                "multiasset_delta": diff, "status": status,
                "source": "V6_EVENT_ENGINE_DOCUMENTARY_V11_1_PROVISIONAL" if documentary_policy else "V6_EVENT_ENGINE_B3_SQLITE_SUPPLEMENT_PROVISIONAL"})

    # Não substituir arquivos existentes antes da validação de paridade.
    cols_year = ["start_year", "start", "end", "rule", "n", "maintain_return",
                 "maintain_cagr", "renew_return", "renew_minus_maintain_pp",
                 "bova_return", "multiasset_delta", "status", "source"]
    cols_pos = ["start_year", "rule", "ticker", "weight", "return",
                "contribution", "cash_final", "final_assets", "gaps", "events_applied", "daily_missing",
                "initial_capital_standalone", "initial_capital_allocated", "cash_final_allocated",
                "final_assets_allocated", "status"]
    cols_audit = ["ticker", "date_com", "kind", "amount_or_multiplier",
                  "source", "status", "detail"]
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "graham_18_coortes.csv", yearly, cols_year)
    write_csv(out / "graham_posicoes.csv", holdings, cols_pos)
    write_csv(out / "b3_suplementacao_auditavel.csv", b3_audit, cols_audit)
    write_csv(out / "alertas_documentais.csv", alerts, cols_audit)
    write_csv(out / "erros_execucao.csv", failures, ["year", "rule", "ticker", "status", "detail"])
    write_csv(out / "paridade_primeiro_ano.csv", first_year_rows,
              ["start_year", "rule", "start", "end", "maintenance", "annual_v10", "delta", "status"])
    write_csv(out / "posicoes_finais_carteira.csv", final_positions,
              ["start_year", "rule", "asset", "quantity", "price", "value", "final_weight"])
    write_csv(out / "trajetoria_anual_manutencao.csv", annual_path,
              ["start_year", "rule", "period_year", "end", "nav", "cash", "period_return", "cumulative_return"])
    (out / "eventos_utilizados.json").write_text(
        json.dumps([asdict(e) for e in events], ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(out / "alteracoes_documentais.csv", amendments,
              ["action", "event_id", "asset", "date", "old_value", "new_value", "source", "reason"])
    summary = {
        "reference": "graham_corrigido_anuais_eventos.csv (v10); mesma data e critérios",
        "legacy_v6_parity": "18/18",
        "first_year_parity": f"{first_year_ok}/18",
        "portfolio_cohorts": len(yearly),
        "positions": len(holdings),
        "supplementary_events_used": sum(e in events for e in full_extra),
        "documentary_policy": documentary_policy,
        "documentary_amendments": len(amendments),
        "method_version": "v11.1_documental" if documentary_policy else "v11_reproducao",
        "unresolved_b3_conflicts": len(alerts),
        "execution_errors": len(failures),
        "certified": False,
        "capital_per_portfolio": 10000.0,
        "standalone_position_capital": 10000.0,
        "position_units": "cash_final/final_assets: standalone; *_allocated: multiplied by initial weight",
        "daily_missing_note": "Interim NAV unavailable without exact quote; no fill. Entry, exit and reinvestment remain strict.",
        "notes": [
            "Manutenção sem rebalancear desde cada junho até junho/2026",
            "Proventos reinvestidos na data-ex segundo o motor legado",
            "Os intervalos protegidos pela v10 nunca recebem eventos B3 novos de forma silenciosa",
            "Fonte nominal SQLite não é certificação independente da B3",
            "Eventos societários fora do catálogo capturado não são presumidos",
            "Nenhum ativo recebeu RECONCILED automaticamente",
            "Renovação dos anos 2021-2026 usa seleção corrigida de cada ano",
        ],
    }
    (out / "resumo_auditoria.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PARIDADE v6: 18/18 | PRIMEIRO ANO vs v10: {first_year_ok}/18")
    print(f"COMPLEMENTOS RETIDOS: {summary['supplementary_events_used']} | ALTERAÇÕES DOCUMENTAIS: {len(amendments)}")
    print(f"ALERTAS DOCUMENTAIS: {len(alerts)} | ERROS DE CÁLCULO: {len(failures)}")
    print("MANUTENÇÃO GRAHAM CORRIGIDA POR COORTE (2020–2026):")
    for r in yearly:
        if r["maintain_return"] == "":
            print(f"  {r['start_year']} {r['rule']}: INCOMPLETO")
        else:
            print(f"  {r['start_year']} {r['rule']}: manter {r['maintain_return']:+.4%} "
                  f"| renovar {r['renew_return']:+.4%} "
                  f"| BOVA {r['bova_return']:+.4%} [{r['status']}]")
    print("ARQUIVOS:", out.resolve())
    if failures:
        return 2
    if alerts:
        print("ATENÇÃO: alerts em alertas_documentais.csv exigem revisão antes de certificação.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Diretório de saída; use um destino novo para preservar checkpoints")
    parser.add_argument("--documentary-policy", choices=("KEEP_CASH", "REINVEST"),
                        help="Aplica alterações rastreáveis; REINVEST autorizado pelo usuário em 07/10/2026")
    args = parser.parse_args()
    raise SystemExit(run(args.out, args.documentary_policy))
