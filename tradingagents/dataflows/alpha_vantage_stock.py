from datetime import datetime

from tradingagents.analysis_horizon import resolve_data_windows
from tradingagents.dataflows.config import get_config

from .alpha_vantage_common import _make_api_request, _filter_csv_by_date_range


def get_stock(symbol: str, start_date: str, end_date: str) -> str:
    """
    Returns OHLCV (dzienne lub intraday) filtered to the specified date range.
    """
    cfg = get_config()
    anchor = end_date or start_date
    if cfg.get("enforce_data_windows", True):
        w = resolve_data_windows(anchor)
        start_date, end_date = w.stock_start, w.stock_end
        if w.use_intraday:
            params = {
                "symbol": symbol,
                "interval": w.av_intraday_interval,
                "outputsize": "full",
                "datatype": "csv",
            }
            response = _make_api_request("TIME_SERIES_INTRADAY", params)
            return _filter_csv_by_date_range(response, start_date, end_date)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    today = datetime.now()
    days_from_today_to_start = (today - start_dt).days
    outputsize = "compact" if days_from_today_to_start < 100 else "full"

    params = {
        "symbol": symbol,
        "outputsize": outputsize,
        "datatype": "csv",
    }

    response = _make_api_request("TIME_SERIES_DAILY_ADJUSTED", params)

    return _filter_csv_by_date_range(response, start_date, end_date)