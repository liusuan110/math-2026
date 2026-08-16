"""问题三垂荡—纵摇线性动力学公共组件。

坐标均以静水平衡位置为零点。物理状态按
``[x_f, v_f, x_o, v_o, theta_f, omega_f, theta_o, omega_o]`` 排列。
该模块只负责参数、矩阵、积分与基础核验，不生成正式结果表或论文图片。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import pi, sqrt
from typing import Iterable

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.integrate import solve_ivp
from scipy.linalg import expm


FloatArray = NDArray[np.float64]


class FloatShellConvention(str, Enum):
    """浮子均匀薄壳的两种几何解释。"""

    SEALED_WITH_TOP = "sealed_with_top"
    LATERAL_ONLY = "lateral_only"


@dataclass(frozen=True)
class FloatGeometry:
    """浮子薄壳质量分配及绕横轴的几何量。"""

    side_mass: float
    top_mass: float
    cone_mass: float
    centroid_to_hinge: float
    inertia_about_hinge: float
    inertia_about_centroid: float


@dataclass(frozen=True)
class Q3Parameters:
    """问题三使用的官方参数与壳体解释口径。"""

    wave_omega: float = 1.7152
    added_mass: float = 1028.876
    added_rotational_inertia: float = 7001.914
    heave_radiation_damping: float = 683.4558
    pitch_radiation_damping: float = 654.3383
    excitation_force_amplitude: float = 3640.0
    excitation_moment_amplitude: float = 1690.0
    float_mass: float = 4866.0
    float_radius: float = 1.0
    float_cylinder_height: float = 3.0
    float_cone_height: float = 0.8
    oscillator_mass: float = 2433.0
    oscillator_radius: float = 0.5
    oscillator_height: float = 0.5
    seawater_density: float = 1025.0
    gravity: float = 9.8
    linear_spring_stiffness: float = 80000.0
    linear_spring_natural_length: float = 0.5
    linear_damping: float = 10000.0
    torsional_spring_stiffness: float = 250000.0
    rotational_damping: float = 1000.0
    hydrostatic_pitch_stiffness: float = 8890.7
    shell_convention: FloatShellConvention = FloatShellConvention.SEALED_WITH_TOP

    def __post_init__(self) -> None:
        positive = {
            name: value
            for name, value in self.__dict__.items()
            if name != "shell_convention"
        }
        invalid = [name for name, value in positive.items() if float(value) <= 0.0]
        if invalid:
            raise ValueError(f"参数必须为正数: {', '.join(invalid)}")
        if not isinstance(self.shell_convention, FloatShellConvention):
            raise TypeError("shell_convention 必须是 FloatShellConvention")
        if self.spring_equilibrium_length <= 0.0:
            raise ValueError("静平衡弹簧长度必须为正")

    @property
    def period(self) -> float:
        return 2.0 * pi / self.wave_omega

    @property
    def forty_period_end(self) -> float:
        return 40.0 * self.period

    @property
    def effective_float_mass(self) -> float:
        return self.float_mass + self.added_mass

    @property
    def hydrostatic_heave_stiffness(self) -> float:
        return self.seawater_density * self.gravity * pi * self.float_radius**2

    @property
    def spring_equilibrium_length(self) -> float:
        return (
            self.linear_spring_natural_length
            - self.oscillator_mass * self.gravity / self.linear_spring_stiffness
        )

    @property
    def oscillator_centroid_to_hinge(self) -> float:
        return self.spring_equilibrium_length + 0.5 * self.oscillator_height

    @property
    def oscillator_centroid_inertia(self) -> float:
        return (
            self.oscillator_mass
            * (3.0 * self.oscillator_radius**2 + self.oscillator_height**2)
            / 12.0
        )

    @property
    def oscillator_hinge_inertia(self) -> float:
        return (
            self.oscillator_centroid_inertia
            + self.oscillator_mass * self.oscillator_centroid_to_hinge**2
        )

    @property
    def float_geometry(self) -> FloatGeometry:
        radius = self.float_radius
        cylinder_height = self.float_cylinder_height
        cone_height = self.float_cone_height
        side_area = 2.0 * pi * radius * cylinder_height
        cone_area = pi * radius * sqrt(radius**2 + cone_height**2)
        top_area = (
            pi * radius**2
            if self.shell_convention is FloatShellConvention.SEALED_WITH_TOP
            else 0.0
        )
        total_area = side_area + cone_area + top_area

        side_mass = self.float_mass * side_area / total_area
        cone_mass = self.float_mass * cone_area / total_area
        top_mass = self.float_mass * top_area / total_area

        side_centroid = 0.5 * cylinder_height
        cone_centroid = -cone_height / 3.0
        top_centroid = cylinder_height
        centroid_to_hinge = (
            side_mass * side_centroid
            + cone_mass * cone_centroid
            + top_mass * top_centroid
        ) / self.float_mass

        side_inertia = side_mass * (
            0.5 * radius**2 + cylinder_height**2 / 3.0
        )
        cone_inertia = cone_mass * (
            0.25 * radius**2 + cone_height**2 / 6.0
        )
        top_inertia = top_mass * (
            0.25 * radius**2 + cylinder_height**2
        )
        inertia_about_hinge = side_inertia + cone_inertia + top_inertia
        inertia_about_centroid = (
            inertia_about_hinge - self.float_mass * centroid_to_hinge**2
        )
        return FloatGeometry(
            side_mass=side_mass,
            top_mass=top_mass,
            cone_mass=cone_mass,
            centroid_to_hinge=centroid_to_hinge,
            inertia_about_hinge=inertia_about_hinge,
            inertia_about_centroid=inertia_about_centroid,
        )


def heave_matrices(params: Q3Parameters) -> tuple[FloatArray, FloatArray, FloatArray]:
    """返回垂荡质量、阻尼和刚度矩阵。"""

    mass = np.diag([params.effective_float_mass, params.oscillator_mass])
    damping = np.array(
        [
            [params.heave_radiation_damping + params.linear_damping, -params.linear_damping],
            [-params.linear_damping, params.linear_damping],
        ],
        dtype=float,
    )
    stiffness = np.array(
        [
            [
                params.hydrostatic_heave_stiffness
                + params.linear_spring_stiffness,
                -params.linear_spring_stiffness,
            ],
            [-params.linear_spring_stiffness, params.linear_spring_stiffness],
        ],
        dtype=float,
    )
    return mass, damping, stiffness


def pitch_matrices(params: Q3Parameters) -> tuple[FloatArray, FloatArray, FloatArray]:
    """返回纵摇质量、阻尼和刚度矩阵。"""

    geometry = params.float_geometry
    a = geometry.centroid_to_hinge
    d = params.oscillator_centroid_to_hinge
    oscillator_mass = params.oscillator_mass

    mass = np.array(
        [
            [
                geometry.inertia_about_centroid
                + params.added_rotational_inertia
                + oscillator_mass * a**2,
                -oscillator_mass * a * d,
            ],
            [
                -oscillator_mass * a * d,
                params.oscillator_centroid_inertia + oscillator_mass * d**2,
            ],
        ],
        dtype=float,
    )
    damping = np.array(
        [
            [
                params.pitch_radiation_damping + params.rotational_damping,
                -params.rotational_damping,
            ],
            [-params.rotational_damping, params.rotational_damping],
        ],
        dtype=float,
    )
    gravity_float = oscillator_mass * params.gravity * a
    gravity_oscillator = oscillator_mass * params.gravity * d
    stiffness = np.array(
        [
            [
                params.hydrostatic_pitch_stiffness
                + params.torsional_spring_stiffness
                + gravity_float,
                -params.torsional_spring_stiffness,
            ],
            [
                -params.torsional_spring_stiffness,
                params.torsional_spring_stiffness - gravity_oscillator,
            ],
        ],
        dtype=float,
    )
    return mass, damping, stiffness


def system_matrices(params: Q3Parameters) -> tuple[FloatArray, FloatArray, FloatArray]:
    """按 ``[x_f, x_o, theta_f, theta_o]`` 返回四自由度矩阵。"""

    heave_mass, heave_damping, heave_stiffness = heave_matrices(params)
    pitch_mass, pitch_damping, pitch_stiffness = pitch_matrices(params)
    zeros = np.zeros((2, 2), dtype=float)
    mass = np.block([[heave_mass, zeros], [zeros, pitch_mass]])
    damping = np.block([[heave_damping, zeros], [zeros, pitch_damping]])
    stiffness = np.block([[heave_stiffness, zeros], [zeros, pitch_stiffness]])
    return mass, damping, stiffness


def forcing_amplitude(params: Q3Parameters) -> FloatArray:
    """按四自由度坐标顺序返回波浪激励振幅。"""

    return np.array(
        [
            params.excitation_force_amplitude,
            0.0,
            params.excitation_moment_amplitude,
            0.0,
        ],
        dtype=float,
    )


def _split_state(state: ArrayLike) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
    values = np.asarray(state, dtype=float)
    if values.shape != (8,):
        raise ValueError("物理状态必须恰好包含 8 项")
    heave_position = values[[0, 2]]
    heave_velocity = values[[1, 3]]
    pitch_position = values[[4, 6]]
    pitch_velocity = values[[5, 7]]
    return heave_position, heave_velocity, pitch_position, pitch_velocity


def state_rhs(
    t: float,
    state: ArrayLike,
    params: Q3Parameters,
    excitation_scale: float = 1.0,
) -> FloatArray:
    """返回八状态一阶方程右端。"""

    qz, vz, qt, vt = _split_state(state)
    mz, cz, kz = heave_matrices(params)
    mt, ct, kt = pitch_matrices(params)
    phase = np.cos(params.wave_omega * t)
    force_z = np.array(
        [excitation_scale * params.excitation_force_amplitude * phase, 0.0]
    )
    force_t = np.array(
        [excitation_scale * params.excitation_moment_amplitude * phase, 0.0]
    )
    az = np.linalg.solve(mz, force_z - cz @ vz - kz @ qz)
    at = np.linalg.solve(mt, force_t - ct @ vt - kt @ qt)
    return np.array(
        [vz[0], az[0], vz[1], az[1], vt[0], at[0], vt[1], at[1]],
        dtype=float,
    )


def mechanical_energy(state: ArrayLike, params: Q3Parameters) -> float:
    """返回平衡点附近的二次机械能，单位 J。"""

    qz, vz, qt, vt = _split_state(state)
    mass, _, stiffness = system_matrices(params)
    position = np.concatenate((qz, qt))
    velocity = np.concatenate((vz, vt))
    return float(
        0.5 * velocity @ mass @ velocity
        + 0.5 * position @ stiffness @ position
    )


def instantaneous_powers(
    t: float,
    state: ArrayLike,
    params: Q3Parameters,
    excitation_scale: float = 1.0,
) -> FloatArray:
    """返回输入、两类兴波耗散和两类 PTO 功率。"""

    _, vz, _, vt = _split_state(state)
    phase = np.cos(params.wave_omega * t)
    input_power = excitation_scale * phase * (
        params.excitation_force_amplitude * vz[0]
        + params.excitation_moment_amplitude * vt[0]
    )
    return np.array(
        [
            input_power,
            params.heave_radiation_damping * vz[0] ** 2,
            params.linear_damping * (vz[1] - vz[0]) ** 2,
            params.pitch_radiation_damping * vt[0] ** 2,
            params.rotational_damping * (vt[1] - vt[0]) ** 2,
        ],
        dtype=float,
    )


def state_rhs_with_energy(
    t: float,
    augmented_state: ArrayLike,
    params: Q3Parameters,
    excitation_scale: float = 1.0,
) -> FloatArray:
    """在八个物理状态后附加五个累计能量状态。"""

    values = np.asarray(augmented_state, dtype=float)
    if values.shape != (13,):
        raise ValueError("能量核验状态必须包含 8 个物理量和 5 个累计量")
    physical_rhs = state_rhs(t, values[:8], params, excitation_scale)
    powers = instantaneous_powers(t, values[:8], params, excitation_scale)
    return np.concatenate((physical_rhs, powers))


def output_time_grid(params: Q3Parameters) -> FloatArray:
    """返回前 40 周期内题目规定的 0.2 s 输出网格。"""

    last_index = int(np.floor(params.forty_period_end / 0.2 + 1e-12))
    return 0.2 * np.arange(last_index + 1, dtype=float)


def diagnostic_time_grid(params: Q3Parameters, step: float = 0.01) -> FloatArray:
    """返回包含精确 40 周期终点的稠密诊断网格。"""

    if step <= 0.0:
        raise ValueError("诊断网格步长必须为正")
    last_index = int(np.floor(params.forty_period_end / step + 1e-12))
    regular = step * np.arange(last_index + 1, dtype=float)
    if np.isclose(regular[-1], params.forty_period_end, rtol=0.0, atol=1e-14):
        regular[-1] = params.forty_period_end
        return regular
    return np.concatenate((regular, np.array([params.forty_period_end])))


def state_space_matrices(params: Q3Parameters) -> tuple[FloatArray, FloatArray]:
    """按 ``[q, qdot]`` 顺序返回状态矩阵和余弦激励向量。"""

    mass, damping, stiffness = system_matrices(params)
    zeros = np.zeros((4, 4), dtype=float)
    identity = np.eye(4, dtype=float)
    state_matrix = np.block(
        [
            [zeros, identity],
            [-np.linalg.solve(mass, stiffness), -np.linalg.solve(mass, damping)],
        ]
    )
    input_vector = np.concatenate(
        (np.zeros(4, dtype=float), np.linalg.solve(mass, forcing_amplitude(params)))
    )
    return state_matrix, input_vector


def matrix_exponential_response(
    times: Iterable[float],
    params: Q3Parameters,
    excitation_scale: float = 1.0,
) -> FloatArray:
    """返回零初值下的精确线性瞬态响应，输出为八状态交错顺序。"""

    evaluation_times = np.asarray(tuple(times), dtype=float)
    if evaluation_times.ndim != 1 or evaluation_times.size == 0:
        raise ValueError("times 必须是一维非空序列")
    if np.any(~np.isfinite(evaluation_times)) or np.any(evaluation_times < 0.0):
        raise ValueError("times 必须是有限的非负时刻")

    state_matrix, input_vector = state_space_matrices(params)
    scaled_input = excitation_scale * input_vector
    identity = np.eye(state_matrix.shape[0], dtype=complex)
    harmonic = np.linalg.solve(
        1j * params.wave_omega * identity - state_matrix,
        scaled_input.astype(complex),
    )
    qv_response = np.empty((8, evaluation_times.size), dtype=float)
    for index, time in enumerate(evaluation_times):
        complex_state = (
            harmonic * np.exp(1j * params.wave_omega * time)
            - expm(state_matrix * time) @ harmonic
        )
        qv_response[:, index] = np.real(complex_state)

    interleaved = np.empty_like(qv_response)
    interleaved[0] = qv_response[0]
    interleaved[1] = qv_response[4]
    interleaved[2] = qv_response[1]
    interleaved[3] = qv_response[5]
    interleaved[4] = qv_response[2]
    interleaved[5] = qv_response[6]
    interleaved[6] = qv_response[3]
    interleaved[7] = qv_response[7]
    return interleaved


def solve_response(
    params: Q3Parameters,
    t_span: tuple[float, float],
    t_eval: Iterable[float],
    *,
    excitation_scale: float = 1.0,
    rtol: float = 1e-10,
    atol: ArrayLike | float | None = None,
    max_step: float = 0.01,
    track_energy: bool = False,
    initial_state: ArrayLike | None = None,
):
    """按统一设置积分问题三模型，并在失败时立即报错。"""

    evaluation_times = np.asarray(tuple(t_eval), dtype=float)
    if evaluation_times.ndim != 1 or evaluation_times.size == 0:
        raise ValueError("t_eval 必须是一维非空时间序列")
    if np.any(np.diff(evaluation_times) <= 0.0):
        raise ValueError("t_eval 必须严格递增")
    if evaluation_times[0] < t_span[0] or evaluation_times[-1] > t_span[1]:
        raise ValueError("t_eval 必须位于 t_span 内")
    if rtol <= 0.0 or max_step <= 0.0:
        raise ValueError("积分容差和最大步长必须为正")

    if track_energy:
        rhs = state_rhs_with_energy
        expected_size = 13
        default_initial = np.zeros(13, dtype=float)
        default_atol = np.array(
            [1e-12] * 4 + [1e-13] * 4 + [1e-10] * 5,
            dtype=float,
        )
    else:
        rhs = state_rhs
        expected_size = 8
        default_initial = np.zeros(8, dtype=float)
        default_atol = np.array([1e-12] * 4 + [1e-13] * 4, dtype=float)

    integration_initial = (
        default_initial
        if initial_state is None
        else np.asarray(initial_state, dtype=float)
    )
    if integration_initial.shape != (expected_size,):
        raise ValueError(f"初始状态必须恰好包含 {expected_size} 项")
    integration_atol = default_atol if atol is None else atol

    solution = solve_ivp(
        rhs,
        t_span,
        integration_initial,
        args=(params, excitation_scale),
        method="DOP853",
        t_eval=evaluation_times,
        rtol=rtol,
        atol=integration_atol,
        max_step=max_step,
        dense_output=False,
    )
    if not solution.success:
        raise RuntimeError(f"积分失败: {solution.message}")
    if solution.y.shape[1] != evaluation_times.size:
        raise RuntimeError("积分器未返回全部指定时刻")
    if not np.all(np.isfinite(solution.y)):
        raise FloatingPointError("积分结果包含 NaN 或无穷值")
    return solution
