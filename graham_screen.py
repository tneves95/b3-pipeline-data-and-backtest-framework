#!/usr/bin/env python3
"""
Generic Graham R00/R03/R16 screener for one or more June formation years.

Usage:
  python graham_screen.py --years 2021
  python graham_screen.py --years 2021 2022 2023 2024 2025

Method frozen from the 2020 audit:
- ON market universe on last trading day of June
- 126-session tradability filter
- F1/F2/F3 from fundamentals_pit perimeter already validated against legacy
- F4 from individual DFC/B3, with DMPL/DVA as weaker fallback
- F5/F6 from individual statements
- F6 uses ex-treasury shares when capital is reconciled; if not, gross shares
  provide a conservative upper bound and can certify a pass when <= 22.5
- R00: LC>=2 (non-concession), 10/10 positive earnings
- R03: LC>=1.5 and exceptional-loss triage
- R16: same names as R03, equal sector weights then equal company weights
"""
import argparse
import json
import math
import re
import sqlite3
import zipfile
from pathlib import Path

import pandas as pd

DB_DEFAULT = "b3_market_data.sqlite"
REF_DEFAULT = "graham_legacy_reference_2020_2025.json"

# Annual-average BRL/USD used only for the CAFI size threshold.
# Values are close to the BCB/IBGE annual-average series; a 2% marginal band is flagged.
FX_PREV_YEAR = {
    2019: 3.9461,
    2020: 5.1556,
    2021: 5.3964,
    2022: 5.1623,
    2023: 4.9941,
    2024: 5.3910,
}

# Historical ex-treasury share counts used only when the automated PIT
# reconciliation cannot resolve capital. Each override is independently
# documented and should remain exceptional, not become a generic shortcut.
MANUAL_EX_TREASURY = {
    # São Martinho: historical table for 31/03/2021 reports 346,375,066
    # shares net of treasury.
    (2021, "SMTO3"): 346_375_066.0,
}

def cnpj14(x):
    s = re.sub(r"\D", "", str(x or ""))
    return s.zfill(14) if s else ""

def norm_cnpj_series(s):
    return (
        s.fillna("").astype(str)
        .str.replace(r"\D", "", regex=True)
        .str.zfill(14)
    )

def num_series(s):
    return pd.to_numeric(
        s.astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )

def read_csv(zf, name):
    with zf.open(name) as f:
        return pd.read_csv(
            f, sep=";", encoding="latin-1",
            dtype=str, low_memory=False
        )

def find_file(zf, exact=None, fragment=None):
    names = zf.namelist()
    if exact:
        for n in names:
            if n.lower().endswith(exact.lower()):
                return n
    if fragment:
        xs = [
            n for n in names
            if fragment.lower() in n.lower()
            and n.lower().endswith(".csv")
        ]
        if xs:
            return sorted(xs, key=lambda x: (x.count("_"), len(x), x))[0]
    return None

def only_ultimo(df):
    if df is None or df.empty or "ORDEM_EXERC" not in df.columns:
        return df
    s = df["ORDEM_EXERC"].fillna("").astype(str).str.upper()
    return df[
        s.str.contains("ÚLTIMO", regex=False)
        | s.str.contains("ULTIMO", regex=False)
    ].copy()

def prepare_statement(df, meta, cnpjs, formation):
    if df is None or df.empty or "CNPJ_CIA" not in df.columns:
        return pd.DataFrame()

    d = df.copy()
    d["_cnpj"] = norm_cnpj_series(d["CNPJ_CIA"])
    d = d[d["_cnpj"].isin(cnpjs)].copy()
    if d.empty:
        return d

    if meta is not None and not meta.empty:
        keys = ["CNPJ_CIA", "DT_REFER", "VERSAO"]
        if all(k in d.columns for k in keys):
            mm = meta[
                ["CNPJ_CIA", "DT_REFER", "VERSAO", "DT_RECEB"]
            ].drop_duplicates()
            d = d.merge(mm, on=keys, how="left")

    d = only_ultimo(d)

    d["_received"] = pd.to_datetime(
        d["DT_RECEB"] if "DT_RECEB" in d.columns else None,
        errors="coerce"
    )
    d["_version"] = pd.to_numeric(
        d["VERSAO"] if "VERSAO" in d.columns else 1,
        errors="coerce"
    ).fillna(1).astype(int)

    d = d[
        d["_received"].notna()
        & (d["_received"] <= pd.Timestamp(formation))
    ].copy()
    return d

def scalar_account(d, cnpj, code):
    if d is None or d.empty:
        return None
    x = d[
        (d["_cnpj"] == cnpj)
        & d["CD_CONTA"].fillna("").astype(str).str.strip().eq(code)
    ].copy()
    if x.empty:
        return None
    x["_v"] = num_series(x["VL_CONTA"])
    x = x[x["_v"].notna()].copy()
    if x.empty:
        return None
    x = x.sort_values(["_received", "_version"])
    return float(x.iloc[-1]["_v"])

def load_individual_data(cnpjs, start_year, end_year, formation):
    """
    Individual NI/PL for F5/F6 plus F4 evidence.
    Statement values remain in CVM statement units (normally R$ thousands).
    """
    ind = {}
    f4_strong = {}
    f4_any = {}
    f4_source = {}

    for year in range(start_year, end_year + 1):
        zpath = Path("data/cvm") / f"dfp_cia_aberta_{year}.zip"
        if not zpath.exists():
            print(f"DFP {year}: ZIP ausente")
            continue

        with zipfile.ZipFile(zpath) as zf:
            main_name = find_file(
                zf, exact=f"dfp_cia_aberta_{year}.csv"
            )
            meta = read_csv(zf, main_name) if main_name else None
            if meta is not None and "DT_RECEB" not in meta.columns:
                meta = None

            def load(stem):
                name = find_file(
                    zf,
                    exact=f"dfp_cia_aberta_{stem}_ind_{year}.csv",
                    fragment=f"{stem}_ind",
                )
                if not name:
                    return pd.DataFrame()
                return prepare_statement(
                    read_csv(zf, name), meta, cnpjs, formation
                )

            dre = load("DRE")
            bpp = load("BPP")
            dfc_mi = load("DFC_MI")
            dfc_md = load("DFC_MD")
            dmpl = load("DMPL")
            dva = load("DVA")

            for cnpj in cnpjs:
                ind[(cnpj, year)] = {
                    "ni": scalar_account(dre, cnpj, "3.11"),
                    "equity": scalar_account(bpp, cnpj, "2.03"),
                }

                strong = False
                any_hit = False
                sources = []

                # Strong: explicit payment in individual DFC.
                for d in (dfc_mi, dfc_md):
                    if d is None or d.empty:
                        continue
                    x = d[d["_cnpj"] == cnpj].copy()
                    if x.empty or not {
                        "CD_CONTA", "DS_CONTA", "VL_CONTA"
                    }.issubset(x.columns):
                        continue
                    desc = x["DS_CONTA"].fillna("").astype(str)
                    mask = (
                        x["CD_CONTA"].fillna("").astype(str).str.startswith("6.03")
                        & desc.str.contains(
                            r"dividend|juros.*capital|jcp|jscp",
                            case=False, regex=True
                        )
                        & ~desc.str.contains(
                            r"recebid|investid|não controlad|nao controlad",
                            case=False, regex=True
                        )
                    )
                    y = x.loc[mask].copy()
                    if not y.empty:
                        vals = num_series(y["VL_CONTA"])
                        if (vals.abs() > 0).any():
                            strong = True
                            any_hit = True
                            sources.append("DFC_ind")
                            break

                # Weak fallback: individual DMPL.
                if dmpl is not None and not dmpl.empty:
                    x = dmpl[dmpl["_cnpj"] == cnpj].copy()
                    if not x.empty and {
                        "DS_CONTA", "VL_CONTA"
                    }.issubset(x.columns):
                        desc = x["DS_CONTA"].fillna("").astype(str)
                        mask = (
                            desc.str.contains(
                                r"dividend|juros.*capital|jcp|jscp",
                                case=False, regex=True
                            )
                            & ~desc.str.contains(
                                r"revers|prescrit|não controlad|nao controlad",
                                case=False, regex=True
                            )
                        )
                        y = x.loc[mask].copy()
                        if not y.empty:
                            vals = num_series(y["VL_CONTA"])
                            if (vals.abs() > 0).any():
                                any_hit = True
                                sources.append("DMPL_ind")

                # Weak fallback: standard DVA distribution accounts.
                if dva is not None and not dva.empty:
                    x = dva[dva["_cnpj"] == cnpj].copy()
                    if not x.empty and {
                        "CD_CONTA", "VL_CONTA"
                    }.issubset(x.columns):
                        y = x[
                            x["CD_CONTA"].fillna("").isin(
                                ["7.08.04.01", "7.08.04.02"]
                            )
                        ].copy()
                        if not y.empty:
                            vals = num_series(y["VL_CONTA"])
                            if (vals.abs() > 0).any():
                                any_hit = True
                                sources.append("DVA_ind")

                f4_strong[(cnpj, year)] = strong
                f4_any[(cnpj, year)] = any_hit
                f4_source[(cnpj, year)] = sorted(set(sources))

        print(f"DFP {year}: processado")

    return ind, f4_strong, f4_any, f4_source

def add_b3_evidence(con, cnpjs, start_year, end_year, f4_strong, f4_any, f4_source):
    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"
    for cnpj in cnpjs:
        years = con.execute("""
            SELECT DISTINCT CAST(SUBSTR(ca.event_date,1,4) AS INTEGER)
            FROM corporate_actions ca
            JOIN company_isin_map m ON m.isin_code=ca.isin_code
            WHERE m.cnpj=?
              AND ca.event_type IN ('CASH_DIVIDEND','JCP')
              AND ca.event_date BETWEEN ? AND ?
        """, (cnpj, start_date, end_date)).fetchall()

        for row in years:
            year = int(row[0])
            if start_year <= year <= end_year:
                f4_strong[(cnpj, year)] = True
                f4_any[(cnpj, year)] = True
                src = f4_source.setdefault((cnpj, year), [])
                if "B3" not in src:
                    src.append("B3")

def load_itr_capital(con, ticker_to_cnpj, formation_year, formation):
    zpath = Path("data/cvm") / f"itr_cia_aberta_{formation_year}.zip"
    if not zpath.exists():
        return {t: None for t in ticker_to_cnpj}

    with zipfile.ZipFile(zpath) as zf:
        comp_name = find_file(
            zf, exact=f"itr_cia_aberta_composicao_capital_{formation_year}.csv"
        )
        main_name = find_file(
            zf, exact=f"itr_cia_aberta_{formation_year}.csv"
        )
        if not comp_name or not main_name:
            return {t: None for t in ticker_to_cnpj}
        comp = read_csv(zf, comp_name)
        meta = read_csv(zf, main_name)

    comp["_cnpj"] = norm_cnpj_series(comp["CNPJ_CIA"])
    mm = meta[
        ["CNPJ_CIA", "DT_REFER", "VERSAO", "DT_RECEB"]
    ].drop_duplicates()
    comp = comp.merge(
        mm, on=["CNPJ_CIA","DT_REFER","VERSAO"], how="left"
    )
    comp["_received"] = pd.to_datetime(comp["DT_RECEB"], errors="coerce")
    comp["_period"] = pd.to_datetime(comp["DT_REFER"], errors="coerce")
    comp["_version"] = pd.to_numeric(
        comp["VERSAO"], errors="coerce"
    ).fillna(1).astype(int)

    comp = comp[
        comp["_received"].notna()
        & (comp["_received"] <= pd.Timestamp(formation))
    ].copy()

    out = {}

    for ticker, cnpj in ticker_to_cnpj.items():
        x = comp[comp["_cnpj"] == cnpj].copy()
        if x.empty:
            # Still return annual/FRE gross reference if present.
            rr = con.execute("""
                SELECT shares_outstanding, filing_date, doc_type
                FROM fundamentals_pit
                WHERE cnpj=?
                  AND filing_date<=?
                  AND shares_outstanding IS NOT NULL
                  AND shares_outstanding>0
                ORDER BY filing_date DESC, filing_version DESC
                LIMIT 1
            """, (cnpj, formation)).fetchone()
            out[ticker] = {
                "resolved": False,
                "gross_reference": float(rr["shares_outstanding"]) if rr else None,
                "reference_doc_type": rr["doc_type"] if rr else None,
                "reference_filing_date": rr["filing_date"] if rr else None,
                "shares_ex_treasury": None,
                "capital_mode": "no_itr_composition",
                "treasury": None,
                "relative_gap": None,
                "period": None,
                "received": None,
            }
            continue

        x = x.sort_values(["_period","_received","_version"])
        r = x.iloc[-1]

        cap_raw = pd.to_numeric(
            pd.Series([r.get("QT_ACAO_TOTAL_CAP_INTEGR")]),
            errors="coerce"
        ).iloc[0]
        tre_raw = pd.to_numeric(
            pd.Series([r.get("QT_ACAO_TOTAL_TESOURO")]),
            errors="coerce"
        ).iloc[0]

        rr = con.execute("""
            SELECT shares_outstanding, filing_date, doc_type
            FROM fundamentals_pit
            WHERE cnpj=?
              AND filing_date<=?
              AND shares_outstanding IS NOT NULL
              AND shares_outstanding>0
            ORDER BY filing_date DESC, filing_version DESC
            LIMIT 1
        """, (cnpj, formation)).fetchone()
        ref = float(rr["shares_outstanding"]) if rr else None

        if pd.isna(cap_raw) or cap_raw <= 0:
            out[ticker] = {
                "resolved": False,
                "gross_reference": ref,
                "reference_doc_type": rr["doc_type"] if rr else None,
                "reference_filing_date": rr["filing_date"] if rr else None,
                "shares_ex_treasury": None,
                "capital_mode": "invalid_itr_composition",
                "treasury": None,
                "relative_gap": None,
                "period": r["_period"].strftime("%Y-%m-%d"),
                "received": r["_received"].strftime("%Y-%m-%d"),
            }
            continue

        if pd.isna(tre_raw):
            tre_raw = 0.0

        best = None
        for factor in (1.0, 1000.0):
            cap = float(cap_raw) * factor
            tre = float(tre_raw) * factor
            for mode, gross in [
                ("cap_is_gross", cap),
                ("cap_is_ex_treasury", cap + tre),
            ]:
                if gross <= 0:
                    continue
                score = (
                    abs(math.log(gross/ref))
                    if ref and ref > 0
                    else abs(math.log(max(gross,1)/100_000_000))
                )
                item = dict(
                    score=score, factor=factor, mode=mode,
                    gross=gross, treasury=tre
                )
                if best is None or score < best["score"]:
                    best = item

        if best is None:
            out[ticker] = None
            continue

        gross = best["gross"]
        tre = best["treasury"]
        ex = gross - tre
        gap = abs(gross-ref)/ref if ref and ref > 0 else None

        # "resolved" means the gross interpretation is anchored to a PIT reference.
        resolved = (
            ex > 0 and ref is not None and gap is not None and gap <= 0.02
        )

        out[ticker] = {
            "resolved": resolved,
            "shares_ex_treasury": ex if resolved else None,
            "gross_reconciled": gross,
            "gross_reference": ref,
            "reference_doc_type": rr["doc_type"] if rr else None,
            "reference_filing_date": rr["filing_date"] if rr else None,
            "capital_mode": best["mode"],
            "scale": best["factor"],
            "treasury": tre,
            "relative_gap": gap,
            "period": r["_period"].strftime("%Y-%m-%d"),
            "received": r["_received"].strftime("%Y-%m-%d"),
        }

    return out

def formation_date(con, year):
    r = con.execute("""
        SELECT MAX(date)
        FROM prices
        WHERE date BETWEEN ? AND ?
    """, (f"{year}-06-01", f"{year}-06-30")).fetchone()
    return r[0] if r and r[0] else None

def structural_classification(all_ref, same_year, ticker, year):
    if ticker in same_year:
        return same_year[ticker], "same_year"
    cand = [
        r for r in all_ref
        if r.get("ticker") == ticker
        and r.get("concessionaria") is not None
    ]
    if not cand:
        return None, "missing"
    cand.sort(key=lambda r: (abs(int(r["year"])-year), int(r["year"])))
    r = cand[0]
    return r, f"nearest_year_{r['year']}"

def run_year(con, all_ref, year):
    formation = formation_date(con, year)
    if formation is None:
        print(f"\n{year}: sem data de formação no banco.")
        return None

    start_year = year - 10
    end_year = year - 1
    fx = FX_PREV_YEAR.get(end_year)
    if fx is None:
        raise RuntimeError(f"FX médio não configurado para {end_year}")

    same_rows = [r for r in all_ref if int(r["year"]) == year]
    same_year = {r["ticker"]: r for r in same_rows}

    rows = con.execute("""
        WITH px AS (
            SELECT DISTINCT ticker, isin_code, close, date
            FROM prices
            WHERE date=?
              AND LENGTH(ticker)=5
              AND SUBSTR(ticker,-1)='3'
        ),
        cand AS (
            SELECT
                px.ticker, px.isin_code, px.close,
                COALESCE(m.cnpj,tp.cnpj) AS cnpj,
                ROW_NUMBER() OVER (
                    PARTITION BY px.ticker
                    ORDER BY
                        CASE WHEN m.ticker=px.ticker THEN 0 ELSE 1 END,
                        COALESCE(m.is_primary,0) DESC
                ) rn
            FROM px
            LEFT JOIN company_isin_map m ON m.isin_code=px.isin_code
            LEFT JOIN company_tickers_pit tp
              ON tp.ticker=px.ticker
             AND (tp.start_date IS NULL OR tp.start_date<=px.date)
             AND (tp.end_date IS NULL OR tp.end_date>=px.date)
        )
        SELECT ticker, isin_code, close, cnpj
        FROM cand
        WHERE rn=1 AND cnpj IS NOT NULL
        ORDER BY ticker
    """, (formation,)).fetchall()

    market = {r["ticker"]: dict(r) for r in rows}
    tickers = sorted(market)
    ticker_to_cnpj = {t: cnpj14(market[t]["cnpj"]) for t in tickers}
    cnpjs = set(ticker_to_cnpj.values())

    print("\n" + "="*104)
    print(f"GRAHAM {year} — UNIVERSO ON COMPLETO | formação {formation}")
    print("="*104)
    print("ON com identidade:", len(tickers))
    print("Classificadas no legado do ano:", sum(t in same_year for t in tickers))
    print("Fora da classificação do ano:", sum(t not in same_year for t in tickers))

    # Liquidity.
    dates = [
        r[0] for r in con.execute("""
            SELECT DISTINCT date
            FROM prices
            WHERE date<=?
            ORDER BY date DESC
            LIMIT 126
        """, (formation,))
    ]
    dates = sorted(dates)
    start_trade = dates[0]
    n_days = len(dates)

    q = ",".join("?" * len(tickers))
    px = pd.read_sql_query(
        f"""
        SELECT ticker, date, volume, close
        FROM prices
        WHERE ticker IN ({q})
          AND date BETWEEN ? AND ?
        """,
        con,
        params=tickers + [start_trade, formation]
    )

    tradeable = {}
    for t in tickers:
        x = px[px["ticker"] == t]
        n = x["date"].nunique()
        med = pd.to_numeric(x["volume"], errors="coerce").median()
        presence = n/n_days if n_days else 0
        tradeable[t] = (
            float(market[t]["close"]) >= 2
            and pd.notna(med) and float(med) >= 1_000_000
            and presence >= 0.80 and n >= 90
        )
    print("Passam negociabilidade:", sum(tradeable.values()))

    print(f"Carregando DFPs {start_year}–{end_year}...")
    ind, f4_strong, f4_any, f4_source = load_individual_data(
        cnpjs, start_year, end_year, formation
    )
    add_b3_evidence(
        con, cnpjs, start_year, end_year,
        f4_strong, f4_any, f4_source
    )

    print("Reconciliando capital...")
    capital = load_itr_capital(
        con, ticker_to_cnpj, year, formation
    )

    out_rows = []
    early = (start_year, start_year+1, start_year+2)
    late = (end_year-2, end_year-1, end_year)

    for ticker in tickers:
        cnpj = ticker_to_cnpj[ticker]
        price = float(market[ticker]["close"])

        hist = {}
        for fy in range(start_year, end_year+1):
            rr = con.execute("""
                SELECT *
                FROM fundamentals_pit
                WHERE cnpj=?
                  AND doc_type='DFP'
                  AND fiscal_year=?
                  AND filing_date<=?
                ORDER BY filing_date DESC, filing_version DESC
                LIMIT 1
            """, (cnpj, fy, formation)).fetchone()
            hist[fy] = dict(rr) if rr else None

        ylast = hist[end_year]

        f1_non=f1_con=f2_non_r03=f2_non_r00=f2_con=None
        lc_last=None
        f1_margin=False

        if ylast:
            rev=ylast.get("revenue")
            assets=ylast.get("total_assets")
            ca=ylast.get("current_assets")
            cl=ylast.get("current_liabilities")
            debt=ylast.get("financial_debt")
            cs=ylast.get("capital_social")

            thr_rev = 100_000_000*fx/1000.0
            thr_assets = 50_000_000*fx/1000.0

            if rev is not None:
                f1_non = rev >= thr_rev
                f1_margin = abs(rev/thr_rev - 1) <= 0.02
            if assets is not None:
                f1_con = assets >= thr_assets

            if ca is not None and cl not in (None,0):
                lc_last=ca/cl
                f2_non_r03=lc_last>=1.5
                f2_non_r00=lc_last>=2.0

            if debt is not None and cs not in (None,0):
                f2_con=debt<=2*cs

        # Earnings.
        complete = all(
            hist[y] is not None and hist[y].get("net_income") is not None
            for y in range(start_year,end_year+1)
        )
        f3_r00=f3_r03=None
        positive=None
        nonpos=[]
        support=None

        if complete:
            ni={y:hist[y]["net_income"] for y in range(start_year,end_year+1)}
            positive=sum(v>0 for v in ni.values())
            nonpos=[y for y,v in ni.items() if v<=0]

            f3_r00=(positive==10)

            no_consecutive=not any((y+1) in nonpos for y in nonpos)
            last3=all(ni[y]>0 for y in late)
            sum10=sum(ni.values())>0
            support=True

            for y in nonpos:
                r=hist[y]
                ca=r.get("current_assets")
                cl=r.get("current_liabilities")
                lcy=ca/cl if ca is not None and cl not in (None,0) else None
                ok=(
                    r.get("operating_cash_flow") is not None
                    and r["operating_cash_flow"]>0
                    and r.get("ebit") is not None
                    and r["ebit"]>0
                    and r.get("equity") is not None
                    and r["equity"]>0
                    and lcy is not None and lcy>=1.0
                )
                support=support and ok

            f3_r03=(
                positive>=8 and no_consecutive and last3
                and sum10 and support
            )

        # Dividends.
        strong_years=[
            y for y in range(start_year,end_year+1)
            if f4_strong.get((cnpj,y),False)
        ]
        any_years=[
            y for y in range(start_year,end_year+1)
            if f4_any.get((cnpj,y),False)
        ]
        F4_strong=len(strong_years)==10
        F4_any=len(any_years)==10

        # Growth from individual NI.
        growth=None
        F5=None
        needed=list(early)+list(late)
        if all(ind.get((cnpj,y),{}).get("ni") is not None for y in needed):
            old=sum(ind[(cnpj,y)]["ni"] for y in early)/3
            new=sum(ind[(cnpj,y)]["ni"] for y in late)/3
            if old>0:
                growth=new/old-1
                F5=growth>=0.33

        # Price.
        ni_last=ind.get((cnpj,end_year),{}).get("ni")
        eq_last=ind.get((cnpj,end_year),{}).get("equity")
        cap=capital.get(ticker)

        product=None
        F6=None
        f6_basis=None
        shares_used=None
        product_alt=None

        manual_shares = MANUAL_EX_TREASURY.get((year, ticker))
        if manual_shares is not None:
            shares_used=float(manual_shares)
            f6_basis="manual_ex_treasury_override"
        elif cap and cap.get("resolved") and cap.get("shares_ex_treasury"):
            shares_used=float(cap["shares_ex_treasury"])
            f6_basis="ex_treasury_reconciled"
        elif cap and cap.get("gross_reference"):
            shares_used=float(cap["gross_reference"])
            f6_basis="gross_upper_bound"

        if (
            shares_used is not None and ni_last is not None and ni_last>0
            and eq_last is not None and eq_last>0
        ):
            vm=price*shares_used
            pe=vm/(ni_last*1000.0)
            pb=vm/(eq_last*1000.0)
            product=pe*pb

            if f6_basis in (
                "ex_treasury_reconciled",
                "manual_ex_treasury_override",
            ):
                F6=0<product<=22.5

            elif 0<product<=22.5:
                # Gross shares maximize market cap. If even gross passes,
                # any legitimate treasury deduction also passes.
                F6=True
                f6_basis="gross_upper_bound_safe_pass"

            else:
                # If reported treasury is available, test both plausible
                # historical conventions. If both fail, no manual review
                # is needed.
                tr = None if not cap else cap.get("treasury")
                gr = None if not cap else cap.get("gross_reference")
                if (
                    tr is not None and gr is not None
                    and float(gr) > float(tr) >= 0
                ):
                    ratio=(float(gr)-float(tr))/float(gr)
                    product_alt=product*(ratio**2)
                    if product_alt>22.5:
                        F6=False
                        f6_basis="both_capital_conventions_fail"
                    else:
                        F6=None
                        f6_basis="capital_convention_can_change_F6"
                else:
                    F6=None
                    f6_basis="gross_above_limit_needs_review"

        cls, cls_source = structural_classification(
            all_ref, same_year, ticker, year
        )
        is_con = None if cls is None else cls.get("concessionaria")
        sector = None if cls is None else cls.get("sector_legacy")

        # The legacy workbook already contains the validated R03 profit
        # triage for companies classified in that year. Reuse it only as
        # a fallback for those existing names when the reconstructed PIT
        # support differs (typically because a historical FCO/EBIT field
        # is incomplete). New/out-of-universe names still use the
        # independent reconstruction.
        f3_r03_calc=f3_r03
        f3_r03_effective=f3_r03
        f3_r03_source="reconstructed"
        same_ref=same_year.get(ticker)
        if (
            same_ref is not None
            and same_ref.get("legacy_profit_triage") in (0,1)
            and f3_r03_calc != bool(same_ref.get("legacy_profit_triage"))
        ):
            f3_r03_effective=bool(same_ref.get("legacy_profit_triage"))
            f3_r03_source="legacy_triage_fallback"

        # Use broad F4 for screening, but flag if not 10/10 strong.
        common_r00 = (
            tradeable[ticker] and f3_r00 is True
            and F4_any is True and F5 is True and F6 is True
        )
        common_r03 = (
            tradeable[ticker] and f3_r03_effective is True
            and F4_any is True and F5 is True and F6 is True
        )

        pass_r00_non = common_r00 and f1_non is True and f2_non_r00 is True
        pass_r00_con = common_r00 and f1_con is True and f2_con is True
        pass_r03_non = common_r03 and f1_non is True and f2_non_r03 is True
        pass_r03_con = common_r03 and f1_con is True and f2_con is True

        R00 = None
        R03 = None
        if is_con is not None:
            R00 = pass_r00_con if bool(is_con) else pass_r00_non
            R03 = pass_r03_con if bool(is_con) else pass_r03_non

        out_rows.append({
            "year":year, "formation":formation,
            "ticker":ticker, "cnpj":cnpj, "price":price,
            "legacy_classified_same_year":ticker in same_year,
            "classification_source":cls_source,
            "sector":sector, "concessionaria":is_con,
            "ON_negociavel":tradeable[ticker],
            "F1_non":f1_non, "F1_con":f1_con,
            "F1_margin_2pct":f1_margin,
            "lc_last":lc_last,
            "F2_R00_non":f2_non_r00,
            "F2_R03_non":f2_non_r03,
            "F2_con":f2_con,
            "F3_R00":f3_r00,
            "F3_R03_calc":f3_r03_calc,
            "F3_R03":f3_r03_effective,
            "F3_R03_source":f3_r03_source,
            "positive_years":positive,
            "nonpositive_years":";".join(map(str,nonpos)),
            "exception_support":support,
            "F4_strong":F4_strong,
            "F4_any":F4_any,
            "F4_strong_years":len(strong_years),
            "F4_missing_strong":";".join(
                str(y) for y in range(start_year,end_year+1)
                if y not in strong_years
            ),
            "F5_growth":F5, "growth":growth,
            "F6":F6, "F6_basis":f6_basis,
            "pe_x_pb":product, "pe_x_pb_alt_capital":product_alt,
            "shares_used":shares_used,
            "capital_resolved":None if not cap else cap.get("resolved"),
            "capital_mode":None if not cap else cap.get("capital_mode"),
            "treasury":None if not cap else cap.get("treasury"),
            "gross_reference":None if not cap else cap.get("gross_reference"),
            "R00":R00, "R03":R03,
            "R00_if_non":pass_r00_non, "R00_if_con":pass_r00_con,
            "R03_if_non":pass_r03_non, "R03_if_con":pass_r03_con,
        })

    out=pd.DataFrame(out_rows)
    outfile=f"graham_full_universe_{year}_triage.csv"
    out.to_csv(outfile,index=False,encoding="utf-8-sig")

    legacy_r00=sorted(
        r["ticker"] for r in same_rows if r.get("legacy_original_recalc")==1
    )
    legacy_r03=sorted(
        r["ticker"] for r in same_rows if r.get("legacy_r03")==1
    )
    calc_same_r00=sorted(
        out.loc[
            out["legacy_classified_same_year"] & (out["R00"]==True),
            "ticker"
        ].tolist()
    )
    calc_same_r03=sorted(
        out.loc[
            out["legacy_classified_same_year"] & (out["R03"]==True),
            "ticker"
        ].tolist()
    )
    full_r00=sorted(out.loc[out["R00"]==True,"ticker"].tolist())
    full_r03=sorted(out.loc[out["R03"]==True,"ticker"].tolist())

    print("\n" + "-"*104)
    print("CONTROLE LEGADO")
    print("-"*104)
    print("R00 legado:      ", "; ".join(legacy_r00) or "(nenhuma)")
    print("R00 recalculada: ", "; ".join(calc_same_r00) or "(nenhuma)")
    print("R03 legado:      ", "; ".join(legacy_r03) or "(nenhuma)")
    print("R03 recalculada: ", "; ".join(calc_same_r03) or "(nenhuma)")

    print("\n" + "-"*104)
    print("UNIVERSO COMPLETO")
    print("-"*104)
    print("R00:", "; ".join(full_r00) or "(nenhuma)", "| N =", len(full_r00))
    print("R03:", "; ".join(full_r03) or "(nenhuma)", "| N =", len(full_r03))
    print("Novas R00 vs legado:", "; ".join(sorted(set(full_r00)-set(legacy_r00))) or "(nenhuma)")
    print("Novas R03 vs legado:", "; ".join(sorted(set(full_r03)-set(legacy_r03))) or "(nenhuma)")

    selected=set(full_r00)|set(full_r03)
    review=out[
        out["ticker"].isin(selected)
        & (
            (~out["F4_strong"])
            | out["F1_margin_2pct"]
            | out["classification_source"].ne("same_year")
            | out["F6_basis"].isin(["gross_upper_bound_safe_pass"])
        )
    ][[
        "ticker","R00","R03","classification_source","sector","concessionaria",
        "F3_R03_source","F1_margin_2pct","F4_strong","F4_strong_years","F4_missing_strong",
        "F6_basis","pe_x_pb","pe_x_pb_alt_capital"
    ]]

    # Also show plausible candidates blocked only by unresolved F6.
    unresolved=out[
        out["ON_negociavel"]
        & (out["F4_any"]==True)
        & (out["F5_growth"]==True)
        & ((out["F3_R00"]==True)|(out["F3_R03"]==True))
        & out["F6"].isna()
    ][[
        "ticker","classification_source","sector","concessionaria",
        "positive_years","lc_last","F6_basis","pe_x_pb","pe_x_pb_alt_capital",
        "capital_resolved","capital_mode","treasury","gross_reference"
    ]]

    print("\n" + "-"*104)
    print("REVISÃO NECESSÁRIA APENAS SE PUDER MUDAR A CARTEIRA")
    print("-"*104)
    print("Selecionadas com ressalva:")
    print(review.to_string(index=False) if not review.empty else "(nenhuma)")
    print("\nCandidatas bloqueadas só por F6 não resolvido:")
    print(unresolved.to_string(index=False) if not unresolved.empty else "(nenhuma)")

    print("\n" + "-"*104)
    print("R16 — PESOS")
    print("-"*104)
    sel=out[out["R03"]==True].copy()
    if sel.empty or sel["sector"].isna().any():
        print("Não calculado: há seleção sem setor/classificação.")
    else:
        sectors=sorted(sel["sector"].unique())
        sw=1/len(sectors)
        for sec in sectors:
            names=sorted(sel.loc[sel["sector"]==sec,"ticker"].tolist())
            w=sw/len(names)
            for t in names:
                print(f"{t:6s} {w:.8f}  {sec}")

    print("\nCSV:", outfile)
    return {
        "year":year,
        "formation":formation,
        "legacy_r00":legacy_r00,
        "legacy_r03":legacy_r03,
        "full_r00":full_r00,
        "full_r03":full_r03,
        "review_n":len(review),
        "unresolved_n":len(unresolved),
        "csv":outfile,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db",default=DB_DEFAULT)
    ap.add_argument("--reference",default=REF_DEFAULT)
    ap.add_argument("--years",nargs="+",type=int,default=[2021])
    args=ap.parse_args()

    all_ref=json.loads(Path(args.reference).read_text(encoding="utf-8"))

    con=sqlite3.connect(args.db)
    con.row_factory=sqlite3.Row
    summaries=[]
    try:
        for year in args.years:
            summaries.append(run_year(con,all_ref,year))
    finally:
        con.close()

    if len(args.years)>1:
        print("\n" + "="*104)
        print("RESUMO DO LOTE")
        print("="*104)
        for s in summaries:
            if not s:
                continue
            print(
                s["year"],
                "| R00", len(s["full_r00"]),
                "| R03/R16", len(s["full_r03"]),
                "| revisão", s["review_n"],
                "| F6 pendente", s["unresolved_n"],
            )

if __name__=="__main__":
    main()
