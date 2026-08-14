"""物理 / 工程题常用全局优化流程。

当前 `heuristic.py` 已有 SA/GA/PSO 的纯 numpy 实现；本文件补充 scipy 的成熟全局优化器，
以及“粗搜索 -> 全局搜索 -> 局部精修 -> 多随机种子统计”的赛时流程。

适合：
    - 烟幕投放参数优化
    - 定日镜布局/角度优化
    - 多波束测线规划
    - 任意目标函数不光滑、约束复杂、局部最优多的问题
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import basinhopping, differential_evolution, dual_annealing, minimize


def penalty_objective(objective, constraints=(), penalty_weight=1e6):
    """把约束问题转为无约束罚函数问题。

    constraints 中每个函数 g(x) 应满足 g(x) >= 0。
    违反约束时加入 penalty_weight * violation^2。
    """

    def wrapped(x):
        x = np.asarray(x, dtype=float)
        val = float(objective(x))
        penalty = 0.0
        for g in constraints:
            gv = float(g(x))
            if gv < 0:
                penalty += gv * gv
        return val + penalty_weight * penalty

    return wrapped


def coarse_grid_search(objective, bounds, points_per_dim=8, top_k=5) -> pd.DataFrame:
    """低维问题粗网格搜索，用来找多初值和画响应面。

    注意：维度高时网格数量会爆炸，只建议 dim<=4。
    """
    grids = [np.linspace(lo, hi, points_per_dim) for lo, hi in bounds]
    rows = []
    for values in np.array(np.meshgrid(*grids)).T.reshape(-1, len(bounds)):
        rows.append({"x": values, "fx": float(objective(values))})
    df = pd.DataFrame(rows).sort_values("fx", ascending=True).reset_index(drop=True)
    return df.head(top_k)


def solve_differential_evolution(objective, bounds, seed=0, maxiter=300, polish=True) -> dict:
    """差分进化：物理题非凸连续参数优化的首选基线。"""
    res = differential_evolution(
        objective,
        bounds=bounds,
        seed=seed,
        maxiter=maxiter,
        polish=polish,
        updating="immediate",
        workers=1,
        tol=1e-7,
    )
    return {"x": res.x, "fx": float(res.fun), "success": bool(res.success), "message": str(res.message)}


def solve_dual_annealing(objective, bounds, seed=0, maxiter=500) -> dict:
    """dual_annealing：适合多峰、变量范围较宽的问题，作为 DE 的交叉验证。"""
    res = dual_annealing(objective, bounds=bounds, seed=seed, maxiter=maxiter)
    return {"x": res.x, "fx": float(res.fun), "success": bool(res.success), "message": str(res.message)}


def polish_local(objective, x0, bounds=None, method="Nelder-Mead") -> dict:
    """局部精修：全局算法找到候选解后，再做局部优化。"""
    if method.upper() == "SLSQP":
        res = minimize(objective, x0, method="SLSQP", bounds=bounds)
    else:
        res = minimize(objective, x0, method=method)
    return {"x": res.x, "fx": float(res.fun), "success": bool(res.success), "message": str(res.message)}


def solve_basinhopping(objective, x0, bounds=None, seed=0, niter=100) -> dict:
    """basinhopping：局部搜索 + 随机跳跃，适合局部最优多但维度不太高的问题。"""
    minimizer_kwargs = {"method": "SLSQP", "bounds": bounds} if bounds else {"method": "Nelder-Mead"}
    res = basinhopping(objective, x0, niter=niter, seed=seed, minimizer_kwargs=minimizer_kwargs)
    return {"x": res.x, "fx": float(res.fun), "success": bool(res.lowest_optimization_result.success)}


def repeated_global_runs(solver, objective, bounds, seeds=range(10), **kwargs) -> pd.DataFrame:
    """多随机种子重复优化，输出稳定性统计的原始表。

    论文里不要只报一次最优值；至少报多次运行最优/均值/标准差。
    """
    rows = []
    for seed in seeds:
        res = solver(objective, bounds, seed=seed, **kwargs)
        rows.append({"seed": seed, "fx": res["fx"], "x": np.asarray(res["x"]), "success": res.get("success", True)})
    return pd.DataFrame(rows).sort_values("fx", ascending=True).reset_index(drop=True)


def global_then_local(objective, bounds, seed=0, maxiter=200, local_method="Nelder-Mead") -> dict:
    """推荐赛时默认流程：差分进化全局搜索 -> 局部精修。"""
    global_res = solve_differential_evolution(objective, bounds, seed=seed, maxiter=maxiter, polish=False)
    local_res = polish_local(objective, global_res["x"], bounds=bounds, method=local_method)
    best = local_res if local_res["fx"] <= global_res["fx"] else global_res
    return {"x": best["x"], "fx": best["fx"], "global": global_res, "local": local_res}


if __name__ == "__main__":
    # Rastrigin 多峰函数：全局最优在 x=0, f=0。
    def rastrigin(x):
        x = np.asarray(x)
        return 10 * len(x) + np.sum(x**2 - 10 * np.cos(2 * np.pi * x))

    bounds = [(-5.12, 5.12), (-5.12, 5.12)]
    res = global_then_local(rastrigin, bounds, seed=3, maxiter=80)
    print("DE -> local:", np.round(res["x"], 4), round(res["fx"], 6))

    runs = repeated_global_runs(solve_differential_evolution, rastrigin, bounds, seeds=range(3), maxiter=60)
    print("多种子最优/均值/标准差:", round(runs["fx"].min(), 6), round(runs["fx"].mean(), 6), round(runs["fx"].std(), 6))
