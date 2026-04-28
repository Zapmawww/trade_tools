"""
指标可视化模块 — 统一画图入口
"""

import sys
sys.path.insert(0, '/home/ubuntu')
from trade_tools.config import load_tushare_token
from trade_tools.indicators import calc_double_line, calc_brick_chart

import tushare as ts
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'WenQuanYi Micro Hei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def plot_double_line_and_brick(
    ts_code: str,
    start_date: str = '20250601',
    end_date: str = None,
    output_path: str = None,
    show_volume: bool = False,
) -> str:
    """
    绘制 双线系统（主图）+ 砖型图（副图）
    可选叠加成交量

    参数:
        ts_code: 股票代码，如 '688981.SH'
        start_date: 起始日期 'YYYYMMDD'
        end_date: 结束日期，默认取最近
        output_path: 输出图片路径，默认 /home/ubuntu/chart_{ts_code}.png
        show_volume: 是否在主图下方增加成交量副图

    返回:
        输出图片的绝对路径
    """
    from datetime import datetime

    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if output_path is None:
        output_path = f'/home/ubuntu/chart_{ts_code.replace(".", "_")}.png'

    # Fetch data
    pro = ts.pro_api(load_tushare_token())
    df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    if df.empty:
        raise ValueError(f'No data for {ts_code} between {start_date} and {end_date}')

    df = df.sort_values('trade_date').reset_index(drop=True)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = calc_double_line(df)
    df = calc_brick_chart(df)
    df_valid = df.dropna(subset=['yellow_line']).copy()

    n = len(df_valid)
    x_int = np.arange(n)

    # Layout
    if show_volume:
        fig, (ax1, ax2, ax3) = plt.subplots(
            3, 1, figsize=(14, 11),
            gridspec_kw={'height_ratios': [3, 1, 1]},
            sharex=True
        )
    else:
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(14, 9),
            gridspec_kw={'height_ratios': [3, 1]},
            sharex=True
        )
        ax3 = None

    fig.suptitle(f'{ts_code} — 双线系统 + 砖型图', fontsize=14, fontweight='bold')

    # Main chart: close + white/yellow lines
    ax1.plot(x_int, df_valid['close'], label='收盘价', color='#333333', linewidth=1.2, alpha=0.7)
    ax1.plot(x_int, df_valid['white_line'], label='白线 EMA(EMA(C,10),10)', color='#4444EE', linewidth=1.5)
    ax1.plot(x_int, df_valid['yellow_line'], label='黄线 BBI改良(14,28,57,114)', color='#DDAA00', linewidth=1.5)
    ax1.set_ylabel('价格', fontsize=11)
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Volume sub-chart (optional)
    if show_volume and ax3 is not None:
        vol_colors = ['#CC2222' if c >= o else '#22AA22' for c, o in zip(df_valid['close'], df_valid['open'])]
        ax3.bar(x_int, df_valid['vol'] / 100, color=vol_colors, width=0.8, alpha=0.7)
        ax3.set_ylabel('成交量(万手)', fontsize=10)
        ax3.grid(True, alpha=0.3)

    # Brick sub-chart
    vals = df_valid['brick_value'].values
    bottoms = []
    heights = []
    colors = []
    for i in range(1, n):
        prev_val = vals[i-1]
        curr_val = vals[i]
        colors.append('#CC2222' if curr_val >= prev_val else '#22AA22')
        bottoms.append(min(prev_val, curr_val))
        heights.append(abs(curr_val - prev_val))

    x_sub = x_int[1:]
    # width=1.0 for continuous wall, no gaps
    ax2.bar(x_sub, heights, bottom=bottoms, color=colors, width=1.0, edgecolor='none', alpha=0.9)
    ax2.axhline(y=0, color='black', linewidth=0.5, alpha=0.3)
    ax2.set_ylabel('砖型图', fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlabel('日期', fontsize=11)
    ax2.set_ylim(max(0, min(vals)*0.95), max(vals)*1.1)

    # X-axis labels: monthly
    dates = df_valid['trade_date']
    month_locs, month_labels = [], []
    for i, d in enumerate(dates):
        if i == 0 or d.month != dates.iloc[i-1].month:
            month_locs.append(i)
            month_labels.append(d.strftime('%Y-%m'))

    ax1.set_xticks(month_locs)
    ax1.set_xticklabels(month_labels, fontsize=8)
    if ax3:
        ax3.set_xticks(month_locs)
        ax3.set_xticklabels(month_labels, fontsize=8)
    ax2.set_xticks(month_locs)
    ax2.set_xticklabels(month_labels, fontsize=8)

    ax1.set_xlim(-0.5, n - 0.5)
    ax2.set_xlim(-0.5, n - 0.5)
    if ax3:
        ax3.set_xlim(-0.5, n - 0.5)

    # Brick legend
    legend_elements = [
        Patch(facecolor='#CC2222', label='红砖 (上升)'),
        Patch(facecolor='#22AA22', label='绿砖 (下降)'),
    ]
    ax2.legend(handles=legend_elements, loc='upper right', fontsize=9)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
