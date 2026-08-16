"""生成问题一数值结果的诊断图，不作为论文正式图片。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
CONTEST_DIR = CODE_DIR.parent
MPL_CONFIG_DIR = CONTEST_DIR / "results" / "models" / ".matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q1_dynamics import DampingLaw, Q1Parameters, damping_force  # noqa: E402


def main() -> None:
    data_path = CONTEST_DIR / "results" / "models" / "q1_full_response.npz"
    output_dir = CONTEST_DIR / "figures" / "q1" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)

    data = np.load(data_path)
    time = data["time"]
    constant = data["constant"]
    power = data["power"]
    params = Q1Parameters()

    relative_displacement_constant = constant[2] - constant[0]
    relative_displacement_power = power[2] - power[0]
    relative_velocity_constant = constant[3] - constant[1]
    relative_velocity_power = power[3] - power[1]
    pto_power_constant = (
        damping_force(relative_velocity_constant, DampingLaw.CONSTANT, params)
        * relative_velocity_constant
    )
    pto_power_power = (
        damping_force(relative_velocity_power, DampingLaw.POWER, params)
        * relative_velocity_power
    )

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    figure, axes = plt.subplots(2, 2, figsize=(12, 7.2), constrained_layout=True)

    axes[0, 0].plot(time, constant[0], label="Float", linewidth=1.0)
    axes[0, 0].plot(time, constant[2], label="Oscillator", linewidth=1.0)
    axes[0, 0].set_title("Constant damping: displacement")
    axes[0, 0].set_ylabel("Displacement (m)")
    axes[0, 0].legend(frameon=False, ncol=2)

    axes[0, 1].plot(time, power[0], label="Float", linewidth=1.0)
    axes[0, 1].plot(time, power[2], label="Oscillator", linewidth=1.0)
    axes[0, 1].set_title("Power-law damping: displacement")
    axes[0, 1].set_ylabel("Displacement (m)")
    axes[0, 1].legend(frameon=False, ncol=2)

    axes[1, 0].plot(
        time,
        relative_displacement_constant,
        label="Constant damping",
        linewidth=1.0,
    )
    axes[1, 0].plot(
        time,
        relative_displacement_power,
        label="Power-law damping",
        linewidth=1.0,
    )
    axes[1, 0].set_title("Relative displacement")
    axes[1, 0].set_xlabel("Time (s)")
    axes[1, 0].set_ylabel("$x_o-x_f$ (m)")
    axes[1, 0].legend(frameon=False)

    axes[1, 1].plot(
        time,
        pto_power_constant,
        label="Constant damping",
        linewidth=0.9,
    )
    axes[1, 1].plot(
        time,
        pto_power_power,
        label="Power-law damping",
        linewidth=0.9,
    )
    axes[1, 1].set_title("Instantaneous PTO dissipation")
    axes[1, 1].set_xlabel("Time (s)")
    axes[1, 1].set_ylabel("Power (W)")
    axes[1, 1].legend(frameon=False)

    for axis in axes.flat:
        axis.set_xlim(time[0], time[-1])

    output_path = output_dir / "q1_full_response_diagnostic.png"
    figure.savefig(output_path, dpi=180, facecolor="white")
    plt.close(figure)
    print(output_path)


if __name__ == "__main__":
    main()
