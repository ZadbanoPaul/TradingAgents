"""Wykonanie pojedynczego zadania analizy (worker lub test)."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.prompts import clear_prompt_overrides, set_prompt_overrides
from tradingagents.runtime_context import bind_job_context, clear_job_context
from web.backend.crypto_store import decrypt_text
from web.backend.models import AnalysisJob, StoredApiKey, User
from web.backend.prompt_versions_service import active_bodies_map
from web.backend.config import get_settings
from web.backend.progress_tracking import (
    describe_state_transition,
    normalize_stream_chunk,
)
from web.backend.transparency_callback import TransparencyCallbackHandler

log = logging.getLogger(__name__)

_MAX_PROGRESS_EVENTS = 1200


def _load_prompt_overrides(db: Session, user_id: int) -> dict[str, str]:
    """Treści promptów: aktywne wersje z ``PromptVersion`` oraz legacy ``PromptOverride``."""
    return active_bodies_map(db, user_id)


def _apply_api_keys_to_environ(db: Session, user_id: int) -> dict[str, str | None]:
    """Zwraca poprzednie wartości env do przywrócenia w ``finally``."""
    prev: dict[str, str | None] = {}
    for provider, env_name in (
        ("openai", "OPENAI_API_KEY"),
        ("alpha_vantage", "ALPHA_VANTAGE_API_KEY"),
    ):
        row = (
            db.query(StoredApiKey)
            .filter(
                StoredApiKey.user_id == user_id,
                StoredApiKey.provider == provider,
            )
            .one_or_none()
        )
        prev[env_name] = os.environ.get(env_name)
        if row and row.ciphertext:
            try:
                os.environ[env_name] = decrypt_text(row.ciphertext)
            except Exception:
                os.environ.pop(env_name, None)
        else:
            os.environ.pop(env_name, None)
    return prev


def _restore_environ(prev: dict[str, str | None]) -> None:
    for k, v in prev.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _serialize_final_state(final_state: dict[str, Any]) -> dict[str, Any]:
    def _short(s: str, n: int = 120_000) -> str:
        if not isinstance(s, str):
            return ""
        return s if len(s) <= n else s[:n] + "\n\n…(obcięte)"

    ids = final_state.get("investment_debate_state") or {}
    rds = final_state.get("risk_debate_state") or {}
    if not isinstance(ids, dict):
        ids = {}
    if not isinstance(rds, dict):
        rds = {}
    return {
        "company_of_interest": final_state.get("company_of_interest"),
        "trade_date": final_state.get("trade_date"),
        "market_report": _short(final_state.get("market_report") or ""),
        "sentiment_report": _short(final_state.get("sentiment_report") or ""),
        "news_report": _short(final_state.get("news_report") or ""),
        "news_web_report": _short(final_state.get("news_web_report") or ""),
        "fundamentals_report": _short(final_state.get("fundamentals_report") or ""),
        "orchestrator_report": _short(final_state.get("orchestrator_report") or ""),
        "accounting_quality_report": _short(final_state.get("accounting_quality_report") or ""),
        "valuation_report": _short(final_state.get("valuation_report") or ""),
        "sector_report": _short(final_state.get("sector_report") or ""),
        "catalyst_report": _short(final_state.get("catalyst_report") or ""),
        "data_quality_report": _short(final_state.get("data_quality_report") or ""),
        "scoring_report": _short(final_state.get("scoring_report") or ""),
        "investment_plan": _short(final_state.get("investment_plan") or ""),
        "trader_investment_plan": _short(final_state.get("trader_investment_plan") or ""),
        "final_trade_decision": _short(final_state.get("final_trade_decision") or ""),
        "investment_debate_state": (
            {k: _short(str(v), 50_000) for k, v in dict(ids).items()} if ids else {}
        ),
        "risk_debate_state": (
            {k: _short(str(v), 50_000) for k, v in dict(rds).items()} if rds else {}
        ),
    }


def _push_item(db: Session, job: AnalysisJob, events: list[dict[str, Any]], item: dict[str, Any]) -> None:
    if "ts" not in item:
        item = {**item, "ts": datetime.now(timezone.utc).isoformat()}
    events.append(item)
    while len(events) > _MAX_PROGRESS_EVENTS:
        events.pop(0)
    job.progress_json = json.dumps(events, ensure_ascii=False)
    db.add(job)
    db.commit()
    if item.get("type") == "graph":
        for ln in (item.get("lines") or [])[:4]:
            log.info("job %s | %s", job.id, str(ln)[:240])


def _push_progress(
    db: Session,
    job: AnalysisJob,
    events: list[dict[str, Any]],
    title: str,
    lines: list[str],
) -> None:
    _push_item(
        db,
        job,
        events,
        {"type": "graph", "title": title, "lines": lines},
    )


def run_job(db: Session, job_id: int) -> None:
    job = db.get(AnalysisJob, job_id)
    if not job or job.status != "pending":
        return

    user = db.get(User, job.user_id)
    if not user:
        job.status = "failed"
        job.error_message = "Brak użytkownika dla zadania."
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        return

    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    job.progress_json = json.dumps([], ensure_ascii=False)
    db.commit()

    t0 = datetime.now(timezone.utc)
    prev_env = _apply_api_keys_to_environ(db, user.id)
    overrides = _load_prompt_overrides(db, user.id)
    set_prompt_overrides(overrides)

    events: list[dict[str, Any]] = []

    try:
        cfg = json.loads(job.config_json)
        base = DEFAULT_CONFIG.copy()
        base.update(
            {
                "llm_provider": cfg.get("llm_provider", base["llm_provider"]),
                "deep_think_llm": cfg.get("deep_think_llm", base["deep_think_llm"]),
                "quick_think_llm": cfg.get("quick_think_llm", base["quick_think_llm"]),
                "max_debate_rounds": int(cfg.get("max_debate_rounds", 1)),
                "max_risk_discuss_rounds": int(cfg.get("max_risk_discuss_rounds", 1)),
                "output_language": cfg.get("output_language", base["output_language"]),
            }
        )
        re_eff = cfg.get("openai_reasoning_effort")
        if re_eff is not None and str(re_eff).strip() != "":
            base["openai_reasoning_effort"] = str(re_eff).strip()
        else:
            base["openai_reasoning_effort"] = None

        for k in (
            "enforce_data_windows",
            "investment_horizon",
            "research_depth",
            "indicators_select_all",
            "selected_indicators",
            "news_query_mode",
            "news_article_limit",
            "news_date_from",
            "news_date_to",
            "news_recent_hours",
            "enable_news_web_agent",
            "full_institutional_pipeline",
        ):
            if k in cfg:
                base[k] = cfg[k]
        im = cfg.get("instrument_meta")
        if isinstance(im, dict) and im:
            merged = dict(base.get("instrument_meta") or {})
            merged.update({str(a).strip(): b for a, b in im.items() if str(a).strip()})
            base["instrument_meta"] = merged
        base["_job_trade_date"] = str(job.trade_date).strip()[:10]

        analysts = cfg.get("analysts") or ["market", "social", "news", "fundamentals"]

        def _emit_transparency(ev: dict[str, Any]) -> None:
            _push_item(db, job, events, ev)

        tb = TransparencyCallbackHandler(
            job_id=job.id,
            data_dir=get_settings()["data_dir"],
            quick_model=str(base["quick_think_llm"]),
            deep_model=str(base["deep_think_llm"]),
            reasoning_effort=base.get("openai_reasoning_effort"),
            emit=_emit_transparency,
        )

        ta = TradingAgentsGraph(analysts, debug=False, config=base, callbacks=[tb])
        ticker_u = job.ticker.upper()
        ta.ticker = ticker_u

        bind_job_context(trade_date=str(job.trade_date).strip()[:10], ticker=ticker_u, extra={"job_id": job.id})

        init_agent_state = ta.propagator.create_initial_state(ticker_u, job.trade_date)
        args = ta.propagator.get_graph_args(callbacks=[tb])

        _push_progress(
            db,
            job,
            events,
            "Start analizy",
            [
                f"Ticker: {ticker_u}, data: {job.trade_date}",
                f"LLM: {base['llm_provider']} — quick `{base['quick_think_llm']}`, deep `{base['deep_think_llm']}`",
                f"OpenAI reasoning_effort: {base.get('openai_reasoning_effort') or '(domyślnie modelu)'}",
                f"Analitycy: {', '.join(analysts)}",
                f"Rundy debat: invest={base['max_debate_rounds']}, risk={base['max_risk_discuss_rounds']}",
                "Transparentność: każde wywołanie LLM i narzędzia zapisuje artefakt JSON (tokeny, koszt, pełna treść).",
            ],
        )

        prev_state: dict[str, Any] | None = None
        final_state: dict[str, Any] | None = None
        step_n = 0

        for raw in ta.graph.stream(init_agent_state, **args):
            chunk = normalize_stream_chunk(raw)
            if not chunk:
                log.warning(
                    "job %s: pominięto krok stream (typ surowy=%s)",
                    job.id,
                    type(raw).__name__,
                )
                continue
            step_n += 1
            lines = describe_state_transition(prev_state, chunk)
            prev_state = chunk
            final_state = chunk
            _push_progress(db, job, events, f"Krok grafu #{step_n}", lines)

        if final_state is None:
            _push_progress(
                db,
                job,
                events,
                "Tryb synchroniczny",
                ["Stream nie zwrócił stanów — wywołanie invoke()."],
            )
            final_state = ta.graph.invoke(init_agent_state, **args)

        ta.curr_state = final_state
        ta._log_state(job.trade_date, final_state)

        signal = ta.process_signal(final_state["final_trade_decision"])

        job.status = "completed"
        job.final_signal = str(signal).strip() if signal else None
        fs = final_state if isinstance(final_state, dict) else dict(final_state)
        job.result_json = json.dumps(_serialize_final_state(fs), ensure_ascii=False)
        job.error_message = None

        _push_progress(
            db,
            job,
            events,
            "Zakończono",
            [
                f"Wyciągnięty sygnał: `{job.final_signal}`",
                "Pełne raporty i debaty zapisane w wyniku (sekcje poniżej po odświeżeniu).",
            ],
        )
    except Exception as e:  # noqa: BLE001
        err = str(e)[:8000]
        job.status = "failed"
        job.error_message = err
        job.final_signal = None
        job.result_json = None
        try:
            _push_progress(
                db,
                job,
                events,
                "Błąd",
                [err[:4000] if err else "Nieznany błąd"],
            )
        except Exception:
            log.exception("job %s: nie udało się zapisać postępu błędu", job_id)
    finally:
        clear_job_context()
        clear_prompt_overrides()
        _restore_environ(prev_env)
        t1 = datetime.now(timezone.utc)
        job.finished_at = t1
        job.duration_ms = int((t1 - t0).total_seconds() * 1000)
        db.commit()
