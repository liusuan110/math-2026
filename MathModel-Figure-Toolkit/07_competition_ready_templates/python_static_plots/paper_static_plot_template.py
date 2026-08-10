"""赛时 Python 论文静态图模板。

用途：
    - 统一 matplotlib 风格
    - 示例生成：真实值-预测值对比、敏感性曲线、优化收敛曲线、热力图
    - 同时导出 PNG / SVG / PDF

运行：
    python paper_static_plot_template.py

比赛时建议：
    1. 把示例数据替换为模型输出的 csv/xlsx/json。
    2. 不在画图脚本里重写核心模型逻辑。
    3. 图名使用 q1/q2/q3 + 结论命名。
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np


OUTPUT_DIR = Path(__file__).resolve().parent / "output"
CACHE_DIR = Path(__file__).resolve().parent / ".mplconfig"
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402


def setup_paper_style(width: float = 6.4, height: float = 3.8) -> None:
    """设置论文图风格。

    若安装了 SciencePlots，会优先使用；否则回退到稳定的 matplotlib 参数。
    """
    try:
        import scienceplots  # noqa: F401

        plt.style.use(["science", "ieee", "no-latex"])
    except Exception:
        plt.style.use("default")

    plt.rcParams.update(
        {
            "figure.figsize": (width, height),
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "font.family": "Times New Roman",
            "font.sans-serif": [
                "PingFang SC",
                "Songti SC",
                "Microsoft YaHei",
                "SimHei",
                "Noto Sans CJK SC",
                "Arial Unicode MS",
            ],
            "axes.unicode_minus": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.9,
            "lines.linewidth": 1.8,
            "legend.frameon": False,
            "legend.fontsize": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
        }
    )


def save_all(fig: plt.Figure, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUTPUT_DIR / f"{name}.{ext}")


def plot_prediction_comparison() -> None:
    x = np.arange(1, 31)
    y_true = 0.35 * x + 1.5 * np.sin(x / 4)
    y_pred = y_true + 0.35 * np.cos(x / 3)

    fig, ax = plt.subplots()
    ax.plot(x, y_true, "o-", label="Observed", color="#2E6F9E")
    ax.plot(x, y_pred, "s--", label="Predicted", color="#C0392B")
    ax.set_xlabel("Sample index")
    ax.set_ylabel("Response value")
    ax.set_title("Observed vs. predicted response")
    ax.legend(loc="best")
    save_all(fig, "q1_prediction_comparison")
    plt.close(fig)


def plot_sensitivity_curve() -> None:
    radius = np.linspace(6, 16, 60)
    score = 1.0 - np.exp(-0.22 * (radius - 5)) + 0.015 * np.sin(radius * 2)

    fig, ax = plt.subplots()
    ax.plot(radius, score, color="#2E6F9E")
    ax.axvline(10, color="#D68910", linestyle=":", linewidth=1.2, label="Baseline")
    ax.set_xlabel("Effective radius / m")
    ax.set_ylabel("Objective value")
    ax.set_title("Sensitivity of objective to effective radius")
    ax.legend(loc="lower right")
    save_all(fig, "q2_radius_sensitivity")
    plt.close(fig)


def plot_optimization_convergence() -> None:
    iteration = np.arange(80)
    best = 7.5 * (1 - np.exp(-iteration / 16)) + 0.08 * np.random.default_rng(7).normal(size=80)
    best = np.maximum.accumulate(best)

    fig, ax = plt.subplots()
    ax.plot(iteration, best, color="#2E6F9E")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Best objective")
    ax.set_title("Optimization convergence")
    save_all(fig, "q3_optimization_convergence")
    plt.close(fig)


def plot_heatmap() -> None:
    x = np.linspace(-3, 3, 80)
    y = np.linspace(-2, 2, 60)
    xx, yy = np.meshgrid(x, y)
    z = np.exp(-0.4 * (xx**2 + 1.5 * yy**2)) * np.cos(1.2 * xx)

    fig, ax = plt.subplots()
    im = ax.imshow(
        z,
        origin="lower",
        aspect="auto",
        cmap="RdBu_r",
        extent=[x.min(), x.max(), y.min(), y.max()],
    )
    cb = fig.colorbar(im, ax=ax)
    cb.set_label("Response")
    ax.set_xlabel("Parameter A")
    ax.set_ylabel("Parameter B")
    ax.set_title("Response surface / feasibility heatmap")
    save_all(fig, "q4_response_heatmap")
    plt.close(fig)


def main() -> None:
    setup_paper_style()
    plot_prediction_comparison()
    plot_sensitivity_curve()
    plot_optimization_convergence()
    plot_heatmap()
    print(f"Saved figures to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
