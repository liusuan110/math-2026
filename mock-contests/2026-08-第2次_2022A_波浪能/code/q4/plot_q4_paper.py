"""生成问题四三张正式论文图。"""

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

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402

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


def plot_power_curves(models_dir: Path, output_dir: Path) -> None:
    scan = np.load(models_dir / "q4_power_curves.npz")
    report = load_json(models_dir / "q4_optimization.json")
    final = report["final_result"]
    damping = scan["damping"] / 1000.0

    configure_style((7.2, 3.25))
    figure, axes = plt.subplots(1, 2, figsize=(7.2, 3.25))
    panels = (
        (
            scan["heave_power"],
            final["linear_damping_N_s_per_m"] / 1000.0,
            final["heave_mean_power_W"],
            BLUE,
            r"Linear damping $c_z$ (kN s m$^{-1}$)",
            r"Mean heave PTO power (W)",
            "(a) Linear PTO damping",
        ),
        (
            scan["pitch_power"],
            final["rotational_damping_N_m_s"] / 1000.0,
            final["pitch_mean_power_W"],
            GREEN,
            r"Rotational damping $c_\theta$ (kN m s)",
            r"Mean rotational PTO power (W)",
            "(b) Rotational PTO damping",
        ),
    )
    for axis, (power, optimum, maximum, color, xlabel, ylabel, title) in zip(axes, panels):
        axis.plot(damping, power, color=color)
        axis.scatter(
            optimum,
            maximum,
            marker="*",
            s=70,
            color=VERMILLION,
            edgecolor=BLACK,
            linewidth=0.45,
            zorder=5,
            label="Constrained optimum",
        )
        axis.set_xlabel(xlabel)
        axis.set_ylabel(ylabel)
        axis.set_title(title, loc="left", pad=4)
        axis.set_xlim(0.0, 102.5)
        axis.margins(x=0)
        axis.legend(loc="lower right")
    axes[0].annotate(
        r"$c_z^*=59.153$ kN s m$^{-1}$" + "\n" + r"$\bar P_z=318.336$ W",
        xy=(final["linear_damping_N_s_per_m"] / 1000.0, final["heave_mean_power_W"]),
        xytext=(67.0, 226.0),
        arrowprops={"arrowstyle": "->", "color": GRAY, "lw": 0.8},
        fontsize=8.5,
    )
    axes[1].annotate(
        r"$c_\theta^*=100$ kN m s" + "\n" + r"$\bar P_\theta=0.3428$ W",
        xy=(100.0, final["pitch_mean_power_W"]),
        xytext=(51.0, 0.245),
        arrowprops={"arrowstyle": "->", "color": GRAY, "lw": 0.8},
        fontsize=8.5,
    )
    figure.subplots_adjust(left=0.10, right=0.99, top=0.94, bottom=0.17, wspace=0.29)
    save_figure(figure, output_dir / "q4_optimization_curves")
    plt.close(figure)


def plot_power_surface(models_dir: Path, output_dir: Path) -> None:
    surface = np.load(models_dir / "q4_power_surface.npz")
    report = load_json(models_dir / "q4_optimization.json")
    final = report["final_result"]
    linear = surface["linear_damping"] / 1000.0
    rotational = surface["rotational_damping"] / 1000.0
    linear_mesh, rotational_mesh = np.meshgrid(linear, rotational)
    total_power = surface["total_power"]

    configure_style((6.9, 4.65))
    figure, axis = plt.subplots(figsize=(6.9, 4.65))
    maximum = float(final["maximum_total_mean_power_W"])
    power_deficit = np.maximum(maximum - total_power, 1e-4)
    levels = np.array([1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0, 400.0])
    filled = axis.contourf(
        linear_mesh,
        rotational_mesh,
        power_deficit,
        levels=levels,
        norm=LogNorm(vmin=levels[0], vmax=levels[-1]),
        cmap="cividis_r",
        extend="max",
    )
    axis.axvline(
        final["linear_damping_N_s_per_m"] / 1000.0,
        color=BLACK,
        linestyle="--",
        linewidth=0.75,
        alpha=0.65,
    )
    axis.scatter(
        final["linear_damping_N_s_per_m"] / 1000.0,
        final["rotational_damping_N_m_s"] / 1000.0,
        marker="*",
        s=90,
        color=VERMILLION,
        edgecolor=BLACK,
        linewidth=0.55,
        zorder=6,
    )
    axis.annotate(
        r"Global optimum: $(c_z^*,c_\theta^*)=(59.153,100)$",
        xy=(final["linear_damping_N_s_per_m"] / 1000.0, 100.0),
        xytext=(28.0, 82.0),
        arrowprops={"arrowstyle": "->", "color": BLACK, "lw": 0.8},
        fontsize=8.5,
    )
    axis.set_xlabel(r"Linear damping $c_z$ (kN s m$^{-1}$)")
    axis.set_ylabel(r"Rotational damping $c_\theta$ (kN m s)")
    axis.set_xlim(0.0, 102.0)
    axis.set_ylim(0.0, 103.0)
    axis.set_title("Power deficit from the constrained global optimum", loc="left", pad=5)
    colorbar = figure.colorbar(filled, ax=axis, pad=0.025, fraction=0.05)
    colorbar.set_label(r"Power deficit $\bar P_{\max}-\bar P$ (W)")
    figure.subplots_adjust(left=0.11, right=0.90, top=0.92, bottom=0.12)
    save_figure(figure, output_dir / "q4_total_power_surface")
    plt.close(figure)


def plot_optimal_period(models_dir: Path, output_dir: Path) -> None:
    data = np.load(models_dir / "q4_optimal_period.npz")
    report = load_json(models_dir / "q4_optimization.json")
    period = float(report["wave_period_s"])
    time = data["time"] / period
    states = data["states"]
    powers = data["powers"]
    relative_heave = states[:, 2] - states[:, 0]
    relative_pitch = states[:, 6] - states[:, 4]

    configure_style((7.2, 5.7))
    figure, axes = plt.subplots(2, 2, sharex=True, figsize=(7.2, 5.7))
    series = (
        (relative_heave, BLUE, r"Relative heave displacement (m)", "(a) Relative heave displacement"),
        (relative_pitch, GREEN, r"Relative pitch angle (rad)", "(b) Relative pitch angle"),
        (powers[:, 2], VERMILLION, r"Linear PTO power (W)", "(c) Linear PTO power"),
        (powers[:, 4], BLACK, r"Rotational PTO power (W)", "(d) Rotational PTO power"),
    )
    for axis, (values, color, ylabel, title) in zip(axes.flat, series):
        axis.plot(time, values, color=color)
        axis.set_ylabel(ylabel)
        axis.set_title(title, loc="left", pad=4)
        axis.set_xlim(0.0, 1.0)
        axis.margins(x=0)
    axes[1, 0].set_xlabel(r"Normalized time $t/T$")
    axes[1, 1].set_xlabel(r"Normalized time $t/T$")
    figure.subplots_adjust(left=0.12, right=0.985, top=0.96, bottom=0.10, wspace=0.30, hspace=0.31)
    save_figure(figure, output_dir / "q4_optimal_period_response")
    plt.close(figure)


def main() -> None:
    models_dir = CONTEST_DIR / "results" / "models"
    output_dir = CONTEST_DIR / "figures" / "final"
    plot_power_curves(models_dir, output_dir)
    plot_power_surface(models_dir, output_dir)
    plot_optimal_period(models_dir, output_dir)


if __name__ == "__main__":
    main()
