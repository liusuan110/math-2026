"""TOPSIS 优劣解距离法：给多个方案综合打分排序。

适用：已有指标权重（可来自 AHP 或熵权法），要对若干方案排名。
原理：离"最优解"越近、离"最劣解"越远，得分越高。
"""
from __future__ import annotations

import numpy as np


def topsis(X, weights=None, benefit_cols=None) -> dict:
    """输入"方案×指标"矩阵，返回综合得分与排名。

    weights: 指标权重（默认等权）；可传入 AHP/熵权法的结果。
    benefit_cols: 效益型指标列索引；其余为成本型。默认全部效益型。

    返回 dict: {score, rank}
    """
    X = np.asarray(X, dtype=float)
    n, m = X.shape
    benefit = set(range(m)) if benefit_cols is None else set(benefit_cols)
    w = np.ones(m) / m if weights is None else np.asarray(weights, dtype=float)
    w = w / w.sum()

    # 1) 向量归一化
    norm = np.sqrt((X ** 2).sum(axis=0))
    norm[norm == 0] = 1e-12
    R = X / norm
    # 2) 加权
    V = R * w
    # 3) 确定正理想解 / 负理想解（成本型指标方向相反）
    v_best = np.where([j in benefit for j in range(m)], V.max(axis=0), V.min(axis=0))
    v_worst = np.where([j in benefit for j in range(m)], V.min(axis=0), V.max(axis=0))
    # 4) 到正/负理想解的欧氏距离
    d_best = np.sqrt(((V - v_best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((V - v_worst) ** 2).sum(axis=1))
    # 5) 相对贴近度（得分）
    score = d_worst / (d_best + d_worst + 1e-12)
    # 排名：得分越高名次越靠前
    rank = (-score).argsort().argsort() + 1
    return {"score": score, "rank": rank}


if __name__ == "__main__":
    from entropy_weight import entropy_weight

    # 4 个方案，3 个效益型指标
    X = [
        [80, 0.7, 110],
        [92, 0.85, 130],
        [70, 0.6, 100],
        [88, 0.9, 125],
    ]
    w = entropy_weight(X)["weight"]          # 用熵权法定权
    res = topsis(X, weights=w)
    print("权重 =", np.round(w, 4))
    print("综合得分 =", np.round(res["score"], 4))
    print("排名 =", res["rank"])
