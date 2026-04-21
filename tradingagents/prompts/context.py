"""Runtime overrides for agent prompts (e.g. set by the web worker per job)."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Dict, Optional

_overrides: ContextVar[Optional[Dict[str, str]]] = ContextVar(
    "tradingagents_prompt_overrides", default=None
)


def set_prompt_overrides(overrides: Optional[Dict[str, str]]) -> None:
    """Replace prompt overrides for the current context (async-safe)."""
    _overrides.set(dict(overrides) if overrides else None)


def clear_prompt_overrides() -> None:
    _overrides.set(None)


def get_prompt_overrides() -> Dict[str, str]:
    v = _overrides.get()
    return dict(v) if v else {}


def resolve_prompt(key: str, default: str) -> str:
    """Return user override for ``key`` when non-empty, otherwise ``default``."""
    o = _overrides.get()
    if o and key in o:
        val = (o.get(key) or "").strip()
        if val:
            return val
    return default
