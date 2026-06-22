"""智能优化算法：模拟退火 SA / 遗传算法 GA / 粒子群 PSO（纯 numpy 实现）。

适用：B 题大规模/非凸优化——当 scipy.optimize、规划求解器搞不定时。
三个函数统一接口：最小化 f(x)，x 在 bounds 给定的盒约束内。
要最大化就把目标取负。
"""
from __future__ import annotations

import numpy as np


def _clip(x, lo, hi):
    return np.minimum(np.maximum(x, lo), hi)


def simulated_annealing(f, bounds, n_iter=5000, T0=10.0, cooling=0.995, seed=0) -> dict:
    """模拟退火。bounds: [(lo,hi), ...]。返回 {x, fx, history}。"""
    rng = np.random.default_rng(seed)
    lo, hi = np.array([b[0] for b in bounds]), np.array([b[1] for b in bounds])
    x = lo + rng.random(len(bounds)) * (hi - lo)
    fx = f(x)
    best_x, best_fx = x.copy(), fx
    T, history = T0, [fx]
    step = (hi - lo) * 0.1
    for _ in range(n_iter):
        x_new = _clip(x + rng.normal(0, 1, len(bounds)) * step, lo, hi)
        fx_new = f(x_new)
        if fx_new < fx or rng.random() < np.exp(-(fx_new - fx) / max(T, 1e-12)):
            x, fx = x_new, fx_new
            if fx < best_fx:
                best_x, best_fx = x.copy(), fx
        T *= cooling
        history.append(best_fx)
    return {"x": best_x, "fx": best_fx, "history": history}


def genetic_algorithm(f, bounds, pop_size=60, n_gen=200, mut_rate=0.2, seed=0) -> dict:
    """实数编码遗传算法：锦标赛选择 + 算术交叉 + 高斯变异 + 精英保留。"""
    rng = np.random.default_rng(seed)
    lo, hi = np.array([b[0] for b in bounds]), np.array([b[1] for b in bounds])
    dim = len(bounds)
    pop = lo + rng.random((pop_size, dim)) * (hi - lo)
    fit = np.array([f(ind) for ind in pop])
    history = [fit.min()]
    for _ in range(n_gen):
        new_pop = [pop[fit.argmin()].copy()]  # 精英
        while len(new_pop) < pop_size:
            # 锦标赛选两个父代
            i, j = rng.integers(0, pop_size, 2)
            p1 = pop[i] if fit[i] < fit[j] else pop[j]
            i, j = rng.integers(0, pop_size, 2)
            p2 = pop[i] if fit[i] < fit[j] else pop[j]
            # 算术交叉
            a = rng.random()
            child = a * p1 + (1 - a) * p2
            # 高斯变异
            if rng.random() < mut_rate:
                child = child + rng.normal(0, 1, dim) * (hi - lo) * 0.1
            new_pop.append(_clip(child, lo, hi))
        pop = np.array(new_pop)
        fit = np.array([f(ind) for ind in pop])
        history.append(fit.min())
    best = fit.argmin()
    return {"x": pop[best], "fx": fit[best], "history": history}


def particle_swarm(f, bounds, n_particles=40, n_iter=200, w=0.7, c1=1.5, c2=1.5, seed=0) -> dict:
    """粒子群优化 PSO。"""
    rng = np.random.default_rng(seed)
    lo, hi = np.array([b[0] for b in bounds]), np.array([b[1] for b in bounds])
    dim = len(bounds)
    X = lo + rng.random((n_particles, dim)) * (hi - lo)
    V = rng.normal(0, 1, (n_particles, dim)) * (hi - lo) * 0.1
    pbest, pbest_f = X.copy(), np.array([f(x) for x in X])
    g = pbest_f.argmin()
    gbest, gbest_f = pbest[g].copy(), pbest_f[g]
    history = [gbest_f]
    for _ in range(n_iter):
        r1, r2 = rng.random((n_particles, dim)), rng.random((n_particles, dim))
        V = w * V + c1 * r1 * (pbest - X) + c2 * r2 * (gbest - X)
        X = _clip(X + V, lo, hi)
        fx = np.array([f(x) for x in X])
        better = fx < pbest_f
        pbest[better], pbest_f[better] = X[better], fx[better]
        g = pbest_f.argmin()
        if pbest_f[g] < gbest_f:
            gbest, gbest_f = pbest[g].copy(), pbest_f[g]
        history.append(gbest_f)
    return {"x": gbest, "fx": gbest_f, "history": history}


if __name__ == "__main__":
    # 测试函数：Rastrigin（多峰、全局最优在原点 f=0），2 维
    def rastrigin(x):
        return 10 * len(x) + sum(xi ** 2 - 10 * np.cos(2 * np.pi * xi) for xi in x)

    bounds = [(-5.12, 5.12), (-5.12, 5.12)]
    for name, algo in [("模拟退火 SA", simulated_annealing),
                       ("遗传算法 GA", genetic_algorithm),
                       ("粒子群 PSO", particle_swarm)]:
        res = algo(rastrigin, bounds)
        print(f"{name}: x≈{np.round(res['x'], 3)}, f={res['fx']:.4f} (理论最优 0)")
