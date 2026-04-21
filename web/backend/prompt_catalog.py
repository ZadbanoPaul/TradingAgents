"""Metadane promptów dla UI (tytuły, opisy)."""

from tradingagents.prompts.defaults import DEFAULT_PROMPTS
from tradingagents.prompts import keys as k

PROMPT_UI = [
    (k.TOOL_COLLABORATOR_SYSTEM, "Współpraca narzędzi (analitycy)", "Szablon systemowy dla analityków korzystających z narzędzi LangChain."),
    (k.MARKET_ANALYST_SYSTEM, "Analityk rynku (techniczny)", "Treść roli i instrukcji wyboru wskaźników."),
    (k.SOCIAL_MEDIA_ANALYST_SYSTEM, "Analityk social / sentyment", "Zakres analizy social media i newsów spółki."),
    (k.NEWS_ANALYST_SYSTEM, "Analityk newsów / makro", "Zakres raportu makro i newsów."),
    (k.NEWS_WEB_ANALYST_SYSTEM, "News Web Agent (RSS)", "Agent uzupełniający nagłówki z Google News RSS."),
    (k.FUNDAMENTALS_ANALYST_SYSTEM, "Analityk fundamentalny", "Zakres raportu fundamentalnego."),
    (k.TRADER_SYSTEM, "Trader", "Instrukcje dla agenta tradera (placeholdery: {past_memory_str})."),
    (k.BULL_RESEARCHER, "Research: Bull", "Szablon debaty byczej (placeholdery raportów i historii)."),
    (k.BEAR_RESEARCHER, "Research: Bear", "Szablon debaty niedźwiedziej."),
    (k.RESEARCH_MANAGER, "Research Manager", "Facilitator debaty i plan inwestycyjny."),
    (k.PORTFOLIO_MANAGER, "Portfolio Manager", "Końcowa ocena i skala ratingu (placeholdery: {language_suffix})."),
    (k.AGGRESSIVE_DEBATOR, "Risk: agresywny", "Agent ryzyka — perspektywa agresywna."),
    (k.CONSERVATIVE_DEBATOR, "Risk: konserwatywny", "Agent ryzyka — perspektywa konserwatywna."),
    (k.NEUTRAL_DEBATOR, "Risk: neutralny", "Agent ryzyka — perspektywa zbalansowana."),
    (k.REFLECTION_SYSTEM, "Refleksja / pamięć", "Prompt refleksji po decyzjach."),
    (k.SIGNAL_EXTRACTOR_SYSTEM, "Ekstrakcja sygnału", "Krótki prompt wyciągający BUY/HOLD/SELL itd."),
]


def list_prompt_items(overrides: dict[str, str]) -> list[dict]:
    items = []
    for key, title, desc in PROMPT_UI:
        items.append(
            {
                "key": key,
                "title": title,
                "description": desc,
                "default_body": DEFAULT_PROMPTS.get(key, ""),
                "current_body": overrides.get(key) or DEFAULT_PROMPTS.get(key, ""),
            }
        )
    return items
