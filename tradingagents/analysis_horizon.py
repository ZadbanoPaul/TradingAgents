"""Horyzont inwestycyjny → okna dat, interwały OHLCV / wskaźników, news (Alpha Vantage / yfinance)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from tradingagents.dataflows.config import get_config


@dataclass(frozen=True)
class DataWindows:
    stock_start: str
    stock_end: str
    use_intraday: bool
    av_intraday_interval: str  # 1min, 5min, 15min, 60min
    price_vendor_interval: str  # label for prompts: intraday_5m, daily, ...
    indicator_interval: str  # Alpha Vantage SMA/RSI interval: daily | 60min | 30min | 15min | 5min | 1min
    indicator_lookback_days: int
    yfinance_indicator_lookback_days: int
    news_start: str
    news_end: str
    news_limit: int
    news_lookback_hours: int | None
    fundamentals_freq: str  # quarterly | annual
    global_news_lookback_days: int
    global_news_limit: int


def _parse_iso(d: str) -> datetime:
    return datetime.strptime(d[:10], "%Y-%m-%d")


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def resolve_data_windows(trade_date: str) -> DataWindows:
    """Łączy `investment_horizon` i parametry news z konfiguracji joba."""
    cfg = get_config()
    horizon = str(cfg.get("investment_horizon") or "swing_medium").lower()
    trade = _parse_iso(trade_date)

    news_mode = str(cfg.get("news_query_mode") or "daterange").lower()
    limit = int(cfg.get("news_article_limit") or 25)
    limit = max(1, min(limit, 200))

    # Domyślne zakresy cenowe / interwały (logika ekonomiczna)
    if horizon == "intraday":
        stock_end = _fmt(trade)
        stock_start = _fmt(trade - timedelta(days=5))
        use_intraday = True
        av_intraday_interval = "5min"
        price_vendor_interval = "intraday_5m"
        indicator_interval = "5min"
        indicator_lookback_days = 5
        yfinance_indicator_lookback_days = 14
        news_hours = int(cfg.get("news_recent_hours") or 36)
        news_hours = max(6, min(news_hours, 72))
        news_start = _fmt(trade - timedelta(hours=news_hours))
        news_end = _fmt(trade)
        news_lookback_hours = news_hours
        global_news_lookback_days = 2
        global_news_limit = min(limit, 30)
        fundamentals_freq = "quarterly"
    elif horizon == "swing_short":
        stock_end = _fmt(trade)
        stock_start = _fmt(trade - timedelta(days=21))
        use_intraday = True
        av_intraday_interval = "15min"
        price_vendor_interval = "intraday_15m_plus_daily"
        indicator_interval = "60min"
        indicator_lookback_days = 14
        yfinance_indicator_lookback_days = 30
        news_hours = int(cfg.get("news_recent_hours") or 120)
        news_hours = max(24, min(news_hours, 240))
        news_start = _fmt(trade - timedelta(hours=news_hours))
        news_end = _fmt(trade)
        news_lookback_hours = news_hours
        global_news_lookback_days = 5
        global_news_limit = min(limit, 40)
        fundamentals_freq = "quarterly"
    elif horizon == "swing_medium":
        stock_end = _fmt(trade)
        stock_start = _fmt(trade - timedelta(days=120))
        use_intraday = False
        av_intraday_interval = "60min"
        price_vendor_interval = "daily"
        indicator_interval = "daily"
        indicator_lookback_days = 60
        yfinance_indicator_lookback_days = 60
        news_lookback_hours = None
        news_start = _fmt(trade - timedelta(days=21))
        news_end = _fmt(trade)
        global_news_lookback_days = 14
        global_news_limit = min(limit, 50)
        fundamentals_freq = "quarterly"
    elif horizon == "position":
        stock_end = _fmt(trade)
        stock_start = _fmt(trade - timedelta(days=365))
        use_intraday = False
        av_intraday_interval = "60min"
        price_vendor_interval = "daily_weekly_mix"
        indicator_interval = "daily"
        indicator_lookback_days = 180
        yfinance_indicator_lookback_days = 120
        news_lookback_hours = None
        news_start = _fmt(trade - timedelta(days=90))
        news_end = _fmt(trade)
        global_news_lookback_days = 30
        global_news_limit = min(limit, 60)
        fundamentals_freq = "quarterly"
    else:  # long_term
        stock_end = _fmt(trade)
        stock_start = _fmt(trade - timedelta(days=365 * 5))
        use_intraday = False
        av_intraday_interval = "daily"
        price_vendor_interval = "weekly_monthly_bias"
        indicator_interval = "daily"
        indicator_lookback_days = 365
        yfinance_indicator_lookback_days = 252
        news_lookback_hours = None
        news_start = _fmt(trade - timedelta(days=365))
        news_end = _fmt(trade)
        global_news_lookback_days = 90
        global_news_limit = min(limit, 80)
        fundamentals_freq = "annual"

    if news_mode == "daterange":
        df = cfg.get("news_date_from")
        dt_to = cfg.get("news_date_to")
        if isinstance(df, str) and df.strip():
            news_start = df.strip()[:10]
        if isinstance(dt_to, str) and dt_to.strip():
            news_end = dt_to.strip()[:10]

    return DataWindows(
        stock_start=stock_start,
        stock_end=stock_end,
        use_intraday=use_intraday,
        av_intraday_interval=av_intraday_interval,
        price_vendor_interval=price_vendor_interval,
        indicator_interval=indicator_interval,
        indicator_lookback_days=indicator_lookback_days,
        yfinance_indicator_lookback_days=yfinance_indicator_lookback_days,
        news_start=news_start,
        news_end=news_end,
        news_limit=limit,
        news_lookback_hours=news_lookback_hours,
        fundamentals_freq=fundamentals_freq,
        global_news_lookback_days=global_news_lookback_days,
        global_news_limit=global_news_limit,
    )


def resolve_effective_stock_window(
    trade_date: str | None,
    llm_start: str,
    llm_end: str,
) -> tuple[str, str]:
    """Zwraca (start,end) OHLCV: domyślnie wg horyzontu joba; gdy ``enforce_data_windows``=False — z LLM."""
    cfg = get_config()
    if not cfg.get("enforce_data_windows", True):
        return llm_start, llm_end
    td = (trade_date or str(cfg.get("_job_trade_date") or "") or llm_end or llm_start)[:10]
    if not td:
        td = datetime.utcnow().strftime("%Y-%m-%d")
    w = resolve_data_windows(td)
    return w.stock_start, w.stock_end


def build_data_description_prefix(
    *,
    tool_name: str,
    symbol: str,
    trade_date: str,
    extra_lines: list[str] | None = None,
) -> str:
    w = resolve_data_windows(trade_date)
    cfg = get_config()
    lines = [
        f"[Kontekst danych dla agenta — narzędzie: {tool_name}]",
        f"Instrument (ticker): {symbol.upper()}",
        f"Data referencyjna analizy (trade_date): {trade_date}",
        f"Horyzont inwestycyjny: {cfg.get('investment_horizon', 'swing_medium')}",
        f"Okno OHLCV: {w.stock_start} … {w.stock_end} (etykieta profilu: {w.price_vendor_interval})",
        f"Interwał wskaźników (Alpha Vantage): {w.indicator_interval}; lookback (dni): {w.indicator_lookback_days}",
        f"News: zakres {w.news_start} … {w.news_end}, limit artykułów: {w.news_limit}",
    ]
    if extra_lines:
        lines.extend(extra_lines)
    return "\n".join(lines) + "\n---\n"


def tool_config_snapshot() -> dict[str, Any]:
    """Do osadzenia w JSON meta dla UI."""
    cfg = get_config()
    td = str(cfg.get("_job_trade_date") or "")[:10] or None
    if not td:
        return {"investment_horizon": cfg.get("investment_horizon")}
    w = resolve_data_windows(td)
    return {
        "investment_horizon": cfg.get("investment_horizon"),
        "research_depth": cfg.get("research_depth"),
        "stock_window": {"start": w.stock_start, "end": w.stock_end},
        "indicator_policy": {
            "interval": w.indicator_interval,
            "lookback_days": w.indicator_lookback_days,
            "yf_lookback_days": w.yfinance_indicator_lookback_days,
        },
        "news_policy": {
            "start": w.news_start,
            "end": w.news_end,
            "limit": w.news_limit,
            "mode": cfg.get("news_query_mode"),
        },
    }
