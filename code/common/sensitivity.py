"""灵敏度分析助手：论文「结果分析」里几乎必有的一节。

给定一个「参数字典 -> 标量输出」的模型函数，扰动某个/某些参数，
观察输出如何变化，量化模型对参数的敏感程度与稳健性。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def one_at_a_time(model, base_params: dict, param: str,
                  ratios=(-0.2, -0.1, 0, 0.1, 0.2)) -> pd.DataFrame:
    """单因素灵敏度(OAT)：固定其它参数，让一个参数在基准值上下按比例变化。

    model(params: dict) -> float。base_params: 基准参数。param: 要扰动的键。
    ratios: 相对基准的变化比例。返回含 [比例, 参数值, 输出, 输出变化率] 的表。
    """
    base_val = base_params[param]
    base_out = model(base_params)
    rows = []
    for r in ratios:
        p = dict(base_params)
        p[param] = base_val * (1 + r)
        out = model(p)
        rows.append({
            "变化比例": r,
            f"{param}": p[param],
            "输出": out,
            "输出变化率": (out - base_out) / (abs(base_out) + 1e-12),
        })
    return pd.DataFrame(rows)


def tornado(model, base_params: dict, params=None, ratio=0.1) -> pd.DataFrame:
    """龙卷风图数据：每个参数 ±ratio 各扰动一次，按影响幅度排序。

    用于一眼看出「哪个参数最关键」。返回按敏感度降序的表。
    """
    base_out = model(base_params)
    params = list(base_params) if params is None else params
    rows = []
    for k in params:
        p_lo, p_hi = dict(base_params), dict(base_params)
        p_lo[k] = base_params[k] * (1 - ratio)
        p_hi[k] = base_params[k] * (1 + ratio)
        out_lo, out_hi = model(p_lo), model(p_hi)
        sens = abs(out_hi - out_lo) / (abs(base_out) + 1e-12)
        rows.append({"参数": k, "下扰动输出": out_lo, "上扰动输出": out_hi,
                     "敏感度": sens})
    return pd.DataFrame(rows).sort_values("敏感度", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    # 示例模型：利润 = (售价-成本)*销量，销量随价格上升而下降
    def profit(p):
        price, cost = p["price"], p["cost"]
        demand = max(0, 1000 - 30 * price)
        return (price - cost) * demand

    base = {"price": 20.0, "cost": 8.0}
    print("基准利润:", profit(base))
    print("\n单因素灵敏度(扰动 price):")
    print(one_at_a_time(profit, base, "price").round(3).to_string(index=False))
    print("\n龙卷风(各参数 ±10%，按敏感度排序):")
    print(tornado(profit, base).round(4).to_string(index=False))
