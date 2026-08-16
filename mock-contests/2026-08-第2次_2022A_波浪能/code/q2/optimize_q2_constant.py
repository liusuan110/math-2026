"""问题二第一部分：常量 PTO 阻尼的一维稳态平均功率优化。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar


CODE_DIR = Path(__file__).resolve().parents[1]
CONTEST_DIR = CODE_DIR.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q2_power import (  # noqa: E402
    constant_mean_power,
    constant_system_matrices,
    periodic_mean_power,
    q2_parameters,
)


LOWER_BOUND = 0.0
UPPER_BOUND = 100000.0
GRID_POINTS = 10001


def analytic_optimum() -> tuple[float, complex]:
    """由秩一阻尼更新推导常量阻尼的无约束解析最优值。

    令 Z(c)=Z0+i*omega*c*q*q^T，其中 q=[1,-1]^T。相对位移
    复幅值的分母为 1+i*omega*c*s，s=q^T*Z0^(-1)*q，故平均
    功率正比于 c/|1+i*omega*c*s|^2，其内部唯一驻点为
    c=1/(omega*|s|)。
    """

    params = q2_parameters()
    mass, damping_zero, stiffness = constant_system_matrices(0.0, params)
    impedance_zero = (
        stiffness
        - params.wave_omega**2 * mass
        + 1j * params.wave_omega * damping_zero
    )
    relative_vector = np.array([1.0, -1.0])
    receptance = relative_vector @ np.linalg.solve(
        impedance_zero, relative_vector
    )
    optimum = 1.0 / (params.wave_omega * abs(receptance))
    return float(optimum), complex(receptance)


def count_strict_grid_peaks(power: np.ndarray) -> tuple[int, np.ndarray]:
    """统计不含边界的严格网格局部极大值。"""

    peak_indices = np.flatnonzero(
        (power[1:-1] > power[:-2]) & (power[1:-1] > power[2:])
    ) + 1
    return int(peak_indices.size), peak_indices


def enforce_acceptance(report: dict[str, object]) -> None:
    """对最优位置、单峰性、解析一致性与时域复核执行硬验收。"""

    checks = report["acceptance"]
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise AssertionError("常量阻尼优化验收失败：" + "、".join(failed))


def main() -> None:
    params = q2_parameters()

    damping_grid = np.linspace(LOWER_BOUND, UPPER_BOUND, GRID_POINTS)
    power_grid = np.array(
        [constant_mean_power(value, params).mean_power for value in damping_grid]
    )
    grid_best_index = int(np.argmax(power_grid))
    peak_count, peak_indices = count_strict_grid_peaks(power_grid)

    optimized = minimize_scalar(
        lambda value: -constant_mean_power(value, params).mean_power,
        bounds=(LOWER_BOUND, UPPER_BOUND),
        method="bounded",
        options={"xatol": 1e-10, "maxiter": 500},
    )
    if not optimized.success:
        raise RuntimeError(f"一维有界优化失败：{optimized.message}")

    optimum_damping = float(optimized.x)
    frequency_result = constant_mean_power(optimum_damping, params)
    analytic_damping, receptance = analytic_optimum()
    analytic_result = constant_mean_power(analytic_damping, params)

    # p=0 时，幂律时域模型严格退化为同一常量阻尼模型。
    time_result = periodic_mean_power(
        optimum_damping,
        0.0,
        params,
        convergence_tolerance=1e-10,
        required_consecutive_cycles=4,
        rtol=1e-10,
        atol=1e-12,
    )

    perturbation_ratios = np.array([-0.05, -0.01, -0.001, 0.001, 0.01, 0.05])
    perturbation_damping = optimum_damping * (1.0 + perturbation_ratios)
    perturbation_power = np.array(
        [constant_mean_power(value, params).mean_power for value in perturbation_damping]
    )
    finite_difference_step = 1.0
    curvature = (
        constant_mean_power(optimum_damping + finite_difference_step, params).mean_power
        - 2.0 * frequency_result.mean_power
        + constant_mean_power(optimum_damping - finite_difference_step, params).mean_power
    ) / finite_difference_step**2

    optimizer_analytic_relative_error = abs(
        optimum_damping - analytic_damping
    ) / analytic_damping
    time_frequency_relative_error = abs(
        time_result.mean_power - frequency_result.mean_power
    ) / frequency_result.mean_power

    report: dict[str, object] = {
        "status": "pending_acceptance",
        "model": "CUMCM 2022 A, question 2, constant PTO damping",
        "bounds_N_s_per_m": [LOWER_BOUND, UPPER_BOUND],
        "dense_grid": {
            "points": GRID_POINTS,
            "step_N_s_per_m": float(damping_grid[1] - damping_grid[0]),
            "best_damping_N_s_per_m": float(damping_grid[grid_best_index]),
            "best_mean_power_W": float(power_grid[grid_best_index]),
            "strict_interior_peak_count": peak_count,
            "strict_peak_damping_N_s_per_m": damping_grid[peak_indices].tolist(),
        },
        "bounded_optimizer": {
            "success": bool(optimized.success),
            "iterations": int(optimized.nit),
            "function_evaluations": int(optimized.nfev),
            "damping_N_s_per_m": optimum_damping,
            "mean_power_W": frequency_result.mean_power,
            "relative_displacement_amplitude_m": (
                frequency_result.relative_displacement_amplitude
            ),
            "relative_velocity_amplitude_m_per_s": (
                frequency_result.relative_velocity_amplitude
            ),
            "float_displacement_phasor_m": {
                "real": float(frequency_result.displacement_phasor[0].real),
                "imag": float(frequency_result.displacement_phasor[0].imag),
            },
            "oscillator_displacement_phasor_m": {
                "real": float(frequency_result.displacement_phasor[1].real),
                "imag": float(frequency_result.displacement_phasor[1].imag),
            },
            "dynamic_residual_norm_N": frequency_result.dynamic_residual_norm,
            "local_curvature_W_per_damping_squared": float(curvature),
        },
        "analytic_check": {
            "receptance_real": float(receptance.real),
            "receptance_imag": float(receptance.imag),
            "damping_N_s_per_m": analytic_damping,
            "mean_power_W": analytic_result.mean_power,
            "optimizer_damping_relative_error": optimizer_analytic_relative_error,
        },
        "time_domain_check": {
            "mean_power_W": time_result.mean_power,
            "frequency_time_relative_error": time_frequency_relative_error,
            "cycles_to_convergence": time_result.cycles,
            "cycle_state_error": time_result.convergence_error,
            "function_evaluations": time_result.function_evaluations,
        },
        "boundary_power_W": {
            "lower": float(power_grid[0]),
            "upper": float(power_grid[-1]),
        },
        "local_perturbations": [
            {
                "relative_damping_change": float(ratio),
                "damping_N_s_per_m": float(damping),
                "mean_power_W": float(power),
                "power_loss_from_optimum_W": float(
                    frequency_result.mean_power - power
                ),
            }
            for ratio, damping, power in zip(
                perturbation_ratios, perturbation_damping, perturbation_power
            )
        ],
        "acceptance": {
            "grid_peak_is_interior": 0 < grid_best_index < GRID_POINTS - 1,
            "grid_has_one_strict_peak": peak_count == 1,
            "optimizer_is_interior": LOWER_BOUND < optimum_damping < UPPER_BOUND,
            "all_local_perturbations_are_lower": bool(
                np.all(perturbation_power < frequency_result.mean_power)
            ),
            "curvature_is_negative": bool(curvature < 0.0),
            "optimizer_matches_analytic_condition": bool(
                optimizer_analytic_relative_error < 1e-6
            ),
            "frequency_dynamic_residual_passes": bool(
                frequency_result.dynamic_residual_norm < 1e-8
            ),
            "time_domain_matches_frequency_domain": bool(
                time_frequency_relative_error < 1e-8
            ),
        },
    }
    enforce_acceptance(report)
    report["status"] = "passed"

    models_dir = CONTEST_DIR / "results" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        models_dir / "q2_constant_power_scan.npz",
        damping=damping_grid,
        mean_power=power_grid,
    )
    with (models_dir / "q2_constant_optimization.json").open(
        "w", encoding="utf-8"
    ) as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
