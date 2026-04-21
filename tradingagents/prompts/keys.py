"""Stable identifiers for editable prompts (API + UI)."""

# Shared analyst orchestration (LangGraph tool-using template)
TOOL_COLLABORATOR_SYSTEM = "tool_collaborator_system"

MARKET_ANALYST_SYSTEM = "market_analyst_system"
SOCIAL_MEDIA_ANALYST_SYSTEM = "social_media_analyst_system"
NEWS_ANALYST_SYSTEM = "news_analyst_system"
NEWS_WEB_ANALYST_SYSTEM = "news_web_analyst_system"
FUNDAMENTALS_ANALYST_SYSTEM = "fundamentals_analyst_system"

TRADER_SYSTEM = "trader_system"

BULL_RESEARCHER = "bull_researcher"
BEAR_RESEARCHER = "bear_researcher"
RESEARCH_MANAGER = "research_manager"
PORTFOLIO_MANAGER = "portfolio_manager"

AGGRESSIVE_DEBATOR = "aggressive_debator"
CONSERVATIVE_DEBATOR = "conservative_debator"
NEUTRAL_DEBATOR = "neutral_debator"

REFLECTION_SYSTEM = "reflection_system"
SIGNAL_EXTRACTOR_SYSTEM = "signal_extractor_system"

ALL_PROMPT_KEYS: tuple[str, ...] = (
    TOOL_COLLABORATOR_SYSTEM,
    MARKET_ANALYST_SYSTEM,
    SOCIAL_MEDIA_ANALYST_SYSTEM,
    NEWS_ANALYST_SYSTEM,
    NEWS_WEB_ANALYST_SYSTEM,
    FUNDAMENTALS_ANALYST_SYSTEM,
    TRADER_SYSTEM,
    BULL_RESEARCHER,
    BEAR_RESEARCHER,
    RESEARCH_MANAGER,
    PORTFOLIO_MANAGER,
    AGGRESSIVE_DEBATOR,
    CONSERVATIVE_DEBATOR,
    NEUTRAL_DEBATOR,
    REFLECTION_SYSTEM,
    SIGNAL_EXTRACTOR_SYSTEM,
)
