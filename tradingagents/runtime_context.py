"""Kontekst wykonywanego joba (data, ticker) widoczny dla narzędzi LangChain w tym samym tasku."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_ctx: ContextVar[dict[str, Any]] = ContextVar("tradingagents_job_ctx", default={})


def bind_job_context(*, trade_date: str, ticker: str, extra: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {"trade_date": str(trade_date), "ticker": str(ticker).strip()}
    if extra:
        payload.update(extra)
    _ctx.set(payload)


def clear_job_context() -> None:
    _ctx.set({})


def get_job_context() -> dict[str, Any]:
    return dict(_ctx.get({}))
