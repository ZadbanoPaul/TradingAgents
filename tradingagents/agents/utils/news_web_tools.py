"""Narzędzie „News Web Agent” — aktualne nagłówki z RSS wyszukiwania Google News."""

from __future__ import annotations

import json
from typing import Annotated

from langchain_core.tools import tool

from tradingagents.agents.utils.tool_json_formatter import tool_response_to_json
from tradingagents.analysis_horizon import resolve_data_windows
from tradingagents.dataflows.google_news_rss import fetch_google_news_rss
from tradingagents.runtime_context import get_job_context


@tool
def search_web_ticker_news(
    query: Annotated[str, "Zapytanie po angielsku, np. AAPL stock earnings OR ticker company name"],
    max_results: Annotated[int, "Maksymalna liczba nagłówków (domyślnie z profilu zadania)"] = 20,
) -> str:
    """
    Wyszukuje najnowsze publicznie dostępne nagłówki wiadomości (RSS Google News) dla podanego zapytania.
    Nie zastępuje źródeł płatnych (Alpha Vantage / yfinance) — uzupełnia obraz o świeże tytuły z sieci.
    """
    ctx = get_job_context()
    td = str(ctx.get("trade_date") or "")[:10]
    w = resolve_data_windows(td) if td else None
    lim = int(max_results) if max_results else 20
    if w:
        lim = max(3, min(lim, int(w.news_limit)))
    articles = fetch_google_news_rss(query, limit=lim)
    payload = {
        "version": 1,
        "tool": "search_web_ticker_news",
        "meta": {"query": query, "source": "google_news_rss"},
        "timeseries": [],
        "kv": [],
        "articles": articles,
        "notes": "Nagłówki z kanału RSS Google News; treść artykułu może być skrócona — zweryfikuj kluczowe fakty.",
    }
    return tool_response_to_json(
        "search_web_ticker_news",
        json.dumps(payload, ensure_ascii=False),
        instrument=str(ctx.get("ticker") or ""),
        trade_date=td or None,
        extra_description_lines=[f"Zapytanie RSS: {query[:200]}"],
    )
