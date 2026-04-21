"""Zgodność opcji OpenAI (Responses / Chat) z konkretnym ID modelu."""

from __future__ import annotations


def openai_model_supports_reasoning_effort(model_id: str) -> bool:
    """Czy można bezpiecznie przekazać ``reasoning_effort`` (pole API ``reasoning.effort``).

    Modele typu GPT-4.x / 4o / 4.1 zwracają 400 ``unsupported_parameter`` dla
    ``reasoning.effort``. Parametr dotyczy modeli z rozszerzonym rozumowaniem
    (seria **o*** oraz rodzina **gpt-5*** w API Responses — patrz dokumentacja OpenAI).
    """
    m = (model_id or "").strip().lower()
    if not m:
        return False
    if m.startswith(("o1", "o2", "o3", "o4")):
        return True
    if m.startswith("gpt-5"):
        return True
    return False
