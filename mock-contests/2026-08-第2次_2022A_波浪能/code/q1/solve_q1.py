"""运行问题一完整 40 周期计算并执行全时域数值验证。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1]
CONTEST_DIR = CODE_DIR.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q1_dynamics import (  # noqa: E402
    DampingLaw,
    Q1Parameters,
    constant_system_matrices,
    damping_force,
    mechanical_energy,
    output_time_grid,
    solve_response,
)


KEY_TIMES = (10.0, 20.0, 40.0, 60.0, 100.0)
STATE_NAMES = ("float_displacement", "float_velocity", "oscillator_displacement", "oscillator_velocity")


def energy_balance_metrics(solution, params: Q1Parameters) -> dict[str, float]:
    """计算全时域能量闭合误差和耗散量。"""

    energies = np.array(
        [mechanical_energy(solution.y[:4, i], params) for i in range(solution.t.size)]
    )
    wave_work, radiation_loss, pto_loss = solution.y[4:7]
    residual = energies - energies[0] - wave_work + radiation_loss + pto_loss
    scale = np.maximum(
        1.0,
        np.abs(energies - energies[0])
        + np.abs(wave_work)
        + np.abs(radiation_loss)
        + np.abs(pto_loss),
    )
    return {
        "max_absolute_residual_J": float(np.max(np.abs(residual))),
        "max_relative_residual": float(np.max(np.abs(residual) / scale)),
        "final_mechanical_energy_J": float(energies[-1]),
        "wave_input_work_J": float(wave_work[-1]),
        "radiation_loss_J": float(radiation_loss[-1]),
        "pto_loss_J": float(pto_loss[-1]),
        "minimum_radiation_loss_J": float(np.min(radiation_loss)),
        "minimum_pto_loss_J": float(np.min(pto_loss)),
    }


def convergence_metrics(standard, reference) -> dict[str, object]:
    """比较正式积分与高精度参考积分的全部输出点。"""

    difference = standard.y[:4] - reference.y[:4]
    per_state = np.max(np.abs(difference), axis=1)
    return {
        "per_state_max_absolute_difference": {
            name: float(value) for name, value in zip(STATE_NAMES, per_state)
        },
        "overall_max_absolute_difference": float(np.max(per_state)),
    }


def frequency_domain_validation(params: Q1Parameters) -> dict[str, object]:
    """以解析稳态作为初值，验证常量阻尼时域方程。"""

    mass, damping, stiffness = constant_system_matrices(params)
    dynamic_stiffness = (
        stiffness
        - params.wave_omega**2 * mass
        + 1j * params.wave_omega * damping
    )
    force = np.array([params.excitation_amplitude, 0.0], dtype=complex)
    displacement_phasor = np.linalg.solve(dynamic_stiffness, force)
    initial_state = np.array(
        [
            displacement_phasor[0].real,
            -params.wave_omega * displacement_phasor[0].imag,
            displacement_phasor[1].real,
            -params.wave_omega * displacement_phasor[1].imag,
        ]
    )
    times = np.linspace(0.0, 5.0 * params.period, 2001)
    numerical = solve_response(
        params,
        DampingLaw.CONSTANT,
        (0.0, times[-1]),
        times,
        initial_state=initial_state,
        rtol=1e-11,
        atol=1e-13,
        max_step=0.01,
    )
    phase = np.exp(1j * params.wave_omega * times)
    exact = np.vstack(
        [
            np.real(displacement_phasor[0] * phase),
            np.real(1j * params.wave_omega * displacement_phasor[0] * phase),
            np.real(displacement_phasor[1] * phase),
            np.real(1j * params.wave_omega * displacement_phasor[1] * phase),
        ]
    )
    error = numerical.y - exact
    amplitude_scale = np.maximum(np.max(np.abs(exact), axis=1), 1e-15)
    relative_errors = np.max(np.abs(error), axis=1) / amplitude_scale
    return {
        "displacement_amplitude_m": {
            "float": float(abs(displacement_phasor[0])),
            "oscillator": float(abs(displacement_phasor[1])),
        },
        "velocity_amplitude_m_per_s": {
            "float": float(params.wave_omega * abs(displacement_phasor[0])),
            "oscillator": float(params.wave_omega * abs(displacement_phasor[1])),
        },
        "per_state_max_relative_error": {
            name: float(value) for name, value in zip(STATE_NAMES, relative_errors)
        },
        "overall_max_absolute_error": float(np.max(np.abs(error))),
        "overall_max_relative_error": float(np.max(relative_errors)),
    }


def response_metrics(solution, params: Q1Parameters, law: DampingLaw) -> dict[str, object]:
    """汇总响应幅值、相对运动、PTO 功率和关键时刻数值。"""

    states = solution.y[:4]
    relative_displacement = states[2] - states[0]
    relative_velocity = states[3] - states[1]
    cylinder_draft = params.static_cylinder_draft - states[0]
    spring_length = params.spring_equilibrium_length + relative_displacement
    pto_power = damping_force(relative_velocity, law, params) * relative_velocity
    key_values: dict[str, dict[str, float]] = {}
    for key_time in KEY_TIMES:
        index = int(round(key_time / 0.2))
        if not np.isclose(solution.t[index], key_time, atol=1e-12):
            raise RuntimeError(f"关键时刻 {key_time} s 未正确落在输出网格上")
        key_values[f"{key_time:.1f}"] = {
            name: float(states[row, index]) for row, name in enumerate(STATE_NAMES)
        }

    return {
        "state_max_absolute": {
            name: float(value)
            for name, value in zip(STATE_NAMES, np.max(np.abs(states), axis=1))
        },
        "relative_displacement_max_absolute_m": float(
            np.max(np.abs(relative_displacement))
        ),
        "relative_velocity_max_absolute_m_per_s": float(
            np.max(np.abs(relative_velocity))
        ),
        "physical_regime": {
            "cylinder_draft_min_m": float(np.min(cylinder_draft)),
            "cylinder_draft_max_m": float(np.max(cylinder_draft)),
            "cylinder_height_m": params.float_cylinder_height,
            "spring_length_min_m": float(np.min(spring_length)),
            "spring_length_max_m": float(np.max(spring_length)),
        },
        "pto_power_min_W": float(np.min(pto_power)),
        "pto_power_max_W": float(np.max(pto_power)),
        "pto_power_mean_over_full_interval_W": float(np.trapezoid(pto_power, solution.t) / (solution.t[-1] - solution.t[0])),
        "key_times": key_values,
    }


def cycle_to_cycle_metrics(params: Q1Parameters, law: DampingLaw) -> dict[str, object]:
    """比较第 39、40 个周期的同相位状态，量化瞬态残留。"""

    phase_points = 201
    times = np.linspace(38.0 * params.period, 40.0 * params.period, 2 * phase_points - 1)
    solution = solve_response(
        params,
        law,
        (0.0, 40.0 * params.period),
        times,
        rtol=1e-10,
        atol=1e-12,
        max_step=0.02,
    )
    cycle_39 = solution.y[:, :phase_points]
    cycle_40 = solution.y[:, phase_points - 1 :]
    absolute_difference = np.max(np.abs(cycle_40 - cycle_39), axis=1)
    later_cycle_amplitude = np.maximum(np.max(np.abs(cycle_40), axis=1), 1e-15)
    later_cycle_half_range = 0.5 * (np.max(cycle_40, axis=1) - np.min(cycle_40, axis=1))
    relative_difference = absolute_difference / later_cycle_amplitude
    return {
        "per_state_max_absolute_difference": {
            name: float(value) for name, value in zip(STATE_NAMES, absolute_difference)
        },
        "per_state_relative_to_cycle_40_amplitude": {
            name: float(value) for name, value in zip(STATE_NAMES, relative_difference)
        },
        "cycle_40_max_absolute": {
            name: float(value) for name, value in zip(STATE_NAMES, later_cycle_amplitude)
        },
        "cycle_40_half_peak_to_peak": {
            name: float(value) for name, value in zip(STATE_NAMES, later_cycle_half_range)
        },
        "overall_max_relative_difference": float(np.max(relative_difference)),
    }


def run_case(params: Q1Parameters, law: DampingLaw, times: np.ndarray) -> tuple[object, dict[str, object]]:
    """运行单个阻尼工况并完成能量、收敛和响应检查。"""

    standard = solve_response(
        params,
        law,
        (0.0, 40.0 * params.period),
        times,
        track_energy=True,
        rtol=1e-10,
        atol=1e-12,
        max_step=0.02,
    )
    reference = solve_response(
        params,
        law,
        (0.0, 40.0 * params.period),
        times,
        rtol=1e-12,
        atol=1e-14,
        max_step=0.01,
    )
    metrics = {
        "solver": {
            "standard_nfev": int(standard.nfev),
            "reference_nfev": int(reference.nfev),
            "output_points": int(times.size),
        },
        "convergence": convergence_metrics(standard, reference),
        "energy_balance": energy_balance_metrics(standard, params),
        "response": response_metrics(standard, params, law),
        "cycle_39_to_40": cycle_to_cycle_metrics(params, law),
    }
    return standard, metrics


def enforce_acceptance(report: dict[str, object]) -> None:
    """任何验收指标不合格时阻止结果落盘。"""

    for law_name in (DampingLaw.CONSTANT.value, DampingLaw.POWER.value):
        case = report["cases"][law_name]
        convergence = case["convergence"]
        energy = case["energy_balance"]
        response = case["response"]
        physical = response["physical_regime"]
        if convergence["overall_max_absolute_difference"] >= 1e-7:
            raise AssertionError(f"{law_name} 全时域收敛未通过")
        if energy["max_relative_residual"] >= 1e-8:
            raise AssertionError(f"{law_name} 能量闭合未通过")
        if energy["minimum_radiation_loss_J"] < -1e-9:
            raise AssertionError(f"{law_name} 兴波累计耗散出现负值")
        if energy["minimum_pto_loss_J"] < -1e-9:
            raise AssertionError(f"{law_name} PTO 累计耗散出现负值")
        if response["pto_power_min_W"] < -1e-9:
            raise AssertionError(f"{law_name} PTO 瞬时功率出现负值")
        if not 0.0 < physical["cylinder_draft_min_m"]:
            raise AssertionError(f"{law_name} 水线越过圆锥顶端")
        if not physical["cylinder_draft_max_m"] < physical["cylinder_height_m"]:
            raise AssertionError(f"{law_name} 水线越过圆柱顶端")
        if physical["spring_length_min_m"] <= 0.0:
            raise AssertionError(f"{law_name} 弹簧计算长度出现非正值")

    frequency = report["constant_frequency_domain_validation"]
    if frequency["overall_max_relative_error"] >= 1e-8:
        raise AssertionError("常量阻尼频域独立校验未通过")


def main() -> None:
    params = Q1Parameters()
    times = output_time_grid(params)
    case_solutions: dict[str, object] = {}
    case_reports: dict[str, object] = {}

    for law in DampingLaw:
        solution, metrics = run_case(params, law, times)
        case_solutions[law.value] = solution
        case_reports[law.value] = metrics

    report: dict[str, object] = {
        "status": "pending_acceptance",
        "model": "CUMCM 2022 A, question 1",
        "time_grid": {
            "start_s": float(times[0]),
            "end_s": float(times[-1]),
            "step_s": 0.2,
            "points": int(times.size),
            "forty_period_endpoint_s": float(40.0 * params.period),
        },
        "cases": case_reports,
        "constant_frequency_domain_validation": frequency_domain_validation(params),
    }
    enforce_acceptance(report)
    report["status"] = "passed"

    models_dir = CONTEST_DIR / "results" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        models_dir / "q1_full_response.npz",
        time=times,
        constant=case_solutions[DampingLaw.CONSTANT.value].y[:4],
        power=case_solutions[DampingLaw.POWER.value].y[:4],
    )
    response_payload = {
        "time": times.tolist(),
        "constant": case_solutions[DampingLaw.CONSTANT.value].y[:4].tolist(),
        "power": case_solutions[DampingLaw.POWER.value].y[:4].tolist(),
    }
    with (models_dir / "q1_full_response.json").open("w", encoding="utf-8") as stream:
        json.dump(response_payload, stream, ensure_ascii=False)
    with (models_dir / "q1_validation.json").open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
