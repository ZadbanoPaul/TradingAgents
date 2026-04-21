"""Szybki skan tickerów (OHLC + proste sygnały) — yfinance, bez wywołań LLM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import yfinance as yf

from web.backend.candidate_universe import DEFAULT_US_LIQUID_TICKERS


@dataclass
class ScreenParams:
    tickers: list[str]
    lookback_days: int
    max_rows: int


def _clip(s: str, n: int = 12) -> str:
    x = (s or "").strip().upper()
    return x[:n] if x else ""


def screen_candidates(p: ScreenParams) -> dict[str, Any]:
    if p.lookback_days < 5 or p.lookback_days > 365:
        raise ValueError("lookback_days musi być w zakresie 5–365")
    tickers = [_clip(t) for t in p.tickers if _clip(t)]
    if not tickers:
        raise ValueError("Brak tickerów")
    tickers = tickers[: p.max_rows]
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=p.lookback_days)

    rows: list[dict[str, Any]] = []
    errors: list[str] = []

    for sym in tickers:
        try:
            df = yf.download(
                sym,
                start=start.isoformat(),
                end=(end + timedelta(days=1)).isoformat(),
                progress=False,
                auto_adjust=True,
                threads=False,
            )
            if df is None or df.empty:
                errors.append(f"{sym}: brak danych OHLC")
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [str(c[0]).strip() for c in df.columns]
            closes = df["Close"].dropna()
            highs = df["High"].dropna()
            lows = df["Low"].dropna()
            if closes.empty:
                continue
            last = float(closes.iloc[-1])
            hi = float(highs.max())
            lo = float(lows.min())
            avg = float(closes.mean())
            from_high_pct = ((hi - last) / hi * 100.0) if hi else None
            from_avg_pct = ((last - avg) / avg * 100.0) if avg else None
            rng = hi - lo
            pos_in_range = (last - lo) / rng if rng else None

            mcap = None
            t = yf.Ticker(sym)
            try:
                fi = getattr(t, "fast_info", None)
                if isinstance(fi, dict):
                    mcap = fi.get("market_cap") or fi.get("marketCap")
                elif fi is not None:
                    mcap = getattr(fi, "market_cap", None) or getattr(fi, "marketCap", None)
            except Exception:
                pass
            if mcap is None:
                try:
                    full = t.info
                    mcap = full.get("marketCap") if isinstance(full, dict) else None
                except Exception:
                    mcap = None

            # Prosty „score” sygnału zakupowego: przecena od szczytu + bliskość do dolnego ograniczenia widełek
            score = 0.0
            if from_high_pct is not None:
                score += min(from_high_pct, 40.0) * 1.2
            if from_avg_pct is not None and from_avg_pct < 0:
                score += min(-from_avg_pct, 15.0)
            if pos_in_range is not None and pos_in_range < 0.35:
                score += 8.0

            rows.append(
                {
                    "ticker": sym,
                    "close": round(last, 4),
                    "period_high": round(hi, 4),
                    "period_low": round(lo, 4),
                    "period_avg_close": round(avg, 4),
                    "decline_from_period_high_pct": round(from_high_pct, 2) if from_high_pct is not None else None,
                    "vs_period_avg_pct": round(from_avg_pct, 2) if from_avg_pct is not None else None,
                    "position_in_range_0_1": round(pos_in_range, 3) if pos_in_range is not None else None,
                    "market_cap": int(mcap) if mcap else None,
                    "signal_score": round(score, 2),
                }
            )
        except Exception as e:  # noqa: BLE001
            errors.append(f"{sym}: {e}")

    rows.sort(key=lambda r: r.get("signal_score") or 0, reverse=True)
    return {
        "as_of": end.isoformat(),
        "lookback_days": p.lookback_days,
        "universe_note": (
            "Skan na podstawie listy tickerów (domyślnie duże spółki US). "
            "To nie jest pełny rynek amerykański — do produkcji podłącz własny universe (CSV / API)."
        ),
        "rows": rows,
        "errors": errors[:40],
    }


def default_universe_tickers(max_n: int) -> list[str]:
    return list(DEFAULT_US_LIQUID_TICKERS[:max_n])
