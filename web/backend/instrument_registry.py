"""Lista instrumentów (NASDAQ Trader) — cache w pamięci, wyszukiwanie po symbolu i nazwie."""

from __future__ import annotations

import logging
import threading
import time
import urllib.error
import urllib.request
from typing import Any

log = logging.getLogger(__name__)

NASDAQ_TRADED_URL = "https://nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"

_CACHE_ROWS: list[dict[str, str]] | None = None
_CACHE_AT: float = 0.0
_CACHE_LOCK = threading.Lock()
_CACHE_TTL_SEC = 24 * 3600


def _parse_nasdaq_traded_text(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) < 3:
            continue
        if parts[0].lower() == "nasdaq traded" or parts[1].lower() == "symbol":
            continue  # nagłówek
        sym = (parts[1] or "").strip().upper()
        name = (parts[2] or "").strip()
        if not sym or len(sym) > 32:
            continue
        rows.append({"symbol": sym, "name": name})
    return rows


def _fallback_rows() -> list[dict[str, str]]:
    return [
        {"symbol": "MSFT", "name": "Microsoft Corporation"},
        {"symbol": "AAPL", "name": "Apple Inc."},
        {"symbol": "GOOGL", "name": "Alphabet Inc. Class A"},
        {"symbol": "AMZN", "name": "Amazon.com, Inc."},
        {"symbol": "NVDA", "name": "NVIDIA Corporation"},
        {"symbol": "META", "name": "Meta Platforms, Inc."},
        {"symbol": "TSLA", "name": "Tesla, Inc."},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co."},
        {"symbol": "V", "name": "Visa Inc."},
        {"symbol": "WMT", "name": "Walmart Inc."},
    ]


def ensure_instrument_rows() -> list[dict[str, str]]:
    """Ładuje (lub odświeża) pełną listę instrumentów."""
    global _CACHE_ROWS, _CACHE_AT
    now = time.monotonic()
    with _CACHE_LOCK:
        if _CACHE_ROWS is not None and (now - _CACHE_AT) < _CACHE_TTL_SEC:
            return _CACHE_ROWS
        try:
            req = urllib.request.Request(
                NASDAQ_TRADED_URL,
                headers={"User-Agent": "ZadbanoInvestingMasters/1.0"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            parsed = _parse_nasdaq_traded_text(body)
            if len(parsed) < 100:
                raise ValueError(f"za mało rekordów: {len(parsed)}")
            _CACHE_ROWS = parsed
            _CACHE_AT = now
            log.info("Załadowano %s instrumentów z NASDAQ Trader", len(parsed))
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError) as e:
            log.warning("Nie udało się pobrać nasdaqtraded.txt (%s) — używam listy zapasowej.", e)
            _CACHE_ROWS = _fallback_rows()
            _CACHE_AT = now
        return _CACHE_ROWS


def search_instruments(query: str, limit: int = 25) -> list[dict[str, str]]:
    """Dopasowanie po symbolu (prefiks, zawiera) oraz po pełnej / częściowej nazwie."""
    q = (query or "").strip().lower()
    if not q or limit < 1:
        return []
    rows = ensure_instrument_rows()
    starts: list[dict[str, str]] = []
    sym_rest: list[dict[str, str]] = []
    name_hit: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(bucket: list[dict[str, str]], r: dict[str, str]) -> None:
        s = r["symbol"]
        if s in seen:
            return
        seen.add(s)
        bucket.append(r)

    for r in rows:
        sym = r["symbol"].lower()
        nm = r["name"].lower()
        if sym.startswith(q):
            add(starts, r)
        elif q in sym:
            add(sym_rest, r)
        elif q in nm:
            add(name_hit, r)
        else:
            for w in nm.replace(",", " ").split():
                if len(w) >= len(q) and w.startswith(q):
                    add(name_hit, r)
                    break

    out = (starts + sym_rest + name_hit)[:limit]
    return out
