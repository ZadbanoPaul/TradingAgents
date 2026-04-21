"""Znane placeholdery w promptach (szablony LangChain / agentów)."""

from __future__ import annotations

# (nazwa, opis, gdzie wstrzykiwane)
PLACEHOLDERS: list[dict[str, str]] = [
    {"id": "tool_names", "description": "Lista nazw narzędzi dostępnych węzłowi (collaborator).", "context": "tool_collaborator"},
    {"id": "system_message", "description": "Treść systemowa konkretnego analityka.", "context": "tool_collaborator"},
    {"id": "current_date", "description": "Data bieżąca symulacji (trade_date).", "context": "tool_collaborator"},
    {"id": "instrument_context", "description": "Rozszerzony kontekst instrumentu (v2: ticker, horyzont, benchmark, limity ryzyka, narzędzia).", "context": "tool_collaborator, research_manager, portfolio_manager"},
    {"id": "orchestrator_report", "description": "Podsumowanie orkiestratora (status procesu, luki danych).", "context": "research_manager"},
    {"id": "data_quality_report", "description": "Raport agenta jakości danych.", "context": "research_manager, portfolio_manager"},
    {"id": "scoring_report", "description": "Agregowana punktacja ważona.", "context": "research_manager, portfolio_manager"},
    {"id": "valuation_report", "description": "Raport wyceny (multiples, scenariusze).", "context": "bull, bear, research_manager"},
    {"id": "accounting_quality_report", "description": "Raport jakości rachunkowości / zysków.", "context": "bull, bear, research_manager"},
    {"id": "sector_report", "description": "Raport sektora i pozycji konkurencyjnej.", "context": "bull, bear, research_manager"},
    {"id": "catalyst_report", "description": "Raport katalizatorów i timingów zdarzeń.", "context": "bull, bear, research_manager"},
    {"id": "bull_argument", "description": "Skumulowana historia / argumentacja byka.", "context": "research_manager"},
    {"id": "bear_argument", "description": "Skumulowana historia / argumentacja niedźwiedzia.", "context": "research_manager"},
    {"id": "past_memory_str", "description": "Skrócone wspomnienia BM25 z pamięci agenta.", "context": "trader, research_manager, bull, bear"},
    {"id": "history", "description": "Historia debaty / ryzyka.", "context": "research_manager, bull, bear, risk"},
    {"id": "market_research_report", "description": "Raport analityka rynku.", "context": "bull, bear, risk, trader"},
    {"id": "sentiment_report", "description": "Raport social / sentyment.", "context": "bull, bear, risk, trader"},
    {"id": "news_report", "description": "Raport newsów (API makro/spółka).", "context": "bull, bear, risk, trader"},
    {"id": "fundamentals_report", "description": "Raport fundamentalny.", "context": "bull, bear, risk, trader"},
    {"id": "current_response", "description": "Ostatnia wypowiedź przeciwnika (debata byk/niedźwiedź).", "context": "bull, bear"},
    {"id": "research_plan", "description": "Plan z Research Manager.", "context": "portfolio_manager"},
    {"id": "trader_plan", "description": "Propozycja tradera.", "context": "portfolio_manager"},
    {"id": "language_suffix", "description": "Instrukcja języka wyjściowego (PL/EN).", "context": "portfolio_manager"},
    {"id": "trader_decision", "description": "Tekst planu / decyzji tradera dla ryzyka.", "context": "risk debators"},
    {"id": "current_aggressive_response", "description": "Ostatnia wypowiedź analityka agresywnego.", "context": "risk"},
    {"id": "current_conservative_response", "description": "Ostatnia wypowiedź konserwatywnego.", "context": "risk"},
    {"id": "current_neutral_response", "description": "Ostatnia wypowiedź neutralnego.", "context": "risk"},
]


def list_placeholders() -> list[dict[str, str]]:
    return list(PLACEHOLDERS)
