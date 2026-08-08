import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# from sklearn.datasets import fetch_california_housing # 加州房价数据集
from sklearn.datasets import load_diabetes  # 糖尿病数据集
from sklearn.impute import SimpleImputer  # 填充缺失值的类
from sklearn.ensemble import RandomForestRegressor  # 随机森林回归
from sklearn.model_selection import cross_val_score  # 交叉验证

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


def load_and_prepare_data():
    dataset = load_diabetes()
    print("数据集维度:", dataset.data.shape)
    print("前5个目标值:", dataset.target[:5])
    return dataset.data, dataset.target


def create_missing_values(X_full, missing_rate=0.3, random_state=0):
    n_samples, n_features = X_full.shape
    rng = np.random.RandomState(random_state)

    n_missing_samples = int(np.floor(n_samples * n_features * missing_rate))

    missing_features = rng.randint(0, n_features, n_missing_samples)
    missing_samples = rng.randint(0, n_samples, n_missing_samples)

    X_missing = X_full.copy()
    X_missing[missing_samples, missing_features] = np.nan

    return pd.DataFrame(X_missing)


def impute_data(X_missing, Y_full):
    imputed_datasets = {}

    # 1. 均值填充
    imp_mean = SimpleImputer(missing_values=np.nan, strategy='mean')
    imputed_datasets["Mean Imputation"] = imp_mean.fit_transform(X_missing)

    # 2. 零值填充
    imp_0 = SimpleImputer(missing_values=np.nan, strategy="constant", fill_value=0)
    imputed_datasets["Zero Imputation"] = imp_0.fit_transform(X_missing)

    # 3. 随机森林填充
    X_missing_reg = X_missing.copy()
    # 按缺失值数量从少到多对列进行排序
    sortindex = np.argsort(X_missing_reg.isnull().sum(axis=0)).values

    for i in sortindex:
        df = X_missing_reg
        fillc = df.iloc[:, i]

        if not fillc.isnull().any():
            continue  # 如果该列没有缺失值，则跳过

        df = pd.concat([df.iloc[:, df.columns != i], pd.DataFrame(Y_full)], axis=1)
        # 使用0填充其他列的缺失值，以便为当前列的预测提供特征
        df_0 = SimpleImputer(missing_values=np.nan, strategy='constant', fill_value=0).fit_transform(df)

        ytrain = fillc[fillc.notnull()]
        ytest = fillc[fillc.isnull()]
        Xtrain = df_0[ytrain.index, :]
        Xtest = df_0[ytest.index, :]

        rfc = RandomForestRegressor(n_estimators=100)
        rfc = rfc.fit(Xtrain, ytrain)
        y_predict = rfc.predict(Xtest)

        X_missing_reg.loc[X_missing_reg.iloc[:, i].isnull(), i] = y_predict

    imputed_datasets["Regressor Imputation"] = X_missing_reg.values

    return imputed_datasets


def evaluate_models(datasets, Y_full):
    """
    使用交叉验证评估不同填充策略的效果。

    Args:
        datasets (dict): 包含不同填充策略结果的数据集字典。
        Y_full (np.ndarray): 完整的目标向量。

    Returns:
        dict: 一个字典，键是数据集名称，值是对应的均方误差 (MSE)。
    """
    mse_scores = {}
    estimator = RandomForestRegressor(random_state=0, n_estimators=100)

    for name, data in datasets.items():
        scores = cross_val_score(estimator, data, Y_full, scoring="neg_mean_squared_error", cv=5).mean()
        mse_scores[name] = scores * -1

    return mse_scores


def plot_results(mse_scores):
    labels = list(mse_scores.keys())
    scores = list(mse_scores.values())

    colors = ['r', 'g', 'b', 'orange']

    plt.figure(figsize=(12, 6))
    ax = plt.subplot(111)

    for i in np.arange(len(scores)):
        ax.barh(i, scores[i], color=colors[i % len(colors)], alpha=0.6, align='center')

    ax.set_title("不同缺失值填充策略的效果对比 (糖尿病数据集)")
    ax.set_xlabel("均方误差 (MSE) - 值越小越好")
    ax.set_xlim(left=np.min(scores) * 0.9, right=np.max(scores) * 1.1)
    ax.set_yticks(np.arange(len(scores)))
    ax.set_yticklabels(labels)
    plt.gca().invert_yaxis()  # 将最好的结果显示在顶部
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.show()


def main():
    X_full, Y_full = load_and_prepare_data()
    X_missing = create_missing_values(X_full, missing_rate=0.3, random_state=0)

    imputed_datasets = impute_data(X_missing, Y_full)
    all_datasets = {"Full Data": X_full, **imputed_datasets}

    mse_scores = evaluate_models(all_datasets, Y_full)
    print("\n各填充策略的均方误差 (MSE):")
    for name, score in mse_scores.items():
        print(f"{name}: {score:.4f}")
    plot_results(mse_scores)


if __name__ == "__main__":
    main()
