"""统一科研绘图风格工具。

优先使用 SciencePlots；若本地未安装，自动退回到 matplotlib 内置参数。
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt


def apply_science_style(figsize: tuple[float, float] = (6.4, 3.8)) -> None:
    """应用论文级 matplotlib 风格。

    参数
    ----
    figsize:
        默认接近 IEEE 单栏/半页图比例，适合插入数模论文。
    """
    try:
        import scienceplots  # noqa: F401

        plt.style.use(["science", "ieee", "no-latex"])
    except Exception:
        plt.style.use("default")

    plt.rcParams.update(
        {
            "figure.figsize": figsize,
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "font.family": "Times New Roman",
            "axes.unicode_minus": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
            "axes.linewidth": 0.9,
            "lines.linewidth": 1.8,
            "legend.frameon": False,
            "legend.fontsize": 9,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
        }
    )


def save_figure(
    fig,
    output_base: str | Path,
    formats: Iterable[str] = ("png", "svg", "pdf"),
    dpi: int = 300,
) -> None:
    """保存 PNG/SVG/PDF 三种论文常用格式。"""
    output_base = Path(output_base)
    output_base.parent.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        fig.savefig(f"{output_base}.{fmt}", dpi=dpi, bbox_inches="tight")


def set_axis_labels(ax, xlabel: str, ylabel: str, title: str | None = None) -> None:
    """统一坐标轴标题与标签。"""
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
