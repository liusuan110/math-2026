"""非线性规划模板（scipy.optimize.minimize）。

适用：目标或约束含非线性项（平方、乘积、开方等）。
注意：结果依赖初值 x0，建议多个初值尝试取最优（避免局部最优）。
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize


def solve_demo():
    """示例：min f(x,y) = (x-1)^2 + (y-2.5)^2
    约束：x - 2y + 2 >= 0, -x - 2y + 6 >= 0, x>=0, y>=0
    """
    def objective(v):
        x, y = v
        return (x - 1) ** 2 + (y - 2.5) ** 2

    # 不等式约束写成 g(x) >= 0 形式
    constraints = [
        {"type": "ineq", "fun": lambda v: v[0] - 2 * v[1] + 2},
        {"type": "ineq", "fun": lambda v: -v[0] - 2 * v[1] + 6},
    ]
    bounds = [(0, None), (0, None)]
    x0 = [0.0, 0.0]

    res = minimize(objective, x0, method="SLSQP",
                   bounds=bounds, constraints=constraints)
    return {"x": res.x, "fmin": res.fun, "success": res.success}


def solve_multistart(objective, bounds, constraints=None, n_starts=20, seed=0):
    """多初值随机重启，缓解非凸问题陷入局部最优。返回最好的解。"""
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(n_starts):
        x0 = [rng.uniform(lo if lo is not None else -10,
                          hi if hi is not None else 10) for lo, hi in bounds]
        r = minimize(objective, x0, method="SLSQP",
                     bounds=bounds, constraints=constraints or [])
        if r.success and (best is None or r.fun < best.fun):
            best = r
    return best


if __name__ == "__main__":
    res = solve_demo()
    print(f"最优解: x={res['x'][0]:.4f}, y={res['x'][1]:.4f}")
    print(f"目标最小值: {res['fmin']:.4f}, 成功: {res['success']}")
