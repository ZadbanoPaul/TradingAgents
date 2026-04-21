"""Rozszerzony kontekst instrumentu + prefiks instytucjonalny dla promptów (v2)."""

from __future__ import annotations

from typing import Any

from tradingagents.agents.utils.agent_utils import build_instrument_context
from tradingagents.dataflows.config import get_config


def _cfg_str(cfg: dict[str, Any], key: str, default: str = "N/A") -> str:
    meta = cfg.get("instrument_meta") or {}
    if not isinstance(meta, dict):
        return default
    v = meta.get(key)
    if v is None or str(v).strip() == "":
        return default
    return str(v).strip()


def horizon_label(cfg: dict[str, Any]) -> str:
    h = str(cfg.get("investment_horizon") or "swing_medium")
    return {
        "intraday": "very short term (days to 2 weeks)",
        "swing_short": "short term (2 weeks to 3 months)",
        "swing_medium": "medium term (3 to 12 months)",
        "position": "long term (12 months or more)",
        "long_term": "long term (12 months or more)",
    }.get(h, f"configured horizon: {h}")


def build_extended_instrument_block(state: dict[str, Any], *, tool_names: str = "N/A") -> str:
    """Blok jak w specyfikacji v2 (placeholdery wypełniane z konfiguracji joba)."""
    cfg = get_config()
    ticker = str(state.get("company_of_interest", "")).strip()
    trade_date = str(state.get("trade_date", "")).strip()
    return (
        "Instrument context:\n"
        f"- Ticker: {ticker}\n"
        f"- Company name: {_cfg_str(cfg, 'company_name', ticker)}\n"
        f"- Exchange: {_cfg_str(cfg, 'exchange')}\n"
        f"- Country / primary listing jurisdiction: {_cfg_str(cfg, 'country')}\n"
        f"- Currency: {_cfg_str(cfg, 'currency')}\n"
        f"- Sector: {_cfg_str(cfg, 'sector')}\n"
        f"- Industry: {_cfg_str(cfg, 'industry')}\n"
        f"- Asset type: {_cfg_str(cfg, 'asset_type', 'equity')}\n"
        f"- Current date: {trade_date}\n"
        f"- Investment horizon (task): {horizon_label(cfg)}\n"
        f"- Strategy style: {_cfg_str(cfg, 'strategy_style', 'quality')}\n"
        f"- Benchmark: {_cfg_str(cfg, 'benchmark')}\n"
        f"- Portfolio context: {_cfg_str(cfg, 'portfolio_context')}\n"
        f"- Existing position: {_cfg_str(cfg, 'existing_position', 'none stated')}\n"
        f"- Maximum position size: {_cfg_str(cfg, 'max_position_size')}\n"
        f"- Risk budget: {_cfg_str(cfg, 'risk_budget')}\n"
        f"- Liquidity constraints: {_cfg_str(cfg, 'liquidity_constraints')}\n"
        f"- Tax / jurisdiction constraints: {_cfg_str(cfg, 'tax_constraints')}\n"
        f"- Available tools: {tool_names}\n"
        f"- Minimal ticker instruction: {build_instrument_context(ticker)}"
    )

