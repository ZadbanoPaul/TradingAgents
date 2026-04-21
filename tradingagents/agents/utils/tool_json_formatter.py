"""Normalizacja wyjść narzędzi get_* do jednego schematu JSON (wykresy + tabele w UI)."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any, Dict, List, Optional

from tradingagents.analysis_horizon import build_data_description_prefix, tool_config_snapshot
from tradingagents.agents.utils.tool_json_financial import (
    parse_alpha_news_json,
    parse_alpha_overview_json,
    parse_alpha_statement_json,
    parse_financial_wide_csv,
)
from tradingagents.runtime_context import get_job_context

SCHEMA_VERSION = 1


def _safe_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def _enrich_payload(
    obj: Dict[str, Any],
    *,
    tool_name: str,
    instrument: str | None,
    trade_date: str | None,
    extra_description_lines: list[str] | None = None,
) -> Dict[str, Any]:
    if instrument and trade_date:
        obj["data_description"] = build_data_description_prefix(
            tool_name=tool_name,
            symbol=instrument,
            trade_date=trade_date,
            extra_lines=extra_description_lines,
        )
        meta = obj.setdefault("meta", {})
        if isinstance(meta, dict):
            meta.setdefault("analysis", tool_config_snapshot())
    return obj


def _parse_stock_csv_block(raw: str) -> Optional[Dict[str, Any]]:
    """Parsuje blok CSV z get_stock_data (yfinance / nagłówki #)."""
    lines = raw.splitlines()
    body: List[str] = []
    meta: Dict[str, str] = {}
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#"):
            m = re.match(r"#\s*Stock data for\s+(\S+)\s+from\s+(\S+)\s+to\s+(\S+)", s, re.I)
            if m:
                meta["symbol"] = m.group(1)
                meta["start_date"] = m.group(2)
                meta["end_date"] = m.group(3)
            continue
        body.append(ln)
    if len(body) < 2:
        return None
    try:
        reader = csv.DictReader(io.StringIO("\n".join(body)))
        rows: List[Dict[str, Any]] = []
        for row in reader:
            out: Dict[str, Any] = {}
            for k, v in row.items():
                raw_key = (k or "").strip()
                if raw_key == "" or raw_key.lower() in ("date", "datetime", "datetime_utc", "datetime"):
                    out["date"] = (v or "").strip()
                    continue
                key = raw_key.replace(" ", "_")
                try:
                    if v is None or str(v).strip() == "" or str(v).lower() == "nan":
                        out[key] = None
                    else:
                        out[key] = float(str(v).replace(",", ""))
                except ValueError:
                    out[key] = v
            if out.get("date"):
                rows.append(out)
        if not rows:
            return None
        return {
            "version": SCHEMA_VERSION,
            "tool": "get_stock_data",
            "meta": meta,
            "timeseries": rows,
            "kv": [],
            "articles": [],
            "notes": "OHLCV z narzędzia; kolumny numeryczne dostępne do wykresów.",
        }
    except Exception:
        return None


def _parse_indicator_block(raw: str) -> Optional[Dict[str, Any]]:
    """Parsuje wyjście get_indicators (linie YYYY-MM-DD: wartość)."""
    lines = raw.splitlines()
    ts: List[Dict[str, Any]] = []
    indicator = "value"
    mhead = re.search(r"^##\s+(\S+)\s+values", raw, re.M)
    if mhead:
        indicator = mhead.group(1)
    pat = re.compile(r"^(\d{4}-\d{2}-\d{2})\s*:\s*(.+)$")
    for ln in lines:
        m = pat.match(ln.strip())
        if not m:
            continue
        d, rest = m.group(1), m.group(2).strip()
        if rest.startswith("N/A"):
            continue
        try:
            val = float(rest.replace(",", ""))
        except ValueError:
            continue
        ts.append({"date": d, "value": val})
    if len(ts) < 2:
        return None
    ts.sort(key=lambda r: r["date"])
    return {
        "version": SCHEMA_VERSION,
        "tool": "get_indicators",
        "meta": {"indicator": indicator},
        "timeseries": ts,
        "kv": [],
        "articles": [],
        "notes": f"Szereg czasowy wskaźnika `{indicator}`.",
    }


def _parse_kv_report(raw: str, tool: str) -> Optional[Dict[str, Any]]:
    """Parsuje raport typu 'Etykieta: wartość' (fundamenty, cashflow itd.)."""
    kv: List[Dict[str, Any]] = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if ":" not in ln:
            continue
        k, v = ln.split(":", 1)
        k, v = k.strip(), v.strip()
        if not k:
            continue
        entry: Dict[str, Any] = {"label": k, "raw": v}
        try:
            entry["value"] = float(v.replace(",", "").replace("%", ""))
        except ValueError:
            entry["value"] = None
        kv.append(entry)
    if len(kv) < 3:
        return None
    return {
        "version": SCHEMA_VERSION,
        "tool": tool,
        "meta": {},
        "timeseries": [],
        "kv": kv,
        "articles": [],
        "notes": "Metryki tekstowe / liczbowe; pole `value` tylko gdy udało się sparsować liczbę.",
    }


def _parse_news_markdown(raw: str, tool: str) -> Dict[str, Any]:
    """Wyciąga artykuły z formatu ### Tytuł (source: …)."""
    articles: List[Dict[str, str]] = []
    blocks = re.split(r"\n###\s+", raw)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        first = block.split("\n", 1)[0]
        m = re.match(r"^(.+?)\s*\(source:\s*([^)]+)\)\s*$", first)
        title = first if not m else m.group(1).strip()
        publisher = "" if not m else m.group(2).strip()
        if not title or title.startswith("##"):
            continue
        rest = block.split("\n", 1)[1] if "\n" in block else ""
        link = ""
        for ln in rest.splitlines():
            if ln.lower().startswith("link:"):
                link = ln.split(":", 1)[1].strip()
                break
        summary = "\n".join(
            ln for ln in rest.splitlines() if not ln.lower().startswith("link:")
        ).strip()
        articles.append(
            {"title": title, "publisher": publisher, "summary": summary[:4000], "link": link}
        )
    return {
        "version": SCHEMA_VERSION,
        "tool": tool,
        "meta": {},
        "timeseries": [],
        "kv": [],
        "articles": articles,
        "notes": "Lista artykułów; brak szeregu liczbowego — możliwa oś czasu po tytule.",
    }


def _try_load_existing_json(raw: str) -> Optional[Dict[str, Any]]:
    s = raw.strip()
    if not s.startswith("{"):
        return None
    try:
        obj = json.loads(s)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    if obj.get("version") == SCHEMA_VERSION and "tool" in obj:
        return obj
    if "timeseries" in obj or "kv" in obj or "articles" in obj:
        obj.setdefault("version", SCHEMA_VERSION)
        return obj
    return None


def tool_response_to_json(
    tool_name: str,
    raw: str,
    *,
    instrument: str | None = None,
    trade_date: str | None = None,
    extra_description_lines: list[str] | None = None,
) -> str:
    """Zwraca **jedną** linię JSON (string) dla LangChain / LLM."""
    if raw is None:
        raw = ""
    ctx = get_job_context()
    if not trade_date:
        trade_date = str(ctx.get("trade_date") or "")[:10] or None
    if not instrument:
        instrument = str(ctx.get("ticker") or "") or None

    def _out(obj: Dict[str, Any]) -> str:
        return _safe_json(
            _enrich_payload(
                obj,
                tool_name=tool_name,
                instrument=instrument,
                trade_date=trade_date,
                extra_description_lines=extra_description_lines,
            )
        )

    existing = _try_load_existing_json(raw)
    if existing is not None:
        return _out(existing)

    if tool_name == "get_stock_data":
        parsed = _parse_stock_csv_block(raw)
        if parsed is not None:
            return _out(parsed)

    if tool_name == "get_indicators":
        parsed = _parse_indicator_block(raw)
        if parsed is not None:
            return _out(parsed)

    if tool_name == "get_fundamentals":
        parsed = parse_alpha_overview_json(raw, tool_name)
        if parsed is not None:
            return _out(parsed)
        parsed = _parse_kv_report(raw, tool_name)
        if parsed is not None:
            return _out(parsed)

    if tool_name in ("get_balance_sheet", "get_cashflow", "get_income_statement"):
        parsed = parse_alpha_statement_json(raw, tool_name)
        if parsed is not None:
            return _out(parsed)
        parsed = parse_financial_wide_csv(raw, tool_name)
        if parsed is not None:
            return _out(parsed)
        parsed = _parse_kv_report(raw, tool_name)
        if parsed is not None:
            return _out(parsed)

    if tool_name in ("get_news", "get_global_news"):
        parsed = parse_alpha_news_json(raw, tool_name)
        if parsed is not None:
            return _out(parsed)
        return _out(_parse_news_markdown(raw, tool_name))

    if tool_name == "search_web_ticker_news":
        parsed = _try_load_existing_json(raw)
        if parsed:
            return _out(parsed)
        return _out(
            {
                "version": SCHEMA_VERSION,
                "tool": tool_name,
                "meta": {},
                "timeseries": [],
                "kv": [],
                "articles": [],
                "notes": raw[:12000],
            }
        )

    if tool_name == "get_insider_transactions":
        parsed = _parse_kv_report(raw, tool_name)
        if parsed is not None:
            return _out(parsed)
        return _out(
            {
                "version": SCHEMA_VERSION,
                "tool": tool_name,
                "meta": {},
                "timeseries": [],
                "kv": [],
                "articles": [],
                "notes": raw[:12000],
            }
        )

    return _out(
        {
            "version": SCHEMA_VERSION,
            "tool": tool_name,
            "meta": {},
            "timeseries": [],
            "kv": [],
            "articles": [],
            "notes": raw[:12000],
        }
    )
