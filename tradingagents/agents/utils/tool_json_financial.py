"""Parsowanie wyciągów finansowych (wide CSV / JSON Alpha Vantage) do ujednoliconego schematu UI."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = 1


def parse_financial_wide_csv(raw: str, tool: str) -> Optional[Dict[str, Any]]:
    """yfinance: indeks (daty) w pierwszej kolumnie, metryki w kolejnych kolumnach okresów."""
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("#") and ln.strip()]
    if len(lines) < 2:
        return None
    reader = csv.reader(io.StringIO("\n".join(lines)))
    rows_list = list(reader)
    if len(rows_list) < 2:
        return None
    header = [h.strip() for h in rows_list[0]]
    if len(header) < 2:
        return None
    if header[0] == "":
        header[0] = "metric"
    period_cols = header[1:]
    metric_rows: list[dict[str, Any]] = []
    for row in rows_list[1:]:
        if not row or not str(row[0]).strip():
            continue
        metric = str(row[0]).strip()
        vals = row[1 : len(period_cols) + 1]
        while len(vals) < len(period_cols):
            vals.append("")
        metric_rows.append(
            {
                "metric": metric,
                "values": {period_cols[i]: vals[i] for i in range(len(period_cols))},
            }
        )
    if len(metric_rows) < 2:
        return None
    return {
        "version": SCHEMA_VERSION,
        "tool": tool,
        "presentation": "financial_period_columns",
        "meta": {"period_columns": period_cols, "row_count": len(metric_rows)},
        "period_columns": period_cols,
        "metric_rows": metric_rows[:400],
        "timeseries": [],
        "kv": [],
        "articles": [],
        "notes": (
            "Dane sprawozdawcze w układzie „wiersz = pozycja rachunku, kolumny = okresy sprawozdawcze” "
            "(jak w eksporcie pandas CSV). Nie jest to szereg czasowy OHLCV."
        ),
    }


def parse_alpha_statement_json(raw: str, tool: str) -> Optional[Dict[str, Any]]:
    """Alpha Vantage: BALANCE_SHEET / INCOME_STATEMENT / CASH_FLOW jako JSON z listami raportów."""
    s = raw.strip()
    if not s.startswith("{"):
        return None
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if "Error Message" in data:
        return None
    reports = data.get("quarterlyReports") or data.get("annualReports")
    if not isinstance(reports, list) or not reports:
        return None
    # najnowsze pierwsze
    try:
        reports = sorted(
            reports,
            key=lambda r: str(r.get("fiscalDateEnding", "")),
            reverse=True,
        )[:8]
    except Exception:
        reports = reports[:8]
    period_keys = [str(r.get("fiscalDateEnding", "")) for r in reports if r.get("fiscalDateEnding")]
    if len(period_keys) < 1:
        return None
    metric_set: list[str] = []
    seen: set[str] = set()
    for r in reports:
        for k in r.keys():
            if k in ("fiscalDateEnding", "reportedCurrency"):
                continue
            if k not in seen:
                seen.add(k)
                metric_set.append(k)
    metric_rows: list[dict[str, Any]] = []
    for m in metric_set[:300]:
        vals: dict[str, str] = {}
        for r in reports:
            fd = str(r.get("fiscalDateEnding", ""))
            if fd:
                vals[fd] = str(r.get(m, ""))
        metric_rows.append({"metric": m, "values": vals})
    return {
        "version": SCHEMA_VERSION,
        "tool": tool,
        "presentation": "financial_period_columns",
        "meta": {"source": "alpha_vantage_json", "period_columns": period_keys},
        "period_columns": period_keys,
        "metric_rows": metric_rows,
        "timeseries": [],
        "kv": [],
        "articles": [],
        "notes": "Struktura API Alpha Vantage (lista raportów kwartalnych/rocznych) spłaszczona do tabeli okresów.",
    }


def parse_alpha_overview_json(raw: str, tool: str) -> Optional[Dict[str, Any]]:
    s = raw.strip()
    if not s.startswith("{"):
        return None
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not data.get("Symbol"):
        return None
    kv: list[dict[str, Any]] = []
    for k, v in data.items():
        if v is None or v == "":
            continue
        entry: dict[str, Any] = {"label": str(k), "raw": str(v)}
        try:
            entry["value"] = float(str(v).replace(",", ""))
        except ValueError:
            entry["value"] = None
        kv.append(entry)
    if len(kv) < 5:
        return None
    return {
        "version": SCHEMA_VERSION,
        "tool": tool,
        "presentation": "key_value_overview",
        "meta": {"source": "alpha_vantage_overview"},
        "timeseries": [],
        "kv": kv[:200],
        "articles": [],
        "notes": "Pola JSON OVERVIEW Alpha Vantage jako lista etykiet (fundamenty profilu spółki).",
    }


def parse_alpha_news_json(raw: str, tool: str) -> Optional[Dict[str, Any]]:
    s = raw.strip()
    if not s.startswith("{"):
        return None
    try:
        data = json.loads(s)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    feed = data.get("feed")
    if not isinstance(feed, list):
        return None
    articles: list[dict[str, str]] = []
    for it in feed[:120]:
        if not isinstance(it, dict):
            continue
        title = re.sub(r"<[^>]+>", "", str(it.get("title", "")))
        articles.append(
            {
                "title": title[:500],
                "publisher": str(it.get("source", "") or it.get("source_domain", "") or "")[:120],
                "summary": str(it.get("summary", "") or it.get("overall_sentiment_label", ""))[:4000],
                "link": str(it.get("url", ""))[:2000],
            }
        )
    if not articles:
        return None
    return {
        "version": SCHEMA_VERSION,
        "tool": tool,
        "presentation": "news_json",
        "meta": {},
        "timeseries": [],
        "kv": [],
        "articles": articles,
        "notes": "NEWS_SENTIMENT Alpha Vantage (JSON).",
    }
