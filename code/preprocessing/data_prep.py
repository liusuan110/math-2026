"""数据预处理工具箱：几乎每道题的第一步（C 题尤甚）。

缺失值报告与填补、异常值检测、归一化/标准化、相关性矩阵（可出热图）。
全部基于 pandas，输入输出都是 DataFrame，赛时直接套数据。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """缺失值概览：每列缺失数量与占比，按缺失率降序。"""
    n = len(df)
    rep = pd.DataFrame({
        "缺失数": df.isna().sum(),
        "缺失率": (df.isna().sum() / n).round(4),
        "类型": df.dtypes.astype(str),
    })
    return rep.sort_values("缺失率", ascending=False)


def fill_missing(df: pd.DataFrame, strategy="median") -> pd.DataFrame:
    """填补缺失值。strategy: median / mean / ffill / zero。数值列用统计量，其余前向填充。"""
    out = df.copy()
    num = out.select_dtypes(include="number").columns
    if strategy == "median":
        out[num] = out[num].fillna(out[num].median())
    elif strategy == "mean":
        out[num] = out[num].fillna(out[num].mean())
    elif strategy == "zero":
        out[num] = out[num].fillna(0)
    elif strategy == "ffill":
        out = out.ffill().bfill()
    # 非数值列统一前向/后向填充
    out = out.ffill().bfill()
    return out


def detect_outliers(df: pd.DataFrame, method="iqr", k=1.5) -> pd.DataFrame:
    """异常值检测，返回与 df 同形的布尔表（True=异常）。method: iqr / zscore。"""
    num = df.select_dtypes(include="number")
    mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    if method == "iqr":
        q1, q3 = num.quantile(0.25), num.quantile(0.75)
        iqr = q3 - q1
        mask[num.columns] = (num < q1 - k * iqr) | (num > q3 + k * iqr)
    else:  # zscore
        z = (num - num.mean()) / (num.std(ddof=0) + 1e-12)
        mask[num.columns] = z.abs() > 3
    return mask


def normalize(df: pd.DataFrame, method="minmax") -> pd.DataFrame:
    """数值列归一化。method: minmax -> [0,1] / zscore -> 均值0方差1。"""
    out = df.copy()
    num = out.select_dtypes(include="number").columns
    if method == "minmax":
        rng = out[num].max() - out[num].min()
        out[num] = (out[num] - out[num].min()) / rng.replace(0, 1e-12)
    else:
        out[num] = (out[num] - out[num].mean()) / (out[num].std(ddof=0) + 1e-12)
    return out


def correlation(df: pd.DataFrame, save_heatmap: str | None = None) -> pd.DataFrame:
    """相关系数矩阵；传 save_heatmap 路径则同时存一张热图（需 matplotlib/seaborn）。"""
    corr = df.select_dtypes(include="number").corr()
    if save_heatmap:
        try:
            import os
            import matplotlib.pyplot as plt
            import seaborn as sns
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
            os.makedirs(os.path.dirname(save_heatmap) or ".", exist_ok=True)
            fig.savefig(save_heatmap, dpi=300, bbox_inches="tight")
            print(f"[data_prep] 热图已保存: {save_heatmap}")
        except ImportError:
            print("[data_prep] 未装 seaborn/matplotlib，跳过热图")
    return corr


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "销量": rng.integers(50, 200, 20).astype(float),
        "价格": rng.normal(10, 2, 20),
        "评分": rng.uniform(3, 5, 20),
    })
    df.loc[2, "销量"] = np.nan          # 制造缺失
    df.loc[5, "价格"] = 999             # 制造异常
    print("缺失报告:\n", missing_report(df), "\n")
    filled = fill_missing(df)
    print("异常值个数(IQR):", int(detect_outliers(filled).values.sum()))
    print("归一化后前3行:\n", normalize(filled).head(3).round(3), "\n")
    print("相关矩阵:\n", correlation(filled).round(2))
