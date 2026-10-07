#!/usr/bin/env python3
"""Consolidar RENOVAÇÃO ANUAL: Graham corrigido v6 local + BESST v9 congelado.

Uso na raiz do Codespaces:
    python scripts/compare_graham_corrected_barsi_v9.py

Não importa o motor nem modifica banco, seleções, registros ou retornos.
Não mistura a manutenção de posições v9 com as seleções Graham corrigidas.
Resultados provisórios de Graham permanecem explicitamente provisórios.
"""
from __future__ import annotations
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

YEARS = {
    2020: ("2020-06-30", "2021-06-30"),
    2021: ("2021-06-30", "2022-06-30"),
    2022: ("2022-06-30", "2023-06-30"),
    2023: ("2023-06-30", "2024-06-28"),
    2024: ("2024-06-28", "2025-06-30"),
    2025: ("2025-06-30", "2026-06-30"),
}
GRAHAM = ("R00", "R03", "R16")
V9_GRAHAM_OLD = {"R00": 1.9480082769519065,
                 "R03": 3.248622531294914, "R16": 3.4060945983486715}
BOVA_V9 = 0.8451211525867715

def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError("Arquivo ausente: " + str(path))
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def number(value, field):
    try:
        out = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field} não numérico: {value!r}")
    if not math.isfinite(out):
        raise ValueError(f"{field} não finito: {value!r}")
    return out

def close(a, b, atol=1e-9):
    return math.isclose(a, b, abs_tol=atol, rel_tol=1e-10)

def must(cond, text):
    if not cond:
        raise RuntimeError(text)

def writecsv(path, records, cols):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(records)

def main():
    root = Path.cwd()
    results = root / "graham_v6_event_results"
    annual = read_csv(results / "graham_corrigido_anuais_eventos.csv")
    positions = read_csv(results / "graham_corrigido_posicoes_eventos.csv")
    parity = read_csv(results / "paridade_original_v6.csv")
    published = read_csv(results / "graham_corrigido_resumo_eventos.csv")
    errors = read_csv(results / "graham_corrigido_pendencias_eventos.csv")
    besst = read_csv(root / "research" / "graham_v6_comparison" / "besst_v9_renewal_frozen.csv")

    pairs = {(int(x["year"]), x["rule"]) for x in parity}
    must(len(parity) == 18 and len(pairs) == 18
         and all(x["status"] == "OK" and abs(number(x["difference"], "paridade")) <= 1e-9 for x in parity),
         "Paridade histórica v6 não é 18/18 OK")
    must(not errors, f"Há {len(errors)} erros do motor corrigido")
    must(len(annual) == 6 and {int(x["year"]) for x in annual} == set(YEARS),
         "As seis janelas anuais Graham não estão completas")
    must(len(besst) == 8, "Snapshot BESST v9 incompleto")
    must({(x["strategy"], x["scenario"]) for x in besst}
         == {(r, scenario) for r in ("B00","B00S","B06","B06S")
             for scenario in ("central", "conservative")},
         "Cenários de BESST v9 ausentes/duplicados")

    index = {(int(x["year"]), rule): [] for x in annual for rule in GRAHAM}
    for x in positions:
        y = int(x["year"])
        if x["rule"] in GRAHAM and (y, x["rule"]) in index:
            index[(y, x["rule"])].append(x)

    for x in annual:
        y = int(x["year"])
        must((x["start"], x["end"]) == YEARS[y], f"Datas incorretas em {y}")
        for rule in GRAHAM:
            w = index[(y, rule)]
            must(w, f"Posições faltantes {y} {rule}")
            must(close(sum(number(v["weight"], "peso") for v in w), 1, atol=1e-9),
                 f"Pesos inválidos {y} {rule}")
            p = sum(number(v["contribution"], "contribution") for v in w)
            must(close(p, number(x[rule], rule), atol=1e-9),
                 f"Contribuições não reconciliadas {y} {rule}")
        must(x.get("BOVA11") and number(x["BOVA11"], "BOVA11") > -1,
             f"BOVA11 ausente em {y}")

    by_year = {int(x["year"]): x for x in annual}
    result = []
    info = {}
    for rule in GRAHAM + ("BOVA11",):
        factor = math.prod(1 + number(by_year[y][rule], f"{y} {rule}") for y in YEARS)
        total = factor - 1
        must(factor > 0, "Fator de retorno inválido")
        status = ("BENCHMARK_COTACAO_V6" if rule == "BOVA11" else
                  "CALCULADO_PROVISORIO" if any(
                      by_year[y].get(rule+"_status") != "COBERTURA_V6" for y in YEARS
                  ) else "COBERTURA_V6")
        info[rule] = total
        result.append(dict(strategy=rule, family="Graham" if rule in GRAHAM else "Benchmark",
                           scenario="corrigido" if rule in GRAHAM else "cota",
                           return_2020_2026=total,
                           range_low="", range_high="",
                           cagr=factor**(1/6)-1,
                           final_per_10000=10000*factor,
                           status=status,
                           source="motor_eventos_v6_com_selecoes_corrigidas" if rule in GRAHAM else "BOVA11_v6"))
    must(close(info["BOVA11"], BOVA_V9, atol=1e-9),
         f"Datas/benchmark divergentes entre v9 e Graham corrigido: {info['BOVA11']} vs {BOVA_V9}")
    old_summary = {x["rule"]: x for x in published}
    for rule in GRAHAM + ("BOVA11",):
        must(rule in old_summary and close(number(old_summary[rule]["return_2020_2026"], rule),
                                          info[rule], atol=1e-8),
             "Resumo local diferente dos retornos anuais: " + rule)

    for b in besst:
        total = number(b["return"], "BESST")
        low = number(b["low"], "BESST.low")
        high = number(b["high"], "BESST.high")
        must(low <= total <= high, f"Envelope inválido {b['strategy']} {b['scenario']}")
        result.append(dict(strategy=b["strategy"], family="BESST",
                           scenario=b["scenario"], return_2020_2026=total,
                           range_low=low, range_high=high,
                           cagr=(1+total)**(1/6)-1,
                           final_per_10000=10000*(1+total),
                           status="PRECISAO_MATERIAL_V9_CENARIO",
                           source="Pacote_Barsi_Graham_Comparacao_Final_v9_2026-10-06.zip"))
    result.sort(key=lambda x: -x["return_2020_2026"])

    outdir = results / "comparacao_corrigida_v10"
    output = outdir / "renovacao_2020_2026.csv"
    writecsv(output, result, ["strategy","family","scenario","return_2020_2026",
                              "range_low","range_high","cagr","final_per_10000","status","source"])
    deltas = [{
        "rule": rule,
        "old_v9_return": V9_GRAHAM_OLD[rule],
        "corrected_v6_return": info[rule],
        "delta_percentage_points": 100*(info[rule]-V9_GRAHAM_OLD[rule]),
        "note": "MUDANCA_DE_CARTEIRA_E_COBERTURA; NAO_E_SOMENTE_CORRECAO_DE_EVENTOS",
    } for rule in GRAHAM]
    writecsv(outdir / "delta_graham_vs_v9.csv", deltas,
             ["rule","old_v9_return","corrected_v6_return","delta_percentage_points","note"])
    summary = {
        "status": "PROVISORIO_SEM_PROMOCAO_AUTOMATICA_DE_COBERTURA",
        "period": "2020-06-30..2026-06-30",
        "historical_parity": "18/18 OK",
        "updated_scenarios": "Somente renovacao anual; manutencao v9 antiga permanece fora deste consolidado",
        "BOVA11_match": True,
        "graham_new": info,
        "besst_v9_envelope_global_high": max(number(x["high"],"high") for x in besst),
        "graham_above_all_besst_v9_envelopes": {
            rule: info[rule] > max(number(x["high"],"high") for x in besst) for rule in GRAHAM},
        "coverage_warning": "Graham possui 12 janelas distintas ano/ativo ainda sem certificacao documental; fonte CSV local.",
        "taxonomy": {"Graham":"Retornos event-level calculados com eventos complementares, sem certificacao completa",
                     "BESST":"Faixas de sensibilidade de precisao material da v9, nao IC estatistico",
                     "BOVA11":"Fechamentos de negociacao das mesmas datas"},
    }
    (outdir / "auditoria_renovacao_v10.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PARIDADE: 18/18 | DATAS: 6/6 | PESOS E CONTRIBUICOES: 18/18 | BOVA: IGUAL V9")
    print("RENOVACAO ANUAL ATUALIZADA (2020-2026):")
    for x in result:
        print(f"  {x['strategy']:6} {x['scenario']:12} "
              f"{x['return_2020_2026']:+.4%} CAGR={x['cagr']:.4%} [{x['status']}]")
    print("ALTERACAO DE GRAHAM V9 -> CORRIGIDO:")
    for d in deltas:
        print(f"  {d['rule']}: {d['delta_percentage_points']:+.4f} p.p. (tambem muda selecao)")
    print("GRAHAM ACIMA DE TODA FAIXA BESST V9:",
          summary["graham_above_all_besst_v9_envelopes"])
    print("AVISO: comparacao provisoria; manutencao de posicoes NAO foi atualizada.")
    print("ARQUIVOS:", outdir.resolve())

if __name__ == "__main__":
    main()
