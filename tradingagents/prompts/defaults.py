"""Domyślne treści promptów v2.0 — baza v1 (``defaults_v1``) + nadpisania instytucjonalne."""

from __future__ import annotations

from tradingagents.prompts.defaults_v1 import DEFAULT_PROMPTS_V1
from tradingagents.prompts.institutional_v2_prompts import V2_MERGE

DEFAULT_PROMPTS: dict[str, str] = {**DEFAULT_PROMPTS_V1, **V2_MERGE}


def catalog() -> dict[str, str]:
    """Niezmienialny snapshot wbudowanych domyślnych promptów (v2.0)."""
    return dict(DEFAULT_PROMPTS)
