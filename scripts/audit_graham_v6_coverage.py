#!/usr/bin/env python3
"""Auditoria somente-leitura: 7 ativos ainda não conciliados no retorno Graham v6.

Uso (na raiz do Codespaces):
    python scripts/audit_graham_v6_coverage.py

Não altera SQLite, motor, eventos, seleções, nem promove coberturas a RECONCILED.
Saídas em graham_v6_event_results/auditoria_7/ .
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import sqlite3
from collections import defaultdict
from pathlib import Path

ASSETS = {"ITSA3", "UNIP3", "SBSP3", "TGMA3", "CSAN3", "SYNE3", "ALOS3"}
WINDOWS = {
    2020: ("2020-06-30", "2021-06-30"),
    2021: ("2021-06-30", "2022-06-30"),
    2022: ("2022-06-30", "2023-06-30"),
    2023: ("2023-06-30", "2024-06-28"),
    2024: ("2024-06-28", "2025-06-30"),
    2025: ("2025-06-30", "2026-06-30"),
}
# Valores brutos por ação e datas-com conferidos em avisos oficiais da Tegma.
# Não constituem certificação de cotações, nem das demais seis empresas.
EVIDENCE = [
    ("TGMA3", "2025-08-07", "CASH_DIVIDEND", 1.21,
     "https://api.mziq.com/mzfilemanager/v2/d/280684e0-28e0-4165-99c5-8a10de86a40c/7438b341-5502-5d45-47fa-6924f62c6f09?origin=1"),
    ("TGMA3", "2025-08-07", "JCP", 0.14,
     "https://api.mziq.com/mzfilemanager/v2/d/280684e0-28e0-4165-99c5-8a10de86a40c/7438b341-5502-5d45-47fa-6924f62c6f09?origin=1"),
    ("TGMA3", "2025-11-06", "CASH_DIVIDEND", 0.79,
     "https://ri.tegma.com.br/noticias/aviso-aos-acionistas-pagamento-de-dividendos-e-juros-sobre-capital-proprio-2/"),
    ("TGMA3", "2025-11-06", "JCP", 0.18,
     "https://ri.tegma.com.br/noticias/aviso-aos-acionistas-pagamento-de-dividendos-e-juros-sobre-capital-proprio-2/"),
    ("TGMA3", "2025-12-02", "CASH_DIVIDEND", 1.52,
     "https://ri.tegma.com.br/noticias/aviso-aos-acionistas-pagamento-de-dividendos/"),
]

def read_csv(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError("Arquivo de trabalho ausente: " + str(path))
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def known_stock_from_bridge(path: Path) -> list[tuple]:
    """Lê a constante KNOWN_STOCK sem executar código local não versionado."""
    if not path.is_file():
        raise FileNotFoundError("Motor complementar ausente: " + str(path))
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "KNOWN_STOCK" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError("KNOWN_STOCK não encontrado em " + str(path))

def value_or_none(s):
    try:
        v = float(s)
        return v if math.isfinite(v) and v > 0 else None
    except (ValueError, TypeError):
        return None

def quote(con, ticker: str, date: str):
    rows = con.execute(
        "SELECT close FROM prices WHERE ticker=? AND date=? ORDER BY isin_code",
        (ticker, date),
    ).fetchall()
    vals = [value_or_none(r[0]) for r in rows]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None, "SEM_COTACAO"
    if len(vals) > 1 and max(vals) / min(vals) > 1.000001:
        return vals[0], "MULTIPLAS_COTACOES_DIVERGENTES"
    return vals[0], "OK"

def quote_around(con, ticker: str, date_com: str):
    before = con.execute(
        "SELECT date,close FROM prices WHERE ticker=? AND date<=? AND close>0 "
        "ORDER BY date DESC LIMIT 1", (ticker, date_com)
    ).fetchone()
    after = con.execute(
        "SELECT date,close FROM prices WHERE ticker=? AND date>? AND close>0 "
        "ORDER BY date ASC LIMIT 1", (ticker, date_com)
    ).fetchone()
    return before, after

def normalized_stock(stock_csv: list[dict], known: list[tuple]):
    all_stock = {}
    disagreements = []
    for tick, date_com, kind, factor, source in known:
        if tick in ASSETS:
            all_stock[(tick, date_com, kind)] = (float(factor), source)
    for row in stock_csv:
        if row["ticker"] not in ASSETS:
            continue
        if row["action_type"] != "BONUS_SHARES":
            disagreements.append({
                "ticker": row["ticker"], "date_com": row["ex_date"],
                "kind": row["action_type"], "issue": "TIPO_NAO_MAPEADO",
                "details": str(row)
            })
            continue
        tick, dc, kind = row["ticker"], row["ex_date"], "BONUS"
        factor = value_or_none(row["factor"])
        if factor is None:
            disagreements.append({
                "ticker": tick, "date_com": dc, "kind": kind,
                "issue": "FATOR_INVALIDO", "details": str(row)
            })
            continue
        multiplier = 1 + factor / 100
        key = (tick, dc, kind)
        if key in all_stock:
            earlier, source = all_stock[key]
            if not math.isclose(earlier, multiplier, rel_tol=1e-7, abs_tol=1e-8):
                disagreements.append({
                    "ticker": tick, "date_com": dc, "kind": kind,
                    "issue": "FATOR_DIVERGENTE",
                    "details": "B3={} vs {} ({})".format(multiplier, earlier, source)
                })
        else:
            all_stock[key] = (multiplier, row.get("source", "B3"))
    return all_stock, disagreements

def audit(root: Path, out: Path, threshold: float):
    cash = read_csv(root / "graham_v6_extra_cash.csv")
    stock = read_csv(root / "graham_v6_extra_stock.csv")
    positions = read_csv(root / "graham_v6_event_results" / "graham_corrigido_posicoes_eventos.csv")
    known = known_stock_from_bridge(root / "graham_v6_event_bridge" / "graham_event_resume.py")
    db = root / "b3_market_data.sqlite"
    if not db.is_file():
        raise FileNotFoundError("Banco SQLite não encontrado: " + str(db))

    evidence_rows = []
    for ticker, dc, kind, expected, url in EVIDENCE:
        matches = [r for r in cash if r["ticker"] == ticker
                   and r["event_date"] == dc and r["event_type"] == kind
                   and value_or_none(r["value"]) is not None
                   and math.isclose(float(r["value"]), expected, rel_tol=0, abs_tol=0.00005)]
        evidence_rows.append({
            "ticker": ticker, "date_com": dc, "kind": kind, "value": expected,
            "source_url": url, "matches": len(matches),
            "status": "RI_CONFERIDO" if len(matches) == 1 else
                      ("AUSENTE" if len(matches) == 0 else "DUPLICADO"),
        })

    # Somar pesos somente dos anos/regras com cobertura não conciliada.
    by_year_asset = defaultdict(list)
    for r in positions:
        if r.get("ticker") in ASSETS and r.get("source_coverage") != "V6_COBERTO":
            by_year_asset[(int(r["year"]), r["ticker"])].append(r)

    priority = []
    for (year, ticker), rows in by_year_asset.items():
        weights = [float(r["weight"]) for r in rows]
        priority.append({
            "year": year, "ticker": ticker, "rules": ",".join(sorted(r["rule"] for r in rows)),
            "max_weight": max(weights), "sum_weights": sum(weights),
            "total_rule_positions": len(rows), "status": "AINDA_NAO_CONCILIADO",
        })
    priority.sort(key=lambda r: (-r["sum_weights"], -r["max_weight"], r["year"], r["ticker"]))

    actions, disagreements = normalized_stock(stock, known)
    structural_rows = []
    quote_rows = []
    with sqlite3.connect("file:{}?mode=ro".format(db.resolve()), uri=True) as con:
        for item in priority:
            year, ticker = item["year"], item["ticker"]
            start, end = WINDOWS[year]
            for boundary, day in (("INICIO", start), ("FIM", end)):
                v, status = quote(con, ticker, day)
                quote_rows.append({
                    "year": year, "ticker": ticker, "boundary": boundary,
                    "date": day, "price_close_nominal": v, "status": status,
                })

        # Ao contrário de adj_close, um fechamento NOMINAL deve refletir
        # a divisão do preço por factor em bonificações/desdobramentos.
        for (ticker, date_com, kind), (factor, source) in sorted(actions.items()):
            affected = [r["year"] for r in priority if r["ticker"] == ticker
                        and WINDOWS[r["year"]][0] < date_com <= WINDOWS[r["year"]][1]]
            if not affected:
                continue
            before, after = quote_around(con, ticker, date_com)
            if not before or not after:
                structural_rows.append({
                    "ticker": ticker, "date_com": date_com, "kind": kind,
                    "multiplier": factor, "source": source, "date_before": before[0] if before else "",
                    "date_after": after[0] if after else "", "price_before": before[1] if before else "",
                    "price_after": after[1] if after else "",
                    "overnight_adjusted_change": "", "status": "COTACAO_AUSENTE",
                    "years": ",".join(map(str, sorted(set(affected)))),
                })
                continue
            delta = float(after[1]) * factor / float(before[1]) - 1
            structural_rows.append({
                "ticker": ticker, "date_com": date_com, "kind": kind,
                "multiplier": factor, "source": source,
                "date_before": before[0], "date_after": after[0],
                "price_before": before[1], "price_after": after[1],
                "overnight_adjusted_change": delta,
                "status": "VERIFICAR_DESCONTINUIDADE" if abs(delta) > threshold else "SEM_ALERTA_MECANICO",
                "years": ",".join(map(str, sorted(set(affected)))),
            })

    write_csv(out / "fontes_RI_conferidas.csv", evidence_rows,
              ["ticker", "date_com", "kind", "value", "source_url", "matches", "status"])
    write_csv(out / "pendencias_priorizadas.csv", priority,
              ["year", "ticker", "rules", "max_weight", "sum_weights",
               "total_rule_positions", "status"])
    write_csv(out / "cotacoes_limites.csv", quote_rows,
              ["year", "ticker", "boundary", "date", "price_close_nominal", "status"])
    write_csv(out / "eventos_estruturais_precos.csv", structural_rows,
              ["ticker", "date_com", "kind", "multiplier", "source", "date_before",
               "date_after", "price_before", "price_after", "overnight_adjusted_change",
               "status", "years"])
    write_csv(out / "divergencias_estruturais.csv", disagreements,
              ["ticker", "date_com", "kind", "issue", "details"])

    pass_ri = sum(r["status"] == "RI_CONFERIDO" for r in evidence_rows)
    quote_issues = [r for r in quote_rows if r["status"] != "OK"]
    stock_alerts = [r for r in structural_rows if r["status"] != "SEM_ALERTA_MECANICO"]
    print("RI Tegma: {}/{} eventos conferidos".format(pass_ri, len(evidence_rows)))
    print("Posições distintas ano/ativo ainda pendentes: {}".format(len(priority)))
    print("Cotações-limite com problema: {}/{}".format(len(quote_issues), len(quote_rows)))
    print("Eventos estruturais com alerta mecânico: {}/{}".format(len(stock_alerts), len(structural_rows)))
    print("Fatores B3 divergentes/não mapeados:", len(disagreements))
    print("CSV de auditoria:", out.resolve())
    print("AVISO: nenhuma cobertura foi promovida a RECONCILED; checagem de preços não certifica documentos.")
    for r in quote_issues[:12]:
        print("  COTACAO:", r["ticker"], r["year"], r["boundary"], r["status"])
    for r in stock_alerts[:12]:
        print("  ESTRUTURA:", r["ticker"], r["date_com"], r["status"], r["overnight_adjusted_change"])
    return 0 if pass_ri == len(evidence_rows) and not quote_issues and not disagreements else 1

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--structural-threshold", type=float, default=0.20)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out or root / "graham_v6_event_results" / "auditoria_7"
    if not 0 < args.structural_threshold < 1:
        parser.error("--structural-threshold deve estar entre 0 e 1")
    return audit(root, out, args.structural_threshold)

if __name__ == "__main__":
    raise SystemExit(main())
