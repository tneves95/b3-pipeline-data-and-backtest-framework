#!/usr/bin/env python3
"""Validate the executed v11 files, including allocated quantities and cash."""
import json
import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from scripts.graham_corrected_maintenance_v11 import read_csv, write_csv


def close(actual, expected):
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-8):
        raise AssertionError(f"{actual} != {expected}")


def main(base=None, comparison=None):
    base = base or Path("graham_v6_event_results/manutencao_corrigida_v11")
    cohorts = read_csv(base / "graham_18_coortes.csv")
    positions = read_csv(base / "graham_posicoes.csv")
    finals = read_csv(base / "posicoes_finais_carteira.csv")
    path = read_csv(base / "trajetoria_anual_manutencao.csv")
    checks = []
    assert len(cohorts) == 18 and len(positions) == 162 and len(path) == 63
    assert not read_csv(base / "erros_execucao.csv")
    for row in cohorts:
        key = (row["start_year"], row["rule"])
        same = lambda r: (r["start_year"],r["rule"]) == key
        ps, fs, trajectory = [r for r in positions if same(r)], [r for r in finals if same(r)], [r for r in path if same(r)]
        close(sum(float(r["weight"]) for r in ps), 1)
        close(sum(float(r["contribution"]) for r in ps), float(row["maintain_return"]))
        for r in ps:
            close(float(r["contribution"]),float(r["weight"])*float(r["return"]))
        close(sum(float(r["final_weight"]) for r in fs), 1)
        close(sum(float(r["value"]) for r in fs),10000*(1+float(row["maintain_return"])))
        allocated = defaultdict(float)
        for r in ps:
            allocated["CASH"] += float(r["cash_final_allocated"])
            for ticker,q in json.loads(r["final_assets_allocated"]).items():
                allocated[ticker] += q
        for r in fs:
            close(allocated.pop(r["asset"],0),float(r["quantity"]))
        assert not allocated
        close(math.prod(1+float(r["period_return"]) for r in trajectory)-1,float(row["maintain_return"]))
        close(float(row["multiasset_delta"]),0)
        checks.append(dict(start_year=key[0],rule=key[1],weights="OK",contributions="OK",
                           final_quantities="OK",final_cash="OK",annual_path="OK",multiasset="OK"))
    comparison = comparison or Path("graham_v6_event_results/comparacao_manutencao_renovacao_v11")
    compare = read_csv(comparison / "comparacao_72_cenarios.csv")
    assert len(compare) == 72
    for r in compare:
        close(float(r["renew_minus_maintain_pp"]),100*(float(r["renew"])-float(r["maintain"])))
    write_csv(base / "validacao_18_coortes.csv",checks,list(checks[0]))
    result = {"cohorts":18,"positions":162,"annual_maintenance_path":63,"comparison_rows":72,
              "quantities_cash_weights_contributions":"18/18 OK","certifies_evidence":False}
    (base/"validacao_execucao.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graham-dir", type=Path)
    parser.add_argument("--comparison-dir", type=Path)
    args = parser.parse_args()
    main(args.graham_dir, args.comparison_dir)
