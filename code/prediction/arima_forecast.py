"""ARIMA 时间序列预测模板（statsmodels）。

适用：有较长时间序列（≥30 点）、需预测未来趋势时。
关键参数 (p,d,q)：d=差分阶数(消除趋势)，p=自回归阶，q=移动平均阶。
入门可先固定 d=1，对 p,q 做小范围网格搜索按 AIC 选优。
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA


def auto_arima(series, p_range=range(0, 3), d=1, q_range=range(0, 3)):
    """对 (p,d,q) 小范围网格搜索，按 AIC 最小选最优模型。"""
    best = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for p in p_range:
            for q in q_range:
                try:
                    model = ARIMA(series, order=(p, d, q)).fit()
                    if best is None or model.aic < best[1]:
                        best = ((p, d, q), model.aic, model)
                except Exception:
                    continue
    return best  # (order, aic, fitted_model)


def forecast(series, steps=10, order=None):
    """预测未来 steps 步。order=None 时自动选参。返回 (order, 预测值)。"""
    if order is None:
        order, _, model = auto_arima(series)
    else:
        model = ARIMA(series, order=order).fit()
    pred = model.forecast(steps=steps)
    return order, np.asarray(pred)


if __name__ == "__main__":
    # 构造带趋势 + 季节波动的序列
    rng = np.random.default_rng(0)
    t = np.arange(120)
    series = pd.Series(0.5 * t + 10 * np.sin(t / 6) + rng.normal(0, 2, len(t)))

    order, pred = forecast(series, steps=12)
    print(f"自动选定 ARIMA 阶数 (p,d,q) = {order}")
    print("未来12步预测 =", np.round(pred, 2))
