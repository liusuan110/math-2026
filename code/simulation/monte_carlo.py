"""蒙特卡洛模拟：含不确定性、难解析时靠随机抽样估计。

三类高频用法：定积分估计、不确定性传播（输入有分布 -> 输出分布与置信区间）、
排队/库存等随机系统仿真的骨架。
"""
from __future__ import annotations

import numpy as np


def estimate_integral(f, bounds, n=100000, seed=0) -> dict:
    """蒙特卡洛估计多重定积分 ∫f dx。bounds: [(lo,hi), ...] 每维积分区间。

    返回 {estimate, std_error}。
    """
    rng = np.random.default_rng(seed)
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])
    vol = np.prod(hi - lo)
    samples = lo + rng.random((n, len(bounds))) * (hi - lo)
    vals = np.array([f(x) for x in samples])
    estimate = vol * vals.mean()
    std_error = vol * vals.std(ddof=1) / np.sqrt(n)
    return {"estimate": estimate, "std_error": std_error}


def propagate_uncertainty(model, samplers: dict, n=10000, seed=0) -> dict:
    """不确定性传播：输入参数各服从某分布，输出的均值/标准差/95%置信区间。

    model(params: dict) -> float。
    samplers: {参数名: 取一个 rng 返回样本数组的函数}，见 __main__ 示例。
    返回 {mean, std, ci95, samples}。
    """
    rng = np.random.default_rng(seed)
    cols = {name: fn(rng, n) for name, fn in samplers.items()}
    out = np.array([model({k: cols[k][i] for k in cols}) for i in range(n)])
    return {"mean": out.mean(), "std": out.std(ddof=1),
            "ci95": (np.percentile(out, 2.5), np.percentile(out, 97.5)),
            "samples": out}


def estimate_pi(n=1000000, seed=0) -> float:
    """经典示例：投点法估计 π（自检蒙特卡洛是否正常）。"""
    rng = np.random.default_rng(seed)
    pts = rng.random((n, 2))
    inside = ((pts ** 2).sum(axis=1) <= 1).sum()
    return 4 * inside / n


if __name__ == "__main__":
    print(f"估计 π ≈ {estimate_pi():.4f}")

    # 定积分：∫_0^1 x^2 dx = 1/3
    res = estimate_integral(lambda x: x[0] ** 2, [(0, 1)])
    print(f"积分 x^2 dx ≈ {res['estimate']:.4f} ± {res['std_error']:.4f} (真值 0.3333)")

    # 不确定性传播：利润=(售价-成本)*销量，三者都有波动
    def profit(p):
        return (p["price"] - p["cost"]) * p["demand"]

    samplers = {
        "price": lambda rng, n: rng.normal(20, 1, n),
        "cost": lambda rng, n: rng.normal(8, 0.5, n),
        "demand": lambda rng, n: rng.normal(400, 50, n),
    }
    u = propagate_uncertainty(profit, samplers)
    print(f"利润: 均值 {u['mean']:.0f}, 标准差 {u['std']:.0f}, "
          f"95%置信区间 [{u['ci95'][0]:.0f}, {u['ci95'][1]:.0f}]")
