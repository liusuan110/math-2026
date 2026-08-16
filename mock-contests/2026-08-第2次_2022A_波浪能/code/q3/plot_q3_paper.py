"""生成问题三三张正式论文图及绘图数据核验指标。"""

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

from common.q3_dynamics import (  # noqa: E402
    FloatShellConvention,
    Q3Parameters,
    diagnostic_time_grid,
    solve_response,
)
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
            "lines.linewidth": 1.25,
        }
    )


def solve_plot_data(models_dir: Path) -> dict[str, np.ndarray | float]:
    params = Q3Parameters()
    time = diagnostic_time_grid(params, step=0.01)
    main_solution = solve_response(
        params,
        (0.0, params.forty_period_end),
        time,
        track_energy=True,
        max_step=0.01,
    )
    alternative_params = Q3Parameters(
        shell_convention=FloatShellConvention.LATERAL_ONLY
    )
    alternative_solution = solve_response(
        alternative_params,
        (0.0, alternative_params.forty_period_end),
        time,
        max_step=0.01,
    )

    frozen = np.load(models_dir / "q3_full_response.npz")
    frozen_time = frozen["time"]
    frozen_states = frozen["states"]
    regular_count = int(np.floor(params.forty_period_end / 0.01 + 1e-12)) + 1
    regular_time = time[:regular_count]
    official_indices = np.rint(frozen_time / 0.01).astype(int)
    if not np.allclose(regular_time[official_indices], frozen_time, rtol=0.0, atol=1e-12):
        raise AssertionError("稠密绘图网格未覆盖官方 0.2 s 输出时刻")
    official_match = float(
        np.max(np.abs(main_solution.y[:8, official_indices].T - frozen_states))
    )
    if official_match > 1e-9:
        raise AssertionError("绘图响应与冻结官方数据不一致")

    state = main_solution.y[:8]
    relative_heave_velocity = state[3] - state[1]
    relative_pitch_velocity = state[7] - state[5]
    linear_power = params.linear_damping * relative_heave_velocity**2
    rotational_power = params.rotational_damping * relative_pitch_velocity**2

    return {
        "time": time,
        "state": state,
        "energy": main_solution.y[8:],
        "alternative_state": alternative_solution.y,
        "linear_power": linear_power,
        "rotational_power": rotational_power,
        "official_match": official_match,
        "period": params.period,
    }


def plot_heave(data: dict[str, np.ndarray | float], output_dir: Path) -> None:
    time = np.asarray(data["time"])
    state = np.asarray(data["state"])
    configure_style((7.0, 5.0))
    figure, axes = plt.subplots(2, 1, sharex=True, figsize=(7.0, 5.0))
    panels = (
        (0, 2, r"Heave displacement (m)", "(a) Heave displacement"),
        (1, 3, r"Heave velocity (m s$^{-1}$)", "(b) Heave velocity"),
    )
    for axis, (float_index, oscillator_index, ylabel, title) in zip(axes, panels):
        axis.plot(time, state[float_index], color=BLUE, label="Float")
        axis.plot(
            time,
            state[oscillator_index],
            color=VERMILLION,
            linestyle="--",
            label="Oscillator",
        )
        axis.set_ylabel(ylabel)
        axis.set_title(title, loc="left", pad=4)
        axis.set_xlim(0.0, float(time[-1]))
        axis.margins(x=0)
    axes[-1].set_xlabel(r"Time $t$ (s)")
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.55, 0.995))
    figure.subplots_adjust(left=0.13, right=0.985, top=0.92, bottom=0.10, hspace=0.28)
    save_figure(figure, output_dir / "q3_heave_response")
    plt.close(figure)


def plot_pitch(data: dict[str, np.ndarray | float], output_dir: Path) -> None:
    time = np.asarray(data["time"])
    state = np.asarray(data["state"])
    configure_style((7.0, 5.0))
    figure, axes = plt.subplots(2, 1, sharex=True, figsize=(7.0, 5.0))
    panels = (
        (4, 6, r"Pitch angle (rad)", "(a) Pitch angle"),
        (5, 7, r"Angular velocity (rad s$^{-1}$)", "(b) Pitch angular velocity"),
    )
    for axis, (float_index, oscillator_index, ylabel, title) in zip(axes, panels):
        axis.plot(time, state[float_index], color=BLUE, label="Float")
        axis.plot(
            time,
            state[oscillator_index],
            color=VERMILLION,
            linestyle="--",
            label="Oscillator",
        )
        axis.set_ylabel(ylabel)
        axis.set_title(title, loc="left", pad=4)
        axis.set_xlim(0.0, float(time[-1]))
        axis.margins(x=0)
    axes[-1].set_xlabel(r"Time $t$ (s)")
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.55, 0.995))
    figure.subplots_adjust(left=0.13, right=0.985, top=0.92, bottom=0.10, hspace=0.28)
    save_figure(figure, output_dir / "q3_pitch_response")
    plt.close(figure)


def plot_pto_and_sensitivity(
    data: dict[str, np.ndarray | float], output_dir: Path
) -> None:
    time = np.asarray(data["time"])
    state = np.asarray(data["state"])
    alternative = np.asarray(data["alternative_state"])
    energy = np.asarray(data["energy"])
    linear_power = np.asarray(data["linear_power"])
    rotational_power = np.asarray(data["rotational_power"])
    configure_style((7.2, 5.8))
    figure, axes = plt.subplots(2, 2, figsize=(7.2, 5.8))
    axes[0, 0].plot(time, linear_power, color=BLUE)
    axes[0, 0].set_ylabel(r"Linear PTO power (W)")
    axes[0, 0].set_title("(a) Linear PTO power", loc="left", pad=4)

    axes[0, 1].plot(time, rotational_power, color=GREEN)
    axes[0, 1].set_ylabel(r"Rotational PTO power (W)")
    axes[0, 1].set_title("(b) Rotational PTO power", loc="left", pad=4)

    axes[1, 0].plot(time, energy[2] / 1000.0, color=VERMILLION)
    axes[1, 0].set_ylabel(r"Cumulative linear PTO energy (kJ)")
    axes[1, 0].set_title("(c) Cumulative linear PTO output", loc="left", pad=4)

    pitch_difference = alternative[4] - state[4]
    peak_index = int(np.argmax(np.abs(pitch_difference)))
    axes[1, 1].plot(time, pitch_difference, color=VERMILLION)
    axes[1, 1].axhline(0.0, color=GRAY, linewidth=0.75)
    axes[1, 1].scatter(
        time[peak_index],
        pitch_difference[peak_index],
        color=BLACK,
        s=20,
        zorder=4,
    )
    axes[1, 1].annotate(
        r"max $|\Delta\theta_f|=0.0616$ rad",
        xy=(time[peak_index], pitch_difference[peak_index]),
        xytext=(78.0, 0.047),
        arrowprops={"arrowstyle": "->", "color": GRAY, "lw": 0.8},
        fontsize=8.5,
    )
    axes[1, 1].set_ylabel(r"Pitch difference $\Delta\theta_f$ (rad)")
    axes[1, 1].set_title("(d) Shell-convention sensitivity", loc="left", pad=4)

    for axis in axes.flat:
        axis.set_xlabel(r"Time $t$ (s)")
        axis.margins(x=0)
    axes[0, 0].set_xlim(0.0, float(time[-1]))
    axes[0, 1].set_xlim(0.0, float(time[-1]))
    axes[1, 0].set_xlim(0.0, float(time[-1]))
    axes[1, 1].set_xlim(0.0, float(time[-1]))
    figure.subplots_adjust(left=0.11, right=0.985, top=0.96, bottom=0.09, wspace=0.29, hspace=0.32)
    save_figure(figure, output_dir / "q3_pto_and_sensitivity")
    plt.close(figure)


def write_plot_metrics(
    data: dict[str, np.ndarray | float], models_dir: Path
) -> None:
    energy = np.asarray(data["energy"])
    metrics = {
        "status": "passed",
        "dense_time_count": int(np.asarray(data["time"]).size),
        "dense_step_s": 0.01,
        "official_frozen_max_absolute_difference": float(data["official_match"]),
        "maximum_instantaneous_linear_pto_power_W": float(
            np.max(np.asarray(data["linear_power"]))
        ),
        "maximum_instantaneous_rotational_pto_power_W": float(
            np.max(np.asarray(data["rotational_power"]))
        ),
        "cumulative_linear_pto_energy_at_40T_J": float(energy[2, -1]),
        "cumulative_rotational_pto_energy_at_40T_J": float(energy[4, -1]),
    }
    with (models_dir / "q3_plot_metrics.json").open("w", encoding="utf-8") as stream:
        json.dump(metrics, stream, ensure_ascii=False, indent=2)


def main() -> None:
    models_dir = CONTEST_DIR / "results" / "models"
    output_dir = CONTEST_DIR / "figures" / "final"
    data = solve_plot_data(models_dir)
    plot_heave(data, output_dir)
    plot_pitch(data, output_dir)
    plot_pto_and_sensitivity(data, output_dir)
    write_plot_metrics(data, models_dir)


if __name__ == "__main__":
    main()
