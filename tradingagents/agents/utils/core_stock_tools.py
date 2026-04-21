from langchain_core.tools import tool
from typing import Annotated

from tradingagents.agents.utils.tool_json_formatter import tool_response_to_json
from tradingagents.analysis_horizon import resolve_effective_stock_window
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.runtime_context import get_job_context


@tool
def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve stock price data (OHLCV) for a given ticker symbol.
    Uses the configured core_stock_apis vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: Pojedynczy obiekt JSON (schema tradingagents) z polem ``timeseries`` (OHLCV) do wykresów.
    """
    ctx = get_job_context()
    s, e = resolve_effective_stock_window(ctx.get("trade_date"), start_date, end_date)
    raw = route_to_vendor("get_stock_data", symbol, s, e)
    td = str(ctx.get("trade_date") or e or s)[:10]
    return tool_response_to_json("get_stock_data", raw, instrument=symbol, trade_date=td)
