"""Local COTAHIST delta overlay: no original database writes or full base copy."""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import defaultdict
import csv
import hashlib
import io
from pathlib import Path
import re
import sqlite3
import zipfile

import pandas as pd
from .audit import guard_space, sha256

EQUITY = re.compile(r"^[A-Z]{4}(?:[3-8]|11)$")
RIGHT = re.compile(r"^[A-Z]{4}[12]$")


def readonly_database(path):
    wal = Path(str(path) + "-wal")
    if wal.exists() and wal.stat().st_size:
        raise RuntimeError("Nonempty source WAL; a consistent snapshot is required")
    conn = sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro&immutable=1", uri=True)
    conn.execute("PRAGMA query_only=ON")
    return conn


def parse_quote(raw, source_file, line_number):
    if raw[:2] != b"01" or raw[24:27] != b"010":
        return None
    ticker = raw[12:24].decode("latin1").strip()
    isin = raw[230:242].decode("latin1").strip()
    if not (EQUITY.fullmatch(ticker) and (isin[6:8] == "AC" or isin[6:10] == "CDAM")
            or RIGHT.fullmatch(ticker)):
        return None
    factor = int(raw[210:217])
    if factor <= 0:
        raise ValueError("Nonpositive quotation factor in original quote")
    day = raw[2:10].decode("ascii")
    return dict(ticker=ticker, isin=isin, date=f"{day[:4]}-{day[4:6]}-{day[6:8]}",
                close=int(raw[108:121]) / 100 / factor, quotation_factor=factor,
                bdi=raw[10:12].decode("ascii"), source_file=source_file,
                source_line=line_number, record_sha256=hashlib.sha256(raw).hexdigest())


def build_overlay(source: Path, output: Path, scratch: Path, cutoffs, years=range(2014, 2027)):
    """Stream originals once; retain deltas, identity spans, calendar and bounded endpoints.

    Every original equity row is reconciled with (ticker,date,ISIN,close,factor)
    in SQLite. Restricted granular outputs stay in the local-only directory.
    """
    output.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    guard_space(output, scratch)
    db = readonly_database(source / "b3_market_data.sqlite")
    path = output / "quote_overlay.sqlite"
    if path.exists():
        raise ValueError("Overlay already exists; use a new run directory to preserve checkpoints")
    overlay = sqlite3.connect(path)
    overlay.execute("CREATE TABLE quotes(ticker TEXT,isin TEXT,date TEXT,close REAL,quotation_factor INTEGER,"
                    "bdi TEXT,source_file TEXT,source_line INTEGER,record_sha256 TEXT,reason TEXT,"
                    "PRIMARY KEY(ticker,date))")
    cutoffs = sorted(set(cutoffs))
    last = {}; snapshots = []; calendar = set(); summaries = []; sources = []; spans = {}
    for year in years:
        guard_space(output, scratch)
        archive = source / "data/raw" / f"COTAHIST_A{year}.ZIP"
        relative = str(archive.relative_to(source))
        sources.append(dict(path=relative, bytes=archive.stat().st_size, sha256=sha256(archive)))
        base = {(t, d): (isin, close, factor) for t, isin, d, close, factor in db.execute(
            "SELECT ticker,isin_code,date,close,quotation_factor FROM prices WHERE date>=? AND date<?",
            (f"{year}-01-01", f"{year+1}-01-01"))}
        stats = defaultdict(int); deltas = []; seen = set(); active_cutoffs = [d for d in cutoffs if int(d[:4]) == year]
        at_cutoff = {cutoff: last.copy() for cutoff in active_cutoffs}
        with zipfile.ZipFile(archive) as z:
            for member in z.namelist():
                if member.endswith("/"):
                    continue
                with io.BufferedReader(z.open(member), buffer_size=1 << 20) as stream:
                    for line_number, raw in enumerate(stream, 1):
                        q = parse_quote(raw, relative, line_number)
                        if q is None:
                            continue
                        day = q['date']
                        # Local 2020/2022 archives contain out-of-order dates.
                        # Compute maxima explicitly; file position is never a time cutoff.
                        for cutoff, state in at_cutoff.items():
                            prior = state.get(q['isin'])
                            if day <= cutoff and (prior is None or day > prior['date']):
                                state[q['isin']] = q
                        calendar.add(day)
                        key = q['ticker'], day
                        if key in seen:
                            raise ValueError(f"Conflicting/duplicate original ticker-date: {key}")
                        seen.add(key)
                        prior = last.get(q['isin'])
                        if prior is None or day > prior['date']:
                            last[q['isin']] = q
                        span = spans.setdefault((q['ticker'], q['isin']), dict(ticker=q['ticker'], isin=q['isin'],
                            first_date=day, last_date=day, rows=0, non_bdi02_rows=0))
                        span['first_date'] = min(span['first_date'], day)
                        span['last_date'] = max(span['last_date'], day)
                        span['rows'] += 1; span['non_bdi02_rows'] += q['bdi'] != '02'
                        is_equity = bool(EQUITY.fullmatch(q['ticker']))
                        stats['original_equity_rows' if is_equity else 'original_right_rows'] += 1
                        stats['bdi_' + q['bdi']] += 1
                        existing = base.get(key)
                        reason = None
                        if existing is None:
                            reason = 'ABSENT_FROM_ORIGINAL_SQLITE'
                            stats['missing_equity_rows' if is_equity else 'missing_right_rows'] += 1
                        elif existing[0] != q['isin']:
                            reason = 'HISTORICAL_ISIN_MISMATCH'; stats['identity_mismatches'] += 1
                        elif existing[1] is None or abs(existing[1] - q['close']) > max(1e-10, abs(q['close']) * 1e-10):
                            reason = 'ORIGINAL_CLOSE_MISMATCH'; stats['close_mismatches'] += 1
                        elif existing[2] != q['quotation_factor']:
                            reason = 'QUOTATION_FACTOR_MISMATCH'; stats['factor_mismatches'] += 1
                        if q['bdi'] != '02' and reason is None:
                            reason = 'NON_BDI02_ORIGINAL_CONFIRMED'
                        if reason:
                            deltas.append(tuple(q[k] for k in ['ticker','isin','date','close','quotation_factor','bdi',
                                'source_file','source_line','record_sha256']) + (reason,))
                        else:
                            stats['sqlite_original_verified'] += 1
        for cutoff, state in at_cutoff.items():
            snapshots.extend(dict(v, cutoff=cutoff) for v in state.values())
        overlay.executemany("INSERT INTO quotes VALUES (?,?,?,?,?,?,?,?,?,?)", deltas)
        overlay.commit()
        summaries.append(dict(year=year, overlay_rows=len(deltas), **stats))
        print(f"COTAHIST {year}: {len(deltas)} overlay records, {stats['missing_equity_rows']} recovered equity trades", flush=True)
    # Unmatured cutoffs can carry a last trade for diagnosis, never calendar completeness.
    for cutoff in [d for d in cutoffs if int(d[:4]) > max(years)]:
        snapshots.extend(dict(v, cutoff=cutoff) for v in last.values())
    overlay.execute("CREATE INDEX quote_isin_date ON quotes(isin,date)")
    overlay.commit(); overlay.close(); db.close()
    pd.DataFrame(summaries).fillna(0).to_csv(output / 'quote_reconstruction_by_year.csv', index=False)
    pd.DataFrame(spans.values()).to_csv(output / 'historical_security_spans.csv', index=False)
    pd.DataFrame({'date': sorted(calendar)}).to_csv(output / 'exchange_calendar.csv', index=False)
    endpoints = pd.DataFrame(snapshots)
    endpoints.to_csv(output / 'endpoint_quote_snapshots.csv', index=False)
    return endpoints, sorted(calendar), sources


def collect_endpoint_quotes(source, cutoffs, years=range(2014, 2027)):
    """Bounded as-of extraction independent of archive ordering and current tickers."""
    cutoffs = sorted(set(cutoffs))
    states = {cutoff: {} for cutoff in cutoffs}
    calendar = set()
    for year in years:
        path = Path(source) / 'data/raw' / f'COTAHIST_A{year}.ZIP'
        with zipfile.ZipFile(path) as z:
            for member in z.namelist():
                if member.endswith('/'): continue
                with io.BufferedReader(z.open(member), buffer_size=1 << 20) as f:
                    for lineno, raw in enumerate(f, 1):
                        q = parse_quote(raw, str(path.relative_to(source)), lineno)
                        if q is None: continue
                        calendar.add(q['date'])
                        for cutoff in cutoffs[bisect_left(cutoffs, q['date']):]:
                            prior = states[cutoff].get(q['isin'])
                            if prior is None or q['date'] > prior['date']:
                                states[cutoff][q['isin']] = q
        print(f'As-of endpoints {year} verified', flush=True)
    return pd.DataFrame([dict(q, cutoff=cutoff) for cutoff, state in states.items() for q in state.values()]), sorted(calendar)


class QuoteBook:
    """Query the source plus the small overlay; prices never cross security identity."""
    def __init__(self, source, overlay, calendar):
        self.base = readonly_database(source)
        self.delta = readonly_database(overlay)
        self.calendar = sorted(calendar)
        self.cache = {}

    def series(self, ticker):
        if ticker not in self.cache:
            rows = {d: dict(ticker=ticker, isin=i, date=d, close=c) for i,d,c in self.base.execute(
                "SELECT isin_code,date,close FROM prices WHERE ticker=? AND date>='2014-01-01'", (ticker,))}
            rows.update({d: dict(ticker=ticker, isin=i, date=d, close=c) for i,d,c in self.delta.execute(
                "SELECT isin,date,close FROM quotes WHERE ticker=?", (ticker,))})
            self.cache[ticker] = (sorted(rows), rows)
        return self.cache[ticker]

    def trade(self, ticker, day, *, isin=None, exact=False, max_age_sessions=0):
        dates, rows = self.series(ticker)
        index = bisect_right(dates, day) - 1
        if index < 0:
            raise ValueError(f"NO_TRADE_AT_OR_BEFORE:{ticker}:{day}")
        row = rows[dates[index]]
        if isin is not None and row['isin'] != isin:
            raise ValueError(f"SECURITY_IDENTITY_CHANGED:{ticker}:{day}")
        if exact and row['date'] != day:
            raise ValueError(f"NO_EXACT_EVENT_QUOTE:{ticker}:{day}")
        age = bisect_right(self.calendar, day) - bisect_right(self.calendar, row['date'])
        if age > max_age_sessions:
            raise ValueError(f"STALE_OR_SUSPENDED_QUOTE:{ticker}:{day}:{age}")
        if row['close'] is None or row['close'] <= 0:
            raise ValueError(f"NONPOSITIVE_QUOTE:{ticker}:{day}")
        return row

    def close(self):
        self.base.close(); self.delta.close()
