"""Agregacja zakończonych analiz (jobów) i prosty szkic alokacji portfela."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from web.backend.models import AnalysisJob


def list_completed_jobs(
    db: Session,
    user_id: int,
    date_from: str | None,
    date_to: str | None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    q = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.user_id == user_id, AnalysisJob.status == "completed")
        .order_by(AnalysisJob.id.desc())
    )
    if date_from:
        q = q.filter(AnalysisJob.trade_date >= date_from)
    if date_to:
        q = q.filter(AnalysisJob.trade_date <= date_to)
    rows = q.limit(limit).all()
    out: list[dict[str, Any]] = []
    for j in rows:
        out.append(
            {
                "id": j.id,
                "ticker": j.ticker,
                "trade_date": j.trade_date,
                "final_signal": j.final_signal,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "duration_ms": j.duration_ms,
            }
        )
    return out


def _signal_weight(sig: str | None) -> float:
    if not sig:
        return 0.0
    s = sig.upper()
    if "BUY" in s or "OVERWEIGHT" in s:
        return 1.0
    if "HOLD" in s or "NEUTRAL" in s:
        return 0.35
    if "SELL" in s or "UNDERWEIGHT" in s:
        return 0.0
    return 0.2


def _minute_last_close(sym: str) -> dict[str, Any] | None:
    try:
        df = yf.download(
            sym,
            period="1d",
            interval="1m",
            progress=False,
            auto_adjust=True,
            threads=False,
        )
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [str(c[0]).strip() for c in df.columns]
        last = float(df["Close"].dropna().iloc[-1])
        prev = float(df["Close"].dropna().iloc[-2]) if len(df) > 1 else last
        return {"last_1m_close": last, "prev_1m_close": prev, "bars": len(df)}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)[:200]}


def build_portfolio_draft(
    db: Session,
    user_id: int,
    job_ids: list[int],
    notional_usd: float,
    num_positions: int,
    include_minute_last_day: bool,
) -> dict[str, Any]:
    job_ids = list(dict.fromkeys(job_ids))
    if not job_ids:
        raise ValueError("job_ids nie może być puste")
    if num_positions < 1 or num_positions > 64:
        raise ValueError("num_positions poza zakresem 1–64")
    if notional_usd <= 0:
        raise ValueError("notional_usd musi być > 0")

    jobs = (
        db.query(AnalysisJob)
        .filter(
            AnalysisJob.user_id == user_id,
            AnalysisJob.id.in_(job_ids),
            AnalysisJob.status == "completed",
        )
        .all()
    )
    if len(jobs) != len(set(job_ids)):
        raise ValueError("Nie znaleziono wszystkich jobów (tylko completed / Twój user)")

    ranked: list[tuple[float, AnalysisJob]] = []
    for j in jobs:
        w = _signal_weight(j.final_signal)
        ranked.append((w, j))
    ranked.sort(key=lambda x: x[0], reverse=True)

    picks = [j for w, j in ranked if w > 0][:num_positions]
    if not picks:
        picks = [j for _, j in ranked][: min(3, len(ranked))]

    weights = [max(_signal_weight(j.final_signal), 0.05) for j in picks]
    s = sum(weights) or 1.0
    weights = [w / s for w in weights]

    lines: list[dict[str, Any]] = []
    minute_block: dict[str, Any] = {}
    for j, w in zip(picks, weights):
        row: dict[str, Any] = {
            "job_id": j.id,
            "ticker": j.ticker,
            "trade_date": j.trade_date,
            "final_signal": j.final_signal,
            "weight": round(w, 4),
            "notional_usd": round(notional_usd * w, 2),
            "entry_note": "Wejście: rozważyć skalowanie / potwierdzenie techniczne wg pełnej analizy.",
        }
        if include_minute_last_day and len(minute_block) < 5:
            minute_block[j.ticker] = _minute_last_close(j.ticker)
        lines.append(row)

    summary_md = (
        "| Job | Ticker | Data | Sygnał | Udział | Kwota (USD) |\n"
        "|---:|---|---|---|---:|---:|\n"
        + "\n".join(
            f"| {r['job_id']} | {r['ticker']} | {r['trade_date']} | {r['final_signal'] or '—'} | "
            f"{r['weight']*100:.1f}% | {r['notional_usd']:.2f} |"
            for r in lines
        )
    )

    digest: list[dict[str, Any]] = []
    for j in picks:
        snippet = ""
        if j.result_json:
            try:
                data = json.loads(j.result_json)
                for key in ("investment_plan", "trader_investment_plan", "scoring_report"):
                    t = data.get(key)
                    if isinstance(t, str) and len(t) > 80:
                        snippet = t[:600].replace("\n", " ")
                        break
            except Exception:
                pass
        digest.append({"job_id": j.id, "ticker": j.ticker, "snippet": snippet})

    return {
        "notional_usd": notional_usd,
        "num_positions": num_positions,
        "include_minute_last_day": include_minute_last_day,
        "minute_snapshot": minute_block if include_minute_last_day else {},
        "lines": lines,
        "markdown_table": summary_md,
        "report_digest_for_agents": digest,
        "note": (
            "Szkic portfela rule-based z wagami po sygnałach końcowych jobów. "
            "Pełna synteza przez LLM (agenci) może być dodana jako osobny krok joba."
        ),
    }
