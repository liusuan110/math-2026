"""熵权法：由数据本身的离散程度客观确定指标权重（无需主观打分）。

适用：有一张"样本×指标"的数值表，想客观赋权。
信息熵越小（某指标各样本差异越大）→ 权重越大。
"""
from __future__ import annotations

import numpy as np


def normalize(X, benefit_cols=None):
    """min-max 标准化到 [0,1]。

    benefit_cols: 效益型(越大越好)指标的列索引集合；其余按成本型(越小越好)处理。
    默认全部为效益型。
    """
    X = np.asarray(X, dtype=float)
    n, m = X.shape
    benefit = set(range(m)) if benefit_cols is None else set(benefit_cols)
    Z = np.zeros_like(X)
    for j in range(m):
        col = X[:, j]
        rng = col.max() - col.min()
        if rng == 0:
            Z[:, j] = 1.0  # 该指标无区分度
        elif j in benefit:
            Z[:, j] = (col - col.min()) / rng
        else:
            Z[:, j] = (col.max() - col) / rng
    return Z


def entropy_weight(X, benefit_cols=None) -> dict:
    """输入"样本×指标"矩阵，返回客观权重。

    返回 dict: {weight, entropy, normalized}
    """
    Z = normalize(X, benefit_cols)
    n, m = Z.shape
    # 计算比重 p_ij（加极小量避免 log0）
    P = Z / (Z.sum(axis=0, keepdims=True) + 1e-12)
    k = 1.0 / np.log(n)
    # 信息熵 e_j
    e = -k * (P * np.log(P + 1e-12)).sum(axis=0)
    # 冗余度 d_j = 1 - e_j，权重归一化
    d = 1 - e
    w = d / d.sum()
    return {"weight": w, "entropy": e, "normalized": Z}


if __name__ == "__main__":
    # 示例：5 个样本，3 个指标（假设都是效益型）
    X = [
        [90, 0.8, 120],
        [75, 0.6, 100],
        [88, 0.9, 110],
        [60, 0.5,  95],
        [95, 0.7, 130],
    ]
    res = entropy_weight(X)
    print("熵权法权重 w =", np.round(res["weight"], 4))
    print("各指标信息熵 e =", np.round(res["entropy"], 4))
