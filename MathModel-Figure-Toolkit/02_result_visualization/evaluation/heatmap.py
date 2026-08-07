"""评价矩阵热力图模板。"""

from __future__ import annotations

import sys
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".matplotlib-cache"))
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "00_style"))

from colors import HEATMAP_CMAP  # noqa: E402
from science_style import apply_science_style, save_figure  # noqa: E402


def plot_heatmap(df: pd.DataFrame, output_base: Path) -> None:
    """绘制带数值标注的评价矩阵热力图。"""
    apply_science_style(figsize=(5.6, 4.6))
    fig, ax = plt.subplots()
    im = ax.imshow(df.values, cmap=HEATMAP_CMAP)
    ax.set_xticks(np.arange(df.shape[1]), labels=df.columns)
    ax.set_yticks(np.arange(df.shape[0]), labels=df.index)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")

    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            ax.text(j, i, f"{df.iloc[i, j]:.2f}", ha="center", va="center", color="white")

    ax.set_title("Evaluation Matrix Heatmap")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    save_figure(fig, output_base)
    plt.close(fig)


def main() -> None:
    """示例：候选方案综合评价矩阵。"""
    df = pd.DataFrame(
        [[0.82, 0.75, 0.91], [0.67, 0.88, 0.72], [0.93, 0.64, 0.85]],
        index=["Plan A", "Plan B", "Plan C"],
        columns=["Cost", "Benefit", "Robustness"],
    )
    plot_heatmap(df, Path(__file__).with_name("output") / "heatmap")


if __name__ == "__main__":
    main()
