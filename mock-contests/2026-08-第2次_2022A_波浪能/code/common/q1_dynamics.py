"""问题一的垂荡动力学模型与数值积分公共组件。

坐标均以静水平衡位置为零点，竖直向上为正。这个模块只包含模型、
积分和核验所需的基础函数，不负责生成正式工作簿或论文图片。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import pi
from typing import Iterable

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.integrate import solve_ivp


FloatArray = NDArray[np.float64]


class DampingLaw(str, Enum):
    """问题一规定的两种 PTO 直线阻尼规律。"""

    CONSTANT = "constant"
    POWER = "power"


@dataclass(frozen=True)
class Q1Parameters:
    """问题一使用的官方参数及阻尼参数。"""

    wave_omega: float = 1.4005
    added_mass: float = 1335.535
    radiation_damping: float = 656.3616
    excitation_amplitude: float = 6250.0
    float_mass: float = 4866.0
    oscillator_mass: float = 2433.0
    seawater_density: float = 1025.0
    gravity: float = 9.8
    float_radius: float = 1.0
    float_cylinder_height: float = 3.0
    float_cone_height: float = 0.8
    spring_stiffness: float = 80000.0
    spring_natural_length: float = 0.5
    constant_damping: float = 10000.0
    power_coefficient: float = 10000.0
    power_exponent: float = 0.5

    def __post_init__(self) -> None:
        positive = {
            "wave_omega": self.wave_omega,
            "added_mass": self.added_mass,
            "radiation_damping": self.radiation_damping,
            "excitation_amplitude": self.excitation_amplitude,
            "float_mass": self.float_mass,
            "oscillator_mass": self.oscillator_mass,
            "seawater_density": self.seawater_density,
            "gravity": self.gravity,
            "float_radius": self.float_radius,
            "float_cylinder_height": self.float_cylinder_height,
            "float_cone_height": self.float_cone_height,
            "spring_stiffness": self.spring_stiffness,
            "spring_natural_length": self.spring_natural_length,
            "constant_damping": self.constant_damping,
            "power_coefficient": self.power_coefficient,
        }
        invalid = [name for name, value in positive.items() if value <= 0]
        if invalid:
            raise ValueError(f"参数必须为正数: {', '.join(invalid)}")
        if self.power_exponent < 0:
            raise ValueError("幂律阻尼指数不得为负")

    @property
    def effective_float_mass(self) -> float:
        """浮子质量与垂荡附加质量之和，单位 kg。"""

        return self.float_mass + self.added_mass

    @property
    def hydrostatic_stiffness(self) -> float:
        """圆柱水线面的静水恢复刚度，单位 N/m。"""

        return self.seawater_density * self.gravity * pi * self.float_radius**2

    @property
    def period(self) -> float:
        """入射波浪周期，单位 s。"""

        return 2.0 * pi / self.wave_omega

    @property
    def static_cylinder_draft(self) -> float:
        """静态时圆锥以上的圆柱浸水高度，单位 m。"""

        displaced_volume = (
            self.float_mass + self.oscillator_mass
        ) / self.seawater_density
        cone_volume = pi * self.float_radius**2 * self.float_cone_height / 3.0
        return (displaced_volume - cone_volume) / (pi * self.float_radius**2)

    @property
    def spring_equilibrium_length(self) -> float:
        """弹簧承担振子重量后的静态长度，单位 m。"""

        compression = self.oscillator_mass * self.gravity / self.spring_stiffness
        return self.spring_natural_length - compression


def damping_force(
    relative_velocity: ArrayLike,
    law: DampingLaw,
    params: Q1Parameters,
) -> FloatArray | np.float64:
    """返回 PTO 对浮子的阻尼力。

    相对速度定义为 ``v_o - v_f``。返回值为该阻尼器对浮子的作用力，
    对振子的作用力取相反数。
    """

    velocity = np.asarray(relative_velocity, dtype=float)
    if law is DampingLaw.CONSTANT:
        force = params.constant_damping * velocity
    elif law is DampingLaw.POWER:
        force = (
            params.power_coefficient
            * np.abs(velocity) ** params.power_exponent
            * velocity
        )
    else:
        raise ValueError(f"未知阻尼规律: {law!r}")
    return np.float64(force) if force.ndim == 0 else force


def coupling_forces(
    relative_displacement: float,
    relative_velocity: float,
    law: DampingLaw,
    params: Q1Parameters,
) -> tuple[float, float]:
    """返回耦合元件分别施加在浮子与振子上的力。"""

    force_on_float = float(
        params.spring_stiffness * relative_displacement
        + damping_force(relative_velocity, law, params)
    )
    return force_on_float, -force_on_float


def state_rhs(
    t: float,
    state: ArrayLike,
    params: Q1Parameters,
    law: DampingLaw,
    excitation_scale: float = 1.0,
) -> FloatArray:
    """四状态一阶方程右端。

    状态顺序固定为 ``[x_f, v_f, x_o, v_o]``。
    """

    values = np.asarray(state, dtype=float)
    if values.shape != (4,):
        raise ValueError("状态向量必须恰好包含 [x_f, v_f, x_o, v_o] 四项")

    x_f, v_f, x_o, v_o = values
    relative_displacement = x_o - x_f
    relative_velocity = v_o - v_f
    force_on_float, force_on_oscillator = coupling_forces(
        relative_displacement, relative_velocity, law, params
    )
    wave_force = (
        excitation_scale
        * params.excitation_amplitude
        * np.cos(params.wave_omega * t)
    )

    acceleration_float = (
        wave_force
        - params.radiation_damping * v_f
        - params.hydrostatic_stiffness * x_f
        + force_on_float
    ) / params.effective_float_mass
    acceleration_oscillator = force_on_oscillator / params.oscillator_mass

    return np.array(
        [v_f, acceleration_float, v_o, acceleration_oscillator], dtype=float
    )


def mechanical_energy(state: ArrayLike, params: Q1Parameters) -> float:
    """返回平衡点增量坐标下的系统机械能，单位 J。"""

    x_f, v_f, x_o, v_o = np.asarray(state, dtype=float)[:4]
    relative_displacement = x_o - x_f
    return float(
        0.5 * params.effective_float_mass * v_f**2
        + 0.5 * params.oscillator_mass * v_o**2
        + 0.5 * params.hydrostatic_stiffness * x_f**2
        + 0.5 * params.spring_stiffness * relative_displacement**2
    )


def state_rhs_with_energy(
    t: float,
    augmented_state: ArrayLike,
    params: Q1Parameters,
    law: DampingLaw,
    excitation_scale: float = 1.0,
) -> FloatArray:
    """在四个物理状态后附加三项累计能量。

    附加状态依次为波浪输入功、兴波耗散、PTO 耗散，均以正值累计。
    """

    values = np.asarray(augmented_state, dtype=float)
    if values.shape != (7,):
        raise ValueError("能量核验状态必须包含 4 个物理量和 3 个累计能量")

    physical_rhs = state_rhs(t, values[:4], params, law, excitation_scale)
    _, v_f, _, v_o = values[:4]
    relative_velocity = v_o - v_f
    wave_force = (
        excitation_scale
        * params.excitation_amplitude
        * np.cos(params.wave_omega * t)
    )
    input_power = wave_force * v_f
    radiation_power = params.radiation_damping * v_f**2
    pto_power = float(damping_force(relative_velocity, law, params)) * relative_velocity

    return np.concatenate(
        (physical_rhs, np.array([input_power, radiation_power, pto_power]))
    )


def output_time_grid(params: Q1Parameters) -> FloatArray:
    """返回题目规定的 40 周期内 0.2 s 等间隔输出网格。"""

    last_index = int(np.floor((40.0 * params.period) / 0.2 + 1e-12))
    return 0.2 * np.arange(last_index + 1, dtype=float)


def solve_response(
    params: Q1Parameters,
    law: DampingLaw,
    t_span: tuple[float, float],
    t_eval: Iterable[float],
    *,
    excitation_scale: float = 1.0,
    rtol: float = 1e-10,
    atol: float = 1e-12,
    max_step: float = 0.02,
    track_energy: bool = False,
    initial_state: ArrayLike | None = None,
):
    """按统一设置积分问题一模型，并在失败时立即报错。"""

    evaluation_times = np.asarray(tuple(t_eval), dtype=float)
    if evaluation_times.ndim != 1 or evaluation_times.size == 0:
        raise ValueError("t_eval 必须是一维非空时间序列")
    if np.any(np.diff(evaluation_times) <= 0):
        raise ValueError("t_eval 必须严格递增")
    if evaluation_times[0] < t_span[0] or evaluation_times[-1] > t_span[1]:
        raise ValueError("t_eval 必须位于 t_span 内")

    if track_energy:
        rhs = state_rhs_with_energy
        default_initial_state = np.zeros(7, dtype=float)
        expected_state_size = 7
    else:
        rhs = state_rhs
        default_initial_state = np.zeros(4, dtype=float)
        expected_state_size = 4

    if initial_state is None:
        integration_initial_state = default_initial_state
    else:
        integration_initial_state = np.asarray(initial_state, dtype=float)
        if integration_initial_state.shape != (expected_state_size,):
            raise ValueError(
                f"初始状态必须包含 {expected_state_size} 项，"
                f"当前形状为 {integration_initial_state.shape}"
            )

    solution = solve_ivp(
        rhs,
        t_span,
        integration_initial_state,
        args=(params, law, excitation_scale),
        method="DOP853",
        t_eval=evaluation_times,
        rtol=rtol,
        atol=atol,
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


def constant_system_matrices(
    params: Q1Parameters,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """返回常量阻尼情形的质量、阻尼、刚度矩阵。"""

    mass = np.diag([params.effective_float_mass, params.oscillator_mass])
    damping = np.array(
        [
            [params.radiation_damping + params.constant_damping, -params.constant_damping],
            [-params.constant_damping, params.constant_damping],
        ],
        dtype=float,
    )
    stiffness = np.array(
        [
            [params.hydrostatic_stiffness + params.spring_stiffness, -params.spring_stiffness],
            [-params.spring_stiffness, params.spring_stiffness],
        ],
        dtype=float,
    )
    return mass, damping, stiffness
