"""问题一：数据质量、周期退化规律和维护事件效应。"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

# Matplotlib 必须在导入 pyplot 前指定可写缓存目录。
_CACHE_ROOT = Path(tempfile.gettempdir()) / "math2026-filter-monitoring"
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(_CACHE_ROOT / "xdg"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.lines import Line2D

from .config import (
    ASSETS,
    BASE_COSTS,
    FIGURES_DIR,
    LIFETIME_THRESHOLD,
    PROCESSED_DIR,
    PROJECT_DIR,
    RESULTS_DIR,
    ensure_output_dirs,
)
from .io import load_maintenance, load_telemetry
from .preprocess import build_daily_panel, data_quality_summary


ANNUAL_PERIOD_DAYS = 365.25
BOOTSTRAP_SEED = 20260722
BOOTSTRAP_REPETITIONS = 2000


def maintenance_summary(maintenance: pd.DataFrame) -> pd.DataFrame:
    """统计各设备各类有记录维护次数。"""

    return (
        maintenance.groupby(["asset", "maintenance_type"], observed=True)
        .size()
        .rename("events")
        .reset_index()
        .sort_values(["asset", "maintenance_type"])
    )


def run_q1_scaffold() -> Dict[str, pd.DataFrame]:
    """生成问题一确定性数据层，不提前宣称统计模型已经完成。"""

    ensure_output_dirs()
    telemetry = load_telemetry()
    maintenance = load_maintenance()
    panel = build_daily_panel(telemetry, maintenance)
    quality = data_quality_summary(telemetry)
    events = maintenance_summary(maintenance)

    panel.to_csv(PROCESSED_DIR / "daily_panel.csv", index=False, date_format="%Y-%m-%d")
    quality.to_csv(RESULTS_DIR / "q1_data_quality.csv", index=False)
    events.to_csv(RESULTS_DIR / "q1_maintenance_summary.csv", index=False)
    return {"daily_panel": panel, "data_quality": quality, "maintenance_summary": events}


def prepare_analysis_panel(panel: pd.DataFrame) -> pd.DataFrame:
    """构造可解释的趋势、季节和维护周期特征。"""

    required = {
        "asset",
        "date",
        "performance_model",
        "performance_median",
        "valid_rows",
        "was_imputed",
        "days_since_maintenance",
        "maintenance_type",
    }
    missing = required - set(panel.columns)
    if missing:
        raise ValueError(f"问题一面板缺少字段：{sorted(missing)}")

    out = panel.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["asset"] = pd.Categorical(out["asset"], categories=ASSETS, ordered=True)
    out = out.dropna(subset=["date", "asset"]).sort_values(["asset", "date"]).reset_index(drop=True)

    start = out["date"].min()
    out["time_days"] = (out["date"] - start).dt.days.astype(float)
    out["time_years"] = out["time_days"] / ANNUAL_PERIOD_DAYS
    phase = 2.0 * np.pi * out["date"].dt.dayofyear.astype(float) / ANNUAL_PERIOD_DAYS
    out["sin_1"] = np.sin(phase)
    out["cos_1"] = np.cos(phase)
    out["sin_2"] = np.sin(2.0 * phase)
    out["cos_2"] = np.cos(2.0 * phase)
    out["month"] = out["date"].dt.month.astype(int)

    since = pd.to_numeric(out["days_since_maintenance"], errors="coerce")
    out["has_maintenance_history"] = since.notna().astype(float)
    since = since.fillna(0.0).clip(lower=0.0)
    out["fouling_0_30"] = since.clip(upper=30.0) / 30.0
    out["fouling_30_90"] = (since - 30.0).clip(lower=0.0, upper=60.0) / 60.0

    valid_rows = pd.to_numeric(out["valid_rows"], errors="coerce").fillna(0.0)
    # 四个有效样本已足以形成稳健日中位数，避免给小时采样阶段过高权重。
    out["quality_weight"] = np.clip(valid_rows / 4.0, 0.25, 1.0)
    out.loc[out["was_imputed"].fillna(False), "quality_weight"] *= 0.5
    out.loc[out["performance_model"].isna(), "quality_weight"] = 0.0
    return out


def fit_panel_models(panel: pd.DataFrame) -> Dict[str, Any]:
    """拟合趋势季节基线与加入维护周期后的完整解释模型。"""

    model_data = panel.loc[panel["performance_model"].notna()].copy()
    if model_data["asset"].nunique() < 2 or len(model_data) < 100:
        raise ValueError("问题一正式模型至少需要两个设备和 100 个有效日观测")

    trend_formula = (
        "performance_model ~ 0 + C(asset) + C(asset):time_years + "
        "sin_1 + cos_1 + sin_2 + cos_2"
    )
    full_formula = (
        trend_formula
        + " + has_maintenance_history + fouling_0_30 + fouling_30_90"
    )
    month_trend_formula = (
        "performance_model ~ 0 + C(asset) + C(asset):time_years + C(month)"
    )
    month_full_formula = (
        month_trend_formula
        + " + has_maintenance_history + fouling_0_30 + fouling_30_90"
    )

    def fit(formula: str) -> Any:
        return smf.wls(
            formula,
            data=model_data,
            weights=model_data["quality_weight"],
        ).fit(
            cov_type="cluster",
            cov_kwds={"groups": model_data["asset"].astype(str), "use_correction": True},
        )

    return {
        "trend_season": fit(trend_formula),
        "full": fit(full_formula),
        "month_trend": fit(month_trend_formula),
        "month_full": fit(month_full_formula),
        "data": model_data,
    }


def _seasonal_curve(model: Any) -> pd.DataFrame:
    days = np.arange(1, 367, dtype=float)
    phase = 2.0 * np.pi * days / ANNUAL_PERIOD_DAYS
    names = ["sin_1", "cos_1", "sin_2", "cos_2"]
    design = np.column_stack(
        [np.sin(phase), np.cos(phase), np.sin(2.0 * phase), np.cos(2.0 * phase)]
    )
    beta = model.params.reindex(names).to_numpy(dtype=float)
    covariance = model.cov_params().loc[names, names].to_numpy(dtype=float)
    # 显式逐项求和，规避部分 macOS Accelerate/NumPy 组合在重复自助抽样后
    # 对小矩阵 matmul 产生的伪浮点告警。
    effect = np.sum(design * beta[np.newaxis, :], axis=1)
    effect = effect - effect.mean()
    standard_error = np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", design, covariance, design), 0.0))
    return pd.DataFrame(
        {
            "day_of_year": days.astype(int),
            "seasonal_effect": effect,
            "ci95_low": effect - 1.96 * standard_error,
            "ci95_high": effect + 1.96 * standard_error,
        }
    )


def _asset_parameter(model: Any, asset: str, suffix: str) -> Tuple[float, float, float]:
    candidates = [name for name in model.params.index if f"[{asset}]" in name and name.endswith(suffix)]
    if len(candidates) != 1:
        raise KeyError(f"无法唯一定位设备 {asset} 的参数 {suffix}: {candidates}")
    name = candidates[0]
    interval = model.conf_int().loc[name]
    return float(model.params[name]), float(interval.iloc[0]), float(interval.iloc[1])


def build_device_metrics(panel: pd.DataFrame, models: Dict[str, Any]) -> pd.DataFrame:
    """生成连接问题一与问题二的设备级指标。"""

    work = panel.copy()
    model_data = work.loc[work["performance_model"].notna()].copy()
    model_data["full_prediction"] = models["full"].predict(model_data)
    model_data["full_residual"] = model_data["performance_model"] - model_data["full_prediction"]
    season = _seasonal_curve(models["full"])
    seasonal_amplitude = float((season["seasonal_effect"].max() - season["seasonal_effect"].min()) / 2.0)

    rows = []
    for asset in ASSETS:
        block = work.loc[work["asset"].astype(str) == asset].sort_values("date").copy()
        fitted = model_data.loc[model_data["asset"].astype(str) == asset]
        rolling = block["performance_model"].rolling(365, min_periods=330).mean()
        latest_rolling = float(rolling.dropna().iloc[-1]) if rolling.notna().any() else np.nan
        slope, slope_low, slope_high = _asset_parameter(models["full"], asset, ":time_years")
        rows.append(
            {
                "asset": asset,
                "start": block["date"].min(),
                "end": block["date"].max(),
                "calendar_days": len(block),
                "observed_days": int(block["performance_median"].notna().sum()),
                "model_days": int(block["performance_model"].notna().sum()),
                "imputed_days": int(block["was_imputed"].fillna(False).sum()),
                "mean_performance": float(block["performance_model"].mean()),
                "latest_rolling_365_mean": latest_rolling,
                "threshold_margin": latest_rolling - LIFETIME_THRESHOLD,
                "adjusted_linear_trend_per_year": slope,
                "trend_ci95_low": slope_low,
                "trend_ci95_high": slope_high,
                "common_seasonal_amplitude": seasonal_amplitude,
                "residual_rmse": float(np.sqrt(np.mean(np.square(fitted["full_residual"])))),
            }
        )
    return pd.DataFrame(rows)


def maintenance_event_effects(panel: pd.DataFrame, trend_model: Any) -> pd.DataFrame:
    """在去除设备趋势和公共季节项后计算每次维护的恢复与保持量。"""

    work = panel.copy()
    valid = work["performance_model"].notna()
    work.loc[valid, "trend_season_prediction"] = trend_model.predict(work.loc[valid])
    work["adjusted_performance"] = work["performance_model"] - work["trend_season_prediction"]

    rows = []
    events = work.loc[work["maintenance_type"].notna(), ["asset", "date", "maintenance_type"]]
    for event in events.itertuples(index=False):
        asset = str(event.asset)
        event_date = pd.Timestamp(event.date)
        block = work.loc[work["asset"].astype(str) == asset].copy()
        delta = (block["date"] - event_date).dt.days

        pre = block.loc[delta.between(-7, -1)]
        post_7 = block.loc[delta.between(1, 7)]
        post_30 = block.loc[delta.between(8, 30)]
        other_events = block.loc[
            block["maintenance_type"].notna() & (block["date"] != event_date), "date"
        ]
        overlap = bool(((other_events - event_date).dt.days.between(-7, 30)).any())

        pre_adjusted = pre["adjusted_performance"].dropna()
        post_7_adjusted = post_7["adjusted_performance"].dropna()
        post_30_adjusted = post_30["adjusted_performance"].dropna()
        pre_raw = pre["performance_model"].dropna()
        post_7_raw = post_7["performance_model"].dropna()
        post_30_raw = post_30["performance_model"].dropna()

        usable_instant = len(pre_adjusted) >= 4 and len(post_7_adjusted) >= 4 and not overlap
        usable_retained = len(pre_adjusted) >= 4 and len(post_30_adjusted) >= 10 and not overlap
        rows.append(
            {
                "asset": asset,
                "maintenance_date": event_date,
                "maintenance_type": str(event.maintenance_type),
                "overlap_with_other_event": overlap,
                "n_pre": len(pre_adjusted),
                "n_post_1_7": len(post_7_adjusted),
                "n_post_8_30": len(post_30_adjusted),
                "instant_gain_adjusted": (
                    float(post_7_adjusted.mean() - pre_adjusted.mean()) if usable_instant else np.nan
                ),
                "retained_gain_adjusted": (
                    float(post_30_adjusted.mean() - pre_adjusted.mean()) if usable_retained else np.nan
                ),
                "instant_gain_raw": (
                    float(post_7_raw.mean() - pre_raw.mean()) if usable_instant else np.nan
                ),
                "retained_gain_raw": (
                    float(post_30_raw.mean() - pre_raw.mean()) if usable_retained else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def _cluster_bootstrap_ci(
    frame: pd.DataFrame,
    value_col: str,
    repetitions: int = BOOTSTRAP_REPETITIONS,
    seed: int = BOOTSTRAP_SEED,
) -> Tuple[float, float]:
    usable = frame.dropna(subset=[value_col]).copy()
    clusters = usable["asset"].drop_duplicates().tolist()
    if not clusters:
        return np.nan, np.nan

    rng = np.random.default_rng(seed)
    grouped = {asset: usable.loc[usable["asset"] == asset, value_col].to_numpy() for asset in clusters}
    estimates = np.empty(repetitions, dtype=float)
    for index in range(repetitions):
        sampled_clusters = rng.choice(clusters, size=len(clusters), replace=True)
        values = np.concatenate([grouped[asset] for asset in sampled_clusters])
        estimates[index] = np.median(values)
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high)


def summarize_maintenance_effects(detail: pd.DataFrame) -> pd.DataFrame:
    """按维护类型汇总调整后恢复量，并给出设备簇自助置信区间。"""

    rows = []
    costs = {"medium": BASE_COSTS.medium, "major": BASE_COSTS.major, "minor": BASE_COSTS.minor}
    for maintenance_type in ("medium", "major"):
        group = detail.loc[detail["maintenance_type"] == maintenance_type].copy()
        instant = group["instant_gain_adjusted"].dropna()
        retained = group["retained_gain_adjusted"].dropna()
        instant_low, instant_high = _cluster_bootstrap_ci(group, "instant_gain_adjusted")
        retained_low, retained_high = _cluster_bootstrap_ci(
            group,
            "retained_gain_adjusted",
            seed=BOOTSTRAP_SEED + 1,
        )
        retained_median = float(retained.median()) if len(retained) else np.nan
        rows.append(
            {
                "maintenance_type": maintenance_type,
                "recorded_events": len(group),
                "usable_instant_events": len(instant),
                "usable_retained_events": len(retained),
                "instant_mean": float(instant.mean()) if len(instant) else np.nan,
                "instant_median": float(instant.median()) if len(instant) else np.nan,
                "instant_ci95_low": instant_low,
                "instant_ci95_high": instant_high,
                "instant_positive_rate": float((instant > 0).mean()) if len(instant) else np.nan,
                "retained_mean": float(retained.mean()) if len(retained) else np.nan,
                "retained_median": retained_median,
                "retained_ci95_low": retained_low,
                "retained_ci95_high": retained_high,
                "retained_positive_rate": float((retained > 0).mean()) if len(retained) else np.nan,
                "retained_gain_per_10k_cost": retained_median / costs[maintenance_type],
            }
        )
    return pd.DataFrame(rows)


def model_diagnostics(models: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name in ("trend_season", "full", "month_trend", "month_full"):
        model = models[name]
        residual = np.asarray(model.resid, dtype=float)
        rows.append(
            {
                "model": name,
                "nobs": int(model.nobs),
                "r_squared": float(model.rsquared),
                "adjusted_r_squared": float(model.rsquared_adj),
                "rmse": float(np.sqrt(np.mean(np.square(residual)))),
                "aic": float(model.aic),
                "bic": float(model.bic),
                "formula": model.model.formula,
            }
        )
    return pd.DataFrame(rows)


def model_parameters(models: Dict[str, Any]) -> pd.DataFrame:
    """导出模型系数、聚类稳健标准误和置信区间，保证论文数字可追溯。"""

    rows = []
    for model_name in ("trend_season", "full", "month_trend", "month_full"):
        model = models[model_name]
        intervals = model.conf_int()
        for term in model.params.index:
            rows.append(
                {
                    "model": model_name,
                    "term": term,
                    "estimate": float(model.params[term]),
                    "cluster_robust_std_error": float(model.bse[term]),
                    "ci95_low": float(intervals.loc[term].iloc[0]),
                    "ci95_high": float(intervals.loc[term].iloc[1]),
                    "p_value": float(model.pvalues[term]),
                }
            )
    return pd.DataFrame(rows)


def detect_residual_outliers(
    panel: pd.DataFrame,
    full_model: Any,
    threshold: float = 3.5,
) -> pd.DataFrame:
    """在拟合季节、趋势和维护周期后，用设备内 MAD 标记残差异常。"""

    work = panel.loc[panel["performance_model"].notna()].copy()
    work["prediction"] = full_model.predict(work)
    work["residual"] = work["performance_model"] - work["prediction"]
    parts = []
    for _, block in work.groupby("asset", observed=True):
        center = float(block["residual"].median())
        mad = float((block["residual"] - center).abs().median())
        scale = max(1.4826 * mad, 1e-9)
        out = block.copy()
        out["robust_z"] = (out["residual"] - center) / scale
        out["is_residual_outlier"] = out["robust_z"].abs() > threshold
        parts.append(out)
    columns = [
        "asset",
        "date",
        "performance_model",
        "prediction",
        "residual",
        "robust_z",
        "maintenance_type",
        "was_imputed",
        "is_residual_outlier",
    ]
    return pd.concat(parts, ignore_index=True)[columns]


def _configure_plot_style() -> None:
    font_path = PROJECT_DIR / "paper" / "fonts" / "SimHei.ttf"
    font_name = "sans-serif"
    if font_path.is_file():
        fontManager.addfont(str(font_path))
        font_name = FontProperties(fname=str(font_path)).get_name()
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "font.family": font_name,
            "axes.unicode_minus": False,
            "figure.dpi": 120,
            "savefig.dpi": 240,
            "axes.titleweight": "bold",
        }
    )


def _save_figure(fig: Any, name: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / name
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_device_overview(panel: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(5, 2, figsize=(14, 18), sharex=True)
    for ax, asset in zip(axes.ravel(), ASSETS):
        block = panel.loc[panel["asset"].astype(str) == asset].sort_values("date")
        ax.plot(block["date"], block["performance_model"], color="#9aa0a6", lw=0.7, alpha=0.55)
        rolling = block["performance_model"].rolling(30, min_periods=15).median()
        ax.plot(block["date"], rolling, color="#2457a7", lw=1.8)
        for event in block.loc[block["maintenance_type"].notna()].itertuples(index=False):
            color = "#d95f02" if event.maintenance_type == "major" else "#f2a900"
            ax.axvline(event.date, color=color, alpha=0.28, lw=0.8)
        ax.set_title(asset)
        ax.set_ylabel("透水率")
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for ax in axes[-1]:
        ax.tick_params(axis="x", rotation=30)
    handles = [
        Line2D([0], [0], color="#2457a7", lw=2, label="30日滚动中位数"),
        Line2D([0], [0], color="#f2a900", lw=2, label="中维护"),
        Line2D([0], [0], color="#d95f02", lw=2, label="大维护"),
    ]
    fig.suptitle("十台设备日透水率与维护记录", fontsize=18, y=0.995)
    fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.978),
        ncol=3,
        frameon=False,
    )
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    return _save_figure(fig, "q1_01_device_overview.png")


def plot_seasonal_curve(seasonal: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = seasonal["day_of_year"].to_numpy()
    ax.plot(x, seasonal["seasonal_effect"], color="#2457a7", lw=2.2, label="公共季节效应")
    ax.fill_between(
        x,
        seasonal["ci95_low"].to_numpy(),
        seasonal["ci95_high"].to_numpy(),
        color="#2457a7",
        alpha=0.18,
        label="95%置信区间",
    )
    month_starts = pd.date_range("2025-01-01", "2025-12-01", freq="MS")
    ax.set_xticks(month_starts.dayofyear)
    ax.set_xticklabels([f"{month}月" for month in range(1, 13)])
    ax.axhline(0.0, color="black", lw=0.8)
    ax.set_xlabel("年内日期")
    ax.set_ylabel("季节调整量")
    ax.set_title("控制设备趋势与维护周期后的公共季节效应")
    ax.legend(frameon=False)
    fig.tight_layout()
    return _save_figure(fig, "q1_02_seasonal_curve.png")


def plot_maintenance_effects(detail: pd.DataFrame) -> Path:
    long = detail.melt(
        id_vars=["asset", "maintenance_type"],
        value_vars=["instant_gain_adjusted", "retained_gain_adjusted"],
        var_name="effect_window",
        value_name="gain",
    ).dropna(subset=["gain"])
    long["维护类型"] = long["maintenance_type"].map({"medium": "中维护", "major": "大维护"})
    long["观察窗口"] = long["effect_window"].map(
        {"instant_gain_adjusted": "维护后1—7日", "retained_gain_adjusted": "维护后8—30日"}
    )
    fig, ax = plt.subplots(figsize=(9, 5.8))
    sns.boxplot(
        data=long,
        x="观察窗口",
        y="gain",
        hue="维护类型",
        showfliers=False,
        palette={"中维护": "#f2a900", "大维护": "#d95f02"},
        ax=ax,
    )
    sns.stripplot(
        data=long,
        x="观察窗口",
        y="gain",
        hue="维护类型",
        dodge=True,
        alpha=0.45,
        size=3,
        palette={"中维护": "#f2a900", "大维护": "#d95f02"},
        legend=False,
        ax=ax,
    )
    ax.axhline(0.0, color="black", lw=0.9)
    ax.set_xlabel("")
    ax.set_ylabel("去趋势、去季节后的透水率变化")
    ax.set_title("维护事件调整后恢复量与保持量")
    ax.legend(title="维护类型", frameon=False)
    fig.tight_layout()
    return _save_figure(fig, "q1_03_maintenance_effects.png")


def plot_device_metrics(metrics: pd.DataFrame) -> Path:
    ordered = metrics.set_index("asset").reindex(ASSETS).reset_index()
    x = np.arange(len(ordered))
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    trend = ordered["adjusted_linear_trend_per_year"].to_numpy()
    low = ordered["trend_ci95_low"].to_numpy()
    high = ordered["trend_ci95_high"].to_numpy()
    axes[0].bar(x, trend, color=np.where(trend < 0, "#c44e52", "#4c72b0"), alpha=0.85)
    axes[0].errorbar(x, trend, yerr=np.vstack([trend - low, high - trend]), fmt="none", ecolor="black", capsize=3)
    axes[0].axhline(0.0, color="black", lw=0.8)
    axes[0].set_ylabel("年变化量")
    axes[0].set_title("控制季节和维护周期后的设备线性趋势（95%置信区间）")

    margin = ordered["threshold_margin"].to_numpy()
    axes[1].bar(x, margin, color="#55a868", alpha=0.85)
    axes[1].axhline(0.0, color="black", lw=0.8)
    axes[1].set_ylabel("滚动年均值减37")
    axes[1].set_title("当前滚动365日性能阈值裕度")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(ordered["asset"])
    fig.tight_layout()
    return _save_figure(fig, "q1_04_device_metrics.png")


def plot_sampling_profile(panel: pd.DataFrame) -> Path:
    profile = panel.groupby("date", as_index=False)["valid_rows"].median()
    profile["rolling_14"] = profile["valid_rows"].rolling(14, min_periods=7).median()
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(profile["date"], profile["valid_rows"], color="#9aa0a6", alpha=0.35, lw=0.7)
    ax.plot(profile["date"], profile["rolling_14"], color="#8172b2", lw=2.0)
    ax.set_ylabel("每日有效样本数中位数")
    ax.set_xlabel("日期")
    ax.set_title("采样频率变化：十台设备每日有效记录数")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return _save_figure(fig, "q1_05_sampling_profile.png")


def _write_key_findings(
    metrics: pd.DataFrame,
    seasonal: pd.DataFrame,
    maintenance: pd.DataFrame,
    diagnostics: pd.DataFrame,
    outliers: pd.DataFrame,
    figure_paths: Iterable[Path],
) -> Dict[str, Any]:
    peak = seasonal.loc[seasonal["seasonal_effect"].idxmax()]
    trough = seasonal.loc[seasonal["seasonal_effect"].idxmin()]
    findings: Dict[str, Any] = {
        "analysis_version": "q1-formal-v1",
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
        "device_count": int(metrics["asset"].nunique()),
        "annual_seasonal_amplitude": float(metrics["common_seasonal_amplitude"].iloc[0]),
        "seasonal_peak_day_of_year": int(peak["day_of_year"]),
        "seasonal_trough_day_of_year": int(trough["day_of_year"]),
        "full_model_r_squared": float(
            diagnostics.loc[diagnostics["model"] == "full", "r_squared"].iloc[0]
        ),
        "residual_outlier_count": int(outliers["is_residual_outlier"].sum()),
        "residual_outlier_rate": float(outliers["is_residual_outlier"].mean()),
        "maintenance_effects": maintenance.to_dict(orient="records"),
        "figures": [path.name for path in figure_paths],
        "interpretation_limit": (
            "维护效果已控制公共季节与设备趋势，但仍属于观察性事件研究，"
            "不能排除未记录小维护和指征偏差。"
        ),
    }
    with (RESULTS_DIR / "q1_key_findings.json").open("w", encoding="utf-8") as handle:
        json.dump(findings, handle, ensure_ascii=False, indent=2)
    return findings


def run_q1_formal() -> Dict[str, Any]:
    """运行问题一正式分析，生成可供论文和问题二复用的结果。"""

    base = run_q1_scaffold()
    panel = prepare_analysis_panel(base["daily_panel"])
    models = fit_panel_models(panel)
    metrics = build_device_metrics(panel, models)
    event_detail = maintenance_event_effects(panel, models["trend_season"])
    event_summary = summarize_maintenance_effects(event_detail)
    month_event_detail = maintenance_event_effects(panel, models["month_trend"])
    month_event_summary = summarize_maintenance_effects(month_event_detail)
    event_robustness = pd.concat(
        [
            event_summary.assign(season_specification="fourier"),
            month_event_summary.assign(season_specification="month_fixed_effect"),
        ],
        ignore_index=True,
    )
    diagnostics = model_diagnostics(models)
    parameters = model_parameters(models)
    seasonal = _seasonal_curve(models["full"])
    outliers = detect_residual_outliers(panel, models["full"])

    metrics.to_csv(RESULTS_DIR / "q1_device_metrics.csv", index=False, date_format="%Y-%m-%d")
    event_detail.to_csv(
        RESULTS_DIR / "q1_event_effects_detail.csv",
        index=False,
        date_format="%Y-%m-%d",
    )
    event_summary.to_csv(RESULTS_DIR / "q1_maintenance_effects.csv", index=False)
    event_robustness.to_csv(
        RESULTS_DIR / "q1_maintenance_effects_robustness.csv",
        index=False,
    )
    diagnostics.to_csv(RESULTS_DIR / "q1_model_diagnostics.csv", index=False)
    parameters.to_csv(RESULTS_DIR / "q1_model_parameters.csv", index=False)
    seasonal.to_csv(RESULTS_DIR / "q1_seasonal_curve.csv", index=False)
    outliers.loc[outliers["is_residual_outlier"]].to_csv(
        RESULTS_DIR / "q1_residual_outliers.csv",
        index=False,
        date_format="%Y-%m-%d",
    )

    _configure_plot_style()
    figure_paths = [
        plot_device_overview(panel),
        plot_seasonal_curve(seasonal),
        plot_maintenance_effects(event_detail),
        plot_device_metrics(metrics),
        plot_sampling_profile(panel),
    ]
    findings = _write_key_findings(
        metrics,
        seasonal,
        event_summary,
        diagnostics,
        outliers,
        figure_paths,
    )
    return {
        **base,
        "analysis_panel": panel,
        "models": models,
        "device_metrics": metrics,
        "event_detail": event_detail,
        "maintenance_effects": event_summary,
        "maintenance_effects_robustness": event_robustness,
        "model_diagnostics": diagnostics,
        "model_parameters": parameters,
        "seasonal_curve": seasonal,
        "residual_outliers": outliers,
        "figures": figure_paths,
        "key_findings": findings,
    }
