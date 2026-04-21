"""Szacunkowe stawki USD / 1M tokenów (input / output) — orientacyjnie, bez gwarancji zgodności z fakturą OpenAI."""

from __future__ import annotations

# Wartości przybliżone — aktualizuj przy zmianie cennika OpenAI.
_PER_MILLION: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4.1": (2.0, 8.0),
    "gpt-4.1-mini": (0.4, 1.6),
    "gpt-5": (1.25, 10.0),
    "gpt-5.4": (1.25, 10.0),
    "gpt-5.4-mini": (0.25, 2.0),
    "gpt-5-mini": (0.25, 2.0),
    "o1": (15.0, 60.0),
    "o1-mini": (3.0, 12.0),
    "o3-mini": (1.1, 4.4),
}


def _match_model(model: str) -> tuple[float, float]:
    m = (model or "").lower().strip()
    if m in _PER_MILLION:
        return _PER_MILLION[m]
    for key, prices in _PER_MILLION.items():
        if key in m:
            return prices
    return (5.0, 15.0)


def estimate_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    pin, pout = _match_model(model)
    return (input_tokens / 1_000_000.0) * pin + (output_tokens / 1_000_000.0) * pout
