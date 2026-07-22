"""问题三：分类维护响应、可解释策略搜索与全生命周期年均成本。

问题二的状态模型提供长期退化、季节和“任意一次有记录维护”后的
通用污染重置。本模块在其上增加中/大维护的类型修正、维护损伤情景和
任意维护日历，先用点估计搜索策略，再对前沿方案做蒙特卡复验。
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

# Matplotlib 必须在导入 pyplot 前指定可写缓存目录。
_CACHE_ROOT = Path(tempfile.gettempdir()) / "math2026-filter-monitoring"
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(_CACHE_ROOT / "xdg"))

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import (
    ASSETS,
    BASE_COSTS,
    COMMISSION_DATE,
    LIFETIME_THRESHOLD,
    PROCESSED_DIR,
    RESULTS_DIR,
    ROLLING_YEAR_DAYS,
    CostConfig,
    ensure_output_dirs,
)
from .io import load_maintenance
from .q1_analysis import (
    ANNUAL_PERIOD_DAYS,
    _configure_plot_style,
    _save_figure,
    prepare_analysis_panel,
    run_q1_formal,
    run_q1_scaffold,
)
from .q2_lifetime import (
    FORECAST_HORIZON_YEARS,
    HierarchicalStateModel,
    _ensure_state_features,
    build_future_frame,
    estimate_fixed_schedule,
    fit_hierarchical_state_model,
    residual_outlier_sensitivity,
    structural_sensitivity_models,
)


SEARCH_SEED = 20260725
VALIDATION_SEED = 20260726
SCREENING_PATHS = 200
FINAL_PATHS = 2000
VALIDATION_PATHS = 1000
RESPONSE_SHRINKAGE_EVENTS = 20.0
DAMAGE_SHARES = (0.0, 0.15, 0.30)
MAIN_DAMAGE_SHARE = 0.15
MAJOR_DAMAGE_MULTIPLIER = 4.0
RESPONSE_SCENARIOS = ("shrunk", "empirical", "major_equal")


@dataclass(frozen=True)
class PolicyOutcome:
    """一条更新周期内的寿命和维护次数。"""

    lifetime_days: float
    medium_events: float
    major_events: float
    minor_events: float = 0.0


@dataclass(frozen=True)
class PolicySpec:
    """可解释维护策略。"""

    policy_id: str
    policy_kind: str
    medium_interval_days: int | None = None
    major_interval_days: int | None = None
    trigger_level: float | None = None
    cooldown_days: int | None = None
    description: str = ""


def annualized_lifecycle_cost(
    outcome: PolicyOutcome,
    costs: CostConfig = BASE_COSTS,
) -> float:
    """计算全生命周期年均成本，单位为万元/年。"""

    if outcome.lifetime_days <= 0:
        raise ValueError("设备寿命必须大于 0 天")
    lifecycle_cost = (
        costs.purchase
        + costs.medium * outcome.medium_events
        + costs.major * outcome.major_events
        + costs.minor * outcome.minor_events
    )
    return lifecycle_cost / (outcome.lifetime_days / 365.0)


def build_policy_space() -> tuple[PolicySpec, ...]:
    """构造周期规则和状态触发规则的搜索空间。"""

    specs: list[PolicySpec] = [
        PolicySpec(
            policy_id="current",
            policy_kind="current",
            description="附件维护间隔中位数与历史大维护比例",
        )
    ]
    # 搜索必须跨过现行 54—60 日区间且不在 120 天人为截断；
    # 365 天与每年一次大维护组合时等价于不做额外中维护。
    medium_intervals = (35, 45, 55, 65, 75, 90, 120, 150, 180, 240, 365)
    major_intervals = (91, 122, 183, 365)
    for medium in medium_intervals:
        for major in major_intervals:
            description = (
                "仅每年一次大维护，不安排额外中维护"
                if medium >= major == 365
                else f"每 {medium} 天检修，大维护最大间隔 {major} 天"
            )
            specs.append(
                PolicySpec(
                    policy_id=f"periodic_m{medium}_b{major}",
                    policy_kind="periodic",
                    medium_interval_days=medium,
                    major_interval_days=major,
                    cooldown_days=min(medium, 30),
                    description=description,
                )
            )
    for trigger in (40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0):
        for cooldown in (30, 45, 60):
            for major in major_intervals:
                specs.append(
                    PolicySpec(
                        policy_id=f"trigger_t{int(trigger)}_c{cooldown}_b{major}",
                        policy_kind="trigger",
                        major_interval_days=major,
                        trigger_level=trigger,
                        cooldown_days=cooldown,
                        description=(
                            f"未来30日预测低于 {trigger:.0f} 时中维护，"
                            f"冷却 {cooldown} 天，大维护最大间隔 {major} 天"
                        ),
                    )
                )
    return tuple(specs)


def policy_space_table(specs: Iterable[PolicySpec] | None = None) -> pd.DataFrame:
    rows = [asdict(spec) for spec in (specs or build_policy_space())]
    frame = pd.DataFrame(rows)
    frame["feasible_main"] = True
    frame["major_frequency_per_year"] = np.where(
        frame["major_interval_days"].notna(),
        ANNUAL_PERIOD_DAYS / frame["major_interval_days"],
        np.nan,
    )
    return frame


def estimate_maintenance_response(
    effects: pd.DataFrame,
    prior_events: float = RESPONSE_SHRINKAGE_EVENTS,
) -> pd.DataFrame:
    """将中/大维护事件效果向总体部分汇聚。"""

    required = {
        "maintenance_type",
        "recorded_events",
        "instant_mean",
        "instant_ci95_low",
        "instant_ci95_high",
        "retained_mean",
        "retained_ci95_low",
        "retained_ci95_high",
    }
    missing = required - set(effects.columns)
    if missing:
        raise ValueError(f"维护效果表缺少字段：{sorted(missing)}")
    work = effects.loc[effects["maintenance_type"].isin(["medium", "major"])].copy()
    if set(work["maintenance_type"]) != {"medium", "major"}:
        raise ValueError("维护效果表必须同时包含中维护和大维护")
    weights = work["recorded_events"].to_numpy(dtype=float)
    pooled_instant = float(np.average(work["instant_mean"], weights=weights))
    pooled_retained = float(np.average(work["retained_mean"], weights=weights))
    rows = []
    for row in work.itertuples(index=False):
        n = float(row.recorded_events)
        instant = float(row.instant_mean)
        retained = float(row.retained_mean)
        instant_shrunk = (n * instant + prior_events * pooled_instant) / (n + prior_events)
        retained_shrunk = (n * retained + prior_events * pooled_retained) / (n + prior_events)
        rows.append(
            {
                "maintenance_type": row.maintenance_type,
                "recorded_events": int(row.recorded_events),
                "instant_empirical": instant,
                "retained_empirical": retained,
                "instant_shrunk": instant_shrunk,
                "retained_shrunk": retained_shrunk,
                "instant_standard_error": (
                    float(row.instant_ci95_high) - float(row.instant_ci95_low)
                )
                / (2.0 * 1.96),
                "retained_standard_error": (
                    float(row.retained_ci95_high) - float(row.retained_ci95_low)
                )
                / (2.0 * 1.96),
                "pooled_instant": pooled_instant,
                "pooled_retained": pooled_retained,
                "prior_events": prior_events,
            }
        )
    return pd.DataFrame(rows).sort_values("maintenance_type").reset_index(drop=True)


def validate_maintenance_response(
    event_detail: pd.DataFrame,
    prior_events: float = RESPONSE_SHRINKAGE_EVENTS,
) -> pd.DataFrame:
    """留一设备检查类型效果向新设备的迁移误差。"""

    rows: list[dict[str, Any]] = []
    data = event_detail.copy()
    for held_asset in ASSETS:
        train = data.loc[data["asset"].astype(str) != held_asset]
        test = data.loc[data["asset"].astype(str) == held_asset]
        for maintenance_type in ("medium", "major"):
            for metric in ("instant_gain_adjusted", "retained_gain_adjusted"):
                train_metric = train.loc[
                    train["maintenance_type"].eq(maintenance_type), metric
                ].dropna()
                pooled = train[metric].dropna()
                actual = test.loc[
                    test["maintenance_type"].eq(maintenance_type), metric
                ].dropna()
                if len(actual) == 0 or len(train_metric) == 0 or len(pooled) == 0:
                    continue
                prediction = (
                    len(train_metric) * float(train_metric.mean())
                    + prior_events * float(pooled.mean())
                ) / (len(train_metric) + prior_events)
                for value in actual:
                    rows.append(
                        {
                            "held_asset": held_asset,
                            "maintenance_type": maintenance_type,
                            "metric": metric,
                            "actual": float(value),
                            "prediction": prediction,
                            "error": float(value) - prediction,
                        }
                    )
    detail = pd.DataFrame(rows)
    if detail.empty:
        return detail
    summary = (
        detail.groupby(["maintenance_type", "metric"], as_index=False)
        .agg(
            events=("error", "size"),
            mae=("error", lambda x: float(np.mean(np.abs(x)))),
            rmse=("error", lambda x: float(np.sqrt(np.mean(np.square(x))))),
            mean_error=("error", "mean"),
        )
    )
    return summary


def historical_maintenance_rates(
    maintenance: pd.DataFrame,
    forecast_origin: pd.Timestamp,
) -> pd.DataFrame:
    """计算观测期年频率和投用至预测原点的等价历史次数。"""

    observation_start = pd.to_datetime(maintenance["maintenance_date"]).min()
    observed_years = max(
        float((pd.Timestamp(forecast_origin) - observation_start).days / ANNUAL_PERIOD_DAYS),
        1.0,
    )
    elapsed_years = float(
        (pd.Timestamp(forecast_origin) - pd.Timestamp(COMMISSION_DATE)).days
        / ANNUAL_PERIOD_DAYS
    )
    rows = []
    global_major_rate = float(
        maintenance["maintenance_type"].eq("major").sum()
        / (len(ASSETS) * observed_years)
    )
    for asset in ASSETS:
        block = maintenance.loc[maintenance["asset"].astype(str) == asset]
        medium_rate = float(block["maintenance_type"].eq("medium").sum() / observed_years)
        major_count = int(block["maintenance_type"].eq("major").sum())
        # A4/A8 无大维护记录，成本与损伤基准频率与问题二一样用队列补充。
        major_rate = float(major_count / observed_years) if major_count else global_major_rate
        rows.append(
            {
                "asset": asset,
                "observation_years": observed_years,
                "elapsed_years_at_origin": elapsed_years,
                "medium_rate_per_year": medium_rate,
                "major_rate_per_year": major_rate,
                "historical_medium_events_equiv": medium_rate * elapsed_years,
                "historical_major_events_equiv": major_rate * elapsed_years,
                "major_rate_source": "asset_history" if major_count else "cohort_imputed",
            }
        )
    return pd.DataFrame(rows)


def _event_type_series(
    maintenance_type: pd.Series,
    seed_type: str,
) -> pd.Series:
    out = maintenance_type.copy().astype("object")
    if len(out):
        out.iloc[0] = out.iloc[0] if pd.notna(out.iloc[0]) else seed_type
    return out.ffill().fillna(seed_type)


def _finalize_policy_frame(
    frame: pd.DataFrame,
    seed_last_date: pd.Timestamp,
    seed_last_type: str,
    reference_date: pd.Timestamp,
) -> pd.DataFrame:
    out = frame.sort_values("date").reset_index(drop=True).copy()
    out["last_maintenance_date"] = out["date"].where(out["maintenance_type"].notna())
    if len(out) and pd.isna(out.loc[0, "last_maintenance_date"]):
        out.loc[0, "last_maintenance_date"] = pd.Timestamp(seed_last_date)
    out["last_maintenance_date"] = out["last_maintenance_date"].ffill()
    out["days_since_maintenance"] = (
        out["date"] - out["last_maintenance_date"]
    ).dt.days.astype(int)
    out["last_maintenance_type"] = _event_type_series(
        out["maintenance_type"], seed_last_type
    )
    return _ensure_state_features(out, reference_date)


def build_periodic_policy_frame(
    spec: PolicySpec,
    asset: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    reference_date: pd.Timestamp,
    maintenance: pd.DataFrame,
) -> pd.DataFrame:
    """按中维护与大维护最大间隔生成日历，同日以大维护覆盖。"""

    if spec.medium_interval_days is None or spec.major_interval_days is None:
        raise ValueError("周期策略必须给出中维护和大维护间隔")
    history = maintenance.loc[maintenance["asset"].astype(str) == asset].sort_values(
        "maintenance_date"
    )
    last_event = history.iloc[-1]
    major_history = history.loc[history["maintenance_type"].eq("major")]
    last_any_date = pd.Timestamp(last_event["maintenance_date"])
    last_major_date = (
        pd.Timestamp(major_history.iloc[-1]["maintenance_date"])
        if len(major_history)
        else last_any_date
    )
    last_type = str(last_event["maintenance_type"])
    events: list[tuple[pd.Timestamp, str]] = []
    minimum_gap = int(spec.cooldown_days or min(int(spec.medium_interval_days), 30))
    for date in pd.date_range(pd.Timestamp(start_date) + pd.Timedelta(days=1), end_date, freq="D"):
        action: str | None = None
        days_since_any = (date - last_any_date).days
        days_since_major = (date - last_major_date).days
        days_to_major = int(spec.major_interval_days) - days_since_major
        if (
            days_since_major >= int(spec.major_interval_days)
            and days_since_any >= minimum_gap
        ):
            action = "major"
        elif (
            days_since_any >= int(spec.medium_interval_days)
            and days_to_major > minimum_gap
        ):
            action = "medium"
        if action is not None:
            events.append((date, action))
            last_any_date = date
            last_type = action
            if action == "major":
                last_major_date = date
    event_map = dict(events)
    frame = pd.DataFrame(
        {
            "asset": asset,
            "date": pd.date_range(pd.Timestamp(start_date) + pd.Timedelta(days=1), end_date),
        }
    )
    frame["maintenance_type"] = frame["date"].map(event_map)
    seed = history.iloc[-1]
    return _finalize_policy_frame(
        frame,
        pd.Timestamp(seed["maintenance_date"]),
        str(seed["maintenance_type"]),
        reference_date,
    )


def _response_parameters(
    response: pd.DataFrame,
    scenario: str,
) -> dict[str, tuple[float, float]]:
    lookup = response.set_index("maintenance_type")
    if scenario not in RESPONSE_SCENARIOS:
        raise ValueError(f"未知维护效果情景：{scenario}")
    if scenario == "empirical":
        medium = (
            float(lookup.loc["medium", "instant_empirical"]),
            float(lookup.loc["medium", "retained_empirical"]),
        )
        major = (
            float(lookup.loc["major", "instant_empirical"]),
            float(lookup.loc["major", "retained_empirical"]),
        )
    else:
        medium = (
            float(lookup.loc["medium", "instant_shrunk"]),
            float(lookup.loc["medium", "retained_shrunk"]),
        )
        major = (
            float(lookup.loc["major", "instant_shrunk"]),
            float(lookup.loc["major", "retained_shrunk"]),
        )
        if scenario == "major_equal":
            major = medium
    if scenario == "empirical":
        pooled = (
            float(lookup["pooled_instant"].iloc[0]),
            float(lookup["pooled_retained"].iloc[0]),
        )
    else:
        event_weights = lookup["recorded_events"].to_numpy(dtype=float)
        pooled = (
            float(np.average(lookup["instant_shrunk"], weights=event_weights)),
            float(np.average(lookup["retained_shrunk"], weights=event_weights)),
        )
    return {
        "medium": (medium[0] - pooled[0], medium[1] - pooled[1]),
        "major": (major[0] - pooled[0], major[1] - pooled[1]),
    }


def typed_response_profile(
    frame: pd.DataFrame,
    response: pd.DataFrame,
    scenario: str = "shrunk",
) -> np.ndarray:
    """在问题二通用维护重置上添加中/大维护类型差异。"""

    params = _response_parameters(response, scenario)
    age = pd.to_numeric(frame["days_since_maintenance"], errors="coerce").fillna(9999).to_numpy()
    event_type = frame["last_maintenance_type"].astype(str).to_numpy()
    profile = np.zeros(len(frame), dtype=float)
    for maintenance_type in ("medium", "major"):
        instant_delta, retained_delta = params[maintenance_type]
        mask = event_type == maintenance_type
        profile[mask & (age <= 7)] = instant_delta
        profile[mask & (age >= 8) & (age <= 30)] = retained_delta
        taper = mask & (age >= 31) & (age <= 60)
        profile[taper] = retained_delta * (60.0 - age[taper]) / 30.0
    return profile


def maintenance_damage_correction(
    frame: pd.DataFrame,
    degradation_per_year: float,
    medium_rate_per_year: float,
    major_rate_per_year: float,
    forecast_origin: pd.Timestamp,
    damage_share: float = MAIN_DAMAGE_SHARE,
) -> np.ndarray:
    """将问题二总退化拆为自然退化与随政策变化的维护损伤。

    在历史年频率下，期望修正为 0，因此现行策略能复现问题二；
    改变频率时，按中维护 1、大维护 4 的相对强度累计损伤。
    """

    if not 0.0 <= damage_share <= 1.0:
        raise ValueError("维护损伤份额必须位于 [0,1]")
    intensity = float(
        medium_rate_per_year + MAJOR_DAMAGE_MULTIPLIER * major_rate_per_year
    )
    if intensity <= 0.0 or damage_share == 0.0:
        return np.zeros(len(frame), dtype=float)
    elapsed = (
        pd.to_datetime(frame["date"]) - pd.Timestamp(forecast_origin)
    ).dt.days.to_numpy(dtype=float) / ANNUAL_PERIOD_DAYS
    event_weight = np.where(
        frame["maintenance_type"].eq("medium"),
        1.0,
        np.where(
            frame["maintenance_type"].eq("major"),
            MAJOR_DAMAGE_MULTIPLIER,
            0.0,
        ),
    )
    cumulative_weight = np.cumsum(event_weight)
    return damage_share * float(degradation_per_year) * (
        elapsed - cumulative_weight / intensity
    )


def point_policy_prediction(
    frame: pd.DataFrame,
    model: HierarchicalStateModel,
    response: pd.DataFrame,
    rates: Mapping[str, Any],
    forecast_origin: pd.Timestamp,
    *,
    damage_share: float = MAIN_DAMAGE_SHARE,
    response_scenario: str = "shrunk",
) -> np.ndarray:
    asset = str(frame["asset"].iloc[0])
    base = model.predict(frame)
    correction = maintenance_damage_correction(
        frame,
        model.parameter(f"degradation:{asset}"),
        float(rates["medium_rate_per_year"]),
        float(rates["major_rate_per_year"]),
        forecast_origin,
        damage_share,
    )
    return base + typed_response_profile(frame, response, response_scenario) + correction


def _generic_fouling_effect(model: HierarchicalStateModel, ages: np.ndarray) -> np.ndarray:
    ages = np.maximum(np.asarray(ages, dtype=float), 0.0)
    return (
        model.parameter("fouling_0_30") * np.minimum(ages, 30.0) / 30.0
        + model.parameter("fouling_30_90")
        * np.minimum(np.maximum(ages - 30.0, 0.0), 60.0)
        / 60.0
    )


def build_trigger_policy_frame(
    spec: PolicySpec,
    asset: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    reference_date: pd.Timestamp,
    maintenance: pd.DataFrame,
    history_panel: pd.DataFrame,
    model: HierarchicalStateModel,
    response: pd.DataFrame,
    rates: Mapping[str, Any],
    damage_share: float = MAIN_DAMAGE_SHARE,
) -> pd.DataFrame:
    """根据未来 30 日预测余量生成状态触发日历。

    触发日历使用点估计状态生成，后续蒙特卡评估时把该日历视为
    一套现场可执行的规则结果，而不是预知未来噪声的完美闭环控制。
    """

    if (
        spec.trigger_level is None
        or spec.cooldown_days is None
        or spec.major_interval_days is None
    ):
        raise ValueError("状态触发策略缺少触发线、冷却期或大维护间隔")

    asset_history = maintenance.loc[
        maintenance["asset"].astype(str) == asset
    ].sort_values("maintenance_date")
    last_event = asset_history.iloc[-1]
    major_history = asset_history.loc[asset_history["maintenance_type"].eq("major")]
    last_any_date = pd.Timestamp(last_event["maintenance_date"])
    last_type = str(last_event["maintenance_type"])
    last_major_date = (
        pd.Timestamp(major_history.iloc[-1]["maintenance_date"])
        if len(major_history)
        else last_any_date
    )

    dates = pd.date_range(pd.Timestamp(start_date) + pd.Timedelta(days=1), end_date, freq="D")
    clean_frame = pd.DataFrame(
        {
            "asset": asset,
            "date": dates,
            "days_since_maintenance": np.zeros(len(dates), dtype=int),
        }
    )
    clean_base = model.predict(_ensure_state_features(clean_frame, reference_date))
    elapsed = (dates - pd.Timestamp(start_date)).days.to_numpy(dtype=float) / ANNUAL_PERIOD_DAYS
    degradation = model.parameter(f"degradation:{asset}")
    intensity = float(
        rates["medium_rate_per_year"]
        + MAJOR_DAMAGE_MULTIPLIER * rates["major_rate_per_year"]
    )
    history_values = (
        history_panel.loc[history_panel["asset"].astype(str) == asset]
        .sort_values("date")["performance_model"]
        .interpolate(limit_direction="both")
        .dropna()
        .to_numpy(dtype=float)
    )
    rolling_values = list(history_values[-(ROLLING_YEAR_DAYS - 1) :])
    events: dict[pd.Timestamp, str] = {}
    cumulative_damage_weight = 0.0
    diagnostic_due = False

    # 类型修正只与距上次维护时间有关，在循环中使用小向量评估。
    response_params = _response_parameters(response, "shrunk")

    def type_adjustment(event_type: str, ages: np.ndarray) -> np.ndarray:
        instant_delta, retained_delta = response_params[event_type]
        ages = np.asarray(ages, dtype=float)
        values = np.zeros(len(ages), dtype=float)
        values[ages <= 7] = instant_delta
        values[(ages >= 8) & (ages <= 30)] = retained_delta
        taper = (ages >= 31) & (ages <= 60)
        values[taper] = retained_delta * (60.0 - ages[taper]) / 30.0
        return values

    for index, date in enumerate(dates):
        action: str | None = None
        if diagnostic_due:
            action = "major"
        elif (date - last_major_date).days >= int(spec.major_interval_days):
            action = "major"
        elif (
            index % 7 == 0
            and (date - last_any_date).days >= int(spec.cooldown_days)
        ):
            stop = min(index + 31, len(dates))
            offsets = np.arange(stop - index, dtype=float)
            future_ages = (date - last_any_date).days + offsets
            fouling = _generic_fouling_effect(model, future_ages)
            response_adjustment = type_adjustment(last_type, future_ages)
            if intensity > 0.0:
                damage = damage_share * degradation * (
                    elapsed[index:stop] - cumulative_damage_weight / intensity
                )
            else:
                damage = np.zeros(stop - index, dtype=float)
            no_action_forecast = (
                clean_base[index:stop] + fouling + response_adjustment + damage
            )
            if float(np.min(no_action_forecast)) < float(spec.trigger_level):
                action = "medium"

        if action is not None:
            events[date] = action
            last_any_date = date
            last_type = action
            cumulative_damage_weight += (
                MAJOR_DAMAGE_MULTIPLIER if action == "major" else 1.0
            )
            if action == "major":
                last_major_date = date
                diagnostic_due = False

        age = float((date - last_any_date).days)
        point = clean_base[index] + float(_generic_fouling_effect(model, np.array([age]))[0])
        point += float(type_adjustment(last_type, np.array([age]))[0])
        if intensity > 0.0:
            point += damage_share * degradation * (
                elapsed[index] - cumulative_damage_weight / intensity
            )
        rolling_values.append(point)
        if len(rolling_values) >= ROLLING_YEAR_DAYS:
            rolling_mean = float(np.mean(rolling_values[-ROLLING_YEAR_DAYS:]))
            if rolling_mean < LIFETIME_THRESHOLD and action != "major":
                diagnostic_due = True

    frame = pd.DataFrame({"asset": asset, "date": dates})
    frame["maintenance_type"] = frame["date"].map(events)
    return _finalize_policy_frame(
        frame,
        pd.Timestamp(last_event["maintenance_date"]),
        str(last_event["maintenance_type"]),
        reference_date,
    )


def build_current_policy_frame(
    asset: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    reference_date: pd.Timestamp,
    maintenance: pd.DataFrame,
    fixed_schedule: pd.DataFrame,
) -> pd.DataFrame:
    full = build_future_frame(fixed_schedule, start_date, end_date, reference_date)
    frame = full.loc[full["asset"].astype(str) == asset].copy()
    asset_history = maintenance.loc[
        maintenance["asset"].astype(str) == asset
    ].sort_values("maintenance_date")
    last_event = asset_history.iloc[-1]
    frame["last_maintenance_type"] = _event_type_series(
        frame["maintenance_type"], str(last_event["maintenance_type"])
    )
    return frame.reset_index(drop=True)


def build_policy_frame(
    spec: PolicySpec,
    asset: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    reference_date: pd.Timestamp,
    maintenance: pd.DataFrame,
    fixed_schedule: pd.DataFrame,
    history_panel: pd.DataFrame,
    model: HierarchicalStateModel,
    response: pd.DataFrame,
    rates: Mapping[str, Any],
) -> pd.DataFrame:
    if spec.policy_kind == "current":
        return build_current_policy_frame(
            asset,
            start_date,
            end_date,
            reference_date,
            maintenance,
            fixed_schedule,
        )
    if spec.policy_kind == "periodic":
        return build_periodic_policy_frame(
            spec,
            asset,
            start_date,
            end_date,
            reference_date,
            maintenance,
        )
    if spec.policy_kind == "trigger":
        return build_trigger_policy_frame(
            spec,
            asset,
            start_date,
            end_date,
            reference_date,
            maintenance,
            history_panel,
            model,
            response,
            rates,
        )
    raise ValueError(f"未知策略类型：{spec.policy_kind}")


def _rolling_forecast(
    asset_history: pd.DataFrame,
    prediction: np.ndarray,
) -> np.ndarray:
    historical = (
        asset_history.sort_values("date")["performance_model"]
        .interpolate(limit_direction="both")
        .dropna()
        .to_numpy(dtype=float)
    )
    historical = historical[-(ROLLING_YEAR_DAYS - 1) :]
    if len(historical) < ROLLING_YEAR_DAYS - 1:
        raise ValueError("历史日数不足以计算滚动 365 日均值")
    combined = np.concatenate([historical, np.asarray(prediction, dtype=float)])
    cumulative = np.cumsum(np.concatenate([[0.0], combined]))
    return (
        cumulative[ROLLING_YEAR_DAYS:] - cumulative[:-ROLLING_YEAR_DAYS]
    ) / ROLLING_YEAR_DAYS


def joint_failure_index(
    prediction: np.ndarray,
    rolling: np.ndarray,
    maintenance_type: Sequence[Any],
    recovery_level: float = LIFETIME_THRESHOLD,
) -> tuple[int | None, int | None]:
    """返回年均阈值下穿与联合寿命终点下标。"""

    below = np.flatnonzero(np.asarray(rolling) < LIFETIME_THRESHOLD)
    if len(below) == 0:
        return None, None
    crossing = int(below[0])
    types = np.asarray(maintenance_type, dtype=object)
    major_indices = np.flatnonzero(types == "major")
    for major_index in major_indices[major_indices >= crossing]:
        if major_index + 30 >= len(prediction):
            break
        post = np.asarray(prediction)[major_index + 8 : major_index + 31]
        if len(post) >= 20 and float(np.mean(post)) < recovery_level:
            return crossing, int(major_index + 30)
    return crossing, None


def _historical_cost(rates: Mapping[str, Any], costs: CostConfig) -> float:
    return (
        costs.medium * float(rates["historical_medium_events_equiv"])
        + costs.major * float(rates["historical_major_events_equiv"])
    )


def evaluate_point_policy(
    spec: PolicySpec,
    asset: str,
    frame: pd.DataFrame,
    history_panel: pd.DataFrame,
    model: HierarchicalStateModel,
    response: pd.DataFrame,
    rates: Mapping[str, Any],
    forecast_origin: pd.Timestamp,
    costs: CostConfig = BASE_COSTS,
    *,
    damage_share: float = MAIN_DAMAGE_SHARE,
    response_scenario: str = "shrunk",
) -> dict[str, Any]:
    prediction = point_policy_prediction(
        frame,
        model,
        response,
        rates,
        forecast_origin,
        damage_share=damage_share,
        response_scenario=response_scenario,
    )
    asset_history = history_panel.loc[history_panel["asset"].astype(str) == asset]
    rolling = _rolling_forecast(asset_history, prediction)
    crossing, failure = joint_failure_index(
        prediction,
        rolling,
        frame["maintenance_type"].to_numpy(),
    )
    endpoint = len(frame) - 1 if failure is None else int(failure)
    dates = pd.DatetimeIndex(frame["date"])
    endpoint_date = pd.Timestamp(dates[endpoint])
    total_lifetime_days = float((endpoint_date - pd.Timestamp(COMMISSION_DATE)).days)
    medium_count = int(frame.iloc[: endpoint + 1]["maintenance_type"].eq("medium").sum())
    major_count = int(frame.iloc[: endpoint + 1]["maintenance_type"].eq("major").sum())
    lifecycle_cost = (
        costs.purchase
        + _historical_cost(rates, costs)
        + costs.medium * medium_count
        + costs.major * major_count
    )
    annual_cost = lifecycle_cost / (total_lifetime_days / ANNUAL_PERIOD_DAYS)
    future_years = max(float((endpoint_date - pd.Timestamp(forecast_origin)).days / ANNUAL_PERIOD_DAYS), 1e-9)
    return {
        "asset": asset,
        "policy_id": spec.policy_id,
        "policy_kind": spec.policy_kind,
        "evaluation_stage": "point",
        "simulation_paths": 1,
        "mean_annual_cost": annual_cost,
        "median_annual_cost": annual_cost,
        "p10_annual_cost": annual_cost,
        "p90_annual_cost": annual_cost,
        "cvar90_annual_cost": annual_cost,
        "mean_total_lifetime_years": total_lifetime_days / ANNUAL_PERIOD_DAYS,
        "median_total_lifetime_years": total_lifetime_days / ANNUAL_PERIOD_DAYS,
        "p10_total_lifetime_years": total_lifetime_days / ANNUAL_PERIOD_DAYS,
        "p90_total_lifetime_years": total_lifetime_days / ANNUAL_PERIOD_DAYS,
        "mean_future_medium_events": float(medium_count),
        "mean_future_major_events": float(major_count),
        "mean_medium_events_per_future_year": medium_count / future_years,
        "mean_major_events_per_future_year": major_count / future_years,
        "median_failure_date": endpoint_date,
        "censored_rate": float(failure is None),
        "threshold_crossing_date": (
            pd.NaT if crossing is None else pd.Timestamp(dates[crossing])
        ),
        "damage_share": damage_share,
        "response_scenario": response_scenario,
    }


def _response_uncertainty_bases(
    frame: pd.DataFrame,
) -> dict[str, np.ndarray]:
    age = pd.to_numeric(frame["days_since_maintenance"], errors="coerce").fillna(9999).to_numpy()
    event_type = frame["last_maintenance_type"].astype(str).to_numpy()
    bases: dict[str, np.ndarray] = {}
    for maintenance_type in ("medium", "major"):
        mask = event_type == maintenance_type
        instant = (mask & (age <= 7)).astype(float)
        retained = (mask & (age >= 8) & (age <= 30)).astype(float)
        taper = mask & (age >= 31) & (age <= 60)
        retained[taper] = (60.0 - age[taper]) / 30.0
        bases[f"{maintenance_type}_instant"] = instant
        bases[f"{maintenance_type}_retained"] = retained
    return bases


def simulate_policy_asset(
    spec: PolicySpec,
    asset: str,
    frame: pd.DataFrame,
    history_panel: pd.DataFrame,
    scenario_models: Sequence[HierarchicalStateModel],
    response: pd.DataFrame,
    rates: Mapping[str, Any],
    forecast_origin: pd.Timestamp,
    *,
    paths: int,
    seed: int,
    costs: CostConfig = BASE_COSTS,
    evaluation_stage: str = "final",
) -> tuple[dict[str, Any], pd.DataFrame]:
    """用公共随机数评估单设备、单策略的寿命与年均成本。"""

    if paths <= 0:
        raise ValueError("仿真路径数必须为正")
    if not scenario_models:
        raise ValueError("至少需要一个退化情景模型")

    rng = np.random.default_rng(seed + ASSETS.index(asset) * 1000)
    dates = pd.DatetimeIndex(frame["date"])
    horizon = len(frame)
    elapsed = (dates - pd.Timestamp(forecast_origin)).days.to_numpy(dtype=float) / ANNUAL_PERIOD_DAYS
    scenario_predictions = np.vstack([model.predict(frame) for model in scenario_models])
    scenario_degradation = np.array(
        [model.parameter(f"degradation:{asset}") for model in scenario_models],
        dtype=float,
    )
    scenario_residual = np.array(
        [model.residual_std for model in scenario_models], dtype=float
    )
    model_choices = rng.integers(0, len(scenario_models), size=paths)
    degradation_multiplier = np.exp(
        rng.normal(-0.5 * 0.10**2, 0.10, size=paths)
    )
    chosen_degradation = scenario_degradation[model_choices]
    degradation_draw = chosen_degradation * degradation_multiplier
    level_shift = rng.normal(
        0.0, scenario_residual[model_choices] / np.sqrt(60.0), size=paths
    )
    damage_choices = rng.choice(
        np.asarray(DAMAGE_SHARES, dtype=float),
        size=paths,
        p=np.array([0.2, 0.6, 0.2]),
    )
    response_choices = rng.choice(
        np.arange(len(RESPONSE_SCENARIOS)),
        size=paths,
        p=np.array([0.6, 0.2, 0.2]),
    )
    response_profiles = np.vstack(
        [typed_response_profile(frame, response, scenario) for scenario in RESPONSE_SCENARIOS]
    )
    response_bases = _response_uncertainty_bases(frame)
    response_lookup = response.set_index("maintenance_type")

    intensity = float(
        rates["medium_rate_per_year"]
        + MAJOR_DAMAGE_MULTIPLIER * rates["major_rate_per_year"]
    )
    event_weight = np.where(
        frame["maintenance_type"].eq("medium"),
        1.0,
        np.where(
            frame["maintenance_type"].eq("major"),
            MAJOR_DAMAGE_MULTIPLIER,
            0.0,
        ),
    )
    cumulative_weight = np.cumsum(event_weight)
    damage_gap = (
        elapsed - cumulative_weight / intensity
        if intensity > 0.0
        else np.zeros(horizon, dtype=float)
    )

    asset_history = history_panel.loc[
        history_panel["asset"].astype(str) == asset
    ].sort_values("date")
    past = (
        asset_history["performance_model"]
        .interpolate(limit_direction="both")
        .dropna()
        .to_numpy(dtype=float)
    )[-(ROLLING_YEAR_DAYS - 1) :]
    if len(past) < ROLLING_YEAR_DAYS - 1:
        raise ValueError(f"设备 {asset} 缺少滚动年均历史窗口")

    medium_cumulative = np.cumsum(frame["maintenance_type"].eq("medium").to_numpy(dtype=int))
    major_cumulative = np.cumsum(frame["maintenance_type"].eq("major").to_numpy(dtype=int))
    major_indices = np.flatnonzero(frame["maintenance_type"].eq("major").to_numpy())
    annual_costs = np.empty(paths, dtype=float)
    lifetime_years = np.empty(paths, dtype=float)
    future_medium = np.empty(paths, dtype=float)
    future_major = np.empty(paths, dtype=float)
    failure_indices = np.full(paths, -1, dtype=int)
    crossing_indices = np.full(paths, -1, dtype=int)

    chunk_size = 100
    for start in range(0, paths, chunk_size):
        stop = min(start + chunk_size, paths)
        selected = model_choices[start:stop]
        prediction = scenario_predictions[selected].copy()
        delta = degradation_draw[start:stop] - chosen_degradation[start:stop]
        prediction -= delta[:, np.newaxis] * elapsed[np.newaxis, :]
        prediction += level_shift[start:stop, np.newaxis]
        prediction += response_profiles[response_choices[start:stop]]
        prediction += (
            damage_choices[start:stop, np.newaxis]
            * degradation_draw[start:stop, np.newaxis]
            * damage_gap[np.newaxis, :]
        )

        # 事件效果的均值不确定性按路径抽样，避免把 17 次
        # 大维护的样本误差忽略掉。
        for maintenance_type in ("medium", "major"):
            instant_sd = float(
                response_lookup.loc[maintenance_type, "instant_standard_error"]
            )
            retained_sd = float(
                response_lookup.loc[maintenance_type, "retained_standard_error"]
            )
            instant_draw = rng.normal(0.0, instant_sd, size=stop - start)
            retained_draw = rng.normal(0.0, retained_sd, size=stop - start)
            prediction += (
                instant_draw[:, np.newaxis]
                * response_bases[f"{maintenance_type}_instant"][np.newaxis, :]
                + retained_draw[:, np.newaxis]
                * response_bases[f"{maintenance_type}_retained"][np.newaxis, :]
            )

        historical = np.broadcast_to(past, (stop - start, len(past)))
        combined = np.concatenate([historical, prediction], axis=1)
        cumulative = np.cumsum(
            np.concatenate([np.zeros((stop - start, 1)), combined], axis=1), axis=1
        )
        rolling = (
            cumulative[:, ROLLING_YEAR_DAYS:]
            - cumulative[:, :-ROLLING_YEAR_DAYS]
        ) / ROLLING_YEAR_DAYS
        below = rolling < LIFETIME_THRESHOLD
        has_crossing = below.any(axis=1)
        local_crossings = np.where(has_crossing, below.argmax(axis=1), -1)
        crossing_indices[start:stop] = local_crossings

        for local_index, crossing in enumerate(local_crossings):
            endpoint = horizon - 1
            if crossing >= 0:
                for major_index in major_indices[major_indices >= crossing]:
                    if major_index + 30 >= horizon:
                        break
                    post = prediction[local_index, major_index + 8 : major_index + 31]
                    if float(np.mean(post)) < LIFETIME_THRESHOLD:
                        endpoint = int(major_index + 30)
                        failure_indices[start + local_index] = endpoint
                        break
            endpoint_date = pd.Timestamp(dates[endpoint])
            years = float(
                (endpoint_date - pd.Timestamp(COMMISSION_DATE)).days
                / ANNUAL_PERIOD_DAYS
            )
            med = float(medium_cumulative[endpoint])
            maj = float(major_cumulative[endpoint])
            total_cost = (
                costs.purchase
                + _historical_cost(rates, costs)
                + costs.medium * med
                + costs.major * maj
            )
            lifetime_years[start + local_index] = years
            future_medium[start + local_index] = med
            future_major[start + local_index] = maj
            annual_costs[start + local_index] = total_cost / years

    worst_count = max(int(np.ceil(paths * 0.10)), 1)
    worst_costs = np.sort(annual_costs)[-worst_count:]

    def q(values: np.ndarray, probability: float) -> float:
        return float(np.quantile(values, probability, method="linear"))

    endpoint_indices = np.where(failure_indices >= 0, failure_indices, horizon - 1)
    median_endpoint = int(np.quantile(endpoint_indices, 0.50, method="higher"))
    future_years = np.maximum(
        lifetime_years
        - float(
            (pd.Timestamp(forecast_origin) - pd.Timestamp(COMMISSION_DATE)).days
            / ANNUAL_PERIOD_DAYS
        ),
        1e-9,
    )
    summary = {
        "asset": asset,
        "policy_id": spec.policy_id,
        "policy_kind": spec.policy_kind,
        "evaluation_stage": evaluation_stage,
        "simulation_paths": paths,
        "mean_annual_cost": float(np.mean(annual_costs)),
        "median_annual_cost": q(annual_costs, 0.50),
        "p10_annual_cost": q(annual_costs, 0.10),
        "p90_annual_cost": q(annual_costs, 0.90),
        "cvar90_annual_cost": float(np.mean(worst_costs)),
        "mean_total_lifetime_years": float(np.mean(lifetime_years)),
        "median_total_lifetime_years": q(lifetime_years, 0.50),
        "p10_total_lifetime_years": q(lifetime_years, 0.10),
        "p90_total_lifetime_years": q(lifetime_years, 0.90),
        "mean_future_medium_events": float(np.mean(future_medium)),
        "mean_future_major_events": float(np.mean(future_major)),
        "mean_medium_events_per_future_year": float(np.mean(future_medium / future_years)),
        "mean_major_events_per_future_year": float(np.mean(future_major / future_years)),
        "median_failure_date": pd.Timestamp(dates[median_endpoint]),
        "censored_rate": float(np.mean(failure_indices < 0)),
        "threshold_crossing_date": (
            pd.NaT
            if np.all(crossing_indices < 0)
            else pd.Timestamp(
                dates[
                    int(
                        np.quantile(
                            np.where(crossing_indices >= 0, crossing_indices, horizon - 1),
                            0.50,
                            method="higher",
                        )
                    )
                ]
            )
        ),
        "damage_share": MAIN_DAMAGE_SHARE,
        "response_scenario": "mixture",
    }
    distributions = pd.DataFrame(
        {
            "asset": asset,
            "policy_id": spec.policy_id,
            "path_id": np.arange(paths, dtype=int),
            "annual_cost": annual_costs,
            "total_lifetime_years": lifetime_years,
            "future_medium_events": future_medium,
            "future_major_events": future_major,
            "failure_index": failure_indices,
            "damage_share": damage_choices,
            "response_scenario": [RESPONSE_SCENARIOS[i] for i in response_choices],
        }
    )
    return summary, distributions


def _select_with_tie_break(evaluations: pd.DataFrame) -> pd.Series:
    """成本近似相同时，仅接受同时“维护更少且寿命不短”的替代。"""

    if evaluations.empty:
        raise ValueError("没有可选策略")
    work = evaluations.copy()
    work["mean_total_events"] = (
        work["mean_future_medium_events"] + work["mean_future_major_events"]
    )
    minimum_row = work.sort_values(["mean_annual_cost", "policy_id"]).iloc[0]
    candidates = work.loc[
        (work["mean_annual_cost"] <= float(minimum_row["mean_annual_cost"]) * 1.01)
        & (work["mean_total_events"] <= float(minimum_row["mean_total_events"]))
        & (
            work["median_total_lifetime_years"]
            >= float(minimum_row["median_total_lifetime_years"])
        )
    ].copy()
    if candidates.empty:
        return minimum_row
    return candidates.sort_values(
        ["mean_annual_cost", "mean_total_events", "median_total_lifetime_years", "policy_id"],
        ascending=[True, True, False, True],
    ).iloc[0]


def plot_cost_frontier(
    point_evaluations: pd.DataFrame,
    uniform_policy_id: str,
) -> Path:
    aggregate = (
        point_evaluations.groupby(["policy_id", "policy_kind"], as_index=False)
        .agg(
            fleet_annual_cost=("mean_annual_cost", "sum"),
            mean_lifetime=("median_total_lifetime_years", "mean"),
        )
    )
    colors = {"current": "#d95f02", "periodic": "#2457a7", "trigger": "#2b8c6b"}
    fig, ax = plt.subplots(figsize=(9.5, 6.0))
    for kind, block in aggregate.groupby("policy_kind"):
        ax.scatter(
            block["mean_lifetime"],
            block["fleet_annual_cost"],
            s=28,
            alpha=0.65,
            label={"current": "现行", "periodic": "周期", "trigger": "状态触发"}.get(kind, kind),
            color=colors.get(kind, "#777777"),
        )
    highlight = aggregate.loc[aggregate["policy_id"].eq(uniform_policy_id)]
    if len(highlight):
        ax.scatter(
            highlight["mean_lifetime"],
            highlight["fleet_annual_cost"],
            s=150,
            facecolor="none",
            edgecolor="#111111",
            linewidth=1.8,
            label="全厂统一优选",
            zorder=5,
        )
    ax.set_xlabel("10台设备平均总寿命（年）")
    ax.set_ylabel("全厂全生命周期年均成本（万元/年）")
    ax.set_title("候选维护策略的寿命—成本前沿")
    ax.legend(frameon=False, ncol=2)
    return _save_figure(fig, "q3_01_cost_frontier.png")


def plot_cost_comparison(comparison: pd.DataFrame) -> Path:
    work = comparison.set_index("asset").reindex(ASSETS)
    x = np.arange(len(work))
    width = 0.38
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.bar(
        x - width / 2,
        work["current_mean_annual_cost"],
        width,
        label="现行策略",
        color="#9aa0a6",
    )
    ax.bar(
        x + width / 2,
        work["optimal_mean_annual_cost"],
        width,
        label="优选策略",
        color="#2457a7",
    )
    ax.set_xticks(x, work.index)
    ax.set_ylabel("年均成本（万元/年）")
    ax.set_title("各设备现行与优选维护策略成本对比")
    ax.legend(frameon=False)
    return _save_figure(fig, "q3_02_current_vs_optimal.png")


def plot_recommended_calendar(calendar: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(12.0, 6.4))
    y_lookup = {asset: index for index, asset in enumerate(ASSETS)}
    styles = {
        "medium": ("#f2a900", "o", "中维护"),
        "major": ("#d95f02", "s", "大维护"),
    }
    for maintenance_type, (color, marker, label) in styles.items():
        block = calendar.loc[calendar["maintenance_type"].eq(maintenance_type)]
        ax.scatter(
            pd.to_datetime(block["date"]),
            block["asset"].map(y_lookup),
            color=color,
            marker=marker,
            s=32 if maintenance_type == "medium" else 45,
            label=label,
            alpha=0.85,
        )
    ax.set_yticks(np.arange(len(ASSETS)), ASSETS)
    ax.invert_yaxis()
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_xlabel("建议日期")
    ax.set_title("预测原点后三年推荐维护日历")
    ax.legend(frameon=False, ncol=2)
    fig.autofmt_xdate(rotation=30)
    return _save_figure(fig, "q3_03_recommended_calendar.png")


def plot_savings_uncertainty(comparison: pd.DataFrame) -> Path:
    work = comparison.set_index("asset").reindex(ASSETS).copy()
    y = np.arange(len(work))
    mean = work["mean_savings_percent"].to_numpy(dtype=float)
    lower = mean - work["p10_savings_percent"].to_numpy(dtype=float)
    upper = work["p90_savings_percent"].to_numpy(dtype=float) - mean
    fig, ax = plt.subplots(figsize=(9.5, 6.0))
    ax.errorbar(
        mean,
        y,
        xerr=np.vstack([np.maximum(lower, 0.0), np.maximum(upper, 0.0)]),
        fmt="o",
        color="#2457a7",
        ecolor="#7ba3d1",
        capsize=4,
    )
    ax.axvline(0.0, color="#d95f02", ls="--", lw=1.2)
    ax.set_yticks(y, work.index)
    ax.invert_yaxis()
    ax.set_xlabel("相对现行策略的年均成本节省率（%）")
    ax.set_title("优选策略节省率与80%仿真区间")
    return _save_figure(fig, "q3_04_savings_uncertainty.png")


def _load_q3_inputs() -> dict[str, Any]:
    ensure_output_dirs()
    panel_path = PROCESSED_DIR / "daily_panel.csv"
    if not panel_path.is_file():
        run_q1_scaffold()
    effects_path = RESULTS_DIR / "q1_maintenance_effects.csv"
    detail_path = RESULTS_DIR / "q1_event_effects_detail.csv"
    if not effects_path.is_file() or not detail_path.is_file():
        run_q1_formal()
    raw_panel = pd.read_csv(panel_path, parse_dates=["date", "last_maintenance_date"])
    panel = prepare_analysis_panel(raw_panel)
    maintenance = load_maintenance()
    effects = pd.read_csv(effects_path)
    event_detail = pd.read_csv(detail_path, parse_dates=["maintenance_date"])
    return {
        "raw_panel": raw_panel,
        "panel": panel,
        "maintenance": maintenance,
        "effects": effects,
        "event_detail": event_detail,
    }


def run_q3_formal(
    *,
    screening_paths: int = SCREENING_PATHS,
    final_paths: int = FINAL_PATHS,
    validation_paths: int = VALIDATION_PATHS,
    forecast_horizon_years: int = FORECAST_HORIZON_YEARS,
    costs: CostConfig = BASE_COSTS,
) -> Dict[str, Any]:
    """运行问题三正式策略搜索、蒙特卡复验和图表输出。"""

    inputs = _load_q3_inputs()
    panel: pd.DataFrame = inputs["panel"]
    maintenance: pd.DataFrame = inputs["maintenance"]
    response = estimate_maintenance_response(inputs["effects"])
    response_validation = validate_maintenance_response(inputs["event_detail"])
    main_model = fit_hierarchical_state_model(panel, reference_date=panel["date"].min())
    outlier_path = RESULTS_DIR / "q1_residual_outliers.csv"
    residual_outliers = (
        pd.read_csv(outlier_path, parse_dates=["date"])
        if outlier_path.is_file()
        else pd.DataFrame(columns=["asset", "date", "is_residual_outlier"])
    )
    clean_model, _ = residual_outlier_sensitivity(panel, main_model, residual_outliers)
    scenario_models, _ = structural_sensitivity_models(panel)
    scenario_models = list(scenario_models) + [clean_model]
    fixed_schedule = estimate_fixed_schedule(maintenance)
    forecast_origin = pd.to_datetime(panel["date"]).max()
    forecast_end = forecast_origin + pd.DateOffset(years=forecast_horizon_years)
    rates = historical_maintenance_rates(maintenance, forecast_origin)
    rates_lookup = rates.set_index("asset").to_dict(orient="index")
    specs = build_policy_space()
    spec_lookup = {spec.policy_id: spec for spec in specs}

    def make_frame(asset: str, policy_id: str) -> pd.DataFrame:
        return build_policy_frame(
            spec_lookup[policy_id],
            asset,
            forecast_origin,
            forecast_end,
            main_model.reference_date,
            maintenance,
            fixed_schedule,
            panel,
            main_model,
            response,
            rates_lookup[asset],
        )

    # 第一层：用主结构点估计评估全部规则。
    point_rows: list[dict[str, Any]] = []
    for asset in ASSETS:
        for spec in specs:
            frame = make_frame(asset, spec.policy_id)
            point_rows.append(
                evaluate_point_policy(
                    spec,
                    asset,
                    frame,
                    panel,
                    main_model,
                    response,
                    rates_lookup[asset],
                    forecast_origin,
                    costs,
                )
            )
    point_evaluations = pd.DataFrame(point_rows)

    # 全厂统一策略必须对 10 台设备使用同一组规则参数。
    uniform_point = (
        point_evaluations.loc[~point_evaluations["policy_id"].eq("current")]
        .groupby(["policy_id", "policy_kind"], as_index=False)
        .agg(
            mean_annual_cost=("mean_annual_cost", "sum"),
            median_total_lifetime_years=("median_total_lifetime_years", "mean"),
            mean_future_medium_events=("mean_future_medium_events", "sum"),
            mean_future_major_events=("mean_future_major_events", "sum"),
        )
    )
    uniform_policy_id = str(_select_with_tie_break(uniform_point)["policy_id"])

    # 第二层：每台选点估计前 5 名，并强制包含现行、最优周期和最优触发规则。
    screening_ids: dict[str, list[str]] = {}
    for asset in ASSETS:
        block = point_evaluations.loc[point_evaluations["asset"].eq(asset)]
        ids = block.nsmallest(5, "mean_annual_cost")["policy_id"].tolist()
        ids.append("current")
        ids.append(str(block.loc[block["policy_kind"].eq("periodic")].nsmallest(1, "mean_annual_cost").iloc[0]["policy_id"]))
        ids.append(str(block.loc[block["policy_kind"].eq("trigger")].nsmallest(1, "mean_annual_cost").iloc[0]["policy_id"]))
        ids.append(uniform_policy_id)
        screening_ids[asset] = list(dict.fromkeys(ids))

    screening_rows: list[dict[str, Any]] = []
    for asset in ASSETS:
        for policy_id in screening_ids[asset]:
            summary, _ = simulate_policy_asset(
                spec_lookup[policy_id],
                asset,
                make_frame(asset, policy_id),
                panel,
                scenario_models,
                response,
                rates_lookup[asset],
                forecast_origin,
                paths=screening_paths,
                seed=SEARCH_SEED,
                costs=costs,
                evaluation_stage="screening",
            )
            screening_rows.append(summary)
    screening_evaluations = pd.DataFrame(screening_rows)

    # 第三层：每台对筛选第 1 名、现行和统一策略做 2,000 路径复验。
    final_ids: dict[str, list[str]] = {}
    for asset in ASSETS:
        block = screening_evaluations.loc[screening_evaluations["asset"].eq(asset)]
        ids = block.nsmallest(1, "mean_annual_cost")["policy_id"].tolist()
        ids.extend(["current", uniform_policy_id])
        final_ids[asset] = list(dict.fromkeys(ids))

    final_rows: list[dict[str, Any]] = []
    distributions: dict[tuple[str, str], pd.DataFrame] = {}
    for asset in ASSETS:
        for policy_id in final_ids[asset]:
            summary, distribution = simulate_policy_asset(
                spec_lookup[policy_id],
                asset,
                make_frame(asset, policy_id),
                panel,
                scenario_models,
                response,
                rates_lookup[asset],
                forecast_origin,
                paths=final_paths,
                seed=SEARCH_SEED,
                costs=costs,
                evaluation_stage="final",
            )
            final_rows.append(summary)
            distributions[(asset, policy_id)] = distribution
    final_evaluations = pd.DataFrame(final_rows)

    # 检查新的分类维护层在现行日历下与问题二寿命的衔接程度。
    q2_lifetime_path = RESULTS_DIR / "q2_lifetime_summary.csv"
    if q2_lifetime_path.is_file():
        q2_lifetime = pd.read_csv(q2_lifetime_path)
        q2_bridge = q2_lifetime[
            ["asset", "median_total_lifetime_years"]
        ].rename(columns={"median_total_lifetime_years": "q2_median_lifetime_years"})
        q3_current = final_evaluations.loc[
            final_evaluations["policy_id"].eq("current"),
            ["asset", "median_total_lifetime_years"],
        ].rename(columns={"median_total_lifetime_years": "q3_current_median_lifetime_years"})
        baseline_check = q2_bridge.merge(q3_current, on="asset", how="inner")
        baseline_check["difference_years"] = (
            baseline_check["q3_current_median_lifetime_years"]
            - baseline_check["q2_median_lifetime_years"]
        )
        baseline_check["absolute_difference_years"] = baseline_check[
            "difference_years"
        ].abs()
    else:
        baseline_check = pd.DataFrame(
            columns=[
                "asset",
                "q2_median_lifetime_years",
                "q3_current_median_lifetime_years",
                "difference_years",
                "absolute_difference_years",
            ]
        )

    selected_rows: list[pd.Series] = []
    for asset in ASSETS:
        block = final_evaluations.loc[final_evaluations["asset"].eq(asset)]
        selected_rows.append(_select_with_tie_break(block))
    selected = pd.DataFrame(selected_rows).reset_index(drop=True)
    selected["selection"] = "asset_specific_optimal"
    optimal_policy = selected.merge(
        policy_space_table(specs).drop(columns=["feasible_main"]),
        on=["policy_id", "policy_kind"],
        how="left",
    )

    comparison_rows: list[dict[str, Any]] = []
    for asset in ASSETS:
        optimal_row = selected.loc[selected["asset"].eq(asset)].iloc[0]
        optimal_id = str(optimal_row["policy_id"])
        current_row = final_evaluations.loc[
            final_evaluations["asset"].eq(asset)
            & final_evaluations["policy_id"].eq("current")
        ].iloc[0]
        current_dist = distributions[(asset, "current")].sort_values("path_id")
        optimal_dist = distributions[(asset, optimal_id)].sort_values("path_id")
        savings = current_dist["annual_cost"].to_numpy() - optimal_dist["annual_cost"].to_numpy()
        savings_percent = savings / current_dist["annual_cost"].to_numpy() * 100.0
        comparison_rows.append(
            {
                "asset": asset,
                "optimal_policy_id": optimal_id,
                "optimal_policy_kind": optimal_row["policy_kind"],
                "current_mean_annual_cost": float(current_row["mean_annual_cost"]),
                "optimal_mean_annual_cost": float(optimal_row["mean_annual_cost"]),
                "mean_annual_saving": float(np.mean(savings)),
                "mean_savings_percent": float(np.mean(savings_percent)),
                "p10_savings_percent": float(np.quantile(savings_percent, 0.10)),
                "p90_savings_percent": float(np.quantile(savings_percent, 0.90)),
                "probability_of_positive_saving": float(np.mean(savings > 0.0)),
                "current_median_lifetime_years": float(current_row["median_total_lifetime_years"]),
                "optimal_median_lifetime_years": float(optimal_row["median_total_lifetime_years"]),
                "current_medium_events_per_year": float(current_row["mean_medium_events_per_future_year"]),
                "optimal_medium_events_per_year": float(optimal_row["mean_medium_events_per_future_year"]),
                "current_major_events_per_year": float(current_row["mean_major_events_per_future_year"]),
                "optimal_major_events_per_year": float(optimal_row["mean_major_events_per_future_year"]),
            }
        )
    comparison = pd.DataFrame(comparison_rows)
    comparison["recommendation_confidence"] = np.select(
        [
            comparison["p10_savings_percent"] > 0.0,
            comparison["probability_of_positive_saving"] >= 0.75,
        ],
        ["high", "medium"],
        default="low",
    )
    comparison["risk_note"] = np.where(
        comparison["recommendation_confidence"].eq("low"),
        "风险厌恶时建议暂维持现行策略并继续观测",
        "按期望年均成本执行优选策略",
    )

    # 生成未来三年可执行日历。
    calendar_rows: list[pd.DataFrame] = []
    calendar_end = forecast_origin + pd.DateOffset(years=3)
    for asset in ASSETS:
        policy_id = str(selected.loc[selected["asset"].eq(asset), "policy_id"].iloc[0])
        frame = make_frame(asset, policy_id)
        prediction = point_policy_prediction(
            frame,
            main_model,
            response,
            rates_lookup[asset],
            forecast_origin,
        )
        frame = frame.copy()
        frame["expected_performance"] = prediction
        events = frame.loc[
            frame["maintenance_type"].notna()
            & (frame["date"] <= calendar_end),
            [
                "asset",
                "date",
                "maintenance_type",
                "days_since_maintenance",
                "expected_performance",
            ],
        ].copy()
        events["policy_id"] = policy_id
        calendar_rows.append(events)
    recommended_calendar = pd.concat(calendar_rows, ignore_index=True)

    # 独立随机种子验证与参数情景。
    robustness_rows: list[dict[str, Any]] = []
    for asset in ASSETS:
        optimal_id = str(selected.loc[selected["asset"].eq(asset), "policy_id"].iloc[0])
        validation_distributions: dict[str, pd.DataFrame] = {}
        for policy_id in list(dict.fromkeys(["current", optimal_id])):
            summary, distribution = simulate_policy_asset(
                spec_lookup[policy_id],
                asset,
                make_frame(asset, policy_id),
                panel,
                scenario_models,
                response,
                rates_lookup[asset],
                forecast_origin,
                paths=validation_paths,
                seed=VALIDATION_SEED,
                costs=costs,
                evaluation_stage="validation",
            )
            validation_distributions[policy_id] = distribution
            robustness_rows.append(
                {
                    "asset": asset,
                    "policy_id": policy_id,
                    "robustness_type": "independent_seed",
                    "scenario": f"seed_{VALIDATION_SEED}",
                    "mean_annual_cost": summary["mean_annual_cost"],
                    "median_total_lifetime_years": summary["median_total_lifetime_years"],
                    "savings_percent_vs_current": np.nan,
                }
            )
        current_validation = validation_distributions["current"]["annual_cost"].to_numpy()
        optimal_validation = validation_distributions[optimal_id]["annual_cost"].to_numpy()
        saving_pct = (current_validation - optimal_validation) / current_validation * 100.0
        robustness_rows.append(
            {
                "asset": asset,
                "policy_id": optimal_id,
                "robustness_type": "independent_seed_saving",
                "scenario": f"seed_{VALIDATION_SEED}",
                "mean_annual_cost": float(np.mean(optimal_validation)),
                "median_total_lifetime_years": float(
                    validation_distributions[optimal_id]["total_lifetime_years"].median()
                ),
                "savings_percent_vs_current": float(np.mean(saving_pct)),
            }
        )

        for damage_share in DAMAGE_SHARES:
            for response_scenario in RESPONSE_SCENARIOS:
                scenario_costs: dict[str, float] = {}
                for policy_id in list(dict.fromkeys(["current", optimal_id])):
                    point = evaluate_point_policy(
                        spec_lookup[policy_id],
                        asset,
                        make_frame(asset, policy_id),
                        panel,
                        main_model,
                        response,
                        rates_lookup[asset],
                        forecast_origin,
                        costs,
                        damage_share=damage_share,
                        response_scenario=response_scenario,
                    )
                    scenario_costs[policy_id] = float(point["mean_annual_cost"])
                saving = (
                    scenario_costs["current"] - scenario_costs[optimal_id]
                ) / scenario_costs["current"] * 100.0
                robustness_rows.append(
                    {
                        "asset": asset,
                        "policy_id": optimal_id,
                        "robustness_type": "physical_scenario",
                        "scenario": f"damage_{damage_share:.2f}_{response_scenario}",
                        "mean_annual_cost": scenario_costs[optimal_id],
                        "median_total_lifetime_years": np.nan,
                        "savings_percent_vs_current": saving,
                    }
                )

        # 题目描述的现行工艺为每年 1—4 次大维护。将最大间隔
        # 放宽到 1.5/2 年，只作“非现行工艺”理论对照，不进入主方案。
        base_id = optimal_id if optimal_id != "current" else uniform_policy_id
        base_spec = spec_lookup[base_id]
        for relaxed_interval in (548, 730):
            relaxed_spec = replace(
                base_spec,
                policy_id=f"{base_id}_relaxed_b{relaxed_interval}",
                major_interval_days=relaxed_interval,
                description=base_spec.description + f"；放宽大维护间隔至 {relaxed_interval} 天",
            )
            relaxed_frame = build_policy_frame(
                relaxed_spec,
                asset,
                forecast_origin,
                forecast_end,
                main_model.reference_date,
                maintenance,
                fixed_schedule,
                panel,
                main_model,
                response,
                rates_lookup[asset],
            )
            relaxed_point = evaluate_point_policy(
                relaxed_spec,
                asset,
                relaxed_frame,
                panel,
                main_model,
                response,
                rates_lookup[asset],
                forecast_origin,
                costs,
            )
            current_point = evaluate_point_policy(
                spec_lookup["current"],
                asset,
                make_frame(asset, "current"),
                panel,
                main_model,
                response,
                rates_lookup[asset],
                forecast_origin,
                costs,
            )
            robustness_rows.append(
                {
                    "asset": asset,
                    "policy_id": relaxed_spec.policy_id,
                    "robustness_type": "constraint_relaxation",
                    "scenario": f"major_interval_{relaxed_interval}_days",
                    "mean_annual_cost": relaxed_point["mean_annual_cost"],
                    "median_total_lifetime_years": relaxed_point[
                        "median_total_lifetime_years"
                    ],
                    "savings_percent_vs_current": (
                        (current_point["mean_annual_cost"] - relaxed_point["mean_annual_cost"])
                        / current_point["mean_annual_cost"]
                        * 100.0
                    ),
                }
            )
    robustness = pd.DataFrame(robustness_rows)

    policy_evaluations = pd.concat(
        [point_evaluations, screening_evaluations, final_evaluations],
        ignore_index=True,
    )
    output_tables = {
        "q3_policy_space.csv": policy_space_table(specs),
        "q3_maintenance_response.csv": response,
        "q3_response_validation.csv": response_validation,
        "q3_q2_baseline_check.csv": baseline_check,
        "q3_policy_evaluation.csv": policy_evaluations,
        "q3_optimal_policy_by_asset.csv": optimal_policy,
        "q3_current_vs_optimal.csv": comparison,
        "q3_recommended_calendar.csv": recommended_calendar,
        "q3_robustness.csv": robustness,
    }
    for name, table in output_tables.items():
        table.to_csv(RESULTS_DIR / name, index=False, date_format="%Y-%m-%d")

    _configure_plot_style()
    figures = [
        plot_cost_frontier(point_evaluations, uniform_policy_id),
        plot_cost_comparison(comparison),
        plot_recommended_calendar(recommended_calendar),
        plot_savings_uncertainty(comparison),
    ]

    current_fleet_cost = float(comparison["current_mean_annual_cost"].sum())
    optimal_fleet_cost = float(comparison["optimal_mean_annual_cost"].sum())
    uniform_final = final_evaluations.loc[
        final_evaluations["policy_id"].eq(uniform_policy_id)
    ]
    uniform_fleet_cost = float(uniform_final["mean_annual_cost"].sum())
    key_findings = {
        "analysis_version": "q3-formal-v1",
        "forecast_origin": str(pd.Timestamp(forecast_origin).date()),
        "candidate_policies": len(specs),
        "screening_paths": screening_paths,
        "final_paths": final_paths,
        "validation_paths": validation_paths,
        "objective": "expected pathwise lifecycle annual cost in 10k CNY per year",
        "current_fleet_annual_cost": current_fleet_cost,
        "optimized_fleet_annual_cost": optimal_fleet_cost,
        "fleet_savings_percent": (
            (current_fleet_cost - optimal_fleet_cost) / current_fleet_cost * 100.0
        ),
        "uniform_policy_id": uniform_policy_id,
        "uniform_fleet_annual_cost": uniform_fleet_cost,
        "uniform_gap_to_asset_specific_percent": (
            (uniform_fleet_cost - optimal_fleet_cost) / optimal_fleet_cost * 100.0
        ),
        "optimal_policy_by_asset": dict(
            zip(comparison["asset"], comparison["optimal_policy_id"])
        ),
        "mean_probability_of_positive_saving": float(
            comparison["probability_of_positive_saving"].mean()
        ),
        "low_confidence_assets": comparison.loc[
            comparison["recommendation_confidence"].eq("low"), "asset"
        ].tolist(),
        "maintenance_damage_share_main": MAIN_DAMAGE_SHARE,
        "maintenance_damage_share_sensitivity": list(DAMAGE_SHARES),
        "q2_bridge_mean_absolute_lifetime_difference_years": (
            float(baseline_check["absolute_difference_years"].mean())
            if len(baseline_check)
            else None
        ),
        "q2_bridge_max_absolute_lifetime_difference_years": (
            float(baseline_check["absolute_difference_years"].max())
            if len(baseline_check)
            else None
        ),
        "limitations": [
            "major maintenance has only 17 historical events and suffers indication bias",
            "maintenance damage share is scenario-identified rather than point-identified",
            "small maintenance is unrecorded and held fixed as a background process",
            "no downtime or parallel-capacity constraint was supplied by the problem",
            "state-triggered calendars use the estimated median state rather than future noise foresight",
        ],
        "figures": [path.name for path in figures],
    }
    with (RESULTS_DIR / "q3_key_findings.json").open("w", encoding="utf-8") as file:
        json.dump(key_findings, file, ensure_ascii=False, indent=2)

    return {
        "policy_space": output_tables["q3_policy_space.csv"],
        "maintenance_response": response,
        "response_validation": response_validation,
        "baseline_check": baseline_check,
        "policy_evaluation": policy_evaluations,
        "optimal_policy": optimal_policy,
        "comparison": comparison,
        "recommended_calendar": recommended_calendar,
        "robustness": robustness,
        "figures": figures,
        "key_findings": key_findings,
    }


def optimize_maintenance_policy(*args: Any, **kwargs: Any) -> pd.DataFrame:
    """兼容早期接口：返回逐设备优选策略。"""

    return run_q3_formal(*args, **kwargs)["optimal_policy"]
