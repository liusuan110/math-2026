"""问题二幂律阻尼：固定 a=100000 后优化真实上边界指数。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.optimize import minimize_scalar


CODE_DIR = Path(__file__).resolve().parents[1]
CONTEST_DIR = CODE_DIR.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q2_power import q2_parameters, shooting_mean_power  # noqa: E402


COEFFICIENT = 100000.0
EXPONENT_GRID = np.linspace(0.0, 1.0, 501)
SCREENING_SETTINGS = {
    "root_tolerance": 1e-7,
    "periodicity_tolerance": 2e-6,
    "maximum_root_evaluations": 80,
    "rtol": 2e-7,
    "atol": 2e-9,
    "max_step_fraction": 1.0 / 30.0,
}
REFINEMENT_SETTINGS = {
    "root_tolerance": 1e-11,
    "periodicity_tolerance": 2e-9,
    "maximum_root_evaluations": 150,
    "rtol": 1e-11,
    "atol": 1e-13,
    "max_step_fraction": 1.0 / 180.0,
}


def count_strict_peaks(values: np.ndarray) -> np.ndarray:
    return np.flatnonzero(
        (values[1:-1] > values[:-2]) & (values[1:-1] > values[2:])
    ) + 1


def enforce_acceptance(report: dict[str, object]) -> None:
    failed = [name for name, passed in report["acceptance"].items() if not passed]
    if failed:
        raise AssertionError("幂律上边界优化验收失败：" + "、".join(failed))


def main() -> None:
    params = q2_parameters()
    power_grid = np.zeros(EXPONENT_GRID.size)
    periodicity_error = np.zeros(EXPONENT_GRID.size)
    root_success = np.zeros(EXPONENT_GRID.size, dtype=bool)
    ode_function_evaluations = np.zeros(EXPONENT_GRID.size, dtype=int)
    periodic_states = np.zeros((EXPONENT_GRID.size, 4))
    scan_fallback_count = 0

    scan_start = perf_counter()
    previous_state = None
    for index, exponent in enumerate(EXPONENT_GRID):
        try:
            result = shooting_mean_power(
                COEFFICIENT,
                exponent,
                params,
                initial_state=previous_state,
                **SCREENING_SETTINGS,
            )
        except RuntimeError:
            result = shooting_mean_power(
                COEFFICIENT,
                exponent,
                params,
                initial_state=previous_state,
                **REFINEMENT_SETTINGS,
            )
            scan_fallback_count += 1
        power_grid[index] = result.mean_power
        periodicity_error[index] = result.periodicity_error
        root_success[index] = result.root_success
        ode_function_evaluations[index] = result.ode_function_evaluations
        periodic_states[index] = result.periodic_state
        previous_state = result.periodic_state
    scan_seconds = perf_counter() - scan_start

    grid_best_index = int(np.argmax(power_grid))
    peak_indices = count_strict_peaks(power_grid)

    refined_cache: dict[float, object] = {}

    def refined_result(exponent: float):
        exponent = float(np.clip(exponent, 0.0, 1.0))
        key = round(exponent, 12)
        if key not in refined_cache:
            nearest_index = int(np.argmin(np.abs(EXPONENT_GRID - exponent)))
            refined_cache[key] = shooting_mean_power(
                COEFFICIENT,
                exponent,
                params,
                initial_state=periodic_states[nearest_index],
                **REFINEMENT_SETTINGS,
            )
        return refined_cache[key]

    refine_start = perf_counter()
    optimized = minimize_scalar(
        lambda exponent: -refined_result(exponent).mean_power,
        bounds=(0.0, 1.0),
        method="bounded",
        options={"xatol": 1e-9, "maxiter": 100},
    )
    if not optimized.success:
        raise RuntimeError(f"上边界指数优化失败：{optimized.message}")
    optimum_exponent = float(optimized.x)
    optimum_result = refined_result(optimum_exponent)

    perturbations = np.array([-0.01, -0.005, -0.001, -0.0001, 0.0001, 0.001, 0.005, 0.01])
    perturbation_exponents = optimum_exponent + perturbations
    perturbation_results = [
        refined_result(exponent) for exponent in perturbation_exponents
    ]
    perturbation_power = np.array(
        [result.mean_power for result in perturbation_results]
    )
    refine_seconds = perf_counter() - refine_start

    curvature_step = 1e-4
    curvature = (
        refined_result(optimum_exponent + curvature_step).mean_power
        - 2.0 * optimum_result.mean_power
        + refined_result(optimum_exponent - curvature_step).mean_power
    ) / curvature_step**2

    ridge_report_path = (
        CONTEST_DIR / "results" / "models" / "q2_nonlinear_ridge_refinement.json"
    )
    with ridge_report_path.open("r", encoding="utf-8") as stream:
        ridge_report = json.load(stream)
    internal_audit_best = max(
        run["candidate"]["mean_power_W"]
        for run in ridge_report["interior_multistart_audit"]["runs"]
    )

    report: dict[str, object] = {
        "status": "pending_acceptance",
        "model": "CUMCM 2022 A, question 2, nonlinear coefficient upper boundary",
        "scope": "candidate optimization only; final cold-start verification not executed",
        "fixed_coefficient": COEFFICIENT,
        "full_boundary_scan": {
            "points": int(EXPONENT_GRID.size),
            "step": float(EXPONENT_GRID[1] - EXPONENT_GRID[0]),
            "wall_time_s": scan_seconds,
            "strict_fallback_points": scan_fallback_count,
            "total_ode_function_evaluations": int(
                np.sum(ode_function_evaluations)
            ),
            "maximum_periodicity_error": float(np.max(periodicity_error)),
            "root_non_success_flag_count": int(np.count_nonzero(~root_success)),
            "strict_interior_peak_count": int(peak_indices.size),
            "strict_peak_exponents": EXPONENT_GRID[peak_indices].tolist(),
            "grid_best": {
                "exponent": float(EXPONENT_GRID[grid_best_index]),
                "mean_power_W": float(power_grid[grid_best_index]),
            },
            "endpoint_power_W": {
                "exponent_zero": float(power_grid[0]),
                "exponent_one": float(power_grid[-1]),
            },
        },
        "bounded_refinement": {
            "success": bool(optimized.success),
            "iterations": int(optimized.nit),
            "function_evaluations": int(optimized.nfev),
            "unique_strict_power_evaluations_including_checks": len(refined_cache),
            "wall_time_s": refine_seconds,
            "candidate": {
                "coefficient": COEFFICIENT,
                "exponent": optimum_exponent,
                "mean_power_W": optimum_result.mean_power,
                "periodicity_error": optimum_result.periodicity_error,
                "root_success": optimum_result.root_success,
                "periodic_state": optimum_result.periodic_state.tolist(),
                "pto_energy_one_cycle_J": optimum_result.pto_energy_one_cycle,
            },
            "local_curvature_W_per_exponent_squared": float(curvature),
        },
        "local_perturbations": [
            {
                "exponent_change": float(change),
                "exponent": float(exponent),
                "mean_power_W": float(result.mean_power),
                "power_loss_from_candidate_W": float(
                    optimum_result.mean_power - result.mean_power
                ),
                "periodicity_error": float(result.periodicity_error),
            }
            for change, exponent, result in zip(
                perturbations, perturbation_exponents, perturbation_results
            )
        ],
        "comparison_with_interior_audit": {
            "best_internal_audit_power_W": float(internal_audit_best),
            "boundary_candidate_power_W": optimum_result.mean_power,
            "boundary_advantage_W": float(
                optimum_result.mean_power - internal_audit_best
            ),
        },
        "interpretation": {
            "candidate_lies_on_coefficient_upper_boundary": True,
            "candidate_exponent_is_interior": 0.0 < optimum_exponent < 1.0,
            "final_answer_ready": False,
            "remaining_requirement": "strict shooting and independent cold-start long-transient verification",
        },
        "acceptance": {
            "all_scan_values_are_finite": bool(np.all(np.isfinite(power_grid))),
            "all_scan_power_is_nonnegative": bool(np.min(power_grid) >= -1e-10),
            "all_scan_roots_succeeded_or_closed": bool(
                np.all(
                    root_success
                    | (
                        periodicity_error
                        <= SCREENING_SETTINGS["periodicity_tolerance"]
                    )
                )
            ),
            "all_scan_periodicity_errors_pass": bool(
                np.max(periodicity_error) <= SCREENING_SETTINGS["periodicity_tolerance"]
            ),
            "boundary_scan_has_one_strict_peak": peak_indices.size == 1,
            "scan_peak_is_not_exponent_endpoint": 0 < grid_best_index < EXPONENT_GRID.size - 1,
            "refined_candidate_is_interior_in_exponent": 0.0 < optimum_exponent < 1.0,
            "all_local_perturbations_are_lower": bool(
                np.all(perturbation_power < optimum_result.mean_power)
            ),
            "local_curvature_is_negative": bool(curvature < 0.0),
            "refined_candidate_improves_grid_best": bool(
                optimum_result.mean_power >= power_grid[grid_best_index]
            ),
            "boundary_candidate_exceeds_internal_audit": bool(
                optimum_result.mean_power > internal_audit_best
            ),
            "strict_candidate_periodicity_passes": bool(
                optimum_result.periodicity_error
                <= REFINEMENT_SETTINGS["periodicity_tolerance"]
            ),
        },
    }
    enforce_acceptance(report)
    report["status"] = "passed"

    models_dir = CONTEST_DIR / "results" / "models"
    np.savez_compressed(
        models_dir / "q2_nonlinear_boundary_scan.npz",
        exponent=EXPONENT_GRID,
        mean_power=power_grid,
        periodicity_error=periodicity_error,
        root_success=root_success,
        ode_function_evaluations=ode_function_evaluations,
        periodic_state=periodic_states,
    )
    with (models_dir / "q2_nonlinear_boundary_optimization.json").open(
        "w", encoding="utf-8"
    ) as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
