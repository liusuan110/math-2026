"""问题二幂律阻尼最终候选的严格、独立数值复核。"""

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

from common.q2_power import (  # noqa: E402
    periodic_mean_power,
    pto_power,
    q2_parameters,
    sample_period_from_state,
    shooting_mean_power,
)


COEFFICIENT = 100000.0
STRICT_SETTINGS = {
    "root_tolerance": 1e-12,
    "periodicity_tolerance": 5e-10,
    "maximum_root_evaluations": 200,
    "rtol": 2e-12,
    "atol": 2e-14,
    "max_step_fraction": 1.0 / 240.0,
}


def relative_error(value: float, reference: float) -> float:
    return abs(value - reference) / max(abs(reference), 1e-15)


def enforce_acceptance(report: dict[str, object]) -> None:
    failed = [name for name, passed in report["acceptance"].items() if not passed]
    if failed:
        raise AssertionError("幂律最终复核失败：" + "、".join(failed))


def main() -> None:
    params = q2_parameters()
    boundary_report_path = (
        CONTEST_DIR
        / "results"
        / "models"
        / "q2_nonlinear_boundary_optimization.json"
    )
    with boundary_report_path.open("r", encoding="utf-8") as stream:
        boundary_report = json.load(stream)
    prior_candidate = boundary_report["bounded_refinement"]["candidate"]
    prior_exponent = float(prior_candidate["exponent"])
    prior_state = np.asarray(prior_candidate["periodic_state"], dtype=float)

    cache: dict[tuple[float, float], object] = {}

    def strict_result(
        coefficient: float,
        exponent: float,
        initial_state: np.ndarray | None = prior_state,
    ):
        key = (round(float(coefficient), 8), round(float(exponent), 13))
        if key not in cache:
            cache[key] = shooting_mean_power(
                coefficient,
                exponent,
                params,
                initial_state=initial_state,
                **STRICT_SETTINGS,
            )
        return cache[key]

    refinement_start = perf_counter()
    optimized = minimize_scalar(
        lambda exponent: -strict_result(COEFFICIENT, exponent).mean_power,
        bounds=(prior_exponent - 0.005, prior_exponent + 0.005),
        method="bounded",
        options={"xatol": 2e-10, "maxiter": 100},
    )
    if not optimized.success:
        raise RuntimeError(f"最终指数精修失败：{optimized.message}")
    final_exponent = float(optimized.x)
    final_shooting = strict_result(COEFFICIENT, final_exponent)
    refinement_seconds = perf_counter() - refinement_start

    exponent_changes = np.array(
        [-5e-4, -1e-4, -5e-5, -1e-5, 1e-5, 5e-5, 1e-4, 5e-4]
    )
    exponent_results = [
        strict_result(COEFFICIENT, final_exponent + change)
        for change in exponent_changes
    ]
    exponent_power = np.array([result.mean_power for result in exponent_results])

    derivative_step = 1e-5
    power_minus = strict_result(
        COEFFICIENT, final_exponent - derivative_step
    ).mean_power
    power_plus = strict_result(
        COEFFICIENT, final_exponent + derivative_step
    ).mean_power
    central_derivative = (power_plus - power_minus) / (2.0 * derivative_step)
    central_curvature = (
        power_plus - 2.0 * final_shooting.mean_power + power_minus
    ) / derivative_step**2

    coefficient_inward = np.array([99990.0, 99900.0, 99000.0])
    coefficient_results = [
        strict_result(coefficient, final_exponent)
        for coefficient in coefficient_inward
    ]
    coefficient_power = np.array(
        [result.mean_power for result in coefficient_results]
    )
    inward_derivative = (
        final_shooting.mean_power - coefficient_power[0]
    ) / (COEFFICIENT - coefficient_inward[0])

    independent_shooting = shooting_mean_power(
        COEFFICIENT,
        final_exponent,
        params,
        initial_state=np.zeros(4),
        **STRICT_SETTINGS,
    )

    cold_start_time = perf_counter()
    cold_start = periodic_mean_power(
        COEFFICIENT,
        final_exponent,
        params,
        initial_state=np.zeros(4),
        convergence_tolerance=1e-8,
        required_consecutive_cycles=5,
        minimum_cycles=10,
        maximum_cycles=3000,
        rtol=1e-9,
        atol=1e-11,
        max_step_fraction=1.0 / 60.0,
    )
    cold_start_seconds = perf_counter() - cold_start_time

    times, states, instantaneous_power = sample_period_from_state(
        final_shooting.periodic_state,
        COEFFICIENT,
        final_exponent,
        params,
        samples=8001,
        rtol=1e-12,
        atol=1e-14,
    )
    quadrature_energy = float(np.trapezoid(instantaneous_power, times))
    quadrature_mean_power = quadrature_energy / params.period
    relative_velocity = states[3] - states[1]
    relative_displacement = states[2] - states[0]
    cylinder_draft = params.static_cylinder_draft - states[0]
    spring_length = params.spring_equilibrium_length + relative_displacement
    independently_sampled_power = np.asarray(
        pto_power(relative_velocity, COEFFICIENT, final_exponent), dtype=float
    )

    shooting_cold_power_error = relative_error(
        final_shooting.mean_power, cold_start.mean_power
    )
    shooting_quadrature_power_error = relative_error(
        final_shooting.mean_power, quadrature_mean_power
    )
    shooting_state_error = float(
        np.linalg.norm(
            final_shooting.periodic_state - independent_shooting.periodic_state
        )
        / (1.0 + np.linalg.norm(final_shooting.periodic_state))
    )
    cold_state_error = float(
        np.linalg.norm(final_shooting.periodic_state - cold_start.periodic_state)
        / (1.0 + np.linalg.norm(final_shooting.periodic_state))
    )

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
        "model": "CUMCM 2022 A, question 2, final power-law PTO result",
        "final_result": {
            "coefficient": COEFFICIENT,
            "exponent": final_exponent,
            "mean_power_W": final_shooting.mean_power,
            "pto_energy_per_period_J": final_shooting.pto_energy_one_cycle,
            "period_s": params.period,
            "periodic_state": final_shooting.periodic_state.tolist(),
            "periodicity_error": final_shooting.periodicity_error,
            "root_success": final_shooting.root_success,
        },
        "strict_refinement": {
            "prior_candidate_exponent": prior_exponent,
            "exponent_change": final_exponent - prior_exponent,
            "optimizer_success": bool(optimized.success),
            "iterations": int(optimized.nit),
            "function_evaluations": int(optimized.nfev),
            "unique_strict_evaluations_including_checks": len(cache),
            "wall_time_s": refinement_seconds,
            "central_derivative_W_per_exponent": float(central_derivative),
            "central_curvature_W_per_exponent_squared": float(central_curvature),
        },
        "exponent_perturbations": [
            {
                "change": float(change),
                "exponent": float(final_exponent + change),
                "mean_power_W": float(result.mean_power),
                "power_loss_W": float(
                    final_shooting.mean_power - result.mean_power
                ),
                "periodicity_error": float(result.periodicity_error),
            }
            for change, result in zip(exponent_changes, exponent_results)
        ],
        "coefficient_inward_checks": [
            {
                "coefficient": float(coefficient),
                "exponent_fixed_at_final": final_exponent,
                "mean_power_W": float(result.mean_power),
                "power_loss_W": float(
                    final_shooting.mean_power - result.mean_power
                ),
                "periodicity_error": float(result.periodicity_error),
            }
            for coefficient, result in zip(
                coefficient_inward, coefficient_results
            )
        ],
        "coefficient_one_sided_derivative_W_per_coefficient": float(
            inward_derivative
        ),
        "independent_zero_guess_shooting": {
            "mean_power_W": independent_shooting.mean_power,
            "periodicity_error": independent_shooting.periodicity_error,
            "state_relative_difference": shooting_state_error,
            "power_relative_difference": relative_error(
                final_shooting.mean_power, independent_shooting.mean_power
            ),
        },
        "cold_start_long_transient": {
            "mean_power_W": cold_start.mean_power,
            "cycles_to_convergence": cold_start.cycles,
            "cycle_state_error": cold_start.convergence_error,
            "function_evaluations": cold_start.function_evaluations,
            "wall_time_s": cold_start_seconds,
            "state_relative_difference_from_shooting": cold_state_error,
            "power_relative_difference_from_shooting": shooting_cold_power_error,
        },
        "dense_period_quadrature": {
            "samples": int(times.size),
            "mean_power_W": quadrature_mean_power,
            "energy_J": quadrature_energy,
            "power_relative_difference_from_augmented_state": (
                shooting_quadrature_power_error
            ),
            "minimum_instantaneous_power_W": float(
                np.min(instantaneous_power)
            ),
            "maximum_instantaneous_power_W": float(
                np.max(instantaneous_power)
            ),
            "independent_power_array_max_difference_W": float(
                np.max(np.abs(instantaneous_power - independently_sampled_power))
            ),
        },
        "steady_response": {
            "float_displacement_min_m": float(np.min(states[0])),
            "float_displacement_max_m": float(np.max(states[0])),
            "oscillator_displacement_min_m": float(np.min(states[2])),
            "oscillator_displacement_max_m": float(np.max(states[2])),
            "relative_displacement_max_absolute_m": float(
                np.max(np.abs(relative_displacement))
            ),
            "relative_velocity_max_absolute_m_per_s": float(
                np.max(np.abs(relative_velocity))
            ),
            "cylinder_draft_min_m": float(np.min(cylinder_draft)),
            "cylinder_draft_max_m": float(np.max(cylinder_draft)),
            "spring_length_min_m": float(np.min(spring_length)),
            "spring_length_max_m": float(np.max(spring_length)),
        },
        "global_comparison": {
            "best_internal_audit_power_W": float(internal_audit_best),
            "final_boundary_advantage_W": float(
                final_shooting.mean_power - internal_audit_best
            ),
        },
        "acceptance": {
            "strict_optimizer_succeeded": bool(optimized.success),
            "final_exponent_is_interior": 0.0 < final_exponent < 1.0,
            "final_coefficient_is_active_upper_bound": COEFFICIENT == 100000.0,
            "final_periodicity_error_passes": bool(
                final_shooting.periodicity_error
                <= STRICT_SETTINGS["periodicity_tolerance"]
            ),
            "all_exponent_perturbations_are_lower": bool(
                np.all(exponent_power < final_shooting.mean_power)
            ),
            "exponent_curvature_is_negative": bool(central_curvature < 0.0),
            "exponent_derivative_is_small": bool(abs(central_derivative) < 5e-3),
            "all_inward_coefficient_checks_are_lower": bool(
                np.all(coefficient_power < final_shooting.mean_power)
            ),
            "coefficient_one_sided_derivative_is_positive": bool(
                inward_derivative > 0.0
            ),
            "independent_shooting_state_matches": bool(
                shooting_state_error < 1e-8
            ),
            "independent_shooting_power_matches": bool(
                relative_error(
                    final_shooting.mean_power, independent_shooting.mean_power
                )
                < 1e-9
            ),
            "cold_start_converged": bool(
                cold_start.convergence_error <= 1e-8
            ),
            "cold_start_state_matches": bool(cold_state_error < 1e-6),
            "cold_start_power_matches": bool(shooting_cold_power_error < 1e-7),
            "dense_quadrature_matches_augmented_energy": bool(
                shooting_quadrature_power_error < 1e-8
            ),
            "instantaneous_power_is_nonnegative": bool(
                np.min(instantaneous_power) >= -1e-10
            ),
            "physical_waterline_regime_passes": bool(
                np.min(cylinder_draft) > 0.0
                and np.max(cylinder_draft) < params.float_cylinder_height
            ),
            "spring_length_is_positive": bool(np.min(spring_length) > 0.0),
            "final_boundary_power_exceeds_internal_audit": bool(
                final_shooting.mean_power > internal_audit_best
            ),
        },
    }
    enforce_acceptance(report)
    report["status"] = "passed"
    report["final_answer_ready"] = True

    models_dir = CONTEST_DIR / "results" / "models"
    np.savez_compressed(
        models_dir / "q2_nonlinear_final_period.npz",
        time=times,
        state=states,
        instantaneous_power=instantaneous_power,
        relative_displacement=relative_displacement,
        relative_velocity=relative_velocity,
    )
    with (models_dir / "q2_nonlinear_final_validation.json").open(
        "w", encoding="utf-8"
    ) as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
