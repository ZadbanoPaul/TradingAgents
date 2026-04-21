"""Cache odpowiedzi HTTP Alpha Vantage (tekst) — klucz z funkcji + parametrów, TTL wg katalogu serii."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from tradingagents.dataflows.av_series_catalog import ttl_for_function


def cache_directory() -> Path:
    """Katalog plików cache (do statystyk API)."""
    return _cache_root()


def _cache_root() -> Path:
    base = os.getenv("TRADINGAGENTS_AV_HTTP_CACHE")
    if base:
        return Path(base)
    home = Path(os.path.expanduser("~")) / ".tradingagents" / "av_http_cache"
    home.mkdir(parents=True, exist_ok=True)
    return home


def _key(function_name: str, api_params: dict[str, Any]) -> str:
    stable = {k: v for k, v in sorted(api_params.items()) if k not in ("apikey", "function")}
    raw = json.dumps({"f": function_name, "p": stable}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _meta_path(key: str) -> Path:
    return _cache_root() / f"{key}.meta.json"


def _body_path(key: str) -> Path:
    return _cache_root() / f"{key}.body.txt"


def try_get_cached(function_name: str, api_params: dict[str, Any]) -> str | None:
    if os.getenv("TRADINGAGENTS_AV_HTTP_CACHE_DISABLE", "").lower() in ("1", "true", "yes"):
        return None
    key = _key(function_name, api_params)
    mp = _meta_path(key)
    bp = _body_path(key)
    if not mp.is_file() or not bp.is_file():
        return None
    try:
        meta = json.loads(mp.read_text(encoding="utf-8"))
        fetched = float(meta.get("fetched_at", 0))
        ttl = float(meta.get("ttl_seconds", ttl_for_function(function_name)))
        if time.time() - fetched > ttl:
            return None
        return bp.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def store_cached(function_name: str, api_params: dict[str, Any], response_text: str) -> None:
    if os.getenv("TRADINGAGENTS_AV_HTTP_CACHE_DISABLE", "").lower() in ("1", "true", "yes"):
        return
    # nie cache'uj komunikatów błędów JSON
    s = (response_text or "").strip()
    if s.startswith("{") and ("Error Message" in s or "Information" in s):
        try:
            j = json.loads(s)
            if j.get("Error Message") or (isinstance(j.get("Information"), str) and "rate limit" in j["Information"].lower()):
                return
        except json.JSONDecodeError:
            pass
    key = _key(function_name, api_params)
    root = _cache_root()
    root.mkdir(parents=True, exist_ok=True)
    ttl = ttl_for_function(function_name)
    _meta_path(key).write_text(
        json.dumps({"fetched_at": time.time(), "ttl_seconds": ttl, "function": function_name}, indent=0),
        encoding="utf-8",
    )
    _body_path(key).write_text(response_text, encoding="utf-8", errors="replace")
