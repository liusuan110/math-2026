"""物理 / 工程类题目的轨迹与时序仿真骨架。

适用题型：
    - 烟幕干扰：导弹、无人机、烟幕云团随时间运动
    - 运动规划：最近接近、碰撞/覆盖持续时间
    - 工程仿真：给定参数 -> 轨迹采样 -> 判据 -> 目标函数

本文件尽量保持轻量，只依赖 numpy；复杂 ODE 仍用 `ode_models.py`。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def as_vec(x) -> np.ndarray:
    return np.asarray(x, dtype=float)


@dataclass
class LinearMotion:
    """匀速直线运动：position(t) = p0 + v * t。"""

    p0: np.ndarray
    v: np.ndarray

    def position(self, t):
        t = np.asarray(t, dtype=float)
        return self.p0 + np.expand_dims(t, -1) * self.v if t.ndim else self.p0 + self.v * float(t)


def constant_velocity_motion(p0, speed: float, direction) -> LinearMotion:
    """由初始点、速度大小、方向构造匀速运动。"""
    d = as_vec(direction)
    n = np.linalg.norm(d)
    if n == 0:
        raise ValueError("direction cannot be zero")
    return LinearMotion(as_vec(p0), speed * d / n)


def ballistic_position(p0, v0, t, gravity=9.80665) -> np.ndarray:
    """抛体运动位置。z 轴向上，重力沿 -z。"""
    p0, v0 = as_vec(p0), as_vec(v0)
    t = np.asarray(t, dtype=float)
    g = np.array([0.0, 0.0, -gravity])
    return p0 + np.expand_dims(t, -1) * v0 + 0.5 * np.expand_dims(t**2, -1) * g if t.ndim else p0 + v0 * float(t) + 0.5 * g * float(t) ** 2


def sample_time_grid(t0: float, t1: float, dt: float) -> np.ndarray:
    """稳定生成时间网格，包含右端点附近。"""
    n = int(np.floor((t1 - t0) / dt)) + 1
    return t0 + np.arange(n + 1) * dt


def closest_approach_linear(p1, v1, p2, v2, t_bounds=(0.0, np.inf)) -> dict:
    """两条匀速轨迹在给定时间范围内的最近接近。

    返回 {t, distance, p1, p2}。
    """
    p1, v1, p2, v2 = map(as_vec, (p1, v1, p2, v2))
    rel_p = p1 - p2
    rel_v = v1 - v2
    denom = float(np.dot(rel_v, rel_v))
    if denom < 1e-12:
        t_star = t_bounds[0]
    else:
        t_star = -float(np.dot(rel_p, rel_v)) / denom
        t_star = float(np.clip(t_star, t_bounds[0], t_bounds[1]))
    q1, q2 = p1 + v1 * t_star, p2 + v2 * t_star
    return {"t": t_star, "distance": float(np.linalg.norm(q1 - q2)), "p1": q1, "p2": q2}


def effective_duration(predicate, t0: float, t1: float, dt: float = 0.01) -> dict:
    """计算某个布尔判据在时间区间内成立的总时长和连续区间。

    predicate(t) -> bool。
    采用时间网格近似，适合烟幕遮蔽/覆盖有效时长等问题的快速目标函数。
    """
    ts = sample_time_grid(t0, t1, dt)
    ok = np.array([bool(predicate(float(t))) for t in ts])
    total = float(ok.sum() * dt)

    intervals = []
    in_seg = False
    start = None
    for i, flag in enumerate(ok):
        if flag and not in_seg:
            in_seg = True
            start = ts[i]
        if in_seg and (not flag or i == len(ok) - 1):
            end = ts[i - 1] if not flag else ts[i]
            intervals.append((float(start), float(end)))
            in_seg = False
    return {"duration": total, "intervals": intervals, "t": ts, "mask": ok}


@dataclass
class SmokeCloud:
    """烟幕云团简化模型：起爆后匀速下沉，有效半径固定，有效时长固定。"""

    detonation_position: np.ndarray
    detonation_time: float
    radius: float = 10.0
    sink_speed: float = 3.0
    effective_lifetime: float = 20.0

    def active(self, t: float) -> bool:
        return self.detonation_time <= t <= self.detonation_time + self.effective_lifetime

    def center(self, t: float) -> np.ndarray:
        if not self.active(t):
            return np.full(3, np.nan)
        dt = t - self.detonation_time
        return self.detonation_position + np.array([0.0, 0.0, -self.sink_speed * dt])


def smoke_from_drone_release(
    drone_p0,
    drone_speed: float,
    drone_direction,
    release_time: float,
    delay: float,
    gravity=9.80665,
    radius: float = 10.0,
    sink_speed: float = 3.0,
    effective_lifetime: float = 20.0,
) -> SmokeCloud:
    """由无人机投放参数生成烟幕云团。

    简化假设：无人机匀速直线，烟幕弹释放后继承无人机水平速度，竖直方向自由落体。
    """
    drone = constant_velocity_motion(drone_p0, drone_speed, drone_direction)
    release_pos = drone.position(release_time)
    v0 = drone.v
    det_pos = ballistic_position(release_pos, v0, delay, gravity=gravity)
    return SmokeCloud(det_pos, release_time + delay, radius, sink_speed, effective_lifetime)


if __name__ == "__main__":
    # 最近接近示例：导弹与无人机。
    missile = constant_velocity_motion([1000, -100, 300], 120, [-1, 0.1, -0.3])
    drone = constant_velocity_motion([100, 200, 180], 90, [1, -0.2, 0])
    ca = closest_approach_linear(missile.p0, missile.v, drone.p0, drone.v, (0, 20))
    print(f"最近接近 t={ca['t']:.2f}s, 距离={ca['distance']:.2f}m")

    # 烟幕起爆点示例。
    cloud = smoke_from_drone_release([100, 200, 180], 90, [1, -0.2, 0], 2.0, 3.0)
    print("烟幕起爆时刻/位置:", round(cloud.detonation_time, 2), np.round(cloud.detonation_position, 2))

    # 有效时长示例：某指标在 4~9 秒为真。
    dur = effective_duration(lambda t: 4 <= t <= 9, 0, 12, dt=0.1)
    print(f"有效时长≈{dur['duration']:.2f}s, 区间={dur['intervals'][:1]}")
