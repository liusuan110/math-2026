"""问题二幂律阻尼：追踪高功率脊线并审计内部局部最优。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.optimize import minimize, minimize_scalar


CODE_DIR = Path(__file__).resolve().parents[1]
CONTEST_DIR = CODE_DIR.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q2_power import q2_parameters, shooting_mean_power  # noqa: E402


RIDGE_EXPONENTS = np.linspace(0.0, 0.45, 19)
TRUE_COEFFICIENT_UPPER = 100000.0
# 略低于真实上边界，只用于判断二维搜索是否存在稳定内部驻点。
INTERIOR_AUDIT_UPPER = 99900.0
LOCAL_STARTS = (
    (60000.0, 0.2),
    (75000.0, 0.3),
    (95000.0, 0.4),
)
SCREENING_SETTINGS = {
    "root_tolerance": 1e-7,
    "periodicity_tolerance": 2e-6,
    "maximum_root_evaluations": 80,
    "rtol": 2e-7,
    "atol": 2e-9,
    "max_step_fraction": 1.0 / 30.0,
}
FALLBACK_SETTINGS = {
    "root_tolerance": 1e-9,
    "periodicity_tolerance": 2e-8,
    "maximum_root_evaluations": 120,
    "rtol": 1e-9,
    "atol": 1e-11,
    "max_step_fraction": 1.0 / 90.0,
}


def enforce_acceptance(report: dict[str, object]) -> None:
    failed = [name for name, passed in report["acceptance"].items() if not passed]
    if failed:
        raise AssertionError("幂律脊线精修验收失败：" + "、".join(failed))


def main() -> None:
    params = q2_parameters()
    cache: dict[tuple[float, float], tuple[float, float]] = {}
    fallback_evaluations = 0

    def evaluate(coefficient: float, exponent: float) -> tuple[float, float]:
        nonlocal fallback_evaluations
        coefficient = float(np.clip(coefficient, 0.0, TRUE_COEFFICIENT_UPPER))
        exponent = float(np.clip(exponent, 0.0, 1.0))
        key = (round(coefficient, 6), round(exponent, 10))
        if key not in cache:
            try:
                result = shooting_mean_power(
                    coefficient,
                    exponent,
                    params,
                    **SCREENING_SETTINGS,
                )
            except RuntimeError:
                # 优化器可能短暂探索弱阻尼点；保持闭合标准，不放宽容差。
                result = shooting_mean_power(
                    coefficient,
                    exponent,
                    params,
                    **FALLBACK_SETTINGS,
                )
                fallback_evaluations += 1
            cache[key] = (result.mean_power, result.periodicity_error)
        return cache[key]

    ridge_start = perf_counter()
    ridge_coefficient = np.zeros(RIDGE_EXPONENTS.size)
    ridge_power = np.zeros(RIDGE_EXPONENTS.size)
    ridge_periodicity_error = np.zeros(RIDGE_EXPONENTS.size)
    ridge_success = np.zeros(RIDGE_EXPONENTS.size, dtype=bool)
    ridge_function_evaluations = np.zeros(RIDGE_EXPONENTS.size, dtype=int)

    for index, exponent in enumerate(RIDGE_EXPONENTS):
        optimized = minimize_scalar(
            lambda coefficient: -evaluate(coefficient, exponent)[0],
            bounds=(1.0, TRUE_COEFFICIENT_UPPER - 1.0),
            method="bounded",
            options={"xatol": 2.0, "maxiter": 80},
        )
        ridge_success[index] = optimized.success
        ridge_function_evaluations[index] = int(optimized.nfev)
        ridge_coefficient[index] = float(optimized.x)
        ridge_power[index], ridge_periodicity_error[index] = evaluate(
            optimized.x, exponent
        )
    ridge_seconds = perf_counter() - ridge_start

    ridge_best_index = int(np.argmax(ridge_power))
    boundary_directed = ridge_coefficient >= 0.999 * TRUE_COEFFICIENT_UPPER
    first_boundary_index = (
        int(np.flatnonzero(boundary_directed)[0])
        if np.any(boundary_directed)
        else None
    )

    local_reports: list[dict[str, object]] = []
    local_start = perf_counter()
    for coefficient_start, exponent_start in LOCAL_STARTS:
        scaled_start = np.array(
            [coefficient_start / TRUE_COEFFICIENT_UPPER, exponent_start]
        )
        initial_simplex = np.array(
            [
                scaled_start,
                [
                    min(
                        scaled_start[0] + 0.03,
                        INTERIOR_AUDIT_UPPER / TRUE_COEFFICIENT_UPPER,
                    ),
                    scaled_start[1],
                ],
                [scaled_start[0], min(scaled_start[1] + 0.03, 1.0)],
            ]
        )

        def scaled_objective(scaled: np.ndarray) -> float:
            coefficient = float(scaled[0] * TRUE_COEFFICIENT_UPPER)
            exponent = float(scaled[1])
            return -evaluate(coefficient, exponent)[0]

        optimized = minimize(
            scaled_objective,
            scaled_start,
            method="Nelder-Mead",
            bounds=[
                (1e-5, INTERIOR_AUDIT_UPPER / TRUE_COEFFICIENT_UPPER),
                (0.0, 1.0),
            ],
            options={
                "xatol": 2e-5,
                "fatol": 2e-5,
                "maxfev": 120,
                "initial_simplex": initial_simplex,
            },
        )
        coefficient = float(optimized.x[0] * TRUE_COEFFICIENT_UPPER)
        exponent = float(optimized.x[1])
        mean_power, closure_error = evaluate(coefficient, exponent)
        local_reports.append(
            {
                "start": {
                    "coefficient": coefficient_start,
                    "exponent": exponent_start,
                },
                "success": bool(optimized.success),
                "message": str(optimized.message),
                "function_evaluations": int(optimized.nfev),
                "candidate": {
                    "coefficient": coefficient,
                    "exponent": exponent,
                    "mean_power_W": mean_power,
                    "periodicity_error": closure_error,
                },
                "reaches_interior_audit_cap": bool(
                    coefficient >= 0.998 * TRUE_COEFFICIENT_UPPER
                ),
            }
        )
    local_seconds = perf_counter() - local_start

    local_coefficients = np.array(
        [item["candidate"]["coefficient"] for item in local_reports]
    )
    local_exponents = np.array(
        [item["candidate"]["exponent"] for item in local_reports]
    )
    local_powers = np.array(
        [item["candidate"]["mean_power_W"] for item in local_reports]
    )

    report: dict[str, object] = {
        "status": "pending_acceptance",
        "model": "CUMCM 2022 A, question 2, nonlinear interior ridge refinement",
        "scope": "interior ridge only; true coefficient upper boundary not optimized",
        "ridge_trace": {
            "exponents": RIDGE_EXPONENTS.tolist(),
            "best_coefficient_by_exponent": ridge_coefficient.tolist(),
            "best_mean_power_W_by_exponent": ridge_power.tolist(),
            "periodicity_error": ridge_periodicity_error.tolist(),
            "optimizer_success": ridge_success.tolist(),
            "function_evaluations": ridge_function_evaluations.tolist(),
            "wall_time_s": ridge_seconds,
            "sampled_ridge_best": {
                "coefficient": float(ridge_coefficient[ridge_best_index]),
                "exponent": float(RIDGE_EXPONENTS[ridge_best_index]),
                "mean_power_W": float(ridge_power[ridge_best_index]),
            },
            "first_exponent_directed_to_upper_boundary": (
                float(RIDGE_EXPONENTS[first_boundary_index])
                if first_boundary_index is not None
                else None
            ),
        },
        "interior_multistart_audit": {
            "coefficient_cap": INTERIOR_AUDIT_UPPER,
            "purpose": "detect an interior stationary point without claiming boundary optimum",
            "runs": local_reports,
            "wall_time_s": local_seconds,
            "coefficient_range": [
                float(np.min(local_coefficients)),
                float(np.max(local_coefficients)),
            ],
            "exponent_range": [
                float(np.min(local_exponents)),
                float(np.max(local_exponents)),
            ],
            "power_range_W": [
                float(np.min(local_powers)),
                float(np.max(local_powers)),
            ],
        },
        "interpretation": {
            "stable_interior_stationary_point_detected": False,
            "all_multistarts_move_toward_coefficient_upper_boundary": True,
            "next_required_check": "optimize exponent on the true coefficient=100000 boundary",
        },
        "computation": {
            "unique_power_evaluations": len(cache),
            "strict_fallback_evaluations": fallback_evaluations,
            "total_wall_time_s": ridge_seconds + local_seconds,
        },
        "acceptance": {
            "all_ridge_optimizers_succeeded": bool(np.all(ridge_success)),
            "ridge_coefficient_is_nondecreasing": bool(
                np.all(np.diff(ridge_coefficient) >= -5.0)
            ),
            "ridge_reaches_coefficient_upper_neighborhood": bool(
                np.any(boundary_directed)
            ),
            "all_local_runs_succeeded": all(
                item["success"] for item in local_reports
            ),
            "all_local_runs_reach_audit_cap": all(
                item["reaches_interior_audit_cap"] for item in local_reports
            ),
            "local_exponent_candidates_agree": bool(
                np.ptp(local_exponents) < 0.005
            ),
            "local_power_candidates_agree": bool(np.ptp(local_powers) < 0.01),
            "local_refinement_improves_coarse_grid_best": bool(
                np.min(local_powers) > 229.9166675522596
            ),
            "all_periodicity_errors_pass": bool(
                max(
                    float(np.max(ridge_periodicity_error)),
                    max(
                        item["candidate"]["periodicity_error"]
                        for item in local_reports
                    ),
                )
                <= SCREENING_SETTINGS["periodicity_tolerance"]
            ),
        },
    }
    enforce_acceptance(report)
    report["status"] = "passed"

    models_dir = CONTEST_DIR / "results" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        models_dir / "q2_nonlinear_ridge_trace.npz",
        exponent=RIDGE_EXPONENTS,
        coefficient=ridge_coefficient,
        mean_power=ridge_power,
        periodicity_error=ridge_periodicity_error,
    )
    with (models_dir / "q2_nonlinear_ridge_refinement.json").open(
        "w", encoding="utf-8"
    ) as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
