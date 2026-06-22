"""机器学习增强预测：随机森林 / XGBoost（C 题大数据预测与特征重要性）。

适用：C 题数据量大、关系非线性、要预测或分类并解释「哪些特征重要」。
统一封装：训练 + 交叉验证评分 + 特征重要性。XGBoost 未装时自动回退到
sklearn 的梯度提升，保证赛时一定能跑。
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import (RandomForestRegressor, RandomForestClassifier,
                              GradientBoostingRegressor)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import r2_score, accuracy_score


def train_rf(X, y, task="reg", n_estimators=300, seed=0) -> dict:
    """随机森林训练 + 留出测试 + 5 折交叉验证。

    task: "reg" 回归 / "clf" 分类。
    返回 dict: {model, score(测试集), cv_mean, cv_std, importance(各特征重要性)}。
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=seed)
    if task == "reg":
        model = RandomForestRegressor(n_estimators=n_estimators, random_state=seed)
        scoring, metric = "r2", r2_score
    else:
        model = RandomForestClassifier(n_estimators=n_estimators, random_state=seed)
        scoring, metric = "accuracy", accuracy_score
    model.fit(Xtr, ytr)
    score = metric(yte, model.predict(Xte))
    cv = cross_val_score(model, X, y, cv=5, scoring=scoring)
    return {"model": model, "score": score, "cv_mean": cv.mean(),
            "cv_std": cv.std(), "importance": model.feature_importances_}


def train_xgb(X, y, seed=0) -> dict:
    """XGBoost 回归（未安装则回退到 sklearn GradientBoosting）。"""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=seed)
    try:
        from xgboost import XGBRegressor
        model = XGBRegressor(n_estimators=300, max_depth=4,
                             learning_rate=0.1, random_state=seed)
        backend = "xgboost"
    except ImportError:
        model = GradientBoostingRegressor(n_estimators=300, max_depth=4,
                                          learning_rate=0.1, random_state=seed)
        backend = "sklearn-GBDT(回退)"
    model.fit(Xtr, ytr)
    return {"model": model, "backend": backend,
            "score": r2_score(yte, model.predict(Xte)),
            "importance": model.feature_importances_}


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    n = 400
    X = rng.normal(0, 1, (n, 5))
    # 真实关系：只有前两个特征有用 + 噪声
    y = 3 * X[:, 0] + 2 * X[:, 1] ** 2 + 0.5 * rng.standard_normal(n)

    rf = train_rf(X, y, task="reg")
    print(f"随机森林: 测试 R^2={rf['score']:.3f}, 5折CV={rf['cv_mean']:.3f}±{rf['cv_std']:.3f}")
    print("  特征重要性 =", np.round(rf["importance"], 3))

    xgb = train_xgb(X, y)
    print(f"{xgb['backend']}: 测试 R^2={xgb['score']:.3f}")
    print("  特征重要性 =", np.round(xgb["importance"], 3))
