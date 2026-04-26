# trade_tools

A股复盘辅助工具包。

## 模块
- `config.py` — Token加载、路径配置
- `data.py` — Tushare数据获取
- `indicators.py` — 技术指标计算（MA/成交量等）
- `review.py` — 复盘报告生成逻辑

## 使用
```python
from trade_tools.data import fetch_market_data
from trade_tools.indicators import calc_ma, calc_volume_trend

data = fetch_market_data('20260424')
ma5 = calc_ma(data, period=5)
```
