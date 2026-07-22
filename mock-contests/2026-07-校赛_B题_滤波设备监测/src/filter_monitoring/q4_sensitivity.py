"""问题四：价格波动下的策略稳定区、切换边界与鲁棒方案。

问题三已经把每条物理路径的寿命和中/大维护次数固定下来。价格变化
不会改变这些物理量，因此本模块先把路径级年均成本拆成购置、中维护、
大维护三个线性系数，再在同一批公共随机路径上精确重定价。这样既避免
为每个价格点重复拟合物理模型，也保证价格敏感性与问题三口径一致。
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Matplotlib 缓存必须在导入 pyplot 前指向可写临时目录。
_CACHE_ROOT = Path(tempfile.gettempdir()) / "math2026-filter-monitoring"
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(_CACHE_ROOT / "xdg"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from scipy.optimize import Bounds, LinearConstraint, milp

from .config import (
    ASSETS,
    BASE_COSTS,
    FIGURES_DIR,
    RESULTS_DIR,
    CostConfig,
    ensure_output_dirs,
)
from .q1_analysis import _configure_plot_style, _save_figure
from .q2_lifetime import (
    FORECAST_HORIZON_YEARS,
    estimate_fixed_schedule,
    fit_hierarchical_state_model,
    residual_outlier_sensitivity,
    structural_sensitivity_models,
)
from .q3_optimization import (
    SEARCH_SEED,
    PolicySpec,
    _load_q3_inputs,
    _select_with_tie_break,
    build_policy_frame,
    build_policy_space,
    estimate_maintenance_response,
    historical_maintenance_rates,
    run_q3_formal,
    simulate_policy_asset,
)


Q4_PATHS = 2000
Q4_SEED = SEARCH_SEED
NEAR_OPTIMAL_TOLERANCE = 0.01
COMMON_PRICE_RATIOS = tuple(np.round(np.arange(0.60, 1.4001, 0.05), 2))
SPLIT_MAINTENANCE_RATIOS = tuple(np.round(np.arange(0.50, 2.0001, 0.10), 2))
ONE_FACTOR_RATIOS = tuple(np.round(np.arange(0.25, 3.0001, 0.01), 2))


@dataclass(frozen=True)
class PriceScenario:
    """一个可直接用于路径重定价的价格场景，单位为万元。"""

    scenario_id: str
    purchase_ratio: float
    medium_ratio: float
    major_ratio: float
    purchase_cost: float
    medium_cost: float
    major_cost: float


def build_price_grid(
    purchase_ratios: Iterable[float] = (0.8, 0.9, 1.0, 1.1, 1.2),
    maintenance_ratios: Iterable[float] = (0.8, 0.9, 1.0, 1.1, 1.2),
    base: CostConfig = BASE_COSTS,
) -> pd.DataFrame:
    """生成购置价与中/大维护共同倍率的二维网格。"""

    rows: list[dict[str, Any]] = []
    for purchase_ratio in purchase_ratios:
        for maintenance_ratio in maintenance_ratios:
            pr = float(purchase_ratio)
            mr = float(maintenance_ratio)
            rows.append(
                {
                    "scenario_id": f"purchase_{pr:.2f}_maintenance_{mr:.2f}",
                    "purchase_ratio": pr,
                    "maintenance_ratio": mr,
                    "medium_ratio": mr,
                    "major_ratio": mr,
                    "purchase_cost": base.purchase * pr,
                    "medium_cost": base.medium * mr,
                    "major_cost": base.major * mr,
                }
            )
    return pd.DataFrame(rows)


def build_split_maintenance_grid(
    medium_ratios: Iterable[float] = SPLIT_MAINTENANCE_RATIOS,
    major_ratios: Iterable[float] = SPLIT_MAINTENANCE_RATIOS,
    base: CostConfig = BASE_COSTS,
) -> pd.DataFrame:
    """在购置价固定时分别扰动中维护与大维护价格。"""

    rows: list[dict[str, Any]] = []
    for medium_ratio in medium_ratios:
        for major_ratio in major_ratios:
            mr = float(medium_ratio)
            br = float(major_ratio)
            rows.append(
                {
                    "scenario_id": f"medium_{mr:.2f}_major_{br:.2f}",
                    "purchase_ratio": 1.0,
                    "maintenance_ratio": np.nan,
                    "medium_ratio": mr,
                    "major_ratio": br,
                    "purchase_cost": base.purchase,
                    "medium_cost": base.medium * mr,
                    "major_cost": base.major * br,
                }
            )
    return pd.DataFrame(rows)


def _validate_coefficients(coefficients: pd.DataFrame) -> None:
    required = {
        "asset",
        "policy_id",
        "purchase_annuity_factor",
        "medium_annuity_factor",
        "major_annuity_factor",
        "mean_future_medium_events",
        "mean_future_major_events",
        "median_total_lifetime_years",
    }
    missing = required - set(coefficients.columns)
    if missing:
        raise ValueError(f"价格系数表缺少字段：{sorted(missing)}")
    factors = coefficients[
        [
            "purchase_annuity_factor",
            "medium_annuity_factor",
            "major_annuity_factor",
        ]
    ]
    if factors.isna().any().any() or (factors < 0.0).any().any():
        raise ValueError("价格年化系数必须为非负有限数")


def reprice_policy_coefficients(
    coefficients: pd.DataFrame,
    purchase_cost: float,
    medium_cost: float,
    major_cost: float,
) -> pd.DataFrame:
    """不改变寿命和维护次数，只重算期望年均成本。"""

    _validate_coefficients(coefficients)
    if min(purchase_cost, medium_cost, major_cost) < 0.0:
        raise ValueError("价格不得为负")
    out = coefficients.copy()
    out["mean_annual_cost"] = (
        float(purchase_cost) * out["purchase_annuity_factor"]
        + float(medium_cost) * out["medium_annuity_factor"]
        + float(major_cost) * out["major_annuity_factor"]
    )
    return out


def _plan_signature(rows: pd.DataFrame) -> str:
    mapping = rows.set_index("asset")["policy_id"].astype(str).to_dict()
    return ";".join(f"{asset}={mapping[asset]}" for asset in ASSETS)


def _mapping_signature(mapping: Mapping[str, str]) -> str:
    return ";".join(f"{asset}={mapping[asset]}" for asset in ASSETS)


def _select_asset_rows(scored: pd.DataFrame) -> pd.DataFrame:
    selected: list[pd.Series] = []
    for asset in ASSETS:
        block = scored.loc[scored["asset"].astype(str).eq(asset)]
        if block.empty:
            raise ValueError(f"价格候选中缺少设备 {asset}")
        selected.append(_select_with_tie_break(block))
    return pd.DataFrame(selected).reset_index(drop=True)


def _uniform_scores(scored: pd.DataFrame) -> pd.DataFrame:
    eligible = scored.loc[~scored["policy_id"].eq("current")].copy()
    counts = eligible.groupby("policy_id")["asset"].nunique()
    complete = counts.loc[counts.eq(len(ASSETS))].index
    eligible = eligible.loc[eligible["policy_id"].isin(complete)]
    if eligible.empty:
        raise ValueError("没有覆盖全部设备的统一候选策略")
    return (
        eligible.groupby(["policy_id", "policy_kind"], as_index=False)
        .agg(
            mean_annual_cost=("mean_annual_cost", "sum"),
            mean_future_medium_events=("mean_future_medium_events", "sum"),
            mean_future_major_events=("mean_future_major_events", "sum"),
            median_total_lifetime_years=("median_total_lifetime_years", "mean"),
            operational_feasible=("operational_feasible", "all"),
        )
    )


def _evaluate_price_grid(
    coefficients: pd.DataFrame,
    price_grid: pd.DataFrame,
    baseline_plan: Mapping[str, str],
    uniform_baseline_policy: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    _validate_coefficients(coefficients)
    baseline_signature = _mapping_signature(baseline_plan)
    summary_rows: list[dict[str, Any]] = []
    selection_rows: list[pd.DataFrame] = []

    for scenario in price_grid.to_dict(orient="records"):
        scored = reprice_policy_coefficients(
            coefficients,
            float(scenario["purchase_cost"]),
            float(scenario["medium_cost"]),
            float(scenario["major_cost"]),
        )
        selected = _select_asset_rows(scored)
        selected_signature = _plan_signature(selected)
        theoretical_min = float(
            scored.groupby("asset", sort=False)["mean_annual_cost"].min().sum()
        )
        selected_cost = float(selected["mean_annual_cost"].sum())
        baseline_cost = 0.0
        for asset in ASSETS:
            policy_id = str(baseline_plan[asset])
            row = scored.loc[
                scored["asset"].astype(str).eq(asset)
                & scored["policy_id"].astype(str).eq(policy_id)
            ]
            if len(row) != 1:
                raise ValueError(f"候选表缺少基准策略 {asset}/{policy_id}")
            baseline_cost += float(row.iloc[0]["mean_annual_cost"])

        uniform = _uniform_scores(scored)
        uniform_minimum = float(uniform["mean_annual_cost"].min())
        uniform_selected = _select_with_tie_break(uniform)
        uniform_policy_id = str(uniform_selected["policy_id"])
        uniform_selected_cost = float(uniform_selected["mean_annual_cost"])
        uniform_baseline = uniform.loc[
            uniform["policy_id"].astype(str).eq(uniform_baseline_policy)
        ]
        if len(uniform_baseline) != 1:
            raise ValueError(f"缺少全厂基准策略 {uniform_baseline_policy}")
        uniform_baseline_cost = float(uniform_baseline.iloc[0]["mean_annual_cost"])

        row = dict(scenario)
        row.update(
            {
                "optimal_plan_signature": selected_signature,
                "q3_plan_signature": baseline_signature,
                "theoretical_min_fleet_cost": theoretical_min,
                "recommended_optimal_fleet_cost": selected_cost,
                "recommended_rule_regret_percent": (
                    (selected_cost - theoretical_min) / theoretical_min * 100.0
                ),
                "q3_plan_fleet_cost": baseline_cost,
                "q3_plan_regret_percent": (
                    (baseline_cost - theoretical_min) / theoretical_min * 100.0
                ),
                "q3_plan_exactly_selected": selected_signature == baseline_signature,
                "q3_plan_within_1pct": baseline_cost
                <= theoretical_min * (1.0 + NEAR_OPTIMAL_TOLERANCE),
                "selected_mean_lifetime_years": float(
                    selected["median_total_lifetime_years"].mean()
                ),
                "selected_operational_feasible": bool(
                    selected["operational_feasible"].all()
                ),
                "q3_plan_operational_feasible": True,
                "uniform_optimal_policy_id": uniform_policy_id,
                "uniform_theoretical_min_cost": uniform_minimum,
                "uniform_recommended_cost": uniform_selected_cost,
                "uniform_q3_policy_id": uniform_baseline_policy,
                "uniform_q3_cost": uniform_baseline_cost,
                "uniform_q3_regret_percent": (
                    (uniform_baseline_cost - uniform_minimum)
                    / uniform_minimum
                    * 100.0
                ),
                "uniform_q3_exactly_selected": uniform_policy_id
                == uniform_baseline_policy,
                "uniform_q3_within_1pct": uniform_baseline_cost
                <= uniform_minimum * (1.0 + NEAR_OPTIMAL_TOLERANCE),
            }
        )
        summary_rows.append(row)
        selected_out = selected[
            [
                "asset",
                "policy_id",
                "policy_kind",
                "mean_annual_cost",
                "median_total_lifetime_years",
                "mean_future_medium_events",
                "mean_future_major_events",
                "operational_feasible",
            ]
        ].copy()
        selected_out.insert(0, "scenario_id", str(scenario["scenario_id"]))
        selection_rows.append(selected_out)

    return pd.DataFrame(summary_rows), pd.concat(selection_rows, ignore_index=True)


def evaluate_optimal_policy_grid(
    coefficients: pd.DataFrame,
    price_grid: pd.DataFrame,
    baseline_plan: Mapping[str, str],
    uniform_baseline_policy: str,
) -> pd.DataFrame:
    """公开入口：返回逐价格场景重新选择后的全厂摘要。"""

    summary, _ = _evaluate_price_grid(
        coefficients,
        price_grid,
        baseline_plan,
        uniform_baseline_policy,
    )
    return summary


def contiguous_interval_containing_one(
    factors: Sequence[float],
    stable: Sequence[bool],
) -> tuple[float, float]:
    """返回包含倍率 1 的连续稳定区间；基准点不稳定则返回 NaN。"""

    values = np.asarray(factors, dtype=float)
    mask = np.asarray(stable, dtype=bool)
    if len(values) != len(mask) or len(values) == 0:
        raise ValueError("倍率和稳定标记必须等长且非空")
    order = np.argsort(values)
    values = values[order]
    mask = mask[order]
    center = int(np.argmin(np.abs(values - 1.0)))
    if not np.isclose(values[center], 1.0, atol=1e-8) or not mask[center]:
        return np.nan, np.nan
    left = center
    right = center
    while left > 0 and mask[left - 1]:
        left -= 1
    while right + 1 < len(mask) and mask[right + 1]:
        right += 1
    return float(values[left]), float(values[right])


def _point_cost_coefficients() -> pd.DataFrame:
    evaluation_path = RESULTS_DIR / "q3_policy_evaluation.csv"
    key_path = RESULTS_DIR / "q3_key_findings.json"
    if not evaluation_path.is_file() or not key_path.is_file():
        run_q3_formal()
    evaluations = pd.read_csv(evaluation_path)
    point = evaluations.loc[evaluations["evaluation_stage"].eq("point")].copy()
    if len(point) != len(ASSETS) * 129:
        raise ValueError("问题三点估计策略表不完整，需先重跑 q3")
    inputs = _load_q3_inputs()
    forecast_origin = pd.to_datetime(inputs["panel"]["date"]).max()
    rates = historical_maintenance_rates(inputs["maintenance"], forecast_origin)
    rates = rates[
        [
            "asset",
            "historical_medium_events_equiv",
            "historical_major_events_equiv",
        ]
    ]
    out = point.merge(rates, on="asset", how="left", validate="many_to_one")
    years = out["mean_total_lifetime_years"].to_numpy(dtype=float)
    if np.any(years <= 0.0):
        raise ValueError("问题三策略寿命必须为正")
    out["purchase_annuity_factor"] = 1.0 / years
    out["medium_annuity_factor"] = (
        out["historical_medium_events_equiv"]
        + out["mean_future_medium_events"]
    ) / years
    out["major_annuity_factor"] = (
        out["historical_major_events_equiv"]
        + out["mean_future_major_events"]
    ) / years
    repriced = reprice_policy_coefficients(
        out, BASE_COSTS.purchase, BASE_COSTS.medium, BASE_COSTS.major
    )
    error = np.max(
        np.abs(
            repriced["mean_annual_cost"].to_numpy(dtype=float)
            - point["mean_annual_cost"].to_numpy(dtype=float)
        )
    )
    if error > 1e-8:
        raise AssertionError(f"问题三基准成本分解误差过大：{error}")
    out["operational_feasible"] = True
    return out


def _one_factor_price_table(base: CostConfig = BASE_COSTS) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for factor_name in ("purchase", "maintenance", "medium", "major"):
        for ratio in ONE_FACTOR_RATIOS:
            pr = ratio if factor_name == "purchase" else 1.0
            mr = ratio if factor_name in ("maintenance", "medium") else 1.0
            br = ratio if factor_name in ("maintenance", "major") else 1.0
            rows.append(
                {
                    "scenario_id": f"factor_{factor_name}_{ratio:.2f}",
                    "factor_name": factor_name,
                    "factor_ratio": ratio,
                    "purchase_ratio": pr,
                    "maintenance_ratio": ratio
                    if factor_name == "maintenance"
                    else np.nan,
                    "medium_ratio": mr,
                    "major_ratio": br,
                    "purchase_cost": base.purchase * pr,
                    "medium_cost": base.medium * mr,
                    "major_cost": base.major * br,
                }
            )
    return pd.DataFrame(rows)


def _screen_candidate_pairs(
    point_coefficients: pd.DataFrame,
    price_tables: Sequence[pd.DataFrame],
    baseline_plan: Mapping[str, str],
    uniform_baseline_policy: str,
) -> set[tuple[str, str]]:
    """用全部129组点估计保留每个价格点前两名，再做路径复验。"""

    pairs: set[tuple[str, str]] = {
        (asset, str(baseline_plan[asset])) for asset in ASSETS
    }
    pairs.update((asset, "current") for asset in ASSETS)
    uniform_candidates = {uniform_baseline_policy}

    for table in price_tables:
        for scenario in table.to_dict(orient="records"):
            scored = reprice_policy_coefficients(
                point_coefficients,
                float(scenario["purchase_cost"]),
                float(scenario["medium_cost"]),
                float(scenario["major_cost"]),
            )
            for asset, block in scored.groupby("asset", sort=False):
                pairs.update(
                    (str(asset), str(policy_id))
                    for policy_id in block.nsmallest(2, "mean_annual_cost")[
                        "policy_id"
                    ]
                )
            uniform = _uniform_scores(scored)
            uniform_candidates.add(
                str(uniform.nsmallest(1, "mean_annual_cost").iloc[0]["policy_id"])
            )

    pairs.update(
        (asset, policy_id)
        for policy_id in uniform_candidates
        for asset in ASSETS
    )
    return pairs


def _build_physical_context(
    forecast_horizon_years: int = FORECAST_HORIZON_YEARS,
) -> dict[str, Any]:
    inputs = _load_q3_inputs()
    panel = inputs["panel"]
    maintenance = inputs["maintenance"]
    response = estimate_maintenance_response(inputs["effects"])
    main_model = fit_hierarchical_state_model(
        panel, reference_date=panel["date"].min()
    )
    outlier_path = RESULTS_DIR / "q1_residual_outliers.csv"
    residual_outliers = (
        pd.read_csv(outlier_path, parse_dates=["date"])
        if outlier_path.is_file()
        else pd.DataFrame(columns=["asset", "date", "is_residual_outlier"])
    )
    clean_model, _ = residual_outlier_sensitivity(
        panel, main_model, residual_outliers
    )
    scenario_models, _ = structural_sensitivity_models(panel)
    scenario_models = list(scenario_models) + [clean_model]
    fixed_schedule = estimate_fixed_schedule(maintenance)
    forecast_origin = pd.to_datetime(panel["date"]).max()
    forecast_end = forecast_origin + pd.DateOffset(years=forecast_horizon_years)
    rates = historical_maintenance_rates(maintenance, forecast_origin)
    rates_lookup = rates.set_index("asset").to_dict(orient="index")
    specs = build_policy_space()
    spec_lookup = {spec.policy_id: spec for spec in specs}
    frame_cache: dict[tuple[str, str], pd.DataFrame] = {}

    def make_frame(asset: str, policy_id: str) -> pd.DataFrame:
        key = (asset, policy_id)
        if key not in frame_cache:
            frame_cache[key] = build_policy_frame(
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
        return frame_cache[key]

    return {
        "panel": panel,
        "maintenance": maintenance,
        "response": response,
        "main_model": main_model,
        "scenario_models": scenario_models,
        "forecast_origin": forecast_origin,
        "rates": rates,
        "rates_lookup": rates_lookup,
        "spec_lookup": spec_lookup,
        "make_frame": make_frame,
    }


def _simulate_price_coefficients(
    candidate_pairs: set[tuple[str, str]],
    *,
    paths: int,
    seed: int,
) -> tuple[pd.DataFrame, dict[tuple[str, str], pd.DataFrame]]:
    context = _build_physical_context()
    panel = context["panel"]
    response = context["response"]
    scenario_models = context["scenario_models"]
    forecast_origin = context["forecast_origin"]
    rates_lookup = context["rates_lookup"]
    spec_lookup: Mapping[str, PolicySpec] = context["spec_lookup"]
    make_frame = context["make_frame"]
    distributions: dict[tuple[str, str], pd.DataFrame] = {}
    rows: list[dict[str, Any]] = []
    asset_order = {asset: index for index, asset in enumerate(ASSETS)}

    for asset, policy_id in sorted(
        candidate_pairs, key=lambda item: (asset_order[item[0]], item[1])
    ):
        spec = spec_lookup[policy_id]
        summary, distribution = simulate_policy_asset(
            spec,
            asset,
            make_frame(asset, policy_id),
            panel,
            scenario_models,
            response,
            rates_lookup[asset],
            forecast_origin,
            paths=paths,
            seed=seed,
            costs=BASE_COSTS,
            evaluation_stage="q4_price_repricing",
        )
        years = distribution["total_lifetime_years"].to_numpy(dtype=float)
        med_events = (
            float(rates_lookup[asset]["historical_medium_events_equiv"])
            + distribution["future_medium_events"].to_numpy(dtype=float)
        )
        major_events = (
            float(rates_lookup[asset]["historical_major_events_equiv"])
            + distribution["future_major_events"].to_numpy(dtype=float)
        )
        factor_distribution = pd.DataFrame(
            {
                "path_id": distribution["path_id"].to_numpy(dtype=int),
                "purchase_annuity_factor": 1.0 / years,
                "medium_annuity_factor": med_events / years,
                "major_annuity_factor": major_events / years,
                "total_lifetime_years": years,
            }
        )
        distributions[(asset, policy_id)] = factor_distribution
        row = dict(summary)
        row.update(
            {
                "purchase_annuity_factor": float(
                    factor_distribution["purchase_annuity_factor"].mean()
                ),
                "medium_annuity_factor": float(
                    factor_distribution["medium_annuity_factor"].mean()
                ),
                "major_annuity_factor": float(
                    factor_distribution["major_annuity_factor"].mean()
                ),
                "base_repriced_mean_annual_cost": float(
                    BASE_COSTS.purchase
                    * factor_distribution["purchase_annuity_factor"].mean()
                    + BASE_COSTS.medium
                    * factor_distribution["medium_annuity_factor"].mean()
                    + BASE_COSTS.major
                    * factor_distribution["major_annuity_factor"].mean()
                ),
                "operational_feasible": True,
                "policy_description": spec.description,
            }
        )
        rows.append(row)

    coefficients = pd.DataFrame(rows)
    max_error = float(
        np.max(
            np.abs(
                coefficients["mean_annual_cost"]
                - coefficients["base_repriced_mean_annual_cost"]
            )
        )
    )
    if max_error > 1e-8:
        raise AssertionError(f"路径重定价未复现基准成本：{max_error}")
    return coefficients, distributions


def _factor_sensitivity(
    coefficients: pd.DataFrame,
    factors: pd.DataFrame,
    baseline_plan: Mapping[str, str],
    uniform_baseline_policy: str,
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for factor_name, table in factors.groupby("factor_name", sort=False):
        summary, _ = _evaluate_price_grid(
            coefficients,
            table,
            baseline_plan,
            uniform_baseline_policy,
        )
        summary["factor_name"] = factor_name
        summary["factor_ratio"] = table["factor_ratio"].to_numpy(dtype=float)
        rows.append(summary)
    return pd.concat(rows, ignore_index=True)


def _switch_interval_table(one_factor: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for factor_name, block in one_factor.groupby("factor_name", sort=False):
        block = block.sort_values("factor_ratio")
        factors = block["factor_ratio"].to_numpy(dtype=float)
        for plan_scope, exact_col, near_col in (
            (
                "asset_specific_q3_plan",
                "q3_plan_exactly_selected",
                "q3_plan_within_1pct",
            ),
            (
                "uniform_q3_plan",
                "uniform_q3_exactly_selected",
                "uniform_q3_within_1pct",
            ),
        ):
            exact_low, exact_high = contiguous_interval_containing_one(
                factors, block[exact_col].to_numpy(dtype=bool)
            )
            near_low, near_high = contiguous_interval_containing_one(
                factors, block[near_col].to_numpy(dtype=bool)
            )
            rows.append(
                {
                    "factor_name": factor_name,
                    "plan_scope": plan_scope,
                    "exact_optimal_low_ratio": exact_low,
                    "exact_optimal_high_ratio": exact_high,
                    "within_1pct_low_ratio": near_low,
                    "within_1pct_high_ratio": near_high,
                    "scan_low_ratio": float(factors.min()),
                    "scan_high_ratio": float(factors.max()),
                    "exact_low_truncated": bool(
                        np.isfinite(exact_low) and exact_low == factors.min()
                    ),
                    "exact_high_truncated": bool(
                        np.isfinite(exact_high) and exact_high == factors.max()
                    ),
                    "near_low_truncated": bool(
                        np.isfinite(near_low) and near_low == factors.min()
                    ),
                    "near_high_truncated": bool(
                        np.isfinite(near_high) and near_high == factors.max()
                    ),
                }
            )
    return pd.DataFrame(rows)


def _minimax_asset_plan(
    coefficients: pd.DataFrame,
    price_grid: pd.DataFrame,
) -> tuple[dict[str, str], float, float]:
    """用混合整数线性规划求跨价格场景的全厂最小最大后悔方案。"""

    candidate_rows = coefficients[["asset", "policy_id"]].drop_duplicates().reset_index(drop=True)
    scenario_costs: list[np.ndarray] = []
    optimums: list[float] = []
    for scenario in price_grid.to_dict(orient="records"):
        scored = reprice_policy_coefficients(
            coefficients,
            float(scenario["purchase_cost"]),
            float(scenario["medium_cost"]),
            float(scenario["major_cost"]),
        )
        lookup = scored.set_index(["asset", "policy_id"])["mean_annual_cost"]
        scenario_costs.append(
            np.array(
                [lookup.loc[(row.asset, row.policy_id)] for row in candidate_rows.itertuples()],
                dtype=float,
            )
        )
        optimums.append(
            float(scored.groupby("asset")["mean_annual_cost"].min().sum())
        )
    cost_matrix = np.vstack(scenario_costs)
    optimum = np.asarray(optimums, dtype=float)
    if not np.isfinite(cost_matrix).all() or not np.isfinite(optimum).all():
        raise ValueError("鲁棒优化成本矩阵含非有限数")
    n_candidates = len(candidate_rows)
    n_variables = n_candidates + 1
    objective = np.zeros(n_variables, dtype=float)
    objective[-1] = 1.0
    integrality = np.zeros(n_variables, dtype=int)
    integrality[:n_candidates] = 1
    lower_bounds = np.zeros(n_variables, dtype=float)
    upper_bounds = np.ones(n_variables, dtype=float)
    upper_bounds[-1] = np.inf

    rows: list[np.ndarray] = []
    lower: list[float] = []
    upper: list[float] = []
    for asset in ASSETS:
        equation = np.zeros(n_variables, dtype=float)
        asset_mask = candidate_rows["asset"].astype(str).eq(asset).to_numpy()
        equation[:n_candidates][asset_mask] = 1.0
        rows.append(equation)
        lower.append(1.0)
        upper.append(1.0)
    for index, scenario_cost in enumerate(cost_matrix):
        inequality = np.zeros(n_variables, dtype=float)
        inequality[:n_candidates] = scenario_cost
        inequality[-1] = -optimum[index]
        rows.append(inequality)
        lower.append(-np.inf)
        upper.append(optimum[index])
    result = milp(
        c=objective,
        integrality=integrality,
        bounds=Bounds(lower_bounds, upper_bounds),
        constraints=LinearConstraint(
            np.vstack(rows), np.asarray(lower), np.asarray(upper)
        ),
        options={"time_limit": 60.0},
    )
    if not result.success or result.x is None:
        raise RuntimeError(f"鲁棒方案混合整数规划失败：{result.message}")
    chosen = candidate_rows.loc[result.x[:n_candidates] > 0.5]
    mapping = dict(zip(chosen["asset"].astype(str), chosen["policy_id"].astype(str)))
    if set(mapping) != set(ASSETS):
        raise AssertionError("鲁棒方案没有为每台设备选择一个策略")
    chosen_pairs = set(zip(chosen.asset, chosen.policy_id))
    selected_indices = [
        index
        for index, row in enumerate(candidate_rows.itertuples())
        if (row.asset, row.policy_id) in chosen_pairs
    ]
    plan_cost = cost_matrix[:, selected_indices].sum(axis=1)
    regret = (plan_cost - optimum) / optimum * 100.0
    return mapping, float(np.max(regret)), float(np.mean(regret))


def _minimax_uniform_policy(
    coefficients: pd.DataFrame,
    price_grid: pd.DataFrame,
) -> tuple[str, float, float]:
    policy_ids = sorted(
        policy_id
        for policy_id, block in coefficients.groupby("policy_id")
        if policy_id != "current" and block["asset"].nunique() == len(ASSETS)
    )
    regrets: dict[str, list[float]] = {policy_id: [] for policy_id in policy_ids}
    for scenario in price_grid.to_dict(orient="records"):
        scored = reprice_policy_coefficients(
            coefficients,
            float(scenario["purchase_cost"]),
            float(scenario["medium_cost"]),
            float(scenario["major_cost"]),
        )
        fleet = scored.loc[scored["policy_id"].isin(policy_ids)].groupby(
            "policy_id"
        )["mean_annual_cost"].sum()
        minimum = float(fleet.min())
        for policy_id in policy_ids:
            regrets[policy_id].append(
                (float(fleet.loc[policy_id]) - minimum) / minimum * 100.0
            )
    table = pd.DataFrame(
        {
            "policy_id": policy_ids,
            "max_regret": [max(regrets[p]) for p in policy_ids],
            "mean_regret": [np.mean(regrets[p]) for p in policy_ids],
        }
    ).sort_values(["max_regret", "mean_regret", "policy_id"])
    row = table.iloc[0]
    return str(row["policy_id"]), float(row["max_regret"]), float(row["mean_regret"])


def _short_policy(policy_id: str) -> str:
    if policy_id == "current":
        return "现行"
    match = re.fullmatch(r"periodic_m(\d+)_b(\d+)", policy_id)
    if match:
        medium, major = map(int, match.groups())
        if medium >= major == 365:
            return "年1大"
        return f"中{medium}日/大{major}日"
    match = re.fullmatch(r"trigger_t(\d+)_c(\d+)_b(\d+)", policy_id)
    if match:
        trigger, cooldown, major = match.groups()
        return f"触发{trigger}/冷却{cooldown}/大{major}"
    return policy_id


def _describe_signature(signature: str) -> str:
    mapping = dict(part.split("=", 1) for part in signature.split(";"))
    groups: dict[str, list[str]] = {}
    for asset in ASSETS:
        groups.setdefault(mapping[asset], []).append(asset)
    parts = []
    for policy_id, assets in sorted(groups.items(), key=lambda item: item[0]):
        parts.append(f"{','.join(assets)}:{_short_policy(policy_id)}")
    return "；".join(parts)


def _attach_plan_codes(
    common: pd.DataFrame,
    split: pd.DataFrame,
    one_factor: pd.DataFrame,
    baseline_signature: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    signatures = list(common["optimal_plan_signature"])
    signatures += list(split["optimal_plan_signature"])
    signatures += list(one_factor["optimal_plan_signature"])
    counts = Counter(signatures)
    ordered = [baseline_signature]
    ordered.extend(
        signature
        for signature, _ in counts.most_common()
        if signature != baseline_signature
    )
    code_map = {signature: f"P{index}" for index, signature in enumerate(ordered)}
    for table in (common, split, one_factor):
        table["optimal_plan_code"] = table["optimal_plan_signature"].map(code_map)
    catalog = pd.DataFrame(
        [
            {
                "plan_code": code_map[signature],
                "plan_signature": signature,
                "plan_description": _describe_signature(signature),
                "scenario_count": counts.get(signature, 0),
                "is_q3_baseline_plan": signature == baseline_signature,
            }
            for signature in ordered
        ]
    )
    return common, split, one_factor, catalog


def _plan_cost_distribution(
    plan: Mapping[str, str],
    factor_distributions: Mapping[tuple[str, str], pd.DataFrame],
    purchase_cost: float,
    medium_cost: float,
    major_cost: float,
) -> np.ndarray:
    total: np.ndarray | None = None
    for asset in ASSETS:
        factors = factor_distributions[(asset, str(plan[asset]))]
        cost = (
            purchase_cost * factors["purchase_annuity_factor"].to_numpy(dtype=float)
            + medium_cost * factors["medium_annuity_factor"].to_numpy(dtype=float)
            + major_cost * factors["major_annuity_factor"].to_numpy(dtype=float)
        )
        total = cost.copy() if total is None else total + cost
    if total is None:
        raise ValueError("空维护方案无法计算成本分布")
    return total


def _named_scenario_uncertainty(
    coefficients: pd.DataFrame,
    factor_distributions: Mapping[tuple[str, str], pd.DataFrame],
    baseline_plan: Mapping[str, str],
    robust_plan: Mapping[str, str],
    uniform_baseline_policy: str,
    robust_uniform_policy: str,
) -> pd.DataFrame:
    scenarios = (
        ("baseline", 1.0, 1.0, 1.0),
        ("purchase_down_40pct", 0.6, 1.0, 1.0),
        ("purchase_up_40pct", 1.4, 1.0, 1.0),
        ("maintenance_down_40pct", 1.0, 0.6, 0.6),
        ("maintenance_up_40pct", 1.0, 1.4, 1.4),
        ("purchase_up_maintenance_down", 1.4, 0.6, 0.6),
        ("purchase_down_maintenance_up", 0.6, 1.4, 1.4),
        ("medium_up_major_down", 1.0, 2.0, 0.5),
        ("medium_down_major_up", 1.0, 0.5, 2.0),
    )
    rows: list[dict[str, Any]] = []
    for name, purchase_ratio, medium_ratio, major_ratio in scenarios:
        purchase_cost = BASE_COSTS.purchase * purchase_ratio
        medium_cost = BASE_COSTS.medium * medium_ratio
        major_cost = BASE_COSTS.major * major_ratio
        scored = reprice_policy_coefficients(
            coefficients, purchase_cost, medium_cost, major_cost
        )
        optimal_rows = _select_asset_rows(scored)
        optimal_plan = dict(
            zip(optimal_rows["asset"].astype(str), optimal_rows["policy_id"].astype(str))
        )
        plans = {
            "q3_asset_specific": dict(baseline_plan),
            "reoptimized_asset_specific": optimal_plan,
            "minimax_asset_specific": dict(robust_plan),
            "q3_uniform": {asset: uniform_baseline_policy for asset in ASSETS},
            "minimax_uniform": {asset: robust_uniform_policy for asset in ASSETS},
        }
        theoretical_min = float(
            scored.groupby("asset")["mean_annual_cost"].min().sum()
        )
        for plan_type, plan in plans.items():
            distribution = _plan_cost_distribution(
                plan,
                factor_distributions,
                purchase_cost,
                medium_cost,
                major_cost,
            )
            mean_cost = float(np.mean(distribution))
            rows.append(
                {
                    "scenario": name,
                    "purchase_ratio": purchase_ratio,
                    "medium_ratio": medium_ratio,
                    "major_ratio": major_ratio,
                    "plan_type": plan_type,
                    "plan_signature": _mapping_signature(plan),
                    "mean_fleet_annual_cost": mean_cost,
                    "p10_fleet_annual_cost": float(np.quantile(distribution, 0.10)),
                    "p90_fleet_annual_cost": float(np.quantile(distribution, 0.90)),
                    "regret_percent_vs_theoretical_min": (
                        (mean_cost - theoretical_min) / theoretical_min * 100.0
                    ),
                    "operational_feasible": True,
                }
            )
    return pd.DataFrame(rows)


def plot_price_stability_map(
    price_grid: pd.DataFrame,
    catalog: pd.DataFrame,
) -> Path:
    codes = catalog["plan_code"].tolist()
    code_to_index = {code: index for index, code in enumerate(codes)}
    work = price_grid.copy()
    used_codes = [code for code in codes if code in set(work["optimal_plan_code"])]
    local_index = {code: index for index, code in enumerate(used_codes)}
    work["code_index"] = work["optimal_plan_code"].map(local_index)
    pivot = work.pivot(
        index="maintenance_ratio", columns="purchase_ratio", values="code_index"
    ).sort_index(ascending=True)
    colors = plt.get_cmap("tab20")(np.linspace(0.0, 1.0, max(len(codes), 2)))
    fig, ax = plt.subplots(figsize=(10.5, 7.0))
    used_colors = [colors[code_to_index[code]] for code in used_codes]
    image = ax.imshow(
        pivot.to_numpy(dtype=float),
        origin="lower",
        aspect="auto",
        extent=[
            float(pivot.columns.min()),
            float(pivot.columns.max()),
            float(pivot.index.min()),
            float(pivot.index.max()),
        ],
        interpolation="nearest",
        cmap=ListedColormap(used_colors),
        vmin=-0.5,
        vmax=len(used_codes) - 0.5,
    )
    colorbar = fig.colorbar(
        image,
        ax=ax,
        ticks=range(len(used_codes)),
        fraction=0.055,
        pad=0.03,
    )
    colorbar.ax.set_yticklabels(used_codes)
    colorbar.set_label("方案编号")
    ax.scatter([1.0], [1.0], marker="*", s=115, c="white", edgecolors="black", zorder=3)
    ax.annotate("基准", (1.0, 1.0), xytext=(6, 5), textcoords="offset points")
    ax.set_xlabel("购置价格倍率")
    ax.set_ylabel("中/大维护共同价格倍率")
    ax.set_title("价格波动下逐设备优选方案稳定区域")
    fig.tight_layout()
    return _save_figure(fig, "q4_01_price_stability_map.png")


def plot_q3_plan_regret(price_grid: pd.DataFrame) -> Path:
    pivot = price_grid.pivot(
        index="maintenance_ratio",
        columns="purchase_ratio",
        values="q3_plan_regret_percent",
    ).sort_index(ascending=True)
    x = pivot.columns.to_numpy(dtype=float)
    y = pivot.index.to_numpy(dtype=float)
    z = pivot.to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(9.0, 6.5))
    mesh = ax.pcolormesh(x, y, z, shading="auto", cmap="YlOrRd")
    if float(np.nanmin(z)) <= 1.0 <= float(np.nanmax(z)):
        contour = ax.contour(x, y, z, levels=[1.0], colors="#2457a7", linewidths=1.8)
        ax.clabel(contour, fmt={1.0: "1%近优边界"}, inline=True)
    colorbar = fig.colorbar(mesh, ax=ax)
    colorbar.set_label("问题三逐设备方案后悔值（%）")
    ax.set_xlabel("购置价格倍率")
    ax.set_ylabel("中/大维护共同价格倍率")
    ax.set_title("问题三方案的价格后悔值")
    fig.tight_layout()
    return _save_figure(fig, "q4_02_q3_plan_regret.png")


def plot_split_maintenance_map(
    split_grid: pd.DataFrame,
    catalog: pd.DataFrame,
) -> Path:
    codes = catalog["plan_code"].tolist()
    code_to_index = {code: index for index, code in enumerate(codes)}
    work = split_grid.copy()
    used_codes = [code for code in codes if code in set(work["optimal_plan_code"])]
    local_index = {code: index for index, code in enumerate(used_codes)}
    work["code_index"] = work["optimal_plan_code"].map(local_index)
    pivot = work.pivot(
        index="major_ratio", columns="medium_ratio", values="code_index"
    ).sort_index(ascending=True)
    colors = plt.get_cmap("tab20")(np.linspace(0.0, 1.0, max(len(codes), 2)))
    fig, ax = plt.subplots(figsize=(10.5, 7.0))
    used_colors = [colors[code_to_index[code]] for code in used_codes]
    image = ax.imshow(
        pivot.to_numpy(dtype=float),
        origin="lower",
        aspect="auto",
        extent=[
            float(pivot.columns.min()),
            float(pivot.columns.max()),
            float(pivot.index.min()),
            float(pivot.index.max()),
        ],
        interpolation="nearest",
        cmap=ListedColormap(used_colors),
        vmin=-0.5,
        vmax=len(used_codes) - 0.5,
    )
    colorbar = fig.colorbar(
        image,
        ax=ax,
        ticks=range(len(used_codes)),
        fraction=0.055,
        pad=0.03,
    )
    colorbar.ax.set_yticklabels(used_codes)
    colorbar.set_label("方案编号")
    ax.scatter([1.0], [1.0], marker="*", s=115, c="white", edgecolors="black", zorder=3)
    ax.annotate("基准", (1.0, 1.0), xytext=(6, 5), textcoords="offset points")
    ax.set_xlabel("中维护价格倍率")
    ax.set_ylabel("大维护价格倍率")
    ax.set_title("中、大维护价格分别波动时的方案切换")
    fig.tight_layout()
    return _save_figure(fig, "q4_03_split_maintenance_map.png")


def plot_one_factor_regret(one_factor: pd.DataFrame) -> Path:
    labels = {
        "purchase": "购置价",
        "maintenance": "全部维护价",
        "medium": "中维护价",
        "major": "大维护价",
    }
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.2), sharey=False)
    for ax, factor_name in zip(axes.flat, labels):
        block = one_factor.loc[one_factor["factor_name"].eq(factor_name)].sort_values(
            "factor_ratio"
        )
        ax.plot(
            block["factor_ratio"],
            block["q3_plan_regret_percent"],
            label="逐设备方案",
            color="#2457a7",
        )
        ax.plot(
            block["factor_ratio"],
            block["uniform_q3_regret_percent"],
            label="全厂统一方案",
            color="#d95f02",
        )
        ax.axhline(1.0, color="#777777", ls="--", lw=1.0)
        ax.axvline(1.0, color="#999999", ls=":", lw=1.0)
        ax.set_title(labels[factor_name])
        ax.set_xlabel("价格倍率")
        ax.set_ylabel("后悔值（%）")
        ax.grid(alpha=0.2)
    axes[0, 0].legend(frameon=False)
    fig.suptitle("单项价格波动下问题三方案的经济稳健性")
    fig.tight_layout()
    return _save_figure(fig, "q4_04_one_factor_regret.png")


def run_q4_formal(
    *,
    simulation_paths: int = Q4_PATHS,
    seed: int = Q4_SEED,
) -> dict[str, Any]:
    """运行正式价格敏感性、边界和鲁棒后悔分析。"""

    if simulation_paths <= 0:
        raise ValueError("问题四仿真路径数必须为正")
    ensure_output_dirs()
    q3_key_path = RESULTS_DIR / "q3_key_findings.json"
    if not q3_key_path.is_file():
        run_q3_formal()
    with q3_key_path.open(encoding="utf-8") as file:
        q3_key = json.load(file)
    baseline_plan = {
        str(asset): str(policy_id)
        for asset, policy_id in q3_key["optimal_policy_by_asset"].items()
    }
    uniform_baseline_policy = str(q3_key["uniform_policy_id"])
    baseline_signature = _mapping_signature(baseline_plan)

    point_coefficients = _point_cost_coefficients()
    common_grid = build_price_grid(COMMON_PRICE_RATIOS, COMMON_PRICE_RATIOS)
    split_grid = build_split_maintenance_grid()
    one_factor_prices = _one_factor_price_table()
    candidate_pairs = _screen_candidate_pairs(
        point_coefficients,
        (common_grid, split_grid, one_factor_prices),
        baseline_plan,
        uniform_baseline_policy,
    )
    coefficients, factor_distributions = _simulate_price_coefficients(
        candidate_pairs,
        paths=simulation_paths,
        seed=seed,
    )

    common_summary, common_asset = _evaluate_price_grid(
        coefficients, common_grid, baseline_plan, uniform_baseline_policy
    )
    split_summary, split_asset = _evaluate_price_grid(
        coefficients, split_grid, baseline_plan, uniform_baseline_policy
    )
    one_factor = _factor_sensitivity(
        coefficients, one_factor_prices, baseline_plan, uniform_baseline_policy
    )
    common_summary, split_summary, one_factor, catalog = _attach_plan_codes(
        common_summary,
        split_summary,
        one_factor,
        baseline_signature,
    )
    intervals = _switch_interval_table(one_factor)

    robust_plan, robust_max_regret, robust_mean_regret = _minimax_asset_plan(
        coefficients, common_grid
    )
    robust_uniform, robust_uniform_max, robust_uniform_mean = _minimax_uniform_policy(
        coefficients, common_grid
    )
    robust_rows = [
        {
            "plan_type": "asset_specific_minimax",
            "asset": asset,
            "policy_id": robust_plan[asset],
            "max_regret_percent": robust_max_regret,
            "mean_regret_percent": robust_mean_regret,
        }
        for asset in ASSETS
    ]
    robust_rows.append(
        {
            "plan_type": "uniform_minimax",
            "asset": "ALL",
            "policy_id": robust_uniform,
            "max_regret_percent": robust_uniform_max,
            "mean_regret_percent": robust_uniform_mean,
        }
    )
    robust_table = pd.DataFrame(robust_rows)
    named_uncertainty = _named_scenario_uncertainty(
        coefficients,
        factor_distributions,
        baseline_plan,
        robust_plan,
        uniform_baseline_policy,
        robust_uniform,
    )

    output_tables = {
        "q4_policy_coefficients.csv": coefficients,
        "q4_price_grid.csv": common_summary,
        "q4_asset_selection.csv": common_asset,
        "q4_split_maintenance_grid.csv": split_summary,
        "q4_split_asset_selection.csv": split_asset,
        "q4_plan_catalog.csv": catalog,
        "q4_one_factor_sensitivity.csv": one_factor,
        "q4_switch_intervals.csv": intervals,
        "q4_robust_policy.csv": robust_table,
        "q4_scenario_uncertainty.csv": named_uncertainty,
    }
    for name, table in output_tables.items():
        table.to_csv(RESULTS_DIR / name, index=False)

    _configure_plot_style()
    figures = [
        plot_price_stability_map(common_summary, catalog),
        plot_q3_plan_regret(common_summary),
        plot_split_maintenance_map(split_summary, catalog),
        plot_one_factor_regret(one_factor),
    ]

    interval_lookup = intervals.set_index(["factor_name", "plan_scope"])
    asset_intervals = {
        factor: {
            "exact_low": float(
                interval_lookup.loc[
                    (factor, "asset_specific_q3_plan"),
                    "exact_optimal_low_ratio",
                ]
            ),
            "exact_high": float(
                interval_lookup.loc[
                    (factor, "asset_specific_q3_plan"),
                    "exact_optimal_high_ratio",
                ]
            ),
            "near_low": float(
                interval_lookup.loc[
                    (factor, "asset_specific_q3_plan"),
                    "within_1pct_low_ratio",
                ]
            ),
            "near_high": float(
                interval_lookup.loc[
                    (factor, "asset_specific_q3_plan"),
                    "within_1pct_high_ratio",
                ]
            ),
        }
        for factor in ("purchase", "maintenance", "medium", "major")
    }
    uniform_intervals = {
        factor: {
            "exact_low": float(
                interval_lookup.loc[
                    (factor, "uniform_q3_plan"), "exact_optimal_low_ratio"
                ]
            ),
            "exact_high": float(
                interval_lookup.loc[
                    (factor, "uniform_q3_plan"), "exact_optimal_high_ratio"
                ]
            ),
            "near_low": float(
                interval_lookup.loc[
                    (factor, "uniform_q3_plan"), "within_1pct_low_ratio"
                ]
            ),
            "near_high": float(
                interval_lookup.loc[
                    (factor, "uniform_q3_plan"), "within_1pct_high_ratio"
                ]
            ),
        }
        for factor in ("purchase", "maintenance", "medium", "major")
    }
    key_findings = {
        "analysis_version": "q4-formal-v1",
        "simulation_paths_per_asset_policy": simulation_paths,
        "seed": seed,
        "point_policy_space": int(point_coefficients["policy_id"].nunique()),
        "monte_carlo_candidate_pairs": len(candidate_pairs),
        "common_price_grid_scenarios": len(common_summary),
        "common_price_ratio_range": [
            min(COMMON_PRICE_RATIOS),
            max(COMMON_PRICE_RATIOS),
        ],
        "split_maintenance_grid_scenarios": len(split_summary),
        "split_maintenance_ratio_range": [
            min(SPLIT_MAINTENANCE_RATIOS),
            max(SPLIT_MAINTENANCE_RATIOS),
        ],
        "one_factor_ratio_range": [
            min(ONE_FACTOR_RATIOS),
            max(ONE_FACTOR_RATIOS),
        ],
        "q3_asset_plan_exact_share_common_grid": float(
            common_summary["q3_plan_exactly_selected"].mean()
        ),
        "q3_asset_plan_within_1pct_share_common_grid": float(
            common_summary["q3_plan_within_1pct"].mean()
        ),
        "q3_uniform_plan_exact_share_common_grid": float(
            common_summary["uniform_q3_exactly_selected"].mean()
        ),
        "q3_uniform_plan_within_1pct_share_common_grid": float(
            common_summary["uniform_q3_within_1pct"].mean()
        ),
        "q3_plan_max_regret_common_grid_percent": float(
            common_summary["q3_plan_regret_percent"].max()
        ),
        "q3_uniform_max_regret_common_grid_percent": float(
            common_summary["uniform_q3_regret_percent"].max()
        ),
        "asset_specific_price_intervals": asset_intervals,
        "uniform_price_intervals": uniform_intervals,
        "asset_specific_minimax_plan": robust_plan,
        "asset_specific_minimax_max_regret_percent": robust_max_regret,
        "asset_specific_minimax_mean_regret_percent": robust_mean_regret,
        "uniform_minimax_policy_id": robust_uniform,
        "uniform_minimax_max_regret_percent": robust_uniform_max,
        "uniform_minimax_mean_regret_percent": robust_uniform_mean,
        "operational_feasibility": (
            "价格不进入状态转移，问题三方案寿命、维护次数和1—4次大维护约束均不变"
        ),
        "limitations": [
            "价格网格未包含停机损失和并联产能约束，题目未提供这些成本",
            "价格边界基于问题三候选规则集，不外推到完全不同的维护技术",
            "物理参数不确定性由问题三模型混合路径传播，未假设价格与退化参数相关",
        ],
        "figures": [path.name for path in figures],
    }
    with (RESULTS_DIR / "q4_key_findings.json").open("w", encoding="utf-8") as file:
        json.dump(key_findings, file, ensure_ascii=False, indent=2)

    return {
        "policy_coefficients": coefficients,
        "price_grid": common_summary,
        "asset_selection": common_asset,
        "split_maintenance_grid": split_summary,
        "split_asset_selection": split_asset,
        "plan_catalog": catalog,
        "one_factor_sensitivity": one_factor,
        "switch_intervals": intervals,
        "robust_policy": robust_table,
        "scenario_uncertainty": named_uncertainty,
        "figures": figures,
        "key_findings": key_findings,
    }
