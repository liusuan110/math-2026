"""敏感性分析曲线模板。"""

from __future__ import annotations

import sys
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".matplotlib-cache"))
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "00_style"))

from science_style import apply_science_style, save_figure, set_axis_labels  # noqa: E402


def plot_sensitivity(parameter_values: np.ndarray, objective_values: np.ndarray, output_base: Path) -> None:
    """绘制参数变化对目标函数的影响曲线。"""
    apply_science_style()
    fig, ax = plt.subplots()
    ax.plot(parameter_values, objective_values, marker="o", markersize=3)
    best_idx = int(np.argmax(objective_values))
    ax.scatter(parameter_values[best_idx], objective_values[best_idx], color="#d62728", zorder=5)
    ax.annotate(
        "Best",
        xy=(parameter_values[best_idx], objective_values[best_idx]),
        xytext=(8, 8),
        textcoords="offset points",
    )
    set_axis_labels(ax, "Parameter value", "Objective value", "Sensitivity Analysis")
    save_figure(fig, output_base)
    plt.close(fig)


def main() -> None:
    """示例：资源投入比例对收益的影响。"""
    p = np.linspace(0.1, 1.0, 30)
    y = 80 * (1 - np.exp(-3 * p)) - 18 * p**2
    plot_sensitivity(p, y, Path(__file__).with_name("output") / "sensitivity_analysis")


if __name__ == "__main__":
    main()
