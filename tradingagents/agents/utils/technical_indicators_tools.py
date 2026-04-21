from langchain_core.tools import tool
from typing import Annotated

from tradingagents.agents.utils.tool_json_formatter import tool_response_to_json
from tradingagents.dataflows.config import get_config
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.indicators_catalog import resolve_user_indicator_selection
from tradingagents.runtime_context import get_job_context


@tool
def get_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 30,
) -> str:
    """
    Retrieve a single technical indicator for a given ticker symbol.
    Uses the configured technical_indicators vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        indicator (str): A single technical indicator name, e.g. 'rsi', 'macd'. Call this tool once per indicator.
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 30
    Returns:
        str: JSON (schema tradingagents) z ``timeseries`` dla wskaźnika — przy wielu wskaźnikach zwracana jest lista JSON w jednym stringu (bloki oddzielone ``\\n\\n``).
    """
    cfg = get_config()
    ctx = get_job_context()
    td = str(ctx.get("trade_date") or curr_date)[:10]
    allowed = set(
        resolve_user_indicator_selection(
            select_all=bool(cfg.get("indicators_select_all")),
            selected=list(cfg.get("selected_indicators") or []),
            depth=str(cfg.get("research_depth", "medium")),
            horizon=str(cfg.get("investment_horizon", "swing_medium")),
        )
    )
    indicators = [i.strip().lower() for i in indicator.split(",") if i.strip()]
    indicators = [i for i in indicators if i in allowed][:12]
    if not indicators:
        indicators = list(allowed)[:10]
    results = []
    for ind in indicators:
        try:
            raw = route_to_vendor("get_indicators", symbol, ind, curr_date, look_back_days)
            results.append(
                tool_response_to_json(
                    "get_indicators",
                    raw,
                    instrument=symbol,
                    trade_date=td,
                    extra_description_lines=[f"Wskaźnik (id): {ind}"],
                )
            )
        except ValueError as e:
            results.append(
                tool_response_to_json(
                    "get_indicators",
                    str(e),
                    instrument=symbol,
                    trade_date=td,
                )
            )
    return "\n\n".join(results)