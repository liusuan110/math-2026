"""问题四：直线与旋转常量阻尼的全域优化和最终时域复核。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import simpson
from scipy.optimize import differential_evolution, minimize_scalar


CODE_DIR = Path(__file__).resolve().parents[1]
CONTEST_DIR = CODE_DIR.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q3_dynamics import instantaneous_powers, mechanical_energy, solve_response  # noqa: E402
from common.q4_power import (  # noqa: E402
    AxisPowerResult,
    axis_mean_power,
    constrained_analytic_optimum,
    q4_parameters,
    total_mean_power,
    unconstrained_optimal_damping,
)


def result_payload(result: AxisPowerResult) -> dict[str, object]:
    return {
        "damping": result.damping,
        "mean_power_W": result.mean_power,
        "relative_displacement_amplitude": result.relative_displacement_amplitude,
        "relative_velocity_amplitude": result.relative_velocity_amplitude,
        "dynamic_residual": result.dynamic_residual,
        "displacement_phasor_real": result.displacement_phasor.real.tolist(),
        "displacement_phasor_imag": result.displacement_phasor.imag.tolist(),
    }


def bounded_axis_optimum(axis: str, params) -> AxisPowerResult:
    optimized = minimize_scalar(
        lambda value: -axis_mean_power(axis, float(value), params).mean_power,
        bounds=(0.0, 100000.0),
        method="bounded",
        options={"xatol": 1e-9, "maxiter": 1000},
    )
    if not optimized.success:
        raise RuntimeError(f"{axis} 有界优化失败：{optimized.message}")
    candidates = [0.0, float(optimized.x), 100000.0]
    return max(
        (axis_mean_power(axis, value, params) for value in candidates),
        key=lambda result: result.mean_power,
    )


def periodic_initial_state(heave: AxisPowerResult, pitch: AxisPowerResult, omega: float) -> np.ndarray:
    initial = np.zeros(8)
    for offset, response in ((0, heave.displacement_phasor), (4, pitch.displacement_phasor)):
        initial[offset] = response[0].real
        initial[offset + 1] = (1j * omega * response[0]).real
        initial[offset + 2] = response[1].real
        initial[offset + 3] = (1j * omega * response[1]).real
    return initial


def main() -> None:
    models_dir = CONTEST_DIR / "results" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    params = q4_parameters()

    scan_damping = np.linspace(0.0, 100000.0, 10001)
    heave_scan = np.array(
        [axis_mean_power("heave", value, params).mean_power for value in scan_damping]
    )
    pitch_scan = np.array(
        [axis_mean_power("pitch", value, params).mean_power for value in scan_damping]
    )
    np.savez_compressed(
        models_dir / "q4_power_curves.npz",
        damping=scan_damping,
        heave_power=heave_scan,
        pitch_power=pitch_scan,
    )

    analytic_heave = constrained_analytic_optimum("heave", params)
    analytic_pitch = constrained_analytic_optimum("pitch", params)
    bounded_heave = bounded_axis_optimum("heave", params)
    bounded_pitch = bounded_axis_optimum("pitch", params)
    final_linear = analytic_heave.damping
    final_rotational = analytic_pitch.damping
    final_total = total_mean_power(final_linear, final_rotational, params)

    joint = differential_evolution(
        lambda values: -total_mean_power(float(values[0]), float(values[1]), params),
        bounds=((0.0, 100000.0), (0.0, 100000.0)),
        seed=202208,
        tol=1e-11,
        atol=1e-11,
        polish=True,
        workers=1,
        updating="immediate",
    )
    if not joint.success:
        raise RuntimeError(f"二维独立优化失败：{joint.message}")

    final_params = q4_parameters(
        linear_damping=final_linear,
        rotational_damping=final_rotational,
    )
    time = np.linspace(0.0, params.period, 8001)
    initial = periodic_initial_state(analytic_heave, analytic_pitch, params.wave_omega)
    solution = solve_response(
        final_params,
        (0.0, params.period),
        time,
        initial_state=initial,
        rtol=1e-11,
        max_step=params.period / 3000.0,
    )
    powers = np.column_stack(
        [instantaneous_powers(t, solution.y[:, i], final_params) for i, t in enumerate(time)]
    )
    mean_power_components = simpson(powers, x=time, axis=1) / params.period
    time_total_pto = float(mean_power_components[2] + mean_power_components[4])
    periodic_closure = float(np.max(np.abs(solution.y[:, -1] - solution.y[:, 0])))
    mechanical_change = mechanical_energy(solution.y[:, -1], final_params) - mechanical_energy(
        solution.y[:, 0], final_params
    )
    energy_average_residual = float(
        mean_power_components[0]
        - mean_power_components[1]
        - mean_power_components[2]
        - mean_power_components[3]
        - mean_power_components[4]
    )
    relative_heave = solution.y[2] - solution.y[0]
    spring_length = params.spring_equilibrium_length + relative_heave
    maximum_pitch = float(np.max(np.abs(solution.y[[4, 6]])))
    static_cylinder_draft = (
        (params.float_mass + params.oscillator_mass) / params.seawater_density
        - np.pi * params.float_radius**2 * params.float_cone_height / 3.0
    ) / (np.pi * params.float_radius**2)
    draft = static_cylinder_draft - solution.y[0]

    neighbor_checks: dict[str, float] = {}
    for delta in (1.0, 10.0, 100.0, 1000.0):
        neighbor_checks[f"linear_minus_{delta:g}"] = total_mean_power(
            final_linear - delta, final_rotational, params
        )
        if final_linear + delta <= 100000.0:
            neighbor_checks[f"linear_plus_{delta:g}"] = total_mean_power(
                final_linear + delta, final_rotational, params
            )
        neighbor_checks[f"rotational_minus_{delta:g}"] = total_mean_power(
            final_linear, final_rotational - delta, params
        )

    checks = {
        "scan_heave_peak_near_final": abs(scan_damping[np.argmax(heave_scan)] - final_linear) <= 10.0,
        "scan_pitch_peak_at_upper_boundary": scan_damping[np.argmax(pitch_scan)] == 100000.0,
        "bounded_heave_matches_analytic": abs(bounded_heave.damping - final_linear) < 1e-2,
        "bounded_pitch_at_upper_boundary": bounded_pitch.damping == 100000.0,
        "joint_power_matches_separable_global": abs(-joint.fun - final_total) / final_total < 1e-9,
        "joint_linear_near_final": abs(joint.x[0] - final_linear) < 0.1,
        "joint_rotational_at_boundary": abs(joint.x[1] - final_rotational) < 0.1,
        "all_neighbor_powers_lower": all(value < final_total for value in neighbor_checks.values()),
        "phasor_residuals_small": max(analytic_heave.dynamic_residual, analytic_pitch.dynamic_residual) < 1e-8,
        "periodic_state_closure": periodic_closure < 1e-9,
        "time_frequency_power_agreement": abs(time_total_pto - final_total) / final_total < 1e-9,
        "time_heave_power_agreement": abs(mean_power_components[2] - analytic_heave.mean_power) / analytic_heave.mean_power < 1e-9,
        "time_pitch_power_agreement": abs(mean_power_components[4] - analytic_pitch.mean_power) / analytic_pitch.mean_power < 1e-9,
        "periodic_mechanical_energy_closure": abs(mechanical_change) < 1e-7,
        "periodic_energy_balance": abs(energy_average_residual) < 1e-8,
        "instantaneous_pto_nonnegative": bool(np.min(powers[[2, 4]]) >= 0.0),
        "spring_length_positive": float(np.min(spring_length)) > 0.0,
        "waterline_in_cylinder": float(np.min(draft)) > 0.0 and float(np.max(draft)) < params.float_cylinder_height,
        "small_angle_range": maximum_pitch < 0.2,
    }
    checks = {name: bool(passed) for name, passed in checks.items()}
    failed = [name for name, passed in checks.items() if not passed]

    surface_damping = np.linspace(0.0, 100000.0, 201)
    surface_heave = np.array(
        [axis_mean_power("heave", value, params).mean_power for value in surface_damping]
    )
    surface_pitch = np.array(
        [axis_mean_power("pitch", value, params).mean_power for value in surface_damping]
    )
    np.savez_compressed(
        models_dir / "q4_power_surface.npz",
        linear_damping=surface_damping,
        rotational_damping=surface_damping,
        total_power=surface_pitch[:, None] + surface_heave[None, :],
    )
    np.savez_compressed(
        models_dir / "q4_optimal_period.npz",
        time=time,
        states=solution.y.T,
        powers=powers.T,
        state_order=np.array(
            [
                "float_heave_displacement",
                "float_heave_velocity",
                "oscillator_heave_displacement",
                "oscillator_heave_velocity",
                "float_pitch_displacement",
                "float_pitch_velocity",
                "oscillator_pitch_displacement",
                "oscillator_pitch_velocity",
            ]
        ),
        power_order=np.array(
            [
                "wave_input",
                "heave_radiation",
                "linear_pto",
                "pitch_radiation",
                "rotational_pto",
            ]
        ),
    )

    report: dict[str, object] = {
        "status": "passed" if not failed else "failed",
        "model": "CUMCM 2022 A, question 4",
        "parameter_case": 4,
        "shell_convention": params.shell_convention.value,
        "wave_period_s": params.period,
        "optimization_bounds": [0.0, 100000.0],
        "analytic_unconstrained_damping": {
            "linear_N_s_per_m": unconstrained_optimal_damping("heave", params),
            "rotational_N_m_s": unconstrained_optimal_damping("pitch", params),
        },
        "final_result": {
            "linear_damping_N_s_per_m": final_linear,
            "rotational_damping_N_m_s": final_rotational,
            "heave_mean_power_W": analytic_heave.mean_power,
            "pitch_mean_power_W": analytic_pitch.mean_power,
            "maximum_total_mean_power_W": final_total,
            "total_energy_per_period_J": final_total * params.period,
        },
        "heave": result_payload(analytic_heave),
        "pitch": result_payload(analytic_pitch),
        "bounded_optimizer": {
            "heave": result_payload(bounded_heave),
            "pitch": result_payload(bounded_pitch),
        },
        "joint_differential_evolution": {
            "linear_damping": float(joint.x[0]),
            "rotational_damping": float(joint.x[1]),
            "mean_power_W": float(-joint.fun),
            "evaluations": int(joint.nfev),
        },
        "periodic_time_domain_validation": {
            "sample_count": int(time.size),
            "state_closure_max_absolute": periodic_closure,
            "mean_power_components_W": mean_power_components.tolist(),
            "total_pto_mean_power_W": time_total_pto,
            "mechanical_energy_change_J": float(mechanical_change),
            "mean_energy_balance_residual_W": energy_average_residual,
            "minimum_spring_length_m": float(np.min(spring_length)),
            "maximum_spring_length_m": float(np.max(spring_length)),
            "minimum_cylinder_draft_m": float(np.min(draft)),
            "maximum_cylinder_draft_m": float(np.max(draft)),
            "maximum_absolute_pitch_rad": maximum_pitch,
            "maximum_instantaneous_linear_pto_power_W": float(np.max(powers[2])),
            "maximum_instantaneous_rotational_pto_power_W": float(np.max(powers[4])),
        },
        "neighbor_total_powers_W": neighbor_checks,
        "checks": checks,
        "passed_count": sum(checks.values()),
        "total_count": len(checks),
        "failed": failed,
    }
    with (models_dir / "q4_optimization.json").open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    if failed:
        raise AssertionError("问题四优化验收失败：" + "、".join(failed))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
