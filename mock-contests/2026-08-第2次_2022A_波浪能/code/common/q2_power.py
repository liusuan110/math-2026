"""问题二的稳态平均功率计算器。

常量阻尼采用复频域解析稳态；幂律阻尼采用逐周期时域积分，并把
PTO 瞬时功率作为附加状态积分，以避免粗采样数值积分误差。
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.integrate import solve_ivp
from scipy.optimize import root

from common.q1_dynamics import Q1Parameters


FloatArray = NDArray[np.float64]


def q2_parameters() -> Q1Parameters:
    """返回附件 3 情形 2 与附件 4 组成的问题二参数。"""

    return Q1Parameters(
        wave_omega=2.2143,
        added_mass=1165.992,
        radiation_damping=167.8395,
        excitation_amplitude=4890.0,
    )


@dataclass(frozen=True)
class ConstantPowerResult:
    """常量阻尼复频域稳态计算结果。"""

    damping: float
    mean_power: float
    displacement_phasor: NDArray[np.complex128]
    relative_displacement_amplitude: float
    relative_velocity_amplitude: float
    dynamic_residual_norm: float


@dataclass(frozen=True)
class PeriodicPowerResult:
    """幂律阻尼周期稳态平均功率结果。"""

    coefficient: float
    exponent: float
    mean_power: float
    cycles: int
    convergence_error: float
    consecutive_converged_cycles: int
    periodic_state: FloatArray
    pto_energy_last_cycle: float
    function_evaluations: int


@dataclass(frozen=True)
class ShootingPowerResult:
    """周期射击法得到的幂律阻尼稳态平均功率结果。"""

    coefficient: float
    exponent: float
    mean_power: float
    periodic_state: FloatArray
    pto_energy_one_cycle: float
    periodicity_error: float
    root_success: bool
    root_message: str
    root_map_evaluations: int
    ode_function_evaluations: int


def _validate_constant_damping(damping: float) -> float:
    damping = float(damping)
    if not np.isfinite(damping) or not 0.0 <= damping <= 100000.0:
        raise ValueError("常量阻尼系数必须位于 [0, 100000]")
    return damping


def _validate_power_parameters(coefficient: float, exponent: float) -> tuple[float, float]:
    coefficient = float(coefficient)
    exponent = float(exponent)
    if not np.isfinite(coefficient) or not 0.0 <= coefficient <= 100000.0:
        raise ValueError("幂律比例系数必须位于 [0, 100000]")
    if not np.isfinite(exponent) or not 0.0 <= exponent <= 1.0:
        raise ValueError("幂律指数必须位于 [0, 1]")
    return coefficient, exponent


def constant_system_matrices(
    damping: float,
    params: Q1Parameters | None = None,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """返回问题二常量阻尼系统的 M、C、K 矩阵。"""

    damping = _validate_constant_damping(damping)
    params = q2_parameters() if params is None else params
    mass = np.diag([params.effective_float_mass, params.oscillator_mass])
    damping_matrix = np.array(
        [
            [params.radiation_damping + damping, -damping],
            [-damping, damping],
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
    return mass, damping_matrix, stiffness


def constant_mean_power(
    damping: float,
    params: Q1Parameters | None = None,
) -> ConstantPowerResult:
    """用复频域稳态响应计算常量阻尼的平均输出功率。"""

    damping = _validate_constant_damping(damping)
    params = q2_parameters() if params is None else params
    mass, damping_matrix, stiffness = constant_system_matrices(damping, params)
    dynamic_stiffness = (
        stiffness
        - params.wave_omega**2 * mass
        + 1j * params.wave_omega * damping_matrix
    )
    excitation = np.array([params.excitation_amplitude, 0.0], dtype=complex)
    displacement = np.linalg.solve(dynamic_stiffness, excitation)
    relative_displacement = displacement[1] - displacement[0]
    relative_displacement_amplitude = float(abs(relative_displacement))
    relative_velocity_amplitude = params.wave_omega * relative_displacement_amplitude
    mean_power = 0.5 * damping * relative_velocity_amplitude**2
    residual = dynamic_stiffness @ displacement - excitation

    return ConstantPowerResult(
        damping=damping,
        mean_power=float(mean_power),
        displacement_phasor=displacement,
        relative_displacement_amplitude=relative_displacement_amplitude,
        relative_velocity_amplitude=float(relative_velocity_amplitude),
        dynamic_residual_norm=float(np.linalg.norm(residual)),
    )


def pto_force(relative_velocity: ArrayLike, coefficient: float, exponent: float):
    """返回幂律 PTO 阻尼力，方向按对浮子的作用力定义。"""

    coefficient, exponent = _validate_power_parameters(coefficient, exponent)
    velocity = np.asarray(relative_velocity, dtype=float)
    force = coefficient * np.abs(velocity) ** exponent * velocity
    return np.float64(force) if force.ndim == 0 else force


def pto_power(relative_velocity: ArrayLike, coefficient: float, exponent: float):
    """返回非负的 PTO 瞬时耗散功率。"""

    velocity = np.asarray(relative_velocity, dtype=float)
    power = pto_force(velocity, coefficient, exponent) * velocity
    return np.float64(power) if power.ndim == 0 else power


def nonlinear_state_rhs(
    t: float,
    state: ArrayLike,
    coefficient: float,
    exponent: float,
    params: Q1Parameters | None = None,
) -> FloatArray:
    """问题二幂律阻尼四状态方程右端。"""

    coefficient, exponent = _validate_power_parameters(coefficient, exponent)
    params = q2_parameters() if params is None else params
    values = np.asarray(state, dtype=float)
    if values.shape != (4,):
        raise ValueError("状态向量必须包含 [x_f, v_f, x_o, v_o] 四项")

    x_f, v_f, x_o, v_o = values
    relative_displacement = x_o - x_f
    relative_velocity = v_o - v_f
    damper = float(pto_force(relative_velocity, coefficient, exponent))
    spring = params.spring_stiffness * relative_displacement
    wave = params.excitation_amplitude * np.cos(params.wave_omega * t)
    acceleration_float = (
        wave
        - params.radiation_damping * v_f
        - params.hydrostatic_stiffness * x_f
        + spring
        + damper
    ) / params.effective_float_mass
    acceleration_oscillator = (-spring - damper) / params.oscillator_mass
    return np.array([v_f, acceleration_float, v_o, acceleration_oscillator])


def _augmented_cycle_rhs(
    t: float,
    augmented_state: ArrayLike,
    coefficient: float,
    exponent: float,
    params: Q1Parameters,
) -> FloatArray:
    """四个动力学状态加一个周期 PTO 累计能量。"""

    values = np.asarray(augmented_state, dtype=float)
    physical_rhs = nonlinear_state_rhs(
        t, values[:4], coefficient, exponent, params
    )
    relative_velocity = values[3] - values[1]
    instantaneous_power = float(pto_power(relative_velocity, coefficient, exponent))
    return np.concatenate((physical_rhs, [instantaneous_power]))


def _cycle_convergence(previous: FloatArray, current: FloatArray) -> float:
    """计算相邻周期同相位状态的无量纲相对差。"""

    return float(np.linalg.norm(current - previous) / (1.0 + np.linalg.norm(current)))


def periodic_mean_power(
    coefficient: float,
    exponent: float,
    params: Q1Parameters | None = None,
    *,
    initial_state: ArrayLike | None = None,
    convergence_tolerance: float = 1e-9,
    required_consecutive_cycles: int = 3,
    minimum_cycles: int = 8,
    maximum_cycles: int = 2000,
    rtol: float = 1e-9,
    atol: float = 1e-11,
    max_step_fraction: float = 1.0 / 120.0,
) -> PeriodicPowerResult:
    """计算幂律阻尼的周期稳态平均输出功率。

    每次只积分一个完整波浪周期，在相同激励相位比较周期端点状态。
    连续多个周期满足收敛阈值后，使用最后一周期的累计 PTO 能量除以
    周期长度得到平均功率。
    """

    coefficient, exponent = _validate_power_parameters(coefficient, exponent)
    params = q2_parameters() if params is None else params
    if convergence_tolerance <= 0.0:
        raise ValueError("收敛阈值必须为正数")
    if required_consecutive_cycles < 1:
        raise ValueError("连续收敛周期数至少为 1")
    if minimum_cycles < 1 or maximum_cycles < minimum_cycles:
        raise ValueError("周期数设置无效")
    if max_step_fraction <= 0.0:
        raise ValueError("最大步长比例必须为正数")

    if coefficient == 0.0:
        return PeriodicPowerResult(
            coefficient=coefficient,
            exponent=exponent,
            mean_power=0.0,
            cycles=0,
            convergence_error=0.0,
            consecutive_converged_cycles=required_consecutive_cycles,
            periodic_state=np.zeros(4),
            pto_energy_last_cycle=0.0,
            function_evaluations=0,
        )

    if initial_state is None:
        state = np.zeros(4, dtype=float)
    else:
        state = np.asarray(initial_state, dtype=float)
        if state.shape != (4,) or not np.all(np.isfinite(state)):
            raise ValueError("initial_state 必须是有限的四状态向量")

    period = 2.0 * pi / params.wave_omega
    max_step = period * max_step_fraction
    consecutive = 0
    convergence_error = np.inf
    total_nfev = 0
    last_energy = 0.0

    for cycle in range(1, maximum_cycles + 1):
        start_time = (cycle - 1) * period
        end_time = cycle * period
        augmented_initial = np.concatenate((state, [0.0]))
        solution = solve_ivp(
            _augmented_cycle_rhs,
            (start_time, end_time),
            augmented_initial,
            args=(coefficient, exponent, params),
            method="DOP853",
            rtol=rtol,
            atol=atol,
            max_step=max_step,
        )
        if not solution.success:
            raise RuntimeError(f"第 {cycle} 周期积分失败: {solution.message}")
        if not np.all(np.isfinite(solution.y)):
            raise FloatingPointError(f"第 {cycle} 周期结果含非有限值")

        new_state = solution.y[:4, -1]
        last_energy = float(solution.y[4, -1])
        total_nfev += int(solution.nfev)
        convergence_error = _cycle_convergence(state, new_state)
        state = new_state

        if cycle >= minimum_cycles and convergence_error <= convergence_tolerance:
            consecutive += 1
        else:
            consecutive = 0

        if consecutive >= required_consecutive_cycles:
            if last_energy < -1e-8:
                raise AssertionError("PTO 周期耗散能量出现负值")
            return PeriodicPowerResult(
                coefficient=coefficient,
                exponent=exponent,
                mean_power=last_energy / period,
                cycles=cycle,
                convergence_error=convergence_error,
                consecutive_converged_cycles=consecutive,
                periodic_state=state.copy(),
                pto_energy_last_cycle=last_energy,
                function_evaluations=total_nfev,
            )

    raise RuntimeError(
        f"在 {maximum_cycles} 个周期内未收敛，末次误差为 {convergence_error:.3e}"
    )


def _linear_proxy_periodic_state(
    coefficient: float,
    params: Q1Parameters,
) -> FloatArray:
    """用同系数常量阻尼稳态响应构造射击法初值。"""

    phasor = constant_mean_power(coefficient, params).displacement_phasor
    return np.array(
        [
            phasor[0].real,
            -params.wave_omega * phasor[0].imag,
            phasor[1].real,
            -params.wave_omega * phasor[1].imag,
        ],
        dtype=float,
    )


def shooting_mean_power(
    coefficient: float,
    exponent: float,
    params: Q1Parameters | None = None,
    *,
    initial_state: ArrayLike | None = None,
    root_tolerance: float = 1e-8,
    periodicity_tolerance: float = 1e-7,
    maximum_root_evaluations: int = 100,
    rtol: float = 1e-8,
    atol: float = 1e-10,
    max_step_fraction: float = 1.0 / 60.0,
) -> ShootingPowerResult:
    """用周期射击法直接求幂律阻尼的周期稳态平均功率。

    未提供初值时，以同系数常量阻尼的解析周期状态作为初猜。二维搜索
    时可把相邻参数点的周期状态传入 ``initial_state`` 进行连续延拓。
    """

    coefficient, exponent = _validate_power_parameters(coefficient, exponent)
    params = q2_parameters() if params is None else params
    if root_tolerance <= 0.0 or periodicity_tolerance <= 0.0:
        raise ValueError("射击法容差必须为正数")
    if maximum_root_evaluations < 1:
        raise ValueError("射击法最大映射次数至少为 1")
    if rtol <= 0.0 or atol <= 0.0 or max_step_fraction <= 0.0:
        raise ValueError("积分容差与最大步长比例必须为正数")

    if coefficient == 0.0:
        return ShootingPowerResult(
            coefficient=coefficient,
            exponent=exponent,
            mean_power=0.0,
            periodic_state=np.zeros(4),
            pto_energy_one_cycle=0.0,
            periodicity_error=0.0,
            root_success=True,
            root_message="zero-power boundary",
            root_map_evaluations=0,
            ode_function_evaluations=0,
        )

    if initial_state is None:
        guess = _linear_proxy_periodic_state(coefficient, params)
    else:
        guess = np.asarray(initial_state, dtype=float)
        if guess.shape != (4,) or not np.all(np.isfinite(guess)):
            raise ValueError("initial_state 必须是有限的四状态向量")

    period = params.period
    max_step = period * max_step_fraction
    total_ode_evaluations = 0

    def periodicity_residual(state: FloatArray) -> FloatArray:
        nonlocal total_ode_evaluations
        solution = solve_ivp(
            nonlinear_state_rhs,
            (0.0, period),
            state,
            args=(coefficient, exponent, params),
            method="DOP853",
            rtol=rtol,
            atol=atol,
            max_step=max_step,
        )
        if not solution.success:
            raise RuntimeError(f"射击映射积分失败：{solution.message}")
        total_ode_evaluations += int(solution.nfev)
        return solution.y[:, -1] - state

    root_result = root(
        periodicity_residual,
        guess,
        method="hybr",
        options={"xtol": root_tolerance, "maxfev": maximum_root_evaluations},
    )
    state = np.asarray(root_result.x, dtype=float)
    if not np.all(np.isfinite(state)):
        raise FloatingPointError("射击法返回了非有限周期状态")

    augmented = solve_ivp(
        _augmented_cycle_rhs,
        (0.0, period),
        np.concatenate((state, [0.0])),
        args=(coefficient, exponent, params),
        method="DOP853",
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    if not augmented.success:
        raise RuntimeError(f"射击法功率积分失败：{augmented.message}")
    total_ode_evaluations += int(augmented.nfev)
    closure = augmented.y[:4, -1] - state
    periodicity_error = _cycle_convergence(state, augmented.y[:4, -1])
    energy = float(augmented.y[4, -1])
    if energy < -1e-8:
        raise AssertionError("射击法 PTO 周期耗散能量出现负值")
    if periodicity_error > periodicity_tolerance:
        raise RuntimeError(
            "射击法周期闭合未通过："
            f"error={periodicity_error:.3e}, residual_norm={np.linalg.norm(closure):.3e}, "
            f"root_message={root_result.message}"
        )

    return ShootingPowerResult(
        coefficient=coefficient,
        exponent=exponent,
        mean_power=energy / period,
        periodic_state=state.copy(),
        pto_energy_one_cycle=energy,
        periodicity_error=periodicity_error,
        root_success=bool(root_result.success),
        root_message=str(root_result.message),
        root_map_evaluations=int(root_result.nfev),
        ode_function_evaluations=total_ode_evaluations,
    )


def sample_period_from_state(
    periodic_state: ArrayLike,
    coefficient: float,
    exponent: float,
    params: Q1Parameters | None = None,
    *,
    samples: int = 2001,
    rtol: float = 1e-11,
    atol: float = 1e-13,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """从周期起点状态重算一个周期，返回时间、状态和瞬时功率。"""

    coefficient, exponent = _validate_power_parameters(coefficient, exponent)
    params = q2_parameters() if params is None else params
    state = np.asarray(periodic_state, dtype=float)
    if state.shape != (4,):
        raise ValueError("periodic_state 必须为四状态向量")
    if samples < 3:
        raise ValueError("每周期采样点至少为 3")

    period = 2.0 * pi / params.wave_omega
    times = np.linspace(0.0, period, samples)
    solution = solve_ivp(
        nonlinear_state_rhs,
        (0.0, period),
        state,
        t_eval=times,
        args=(coefficient, exponent, params),
        method="DOP853",
        rtol=rtol,
        atol=atol,
        max_step=period / 240.0,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    relative_velocity = solution.y[3] - solution.y[1]
    power = np.asarray(pto_power(relative_velocity, coefficient, exponent))
    return solution.t, solution.y, power
