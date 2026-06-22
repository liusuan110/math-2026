"""模糊综合评价 + 灰色关联分析（评价类题补全）。

- 灰色关联分析(GRA)：衡量各方案/因素与「参考序列(最优)」的接近程度，
  小样本、无需大量数据时的关联度排序，常与熵权法配合。
- 模糊综合评价(FCE)：因素权重 + 隶属度矩阵 -> 综合评价向量，处理「优/良/中/差」
  这类等级评定的模糊性。
"""
from __future__ import annotations

import numpy as np


def grey_relation(X, reference=None, rho=0.5, benefit_cols=None) -> dict:
    """灰色关联分析。

    X: 「方案×指标」矩阵。reference: 参考序列（默认取各指标理想值）。
    rho: 分辨系数（惯例 0.5）。benefit_cols: 效益型列索引集合，其余按成本型。
    返回 dict: {grade, rank}—grade 为各方案对参考序列的关联度（越大越优）。
    """
    X = np.asarray(X, dtype=float)
    n, m = X.shape
    benefit = set(range(m)) if benefit_cols is None else set(benefit_cols)
    # 1) 归一化（效益型越大越好、成本型取反），统一到 [0,1]
    Z = np.zeros_like(X)
    for j in range(m):
        col = X[:, j]
        rng = col.max() - col.min()
        rng = rng if rng != 0 else 1e-12
        Z[:, j] = (col - col.min()) / rng if j in benefit else (col.max() - col) / rng
    # 2) 参考序列（默认每个指标取归一化后的最大值 1）
    ref = np.ones(m) if reference is None else np.asarray(reference, dtype=float)
    # 3) 关联系数
    diff = np.abs(Z - ref)
    dmin, dmax = diff.min(), diff.max()
    xi = (dmin + rho * dmax) / (diff + rho * dmax + 1e-12)
    # 4) 关联度 = 各指标关联系数均值
    grade = xi.mean(axis=1)
    rank = (-grade).argsort().argsort() + 1
    return {"grade": grade, "rank": rank}


def fuzzy_evaluation(weights, membership) -> dict:
    """模糊综合评价。

    weights: 因素权重向量（长度 = 因素个数 m，自动归一化）。
    membership: 隶属度矩阵 R，形状 [m 因素 × p 评语等级]，每行是该因素对各等级的隶属度。
    返回 dict: {result(综合评价向量), best_grade_index}。
    采用加权平均合成算子 B = W · R 并归一化。
    """
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    R = np.asarray(membership, dtype=float)
    B = w @ R
    B = B / (B.sum() + 1e-12)
    return {"result": B, "best_grade_index": int(B.argmax())}


if __name__ == "__main__":
    # 灰色关联：4 个方案、3 个效益型指标
    X = [[80, 0.7, 110], [92, 0.85, 130], [70, 0.6, 100], [88, 0.9, 125]]
    gr = grey_relation(X)
    print("灰色关联度 =", np.round(gr["grade"], 4), " 排名 =", gr["rank"])

    # 模糊综合评价：3 个因素（权重），评语等级 [优, 良, 中, 差]
    weights = [0.5, 0.3, 0.2]
    R = [
        [0.6, 0.3, 0.1, 0.0],   # 因素1 对四个等级的隶属度
        [0.2, 0.5, 0.2, 0.1],   # 因素2
        [0.1, 0.3, 0.4, 0.2],   # 因素3
    ]
    grades = ["优", "良", "中", "差"]
    fe = fuzzy_evaluation(weights, R)
    print("综合评价向量 =", np.round(fe["result"], 4))
    print("最终评定等级 =", grades[fe["best_grade_index"]])
