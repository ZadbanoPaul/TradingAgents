"""Katalog serii Alpha Vantage + statystyki prostego cache HTTP."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from tradingagents.dataflows.av_http_cache import cache_directory
from tradingagents.dataflows.av_series_catalog import list_av_series
from web.backend.deps import get_current_user
from web.backend.models import User

router = APIRouter(prefix="/api/data-catalog", tags=["data-catalog"])


@router.get("/av-series")
def av_series_catalog(_user: User = Depends(get_current_user)):
    del _user
    return {"series": list_av_series(), "source_doc": "https://www.alphavantage.co/documentation/"}


@router.get("/av-cache-stats")
def av_cache_stats(_user: User = Depends(get_current_user)):
    del _user
    root = cache_directory()
    files = list(root.glob("*.body.txt")) if root.is_dir() else []
    metas = list(root.glob("*.meta.json")) if root.is_dir() else []
    newest_iso: str | None = None
    oldest_iso: str | None = None
    newest_ts = 0.0
    oldest_ts = float("inf")
    for mp in metas:
        try:
            meta = json.loads(mp.read_text(encoding="utf-8"))
            ts = float(meta.get("fetched_at", 0))
            if ts <= 0:
                continue
            if ts > newest_ts:
                newest_ts = ts
            if ts < oldest_ts:
                oldest_ts = ts
        except Exception:
            continue
    if newest_ts > 0:
        newest_iso = datetime.fromtimestamp(newest_ts, tz=timezone.utc).isoformat()
    if oldest_ts < float("inf"):
        oldest_iso = datetime.fromtimestamp(oldest_ts, tz=timezone.utc).isoformat()
    return {
        "cache_dir": str(root.resolve()),
        "body_files": len(files),
        "meta_files": len(metas),
        "newest_cached_response_at": newest_iso,
        "oldest_cached_response_at": oldest_iso,
        "note": "Odpowiedzi AV zapisywane przy sukcesie; TTL wg av_series_catalog. Wyłącz: TRADINGAGENTS_AV_HTTP_CACHE_DISABLE=1",
    }
