"""Pearson 相关矩阵热力图模板。"""

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

from colors import ERROR_CMAP  # noqa: E402
from science_style import apply_science_style, save_figure  # noqa: E402


def plot_correlation(df: pd.DataFrame, output_base: Path) -> None:
    """绘制 Pearson 相关矩阵。"""
    corr = df.corr(method="pearson")
    apply_science_style(figsize=(5.6, 4.8))
    fig, ax = plt.subplots()
    im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap=ERROR_CMAP)
    ax.set_xticks(np.arange(len(corr.columns)), corr.columns)
    ax.set_yticks(np.arange(len(corr.index)), corr.index)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")

    for i in range(corr.shape[0]):
        for j in range(corr.shape[1]):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)

    ax.set_title("Pearson Correlation Matrix")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    save_figure(fig, output_base)
    plt.close(fig)


def main() -> None:
    """示例：构造具有相关结构的数据表。"""
    rng = np.random.default_rng(2026)
    x1 = rng.normal(size=120)
    df = pd.DataFrame(
        {
            "Demand": x1,
            "Price": -0.55 * x1 + rng.normal(0, 0.7, 120),
            "Temperature": rng.normal(size=120),
            "Sales": 0.75 * x1 + rng.normal(0, 0.5, 120),
        }
    )
    plot_correlation(df, Path(__file__).with_name("output") / "correlation")


if __name__ == "__main__":
    main()
