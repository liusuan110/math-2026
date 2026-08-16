"""验证问题二幂律阻尼二维分层搜索所需的快速目标函数设置。

本脚本只比较预先固定的哨兵参数点，不搜索最优参数。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1]
CONTEST_DIR = CODE_DIR.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q2_power import (  # noqa: E402
    constant_mean_power,
    periodic_mean_power,
    q2_parameters,
    shooting_mean_power,
)


# 固定哨兵点覆盖线性退化、低功率内部点、高指数点和接近上边界的高功率点。
SENTINEL_POINTS = (
    (10000.0, 0.0),
    (10000.0, 0.5),
    (50000.0, 1.0),
    (90000.0, 0.25),
)

SCREENING_SETTINGS = {
    "root_tolerance": 1e-7,
    "periodicity_tolerance": 2e-6,
    "maximum_root_evaluations": 80,
    "rtol": 2e-7,
    "atol": 2e-9,
    "max_step_fraction": 1.0 / 30.0,
}

STRICT_SETTINGS = {
    "root_tolerance": 1e-11,
    "periodicity_tolerance": 1e-10,
    "maximum_root_evaluations": 150,
    "rtol": 1e-11,
    "atol": 1e-13,
    "max_step_fraction": 1.0 / 180.0,
}


def relative_error(value: float, reference: float) -> float:
    return abs(value - reference) / max(abs(reference), 1e-15)


def enforce_acceptance(report: dict[str, object]) -> None:
    failed = [name for name, passed in report["acceptance"].items() if not passed]
    if failed:
        raise AssertionError("幂律搜索设计验收失败：" + "、".join(failed))


def main() -> None:
    params = q2_parameters()
    point_reports: list[dict[str, object]] = []

    for coefficient, exponent in SENTINEL_POINTS:
        screening_start = perf_counter()
        screening = shooting_mean_power(
            coefficient,
            exponent,
            params,
            **SCREENING_SETTINGS,
        )
        screening_seconds = perf_counter() - screening_start

        strict_start = perf_counter()
        strict = shooting_mean_power(
            coefficient,
            exponent,
            params,
            initial_state=screening.periodic_state,
            **STRICT_SETTINGS,
        )
        strict_seconds = perf_counter() - strict_start

        if exponent == 0.0:
            reference_power = constant_mean_power(coefficient, params).mean_power
            reference_kind = "frequency-domain exact solution"
            reference_seconds = 0.0
            reference_cycles = 0
            reference_ode_evaluations = 0
            reference_state_error = 0.0
        else:
            reference_start = perf_counter()
            reference = periodic_mean_power(
                coefficient,
                exponent,
                params,
                convergence_tolerance=1e-10,
                required_consecutive_cycles=4,
                rtol=1e-10,
                atol=1e-12,
            )
            reference_seconds = perf_counter() - reference_start
            reference_power = reference.mean_power
            reference_kind = "cold-start long-transient periodic convergence"
            reference_cycles = reference.cycles
            reference_ode_evaluations = reference.function_evaluations
            reference_state_error = reference.convergence_error

        point_reports.append(
            {
                "coefficient": coefficient,
                "exponent": exponent,
                "screening": {
                    "mean_power_W": screening.mean_power,
                    "periodicity_error": screening.periodicity_error,
                    "root_success": screening.root_success,
                    "root_map_evaluations": screening.root_map_evaluations,
                    "ode_function_evaluations": screening.ode_function_evaluations,
                    "wall_time_s": screening_seconds,
                },
                "strict": {
                    "mean_power_W": strict.mean_power,
                    "periodicity_error": strict.periodicity_error,
                    "root_success": strict.root_success,
                    "root_map_evaluations": strict.root_map_evaluations,
                    "ode_function_evaluations": strict.ode_function_evaluations,
                    "wall_time_s": strict_seconds,
                },
                "independent_reference": {
                    "kind": reference_kind,
                    "mean_power_W": reference_power,
                    "cycles": reference_cycles,
                    "state_error": reference_state_error,
                    "ode_function_evaluations": reference_ode_evaluations,
                    "wall_time_s": reference_seconds,
                },
                "screening_to_strict_relative_error": relative_error(
                    screening.mean_power, strict.mean_power
                ),
                "strict_to_reference_relative_error": relative_error(
                    strict.mean_power, reference_power
                ),
                "ode_evaluation_speedup_over_reference": (
                    reference_ode_evaluations / screening.ode_function_evaluations
                    if reference_ode_evaluations
                    else None
                ),
            }
        )

    screening_power = np.array(
        [point["screening"]["mean_power_W"] for point in point_reports]
    )
    strict_power = np.array(
        [point["strict"]["mean_power_W"] for point in point_reports]
    )
    screening_order = np.argsort(-screening_power).tolist()
    strict_order = np.argsort(-strict_power).tolist()
    nonlinear_points = [point for point in point_reports if point["exponent"] > 0.0]

    report: dict[str, object] = {
        "status": "pending_acceptance",
        "purpose": "validate evaluator settings before nonlinear optimization",
        "optimization_executed": False,
        "sentinel_points": point_reports,
        "ranking": {
            "screening_descending_indices": screening_order,
            "strict_descending_indices": strict_order,
            "preserved": screening_order == strict_order,
        },
        "search_design": {
            "stage_1": "21 x 11 full-domain grid using screening shooting settings",
            "stage_2": "refine cells surrounding separated high-power grid candidates",
            "stage_3": "bounded multi-start local refinement from separated candidates",
            "stage_4": "strict shooting recomputation and local perturbation checks",
            "stage_5": "independent cold-start long-transient verification only at finalists",
            "continuation": "reuse neighboring periodic state as the next shooting initial guess",
            "zero_boundary": "treat coefficient=0 as an exact zero-power boundary",
        },
        "acceptance": {
            "all_screening_roots_converged": all(
                point["screening"]["root_success"] for point in point_reports
            ),
            "all_strict_roots_converged": all(
                point["strict"]["root_success"] for point in point_reports
            ),
            "screening_power_error_below_1e-5": max(
                point["screening_to_strict_relative_error"] for point in point_reports
            )
            < 1e-5,
            "strict_reference_error_below_1e-8": max(
                point["strict_to_reference_relative_error"] for point in point_reports
            )
            < 1e-8,
            "screening_preserves_sentinel_ranking": screening_order == strict_order,
            "nonlinear_speedup_exceeds_20x": min(
                point["ode_evaluation_speedup_over_reference"]
                for point in nonlinear_points
            )
            > 20.0,
        },
    }
    enforce_acceptance(report)
    report["status"] = "passed"

    models_dir = CONTEST_DIR / "results" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    with (models_dir / "q2_nonlinear_search_design_validation.json").open(
        "w", encoding="utf-8"
    ) as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
