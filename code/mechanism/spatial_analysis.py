"""空间点集与覆盖分析模板。

参考思想：
    - scipy.spatial: KDTree、Delaunay、ConvexHull、距离矩阵等空间算法

适合：
    - 多波束测线：测线点到海域采样点的覆盖距离
    - 定日镜场：镜面/采样点的近邻、遮挡候选筛选
    - 烟幕题：目标点云、云团中心、视线采样的近邻判定
    - 任何二维/三维空间覆盖、分区、凸包面积/体积估计
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import ConvexHull, Delaunay, KDTree, distance_matrix


def nearest_neighbors(points, query_points, k=1) -> dict:
    """KDTree 最近邻查询。"""
    pts = np.asarray(points, dtype=float)
    q = np.asarray(query_points, dtype=float)
    tree = KDTree(pts)
    dist, idx = tree.query(q, k=k)
    return {"distance": dist, "index": idx}


def coverage_by_centers(sample_points, centers, radius: float) -> dict:
    """多个中心点半径覆盖：判断采样点是否被任一中心覆盖。"""
    sample_points = np.asarray(sample_points, dtype=float)
    centers = np.asarray(centers, dtype=float)
    tree = KDTree(centers)
    dist, idx = tree.query(sample_points, k=1)
    covered = dist <= radius
    return {
        "covered": covered,
        "coverage_rate": float(np.mean(covered)),
        "nearest_center_index": idx,
        "nearest_distance": dist,
    }


def pairwise_distance_stats(points_a, points_b) -> dict:
    """两组点之间距离矩阵统计。"""
    D = distance_matrix(np.asarray(points_a, dtype=float), np.asarray(points_b, dtype=float))
    return {
        "min": float(np.min(D)),
        "max": float(np.max(D)),
        "mean": float(np.mean(D)),
        "matrix": D,
    }


def convex_hull_measure(points) -> dict:
    """凸包面积/体积。

    2D: hull.volume 是面积，hull.area 是周长。
    3D: hull.volume 是体积，hull.area 是表面积。
    """
    pts = np.asarray(points, dtype=float)
    hull = ConvexHull(pts)
    dim = pts.shape[1]
    return {
        "dimension": dim,
        "vertices": hull.vertices,
        "area_or_perimeter": float(hull.area),
        "volume_or_area": float(hull.volume),
        "hull": hull,
    }


def point_in_convex_hull(points, query_points, tol=1e-12) -> np.ndarray:
    """判断查询点是否在点集凸包内。

    用 Delaunay 三角剖分近似判断，适合二维/三维点云。
    """
    tri = Delaunay(np.asarray(points, dtype=float))
    q = np.asarray(query_points, dtype=float)
    return tri.find_simplex(q, tol=tol) >= 0


def line_coverage_strip(points, line_start, line_end, half_width: float) -> np.ndarray:
    """二维/三维测线条带覆盖判定：点到线段距离 <= half_width。

    多波束测线题里，可把测线看成一条带状覆盖区域的中心线。
    """
    pts = np.asarray(points, dtype=float)
    a = np.asarray(line_start, dtype=float)
    b = np.asarray(line_end, dtype=float)
    ab = b - a
    denom = np.dot(ab, ab)
    if denom <= 1e-15:
        dist = np.linalg.norm(pts - a, axis=1)
    else:
        t = np.clip(((pts - a) @ ab) / denom, 0.0, 1.0)
        closest = a + t[:, None] * ab
        dist = np.linalg.norm(pts - closest, axis=1)
    return dist <= half_width


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    area_points = rng.random((500, 2)) * np.array([1000, 600])
    survey_lines = np.array([[200, 150], [500, 300], [800, 450]])
    cov = coverage_by_centers(area_points, survey_lines, radius=120)
    print(f"中心覆盖率: {cov['coverage_rate']:.3f}")

    strip = line_coverage_strip(area_points, [0, 300], [1000, 300], half_width=80)
    print(f"单条测线条带覆盖率: {strip.mean():.3f}")

    hull = convex_hull_measure(area_points[:30])
    print(f"二维凸包面积≈{hull['volume_or_area']:.1f}, 周长≈{hull['area_or_perimeter']:.1f}")
