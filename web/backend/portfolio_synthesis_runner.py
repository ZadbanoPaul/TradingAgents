"""Job „synteza portfela LLM”: agregacja zakończonych analiz + jeden wywołanie modelu „deep”."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from tradingagents.graph.signal_processing import SignalProcessor
from tradingagents.llm_clients import create_llm_client
from tradingagents.llm_clients.openai_capabilities import openai_model_supports_reasoning_effort
from web.backend.models import AnalysisJob, User
from web.backend.services.historical_insights import build_portfolio_draft

log = logging.getLogger(__name__)

_REPORT_KEYS_ORDER = [
    "orchestrator_report",
    "market_report",
    "sentiment_report",
    "news_report",
    "news_web_report",
    "fundamentals_report",
    "accounting_quality_report",
    "valuation_report",
    "sector_report",
    "catalyst_report",
    "data_quality_report",
    "scoring_report",
    "investment_plan",
    "trader_investment_plan",
    "final_trade_decision",
]


def _kwargs_for_model(config: dict[str, Any], model_name: str) -> dict[str, Any]:
    """Jak w TradingAgentsGraph: reasoning_effort tylko dla OpenAI + modeli z whitelisty."""
    kw: dict[str, Any] = {}
    if str(config.get("llm_provider", "")).lower() != "openai":
        return kw
    eff = config.get("openai_reasoning_effort")
    if eff and openai_model_supports_reasoning_effort(str(model_name)):
        kw["reasoning_effort"] = eff
    return kw


def _truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[: n - 20] + "\n…[ucięto]…"


def _extract_job_text_blob(data: dict[str, Any], per_job_cap: int) -> str:
    parts: list[str] = []
    for key in _REPORT_KEYS_ORDER:
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(f"### {key}\n{_truncate(val, per_job_cap)}")
    return "\n\n".join(parts) if parts else "(brak tekstowych sekcji raportu w result_json)"


def run_portfolio_synthesis_job(
    db: Session,
    job: AnalysisJob,
    user: User,
    cfg: dict[str, Any],
    base: dict[str, Any],
    push_progress: Callable[..., None],
) -> None:
    """
    Ustawia job.status / result_json / final_signal / error_message.
    Wywoływane z job_runner po zainicjowaniu events i progress.
    """
    ids_raw = cfg.get("source_job_ids") or []
    try:
        source_job_ids = [int(x) for x in ids_raw]
    except (TypeError, ValueError) as e:
        raise ValueError("source_job_ids musi być listą liczb całkowitych") from e

    notional = float(cfg.get("notional_usd", 0))
    num_pos = int(cfg.get("num_positions", 8))
    minute = bool(cfg.get("include_minute_last_day", False))
    max_ctx = int(cfg.get("max_context_chars", 90_000))
    max_ctx = max(5_000, min(max_ctx, 200_000))

    lang = str(cfg.get("report_language") or "en").lower()
    out_lang = "Polish" if lang == "pl" else "English"

    push_progress(
        "Synteza portfela — przygotowanie",
        [
            f"Joby źródłowe: {source_job_ids}",
            f"Kapitał: {notional:,.0f} USD, pozycje: {num_pos}, 1m: {minute}",
            f"Budżet kontekstu znaków: {max_ctx}",
        ],
        step_no=1,
        agent_label="Portfolio synthesis",
    )

    draft = build_portfolio_draft(
        db,
        user.id,
        source_job_ids,
        notional,
        num_pos,
        minute,
    )
    pick_ids = [int(r["job_id"]) for r in draft.get("lines") or []]
    if not pick_ids:
        raise ValueError("Szkic portfela nie zwrócił żadnych pozycji")

    n = max(1, len(pick_ids))
    per_job = max(2_000, max_ctx // n)

    blocks: list[str] = []
    for jid in pick_ids:
        row = db.get(AnalysisJob, jid)
        if not row or row.user_id != user.id or row.status != "completed":
            continue
        ticker = str(row.ticker).upper()
        blob = ""
        if row.result_json:
            try:
                data = json.loads(row.result_json)
                if isinstance(data, dict):
                    blob = _extract_job_text_blob(data, per_job)
            except json.JSONDecodeError:
                blob = "(niepoprawny JSON wyniku joba)"
        blocks.append(f"## {ticker} (job {jid}, data {row.trade_date}, sygnał: {row.final_signal})\n{blob}")

    research_pack = "\n\n".join(blocks)
    research_pack = _truncate(research_pack, max_ctx)

    md_table = str(draft.get("markdown_table") or "")
    minute_json = json.dumps(draft.get("minute_snapshot") or {}, ensure_ascii=False)

    system_pl = (
        "Jesteś starszym analitykiem portfelowym (buy-side). "
        "Na podstawie DOŁĄCZONYCH fragmentów raportów z jobów oraz szkicu wag rule-based "
        "przygotuj spójną syntezę alokacji dla jednego konta. "
        "Nie wymyślaj faktów spoza materiału; jeśli czegoś brakuje, napisz wprost. "
        "Uwzględnij koncentrację ryzyka, sektorowość (jeśli widać z tickerów), płynność, horyzont. "
        "Zakończ krótką sekcją „zastrzeżenia / nie jest poradą inwestycyjną”."
    )
    system_en = (
        "You are a senior portfolio analyst (buy-side). "
        "Using ONLY the attached excerpts from per-ticker analysis jobs and the rule-based weight draft, "
        "produce a coherent portfolio synthesis for a single account. "
        "Do not invent facts; state gaps explicitly. "
        "Address concentration, sector hints from tickers if any, liquidity, horizon. "
        "End with a short “disclaimers / not investment advice” section."
    )
    system = system_pl if lang == "pl" else system_en

    if lang == "pl":
        tail = (
            "---\n"
            "Zwróć: (1) streszczenie wykonawcze, (2) tabela wag (ticker, %, uzasadnienie), "
            "(3) kluczowe ryzyka i mitygacje, (4) lista monitorowania na 2–4 tygodnie."
        )
    else:
        tail = (
            "---\n"
            "Deliver: (1) Executive summary, (2) proposed weights table (ticker, %, rationale), "
            "(3) key risks and mitigations, (4) monitoring checklist for the next 2–4 weeks."
        )
    user_body = (
        f"Output language: {out_lang}.\n\n"
        f"## Rule-based draft (weights from job signals)\n{md_table}\n\n"
        f"## Minute snapshot (optional)\n{minute_json}\n\n"
        f"## Research excerpts per position\n{research_pack}\n\n"
        f"{tail}"
    )

    provider = str(base.get("llm_provider") or "openai")
    deep_model = str(base.get("deep_think_llm") or "gpt-4o")
    quick_model = str(base.get("quick_think_llm") or "gpt-4o-mini")

    deep_client = create_llm_client(
        provider=provider,
        model=deep_model,
        base_url=base.get("backend_url"),
        **_kwargs_for_model(base, deep_model),
    )
    quick_client = create_llm_client(
        provider=provider,
        model=quick_model,
        base_url=base.get("backend_url"),
        **_kwargs_for_model(base, quick_model),
    )
    deep_llm = deep_client.get_llm()
    quick_llm = quick_client.get_llm()

    push_progress(
        "Synteza portfela — LLM",
        [
            f"Wywołanie modelu: `{deep_model}` ({provider})",
            f"Ekstrakcja sygnału: `{quick_model}`",
        ],
        step_no=2,
        agent_label="Portfolio synthesis",
    )

    messages = [
        ("system", system),
        ("human", user_body),
    ]
    resp = deep_llm.invoke(messages)
    text = getattr(resp, "content", None) or str(resp)
    text = str(text).strip()
    if not text:
        raise RuntimeError("Pusty wynik LLM")

    sig = SignalProcessor(quick_thinking_llm=quick_llm).process_signal(text[:12_000])

    meta = {
        "source_job_ids": source_job_ids,
        "portfolio_pick_job_ids": pick_ids,
        "notional_usd": notional,
        "num_positions": num_pos,
        "include_minute_last_day": minute,
        "rule_based_markdown_table": md_table,
    }
    job.result_json = json.dumps(
        {
            "portfolio_synthesis_report": text,
            "portfolio_synthesis_meta": meta,
        },
        ensure_ascii=False,
    )
    job.final_signal = str(sig).strip() if sig else None
    job.status = "completed"
    job.error_message = None

    push_progress(
        "Synteza portfela — zakończono",
        [
            f"Zapisano raport ({len(text)} znaków).",
            f"Wyciągnięty sygnał (heurystyka z treści): `{job.final_signal}`",
        ],
        step_no=3,
        agent_label="Portfolio synthesis",
    )
    log.info("job %s portfolio_synthesis done, signal=%s", job.id, job.final_signal)
