"""Katalog funkcji Alpha Vantage używanych / planowanych w TradingAgents — częstotliwość nominalna i TTL cache."""

from __future__ import annotations

# function_name -> { label, nominal_refresh, ttl_seconds }
# nominal_refresh: opis dla UI (Alpha Vantage ma różne opóźnienia publikacji — traktuj jako orientacyjne).
AV_SERIES: list[dict[str, str | int]] = [
    {"function": "TIME_SERIES_INTRADAY", "label": "Intraday OHLCV", "nominal_refresh": "1 min – opóźnienie real-time / near-time", "ttl_seconds": 300},
    {"function": "TIME_SERIES_DAILY_ADJUSTED", "label": "Dzienne OHLCV (adjusted)", "nominal_refresh": "1× dziennie po zamknięciu sesji US", "ttl_seconds": 86400},
    {"function": "TIME_SERIES_WEEKLY_ADJUSTED", "label": "Tygodniowe OHLCV", "nominal_refresh": "1× tygodniowo", "ttl_seconds": 86400 * 7},
    {"function": "TIME_SERIES_MONTHLY_ADJUSTED", "label": "Miesięczne OHLCV", "nominal_refresh": "1× miesięcznie", "ttl_seconds": 86400 * 30},
    {"function": "RSI", "label": "RSI", "nominal_refresh": "zależny od serii cenowej (dzień/intraday)", "ttl_seconds": 3600},
    {"function": "MACD", "label": "MACD", "nominal_refresh": "jak RSI", "ttl_seconds": 3600},
    {"function": "MFI", "label": "MFI", "nominal_refresh": "jak RSI", "ttl_seconds": 3600},
    {"function": "SMA", "label": "SMA", "nominal_refresh": "jak RSI", "ttl_seconds": 3600},
    {"function": "EMA", "label": "EMA", "nominal_refresh": "jak RSI", "ttl_seconds": 3600},
    {"function": "BBANDS", "label": "Bollinger Bands", "nominal_refresh": "jak RSI", "ttl_seconds": 3600},
    {"function": "ATR", "label": "ATR", "nominal_refresh": "jak RSI", "ttl_seconds": 3600},
    {"function": "OVERVIEW", "label": "Fundamenty — profil spółki", "nominal_refresh": "1× dziennie (overview)", "ttl_seconds": 86400},
    {"function": "BALANCE_SHEET", "label": "Bilans", "nominal_refresh": "kwartalnie / po raporcie", "ttl_seconds": 86400},
    {"function": "INCOME_STATEMENT", "label": "Rachunek zysków i strat", "nominal_refresh": "kwartalnie / po raporcie", "ttl_seconds": 86400},
    {"function": "CASH_FLOW", "label": "Przepływy gotówkowe", "nominal_refresh": "kwartalnie / po raporcie", "ttl_seconds": 86400},
    {"function": "NEWS_SENTIMENT", "label": "News + sentyment", "nominal_refresh": "intraday / rolling", "ttl_seconds": 900},
    {"function": "INSIDER_TRANSACTIONS", "label": "Transakcje insiderów", "nominal_refresh": "rzadziej (SEC / opóźnienie)", "ttl_seconds": 86400},
]


def list_av_series() -> list[dict[str, str | int]]:
    return list(AV_SERIES)


def ttl_for_function(function_name: str) -> int:
    for row in AV_SERIES:
        if row["function"] == function_name:
            return int(row["ttl_seconds"])
    return 3600
