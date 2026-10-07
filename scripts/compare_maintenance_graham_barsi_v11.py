#!/usr/bin/env python3
"""Comparação provisória e auditável: Graham v11 vs BESST v9, manter x renovar.

Usar após scripts/graham_corrected_maintenance_v11.py na raiz do repositório:
    python scripts/compare_maintenance_graham_barsi_v11.py

Não mistura janelas: todas as estratégias partem da mesma data de junho de
cada coorte e terminam em 30/06/2026. A renovação reaplica a seleção anual;
a manutenção mantém a seleção inicial e reinveste proventos. Sem custos/tributos.
"""
from __future__ import annotations
import csv
import argparse
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path.cwd()
YEAR_START = {
    2020: "2020-06-30", 2021: "2021-06-30", 2022: "2022-06-30",
    2023: "2023-06-30", 2024: "2024-06-28", 2025: "2025-06-30",
}
END = "2026-06-30"
GRAHAM = ("R00", "R03", "R16")
BESST = ("B00", "B00S", "B06", "B06S")
SCENARIOS = ("central", "conservative")


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write(path, rows, cols):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        wr = csv.DictWriter(handle, fieldnames=cols)
        wr.writeheader()
        wr.writerows(rows)


def val(v, name):
    try:
        x = float(v)
    except (ValueError, TypeError):
        raise RuntimeError(f"{name}: número não informado ou inválido ({v!r})")
    if not math.isfinite(x):
        raise RuntimeError(f"{name}: valor não finito")
    return x


def expected_set(rows, keys, expected, label):
    entries = [tuple(r[k] for k in keys) for r in rows]
    if len(entries) != len(expected) or set(entries) != expected:
        raise RuntimeError(f"{label}: combinação duplicada, faltante ou inesperada")


def cumulative_annual(index, start_year, portfolio, scenario=None, field="return"):
    f = 1.0
    for year in range(start_year, 2026):
        k = (str(year), portfolio, scenario) if scenario is not None else str(year)
        row = index[k]
        f *= 1 + val(row[portfolio] if scenario is None else row[field],
                     f"{portfolio} {scenario} {year}")
    return f - 1


def main(graham_dir=None, output_dir=None):
    work = ROOT / "graham_v6_event_results"
    v11 = graham_dir or work / "manutencao_corrigida_v11"
    rs = read(v11 / "graham_18_coortes.csv")
    summary = json.loads((v11 / "resumo_auditoria.json").read_text(encoding="utf-8"))
    graham_status = ("CALCULADO_PROVISORIO_V11_1" if summary.get("documentary_policy")
                     else "CALCULADO_PROVISORIO_V11")
    if summary["legacy_v6_parity"] != "18/18" or summary["first_year_parity"] != "18/18":
        raise RuntimeError("Paridade Graham não passou")
    if summary["execution_errors"] or any(r["status"] == "INCOMPLETO" for r in rs):
        raise RuntimeError("Existem carteiras incompletas: consultar erros_execucao.csv")
    expected_set(rs, ("start_year", "rule"),
                 {(str(y), r) for y in YEAR_START for r in GRAHAM}, "Manutenção Graham")
    for row in rs:
        if row["start"] != YEAR_START[int(row["start_year"])] or row["end"] != END:
            raise RuntimeError("Datas de manutenção Graham incompatíveis com a comparação")
    corrected_annual = read(work / "graham_corrigido_anuais_eventos.csv")
    expected_set(corrected_annual, ("year",), {(str(y),) for y in YEAR_START},
                 "Anuais Graham corrigidos")
    for row in corrected_annual:
        year = int(row["year"])
        if row["start"] != YEAR_START[year] or row["end"] != YEAR_START.get(year + 1, END):
            raise RuntimeError("Datas anuais Graham incompatíveis com a comparação")
    aidx = {r["year"]: r for r in corrected_annual}
    mx = {(r["start_year"], r["rule"]): r for r in rs}

    folder = ROOT / "research" / "graham_v6_comparison"
    annual = read(folder / "besst_v9_annual_frozen.csv")
    maintain = read(folder / "besst_v9_maintenance_frozen.csv")
    frozen_2020 = read(folder / "besst_v9_renewal_frozen.csv")
    expected = {(str(y), t, s) for y in YEAR_START for t in BESST for s in SCENARIOS}
    expected_set(annual, ("year", "strategy", "scenario"), expected, "BESST anual v9")
    expected_set(maintain, ("start_year", "strategy", "scenario"), expected,
                 "BESST manutenção v9")
    expected_set(frozen_2020, ("strategy", "scenario"),
                 {(t, s) for t in BESST for s in SCENARIOS}, "BESST renovação v9")
    bi = {(r["year"], r["strategy"], r["scenario"]): r for r in annual}
    bm = {(r["start_year"], r["strategy"], r["scenario"]): r for r in maintain}
    b20 = {(r["strategy"], r["scenario"]): r for r in frozen_2020}
    for t in BESST:
        for s in SCENARIOS:
            computed = cumulative_annual(bi, 2020, t, s)
            original = val(b20[(t, s)]["return"], f"{t}/{s} retorno v9")
            if not math.isclose(computed, original, abs_tol=1e-9, rel_tol=1e-10):
                raise RuntimeError(f"Reprodução da BESST v9 falhou: {t}/{s}")

    records = []
    for year in YEAR_START:
        duration = (date.fromisoformat(END) - date.fromisoformat(YEAR_START[year])).days / 365.25
        bench_renew = math.prod(1 + val(aidx[str(y)]["BOVA11"], "BOVA")
                                for y in range(year, 2026)) - 1
        bova_values = [val(mx[(str(year), t)]["bova_return"], "BOVA manutenção") for t in GRAHAM]
        if not all(math.isclose(v, bench_renew, abs_tol=1e-9) for v in bova_values):
            raise RuntimeError(f"Datas inconsistentes BOVA11 coorte {year}")
        for strategy in GRAHAM:
            row = mx[(str(year), strategy)]
            renew = cumulative_annual(aidx, year, strategy)
            hold = val(row["maintain_return"], "Graham manutenção")
            if not math.isclose(renew, val(row["renew_return"], "Graham renovação"),
                                rel_tol=1e-10, abs_tol=1e-9):
                raise RuntimeError(f"Renovação Graham inconsistente: {year} {strategy}")
            records.append(dict(start_year=year, strategy=strategy, family="Graham",
                                scenario="corrigido", maintain=hold, renew=renew,
                                maintain_low="", maintain_high="",
                                renew_low="", renew_high="",
                                bova=bench_renew, maintain_cagr=(1+hold)**(1/duration)-1,
                                renew_cagr=(1+renew)**(1/duration)-1,
                                renew_minus_maintain_pp=100*(renew-hold),
                                status=graham_status))
        for strategy in BESST:
            for scenario in SCENARIOS:
                h = bm[(str(year), strategy, scenario)]
                hold = val(h["return"], "BESST manutenção")
                if not (val(h["low"], "manutenção low") <= hold <= val(h["high"], "manutenção high")):
                    raise RuntimeError(f"Limites BESST manutenção inválidos: {year} {strategy} {scenario}")
                renew = cumulative_annual(bi, year, strategy, scenario)
                low = math.prod(1+val(bi[(str(y),strategy,scenario)]["low"],"BESST low")
                                for y in range(year,2026))-1
                high = math.prod(1+val(bi[(str(y),strategy,scenario)]["high"],"BESST high")
                                 for y in range(year,2026))-1
                if not (low - 1e-10 <= renew <= high + 1e-10):
                    raise RuntimeError(f"Limites BESST renovação inválidos: {year} {strategy} {scenario}")
                records.append(dict(start_year=year, strategy=strategy, family="BESST",
                                    scenario=scenario, maintain=hold, renew=renew,
                                    maintain_low=val(h["low"],"manutenção low"),
                                    maintain_high=val(h["high"],"manutenção high"),
                                    renew_low=low, renew_high=high,
                                    bova=bench_renew,
                                    maintain_cagr=(1+hold)**(1/duration)-1,
                                    renew_cagr=(1+renew)**(1/duration)-1,
                                    renew_minus_maintain_pp=100*(renew-hold),
                                    status="PRECISAO_MATERIAL_V9_CENARIO"))
        records.append(dict(start_year=year, strategy="BOVA11", family="Benchmark",
                            scenario="cota", maintain=bench_renew, renew=bench_renew,
                            maintain_low="", maintain_high="", renew_low="", renew_high="",
                            bova=bench_renew,
                            maintain_cagr=(1+bench_renew)**(1/duration)-1,
                            renew_cagr=(1+bench_renew)**(1/duration)-1,
                            renew_minus_maintain_pp=0,
                            status="COTACAO_V6"))
    assert len(records) == 72

    rank = []
    for year in YEAR_START:
        subset = [r for r in records if r["start_year"] == year and
                  (r["family"] != "BESST" or r["scenario"] == "central")]
        for mechanism in ("maintain", "renew"):
            sorted_rows = sorted(subset, key=lambda r: r[mechanism], reverse=True)
            for rank_no, r in enumerate(sorted_rows, 1):
                rank.append(dict(start_year=year, mechanism=mechanism, rank=rank_no,
                                 strategy=r["strategy"], result=r[mechanism],
                                 status=r["status"]))
    out = output_dir or work / "comparacao_manutencao_renovacao_v11"
    write(out / "comparacao_72_cenarios.csv", records,
          ["start_year","strategy","family","scenario","maintain","renew",
           "maintain_low","maintain_high","renew_low","renew_high",
           "bova","maintain_cagr","renew_cagr","renew_minus_maintain_pp","status"])
    write(out / "ranking_central_96_posicoes.csv", rank,
          ["start_year","mechanism","rank","strategy","result","status"])
    report = {
        "provisional": True,
        "Graham_method_version": summary.get("method_version", "v11"),
        "Graham_documentary_policy": summary.get("documentary_policy"),
        "rows": len(records),
        "rankings": len(rank),
        "start_years": list(YEAR_START),
        "Graham": "seleções corrigidas v10, motor v6 até 2026, complementos B3 v11",
        "BESST": "seleções e hipóteses congeladas do Pacote Final v9",
        "BOVA11": "mesmas datas por coorte; retorno nominal",
        "scenario_interpretation": "low/high BESST são sensibilidades, não IC estatísticos",
        "caveat": "sem custo/impostos; proteção de paridade não prova completude documental; não cobre retornos líquidos reais",
        "BESST_dates_evidence": "datas herdadas da especificação v9; os CSVs congelados só contêm anos, sem prova independente das datas de execução",
        "BESST_positions_evidence": "composição, pesos, contribuições e motor v9 não incluídos nos três CSVs congelados; reprodução apenas agregada",
    }
    source_audit_path = work / "auditoria_besst_v9" / "manifesto_auditoria.json"
    if source_audit_path.exists():
        source_audit = json.loads(source_audit_path.read_text(encoding="utf-8"))
        if not source_audit["all_csv_identical"] or not source_audit["dates_match_graham"]:
            raise RuntimeError("Auditoria do pacote Barsi não passou")
        report["BESST_dates_evidence"] = "Datas conferidas no pacote v9 original e em sua reprodução integral"
        report["BESST_positions_evidence"] = (
            f"{source_audit['positions']} registros; {source_audit['portfolio_weight_contribution_checks']} "
            f"carteiras com pesos/contribuições conciliados; {source_audit['patrimony_mismatches']} "
            "posições com ancoragem de retorno sem conciliação de caixa/ações")
        report["BESST_archive_sha256"] = source_audit["archive_sha256"]
        reconciliation_path = work / "auditoria_besst_v9" / "manifesto_patrimonio_conciliado.json"
        if reconciliation_path.exists():
            reconciliation = json.loads(reconciliation_path.read_text(encoding="utf-8"))
            if reconciliation["remaining_arithmetic_mismatches"]:
                raise RuntimeError("Patrimônio Barsi ainda não concilia")
            report["BESST_positions_evidence"] += "; correção de apresentação por checkpoint: 32 divergências resolvidas, retornos preservados"
    (out / "manifesto_comparacao_v11.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("VERIFICADO: 18 Graham + 48 BESST + 6 BOVA = 72 linhas")
    print("RENOVAÇÃO BESST v9: oito cenários reproduzidos integralmente")
    print("RANKING CENTRAL (formação em 2020, final junho/2026):")
    for mechanism in ("maintain","renew"):
        print(f"  {mechanism.upper()}:")
        for r in rank:
            if r["start_year"] == 2020 and r["mechanism"] == mechanism:
                print(f"   #{r['rank']:2} {r['strategy']:6} {r['result']:+.4%} [{r['status']}]")
    print("ARQUIVOS:", out.resolve())
    print("STATUS: PROVISORIO. NÃO PROMOVIDO A RECONCILED.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graham-dir", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    raise SystemExit(main(args.graham_dir, args.out))
