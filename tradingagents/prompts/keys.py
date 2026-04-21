"""Stable identifiers for editable prompts (API + UI)."""

# Global institutional contract (prefixed to analyst system bodies)
INSTITUTIONAL_GLOBAL_SYSTEM = "institutional_global_system"

# Shared analyst orchestration (LangGraph tool-using template)
TOOL_COLLABORATOR_SYSTEM = "tool_collaborator_system"

ORCHESTRATOR_SYSTEM = "orchestrator_system"
DATA_QUALITY_SYSTEM = "data_quality_system"
VALUATION_SYSTEM = "valuation_system"
ACCOUNTING_QUALITY_SYSTEM = "accounting_quality_system"
SECTOR_SYSTEM = "sector_system"
CATALYST_SYSTEM = "catalyst_system"
SCORING_SYSTEM = "scoring_system"

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
    INSTITUTIONAL_GLOBAL_SYSTEM,
    TOOL_COLLABORATOR_SYSTEM,
    ORCHESTRATOR_SYSTEM,
    DATA_QUALITY_SYSTEM,
    MARKET_ANALYST_SYSTEM,
    SOCIAL_MEDIA_ANALYST_SYSTEM,
    NEWS_ANALYST_SYSTEM,
    NEWS_WEB_ANALYST_SYSTEM,
    FUNDAMENTALS_ANALYST_SYSTEM,
    ACCOUNTING_QUALITY_SYSTEM,
    VALUATION_SYSTEM,
    SECTOR_SYSTEM,
    CATALYST_SYSTEM,
    TRADER_SYSTEM,
    BULL_RESEARCHER,
    BEAR_RESEARCHER,
    RESEARCH_MANAGER,
    PORTFOLIO_MANAGER,
    AGGRESSIVE_DEBATOR,
    CONSERVATIVE_DEBATOR,
    NEUTRAL_DEBATOR,
    REFLECTION_SYSTEM,
    SCORING_SYSTEM,
    SIGNAL_EXTRACTOR_SYSTEM,
)
