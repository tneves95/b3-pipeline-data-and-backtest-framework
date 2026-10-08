#!/usr/bin/env python3
"""Freeze the B3 index page's official annual responses; no market proxies."""
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/returns_2014_2026_inputs/b3"
ENDPOINT = "https://sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/GetPortfolioDay/"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = []
    for year in range(2014, 2027):
        query = dict(index="IBOVESPA", language="pt-br", year=str(year))
        url = ENDPOINT + base64.b64encode(json.dumps(query, separators=(",", ":")).encode()).decode()
        with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40) as response:
            data = response.read()
        result = json.loads(data)
        if not isinstance(result, dict) or not result.get("results"):
            raise ValueError(f"No official B3 observations for {year}: {result!r}")
        target = OUT / f"ibov_{year}.json"
        target.write_bytes(data)
        sources.append(dict(year=year, url=url, path=target.name,
                            retrieved_at=datetime.now(timezone.utc).isoformat(),
                            sha256=hashlib.sha256(data).hexdigest()))
        print(year, len(result["results"]), flush=True)
    (OUT / "sources.json").write_text(json.dumps(sources, indent=2) + "\n")


if __name__ == "__main__":
    main()
