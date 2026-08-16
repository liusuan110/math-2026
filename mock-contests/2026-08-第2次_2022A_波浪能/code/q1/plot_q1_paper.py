"""生成问题一可直接用于论文的正式图片。"""

from __future__ import annotations

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

from science_style import apply_science_style, save_figure  # noqa: E402


BLUE = "#0072B2"
VERMILLION = "#D55E00"


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
            "legend.fontsize": 9,
            "lines.linewidth": 1.35,
        }
    )


def style_axis(axis) -> None:
    axis.axhline(0.0, color="#666666", linewidth=0.7, alpha=0.55, zorder=0)
    axis.margins(x=0)


def plot_two_case_response(
    time: np.ndarray,
    constant: np.ndarray,
    power: np.ndarray,
    *,
    state_rows: tuple[int, int],
    ylabel: str,
    output_name: str,
) -> None:
    configure_style((6.9, 5.4))
    figure, axes = plt.subplots(2, 1, sharex=True, figsize=(6.9, 5.4))
    cases = ((constant, "(a) Constant damping"), (power, "(b) Power-law damping"))

    for axis, (states, title) in zip(axes, cases):
        axis.plot(time, states[state_rows[0]], color=BLUE, label="Float")
        axis.plot(
            time,
            states[state_rows[1]],
            color=VERMILLION,
            linestyle="--",
            label="Oscillator",
        )
        axis.set_ylabel(ylabel)
        axis.set_title(title, loc="left", pad=4)
        axis.legend(loc="upper right", ncol=2)
        axis.set_xlim(time[0], time[-1])
        style_axis(axis)

    axes[-1].set_xlabel(r"Time $t$ (s)")
    figure.subplots_adjust(left=0.12, right=0.98, top=0.97, bottom=0.10, hspace=0.24)
    save_figure(figure, CONTEST_DIR / "figures" / "final" / output_name)
    plt.close(figure)


def plot_relative_response(
    time: np.ndarray,
    constant: np.ndarray,
    power: np.ndarray,
    period: float,
) -> None:
    configure_style((6.9, 4.8))
    start_time = time[-1] - 3.0 * period
    mask = time >= start_time
    local_time = time[mask] - time[mask][0]
    relative_displacement_constant = constant[2, mask] - constant[0, mask]
    relative_displacement_power = power[2, mask] - power[0, mask]
    relative_velocity_constant = constant[3, mask] - constant[1, mask]
    relative_velocity_power = power[3, mask] - power[1, mask]

    figure, axes = plt.subplots(2, 1, sharex=True, figsize=(6.9, 4.8))
    series = (
        (
            relative_displacement_constant,
            relative_displacement_power,
            r"Relative displacement $x_o-x_f$ (m)",
            "(a) Relative displacement",
        ),
        (
            relative_velocity_constant,
            relative_velocity_power,
            r"Relative velocity $v_o-v_f$ (m s$^{-1}$)",
            "(b) Relative velocity",
        ),
    )

    for axis, (constant_values, power_values, ylabel, title) in zip(axes, series):
        axis.plot(local_time, constant_values, color=BLUE, label="Constant damping")
        axis.plot(
            local_time,
            power_values,
            color=VERMILLION,
            linestyle="--",
            label="Power-law damping",
        )
        axis.set_ylabel(ylabel)
        axis.set_title(title, loc="left", pad=4)
        style_axis(axis)

    axes[-1].set_xlabel("Time within the final three periods (s)")
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(
        handles,
        labels,
        loc="upper right",
        bbox_to_anchor=(0.98, 0.995),
        ncol=2,
    )
    figure.subplots_adjust(left=0.14, right=0.98, top=0.90, bottom=0.11, hspace=0.30)
    save_figure(
        figure,
        CONTEST_DIR / "figures" / "final" / "q1_relative_response",
    )
    plt.close(figure)


def main() -> None:
    data = np.load(CONTEST_DIR / "results" / "models" / "q1_full_response.npz")
    time = data["time"]
    constant = data["constant"]
    power = data["power"]
    period = 2.0 * np.pi / 1.4005

    plot_two_case_response(
        time,
        constant,
        power,
        state_rows=(0, 2),
        ylabel="Heave displacement (m)",
        output_name="q1_displacement_response",
    )
    plot_two_case_response(
        time,
        constant,
        power,
        state_rows=(1, 3),
        ylabel=r"Heave velocity (m s$^{-1}$)",
        output_name="q1_velocity_response",
    )
    plot_relative_response(time, constant, power, period)


if __name__ == "__main__":
    main()
