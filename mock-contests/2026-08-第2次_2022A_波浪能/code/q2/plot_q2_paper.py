"""生成问题二可直接用于论文的三张正式图片。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
CONTEST_DIR = CODE_DIR.parent
REPO_DIR = CONTEST_DIR.parents[1]
STYLE_DIR = REPO_DIR / "MathModel-Figure-Toolkit" / "00_style"
MPL_CONFIG_DIR = CONTEST_DIR / "results" / "models" / ".matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

if str(STYLE_DIR) not in sys.path:
    sys.path.insert(0, str(STYLE_DIR))
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from common.q2_power import constant_mean_power, q2_parameters  # noqa: E402
from science_style import apply_science_style, save_figure  # noqa: E402


BLUE = "#0072B2"
VERMILLION = "#D55E00"
GREEN = "#009E73"
BLACK = "#222222"
GRAY = "#666666"


def configure_style(figsize: tuple[float, float]) -> None:
    apply_science_style(figsize=figsize)
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "mathtext.fontset": "stix",
            "axes.titlesize": 10.5,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8.5,
            "lines.linewidth": 1.4,
        }
    )


def load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def plot_optimization_curves(models_dir: Path, output_dir: Path) -> None:
    constant_scan = np.load(models_dir / "q2_constant_power_scan.npz")
    boundary_scan = np.load(models_dir / "q2_nonlinear_boundary_scan.npz")
    constant_report = load_json(models_dir / "q2_constant_optimization.json")
    nonlinear_report = load_json(models_dir / "q2_nonlinear_final_validation.json")

    constant_optimum = constant_report["bounded_optimizer"]
    nonlinear_optimum = nonlinear_report["final_result"]

    configure_style((7.2, 3.25))
    figure, axes = plt.subplots(1, 2, figsize=(7.2, 3.25))

    axes[0].plot(
        constant_scan["damping"] / 1000.0,
        constant_scan["mean_power"],
        color=BLUE,
    )
    axes[0].scatter(
        constant_optimum["damping_N_s_per_m"] / 1000.0,
        constant_optimum["mean_power_W"],
        marker="*",
        s=65,
        color=VERMILLION,
        edgecolor=BLACK,
        linewidth=0.45,
        zorder=5,
        label="Optimum",
    )
    axes[0].annotate(
        r"$c^*=37.194$ kN s m$^{-1}$" + "\n" + r"$\bar P=229.334$ W",
        xy=(
            constant_optimum["damping_N_s_per_m"] / 1000.0,
            constant_optimum["mean_power_W"],
        ),
        xytext=(52, 168),
        textcoords="data",
        arrowprops={"arrowstyle": "->", "color": GRAY, "lw": 0.8},
        fontsize=8.5,
    )
    axes[0].set_xlabel(r"Constant damping $c$ (kN s m$^{-1}$)")
    axes[0].set_ylabel(r"Mean power $\bar P$ (W)")
    axes[0].set_title("(a) Constant-damping optimization", loc="left", pad=4)
    axes[0].set_xlim(0.0, 100.0)
    axes[0].set_ylim(0.0, 245.0)

    axes[1].plot(
        boundary_scan["exponent"],
        boundary_scan["mean_power"],
        color=GREEN,
    )
    axes[1].scatter(
        nonlinear_optimum["exponent"],
        nonlinear_optimum["mean_power_W"],
        marker="*",
        s=65,
        color=VERMILLION,
        edgecolor=BLACK,
        linewidth=0.45,
        zorder=5,
        label="Optimum",
    )
    axes[1].annotate(
        r"$p^*=0.41572$" + "\n" + r"$\bar P=229.994$ W",
        xy=(nonlinear_optimum["exponent"], nonlinear_optimum["mean_power_W"]),
        xytext=(0.57, 166),
        textcoords="data",
        arrowprops={"arrowstyle": "->", "color": GRAY, "lw": 0.8},
        fontsize=8.5,
    )
    axes[1].set_xlabel(r"Power exponent $p$ at $a=100$ kN")
    axes[1].set_ylabel(r"Mean power $\bar P$ (W)")
    axes[1].set_title("(b) Upper-bound exponent optimization", loc="left", pad=4)
    axes[1].set_xlim(0.0, 1.0)
    axes[1].set_ylim(0.0, 245.0)

    for axis in axes:
        axis.legend(loc="lower center")
        axis.margins(x=0)

    figure.subplots_adjust(left=0.09, right=0.99, top=0.94, bottom=0.17, wspace=0.27)
    save_figure(figure, output_dir / "q2_optimization_curves")
    plt.close(figure)


def plot_power_surface(models_dir: Path, output_dir: Path) -> None:
    coarse = np.load(models_dir / "q2_nonlinear_coarse_grid.npz")
    ridge = np.load(models_dir / "q2_nonlinear_ridge_trace.npz")
    final_report = load_json(models_dir / "q2_nonlinear_final_validation.json")
    final = final_report["final_result"]

    coefficient = coarse["coefficient"] / 1000.0
    exponent = coarse["exponent"]
    coefficient_mesh, exponent_mesh = np.meshgrid(coefficient, exponent)
    mean_power = coarse["mean_power"]

    configure_style((6.9, 4.55))
    figure, axis = plt.subplots(figsize=(6.9, 4.55))
    levels = np.linspace(0.0, 230.0, 24)
    filled = axis.contourf(
        coefficient_mesh,
        exponent_mesh,
        mean_power,
        levels=levels,
        cmap="cividis",
        extend="max",
    )
    contour = axis.contour(
        coefficient_mesh,
        exponent_mesh,
        mean_power,
        levels=[180.0, 210.0, 225.0, 229.0],
        colors=BLACK,
        linewidths=0.55,
        alpha=0.72,
    )
    axis.clabel(contour, fmt="%.0f W", fontsize=7.5, inline_spacing=3)
    axis.scatter(
        coefficient_mesh,
        exponent_mesh,
        s=5,
        color=BLACK,
        alpha=0.25,
        linewidth=0,
        label="Coarse grid",
    )
    axis.plot(
        ridge["coefficient"] / 1000.0,
        ridge["exponent"],
        color=VERMILLION,
        linestyle="--",
        linewidth=1.5,
        label="Optimized ridge",
    )
    axis.scatter(
        final["coefficient"] / 1000.0,
        final["exponent"],
        marker="*",
        s=85,
        color=VERMILLION,
        edgecolor=BLACK,
        linewidth=0.55,
        zorder=6,
        label="Final optimum",
    )
    axis.annotate(
        r"$(a^*,p^*)=(100$ kN$,,0.41572)$",
        xy=(final["coefficient"] / 1000.0, final["exponent"]),
        xytext=(58, 0.58),
        arrowprops={"arrowstyle": "->", "color": BLACK, "lw": 0.8},
        fontsize=8.5,
    )
    axis.set_xlabel(r"Power-law coefficient $a$ (kN)")
    axis.set_ylabel(r"Power exponent $p$")
    axis.set_xlim(0.0, 102.5)
    axis.set_ylim(0.0, 1.0)
    axis.set_title("Mean PTO power over the power-law parameter domain", loc="left", pad=5)
    axis.legend(loc="upper left", ncol=3)
    colorbar = figure.colorbar(filled, ax=axis, pad=0.025, fraction=0.05)
    colorbar.set_label(r"Mean power $\bar P$ (W)")
    figure.subplots_adjust(left=0.10, right=0.91, top=0.92, bottom=0.12)
    save_figure(figure, output_dir / "q2_nonlinear_power_surface")
    plt.close(figure)


def plot_optimal_period_comparison(models_dir: Path, output_dir: Path) -> None:
    constant_report = load_json(models_dir / "q2_constant_optimization.json")
    nonlinear_report = load_json(models_dir / "q2_nonlinear_final_validation.json")
    nonlinear_data = np.load(models_dir / "q2_nonlinear_final_period.npz")
    params = q2_parameters()

    constant_optimum = constant_report["bounded_optimizer"]
    nonlinear_optimum = nonlinear_report["final_result"]
    constant_damping = float(constant_optimum["damping_N_s_per_m"])
    phasor = constant_mean_power(constant_damping, params).displacement_phasor

    time = nonlinear_data["time"]
    normalized_time = time / params.period
    phase = np.exp(1j * params.wave_omega * time)
    constant_displacement = np.vstack(
        [np.real(phasor[0] * phase), np.real(phasor[1] * phase)]
    )
    constant_velocity = np.vstack(
        [
            np.real(1j * params.wave_omega * phasor[0] * phase),
            np.real(1j * params.wave_omega * phasor[1] * phase),
        ]
    )
    constant_relative_displacement = (
        constant_displacement[1] - constant_displacement[0]
    )
    constant_relative_velocity = constant_velocity[1] - constant_velocity[0]
    constant_power = constant_damping * constant_relative_velocity**2

    nonlinear_relative_displacement = nonlinear_data["relative_displacement"]
    nonlinear_relative_velocity = nonlinear_data["relative_velocity"]
    nonlinear_power = nonlinear_data["instantaneous_power"]

    configure_style((6.9, 6.15))
    figure, axes = plt.subplots(3, 1, sharex=True, figsize=(6.9, 6.15))
    panels = (
        (
            constant_relative_displacement,
            nonlinear_relative_displacement,
            r"Relative displacement (m)",
            "(a) Relative displacement",
        ),
        (
            constant_relative_velocity,
            nonlinear_relative_velocity,
            r"Relative velocity (m s$^{-1}$)",
            "(b) Relative velocity",
        ),
        (
            constant_power,
            nonlinear_power,
            r"Instantaneous PTO power (W)",
            "(c) Instantaneous PTO power",
        ),
    )

    for axis, (constant_values, nonlinear_values, ylabel, title) in zip(axes, panels):
        axis.plot(
            normalized_time,
            constant_values,
            color=BLUE,
            label="Optimal constant damping",
        )
        axis.plot(
            normalized_time,
            nonlinear_values,
            color=VERMILLION,
            linestyle="--",
            label="Optimal power-law damping",
        )
        axis.set_ylabel(ylabel)
        axis.set_title(title, loc="left", pad=4)
        axis.set_xlim(0.0, 1.0)
        axis.margins(x=0)

    axes[-1].set_xlabel(r"Normalized time $t/T$")
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.56, 0.995),
        ncol=2,
    )
    figure.subplots_adjust(left=0.13, right=0.985, top=0.93, bottom=0.08, hspace=0.28)
    save_figure(figure, output_dir / "q2_optimal_period_comparison")
    plt.close(figure)


def main() -> None:
    models_dir = CONTEST_DIR / "results" / "models"
    output_dir = CONTEST_DIR / "figures" / "final"
    plot_optimization_curves(models_dir, output_dir)
    plot_power_surface(models_dir, output_dir)
    plot_optimal_period_comparison(models_dir, output_dir)


if __name__ == "__main__":
    main()
