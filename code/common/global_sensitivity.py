"""全局敏感性分析：Morris 筛选 + Sobol 近似指标。

参考思想：
    - SALib: Sobol / Morris / FAST 等全局敏感性分析工具
    - Saltelli / Morris 方法在数学建模论文中常用于说明“哪个参数最影响结论”

为什么另写轻量模板：
    赛时不一定能临时安装 SALib；本文件只依赖 numpy/pandas，
    先提供足够写论文的全局敏感性基线。若时间充裕，可再用 SALib 复核。

约定：
    model(params: dict) -> float
    bounds: {"参数名": (lo, hi), ...}
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _scale_unit_samples(unit_samples: np.ndarray, names: list[str], bounds: dict) -> list[dict]:
    """把 [0,1] 单位超立方样本映射到参数字典列表。"""
    rows = []
    for u in unit_samples:
        p = {}
        for j, name in enumerate(names):
            lo, hi = bounds[name]
            p[name] = float(lo + u[j] * (hi - lo))
        rows.append(p)
    return rows


def latin_hypercube(bounds: dict, n: int, seed=0) -> pd.DataFrame:
    """简单 Latin Hypercube 抽样。

    每个参数维度分成 n 个区间，每个区间取一次，能比纯随机更均匀地覆盖空间。
    """
    rng = np.random.default_rng(seed)
    names = list(bounds)
    unit = np.zeros((n, len(names)))
    for j in range(len(names)):
        unit[:, j] = (np.arange(n) + rng.random(n)) / n
        rng.shuffle(unit[:, j])
    rows = _scale_unit_samples(unit, names, bounds)
    return pd.DataFrame(rows)


def evaluate_samples(model, samples: pd.DataFrame) -> pd.DataFrame:
    """对样本表逐行运行模型，追加 output 列。"""
    out = samples.copy()
    out["output"] = [float(model(row.to_dict())) for _, row in samples.iterrows()]
    return out


def morris_screening(model, bounds: dict, n_trajectories=20, levels=6, seed=0) -> pd.DataFrame:
    """Morris Elementary Effects 参数筛选。

    返回：
        mu_star: 平均绝对效应，越大越重要
        sigma: 效应标准差，越大代表非线性或交互越强

    这是“先找关键参数”的好工具，适合比赛早期快速决定敏感性分析重点。
    """
    rng = np.random.default_rng(seed)
    names = list(bounds)
    d = len(names)
    delta = 1.0 / (levels - 1)
    effects = {name: [] for name in names}

    for _ in range(n_trajectories):
        x = rng.integers(0, levels - 1, size=d) / (levels - 1)
        order = rng.permutation(d)
        params = _scale_unit_samples(x[None, :], names, bounds)[0]
        y = float(model(params))

        for j in order:
            x2 = x.copy()
            step = delta if x2[j] + delta <= 1.0 else -delta
            x2[j] += step
            params2 = _scale_unit_samples(x2[None, :], names, bounds)[0]
            y2 = float(model(params2))
            lo, hi = bounds[names[j]]
            # 转为“每实际单位参数变化导致的输出变化”，便于不同量纲比较。
            effects[names[j]].append((y2 - y) / (step * (hi - lo)))
            x, y = x2, y2

    rows = []
    for name in names:
        ee = np.asarray(effects[name], dtype=float)
        rows.append(
            {
                "parameter": name,
                "mu": float(np.mean(ee)),
                "mu_star": float(np.mean(np.abs(ee))),
                "sigma": float(np.std(ee, ddof=1)) if len(ee) > 1 else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values("mu_star", ascending=False).reset_index(drop=True)


def sobol_first_total(model, bounds: dict, n=1024, seed=0) -> pd.DataFrame:
    """Saltelli/Jansen 风格的一阶与总效应 Sobol 近似。

    只实现最常用的一阶 S1 和总效应 ST：
        S1_i: 单独参数 i 对输出方差的贡献
        ST_i: 参数 i 及其交互项对输出方差的总贡献

    注意：
        这是轻量实现，适合赛时快速分析和论文说明；正式科研建议用 SALib 复核。
    """
    rng = np.random.default_rng(seed)
    names = list(bounds)
    d = len(names)
    A = rng.random((n, d))
    B = rng.random((n, d))

    def eval_unit(U):
        params = _scale_unit_samples(U, names, bounds)
        return np.asarray([float(model(p)) for p in params])

    YA = eval_unit(A)
    YB = eval_unit(B)
    var_y = float(np.var(np.r_[YA, YB], ddof=1))
    if var_y <= 1e-15:
        return pd.DataFrame({"parameter": names, "S1": 0.0, "ST": 0.0})

    rows = []
    for j, name in enumerate(names):
        ABj = A.copy()
        ABj[:, j] = B[:, j]
        YABj = eval_unit(ABj)

        # Saltelli 2010 first-order estimator and Jansen total-order estimator.
        s1 = np.mean(YB * (YABj - YA)) / var_y
        st = 0.5 * np.mean((YA - YABj) ** 2) / var_y
        rows.append({"parameter": name, "S1": float(s1), "ST": float(st)})
    return pd.DataFrame(rows).sort_values("ST", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    # 示例：输出主要受 x1 与 x2 影响，x3 基本不重要。
    bounds = {"x1": (-1, 1), "x2": (0, 2), "x3": (10, 20)}

    def model(p):
        return 2.0 * p["x1"] + 0.8 * p["x2"] ** 2 + 0.02 * p["x3"]

    print("LHS samples:")
    print(latin_hypercube(bounds, 5, seed=1).round(3).to_string(index=False))
    print("\nMorris screening:")
    print(morris_screening(model, bounds, n_trajectories=20, seed=2).round(4).to_string(index=False))
    print("\nSobol approximation:")
    print(sobol_first_total(model, bounds, n=512, seed=3).round(4).to_string(index=False))
