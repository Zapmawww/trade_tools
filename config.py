"""
配置模块 — 统一加载 Token 和路径配置
安全：Token 从 ~/tushare.env 读取，不在输出中展示
"""

import os


def load_tushare_token() -> str:
    """从安全的环境文件加载 Tushare Token"""
    env_path = os.path.expanduser('~/tushare.env')
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"未找到 {env_path}，请先创建")

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith('TUSHARE_TOKEN='):
                return line.split('=', 1)[1].strip()

    raise ValueError("未找到 TUSHARE_TOKEN 配置")


# 项目路径常量
BASE_DIR = os.path.expanduser('~/obsidian_notes/40-Investment/XY老师笔记')
TIMELINE_DIR = os.path.join(BASE_DIR, '01-时间线')
THEME_DIR = os.path.join(BASE_DIR, '02-主题')
REVIEW_DIR = os.path.join(BASE_DIR, '03-复盘')
WATCHLIST_FILE = os.path.join(REVIEW_DIR, '观察池.md')
TIMING_FILE = os.path.join(REVIEW_DIR, '择时状态.md')
