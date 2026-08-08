import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.datasets import fetch_california_housing
from sklearn.ensemble import RandomForestRegressor
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer, SimpleImputer
from sklearn.kernel_approximation import Nystroem
from sklearn.linear_model import BayesianRidge, Ridge
from sklearn.model_selection import cross_val_score
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler

# -- 图片预设，需要 plt, fm, cycler 库
import matplotlib.font_manager as fm
from cycler import cycler
import os

font_path = "../../utils/fonts/SourceHanSerifCN-Regular.otf"
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rcParams['font.sans-serif'] = [font_name]
else:
    fallback_fonts = ['STZhongsong', 'SimSun', 'SimHei', 'Microsoft YaHei']
    plt.rcParams['font.sans-serif'] = fallback_fonts

plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'  # 保存后自动裁剪白边
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.prop_cycle'] = cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
plt.rcParams['axes.unicode_minus'] = False
# -- 图片预设


def load_and_preprocess_data(subsample_step=10):
    X_full, y_full = fetch_california_housing(return_X_y=True)
    X_full = X_full[::subsample_step]
    y_full = y_full[::subsample_step]
    print(f"数据加载完成，维度: {X_full.shape}")
    return X_full, y_full


def create_missing_data(X_full, random_state=0):
    rng = np.random.RandomState(random_state)
    n_samples, n_features = X_full.shape

    X_missing = X_full.copy()
    missing_samples = np.arange(n_samples)
    missing_features = rng.choice(n_features, n_samples, replace=True)

    X_missing[missing_samples, missing_features] = np.nan
    return X_missing


def evaluate_pipeline_score(X, y, imputer=None, n_splits=5):
    """
    评估一个包含数据缩放、填充和回归的 Pipeline 的性能。

    Args:
        X (np.ndarray): 特征矩阵。
        y (np.ndarray): 目标向量。
        imputer (object, optional): 用于填充缺失值的 scikit-learn imputer 对象。Defaults to None.
        n_splits (int): 交叉验证的折数。

    Returns:
        np.ndarray: 交叉验证的分数数组 (负均方误差)。
    """
    if imputer is None:
        estimator = make_pipeline(RobustScaler(), BayesianRidge())
    else:
        estimator = make_pipeline(RobustScaler(), imputer, BayesianRidge())

    return cross_val_score(
        estimator, X, y, scoring="neg_mean_squared_error", cv=n_splits
    )


def run_all_imputation_evaluations(X_full, y_full, X_missing, n_splits):
    """
    对所有不同的缺失值填充策略进行评估。

    Args:
        X_full (np.ndarray): 完整的特征矩阵。
        y_full (np.ndarray): 完整的目标向量。
        X_missing (np.ndarray): 包含缺失值的特征矩阵。
        n_splits (int): 交叉验证的折数。

    Returns:
        pd.DataFrame: 一个包含所有评估结果的多级索引 DataFrame。
    """
    score_full_data = pd.DataFrame(
        evaluate_pipeline_score(X_full, y_full, n_splits=n_splits),
        columns=["Full Data"],
    )

    # 2. 评估简单填充策略 (均值和中位数)
    score_simple_imputer = pd.DataFrame()
    for strategy in ("mean", "median"):
        print(f"  - 评估 SimpleImputer (strategy='{strategy}')...")
        imputer = SimpleImputer(strategy=strategy)
        score_simple_imputer[strategy] = evaluate_pipeline_score(
            X_missing, y_full, imputer, n_splits=n_splits
        )

    # 3. 评估迭代填充策略
    # 定义用于迭代填充的估算器及其参数
    named_estimators = [
        ("Bayesian Ridge", BayesianRidge()),
        ("Random Forest", RandomForestRegressor(n_estimators=5, max_depth=10, bootstrap=True, max_samples=0.5, n_jobs=2, random_state=0)),
        ("Nystroem + Ridge", make_pipeline(Nystroem(kernel="polynomial", degree=2, random_state=0), Ridge(alpha=1e4))),
        ("k-NN", KNeighborsRegressor(n_neighbors=10)),
    ]
    tolerances = (1e-3, 1e-1, 1e-1, 1e-2)

    score_iterative_imputer = pd.DataFrame()
    for (name, impute_estimator), tol in zip(named_estimators, tolerances):
        print(f"  - 评估 IterativeImputer (estimator='{name}')...")
        imputer = IterativeImputer(
            random_state=0, estimator=impute_estimator, max_iter=40, tol=tol
        )
        score_iterative_imputer[name] = evaluate_pipeline_score(
            X_missing, y_full, imputer, n_splits=n_splits
        )

    # 4. 合并所有分数
    scores = pd.concat(
        [score_full_data, score_simple_imputer, score_iterative_imputer],
        keys=["Original", "SimpleImputer", "IterativeImputer"],
        axis=1,
    )
    print("所有评估完成。")
    return scores


def plot_results(scores):
    fig, ax = plt.subplots(figsize=(13, 8))

    means = -scores.mean().sort_values()  # 转换为正MSE并排序
    errors = scores.std()

    # 确保 errors 和 means 的索引顺序一致
    errors = errors[means.index]

    means.plot.barh(xerr=errors, ax=ax, capsize=4)

    ax.set_title("不同缺失值填充方法在加州房价数据集上的性能对比", fontsize=16)
    ax.set_xlabel("均方误差 (MSE) - 值越小越好", fontsize=12)
    ax.set_ylabel("填充策略", fontsize=12)
    ax.set_yticklabels([" / ".join(label) for label in means.index.tolist()])
    ax.grid(axis='x', linestyle='--', alpha=0.6)

    plt.tight_layout(pad=1)
    plt.show()


def main():
    N_SPLITS = 5
    X_full, y_full = load_and_preprocess_data(subsample_step=10)
    X_missing = create_missing_data(X_full, random_state=0)
    scores = run_all_imputation_evaluations(X_full, y_full, X_missing, n_splits=N_SPLITS)
    print("\n评估分数 (负均方误差):")
    print(scores)
    plot_results(scores)


if __name__ == "__main__":
    main()
