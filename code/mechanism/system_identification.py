"""数据驱动动力学识别：轻量 SINDy 模板。

参考思想：
    - PySINDy: Sparse Identification of Nonlinear Dynamical Systems
    - 通过观测状态 x(t)，识别 dx/dt = f(x) 的稀疏可解释方程

适合：
    - 物理过程只有观测数据，但题目要求给出机理解释
    - 先用数据发现可能的动力学项，再回到物理意义筛选
    - 与 `ode_models.py` 搭配：识别方程 -> 数值仿真 -> 参数解释

注意：
    本文件是轻量教学/赛时模板，不替代完整 PySINDy。
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso, LinearRegression
from sklearn.preprocessing import PolynomialFeatures


def finite_difference(X, t) -> np.ndarray:
    """中心差分估计 dX/dt。"""
    X = np.asarray(X, dtype=float)
    t = np.asarray(t, dtype=float)
    return np.gradient(X, t, axis=0)


def polynomial_library(X, degree=2, include_bias=True) -> tuple[np.ndarray, list[str]]:
    """构造多项式候选函数库。"""
    X = np.asarray(X, dtype=float)
    n_features = X.shape[1]
    names = [f"x{i+1}" for i in range(n_features)]
    poly = PolynomialFeatures(degree=degree, include_bias=include_bias)
    Theta = poly.fit_transform(X)

    try:
        feature_names = list(poly.get_feature_names_out(names))
    except AttributeError:
        feature_names = list(poly.get_feature_names(names))
    return Theta, feature_names


def sindy_fit(X, t, degree=2, alpha=1e-3, threshold=1e-6) -> dict:
    """用 Lasso 做稀疏动力学识别。

    返回：
        coef: shape = [状态维度, 候选项数量]
        equations: 可读方程字符串
    """
    X = np.asarray(X, dtype=float)
    dXdt = finite_difference(X, t)
    Theta, names = polynomial_library(X, degree=degree, include_bias=True)

    coefs = []
    for j in range(X.shape[1]):
        model = Lasso(alpha=alpha, fit_intercept=False, max_iter=20000)
        model.fit(Theta, dXdt[:, j])
        c = model.coef_
        c[np.abs(c) < threshold] = 0.0
        # 对筛选出的项再做一次普通最小二乘，减小 Lasso 收缩偏差。
        active = np.abs(c) > 0
        if active.any():
            lr = LinearRegression(fit_intercept=False)
            lr.fit(Theta[:, active], dXdt[:, j])
            c2 = np.zeros_like(c)
            c2[active] = lr.coef_
            c = c2
        coefs.append(c)
    coefs = np.asarray(coefs)
    return {"coef": coefs, "feature_names": names, "equations": format_equations(coefs, names)}


def format_equations(coefs, feature_names, state_names=None, precision=4) -> list[str]:
    """把系数矩阵转成可读方程。"""
    coefs = np.asarray(coefs)
    if state_names is None:
        state_names = [f"x{i+1}" for i in range(coefs.shape[0])]
    equations = []
    for i, row in enumerate(coefs):
        terms = []
        for c, name in zip(row, feature_names):
            if abs(c) > 1e-12:
                terms.append(f"{c:.{precision}g}*{name}")
        rhs = " + ".join(terms) if terms else "0"
        equations.append(f"d{state_names[i]}/dt = {rhs}")
    return equations


def simulate_identified_model(x0, t, coef, feature_names, degree=2) -> np.ndarray:
    """用识别出的多项式模型做欧拉仿真，便于快速 sanity check。"""
    x0 = np.asarray(x0, dtype=float)
    t = np.asarray(t, dtype=float)
    X = np.zeros((len(t), len(x0)))
    X[0] = x0
    for k in range(len(t) - 1):
        Theta, _ = polynomial_library(X[k : k + 1], degree=degree, include_bias=True)
        dx = (coef @ Theta[0]).ravel()
        X[k + 1] = X[k] + (t[k + 1] - t[k]) * dx
    return X


def candidate_interaction_terms(variable_names, max_degree=2) -> pd.DataFrame:
    """列出候选交互项，帮助论文解释“函数库里包含哪些可能机理”。"""
    rows = []
    for degree in range(1, max_degree + 1):
        for combo in itertools.combinations_with_replacement(variable_names, degree):
            rows.append({"degree": degree, "term": "*".join(combo)})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    # 示例系统：x'=-2x, y'=y。看能否从数据识别出来。
    t = np.linspace(0, 1.5, 160)
    x = 3 * np.exp(-2 * t)
    y = 0.5 * np.exp(t)
    X = np.column_stack([x, y])

    res = sindy_fit(X, t, degree=1, alpha=1e-5)
    print("\n".join(res["equations"]))
    X_sim = simulate_identified_model(X[0], t, res["coef"], res["feature_names"], degree=1)
    rmse = np.sqrt(np.mean((X - X_sim) ** 2))
    print(f"识别模型欧拉仿真 RMSE≈{rmse:.5f}")
