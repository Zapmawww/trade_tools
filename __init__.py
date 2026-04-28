"""
trade_tools — A股复盘辅助工具包
"""

from .config import load_tushare_token, BASE_DIR, TIMELINE_DIR, THEME_DIR, REVIEW_DIR, WATCHLIST_FILE, TIMING_FILE
from .data import fetch_index_data, fetch_market_history, is_trade_day
from .indicators import (
    calc_ma, calc_ma_series,
    calc_volume_trend, calc_volume_threshold,
    calc_trend_direction,
    calc_stock_ma, search_stock_by_name, find_stock_code,
    # 标准指标
    calc_kdj, calc_macd,
    # 双线系统
    calc_double_line,
    # 砖型图
    calc_brick_chart,
)
from .plotting import plot_double_line_and_brick

__all__ = [
    'load_tushare_token',
    'BASE_DIR', 'TIMELINE_DIR', 'THEME_DIR', 'REVIEW_DIR', 'WATCHLIST_FILE', 'TIMING_FILE',
    'fetch_index_data', 'fetch_market_history', 'is_trade_day',
    'calc_ma', 'calc_ma_series',
    'calc_volume_trend', 'calc_volume_threshold',
    'calc_trend_direction', 'calc_stock_ma',
    'search_stock_by_name', 'find_stock_code',
    # 标准指标
    'calc_kdj', 'calc_macd',
    # 双线系统
    'calc_double_line',
    # 砖型图
    'calc_brick_chart',
    # 可视化
    'plot_double_line_and_brick',
]
