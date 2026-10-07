#!/usr/bin/env python3
"""
Recalcula os retornos anuais Graham R00/R03/R16 corrigidos (2020-2026)
diretamente do banco B3, usando `prices.adj_close` como série de retorno total.

Antes de aceitar os novos resultados, o script faz um CONTROLE DE PARIDADE:
reconstrói as carteiras legadas com as mesmas listas/pesos usados na Retomada v6
e compara com os 18 retornos anuais já conciliados. Se a diferença for material,
o ano/regra fica marcado FAIL e o resumo corrigido permanece explicitamente
"não validado".

Convenção preservada:
- formação/renovação anual em junho;
- R00 e R03: pesos iguais por companhia;
- R16: pesos iguais por grupo setorial, depois iguais dentro do grupo;
- BOVA11: fechamento nominal da cota, sem somar dividendos dos componentes;
- cálculos sem arredondamento intermediário.
"""
import math
import sqlite3
from pathlib import Path

import pandas as pd

DB = "b3_market_data.sqlite"

WINDOWS = {
    2020: ("2020-06-30", "2021-06-30"),
    2021: ("2021-06-30", "2022-06-30"),
    2022: ("2022-06-30", "2023-06-30"),
    2023: ("2023-06-30", "2024-06-28"),
    2024: ("2024-06-28", "2025-06-30"),
    2025: ("2025-06-30", "2026-06-30"),
}

# Retornos anuais conciliados da Retomada v6 — servem APENAS como controle
# de paridade do motor de retorno, não como entrada do resultado corrigido.
LEGACY_RETURNS = {
    2020: {"R00": -0.10805958695585346, "R03": 0.2446490194308152, "R16": 0.37682595688601533},
    2021: {"R00":  0.1970115521926642,  "R03": 0.09267160243531747, "R16": 0.09267160243531747},
    2022: {"R00":  0.370888778944839,   "R03": 0.5439827954420227,  "R16": 0.5338595774190839},
    2023: {"R00":  0.15339450821712253, "R03": 0.14476178316388344, "R16": 0.14863502225019032},
    2024: {"R00":  0.5077432369983123,  "R03": 0.33138657046461983, "R16": 0.2915252198882591},
    2025: {"R00":  0.15820923892087735, "R03": 0.3275467969582439,  "R16": 0.2871067513831422},
}

# Antigas seleções usadas na Retomada v6.
LEGACY_R00 = {
    2020: ["ENBR3","SBSP3","ITSA3","CPLE3","SAPR3"],
    2021: ["ENBR3","CPLE3","SAPR3"],
    2022: ["CPLE3","ENBR3","GRND3","SAPR3","SBSP3","TRIS3"],
    2023: ["CPLE3","SAPR3","SBSP3","TRIS3"],
    2024: ["CMIG3","CPLE3","POMO3","SAPR3","TRIS3"],
    2025: ["CMIG3","CPLE3","FLRY3","SAPR3","TRIS3"],
}
LEGACY_R03 = {
    2020: ["ENBR3","SEER3","SBSP3","LEVE3","ITSA3","CPLE3","SAPR3","SLCE3"],
    2021: ["ENBR3","CSMG3","CPLE3","SAPR3"],
    2022: ["ENBR3","TRIS3","CSMG3","SBSP3","LEVE3","CPLE3","SAPR3","FRAS3","GRND3"],
    2023: ["TRIS3","ENAT3","CSMG3","SBSP3","CPLE3","SAPR3","SLCE3","DXCO3"],
    2024: ["TRIS3","CMIG3","CSMG3","CPLE3","SAPR3","POMO3","SLCE3","KLBN3","PNVL3","LREN3","DXCO3"],
    2025: ["TRIS3","CMIG3","CSMG3","UGPA3","FLRY3","CPLE3","SAPR3","POMO3","PNVL3"],
}

# Seleções corrigidas já fechadas para 2020 e 2021.
CORRECTED_2020_2021 = {
    2020: {
        "R00": ["CPLE3","ENAT3","ENBR3","ITSA3","SAPR3","SBSP3"],
        "R03": ["CPLE3","ENAT3","ENBR3","ITSA3","LEVE3","SAPR3","SBSP3","SEER3","SLCE3"],
        "sectors": {
            "CPLE3":"Energia Elétrica",
            "ENBR3":"Energia Elétrica",
            "ENAT3":"Petróleo e Gás",
            "ITSA3":"Sem Setor Principal",
            "LEVE3":"Máquinas, Equipamentos, Veículos e Peças",
            "SAPR3":"Saneamento, Serv. Água e Gás",
            "SBSP3":"Saneamento, Serv. Água e Gás",
            "SEER3":"Educação",
            "SLCE3":"Agricultura (Açúcar, Álcool e Cana)",
        },
    },
    2021: {
        "R00": ["CPLE3","ENBR3","SAPR3"],
        "R03": ["CPLE3","CSMG3","ENBR3","SAPR3"],
        "sectors": {
            "CPLE3":"Energia Elétrica",
            "ENBR3":"Energia Elétrica",
            "CSMG3":"Saneamento, Serv. Água e Gás",
            "SAPR3":"Saneamento, Serv. Água e Gás",
        },
    },
}

def as_true(v):
    if pd.isna(v):
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int,float)):
        return bool(v)
    return str(v).strip().lower() in {"true","1","yes","sim"}

def load_corrected():
    out = dict(CORRECTED_2020_2021)
    for year in [2022,2023,2024,2025]:
        path = Path(f"graham_final_{year}.csv")
        if not path.exists():
            raise FileNotFoundError(
                f"{path} não encontrado. Rode antes graham_finalize_2022_2025.py."
            )
        d = pd.read_csv(path)
        r00 = sorted(d.loc[d["R00_final"].apply(as_true),"ticker"].tolist())
        r03 = sorted(d.loc[d["R03_final"].apply(as_true),"ticker"].tolist())
        sectors = {
            r["ticker"]: r["sector"]
            for _, r in d[d["ticker"].isin(r03)].iterrows()
        }
        missing = [t for t in r03 if pd.isna(sectors.get(t))]
        if missing:
            raise RuntimeError(f"{year}: selecionadas sem setor: {missing}")
        out[year] = {"R00":r00, "R03":r03, "sectors":sectors}
    return out

def px(con, ticker, date, field):
    r = con.execute(
        f"SELECT {field} FROM prices WHERE ticker=? AND date=? LIMIT 1",
        (ticker,date)
    ).fetchone()
    if not r or r[0] is None:
        raise RuntimeError(f"Preço ausente: {ticker} {date} campo={field}")
    return float(r[0])

def asset_total_return(con, ticker, start, end):
    a0 = px(con,ticker,start,"adj_close")
    a1 = px(con,ticker,end,"adj_close")
    if a0 <= 0 or a1 <= 0:
        raise RuntimeError(f"adj_close inválido: {ticker} {start}->{end}")
    return a1/a0 - 1.0

def equal_weights(names):
    w = 1.0/len(names)
    return {t:w for t in names}

def sector_weights(names, sectors):
    groups = {}
    for t in names:
        sec = sectors[t]
        groups.setdefault(sec,[]).append(t)
    sw = 1.0/len(groups)
    out = {}
    for sec, ts in groups.items():
        for t in ts:
            out[t] = sw/len(ts)
    return out

def portfolio_return(asset_returns, weights):
    if abs(sum(weights.values())-1.0) > 1e-10:
        raise RuntimeError(f"Pesos não somam 1: {sum(weights.values())}")
    return sum(weights[t]*asset_returns[t] for t in weights)

def sector_map_for_legacy(year, corrected):
    # Em 2022-2025 todos os nomes legados estão no CSV final daquele ano.
    # Em 2020-2021 usamos o mapa manual já fechado.
    sectors = dict(corrected[year]["sectors"])
    missing = [t for t in LEGACY_R03[year] if t not in sectors]
    if missing:
        raise RuntimeError(f"{year}: setor legado ausente para {missing}")
    return sectors

def main():
    corrected = load_corrected()
    con = sqlite3.connect(DB)

    position_rows = []
    annual_rows = []
    parity_rows = []

    try:
        # ------------------------------------------------------------
        # 1) PARIDADE: adj_close vs motor legado
        # ------------------------------------------------------------
        print("="*112)
        print("1. CONTROLE DE PARIDADE — adj_close × Retomada v6")
        print("="*112)

        all_parity_ok = True
        # Tolerância: 0,75 ponto percentual por carteira anual.
        # Acima disso, não tratamos adj_close como substituto validado do motor anterior.
        tol = 0.0075

        for year,(start,end) in WINDOWS.items():
            names_union = sorted(set(LEGACY_R00[year]) | set(LEGACY_R03[year]))
            ar = {t:asset_total_return(con,t,start,end) for t in names_union}

            r00 = portfolio_return(ar,equal_weights(LEGACY_R00[year]))
            r03 = portfolio_return(ar,equal_weights(LEGACY_R03[year]))
            sw = sector_weights(
                LEGACY_R03[year],
                sector_map_for_legacy(year,corrected)
            )
            r16 = portfolio_return(ar,sw)

            vals = {"R00":r00,"R03":r03,"R16":r16}
            for rule in ["R00","R03","R16"]:
                ref = LEGACY_RETURNS[year][rule]
                diff = vals[rule]-ref
                ok = abs(diff) <= tol
                all_parity_ok &= ok
                parity_rows.append({
                    "year":year,"rule":rule,
                    "adjclose_return":vals[rule],
                    "legacy_v6_return":ref,
                    "diff":diff,"ok":ok
                })
                print(
                    f"{year} {rule:3s} | adj={vals[rule]:+.6%} "
                    f"| v6={ref:+.6%} | Δ={diff:+.4%} | "
                    f"{'OK' if ok else 'FAIL'}"
                )

        parity = pd.DataFrame(parity_rows)
        parity.to_csv(
            "graham_return_parity_2020_2026.csv",
            index=False,encoding="utf-8-sig"
        )

        print("\nPARIDADE GLOBAL:", "OK" if all_parity_ok else "FAIL")

        # ------------------------------------------------------------
        # 2) RETORNOS CORRIGIDOS
        # ------------------------------------------------------------
        print("\n" + "="*112)
        print("2. RETORNOS ANUAIS CORRIGIDOS")
        print("="*112)

        for year,(start,end) in WINDOWS.items():
            sel = corrected[year]
            names_union = sorted(set(sel["R00"]) | set(sel["R03"]))
            ar = {t:asset_total_return(con,t,start,end) for t in names_union}

            w00 = equal_weights(sel["R00"])
            w03 = equal_weights(sel["R03"])
            w16 = sector_weights(sel["R03"],sel["sectors"])

            r00 = portfolio_return(ar,w00)
            r03 = portfolio_return(ar,w03)
            r16 = portfolio_return(ar,w16)

            b0 = px(con,"BOVA11",start,"close")
            b1 = px(con,"BOVA11",end,"close")
            bova = b1/b0 - 1.0

            annual_rows.append({
                "formation_year":year,
                "start":start,"end":end,
                "N_R00":len(sel["R00"]),
                "N_R03":len(sel["R03"]),
                "N_R16":len(sel["R03"]),
                "R00":r00,"R03":r03,"R16":r16,"BOVA11":bova,
                "parity_global_ok":all_parity_ok,
            })

            print(
                f"{year}–{year+1} | "
                f"R00 {r00:+.4%} | R03 {r03:+.4%} | "
                f"R16 {r16:+.4%} | BOVA11 {bova:+.4%}"
            )

            for rule, weights in [("R00",w00),("R03",w03),("R16",w16)]:
                for t,w in sorted(weights.items()):
                    position_rows.append({
                        "formation_year":year,
                        "start":start,"end":end,
                        "rule":rule,"ticker":t,
                        "sector":sel["sectors"].get(t),
                        "weight":w,
                        "asset_total_return":ar[t],
                        "contribution":w*ar[t],
                    })

        annual = pd.DataFrame(annual_rows)
        positions = pd.DataFrame(position_rows)

        annual.to_csv(
            "graham_returns_corrected_2020_2026.csv",
            index=False,encoding="utf-8-sig"
        )
        positions.to_csv(
            "graham_positions_corrected_2020_2026.csv",
            index=False,encoding="utf-8-sig"
        )

        # ------------------------------------------------------------
        # 3) ENCADEAMENTO 2020-2026
        # ------------------------------------------------------------
        print("\n" + "="*112)
        print("3. RENOVAÇÃO ANUAL ENCADEADA — 30/06/2020 → 30/06/2026")
        print("="*112)

        summary = []
        for rule in ["R00","R03","R16","BOVA11"]:
            factor = float((1.0 + annual[rule]).prod())
            accumulated = factor - 1.0
            cagr = factor**(1/6)-1.0
            final = 10000*factor
            summary.append({
                "rule":rule,
                "accumulated_return":accumulated,
                "cagr":cagr,
                "final_per_10000":final,
                "parity_global_ok":all_parity_ok,
            })
            print(
                f"{rule:6s} | acumulado {accumulated:+.4%} "
                f"| CAGR {cagr:+.4%} | R$ {final:,.2f}"
            )

        pd.DataFrame(summary).to_csv(
            "graham_summary_corrected_2020_2026.csv",
            index=False,encoding="utf-8-sig"
        )

        # ------------------------------------------------------------
        # 4) DELTA VS RESULTADO ANTIGO
        # ------------------------------------------------------------
        print("\n" + "="*112)
        print("4. DELTA VS RETOMADA v6")
        print("="*112)

        old_factor = {}
        for rule in ["R00","R03","R16"]:
            f=1.0
            for y in WINDOWS:
                f *= 1.0 + LEGACY_RETURNS[y][rule]
            old_factor[rule]=f

        for rule in ["R00","R03","R16"]:
            new_factor=float((1.0+annual[rule]).prod())
            print(
                f"{rule}: antigo {(old_factor[rule]-1):+.4%} "
                f"→ corrigido {(new_factor-1):+.4%} "
                f"| Δ {(new_factor-old_factor[rule]):+.4%}"
            )

        print("\nArquivos:")
        print("  graham_return_parity_2020_2026.csv")
        print("  graham_returns_corrected_2020_2026.csv")
        print("  graham_positions_corrected_2020_2026.csv")
        print("  graham_summary_corrected_2020_2026.csv")

        if not all_parity_ok:
            print(
                "\nATENÇÃO: a paridade com a Retomada v6 FALHOU em pelo menos "
                "um caso. Não trate o resumo corrigido como definitivo até "
                "reconciliar as linhas FAIL."
            )
        else:
            print(
                "\nPARIDADE VALIDADA. O resumo corrigido pode substituir "
                "a seleção/renovação Graham anterior."
            )

    finally:
        con.close()

if __name__ == "__main__":
    main()
