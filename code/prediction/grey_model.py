"""灰色预测 GM(1,1)：小样本、趋势性数据的短期预测。

适用：数据量少（4~10 个点）、近似指数增长趋势时（数模高频）。
自带后验差比检验 C 值，判断模型精度。
"""
from __future__ import annotations

import numpy as np


def gm11(x0, predict_n=5) -> dict:
    """GM(1,1) 建模与预测。

    x0: 原始序列（1 维，需为正数序列）
    predict_n: 向后预测的步数
    返回 dict: {fit, forecast, a, b, C, level}
      - fit: 对原始序列的拟合值
      - forecast: 未来 predict_n 步预测
      - C: 后验差比（越小越好；<0.35 优, <0.5 合格, <0.65 勉强, 否则不合格）
    """
    x0 = np.asarray(x0, dtype=float)
    n = len(x0)
    # 1) 一次累加生成 (1-AGO)
    x1 = np.cumsum(x0)
    # 2) 紧邻均值生成 z1
    z1 = 0.5 * (x1[1:] + x1[:-1])
    # 3) 最小二乘求参数 a（发展系数）、b（灰作用量）
    B = np.vstack([-z1, np.ones(n - 1)]).T
    Y = x0[1:]
    a, b = np.linalg.lstsq(B, Y, rcond=None)[0]
    # 4) 时间响应函数，求累加预测值再做累减还原
    def x1_hat(k):  # k 从 0 开始
        return (x0[0] - b / a) * np.exp(-a * k) + b / a
    total = n + predict_n
    x1_pred = np.array([x1_hat(k) for k in range(total)])
    x0_pred = np.empty(total)
    x0_pred[0] = x1_pred[0]
    x0_pred[1:] = np.diff(x1_pred)

    fit = x0_pred[:n]
    forecast = x0_pred[n:]

    # 5) 后验差比检验
    residual = x0 - fit
    C = residual.std(ddof=0) / (x0.std(ddof=0) + 1e-12)
    if C < 0.35:
        level = "优"
    elif C < 0.5:
        level = "合格"
    elif C < 0.65:
        level = "勉强合格"
    else:
        level = "不合格"

    return {"fit": fit, "forecast": forecast, "a": a, "b": b, "C": C, "level": level}


if __name__ == "__main__":
    data = [71.1, 72.4, 72.4, 72.1, 71.4, 72.0, 71.6]
    res = gm11(data, predict_n=3)
    print("拟合值 =", np.round(res["fit"], 2))
    print("未来3期预测 =", np.round(res["forecast"], 2))
    print(f"发展系数 a={res['a']:.4f}, 灰作用量 b={res['b']:.4f}")
    print(f"后验差比 C={res['C']:.4f} -> 精度等级: {res['level']}")
