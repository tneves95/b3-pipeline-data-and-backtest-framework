#!/usr/bin/env python3
"""Reproduce the user-supplied v9 package in isolation and audit its positions.

The v9 scripts are preserved verbatim. No recalibration or selection change.
The archive and extracted historical source data stay local, outside Git.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from scripts.graham_corrected_maintenance_v11 import read_csv, write_csv


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def extract(archive, target):
    target = target.resolve()
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            if not (target / info.filename).resolve().is_relative_to(target):
                raise ValueError("Unsafe archive member: " + info.filename)
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Archive symlink: " + info.filename)
        z.extractall(target)


def close(a, b, label):
    if not math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=1e-9):
        raise RuntimeError(f"{label}: {a} != {b}")


def main(archive):
    work = Path(".cache/besst_v9_reproduction").resolve()
    if work.exists():
        raise FileExistsError(f"Use a fresh checkout/cache to preserve the earlier reproduction: {work}")
    extract(archive,work)
    package = work / "Barsi_Graham_Comparacao_Final_v9"
    runtime = work / "runtime"
    extract(package/"herdado_v8/Pacote_Barsi_Graham_Retomada_v8_2026-10-05.zip", runtime)
    generated = runtime/"results_v9"
    generated.mkdir(parents=True)
    out = Path("graham_v6_event_results/auditoria_besst_v9")
    out.mkdir(parents=True,exist_ok=True)
    env = dict(os.environ, BG_WORK_ROOT=str(runtime),
               BG_V8_ROOT=str(runtime/"Barsi_Graham_Retomada_v8"),
               BG_RESULTS_ROOT=str(generated),BG_SCRIPT_ROOT=str(package/"scripts"))
    execution = []
    for script in ("compute_besst.py","compute_maintenance.py","complete_graham_maintenance.py","consolidate_v9.py"):
        cp = subprocess.run([sys.executable,str(package/"scripts"/script)],env=env,text=True,capture_output=True)
        (out/(script+".log")).write_text(cp.stdout+cp.stderr)
        execution.append({"script":script,"returncode":cp.returncode,"script_sha256":sha(package/"scripts"/script)})
        if cp.returncode:
            raise RuntimeError(f"v9 failed: {script}; see log in {out}")
    # All generated CSV files, beyond the original package's 11-file control.
    reproductions = []
    for path in sorted(generated.glob("*.csv")):
        reference = package/"resultados"/path.name
        if not reference.is_file():
            raise FileNotFoundError(reference)
        reproductions.append({"file":path.name,"generated_sha256":sha(path),"packaged_sha256":sha(reference),
                              "identical":sha(path)==sha(reference)})
    write_csv(out/"reproducao_arquivos.csv",reproductions,list(reproductions[0]))
    frozen = Path("research/graham_v6_comparison")
    for name,keys,datekey in [("annual",("year","portfolio","scenario"),"year"),
                               ("maintenance",("start_year","portfolio","scenario"),"start_year"),
                               ("renewal",("portfolio","scenario"),None)]:
        original = read_csv(generated/("besst_"+name+".csv"))
        if name=="renewal":original=[r for r in original if r["start_year"]=="2020"]
        index={tuple(r[k] for k in keys):r for r in original}
        for row in read_csv(frozen/("besst_v9_"+name+"_frozen.csv")):
            key=tuple(row["strategy"] if k=="portfolio" else row[k] for k in keys)
            ref=index[key]
            for a,b in [("return","return"),("low","cash_low"),("high","cash_high")]:
                close(row[a],ref[b],f"frozen {name} {key} {a}")
    allocations, totals, anomalies = [], [], []
    for mechanism,portfolio_file,position_file,year_field in [
        ("renew","besst_annual.csv","besst_individual_annual.csv","year"),
        ("maintain","besst_maintenance.csv","besst_maintenance_holdings.csv","start_year")]:
        grouped=defaultdict(list)
        for r in read_csv(generated/position_file):
            grouped[(r[year_field],r["portfolio"],r["scenario"])].append(r)
        for p in read_csv(generated/portfolio_file):
            key=(p[year_field],p["portfolio"],p["scenario"])
            holdings=grouped[key]
            close(sum(float(r["weight"]) for r in holdings),1,f"weights {key}")
            contribution=sum(float(r["weight"])*float(r["return"]) for r in holdings)
            close(contribution,p["return"],f"contributions {mechanism} {key}")
            totals.append(dict(mechanism=mechanism,year=key[0],strategy=key[1],scenario=key[2],
                               start=p["start"],end=p["end"],positions=len(holdings),
                               contribution_sum=contribution,portfolio_return=p["return"],status="OK"))
            for r in holdings:
                allocation=dict(mechanism=mechanism,year=key[0],strategy=key[1],scenario=key[2],
                    ticker=r["ticker"],weight=r["weight"],asset_return=r["return"],
                    contribution=float(r["weight"])*float(r["return"]),final_state=r.get("final_state",""),
                    valuation_delta="",status="AGREGADO_REPRODUZIDO_NAO_CERTIFICADO")
                if mechanism=="maintain":
                    delta=float(r["factor"])-float(r["final_cash"])-float(r["final_stock"])
                    allocation["valuation_delta"]=delta
                    if abs(delta)>1e-9:
                        allocation["status"]="ANCORA_RETORNO_SEM_CONCILIACAO_PATRIMONIAL"
                        anomalies.append(dict(year=key[0],strategy=key[1],scenario=key[2],ticker=r["ticker"],
                             factor=r["factor"],final_cash=r["final_cash"],final_stock=r["final_stock"],
                             delta=delta,weighted_delta_pp=100*float(r["weight"])*delta))
                allocations.append(allocation)
    write_csv(out/"posicoes_contribuicoes_besst.csv",allocations,list(allocations[0]))
    write_csv(out/"validacao_96_carteiras.csv",totals,list(totals[0]))
    write_csv(out/"divergencias_ancoras_patrimonio.csv",anomalies,
              ["year","strategy","scenario","ticker","factor","final_cash","final_stock","delta","weighted_delta_pp"])
    # Preserve the original selections as provenance, never rerun the Graham screen.
    (out/"selection_rows.json").write_bytes((runtime/"selection_rows.json").read_bytes())
    dates={2020:"2020-06-30",2021:"2021-06-30",2022:"2022-06-30",2023:"2023-06-30",2024:"2024-06-28",2025:"2025-06-30"}
    for r in totals:
        assert r["start"]==dates[int(r["year"])]
        assert r["end"]==("2026-06-30" if r["mechanism"]=="maintain" else dates.get(int(r["year"])+1,"2026-06-30"))
    summary={"archive":archive.name,"archive_sha256":sha(archive),"scripts":execution,
             "reproduced_csv_files":len(reproductions),"all_csv_identical":all(r["identical"] for r in reproductions),
             "frozen_aggregate_values":"104/104 rows match source package (48 annual + 48 maintenance + 8 full renewal)",
             "portfolio_weight_contribution_checks":len(totals),"positions":len(allocations),
             "patrimony_mismatches":len(anomalies),"dates_match_graham":True,"certified":False,
             "method_differences":["Barsi material returns: interpolated yearly cash, end-of-interval reinvestment",
               "Some central return factors replaced by v6 checkpoints without updating approximate cash/stock",
               "Sensitivity low/high uses a different approximation where central uses exact anchors",
               "These checks reproduce the prior model; they do not certify point-in-time selection or events"]}
    (out/"manifesto_auditoria.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if not summary["all_csv_identical"]:
        raise RuntimeError("Non-identical reproduction: inspect generated CSV comparison")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive",type=Path)
    main(parser.parse_args().archive)
