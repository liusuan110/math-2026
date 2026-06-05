"""线性规划 / 整数规划模板（scipy.optimize）。

适用：B 题运筹优化——在线性约束下最大化/最小化线性目标。
用 scipy 自带的 linprog / milp，**无需外部求解器二进制**，装了 scipy 就能跑
（pulp 自带的 CBC 在 Apple Silicon 上有架构问题，故这里用 scipy）。

约定：scipy 默认做**最小化**。要最大化目标，把目标系数取负即可。
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds


def solve_demo_production(integer=True):
    """示例：生产计划问题。

    某厂生产 A、B 两种产品，单位利润 3、5。
    约束：原料(2A + 4B <= 80)、工时(3A + 2B <= 60)，产量非负。
    目标：最大化总利润 = 3A + 5B。

    integer=True 走整数规划(milp)，False 走线性规划(linprog)。
    """
    # 目标：最大化 3A+5B  ->  最小化 -(3A+5B)
    c = np.array([-3.0, -5.0])
    # 约束矩阵 A_ub @ x <= b_ub
    A = np.array([[2.0, 4.0],
                  [3.0, 2.0]])
    b = np.array([80.0, 60.0])

    if integer:
        constraints = LinearConstraint(A, ub=b)        # A x <= b
        bounds = Bounds(lb=0, ub=np.inf)
        integrality = np.ones(2)                        # 两个变量都取整
        res = milp(c, constraints=constraints, integrality=integrality, bounds=bounds)
        x = res.x
    else:
        res = linprog(c, A_ub=A, b_ub=b, bounds=[(0, None), (0, None)])
        x = res.x

    return {
        "success": res.success,
        "A": x[0],
        "B": x[1],
        "max_profit": -res.fun,    # 还原为最大化目标值
    }


if __name__ == "__main__":
    res = solve_demo_production(integer=True)
    print("求解成功:", res["success"])
    print(f"最优产量: A={res['A']:.0f}, B={res['B']:.0f}")
    print(f"最大利润: {res['max_profit']:.1f}")
