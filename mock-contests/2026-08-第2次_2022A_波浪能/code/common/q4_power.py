"""问题四常量直线/旋转 PTO 阻尼的频域功率计算器。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from common.q3_dynamics import Q3Parameters, heave_matrices, pitch_matrices


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]
AxisName = Literal["heave", "pitch"]
RELATIVE_VECTOR = np.array([1.0, -1.0])
LOWER_DAMPING = 0.0
UPPER_DAMPING = 100000.0


@dataclass(frozen=True)
class AxisPowerResult:
    axis: AxisName
    damping: float
    mean_power: float
    displacement_phasor: ComplexArray
    relative_displacement_amplitude: float
    relative_velocity_amplitude: float
    dynamic_residual: float


def q4_parameters(**overrides: float) -> Q3Parameters:
    """返回附件 3 情形 4 与附件 4 组合得到的参数。"""

    values: dict[str, float] = {
        "wave_omega": 1.9806,
        "added_mass": 1091.099,
        "added_rotational_inertia": 7142.493,
        "heave_radiation_damping": 528.5018,
        "pitch_radiation_damping": 1655.909,
        "excitation_force_amplitude": 1760.0,
        "excitation_moment_amplitude": 2140.0,
    }
    values.update(overrides)
    return Q3Parameters(**values)


def _validate_damping(damping: float) -> float:
    value = float(damping)
    if not np.isfinite(value):
        raise ValueError("阻尼系数必须为有限实数")
    if value < LOWER_DAMPING or value > UPPER_DAMPING:
        raise ValueError("阻尼系数必须位于 [0, 100000]")
    return value


def axis_data(
    axis: AxisName, params: Q3Parameters
) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    """返回单个运动方向的 M、无 PTO 的 C、K 和激励振幅向量。"""

    if axis == "heave":
        mass, _, stiffness = heave_matrices(params)
        baseline_damping = np.diag([params.heave_radiation_damping, 0.0])
        forcing = np.array([params.excitation_force_amplitude, 0.0])
    elif axis == "pitch":
        mass, _, stiffness = pitch_matrices(params)
        baseline_damping = np.diag([params.pitch_radiation_damping, 0.0])
        forcing = np.array([params.excitation_moment_amplitude, 0.0])
    else:
        raise ValueError("axis 必须为 'heave' 或 'pitch'")
    return mass, baseline_damping, stiffness, forcing


def axis_mean_power(
    axis: AxisName, damping: float, params: Q3Parameters | None = None
) -> AxisPowerResult:
    """返回指定常量阻尼下的周期稳态复响应与平均 PTO 功率。"""

    p = q4_parameters() if params is None else params
    coefficient = _validate_damping(damping)
    mass, baseline_damping, stiffness, forcing = axis_data(axis, p)
    pto_matrix = coefficient * np.outer(RELATIVE_VECTOR, RELATIVE_VECTOR)
    dynamic_matrix = (
        stiffness
        - p.wave_omega**2 * mass
        + 1j * p.wave_omega * (baseline_damping + pto_matrix)
    )
    response = np.linalg.solve(dynamic_matrix, forcing)
    relative = complex(RELATIVE_VECTOR @ response)
    relative_displacement_amplitude = abs(relative)
    relative_velocity_amplitude = p.wave_omega * relative_displacement_amplitude
    mean_power = 0.5 * coefficient * relative_velocity_amplitude**2
    residual = float(np.linalg.norm(dynamic_matrix @ response - forcing, ord=np.inf))
    return AxisPowerResult(
        axis=axis,
        damping=coefficient,
        mean_power=float(mean_power),
        displacement_phasor=np.asarray(response, dtype=complex),
        relative_displacement_amplitude=float(relative_displacement_amplitude),
        relative_velocity_amplitude=float(relative_velocity_amplitude),
        dynamic_residual=residual,
    )


def total_mean_power(
    linear_damping: float,
    rotational_damping: float,
    params: Q3Parameters | None = None,
) -> float:
    """返回两个 PTO 阻尼器的周期稳态平均功率之和。"""

    p = q4_parameters() if params is None else params
    return (
        axis_mean_power("heave", linear_damping, p).mean_power
        + axis_mean_power("pitch", rotational_damping, p).mean_power
    )


def unconstrained_optimal_damping(
    axis: AxisName, params: Q3Parameters | None = None
) -> float:
    """由秩一阻尼更新给出单个方向的无约束正最优阻尼。"""

    p = q4_parameters() if params is None else params
    mass, baseline_damping, stiffness, _ = axis_data(axis, p)
    baseline_dynamic = (
        stiffness - p.wave_omega**2 * mass + 1j * p.wave_omega * baseline_damping
    )
    compliance = complex(
        RELATIVE_VECTOR
        @ np.linalg.solve(baseline_dynamic, RELATIVE_VECTOR)
    )
    return float(1.0 / (p.wave_omega * abs(compliance)))


def constrained_analytic_optimum(
    axis: AxisName, params: Q3Parameters | None = None
) -> AxisPowerResult:
    """将解析无约束最优点投影到题设闭区间并返回结果。"""

    p = q4_parameters() if params is None else params
    optimum = np.clip(
        unconstrained_optimal_damping(axis, p),
        LOWER_DAMPING,
        UPPER_DAMPING,
    )
    return axis_mean_power(axis, float(optimum), p)
