#!/usr/bin/env python3
"""
Próbne zapytania do wybranych endpointów Alpha Vantage (wymaga ALPHA_VANTAGE_API_KEY).
Uruchom z katalogu projektu:  python scripts/sample_alphavantage_endpoints.py

Zapisuje skrócone metadane odpowiedzi (klucze JSON / pierwsze znaki CSV) do stdout,
aby dopasować formatowanie w ``tool_json_formatter`` / ``tool_json_financial``.
"""

from __future__ import annotations

import json
import os
import sys

import requests

BASE = "https://www.alphavantage.co/query"
SYMBOL = "IBM"


def call(params: dict) -> tuple[str, object]:
    r = requests.get(BASE, params=params, timeout=60)
    r.raise_for_status()
    text = r.text
    try:
        return "json", json.loads(text)
    except json.JSONDecodeError:
        return "text", text[:800]


def main() -> int:
    key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not key:
        print("Brak ALPHA_VANTAGE_API_KEY — pomijam próby sieciowe.", file=sys.stderr)
        return 1

    common = {"apikey": key, "symbol": SYMBOL}

    specs = [
        ("TIME_SERIES_INTRADAY", {**common, "function": "TIME_SERIES_INTRADAY", "interval": "5min", "outputsize": "compact"}),
        ("TIME_SERIES_DAILY_ADJUSTED", {**common, "function": "TIME_SERIES_DAILY_ADJUSTED", "outputsize": "compact"}),
        ("RSI", {**common, "function": "RSI", "interval": "daily", "series_type": "close", "time_period": "14"}),
        ("MFI", {**common, "function": "MFI", "interval": "daily", "series_type": "close", "time_period": "14"}),
        ("OVERVIEW", {**common, "function": "OVERVIEW"}),
        ("BALANCE_SHEET", {**common, "function": "BALANCE_SHEET"}),
        ("INCOME_STATEMENT", {**common, "function": "INCOME_STATEMENT"}),
        ("CASH_FLOW", {**common, "function": "CASH_FLOW"}),
        ("NEWS_SENTIMENT", {"function": "NEWS_SENTIMENT", "apikey": key, "tickers": SYMBOL, "limit": "5"}),
    ]

    for name, params in specs:
        kind, body = call(params)
        print(f"\n=== {name} ({kind}) ===")
        if kind == "json" and isinstance(body, dict):
            print("keys:", sorted(body.keys())[:40])
            if "feed" in body:
                print("feed[0] keys:", sorted((body["feed"] or [{}])[0].keys())[:30] if body.get("feed") else [])
        else:
            print(str(body)[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
