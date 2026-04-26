"""
技术指标模块 — 用 pandas 计算，避免 LLM 估算误差
"""

import pandas as pd
import numpy as np


# ============================================================
# 均线系列
# ============================================================

def calc_ma(df: pd.DataFrame, price_col: str = 'close', period: int = 5) -> float:
    """
    计算最新一天的 N 日均线
    df: 需要包含 price_col 列，按时间升序
    """
    if len(df) < period:
        return None
    return round(df[price_col].tail(period).mean(), 2)


def calc_ma_series(df: pd.DataFrame, price_col: str = 'close', period: int = 5) -> pd.Series:
    """计算完整的均线序列"""
    return df[price_col].rolling(window=period).mean()


# ============================================================
# 成交量系列
# ============================================================

def calc_volume_trend(df: pd.DataFrame, vol_col: str = 'total_amt') -> dict:
    """
    计算成交量趋势
    df: 需要包含 vol_col 列（单位：万亿）
    返回: {
        'today': 今日成交量,
        'avg_5': 5日均量,
        'avg_20': 20日均量,
        'trend': '放量'/'缩量'/'平量',
        'vs_5': 相对5日均量的变化百分比,
        'vs_20': 相对20日均量的变化百分比,
    }
    """
    if len(df) < 5:
        return {'trend': '数据不足', 'today': None, 'avg_5': None, 'avg_20': None}

    today = float(df[vol_col].iloc[-1])
    avg_5 = float(df[vol_col].tail(5).mean())
    avg_20 = float(df[vol_col].tail(min(20, len(df))).mean()) if len(df) >= 20 else avg_5

    vs_5 = round((today - avg_5) / avg_5 * 100, 1) if avg_5 > 0 else 0
    vs_20 = round((today - avg_20) / avg_20 * 100, 1) if avg_20 > 0 else 0

    # 相对5日均量的判断
    if vs_5 > 10:
        trend = '放量'
    elif vs_5 < -10:
        trend = '缩量'
    else:
        trend = '平量'

    return {
        'today': round(today, 2),
        'avg_5': round(avg_5, 2),
        'avg_20': round(avg_20, 2),
        'trend': trend,
        'vs_5': vs_5,
        'vs_20': vs_20,
    }


def calc_volume_threshold(df: pd.DataFrame, vol_col: str = 'total_amt') -> dict:
    """
    计算动态量能门槛（替代固定数字如 2.56万亿）
    用近20日均量的 1.15x 作为"充分量能"门槛
    返回: {
        'threshold_active': 活跃门槛（20日均量x1.15）,
        'threshold_strong': 强势门槛（20日均量x1.30）,
        'recommendation': 量能评估,
    }
    """
    if len(df) < 10:
        return {'threshold_active': None, 'threshold_strong': None, 'recommendation': '数据不足'}

    avg_20 = float(df[vol_col].tail(min(20, len(df))).mean())
    today = float(df[vol_col].iloc[-1])

    threshold_active = round(avg_20 * 1.15, 2)  # 活跃门槛
    threshold_strong = round(avg_20 * 1.30, 2)  # 强势门槛

    if today >= threshold_strong:
        rec = f'量能达到强势门槛（{threshold_strong}万亿），支撑主升'
    elif today >= threshold_active:
        rec = f'量能达标活跃门槛（{threshold_active}万亿），结构性行情可行'
    else:
        rec = f'量能不足（需{threshold_active}万亿），以防守为主'

    return {
        'threshold_active': threshold_active,
        'threshold_strong': threshold_strong,
        'current': round(today, 2),
        'avg_20': round(avg_20, 2),
        'recommendation': rec,
    }


# ============================================================
# 趋势判断
# ============================================================

def calc_trend_direction(df: pd.DataFrame, price_col: str = 'sh_close', period: int = 5) -> str:
    """
    判断最近 period 天的趋势方向
    返回: '上升'/'下降'/'震荡'
    """
    if len(df) < period + 1:
        return '数据不足'

    prices = df[price_col].tail(period + 1)
    change_pct = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0] * 100

    if change_pct > 2:
        return '上升'
    elif change_pct < -2:
        return '下降'
    else:
        return '震荡'


# ============================================================
# 个股均线（单只股票）
# ============================================================

def search_stock_by_name(api, keyword: str) -> list:
    """
    通过部分名称搜索股票代码
    例: search_stock_by_name(api, "大普微") → [{'ts_code': '688789.SH', 'name': '大普微', ...}]
    """
    import time as _time
    df = api.stock_basic(exchange='', list_status='L',
                         fields='ts_code,name,industry,list_date')
    _time.sleep(0.36)
    if df.empty:
        return []

    matches = df[df['name'].str.contains(keyword, na=False)]
    return matches.to_dict('records')


def find_stock_code(api, keyword: str) -> str | None:
    """
    通过部分名称查找股票代码，返回第一个匹配的 ts_code
    例: find_stock_code(api, "大普微") → '688789.SH'
    例: find_stock_code(api, "东山精密") → '002456.SZ'
    如果没有精确匹配，尝试模糊搜索
    """
    # 先精确匹配
    result = search_stock_by_name(api, f"^{keyword}$")
    if result:
        return result[0]['ts_code']

    # 再模糊匹配
    result = search_stock_by_name(api, keyword)
    if result:
        print(f"  模糊匹配 '{keyword}' → {len(result)} 个结果:")
        for r in result[:5]:
            print(f"    {r['ts_code']} {r['name']} ({r.get('industry', '')})")
        return result[0]['ts_code']

    return None


def calc_stock_ma(api, ts_code: str, trade_date: str, ma_periods: list = [5, 10, 20]) -> dict:
    """
    计算单只股票的多条均线
    api: Tushare Pro API
    ts_code: 股票代码，如 '002456.SZ'
    trade_date: 格式 '20260424'
    ma_periods: 均线周期列表
    返回: {date, close, ma5, ma10, ma20, ...}
    """
    import time as _time
    from datetime import datetime, timedelta

    end_dt = datetime.strptime(trade_date, '%Y%m%d')
    start_dt = end_dt - timedelta(days=max(ma_periods) * 3)
    start_str = start_dt.strftime('%Y%m%d')

    df = api.daily(ts_code=ts_code, start_date=start_str, end_date=trade_date,
                   fields='trade_date,close')
    if df.empty:
        return None

    df = df.sort_values('trade_date').reset_index(drop=True)
    result = {'trade_date': trade_date, 'close': round(float(df.iloc[-1]['close']), 2)}

    for period in ma_periods:
        if len(df) >= period:
            result[f'ma{period}'] = round(float(df.iloc[-period:]['close'].mean()), 2)
        else:
            result[f'ma{period}'] = None

    _time.sleep(0.36)
    return result
