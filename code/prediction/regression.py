"""多元线性回归模板（statsmodels）：带完整统计报告。

适用：分析自变量对因变量的影响、做可解释的预测。
statsmodels 的 summary() 直接给 R²、系数、p 值，写论文非常好用。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def ols_fit(df: pd.DataFrame, y_col: str, x_cols: list[str]):
    """普通最小二乘回归。返回拟合后的 statsmodels 结果对象。

    用法：
        model = ols_fit(df, "y", ["x1", "x2"])
        print(model.summary())        # 完整统计报告
        pred = model.predict(sm.add_constant(new_X))
    """
    X = sm.add_constant(df[x_cols])   # 加截距项
    y = df[y_col]
    model = sm.OLS(y, X).fit()
    return model


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    n = 100
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(5, 2, n)
    y = 3 + 2 * x1 - 1.5 * x2 + rng.normal(0, 0.5, n)
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    model = ols_fit(df, "y", ["x1", "x2"])
    print(model.summary())
    print("\n系数:", dict(zip(["const", "x1", "x2"], np.round(model.params.values, 3))))
    print(f"R² = {model.rsquared:.4f}")
