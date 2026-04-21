from langchain_core.tools import tool
from typing import Annotated

from tradingagents.agents.utils.tool_json_formatter import tool_response_to_json
from tradingagents.analysis_horizon import resolve_data_windows
from tradingagents.dataflows.config import get_config
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.runtime_context import get_job_context


@tool
def get_news(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve news data for a given ticker symbol.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: JSON z listą ``articles`` (tytuł, źródło, skrót, link).
    """
    ctx = get_job_context()
    anchor = str(ctx.get("trade_date") or end_date or start_date)[:10]
    if get_config().get("enforce_data_windows", True):
        w = resolve_data_windows(anchor)
        start_date, end_date = w.news_start, w.news_end
    raw = route_to_vendor("get_news", ticker, start_date, end_date)
    return tool_response_to_json("get_news", raw, instrument=ticker, trade_date=anchor)


@tool
def get_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:
    """
    Retrieve global news data.
    Uses the configured news_data vendor.
    Args:
        curr_date (str): Current date in yyyy-mm-dd format
        look_back_days (int): Number of days to look back (default 7)
        limit (int): Maximum number of articles to return (default 5)
    Returns:
        str: JSON z ``articles`` dla newsów makro.
    """
    ctx = get_job_context()
    td = str(ctx.get("trade_date") or curr_date)[:10]
    raw = route_to_vendor("get_global_news", td, look_back_days, limit)
    return tool_response_to_json("get_global_news", raw, instrument="GLOBAL", trade_date=td)


@tool
def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve insider transaction information about a company.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: JSON (``kv`` lub ``notes``) z transakcjami insiderów.
    """
    ctx = get_job_context()
    td = str(ctx.get("trade_date") or "")[:10] or None
    raw = route_to_vendor("get_insider_transactions", ticker)
    return tool_response_to_json("get_insider_transactions", raw, instrument=ticker, trade_date=td)
