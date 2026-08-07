"""综合评价雷达图模板。"""

from __future__ import annotations

import sys
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".matplotlib-cache"))
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "00_style"))

from colors import MODEL_COLORS  # noqa: E402
from science_style import apply_science_style, save_figure  # noqa: E402


def plot_radar(labels: list[str], scores: dict[str, list[float]], output_base: Path) -> None:
    """绘制多方案雷达图。"""
    apply_science_style(figsize=(5.2, 5.2))
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(subplot_kw={"polar": True})
    for idx, (name, values) in enumerate(scores.items()):
        values_closed = values + values[:1]
        ax.plot(angles, values_closed, label=name, color=MODEL_COLORS[idx])
        ax.fill(angles, values_closed, alpha=0.08, color=MODEL_COLORS[idx])

    ax.set_xticks(angles[:-1], labels)
    ax.set_ylim(0, 1)
    ax.set_title("Comprehensive Evaluation")
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.10))
    save_figure(fig, output_base)
    plt.close(fig)


def main() -> None:
    """示例：三种方案在多个指标上的综合表现。"""
    labels = ["Accuracy", "Cost", "Speed", "Robustness", "Interpretability"]
    scores = {
        "Plan A": [0.88, 0.72, 0.76, 0.91, 0.83],
        "Plan B": [0.81, 0.89, 0.85, 0.74, 0.78],
        "Plan C": [0.92, 0.68, 0.70, 0.86, 0.88],
    }
    plot_radar(labels, scores, Path(__file__).with_name("output") / "radar_chart")


if __name__ == "__main__":
    main()
