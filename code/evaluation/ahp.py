"""AHP 层次分析法：由"两两比较判断矩阵"求指标权重，并做一致性检验。

适用：指标权重靠专家主观打分确定时（如"重要性 1~9 标度"）。
核心产出：权重向量 w + 一致性比率 CR（CR<0.1 才可接受）。
"""
from __future__ import annotations

import numpy as np

# 随机一致性指标 RI（n=1..15），AHP 标准表
_RI = [0, 0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41,
       1.45, 1.49, 1.51, 1.48, 1.56, 1.57, 1.59]


def ahp_weight(matrix) -> dict:
    """输入两两比较判断矩阵（n×n，正互反阵），返回权重与一致性检验结果。

    返回 dict: {weight, lambda_max, CI, CR, consistent}
    - weight: 归一化权重向量
    - CR < 0.1 时 consistent=True，权重可用
    """
    A = np.asarray(matrix, dtype=float)
    n = A.shape[0]
    assert A.shape == (n, n), "判断矩阵必须是方阵"

    # 特征值法求权重：取最大特征值对应的特征向量并归一化
    eigvals, eigvecs = np.linalg.eig(A)
    idx = np.argmax(eigvals.real)
    lambda_max = eigvals.real[idx]
    w = np.abs(eigvecs.real[:, idx])
    w = w / w.sum()

    # 一致性检验
    CI = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    RI = _RI[n - 1] if n <= len(_RI) else _RI[-1]
    CR = CI / RI if RI > 0 else 0.0

    return {
        "weight": w,
        "lambda_max": lambda_max,
        "CI": CI,
        "CR": CR,
        "consistent": CR < 0.1,
    }


if __name__ == "__main__":
    # 示例：4 个指标的两两比较矩阵
    A = [
        [1,   2,   3,   5],
        [1/2, 1,   2,   3],
        [1/3, 1/2, 1,   2],
        [1/5, 1/3, 1/2, 1],
    ]
    res = ahp_weight(A)
    print("权重 w =", np.round(res["weight"], 4))
    print(f"lambda_max = {res['lambda_max']:.4f}, CI = {res['CI']:.4f}, CR = {res['CR']:.4f}")
    print("一致性检验:", "通过(CR<0.1)" if res["consistent"] else "不通过，需重新打分")
