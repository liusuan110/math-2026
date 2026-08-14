"""物理 / 工程类题目的三维几何判据工具。

适用题型：
    - 烟幕遮蔽：点/线段/球体距离，视线是否被遮挡
    - 定日镜场：向量反射、平面/射线交点、遮挡检查
    - 多波束测线：覆盖宽度、点到测线距离
    - 轨迹规划：最近距离、碰撞/覆盖判据

设计原则：
    1. 只依赖 numpy，便于赛时复制到任意题目工程。
    2. 函数尽量返回可解释的中间量，方便写论文和画机制图。
    3. 默认按三维向量处理，二维点也可补 z=0 后使用。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


EPS = 1e-12


def as_vec(x) -> np.ndarray:
    """转为 float 向量。"""
    return np.asarray(x, dtype=float)


def norm(v) -> float:
    """欧氏范数。"""
    return float(np.linalg.norm(as_vec(v)))


def unit(v) -> np.ndarray:
    """单位向量；零向量会抛错，避免静默产生 NaN。"""
    v = as_vec(v)
    n = np.linalg.norm(v)
    if n < EPS:
        raise ValueError("zero vector has no direction")
    return v / n


def angle_between(a, b) -> float:
    """两个向量夹角，单位 rad。"""
    ua, ub = unit(a), unit(b)
    c = float(np.clip(np.dot(ua, ub), -1.0, 1.0))
    return float(math.acos(c))


def projection_parameter(point, a, b) -> float:
    """点 point 在线段 a-b 所在直线上的投影参数 t。

    t=0 对应 a，t=1 对应 b；若 0<=t<=1，投影落在线段内部。
    """
    p, a, b = as_vec(point), as_vec(a), as_vec(b)
    ab = b - a
    denom = float(np.dot(ab, ab))
    if denom < EPS:
        return 0.0
    return float(np.dot(p - a, ab) / denom)


def closest_point_on_segment(point, a, b) -> np.ndarray:
    """点到线段的最近点。"""
    t = np.clip(projection_parameter(point, a, b), 0.0, 1.0)
    a, b = as_vec(a), as_vec(b)
    return a + t * (b - a)


def distance_point_to_line(point, a, b) -> float:
    """点到无限直线 a-b 的距离。"""
    p, a, b = as_vec(point), as_vec(a), as_vec(b)
    ab = b - a
    if np.dot(ab, ab) < EPS:
        return norm(p - a)
    return norm(np.cross(p - a, ab)) / norm(ab)


def distance_point_to_segment(point, a, b) -> float:
    """点到线段 a-b 的距离。"""
    return norm(as_vec(point) - closest_point_on_segment(point, a, b))


@dataclass
class SegmentSphereResult:
    intersects: bool
    distance: float
    closest_point: np.ndarray
    t: float


def segment_sphere_intersection(a, b, center, radius: float) -> SegmentSphereResult:
    """线段 a-b 是否穿过/接触球体。

    这就是烟幕遮蔽、碰撞检测、有效覆盖判断里最常用的核心判据：
    若球心到视线线段的最近距离 <= 半径，则视线被球体覆盖。
    """
    a, b, c = as_vec(a), as_vec(b), as_vec(center)
    t = float(np.clip(projection_parameter(c, a, b), 0.0, 1.0))
    q = a + t * (b - a)
    d = norm(c - q)
    return SegmentSphereResult(d <= radius + EPS, d, q, t)


def line_plane_intersection(point_on_line, direction, point_on_plane, normal):
    """直线与平面交点。

    返回 None 表示直线与平面平行或重合；否则返回交点坐标。
    """
    p0, d = as_vec(point_on_line), as_vec(direction)
    pp, n = as_vec(point_on_plane), as_vec(normal)
    denom = float(np.dot(d, n))
    if abs(denom) < EPS:
        return None
    t = float(np.dot(pp - p0, n) / denom)
    return p0 + t * d


def ray_plane_intersection(ray_origin, ray_direction, point_on_plane, normal):
    """射线与平面交点；若交点在射线反方向，返回 None。"""
    p0, d = as_vec(ray_origin), as_vec(ray_direction)
    pp, n = as_vec(point_on_plane), as_vec(normal)
    denom = float(np.dot(d, n))
    if abs(denom) < EPS:
        return None
    t = float(np.dot(pp - p0, n) / denom)
    if t < -EPS:
        return None
    return p0 + t * d


def reflect_vector(incoming, normal) -> np.ndarray:
    """向量关于法向量 normal 的镜面反射。

    incoming 是入射方向向量；返回反射方向。
    """
    v = unit(incoming)
    n = unit(normal)
    return v - 2 * np.dot(v, n) * n


def rotation_matrix(axis, angle: float) -> np.ndarray:
    """Rodrigues 旋转矩阵。axis 为旋转轴，angle 单位 rad。"""
    x, y, z = unit(axis)
    c, s = math.cos(angle), math.sin(angle)
    C = 1 - c
    return np.array(
        [
            [c + x * x * C, x * y * C - z * s, x * z * C + y * s],
            [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
            [z * x * C - y * s, z * y * C + x * s, c + z * z * C],
        ]
    )


def transform_points(points, R=None, translation=None) -> np.ndarray:
    """批量坐标变换：points @ R.T + translation。"""
    pts = np.asarray(points, dtype=float)
    out = pts.copy()
    if R is not None:
        out = out @ np.asarray(R, dtype=float).T
    if translation is not None:
        out = out + as_vec(translation)
    return out


def sample_cylinder_surface(center, radius: float, height: float, n_theta=72, n_z=12) -> np.ndarray:
    """采样竖直圆柱表面点，适合把真实目标/障碍物离散成判据点。"""
    cx, cy, cz = as_vec(center)
    theta = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    z = np.linspace(cz - height / 2, cz + height / 2, n_z)
    tt, zz = np.meshgrid(theta, z)
    x = cx + radius * np.cos(tt)
    y = cy + radius * np.sin(tt)
    return np.column_stack([x.ravel(), y.ravel(), zz.ravel()])


def point_in_vertical_cylinder(point, center_xy, radius: float, z_min: float, z_max: float) -> bool:
    """点是否在竖直圆柱内部。"""
    p = as_vec(point)
    c = as_vec(center_xy)
    inside_xy = norm(p[:2] - c[:2]) <= radius + EPS
    inside_z = z_min - EPS <= p[2] <= z_max + EPS
    return bool(inside_xy and inside_z)


def multibeam_coverage_width(depth: float, beam_angle_deg: float, slope_angle_deg: float = 0.0) -> float:
    """多波束覆盖宽度的常用近似公式。

    平坦海底时 width = 2 * depth * tan(theta/2)。
    若海底坡度为 alpha，这里给一个常用坡度修正近似：
    width = depth * sin(theta) / (cos(alpha)^2 - sin(theta/2)^2)

    赛时应以题面给定几何关系为准；本函数主要作为快速基线。
    """
    theta = math.radians(beam_angle_deg)
    alpha = math.radians(slope_angle_deg)
    if abs(alpha) < EPS:
        return float(2 * depth * math.tan(theta / 2))
    denom = math.cos(alpha) ** 2 - math.sin(theta / 2) ** 2
    if abs(denom) < EPS:
        raise ValueError("coverage formula denominator is near zero")
    return float(depth * math.sin(theta) * math.cos(alpha) / denom)


if __name__ == "__main__":
    # 烟幕遮蔽式判据：云团是否遮住“导弹-目标”视线。
    missile = np.array([1000.0, -100.0, 300.0])
    target = np.array([0.0, 0.0, 0.0])
    cloud = np.array([420.0, -42.0, 126.0])
    radius = 12.0
    res = segment_sphere_intersection(missile, target, cloud, radius)
    print(f"视线到云团最近距离 = {res.distance:.3f} m, 是否遮蔽 = {res.intersects}")

    # 定日镜式反射：入射光关于镜面法向反射。
    incoming = unit([0, 0, -1])
    normal = unit([0.2, 0.0, 1.0])
    reflected = reflect_vector(incoming, normal)
    print("反射方向:", np.round(reflected, 4))

    # 多波束覆盖宽度基线。
    print("水深 100m、开角120°覆盖宽度:", round(multibeam_coverage_width(100, 120), 2), "m")
