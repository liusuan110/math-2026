import os

import pandas as pd
import numpy as np
import statsmodels.api as sm
import seaborn as sns
import matplotlib.pyplot as plt

from pprint import pprint
from statsmodels.graphics.api import qqplot
from statsmodels.tsa.stattools import adfuller  # ACF / PACF
from statsmodels.stats.diagnostic import acorr_ljungbox  # 白噪声检验

import warnings

warnings.filterwarnings("ignore")

# -- 图片预设，需要 plt, fm, cycler 库
import matplotlib.font_manager as fm
from cycler import cycler

font_path = "../../utils/fonts/SourceHanSerifCN-Regular.otf"
if os.path.exists(font_path):
    # 如果字体文件存在，则加载并使用它
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rcParams['font.sans-serif'] = [font_name]
else:
    fallback_fonts = ['STZhongsong', 'SimHei', 'Microsoft YaHei', 'Heiti TC', 'PingFang SC', 'sans-serif']
    plt.rcParams['font.sans-serif'] = fallback_fonts
    print(f"警告: 字体文件 '{font_path}' 未找到, 将使用系统备选字体: {fallback_fonts}")

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

ds = [10930, 10318, 10595, 10972, 7706, 6756, 9092, 10551, 9722, 10913, 11151, 8186, 6422,
      6337, 11649, 11652, 10310, 12043, 7937, 6476, 9662, 9570, 9981, 9331, 9449, 6773, 6304, 9355,
      10477, 10148, 10395, 11261, 8713, 7299, 10424, 10795, 11069, 11602, 11427, 9095, 7707, 10767,
      12136, 12812, 12006, 12528, 10329, 7818, 11719, 11683, 12603, 11495, 13670, 11337, 10232,
      13261, 13230, 15535, 16837, 19598, 14823, 11622, 19391, 18177, 19994, 14723, 15694, 13248,
      9543, 12872, 13101, 15053, 12619, 13749, 10228, 9725, 14729, 12518, 14564, 15085, 14722,
      11999, 9390, 13481, 14795, 15845, 15271, 14686, 11054, 10395]


# 原 Data Series
def read_and_display_data(time_series: pd.Series) -> pd.Series:
    time_series = pd.Series(time_series)
    time_series.index = pd.Index(sm.tsa.datetools.dates_from_range('2001', '2090'))
    time_series.plot(figsize=(12, 8))
    plt.title('Original Data Series')
    return time_series


def diff_data(time_series: pd.Series) -> pd.Series:
    """序列差分"""
    fig = plt.figure(figsize=(12, 8))
    ax1 = fig.add_subplot(111)
    diff_ds_1 = time_series.diff(1)
    diff_ds_1.plot(ax=ax1)
    plt.title('Difference (1) Data Series')
    diff_ds_1.dropna(inplace=True)
    return diff_ds_1


def ljung_box_test(time_series: pd.Series) -> None:
    """白噪声检验"""
    ljung_box_result = acorr_ljungbox(time_series, lags=[6, 12, 24], return_df=True)
    print(ljung_box_result)

    if ljung_box_result.iloc[-1]['lb_pvalue'] < 0.05:
        print("\n在所有检验的延迟阶数上，P值均小于0.05，因此拒绝原假设。则序列为非白噪声序列，存在自相关性，适合 ARIMA 模型")
    else:
        print("\nP值大于0.05，无法拒绝原假设，序列可能为白噪声序列。")


def test_stationarity(time_series: pd.Series):
    """计算滚动均值"""
    roll_mean = time_series.rolling(20).mean()
    roll_std = time_series.rolling(20).std()

    plt.figure(figsize=(10, 5))
    plt.plot(time_series, color='blue', label='原序列')
    plt.plot(roll_mean, color='red', label='滚动均值')
    plt.plot(roll_std, color='black', label='滚动标准差')
    plt.legend(loc='best')
    plt.title('Rolling Mean & Standard Deviation')
    plt.show()

    # Perform Augmented-Dickey-Fuller Test:
    res = adfuller(time_series, autolag='AIC')  # 使用 AIC 准则选择滞后阶数
    print(f"ADF Value: {res[0]:.4f}, P: {res[1]:.8f}")
    for k, v in res[4].items():
        print('Critical Values:')
        print(f'   {k}, {v:.3f}')
    return res


def plot_acf_pacf(time_series: pd.Series):
    """绘制平稳时间序列的自相关图和偏自相关图"""
    fig = plt.figure(figsize=(12, 8))
    ax1 = fig.add_subplot(211)
    fig = sm.graphics.tsa.plot_acf(time_series, lags=40, ax=ax1)
    ax2 = fig.add_subplot(212)
    fig = sm.graphics.tsa.plot_pacf(time_series, lags=40, ax=ax2)
    plt.show()
    # fig 为一个父对象，ax1、ax2 是子对象，这里的 211 是缩写
    # 分割为两行一列，激活第 1 / 2 张图


def aic_and_bic(p_max: int, q_max: int) -> (tuple[int, int]):
    """AIC / BIC 信息量推优"""
    # 将行设置为 p (AR)，列设置为 q (MA)
    aic_matrix = pd.DataFrame(index=[f'AR{i}' for i in range(p_max + 1)],
                              columns=[f'MA{i}' for i in range(q_max + 1)],
                              dtype=float)
    bic_matrix = pd.DataFrame(index=[f'AR{i}' for i in range(p_max + 1)],
                              columns=[f'MA{i}' for i in range(q_max + 1)],
                              dtype=float)

    for p in range(p_max + 1):
        for q in range(q_max + 1):
            if p == 0 and q == 0:
                continue  # 避免拟合 ARIMA(0,1,0) 模型

            # 原始序列 ds 上操作，并设置 d = 1
            arima_model = sm.tsa.ARIMA(ds, order=(p, 1, q))
            results = arima_model.fit()

            aic_matrix.iloc[p, q] = results.aic
            bic_matrix.iloc[p, q] = results.bic
            print(f'完成: ARIMA({p}, 1, {q}) - AIC:{results.aic:.2f}, BIC:{results.bic:.2f}')

    min_aic_pq = aic_matrix.stack().idxmin()
    min_bic_pq = bic_matrix.stack().idxmin()

    print(f"最小 AIC 值的组合为: {min_aic_pq}，值为: {aic_matrix.min().min():.2f}")
    print(f"最小 BIC 值的组合为: {min_bic_pq}，值为: {bic_matrix.min().min():.2f}")

    plt.figure(figsize=(10, 8))
    sns.heatmap(bic_matrix.astype(float), annot=True, fmt=".2f", cmap="Purples")
    plt.title('BIC (Bayesian Information Criterion) Heatmap')
    plt.xlabel('MA order (q)')
    plt.ylabel('AR order (p)')
    plt.show()

    return int(min_bic_pq[0][2:]), int(min_bic_pq[1][2:])  # 常用 BIC 信息量作为标准


def run_model_diagnostics(results, lags=24):
    """
    执行模型残差诊断.
    results: 已拟合的 statsmodels 模型结果对象。
    lags: Ljung-Box 检验的最大滞后阶数。
    """
    # 四图：标准化残差图、直方图与密度估计图、正态 Q-Q 图、自相关图
    results.plot_diagnostics(figsize=(15, 12))
    plt.tight_layout()
    plt.show()

    residuals = results.resid
    lb_results_df = sm.stats.acorr_ljungbox(residuals, lags=range(1, lags + 1), return_df=True)
    print("\nLjung-Box Test on Residuals:")
    print(lb_results_df)

    dw_stat = sm.stats.durbin_watson(residuals.values)
    print(f"\nDurbin-Watson Statistic: {dw_stat:.4f}")


# 构建 ARIMA 模型
def build_arima_model(time_series: pd.Series, p: int, d: int, q: int):
    arima_model = sm.tsa.ARIMA(time_series, order=(p, d, q))
    arima_results = arima_model.fit()
    pprint(arima_results.summary())

    # 在指数平滑模型下，观察 ARIMA 模型的残差是否是平均值为 0
    # 且方差为常数的正态分布（服从零均值、方差不变的正态分布），同时也要观察连续残差是否（自）相关
    resid = arima_results.resid
    fig = plt.figure(figsize=(12, 8))
    ax1 = fig.add_subplot(211)
    fig = sm.graphics.tsa.plot_acf(resid.values.squeeze(), lags=40, ax=ax1)
    ax2 = fig.add_subplot(212)
    sm.graphics.tsa.plot_pacf(resid, lags=40, ax=ax2)

    run_model_diagnostics(arima_results, lags=12)

    return arima_results


def build_sarima_model(time_series: pd.Series, p: int, d: int, q: int, s: int):
    """建立 SARIMA 模型
    :param: s: 周期性
    """
    sarima_model = sm.tsa.SARIMAX(time_series, order=(p, d, q), seasonal_order=(p, d, q, s))
    sarima_results = sarima_model.fit()
    pprint(sarima_results.summary())

    run_model_diagnostics(sarima_results, lags=12)

    return sarima_results


def plot_forecast(results, time_series, forecast_steps=10):
    """
    根据已拟合的模型结果，进行未来预测并绘制结果图。

    参数:
    results: 已拟合的 statsmodels 模型结果对象 (例如 arima_results, sarima_results)。
    time_series: pd.Series - 原始的完整时间序列数据，用于绘图。
    forecast_steps: int - 希望向未来预测的步数。
    """
    forecast_obj = results.get_forecast(steps=forecast_steps)
    forecast_values = forecast_obj.predicted_mean
    confidence_intervals = forecast_obj.conf_int()  # 提取置信区间（95%）

    forecast_df = pd.DataFrame({
        'Forecast': forecast_values,
        'Lower CI': confidence_intervals.iloc[:, 0],
        'Upper CI': confidence_intervals.iloc[:, 1]
    })
    print(forecast_df)

    plt.figure()
    plt.plot(time_series, label='历史数据')
    # 为了绘图的连续性，获取历史数据的最后一个点
    last_date = time_series.index[-1]
    last_value = time_series.iloc[-1]
    plot_series = pd.concat([pd.Series({last_date: last_value}), forecast_values])
    plt.plot(plot_series, label='预测值', color='red', linestyle='--')
    plt.fill_between(confidence_intervals.index,
                     confidence_intervals.iloc[:, 0],
                     confidence_intervals.iloc[:, 1],
                     color='pink',
                     alpha=0.6,
                     label='95% 置信区间')
    plt.title('时间序列预测与置信区间')
    plt.xlabel('日期')
    plt.ylabel('数值')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    ds = read_and_display_data(ds)
    diff_ds_1 = diff_data(ds)
    ljung_box_test(diff_ds_1)
    adf_result = test_stationarity(diff_ds_1)
    plot_acf_pacf(diff_ds_1)

    p, q = aic_and_bic(7, 7)
    print(f"推荐 ARIMA(p,d,q) 参数为: p={p}, q={q}")

    build_arima_model(ds, p=6, d=1, q=6)
    sarima_results = build_sarima_model(ds, p=6, d=1, q=6, s=7)

    plot_forecast(sarima_results, ds, forecast_steps=20)
