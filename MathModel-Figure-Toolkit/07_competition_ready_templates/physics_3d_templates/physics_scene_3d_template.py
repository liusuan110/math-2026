"""物理 / 工程类题目的三维机制图模板。

用途：
    - 展示空间几何关系、目标、运动轨迹、覆盖/遮挡区域
    - 适合烟幕、定日镜、多波束、轨迹规划、覆盖优化等题型

运行：
    python physics_scene_3d_template.py

说明：
    本模板默认使用 matplotlib 3D，保证基础环境也能跑。
    若比赛前安装 PyVista，可以参考 external-tools/figure-tools/pyvista
    做更精细的三维网格、透明体、交互式检查图。
"""

from __future__ import annotations

import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_DIR = SCRIPT_DIR / ".mplconfig"
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


OUTPUT_DIR = SCRIPT_DIR / "output"


def set_axes_equal(ax) -> None:
    """让 3D 坐标轴比例一致，避免球体/轨迹视觉变形。"""
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    y_range = abs(y_limits[1] - y_limits[0])
    z_range = abs(z_limits[1] - z_limits[0])

    x_mid = np.mean(x_limits)
    y_mid = np.mean(y_limits)
    z_mid = np.mean(z_limits)
    radius = 0.5 * max([x_range, y_range, z_range])

    ax.set_xlim3d([x_mid - radius, x_mid + radius])
    ax.set_ylim3d([y_mid - radius, y_mid + radius])
    ax.set_zlim3d([z_mid - radius, z_mid + radius])


def sphere_mesh(center, radius, n_u=36, n_v=18):
    u = np.linspace(0, 2 * np.pi, n_u)
    v = np.linspace(0, np.pi, n_v)
    x = center[0] + radius * np.outer(np.cos(u), np.sin(v))
    y = center[1] + radius * np.outer(np.sin(u), np.sin(v))
    z = center[2] + radius * np.outer(np.ones_like(u), np.cos(v))
    return x, y, z


def plot_physics_scene() -> None:
    t = np.linspace(0, 12, 160)
    missile = np.column_stack(
        [
            1100 - 80 * t,
            -180 + 15 * t,
            450 - 28 * t,
        ]
    )
    vehicle = np.column_stack(
        [
            100 + 35 * t,
            260 - 6 * t,
            180 + 0 * t,
        ]
    )
    target = np.array([0, 0, 0])
    cloud_center = np.array([410, 185, 95])
    cloud_radius = 75

    fig = plt.figure(figsize=(8.2, 6.2))
    ax = fig.add_subplot(111, projection="3d")

    ax.plot(missile[:, 0], missile[:, 1], missile[:, 2], color="#C0392B", lw=2.0, label="Incoming trajectory")
    ax.plot(vehicle[:, 0], vehicle[:, 1], vehicle[:, 2], color="#2E6F9E", lw=2.0, label="Vehicle / drone trajectory")
    ax.scatter(*target, color="#333333", marker="s", s=70, label="Protected target")
    ax.scatter(*missile[0], color="#C0392B", marker="^", s=70)
    ax.scatter(*vehicle[0], color="#2E6F9E", marker="o", s=60)

    sx, sy, sz = sphere_mesh(cloud_center, cloud_radius)
    ax.plot_surface(sx, sy, sz, color="#7F8C8D", alpha=0.22, linewidth=0, shade=False)
    ax.scatter(*cloud_center, color="#7F8C8D", s=40, label="Effective region")

    # 关键判据线：目标 - 云团 - 导弹视线示意
    key_index = 88
    key_missile = missile[key_index]
    ax.plot(
        [target[0], cloud_center[0], key_missile[0]],
        [target[1], cloud_center[1], key_missile[1]],
        [target[2], cloud_center[2], key_missile[2]],
        color="#D68910",
        lw=1.4,
        linestyle="--",
        label="Line-of-sight criterion",
    )

    ax.text(*target, "  Target", fontsize=9)
    ax.text(*cloud_center, "  Effective region", fontsize=9)
    ax.text(*key_missile, "  Key time", fontsize=9)

    ax.set_xlabel("X / m")
    ax.set_ylabel("Y / m")
    ax.set_zlabel("Z / m")
    ax.set_title("3D physical mechanism: trajectory and effective region")
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    ax.view_init(elev=22, azim=-58)
    set_axes_equal(ax)
    fig.tight_layout()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUTPUT_DIR / f"physics_3d_scene.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figures to: {OUTPUT_DIR}")


if __name__ == "__main__":
    plot_physics_scene()
