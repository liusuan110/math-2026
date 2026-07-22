"""问题二：现行维护规律下的分层退化状态模型与寿命外推。"""

from __future__ import annotations

import json
import os
import tempfile
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence

# Matplotlib 必须在导入 pyplot 前指定可写缓存目录。
_CACHE_ROOT = Path(tempfile.gettempdir()) / "math2026-filter-monitoring"
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(_CACHE_ROOT / "xdg"))

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.linalg import pinvh
from scipy.optimize import lsq_linear
from statsmodels.tools.sm_exceptions import ConvergenceWarning, ValueWarning
from statsmodels.tsa.statespace.sarimax import SARIMAX

from .config import (
    ASSETS,
    COMMISSION_DATE,
    FIGURES_DIR,
    LIFETIME_THRESHOLD,
    PROCESSED_DIR,
    RESULTS_DIR,
    ROLLING_YEAR_DAYS,
    ensure_output_dirs,
)
from .io import load_maintenance
from .q1_analysis import (
    ANNUAL_PERIOD_DAYS,
    _configure_plot_style,
    _save_figure,
    fit_panel_models,
    prepare_analysis_panel,
    run_q1_scaffold,
)


FORECAST_HORIZON_YEARS = 30
SIMULATION_PATHS = 2000
SIMULATION_SEED = 20260724
STATE_SHRINKAGE = 1600.0
TRANSIENT_TIME_YEARS = 2.0
TRANSIENT_PENALTY = 5.0
PRIOR_WEIGHT = 20.0
BACKTEST_HORIZONS_DAYS = (270, 180, 90)
RECOVERY_LEVELS = (35.0, 37.0, 39.0)
MODEL_FEATURES = (
    "sin_1",
    "cos_1",
    "sin_2",
    "cos_2",
    "has_maintenance_history",
    "fouling_0_30",
    "fouling_30_90",
)


@dataclass(frozen=True)
class HierarchicalStateModel:
    """带非负长期退化率、设备部分汇聚和饱和早期漂移的状态模型。"""

    assets: tuple[str, ...]
    reference_date: pd.Timestamp
    transient_time_years: float
    shrinkage: float
    transient_penalty: float
    parameter_names: tuple[str, ...]
    params: np.ndarray
    covariance: np.ndarray
    residual_std: float
    residual_ar1: float
    nobs: int
    weighted_rmse: float
    r_squared: float
    prior_degradation_per_year: float

    def parameter(self, name: str) -> float:
        return float(self.params[self.parameter_names.index(name)])

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        design = _state_design(
            frame,
            assets=self.assets,
            reference_date=self.reference_date,
            transient_time_years=self.transient_time_years,
            parameter_names=self.parameter_names,
        )
        return np.sum(design * self.params[np.newaxis, :], axis=1)


def add_rolling_annual_mean(
    forecast: pd.DataFrame,
    value_col: str = "performance_forecast",
) -> pd.DataFrame:
    """为每台设备的日预测添加滚动 365 日平均值。"""

    required = {"asset", "date", value_col}
    missing = required - set(forecast.columns)
    if missing:
        raise ValueError(f"寿命预测输入缺少字段：{sorted(missing)}")
    out = forecast.sort_values(["asset", "date"]).copy()
    out["rolling_annual_mean"] = out.groupby("asset")[value_col].transform(
        lambda series: series.rolling(
            ROLLING_YEAR_DAYS,
            min_periods=ROLLING_YEAR_DAYS,
        ).mean()
    )
    return out


def first_threshold_crossing(
    forecast: pd.DataFrame,
    threshold: float = LIFETIME_THRESHOLD,
) -> pd.DataFrame:
    """返回滚动年均首次低于阈值的候选日期。"""

    crossed = forecast.loc[forecast["rolling_annual_mean"] < threshold]
    return (
        crossed.groupby("asset", as_index=False)["date"]
        .min()
        .rename(columns={"date": "candidate_threshold_date"})
    )


def _asset_strings(series: pd.Series) -> pd.Series:
    return series.astype("object").astype(str)


def _ensure_state_features(
    frame: pd.DataFrame,
    reference_date: pd.Timestamp,
) -> pd.DataFrame:
    out = frame.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["asset"] = _asset_strings(out["asset"])
    out["time_years"] = (
        (out["date"] - pd.Timestamp(reference_date)).dt.days.astype(float)
        / ANNUAL_PERIOD_DAYS
    )
    phase = 2.0 * np.pi * out["date"].dt.dayofyear.astype(float) / ANNUAL_PERIOD_DAYS
    out["sin_1"] = np.sin(phase)
    out["cos_1"] = np.cos(phase)
    out["sin_2"] = np.sin(2.0 * phase)
    out["cos_2"] = np.cos(2.0 * phase)

    since = pd.to_numeric(out.get("days_since_maintenance"), errors="coerce")
    out["has_maintenance_history"] = since.notna().astype(float)
    since = since.fillna(0.0).clip(lower=0.0)
    out["fouling_0_30"] = since.clip(upper=30.0) / 30.0
    out["fouling_30_90"] = (since - 30.0).clip(lower=0.0, upper=60.0) / 60.0
    return out


def _parameter_names(assets: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        [f"intercept:{asset}" for asset in assets]
        + [f"degradation:{asset}" for asset in assets]
        + [f"transient:{asset}" for asset in assets]
        + list(MODEL_FEATURES)
        + ["common_degradation"]
    )


def _state_design(
    frame: pd.DataFrame,
    assets: Sequence[str],
    reference_date: pd.Timestamp,
    transient_time_years: float,
    parameter_names: Sequence[str] | None = None,
) -> np.ndarray:
    work = _ensure_state_features(frame, reference_date)
    asset_values = work["asset"].to_numpy(dtype=str)
    time_years = work["time_years"].to_numpy(dtype=float)
    transient = 1.0 - np.exp(-np.maximum(time_years, 0.0) / transient_time_years)
    columns: dict[str, np.ndarray] = {}
    for asset in assets:
        indicator = (asset_values == asset).astype(float)
        columns[f"intercept:{asset}"] = indicator
        columns[f"degradation:{asset}"] = -time_years * indicator
        columns[f"transient:{asset}"] = transient * indicator
    for name in MODEL_FEATURES:
        columns[name] = work[name].to_numpy(dtype=float)
    columns["common_degradation"] = np.zeros(len(work), dtype=float)
    names = tuple(parameter_names or _parameter_names(assets))
    return np.column_stack([columns[name] for name in names])


def _independent_decay_prior(panel: pd.DataFrame) -> float:
    """用训练期设备斜率的稳健中位数给长期退化率设置弱先验。"""

    try:
        model = fit_panel_models(panel)["full"]
        declines = [
            -float(value)
            for name, value in model.params.items()
            if name.endswith(":time_years") and float(value) < 0.0
        ]
    except (ValueError, KeyError, np.linalg.LinAlgError):
        declines = []
    prior = float(np.median(declines)) if declines else 12.0
    return float(np.clip(prior, 3.0, 30.0))


def fit_hierarchical_state_model(
    panel: pd.DataFrame,
    *,
    shrinkage: float = STATE_SHRINKAGE,
    transient_time_years: float = TRANSIENT_TIME_YEARS,
    transient_penalty: float = TRANSIENT_PENALTY,
    reference_date: pd.Timestamp | None = None,
) -> HierarchicalStateModel:
    """拟合可长期外推的分层退化状态模型。

    设备长期退化率被限制为非负并向队列均值汇聚；观测期内的阶段性上升或
    下降由饱和项 ``u_i(1-exp(-t/tau))`` 吸收，避免把正斜率永久外推。
    """

    required = {"asset", "date", "performance_model"}
    missing = required - set(panel.columns)
    if missing:
        raise ValueError(f"问题二面板缺少字段：{sorted(missing)}")
    valid = panel.loc[panel["performance_model"].notna()].copy()
    if len(valid) < 500 or valid["asset"].nunique() < 2:
        raise ValueError("分层退化模型至少需要两个设备和 500 个有效设备日")
    reference = pd.Timestamp(reference_date or pd.to_datetime(valid["date"]).min())
    valid = _ensure_state_features(valid, reference)
    assets = tuple(asset for asset in ASSETS if asset in set(valid["asset"]))
    names = _parameter_names(assets)
    design = _state_design(valid, assets, reference, transient_time_years, names)
    response = valid["performance_model"].to_numpy(dtype=float)
    weights = pd.to_numeric(valid.get("quality_weight", 1.0), errors="coerce")
    if not isinstance(weights, pd.Series):
        weights = pd.Series(np.ones(len(valid)), index=valid.index)
    weights = weights.fillna(0.25).clip(lower=0.05, upper=1.0).to_numpy(dtype=float)
    root_weight = np.sqrt(weights)
    weighted_design = design * root_weight[:, np.newaxis]
    weighted_response = response * root_weight

    prior = _independent_decay_prior(valid)
    penalty_rows: list[np.ndarray] = []
    penalty_targets: list[float] = []
    common_index = names.index("common_degradation")
    for asset in assets:
        row = np.zeros(len(names), dtype=float)
        row[names.index(f"degradation:{asset}")] = np.sqrt(shrinkage)
        row[common_index] = -np.sqrt(shrinkage)
        penalty_rows.append(row)
        penalty_targets.append(0.0)
    row = np.zeros(len(names), dtype=float)
    row[common_index] = np.sqrt(PRIOR_WEIGHT)
    penalty_rows.append(row)
    penalty_targets.append(np.sqrt(PRIOR_WEIGHT) * prior)
    for asset in assets:
        row = np.zeros(len(names), dtype=float)
        row[names.index(f"transient:{asset}")] = np.sqrt(transient_penalty)
        penalty_rows.append(row)
        penalty_targets.append(0.0)

    augmented_design = np.vstack([weighted_design, np.vstack(penalty_rows)])
    augmented_response = np.concatenate([weighted_response, penalty_targets])
    lower = np.full(len(names), -np.inf, dtype=float)
    upper = np.full(len(names), np.inf, dtype=float)
    for index, name in enumerate(names):
        if name.startswith("degradation:") or name == "common_degradation":
            lower[index] = 0.0

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        fitted = lsq_linear(
            augmented_design,
            augmented_response,
            bounds=(lower, upper),
            lsq_solver="lsmr",
            lsmr_tol="auto",
            max_iter=500,
        )
    if not fitted.success:
        raise RuntimeError(f"分层退化状态模型未收敛：{fitted.message}")

    prediction = np.sum(design * fitted.x[np.newaxis, :], axis=1)
    residual = response - prediction
    weighted_sse = float(np.sum(weights * np.square(residual)))
    weighted_rmse = float(np.sqrt(weighted_sse / np.sum(weights)))
    centered = response - np.average(response, weights=weights)
    weighted_sst = float(np.sum(weights * np.square(centered)))
    r_squared = 1.0 - weighted_sse / weighted_sst

    ar1_values = []
    residual_frame = valid[["asset", "date"]].copy()
    residual_frame["residual"] = residual
    for _, block in residual_frame.groupby("asset"):
        ordered = block.sort_values("date")["residual"]
        correlation = ordered.corr(ordered.shift(1))
        if pd.notna(correlation):
            ar1_values.append(float(correlation))
    residual_ar1 = float(np.clip(np.median(ar1_values), -0.8, 0.9)) if ar1_values else 0.0
    inflation = float(np.clip((1.0 + residual_ar1) / (1.0 - residual_ar1), 1.0, 9.0))
    degrees = max(int(np.sum(weights > 0.0)) - len(names), 1)
    variance = weighted_sse / degrees
    gram = np.einsum("ni,nj->ij", augmented_design, augmented_design)
    # 部分 macOS Accelerate/BLAS 组合会在小型伪逆矩阵乘法时发出伪
    # RuntimeWarning；结果本身有限，故在此局部屏蔽并随后显式校验。
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        covariance = pinvh(gram + np.eye(len(names)) * 1e-9) * variance * inflation
    if not np.isfinite(covariance).all():
        raise RuntimeError("分层退化模型协方差矩阵包含非有限值")

    return HierarchicalStateModel(
        assets=assets,
        reference_date=reference,
        transient_time_years=float(transient_time_years),
        shrinkage=float(shrinkage),
        transient_penalty=float(transient_penalty),
        parameter_names=names,
        params=np.asarray(fitted.x, dtype=float),
        covariance=np.asarray(covariance, dtype=float),
        residual_std=float(np.sqrt(np.mean(np.square(residual)))),
        residual_ar1=residual_ar1,
        nobs=len(valid),
        weighted_rmse=weighted_rmse,
        r_squared=float(r_squared),
        prior_degradation_per_year=prior,
    )


def state_parameter_table(model: HierarchicalStateModel) -> pd.DataFrame:
    standard_error = np.sqrt(np.maximum(np.diag(model.covariance), 0.0))
    rows = []
    for index, name in enumerate(model.parameter_names):
        estimate = float(model.params[index])
        low = estimate - 1.96 * standard_error[index]
        if name.startswith("degradation:") or name == "common_degradation":
            low = max(low, 0.0)
        rows.append(
            {
                "parameter": name,
                "estimate": estimate,
                "approx_std_error_ar1_inflated": float(standard_error[index]),
                "approx_ci95_low": float(low),
                "approx_ci95_high": float(estimate + 1.96 * standard_error[index]),
            }
        )
    return pd.DataFrame(rows)


def _sarimax_prediction(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    exogenous = ("time_years",) + MODEL_FEATURES
    for asset in ASSETS:
        train_block = train.loc[_asset_strings(train["asset"]) == asset].sort_values("date")
        test_block = test.loc[_asset_strings(test["asset"]) == asset].sort_values("date")
        if len(train_block) < 300 or test_block.empty:
            continue
        x_train = np.column_stack(
            [np.ones(len(train_block)), train_block.loc[:, exogenous].to_numpy(dtype=float)]
        )
        x_test = np.column_stack(
            [np.ones(len(test_block)), test_block.loc[:, exogenous].to_numpy(dtype=float)]
        )
        response = pd.Series(train_block["performance_model"].to_numpy(dtype=float))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            warnings.simplefilter("ignore", ValueWarning)
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", RuntimeWarning)
            result = SARIMAX(
                response,
                exog=x_train,
                order=(1, 0, 0),
                trend="n",
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False, maxiter=120)
            prediction = np.asarray(
                result.get_forecast(steps=len(test_block), exog=x_test).predicted_mean,
                dtype=float,
            )
        rows.append(
            pd.DataFrame(
                {
                    "asset": asset,
                    "date": test_block["date"].to_numpy(),
                    "prediction": prediction,
                }
            )
        )
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _prediction_metrics(
    full_panel: pd.DataFrame,
    test: pd.DataFrame,
    predictions: pd.DataFrame,
    cutoff: pd.Timestamp,
) -> dict[str, float | int]:
    actual = test[["asset", "date", "performance_model", "maintenance_type"]].copy()
    actual["asset"] = _asset_strings(actual["asset"])
    merged = actual.merge(predictions, on=["asset", "date"], how="inner")
    valid = merged.dropna(subset=["performance_model", "prediction"]).copy()
    error = valid["performance_model"] - valid["prediction"]

    valid["month"] = pd.to_datetime(valid["date"]).dt.to_period("M")
    monthly = (
        valid.groupby(["asset", "month"])[["performance_model", "prediction"]]
        .mean()
        .reset_index()
    )
    monthly_error = monthly["performance_model"] - monthly["prediction"]

    rolling_errors: list[float] = []
    gain7_errors: list[float] = []
    gain30_errors: list[float] = []
    prediction_lookup = predictions.set_index(["asset", "date"])["prediction"]
    for asset in ASSETS:
        block = full_panel.loc[_asset_strings(full_panel["asset"]) == asset].sort_values("date").copy()
        block["asset"] = asset
        stitched = block["performance_model"].copy()
        test_mask = block["date"] > cutoff
        keys = pd.MultiIndex.from_arrays(
            [np.repeat(asset, int(test_mask.sum())), block.loc[test_mask, "date"]]
        )
        stitched.loc[test_mask] = prediction_lookup.reindex(keys).to_numpy()
        actual_rolling = block["performance_model"].rolling(365, min_periods=330).mean()
        predicted_rolling = stitched.rolling(365, min_periods=330).mean()
        compare = test_mask & actual_rolling.notna() & predicted_rolling.notna()
        rolling_errors.extend((actual_rolling.loc[compare] - predicted_rolling.loc[compare]).tolist())

        asset_predictions = predictions.loc[predictions["asset"] == asset].set_index("date")[
            "prediction"
        ]
        for event in block.loc[
            block["maintenance_type"].notna() & (block["date"] > cutoff + pd.Timedelta(days=7))
        ].itertuples(index=False):
            delta = (block["date"] - event.date).dt.days
            pre = block.loc[delta.between(-7, -1)]
            post7 = block.loc[delta.between(1, 7)]
            post30 = block.loc[delta.between(8, 30)]
            if len(pre) >= 4 and len(post7) >= 4:
                dates = pd.concat([pre["date"], post7["date"]])
                predicted = asset_predictions.reindex(dates)
                if predicted.notna().all():
                    predicted_pre = predicted.iloc[: len(pre)].mean()
                    predicted_post = predicted.iloc[len(pre) :].mean()
                    actual_gain = post7["performance_model"].mean() - pre["performance_model"].mean()
                    gain7_errors.append(float(actual_gain - (predicted_post - predicted_pre)))
            if len(pre) >= 4 and len(post30) >= 10:
                dates = pd.concat([pre["date"], post30["date"]])
                predicted = asset_predictions.reindex(dates)
                if predicted.notna().all():
                    predicted_pre = predicted.iloc[: len(pre)].mean()
                    predicted_post = predicted.iloc[len(pre) :].mean()
                    actual_gain = post30["performance_model"].mean() - pre["performance_model"].mean()
                    gain30_errors.append(float(actual_gain - (predicted_post - predicted_pre)))

    return {
        "n_test": len(valid),
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(np.square(error)))),
        "monthly_rmse": float(np.sqrt(np.mean(np.square(monthly_error)))),
        "rolling_365_rmse": (
            float(np.sqrt(np.mean(np.square(rolling_errors)))) if rolling_errors else np.nan
        ),
        "post_1_7_gain_mae": (
            float(np.mean(np.abs(gain7_errors))) if gain7_errors else np.nan
        ),
        "post_8_30_gain_mae": (
            float(np.mean(np.abs(gain30_errors))) if gain30_errors else np.nan
        ),
    }


def rolling_origin_backtest(panel: pd.DataFrame) -> pd.DataFrame:
    """比较独立线性、SARIMAX 与分层状态模型，不使用随机切分。"""

    work = prepare_analysis_panel(panel)
    last_date = pd.to_datetime(work["date"]).max()
    rows: list[dict[str, Any]] = []
    for horizon in BACKTEST_HORIZONS_DAYS:
        cutoff = last_date - pd.Timedelta(days=horizon)
        train = work.loc[work["date"] <= cutoff].copy()
        test = work.loc[work["date"] > cutoff].copy()

        independent = fit_panel_models(train)["full"]
        valid_test = test.loc[test["performance_model"].notna()].copy()
        independent_predictions = pd.DataFrame(
            {
                "asset": _asset_strings(valid_test["asset"]),
                "date": valid_test["date"].to_numpy(),
                "prediction": independent.predict(valid_test),
            }
        )

        state_model = fit_hierarchical_state_model(train, reference_date=work["date"].min())
        state_predictions = pd.DataFrame(
            {
                "asset": _asset_strings(valid_test["asset"]),
                "date": valid_test["date"].to_numpy(),
                "prediction": state_model.predict(valid_test),
            }
        )
        sarimax_predictions = _sarimax_prediction(train, test)

        for model_name, predictions in (
            ("independent_linear", independent_predictions),
            ("sarimax_ar1", sarimax_predictions),
            ("hierarchical_state", state_predictions),
        ):
            metrics = _prediction_metrics(work, test, predictions, cutoff)
            rows.append(
                {
                    "split": f"holdout_{horizon}d",
                    "train_end": cutoff,
                    "test_end": last_date,
                    "horizon_days": horizon,
                    "model": model_name,
                    **metrics,
                }
            )
    return pd.DataFrame(rows)


def leave_one_asset_validation(panel: pd.DataFrame, calibration_days: int = 120) -> pd.DataFrame:
    """留一设备后，仅用该设备前 120 日校准截距和早期漂移。"""

    work = prepare_analysis_panel(panel)
    reference = pd.to_datetime(work["date"]).min()
    rows = []
    for held_out in ASSETS:
        training = work.loc[_asset_strings(work["asset"]) != held_out].copy()
        held = work.loc[_asset_strings(work["asset"]) == held_out].sort_values("date").copy()
        if held.empty:
            continue
        model = fit_hierarchical_state_model(training, reference_date=reference)
        cutoff = held["date"].min() + pd.Timedelta(days=calibration_days - 1)
        calibration = held.loc[
            (held["date"] <= cutoff) & held["performance_model"].notna()
        ].copy()
        test = held.loc[(held["date"] > cutoff) & held["performance_model"].notna()].copy()
        shared_names = list(MODEL_FEATURES)
        shared = np.column_stack(
            [_ensure_state_features(calibration, reference)[name] for name in shared_names]
        )
        shared_beta = np.array([model.parameter(name) for name in shared_names])
        common_decay = model.parameter("common_degradation")
        time_cal = (
            (calibration["date"] - reference).dt.days.to_numpy(dtype=float) / ANNUAL_PERIOD_DAYS
        )
        transient_cal = 1.0 - np.exp(-np.maximum(time_cal, 0.0) / model.transient_time_years)
        target = (
            calibration["performance_model"].to_numpy(dtype=float)
            - np.sum(shared * shared_beta[np.newaxis, :], axis=1)
            + common_decay * time_cal
        )
        calibration_design = np.column_stack([np.ones(len(calibration)), transient_cal])
        intercept, transient = np.linalg.lstsq(calibration_design, target, rcond=None)[0]

        test_features = _ensure_state_features(test, reference)
        shared_test = test_features.loc[:, shared_names].to_numpy(dtype=float)
        time_test = test_features["time_years"].to_numpy(dtype=float)
        transient_test = 1.0 - np.exp(-np.maximum(time_test, 0.0) / model.transient_time_years)
        prediction = (
            intercept
            - common_decay * time_test
            + transient * transient_test
            + np.sum(shared_test * shared_beta[np.newaxis, :], axis=1)
        )
        error = test["performance_model"].to_numpy(dtype=float) - prediction
        rows.append(
            {
                "asset": held_out,
                "calibration_days": calibration_days,
                "n_test": len(test),
                "mae": float(np.mean(np.abs(error))),
                "rmse": float(np.sqrt(np.mean(np.square(error)))),
                "borrowed_common_degradation_per_year": common_decay,
            }
        )
    return pd.DataFrame(rows)


def estimate_fixed_schedule(maintenance: pd.DataFrame) -> pd.DataFrame:
    """把附件维护记录转为逐设备固定间隔和大维护频率。"""

    ordered = maintenance.sort_values(["asset", "maintenance_date"]).copy()
    global_major_events = int((ordered["maintenance_type"] == "major").sum())
    global_major_every = max(int(round(len(ordered) / max(global_major_events, 1))), 2)
    rows = []
    for asset in ASSETS:
        block = ordered.loc[ordered["asset"] == asset].reset_index(drop=True)
        intervals = block["maintenance_date"].diff().dt.days.dropna()
        interval_days = int(round(float(intervals.median()))) if len(intervals) else 57
        major_positions = block.index[block["maintenance_type"] == "major"].tolist()
        if major_positions:
            major_every = max(int(round(len(block) / len(major_positions))), 2)
            major_source = "asset_history"
            events_since_major = len(block) - 1 - major_positions[-1]
        else:
            major_every = global_major_every
            major_source = "cohort_imputed_no_recorded_major"
            events_since_major = 0
        rows.append(
            {
                "asset": asset,
                "observed_events": len(block),
                "observed_major_events": len(major_positions),
                "interval_days": interval_days,
                "interval_q25_days": float(intervals.quantile(0.25)) if len(intervals) else np.nan,
                "interval_q75_days": float(intervals.quantile(0.75)) if len(intervals) else np.nan,
                "major_every_events": major_every,
                "major_frequency_source": major_source,
                "events_since_major_at_origin": events_since_major,
                "last_recorded_event_date": block["maintenance_date"].max(),
                "last_recorded_event_type": block.iloc[-1]["maintenance_type"],
            }
        )
    return pd.DataFrame(rows)


def build_future_frame(
    policy: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    reference_date: pd.Timestamp,
) -> pd.DataFrame:
    """按逐设备固定规律生成未来维护日历和状态特征。"""

    parts = []
    for row in policy.itertuples(index=False):
        dates = pd.date_range(pd.Timestamp(start_date) + pd.Timedelta(days=1), end_date, freq="D")
        events: dict[pd.Timestamp, str] = {}
        event_date = pd.Timestamp(row.last_recorded_event_date)
        count_since_major = int(row.events_since_major_at_origin)
        while event_date <= end_date:
            event_date += pd.Timedelta(days=int(row.interval_days))
            if count_since_major + 1 >= int(row.major_every_events):
                event_type = "major"
                count_since_major = 0
            else:
                event_type = "medium"
                count_since_major += 1
            if event_date > start_date and event_date <= end_date:
                events[event_date] = event_type
        block = pd.DataFrame({"asset": row.asset, "date": dates})
        block["maintenance_type"] = block["date"].map(events)
        block["last_maintenance_date"] = block["date"].where(
            block["maintenance_type"].notna()
        )
        seed_last = pd.Timestamp(row.last_recorded_event_date)
        if len(block):
            block.loc[block.index[0], "last_maintenance_date"] = (
                block.loc[block.index[0], "last_maintenance_date"]
                if pd.notna(block.loc[block.index[0], "last_maintenance_date"])
                else seed_last
            )
        block["last_maintenance_date"] = block["last_maintenance_date"].ffill()
        block["days_since_maintenance"] = (
            block["date"] - block["last_maintenance_date"]
        ).dt.days
        parts.append(block)
    future = pd.concat(parts, ignore_index=True)
    return _ensure_state_features(future, reference_date)


def _attach_historical_rolling(
    history: pd.DataFrame,
    future: pd.DataFrame,
    value_col: str = "performance_forecast",
) -> pd.DataFrame:
    parts = []
    for asset in ASSETS:
        past = history.loc[_asset_strings(history["asset"]) == asset].sort_values("date").copy()
        forecast = future.loc[_asset_strings(future["asset"]) == asset].sort_values("date").copy()
        past_values = past["performance_model"].interpolate(limit_direction="both")
        combined = pd.concat(
            [
                pd.DataFrame({"date": past["date"], "value": past_values}),
                pd.DataFrame({"date": forecast["date"], "value": forecast[value_col]}),
            ],
            ignore_index=True,
        )
        rolling = combined["value"].rolling(ROLLING_YEAR_DAYS, min_periods=ROLLING_YEAR_DAYS).mean()
        forecast["rolling_annual_mean"] = rolling.iloc[-len(forecast) :].to_numpy()
        parts.append(forecast)
    return pd.concat(parts, ignore_index=True)


def joint_failure_dates(
    forecast: pd.DataFrame,
    recovery_level: float = LIFETIME_THRESHOLD,
) -> pd.DataFrame:
    """联合判据：年均低于 37，且随后大维护 8—30 日均值仍低于恢复线。"""

    rows = []
    for asset, block in forecast.groupby("asset"):
        ordered = block.sort_values("date").reset_index(drop=True)
        crossing = ordered.index[ordered["rolling_annual_mean"] < LIFETIME_THRESHOLD]
        threshold_date = pd.NaT
        diagnostic_major_date = pd.NaT
        post_major_mean = np.nan
        failure_date = pd.NaT
        if len(crossing):
            first_index = int(crossing[0])
            threshold_date = ordered.loc[first_index, "date"]
            major_indices = ordered.index[
                (ordered.index >= first_index) & (ordered["maintenance_type"] == "major")
            ]
            for major_index in major_indices:
                post = ordered.loc[
                    (ordered.index >= major_index + 8) & (ordered.index <= major_index + 30),
                    "performance_forecast",
                ]
                if len(post) >= 20 and float(post.mean()) < recovery_level:
                    diagnostic_major_date = ordered.loc[major_index, "date"]
                    post_major_mean = float(post.mean())
                    failure_date = ordered.loc[major_index + 30, "date"]
                    break
        rows.append(
            {
                "asset": asset,
                "candidate_threshold_date": threshold_date,
                "diagnostic_major_date": diagnostic_major_date,
                "post_major_8_30_mean": post_major_mean,
                "joint_failure_date": failure_date,
                "recovery_level": recovery_level,
            }
        )
    return pd.DataFrame(rows)


def structural_sensitivity_models(panel: pd.DataFrame) -> tuple[list[HierarchicalStateModel], pd.DataFrame]:
    """用可解释的超参数组构造结构不确定性集合。"""

    specifications = (
        (400.0, 1.0, 5.0),
        (400.0, 2.0, 5.0),
        (400.0, 4.0, 5.0),
        (1600.0, 1.0, 2.0),
        (1600.0, 2.0, 5.0),
        (1600.0, 4.0, 10.0),
        (5000.0, 1.0, 5.0),
        (5000.0, 2.0, 5.0),
        (5000.0, 4.0, 5.0),
    )
    reference = pd.to_datetime(panel["date"]).min()
    models = []
    rows = []
    for model_id, (shrinkage, transient_years, transient_penalty) in enumerate(specifications):
        model = fit_hierarchical_state_model(
            panel,
            shrinkage=shrinkage,
            transient_time_years=transient_years,
            transient_penalty=transient_penalty,
            reference_date=reference,
        )
        models.append(model)
        for asset in ASSETS:
            rows.append(
                {
                    "model_id": model_id,
                    "asset": asset,
                    "shrinkage": shrinkage,
                    "transient_time_years": transient_years,
                    "transient_penalty": transient_penalty,
                    "degradation_per_year": model.parameter(f"degradation:{asset}"),
                    "common_degradation_per_year": model.parameter("common_degradation"),
                    "weighted_rmse": model.weighted_rmse,
                    "r_squared": model.r_squared,
                }
            )
    return models, pd.DataFrame(rows)


def residual_outlier_sensitivity(
    panel: pd.DataFrame,
    main_model: HierarchicalStateModel,
    residual_outliers: pd.DataFrame,
) -> tuple[HierarchicalStateModel, pd.DataFrame]:
    """比较保留与排除问题一残差异常日时的长期退化率。"""

    flagged = residual_outliers.copy()
    flagged["date"] = pd.to_datetime(flagged["date"], errors="coerce")
    if "is_residual_outlier" in flagged:
        flag = flagged["is_residual_outlier"]
        if flag.dtype == object:
            flag = flag.astype(str).str.lower().isin({"true", "1", "yes"})
        flagged = flagged.loc[flag.astype(bool)]
    keys = pd.MultiIndex.from_frame(flagged[["asset", "date"]].drop_duplicates())
    work = panel.copy()
    work["asset"] = _asset_strings(work["asset"])
    work["date"] = pd.to_datetime(work["date"])
    panel_keys = pd.MultiIndex.from_frame(work[["asset", "date"]])
    clean = work.loc[~panel_keys.isin(keys)].copy()
    clean_model = fit_hierarchical_state_model(
        clean,
        reference_date=main_model.reference_date,
        shrinkage=main_model.shrinkage,
        transient_time_years=main_model.transient_time_years,
        transient_penalty=main_model.transient_penalty,
    )
    rows = []
    for asset in ASSETS:
        main_rate = main_model.parameter(f"degradation:{asset}")
        clean_rate = clean_model.parameter(f"degradation:{asset}")
        rows.append(
            {
                "asset": asset,
                "flagged_days_removed": int(
                    ((flagged["asset"] == asset) & flagged["date"].notna()).sum()
                ),
                "degradation_with_outliers": main_rate,
                "degradation_without_outliers": clean_rate,
                "absolute_difference": clean_rate - main_rate,
                "relative_difference": (
                    (clean_rate - main_rate) / main_rate if main_rate > 0.0 else np.nan
                ),
            }
        )
    return clean_model, pd.DataFrame(rows)


def _censored_quantile_index(indices: np.ndarray, horizon: int, probability: float) -> int | None:
    filled = np.where(indices >= 0, indices, horizon)
    result = int(np.quantile(filled, probability, method="higher"))
    return None if result >= horizon else result


def simulate_lifetime_distribution(
    history: pd.DataFrame,
    future: pd.DataFrame,
    scenario_models: Sequence[HierarchicalStateModel],
    paths: int = SIMULATION_PATHS,
    seed: int = SIMULATION_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """在结构模型集合上做蒙特卡洛外推，返回寿命、判据和预测带。"""

    rng = np.random.default_rng(seed)
    lifetime_rows = []
    sensitivity_rows = []
    band_rows = []
    commission = pd.Timestamp(COMMISSION_DATE)
    forecast_origin = pd.to_datetime(history["date"]).max()

    for asset in ASSETS:
        block = future.loc[_asset_strings(future["asset"]) == asset].sort_values("date").reset_index(drop=True)
        dates = pd.DatetimeIndex(block["date"])
        horizon = len(block)
        elapsed_years = (dates - forecast_origin).days.to_numpy(dtype=float) / ANNUAL_PERIOD_DAYS
        scenario_paths = np.vstack([model.predict(block) for model in scenario_models])
        scenario_degradation = np.array(
            [model.parameter(f"degradation:{asset}") for model in scenario_models], dtype=float
        )
        scenario_residual = np.array([model.residual_std for model in scenario_models], dtype=float)
        choices = rng.integers(0, len(scenario_models), size=paths)
        degradation_multiplier = np.exp(rng.normal(-0.5 * 0.10**2, 0.10, size=paths))
        chosen_degradation = scenario_degradation[choices]
        degradation_draw = chosen_degradation * degradation_multiplier
        level_shift = rng.normal(0.0, scenario_residual[choices] / np.sqrt(60.0), size=paths)

        past = history.loc[_asset_strings(history["asset"]) == asset].sort_values("date")
        past_values = past["performance_model"].interpolate(limit_direction="both").to_numpy(dtype=float)
        past_values = past_values[-(ROLLING_YEAR_DAYS - 1) :]
        if len(past_values) < ROLLING_YEAR_DAYS - 1:
            raise ValueError(f"设备 {asset} 缺少滚动年均所需历史窗口")

        failure_by_level = {
            level: np.full(paths, -1, dtype=int) for level in RECOVERY_LEVELS
        }
        crossing_indices = np.full(paths, -1, dtype=int)
        month_indices = np.flatnonzero(dates.is_month_end)
        monthly_samples = np.empty((paths, len(month_indices)), dtype=float)
        major_indices = np.flatnonzero(block["maintenance_type"].eq("major").to_numpy())

        chunk_size = 100
        for start in range(0, paths, chunk_size):
            stop = min(start + chunk_size, paths)
            selected = choices[start:stop]
            prediction = scenario_paths[selected].copy()
            delta = degradation_draw[start:stop] - chosen_degradation[start:stop]
            prediction -= delta[:, np.newaxis] * elapsed_years[np.newaxis, :]
            prediction += level_shift[start:stop, np.newaxis]

            historical = np.broadcast_to(past_values, (stop - start, len(past_values)))
            combined = np.concatenate([historical, prediction], axis=1)
            cumulative = np.cumsum(
                np.concatenate([np.zeros((stop - start, 1)), combined], axis=1),
                axis=1,
            )
            rolling = (
                cumulative[:, ROLLING_YEAR_DAYS:]
                - cumulative[:, :-ROLLING_YEAR_DAYS]
            ) / ROLLING_YEAR_DAYS
            monthly_samples[start:stop] = rolling[:, month_indices]
            below = rolling < LIFETIME_THRESHOLD
            has_crossing = below.any(axis=1)
            local_crossing = np.where(has_crossing, below.argmax(axis=1), -1)
            crossing_indices[start:stop] = local_crossing

            for local_index, crossing in enumerate(local_crossing):
                if crossing < 0:
                    continue
                candidate_majors = major_indices[major_indices >= crossing]
                for level in RECOVERY_LEVELS:
                    for major_index in candidate_majors:
                        if major_index + 30 >= horizon:
                            break
                        post_mean = float(prediction[local_index, major_index + 8 : major_index + 31].mean())
                        if post_mean < level:
                            failure_by_level[level][start + local_index] = major_index + 30
                            break

        for month_column, date_index in enumerate(month_indices):
            values = monthly_samples[:, month_column]
            band_rows.append(
                {
                    "asset": asset,
                    "date": dates[date_index],
                    "rolling_p10": float(np.quantile(values, 0.10)),
                    "rolling_p50": float(np.quantile(values, 0.50)),
                    "rolling_p90": float(np.quantile(values, 0.90)),
                }
            )

        nominal = failure_by_level[LIFETIME_THRESHOLD]
        quantile_indices = {
            "p025": _censored_quantile_index(nominal, horizon, 0.025),
            "p10": _censored_quantile_index(nominal, horizon, 0.10),
            "p50": _censored_quantile_index(nominal, horizon, 0.50),
            "p90": _censored_quantile_index(nominal, horizon, 0.90),
            "p975": _censored_quantile_index(nominal, horizon, 0.975),
        }

        def date_at(index: int | None) -> pd.Timestamp:
            return pd.NaT if index is None else pd.Timestamp(dates[index])

        median_date = date_at(quantile_indices["p50"])
        lifetime_rows.append(
            {
                "asset": asset,
                "forecast_origin": forecast_origin,
                "simulation_paths": paths,
                "horizon_end": dates[-1],
                "median_failure_date": median_date,
                "p10_failure_date": date_at(quantile_indices["p10"]),
                "p90_failure_date": date_at(quantile_indices["p90"]),
                "p025_failure_date": date_at(quantile_indices["p025"]),
                "p975_failure_date": date_at(quantile_indices["p975"]),
                "median_total_lifetime_years": (
                    float((median_date - commission).days / ANNUAL_PERIOD_DAYS)
                    if pd.notna(median_date)
                    else np.nan
                ),
                "median_remaining_years": (
                    float((median_date - forecast_origin).days / ANNUAL_PERIOD_DAYS)
                    if pd.notna(median_date)
                    else np.nan
                ),
                "censored_rate_at_horizon": float(np.mean(nominal < 0)),
                "median_threshold_crossing_date": date_at(
                    _censored_quantile_index(crossing_indices, horizon, 0.50)
                ),
            }
        )
        for level, failure_indices in failure_by_level.items():
            median_index = _censored_quantile_index(failure_indices, horizon, 0.50)
            median_failure = date_at(median_index)
            sensitivity_rows.append(
                {
                    "asset": asset,
                    "post_major_recovery_level": level,
                    "median_failure_date": median_failure,
                    "median_total_lifetime_years": (
                        float((median_failure - commission).days / ANNUAL_PERIOD_DAYS)
                        if pd.notna(median_failure)
                        else np.nan
                    ),
                    "censored_rate_at_horizon": float(np.mean(failure_indices < 0)),
                }
            )

    return (
        pd.DataFrame(lifetime_rows),
        pd.DataFrame(sensitivity_rows),
        pd.DataFrame(band_rows),
    )


def plot_backtest(backtest: pd.DataFrame) -> Path:
    summary = backtest.groupby("model", as_index=False)["rmse"].mean()
    labels = {
        "independent_linear": "设备独立线性",
        "sarimax_ar1": "SARIMAX-AR(1)",
        "hierarchical_state": "分层退化状态",
    }
    summary["模型"] = summary["model"].map(labels)
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    sns.barplot(data=summary, x="模型", y="rmse", color="#3f77b5", ax=ax)
    ax.set_ylabel("滚动留出日预测 RMSE")
    ax.set_xlabel("")
    ax.set_title("问题二候选模型时间留出比较")
    for patch, value in zip(ax.patches, summary["rmse"]):
        ax.text(patch.get_x() + patch.get_width() / 2, value + 0.2, f"{value:.2f}", ha="center")
    return _save_figure(fig, "q2_01_backtest.png")


def plot_degradation_sensitivity(
    parameters: pd.DataFrame,
    main_model: HierarchicalStateModel,
) -> Path:
    grouped = parameters.groupby("asset")["degradation_per_year"]
    summary = grouped.quantile([0.1, 0.9]).unstack()
    summary.columns = ["low", "high"]
    summary["main"] = [main_model.parameter(f"degradation:{asset}") for asset in summary.index]
    summary = summary.reindex(ASSETS)
    x = np.arange(len(summary))
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.errorbar(
        x,
        summary["main"],
        yerr=np.vstack([summary["main"] - summary["low"], summary["high"] - summary["main"]]),
        fmt="o",
        color="#2457a7",
        ecolor="#7ba3d1",
        capsize=4,
    )
    ax.set_xticks(x, summary.index)
    ax.set_ylabel("长期不可逆退化率（透水率单位/年）")
    ax.set_title("分层状态模型的设备退化率与结构敏感区间")
    return _save_figure(fig, "q2_02_degradation_rates.png")


def plot_forecast_bands(bands: pd.DataFrame, lifetimes: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(5, 2, figsize=(14, 18), sharex=True, sharey=True)
    lifetime_lookup = lifetimes.set_index("asset")
    display_end = pd.to_datetime(lifetimes["p90_failure_date"]).max() + pd.DateOffset(years=2)
    for ax, asset in zip(axes.ravel(), ASSETS):
        block = bands.loc[
            (bands["asset"] == asset) & (pd.to_datetime(bands["date"]) <= display_end)
        ].sort_values("date")
        x = pd.to_datetime(block["date"])
        ax.fill_between(
            mdates.date2num(x),
            block["rolling_p10"].clip(lower=0.0).to_numpy(),
            block["rolling_p90"].clip(lower=0.0).to_numpy(),
            color="#8db8df",
            alpha=0.35,
        )
        ax.plot(x, block["rolling_p50"].clip(lower=0.0), color="#2457a7", lw=1.4)
        ax.axhline(LIFETIME_THRESHOLD, color="#c43c39", ls="--", lw=1.0)
        failure = lifetime_lookup.loc[asset, "median_failure_date"]
        if pd.notna(failure):
            ax.axvline(pd.Timestamp(failure), color="#d95f02", ls=":", lw=1.2)
        ax.set_title(asset)
        ax.set_ylim(0.0, 125.0)
        ax.xaxis.set_major_locator(mdates.YearLocator(3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for ax in axes[-1]:
        ax.tick_params(axis="x", rotation=30)
    fig.suptitle("现行维护规律下滚动年均透水率预测（失效判据附近）", fontsize=18, y=0.995)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    handles = [
        Patch(facecolor="#8db8df", alpha=0.35, label="80%区间"),
        Line2D([0], [0], color="#2457a7", lw=1.5, label="中位路径"),
        Line2D([0], [0], color="#c43c39", ls="--", label="阈值37"),
        Line2D([0], [0], color="#d95f02", ls=":", label="寿命中位数"),
    ]
    fig.legend(
        handles=handles,
        loc="upper center",
        ncol=4,
        bbox_to_anchor=(0.5, 0.978),
        frameon=False,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return _save_figure(fig, "q2_03_lifetime_forecast.png")


def plot_lifetime_summary(lifetimes: pd.DataFrame) -> Path:
    commission = pd.Timestamp(COMMISSION_DATE)
    work = lifetimes.copy().set_index("asset").reindex(ASSETS)
    for name in ("p10", "p50", "p90"):
        column = "median_failure_date" if name == "p50" else f"{name}_failure_date"
        work[name] = (
            pd.to_datetime(work[column]) - commission
        ).dt.days / ANNUAL_PERIOD_DAYS
    y = np.arange(len(work))
    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    ax.hlines(y, work["p10"], work["p90"], color="#7ba3d1", lw=5, alpha=0.7)
    ax.scatter(work["p50"], y, color="#2457a7", s=50, zorder=3)
    ax.set_yticks(y, work.index)
    ax.invert_yaxis()
    ax.set_xlabel("自 2022-04-01 投用起的总寿命（年）")
    ax.set_title("十台设备寿命中位数与80%预测区间")
    return _save_figure(fig, "q2_04_lifetime_summary.png")


def run_q2_formal(
    *,
    simulation_paths: int = SIMULATION_PATHS,
    forecast_horizon_years: int = FORECAST_HORIZON_YEARS,
) -> Dict[str, Any]:
    """运行问题二完整流程并保存可追溯结果、图形和关键结论。"""

    ensure_output_dirs()
    panel_path = PROCESSED_DIR / "daily_panel.csv"
    if not panel_path.is_file():
        run_q1_scaffold()
    raw_panel = pd.read_csv(panel_path, parse_dates=["date", "last_maintenance_date"])
    panel = prepare_analysis_panel(raw_panel)
    maintenance = load_maintenance()

    backtest = rolling_origin_backtest(raw_panel)
    leave_one = leave_one_asset_validation(raw_panel)
    main_model = fit_hierarchical_state_model(panel, reference_date=panel["date"].min())
    parameters = state_parameter_table(main_model)
    outlier_path = RESULTS_DIR / "q1_residual_outliers.csv"
    residual_outliers = (
        pd.read_csv(outlier_path, parse_dates=["date"])
        if outlier_path.is_file()
        else pd.DataFrame(columns=["asset", "date", "is_residual_outlier"])
    )
    clean_model, outlier_sensitivity = residual_outlier_sensitivity(
        panel,
        main_model,
        residual_outliers,
    )
    policy = estimate_fixed_schedule(maintenance)
    forecast_origin = pd.to_datetime(panel["date"]).max()
    forecast_end = forecast_origin + pd.DateOffset(years=forecast_horizon_years)
    future = build_future_frame(policy, forecast_origin, forecast_end, main_model.reference_date)
    future["performance_forecast"] = main_model.predict(future)
    point_forecast = _attach_historical_rolling(panel, future)
    point_failures = joint_failure_dates(point_forecast)

    scenario_models, structural = structural_sensitivity_models(panel)
    scenario_models.append(clean_model)
    lifetimes, lifetime_sensitivity, forecast_bands = simulate_lifetime_distribution(
        panel,
        future,
        scenario_models,
        paths=simulation_paths,
    )
    lifetimes = lifetimes.merge(
        point_failures[
            ["asset", "candidate_threshold_date", "joint_failure_date", "post_major_8_30_mean"]
        ],
        on="asset",
        how="left",
    ).merge(
        policy[
            [
                "asset",
                "interval_days",
                "major_every_events",
                "major_frequency_source",
            ]
        ],
        on="asset",
        how="left",
    )

    output_tables = {
        "q2_model_backtest.csv": backtest,
        "q2_leave_one_asset_validation.csv": leave_one,
        "q2_state_parameters.csv": parameters,
        "q2_structural_sensitivity.csv": structural,
        "q2_outlier_sensitivity.csv": outlier_sensitivity,
        "q2_fixed_schedule.csv": policy,
        "q2_forecast_paths.csv": point_forecast,
        "q2_forecast_bands.csv": forecast_bands,
        "q2_lifetime_summary.csv": lifetimes,
        "q2_lifetime_sensitivity.csv": lifetime_sensitivity,
    }
    for name, frame in output_tables.items():
        frame.to_csv(RESULTS_DIR / name, index=False, date_format="%Y-%m-%d")

    _configure_plot_style()
    figures = [
        plot_backtest(backtest),
        plot_degradation_sensitivity(structural, main_model),
        plot_forecast_bands(forecast_bands, lifetimes),
        plot_lifetime_summary(lifetimes),
    ]

    backtest_summary = backtest.groupby("model")["rmse"].mean().to_dict()
    finite_lifetimes = lifetimes.dropna(subset=["median_total_lifetime_years"])
    key_findings = {
        "forecast_origin": str(forecast_origin.date()),
        "observation_start": str(pd.to_datetime(panel["date"]).min().date()),
        "observation_end": str(forecast_origin.date()),
        "lifetime_definition": (
            "rolling 365-day mean below 37 and the following major maintenance "
            "has post-day-8-to-30 mean below 37"
        ),
        "main_model": "nonnegative hierarchical degradation with saturating transient drift",
        "state_model_r_squared": main_model.r_squared,
        "state_model_weighted_rmse": main_model.weighted_rmse,
        "common_degradation_per_year": main_model.parameter("common_degradation"),
        "mean_backtest_rmse_by_model": backtest_summary,
        "leave_one_asset_mean_rmse": float(leave_one["rmse"].mean()),
        "max_outlier_exclusion_rate_change": float(
            outlier_sensitivity["relative_difference"].abs().max()
        ),
        "simulation_paths": simulation_paths,
        "forecast_horizon_years": forecast_horizon_years,
        "earliest_median_asset": (
            finite_lifetimes.sort_values("median_total_lifetime_years").iloc[0]["asset"]
            if len(finite_lifetimes)
            else None
        ),
        "earliest_median_total_lifetime_years": (
            float(finite_lifetimes["median_total_lifetime_years"].min())
            if len(finite_lifetimes)
            else None
        ),
        "latest_median_asset": (
            finite_lifetimes.sort_values("median_total_lifetime_years").iloc[-1]["asset"]
            if len(finite_lifetimes)
            else None
        ),
        "latest_median_total_lifetime_years": (
            float(finite_lifetimes["median_total_lifetime_years"].max())
            if len(finite_lifetimes)
            else None
        ),
        "limitations": [
            "no observed lifetime termination; results are degradation-threshold extrapolations",
            "A4 and A8 have no recorded major maintenance; cohort major frequency is imputed",
            "small maintenance is unrecorded and absorbed into the background state",
            "prediction intervals include structural model choices but cannot cover unknown regime changes",
        ],
    }
    with (RESULTS_DIR / "q2_key_findings.json").open("w", encoding="utf-8") as file:
        json.dump(key_findings, file, ensure_ascii=False, indent=2)

    return {
        "backtest": backtest,
        "leave_one_asset": leave_one,
        "main_model": main_model,
        "parameters": parameters,
        "policy": policy,
        "point_forecast": point_forecast,
        "lifetimes": lifetimes,
        "lifetime_sensitivity": lifetime_sensitivity,
        "forecast_bands": forecast_bands,
        "figures": figures,
        "key_findings": key_findings,
    }


def fit_and_forecast_fixed_schedule(*args: Any, **kwargs: Any) -> pd.DataFrame:
    """兼容早期接口：返回现行维护规律下的日级点预测。"""

    outputs = run_q2_formal(*args, **kwargs)
    return outputs["point_forecast"]
