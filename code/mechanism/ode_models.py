"""微分方程 / 机理建模：常微分方程数值解 + 参数拟合 + 符号解。

适用：A 题机理建模、传播/增长/物理过程（SIR、Logistic、阻尼振动等）。
核心是 scipy.integrate.solve_ivp 数值求解；含「把模型参数拟合到实测数据」
这一数模高频需求，以及 sympy 解析解（可选）。
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares


def solve_ode(rhs, y0, t_span, t_eval=None, args=(), method="RK45") -> dict:
    """通用 ODE 求解器封装。

    rhs(t, y, *args): 返回 dy/dt 的函数（y 可为向量，解高阶方程时先降阶为一阶组）。
    y0: 初值（标量或向量）。t_span: (t0, t1)。t_eval: 想要输出的时间点。
    返回 dict: {t, y}（y 形状为 [状态维度, 时间点数]）。
    """
    if t_eval is None:
        t_eval = np.linspace(t_span[0], t_span[1], 200)
    sol = solve_ivp(rhs, t_span, np.atleast_1d(y0), t_eval=t_eval,
                    args=args, method=method, rtol=1e-8, atol=1e-10)
    return {"t": sol.t, "y": sol.y, "success": sol.success}


def sir_model(beta, gamma, S0, I0, R0=0.0, days=160) -> dict:
    """SIR 传染病模型。beta 传染率、gamma 恢复率；返回 S/I/R 时间序列。

    dS/dt=-beta*S*I/N, dI/dt=beta*S*I/N-gamma*I, dR/dt=gamma*I
    """
    N = S0 + I0 + R0

    def rhs(t, y):
        S, I, R = y
        dS = -beta * S * I / N
        dI = beta * S * I / N - gamma * I
        dR = gamma * I
        return [dS, dI, dR]

    res = solve_ode(rhs, [S0, I0, R0], (0, days), np.arange(0, days + 1))
    S, I, R = res["y"]
    return {"t": res["t"], "S": S, "I": I, "R": R, "R0_basic": beta / gamma}


def logistic_growth(r, K, x0, t_end=50) -> dict:
    """Logistic 阻滞增长：dx/dt = r*x*(1 - x/K)。r 增长率、K 环境容量。"""
    res = solve_ode(lambda t, x: r * x * (1 - x / K), [x0], (0, t_end))
    return {"t": res["t"], "x": res["y"][0]}


def fit_ode_params(rhs_factory, y0, t_data, y_data, p0, bounds=(-np.inf, np.inf)) -> dict:
    """把 ODE 模型参数拟合到实测数据（最小二乘）。

    rhs_factory(params): 返回一个 rhs(t, y) 函数。
    y0: 初值。t_data/y_data: 实测时间与观测（y_data 为被观测的那一维状态）。
    p0: 参数初值猜测。返回 dict: {params, residual_norm, success}。
    """
    t_data = np.asarray(t_data, dtype=float)
    y_data = np.asarray(y_data, dtype=float)

    def residuals(params):
        sol = solve_ivp(rhs_factory(params), (t_data[0], t_data[-1]),
                        np.atleast_1d(y0), t_eval=t_data, rtol=1e-8, atol=1e-10)
        if not sol.success or sol.y.shape[1] != len(t_data):
            return np.full_like(y_data, 1e6)
        return sol.y[0] - y_data

    res = least_squares(residuals, p0, bounds=bounds)
    return {"params": res.x, "residual_norm": float(np.linalg.norm(res.fun)),
            "success": res.success}


def symbolic_solve_demo():
    """sympy 解析解示例（可选）：解 y' + 2y = 0, y(0)=1 -> y = exp(-2t)。"""
    try:
        import sympy as sp
    except ImportError:
        return "未安装 sympy，跳过符号解（pip install sympy）"
    t = sp.symbols("t")
    y = sp.Function("y")
    sol = sp.dsolve(sp.Eq(y(t).diff(t) + 2 * y(t), 0), y(t),
                    ics={y(0): 1})
    return sol


if __name__ == "__main__":
    # 1) SIR：1万人，初始10感染，beta=0.3, gamma=0.1
    sir = sir_model(beta=0.3, gamma=0.1, S0=9990, I0=10)
    print(f"SIR 基本再生数 R0 = {sir['R0_basic']:.2f}, 感染峰值 = {sir['I'].max():.0f} 人")

    # 2) Logistic：拟合参数到带噪声的数据
    true = logistic_growth(r=0.4, K=1000, x0=20, t_end=30)
    t_obs = np.linspace(0, 30, 15)
    y_obs = np.interp(t_obs, true["t"], true["x"]) * (1 + 0.03 * np.random.default_rng(0).standard_normal(15))
    fit = fit_ode_params(
        lambda p: (lambda t, x: p[0] * x * (1 - x / p[1])),
        y0=20, t_data=t_obs, y_data=y_obs, p0=[0.2, 800], bounds=([0, 0], [2, 5000]))
    print(f"Logistic 参数拟合: r={fit['params'][0]:.3f}, K={fit['params'][1]:.0f} (真值 0.4/1000)")

    # 3) 符号解
    print("符号解 y'+2y=0:", symbolic_solve_demo())
