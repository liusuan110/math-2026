"""物理参数反演与残差诊断模板。

适用题型：
    - 2025B 碳化硅外延层厚度：物理公式 -> 预测曲线 -> 最小二乘反演参数
    - 光学/声学/电磁/热学实验：由观测数据拟合模型参数
    - 任意“给定参数能仿真，要求反推出参数”的 A/B 题

核心功能：
    - 普通/加权最小二乘
    - 多初值反演
    - 参数协方差与置信区间近似
    - 残差诊断
    - 一维信号 FFT 主频估计（反演题常用初值来源）
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.signal import find_peaks


def weighted_residuals(model, x_data, y_data, params, weights=None):
    """加权残差：weights 越大，该观测点越重要。"""
    x_data = np.asarray(x_data, dtype=float)
    y_data = np.asarray(y_data, dtype=float)
    pred = np.asarray(model(x_data, params), dtype=float)
    r = pred - y_data
    if weights is not None:
        r = r * np.sqrt(np.asarray(weights, dtype=float))
    return r


def fit_least_squares(model, x_data, y_data, p0, bounds=(-np.inf, np.inf), weights=None) -> dict:
    """最小二乘参数反演。model(x_data, params) -> y_pred。"""
    res = least_squares(
        lambda p: weighted_residuals(model, x_data, y_data, p, weights),
        x0=np.asarray(p0, dtype=float),
        bounds=bounds,
        jac="2-point",
    )
    return {
        "params": res.x,
        "cost": float(res.cost),
        "residuals": weighted_residuals(model, x_data, y_data, res.x, weights=None),
        "jac": res.jac,
        "success": bool(res.success),
        "message": str(res.message),
    }


def multistart_fit(model, x_data, y_data, bounds, n_starts=30, seed=0, weights=None) -> dict:
    """多初值最小二乘，避免陷入局部最优。"""
    rng = np.random.default_rng(seed)
    lo, hi = np.asarray(bounds[0], dtype=float), np.asarray(bounds[1], dtype=float)
    results = []
    for _ in range(n_starts):
        p0 = lo + rng.random(len(lo)) * (hi - lo)
        fit = fit_least_squares(model, x_data, y_data, p0, bounds=bounds, weights=weights)
        results.append(fit)
    results.sort(key=lambda r: r["cost"])
    return {"best": results[0], "all": results}


def parameter_confidence_interval(jac, residuals, alpha=0.05) -> pd.DataFrame:
    """由雅可比矩阵近似参数标准误和 95% 置信区间。

    这是非线性最小二乘的局部线性近似，赛时可用于“参数可信度”讨论。
    """
    jac = np.asarray(jac, dtype=float)
    residuals = np.asarray(residuals, dtype=float)
    n, p = jac.shape
    dof = max(1, n - p)
    sigma2 = float(np.sum(residuals**2) / dof)
    cov = sigma2 * np.linalg.pinv(jac.T @ jac)
    se = np.sqrt(np.maximum(np.diag(cov), 0.0))

    try:
        from scipy.stats import t

        q = float(t.ppf(1 - alpha / 2, dof))
    except Exception:
        q = 1.96
    return pd.DataFrame({"std_error": se, "half_width": q * se})


def residual_diagnostics(residuals) -> dict:
    """残差诊断基础指标。"""
    r = np.asarray(residuals, dtype=float)
    rmse = float(np.sqrt(np.mean(r**2)))
    mae = float(np.mean(np.abs(r)))
    bias = float(np.mean(r))
    return {"rmse": rmse, "mae": mae, "bias": bias, "max_abs": float(np.max(np.abs(r)))}


def dominant_frequencies(x, y, min_prominence_ratio=0.05, top_k=5) -> pd.DataFrame:
    """一维信号主频估计，用于周期/干涉/波动类反演初值。

    x 应近似等间距；返回频率、幅值和周期。
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    dx = float(np.median(np.diff(x)))
    y0 = y - np.mean(y)
    freq = np.fft.rfftfreq(len(y0), d=dx)
    amp = np.abs(np.fft.rfft(y0))
    if len(amp) > 0:
        amp[0] = 0
    peaks, props = find_peaks(amp, prominence=max(amp.max() * min_prominence_ratio, 1e-12))
    rows = [{"frequency": freq[i], "amplitude": amp[i], "period": np.inf if freq[i] == 0 else 1 / freq[i]} for i in peaks]
    return pd.DataFrame(rows).sort_values("amplitude", ascending=False).head(top_k).reset_index(drop=True)


if __name__ == "__main__":
    rng = np.random.default_rng(2)

    # 示例：y = A * exp(-k x) + c，反演 A/k/c。
    true_params = np.array([5.0, 0.7, 0.4])
    x = np.linspace(0, 5, 80)

    def model(x_data, p):
        A, k, c = p
        return A * np.exp(-k * x_data) + c

    y = model(x, true_params) + rng.normal(0, 0.08, size=len(x))
    fit = multistart_fit(model, x, y, bounds=([0, 0, -2], [10, 3, 2]), n_starts=12, seed=1)["best"]
    diag = residual_diagnostics(fit["residuals"])
    ci = parameter_confidence_interval(fit["jac"], fit["residuals"])
    print("反演参数:", np.round(fit["params"], 4), "真值:", true_params)
    print("残差诊断:", {k: round(v, 5) for k, v in diag.items()})
    print("参数标准误:", np.round(ci["std_error"].to_numpy(), 5))

    # FFT 主频示例。
    y_wave = np.sin(2 * np.pi * 3.0 * x) + 0.25 * rng.normal(size=len(x))
    print("主频估计:\n", dominant_frequencies(x, y_wave, top_k=2).round(4).to_string(index=False))
