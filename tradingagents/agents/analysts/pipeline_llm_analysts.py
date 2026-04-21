"""Analitycy tylko-LLM wykorzystujący złożone raporty ze stanu (data quality, scoring)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from tradingagents.prompts import resolve_prompt
from tradingagents.prompts.defaults import DEFAULT_PROMPTS
from tradingagents.prompts.institutional_compose import institutional_system_prefix
from tradingagents.agents.utils.institutional_context import build_extended_instrument_block


def _reports_digest(state: dict) -> str:
    chunks = []
    pairs = [
        ("Orchestrator", "orchestrator_report"),
        ("Market", "market_report"),
        ("Sentiment / company news", "sentiment_report"),
        ("Macro / news", "news_report"),
        ("News Web", "news_web_report"),
        ("Fundamentals", "fundamentals_report"),
        ("Accounting quality", "accounting_quality_report"),
        ("Valuation", "valuation_report"),
        ("Sector", "sector_report"),
        ("Catalysts", "catalyst_report"),
    ]
    for title, key in pairs:
        v = (state.get(key) or "").strip()
        if v:
            chunks.append(f"### {title}\n{v[:12000]}")
    return "\n\n".join(chunks) if chunks else "(Brak jeszcze raportów upstream — oceń ryzyko danych i kolejne kroki.)"


def create_data_quality_analyst(llm, body_key: str):
    def node(state):
        ext = build_extended_instrument_block(state, tool_names="(retrospekcja raportów)")
        prefix = institutional_system_prefix(
            current_date=state["trade_date"],
            instrument_extended=ext,
        )
        body = resolve_prompt(body_key, DEFAULT_PROMPTS[body_key])
        sys = prefix + body
        human = _reports_digest(state)
        r = llm.invoke([SystemMessage(content=sys), HumanMessage(content=human)])
        return {"data_quality_report": r.content or "", "messages": [r]}

    return node


def create_scoring_analyst(llm, body_key: str):
    def node(state):
        ext = build_extended_instrument_block(state, tool_names="(agregacja scoringu)")
        prefix = institutional_system_prefix(
            current_date=state["trade_date"],
            instrument_extended=ext,
        )
        body = resolve_prompt(body_key, DEFAULT_PROMPTS[body_key])
        sys = prefix + body
        human = _reports_digest(state) + "\n\n### Data quality\n" + (state.get("data_quality_report") or "")
        r = llm.invoke([SystemMessage(content=sys), HumanMessage(content=human)])
        return {"scoring_report": r.content or "", "messages": [r]}

    return node
