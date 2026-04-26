"""
数据模块 — Tushare 数据获取
"""

import time
import tushare as ts
import pandas as pd
from .config import load_tushare_token


def _get_api():
    """初始化 Tushare Pro API"""
    token = load_tushare_token()
    ts.set_token(token)
    return ts.pro_api()


def fetch_index_data(trade_date: str) -> dict:
    """
    获取当日上证/深证指数数据
    trade_date: 格式 '20260424'
    返回: {sh: {...}, sz: {...}}
    """
    api = _get_api()

    sh = api.index_daily(ts_code='000001.SH', start_date=trade_date, end_date=trade_date,
                         fields='ts_code,trade_date,close,pct_chg,amount')
    sz = api.index_daily(ts_code='399001.SZ', start_date=trade_date, end_date=trade_date,
                         fields='ts_code,trade_date,close,pct_chg,amount')

    result = {}
    for name, df in [('sh', sh), ('sz', sz)]:
        if not df.empty:
            row = df.iloc[0]
            result[name] = {
                'close': round(float(row['close']), 2),
                'pct_chg': round(float(row['pct_chg']), 2),
                'amount': float(row['amount']) if 'amount' in row else 0,
            }
        else:
            result[name] = None

    time.sleep(0.36)
    return result


def fetch_market_history(trade_date: str, days: int = 20) -> pd.DataFrame:
    """
    获取最近 N 天的市场数据（上证+深证）
    返回 DataFrame，列: trade_date, sh_close, sh_pct, sz_close, sz_pct, total_amt
    """
    api = _get_api()

    # 计算起始日期（往前推 days*2 天，因为包含非交易日）
    from datetime import datetime, timedelta
    end_dt = datetime.strptime(trade_date, '%Y%m%d')
    start_dt = end_dt - timedelta(days=days * 2)
    start_str = start_dt.strftime('%Y%m%d')

    sh = api.index_daily(ts_code='000001.SH', start_date=start_str, end_date=trade_date,
                         fields='trade_date,close,pct_chg,amount')
    sz = api.index_daily(ts_code='399001.SZ', start_date=start_str, end_date=trade_date,
                         fields='trade_date,close,pct_chg,amount')

    time.sleep(0.36)

    if sh.empty or sz.empty:
        return pd.DataFrame()

    # 合并
    merged = sh.merge(sz, on='trade_date', suffixes=('_sh', '_sz'))
    merged = merged.rename(columns={
        'close_sh': 'sh_close', 'pct_chg_sh': 'sh_pct', 'amount_sh': 'sh_amount',
        'close_sz': 'sz_close', 'pct_chg_sz': 'sz_pct', 'amount_sz': 'sz_amount',
    })
    merged['total_amt'] = (merged['sh_amount'] + merged['sz_amount']) / 1e9  # 万亿
    merged = merged.sort_values('trade_date').reset_index(drop=True)
    return merged.tail(days)


def fetch_sector_ranking(trade_date: str, top_n: int = 5) -> list:
    """
    获取当日行业板块涨跌排行
    返回: [{name, pct_chg}, ...]
    """
    api = _get_api()

    # 用申万行业指数
    df = api.index_daily(trade_date=trade_date, fields='ts_code,trade_date,pct_chg')

    if df.empty:
        return []

    # 过滤申万行业（8开头）
    sw = df[df['ts_code'].str.startswith('8')].copy()
    sw = sw.sort_values('pct_chg', ascending=False).head(top_n)

    # 获取板块名称
    sw_list = sw.to_dict('records')
    time.sleep(0.36)
    return sw_list


def is_trade_day(trade_date: str) -> bool:
    """检查是否为交易日"""
    api = _get_api()
    cal = api.trade_cal(exchange='SSE', start_date=trade_date, end_date=trade_date)
    if cal.empty:
        return False
    return cal.iloc[0]['is_open'] == 1
