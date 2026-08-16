"""问题三完整 40 周期数值验证；不生成正式结果工作簿。"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path
from time import perf_counter

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q3_dynamics import (  # noqa: E402
    FloatShellConvention,
    Q3Parameters,
    diagnostic_time_grid,
    matrix_exponential_response,
    output_time_grid,
    solve_response,
    system_matrices,
)


STATE_NAMES = (
    "float_heave_displacement",
    "float_heave_velocity",
    "oscillator_heave_displacement",
    "oscillator_heave_velocity",
    "float_pitch_displacement",
    "float_pitch_velocity",
    "oscillator_pitch_displacement",
    "oscillator_pitch_velocity",
)
SAFE_SCALES = np.array([1e-3] * 4 + [1e-4] * 4, dtype=float)


def channel_error(candidate: np.ndarray, reference: np.ndarray) -> dict[str, object]:
    """返回逐状态最大误差及统一归一化误差。"""

    maximum = np.max(np.abs(candidate - reference), axis=1)
    rms = np.sqrt(np.mean((candidate - reference) ** 2, axis=1))
    scales = np.maximum(np.max(np.abs(reference), axis=1), SAFE_SCALES)
    normalized = maximum / scales
    return {
        "channel_max_absolute": dict(zip(STATE_NAMES, maximum.tolist(), strict=True)),
        "channel_rms": dict(zip(STATE_NAMES, rms.tolist(), strict=True)),
        "channel_max_normalized": dict(
            zip(STATE_NAMES, normalized.tolist(), strict=True)
        ),
        "global_max_absolute": float(np.max(maximum)),
        "global_max_normalized": float(np.max(normalized)),
    }


def state_energy(states: np.ndarray, params: Q3Parameters) -> np.ndarray:
    """向量化计算八状态序列的机械能。"""

    mass, _, stiffness = system_matrices(params)
    positions = states[[0, 2, 4, 6]]
    velocities = states[[1, 3, 5, 7]]
    kinetic = 0.5 * np.einsum("in,ij,jn->n", velocities, mass, velocities)
    potential = 0.5 * np.einsum("in,ij,jn->n", positions, stiffness, positions)
    return kinetic + potential


def peak_dictionary(states: np.ndarray) -> dict[str, float]:
    return dict(
        zip(STATE_NAMES, np.max(np.abs(states), axis=1).tolist(), strict=True)
    )


def main() -> None:
    params = Q3Parameters()
    output_times = output_time_grid(params)
    diagnostic_times = diagnostic_time_grid(params, step=0.01)
    strict_atol = np.array([2e-14] * 4 + [2e-15] * 4, dtype=float)
    timings: dict[str, float] = {}

    print("[1/6] main 40-period integration", flush=True)
    start = perf_counter()
    main_solution = solve_response(
        params,
        (0.0, params.forty_period_end),
        output_times,
        rtol=1e-10,
        max_step=0.01,
    )
    timings["main_integration_seconds"] = perf_counter() - start

    print("[2/6] strict reference integration", flush=True)
    start = perf_counter()
    reference_solution = solve_response(
        params,
        (0.0, params.forty_period_end),
        output_times,
        rtol=2e-12,
        atol=strict_atol,
        max_step=0.0025,
    )
    timings["reference_integration_seconds"] = perf_counter() - start

    print("[3/6] matrix-exponential reference on official grid", flush=True)
    start = perf_counter()
    exact_solution = matrix_exponential_response(output_times, params)
    exact_endpoint = matrix_exponential_response([params.forty_period_end], params)[:, 0]
    timings["matrix_exponential_seconds"] = perf_counter() - start

    print("[4/6] augmented-energy integration on dense grid", flush=True)
    start = perf_counter()
    energy_solution = solve_response(
        params,
        (0.0, params.forty_period_end),
        diagnostic_times,
        rtol=1e-10,
        max_step=0.01,
        track_energy=True,
    )
    timings["energy_dense_integration_seconds"] = perf_counter() - start

    print("[5/6] physical-range and energy checks", flush=True)
    dense_states = energy_solution.y[:8]
    energies = state_energy(dense_states, params)
    input_work = energy_solution.y[8]
    losses = energy_solution.y[9:13]
    energy_residual = energies - input_work + np.sum(losses, axis=0)
    energy_scale = max(
        1.0,
        float(np.max(np.abs(energies))),
        float(np.max(np.abs(input_work))),
        float(np.max(np.sum(losses, axis=0))),
    )
    energy_relative_residual = float(
        np.max(np.abs(energy_residual)) / energy_scale
    )
    spring_lengths = (
        params.spring_equilibrium_length + dense_states[2] - dense_states[0]
    )
    maximum_pitch = float(np.max(np.abs(dense_states[[4, 6]])))
    output_indices = np.rint(output_times / 0.01).astype(int)
    dense_on_output = dense_states[:, output_indices]

    print("[6/6] alternative-shell sensitivity", flush=True)
    alternative = replace(
        params, shell_convention=FloatShellConvention.LATERAL_ONLY
    )
    start = perf_counter()
    alternative_solution = solve_response(
        alternative,
        (0.0, alternative.forty_period_end),
        diagnostic_times,
        rtol=1e-10,
        max_step=0.01,
    )
    timings["alternative_dense_integration_seconds"] = perf_counter() - start
    alternative_states = alternative_solution.y

    main_reference_error = channel_error(main_solution.y, reference_solution.y)
    main_exact_error = channel_error(main_solution.y, exact_solution)
    reference_exact_error = channel_error(reference_solution.y, exact_solution)
    augmented_main_error = channel_error(dense_on_output, main_solution.y)

    sensitivity_maximum = np.max(
        np.abs(alternative_states - dense_states), axis=1
    )
    main_peaks = np.max(np.abs(dense_states), axis=1)
    alternative_peaks = np.max(np.abs(alternative_states), axis=1)
    peak_relative_change = np.divide(
        alternative_peaks - main_peaks,
        np.maximum(main_peaks, SAFE_SCALES),
    )

    key_indices = {
        str(time): int(np.flatnonzero(np.isclose(output_times, time))[0])
        for time in (10.0, 20.0, 40.0, 60.0, 100.0)
    }
    key_values = {
        time: dict(
            zip(
                STATE_NAMES,
                main_solution.y[:, index].tolist(),
                strict=True,
            )
        )
        for time, index in key_indices.items()
    }

    checks = {
        "official_grid": bool(
            output_times.size == 733
            and output_times[0] == 0.0
            and np.isclose(output_times[-1], 146.4)
        ),
        "all_main_values_finite": bool(np.all(np.isfinite(main_solution.y))),
        "all_dense_values_finite": bool(np.all(np.isfinite(dense_states))),
        "all_alternative_values_finite": bool(
            np.all(np.isfinite(alternative_states))
        ),
        "main_reference_convergence": bool(
            main_reference_error["global_max_normalized"] <= 5e-8
        ),
        "main_matrix_exponential": bool(
            main_exact_error["global_max_normalized"] <= 5e-8
        ),
        "reference_matrix_exponential": bool(
            reference_exact_error["global_max_normalized"] <= 5e-9
        ),
        "augmented_matches_main": bool(
            augmented_main_error["global_max_normalized"] <= 5e-8
        ),
        "energy_balance": bool(energy_relative_residual <= 1e-8),
        "losses_nonnegative": bool(float(np.min(losses)) >= -1e-10),
        "losses_monotone": bool(
            float(np.min(np.diff(losses, axis=1))) >= -1e-9
        ),
        "spring_length_positive": bool(float(np.min(spring_lengths)) > 0.0),
        "small_angle_warning_not_triggered": bool(maximum_pitch <= 0.2),
    }
    checks["all_passed"] = all(checks.values())

    result = {
        "status": "passed" if checks["all_passed"] else "failed",
        "shell_convention": params.shell_convention.value,
        "wave_period": params.period,
        "forty_period_end": params.forty_period_end,
        "official_grid": {
            "count": int(output_times.size),
            "first": float(output_times[0]),
            "last": float(output_times[-1]),
            "step": 0.2,
        },
        "diagnostic_grid": {
            "count": int(diagnostic_times.size),
            "first": float(diagnostic_times[0]),
            "last": float(diagnostic_times[-1]),
            "regular_step": 0.01,
        },
        "timings": timings,
        "errors": {
            "main_vs_reference": main_reference_error,
            "main_vs_matrix_exponential": main_exact_error,
            "reference_vs_matrix_exponential": reference_exact_error,
            "augmented_vs_main": augmented_main_error,
            "energy_relative_residual": energy_relative_residual,
            "energy_absolute_residual": float(np.max(np.abs(energy_residual))),
        },
        "physical_ranges": {
            "main_peak_absolute": peak_dictionary(dense_states),
            "minimum_spring_length": float(np.min(spring_lengths)),
            "maximum_spring_length": float(np.max(spring_lengths)),
            "maximum_absolute_pitch": maximum_pitch,
            "exact_state_at_40_period_end": dict(
                zip(STATE_NAMES, exact_endpoint.tolist(), strict=True)
            ),
        },
        "energy_at_40_period_end": {
            "mechanical": float(energies[-1]),
            "wave_input_work": float(input_work[-1]),
            "heave_radiation_loss": float(losses[0, -1]),
            "linear_pto_output": float(losses[1, -1]),
            "pitch_radiation_loss": float(losses[2, -1]),
            "rotational_pto_output": float(losses[3, -1]),
            "balance_residual": float(energy_residual[-1]),
        },
        "sensitivity": {
            "alternative_shell_convention": alternative.shell_convention.value,
            "channel_max_absolute_difference": dict(
                zip(STATE_NAMES, sensitivity_maximum.tolist(), strict=True)
            ),
            "main_peak_absolute": dict(
                zip(STATE_NAMES, main_peaks.tolist(), strict=True)
            ),
            "alternative_peak_absolute": dict(
                zip(STATE_NAMES, alternative_peaks.tolist(), strict=True)
            ),
            "peak_relative_change": dict(
                zip(STATE_NAMES, peak_relative_change.tolist(), strict=True)
            ),
        },
        "key_time_values": key_values,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2), flush=True)
    if not checks["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
