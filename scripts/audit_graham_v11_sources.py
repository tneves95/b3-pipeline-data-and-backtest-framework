#!/usr/bin/env python3
"""Read-only reconciliation of v11 against archived COTAHIST and official RI tables.

Run from the repository root after v11. Reads a factual RI transcription with
source URLs and provenance; hashes refer to the transcription, not original HTML.
No event or coverage is modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from scripts import graham_corrected_maintenance_v11 as maintenance

URLS = {
    "UNIP3": "https://ri.unipar.com/informacoes-aos-investidores/proventos-e-bonificacoes/",
    "ITSA3": "https://ri.itausa.com.br/informacoes-financeiras/remuneracao-aos-acionistas/",
    "SYNE3": "https://ri.syn.com.br/governanca-corporativa/politica-de-dividendos-e-historico/",
    "CSAN3": "https://www.cosan.com.br/relacoes-com-investidores/outras-informacoes-para-investidores/dividendos/",
}
PENDING = {"ITSA3": [2022, 2023, 2024, 2025], "UNIP3": [2022, 2023],
           "SBSP3": [2025], "TGMA3": [2025], "CSAN3": [2022],
           "SYNE3": [2022], "ALOS3": [2024, 2025]}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path, rows, fields):
    maintenance.write_csv(path, rows, fields)


def ri_tables(cache=None, fetch=False):
    # Factual transcription of the official pages opened on 2026-10-07.
    # The RI server returned HTTP 403 to requests; do not pretend to hash HTML.
    path = Path("research/graham_v6_comparison/ri_events_verified_2026_10_07.csv")
    events = maintenance.read_csv(path)
    for row in events:
        row["amount"] = float(row["amount"])
        row["source_sha256"] = ""  # original web bytes not available
        row["row_id"] = row.pop("evidence_id")
    manifest = [{"artifact": str(path), "artifact_sha256": digest(path),
                 "retrieved_date": "2026-10-07", "method": "transcricao de fatos das paginas oficiais via ferramenta web",
                 "limitation": "HTTP 403 no download direto; hash se refere ao CSV transcrito, nao ao HTML"}]
    return manifest, events


def reconcile_cash(evidence, engine_events):
    rows = []
    seen = set()
    for row in evidence:
        key = (row["ticker"], row["date"], row["date_basis"], row["kind"], row["amount"])
        same = [e for e in engine_events if e["asset"] == row["ticker"] and e["kind"] == "CASH"
                and (e["record_date"] if row["date_basis"] == "com" else e["date"]) == row["date"]]
        matches = [e for e in same if math.isclose(e["amount"], row["amount"], rel_tol=5e-6, abs_tol=5e-7)]
        if key in seen:
            status = "REPETICAO_TABELA_RI_REVISAR"
        elif row["kind"] == "CAPITAL_REDUCTION":
            status = "TRATAMENTO_ECONOMICO_PENDENTE" if not matches else "VALOR_PRESENTE_REVISAR_NATUREZA"
        elif len(matches) == 1:
            status = "VALOR_DATA_PRESENTES"
        elif len(matches) > 1:
            status = "POSSIVEL_DUPLICACAO_MOTOR"
        elif same and row["ticker"] == "SYNE3":
            status = "VALOR_DIVERGENTE_REVISAR"
        else:
            status = "AUSENTE_NO_MOTOR"
        seen.add(key)
        rows.append(dict(row, status=status, matching_ids=";".join(e["event_id"] for e in matches),
                         same_date_values=json.dumps([e["amount"] for e in same])))
    return rows


def cotahist_prices(raw_dir, targets):
    """Independent byte extraction, cash market 010 only, retaining raw record hash."""
    result, manifest = defaultdict(list), []
    years = sorted({int(day[:4]) for _, day in targets})
    names = {t.encode().ljust(12) for t, _ in targets}
    for year in years:
        path = raw_dir / f"COTAHIST_A{year}.ZIP"
        manifest.append({"year": year, "filename": path.name, "bytes": path.stat().st_size,
                         "sha256": digest(path),
                         "source_url": f"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{year}.ZIP",
                         "provenance": "arquivo local preexistente; nao houve novo download independente"})
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if member.endswith("/"):
                    continue
                with archive.open(member) as handle:
                    for lineno, line in enumerate(handle, 1):
                        if line[:2] != b"01" or line[12:24] not in names or line[24:27] != b"010":
                            continue
                        raw_day = line[2:10].decode()
                        day = raw_day[:4] + "-" + raw_day[4:6] + "-" + raw_day[6:8]
                        ticker = line[12:24].decode().strip()
                        if (ticker, day) not in targets:
                            continue
                        factor = int(line[210:217])
                        if factor <= 0:
                            raise ValueError(f"Fator COTAHIST inválido: {path}:{lineno}")
                        result[(ticker, day)].append({"close": int(line[108:121]) / 100 / factor,
                            "isin": line[230:242].decode().strip(), "quotation_factor": factor,
                            "file": path.name, "member": member, "line": lineno,
                            "record_sha256": hashlib.sha256(line).hexdigest()})
        print(f"COTAHIST {year}: extração concluída", flush=True)
    return result, manifest


def run(raw_dir):
    root = Path.cwd()
    out = root / "graham_v6_event_results" / "auditoria_fontes_v11"
    events = json.loads((root / "graham_v6_event_results/manutencao_corrigida_v11/eventos_utilizados.json").read_text())
    manifest, evidence = ri_tables()
    cash = reconcile_cash(evidence, events)
    write(out / "proventos_RI_confrontados.csv", cash,
          ["ticker", "date", "date_basis", "kind", "amount", "payment_date", "source_url", "source_sha256",
           "row_id", "status", "matching_ids", "same_date_values"])
    targets = defaultdict(set)
    for ticker, years in PENDING.items():
        for year in years:
            for day in maintenance.bridge.WINDOWS[year]:
                targets[(ticker, day)].add(f"limite_{year}")
        start = maintenance.bridge.WINDOWS[min(years)][0]
        targets[(ticker, maintenance.END)].add("limite_manutencao")
        for event in events:
            if event["asset"] == ticker and start < event["date"] <= maintenance.END:
                targets[(ticker, event["date"])].add("evento_" + event["kind"])
    calendar, _, _ = maintenance.bridge.load_legacy()
    for row in evidence:
        exdate = row["date"] if row["date_basis"] == "ex" else calendar.next_session(row["date"])
        targets[(row["ticker"], exdate)].add("evento_RI_" + row["kind"])
    for start, end in maintenance.bridge.WINDOWS.values():
        targets[("BOVA11", start)].add("benchmark")
        targets[("BOVA11", end)].add("benchmark")
    # Regression failure must remain a missing interim quote, never a synthetic price.
    targets[("UNIP3", "2025-05-14")].add("regressao_dia_intermediario")
    raw, raw_manifest = cotahist_prices(raw_dir, targets)
    book, _, _ = maintenance.bridge.load_legacy()
    book = maintenance.bridge.expand_with_sqlite(book, set(PENDING))
    quotes = []
    for (ticker, day), uses in sorted(targets.items()):
        prices = raw.get((ticker, day), [])
        engine_price = book.prices.get(ticker, {}).get(day)
        status = "AUSENTE_COTAHIST"
        if len(prices) == 1:
            status = "OK_ARQUIVO_BRUTO" if engine_price is not None and math.isclose(
                prices[0]["close"], engine_price, rel_tol=0, abs_tol=1e-7) else "DIVERGENCIA_PRECO"
        elif len(prices) > 1:
            status = "MULTIPLOS_REGISTROS_REVISAR"
        quotes.append({"ticker": ticker, "date": day, "uses": ";".join(sorted(uses)), "status": status,
                       "engine_price": engine_price, "raw_close": prices[0]["close"] if len(prices)==1 else "",
                       "raw_records": json.dumps(prices, ensure_ascii=False)})
    write(out / "cotacoes_confrontadas_COTAHIST.csv", quotes,
          ["ticker", "date", "uses", "status", "engine_price", "raw_close", "raw_records"])
    matrix = []
    for ticker, years in PENDING.items():
        for year in years:
            start, end = maintenance.bridge.WINDOWS[year]
            qs = [r for r in quotes if r["ticker"] == ticker and start <= r["date"] <= end
                  and "regressao_dia_intermediario" not in r["uses"]]
            cs = [r for r in cash if r["ticker"] == ticker and start < r["date"] <= end]
            matrix.append({"ticker": ticker, "year": year, "start": start, "end": end,
                "quotes_checked": len(qs), "quotes_ok": sum(r["status"]=="OK_ARQUIVO_BRUTO" for r in qs),
                "ri_rows": len(cs), "ri_missing": sum(r["status"]=="AUSENTE_NO_MOTOR" for r in cs),
                "certified": False,
                "remaining": "Completude caixa/estrutura e documentos específicos; arquivo bruto local sem cadeia de download atestada"})
    write(out / "matriz_12_ativo_ano.csv", matrix, list(matrix[0]))
    summary = {"ri_sources": manifest, "cotahist_sources": raw_manifest,
               "quotes": dict(Counter(r["status"] for r in quotes)),
               "cash": dict(Counter(r["status"] for r in cash)),
               "certified": False,
               "limitations": ["Relação de proventos do RI não prova ausência de todos os eventos societários",
                               "ALOS3/TGMA3/SBSP3: documentos específicos precisam de confronto integral adicional",
                               "Auditoria Barsi e conciliação das posições são registradas separadamente em auditoria_besst_v9"]}
    (out / "manifesto_fontes.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps({k:summary[k] for k in ("quotes", "cash", "certified")}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    run(args.raw_dir)
