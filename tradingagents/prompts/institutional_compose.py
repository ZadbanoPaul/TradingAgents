"""Składanie prefiksu instytucjonalnego (bez cykli importu z defaults)."""

from __future__ import annotations

from tradingagents.prompts import keys as prompt_keys
from tradingagents.prompts import resolve_prompt


def institutional_system_prefix(
    *,
    current_date: str,
    instrument_extended: str,
) -> str:
    from tradingagents.prompts.defaults import DEFAULT_PROMPTS

    global_tmpl = resolve_prompt(
        prompt_keys.INSTITUTIONAL_GLOBAL_SYSTEM,
        DEFAULT_PROMPTS[prompt_keys.INSTITUTIONAL_GLOBAL_SYSTEM],
    )
    global_part = global_tmpl.format(
        current_date=current_date,
        instrument_context=instrument_extended,
    )
    return global_part + "\n\n---\n\n"
