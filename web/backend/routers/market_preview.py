"""Podgląd OHLCV dla wykresów w UI (serwer — yfinance)."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from web.backend.deps import get_current_user
from web.backend.models import User

router = APIRouter(prefix="/api/preview", tags=["preview"])


@router.get("/ohlcv")
def preview_ohlcv(
    ticker: str = Query(..., min_length=1, max_length=32),
    days: int = Query(120, ge=5, le=800),
    _user: User = Depends(get_current_user),
):
    del _user
    try:
        import yfinance as yf
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    t = yf.Ticker(ticker.strip().upper())
    end = datetime.utcnow().date()
    start = end - timedelta(days=int(days))
    hist = t.history(start=start.isoformat(), end=(end + timedelta(days=1)).isoformat())
    if hist is None or hist.empty:
        raise HTTPException(status_code=404, detail="Brak danych OHLCV.")
    if hist.index.tz is not None:
        hist.index = hist.index.tz_localize(None)
    def _num(x):
        try:
            v = float(x)
            if v != v:  # NaN
                return None
            return v
        except Exception:
            return None

    rows = []
    for idx, row in hist.iterrows():
        d = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
        vol = row["Volume"] if "Volume" in row.index else None
        rows.append(
            {
                "date": d,
                "open": _num(row["Open"]),
                "high": _num(row["High"]),
                "low": _num(row["Low"]),
                "close": _num(row["Close"]),
                "volume": _num(vol) if vol is not None else None,
            }
        )
    return {"ticker": ticker.strip().upper(), "rows": rows}
