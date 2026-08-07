"""时间序列预测结果图模板。"""

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

from science_style import apply_science_style, save_figure, set_axis_labels  # noqa: E402


def plot_forecast(history: pd.Series, forecast: pd.Series, output_base: Path) -> None:
    """绘制历史序列和未来预测序列。"""
    apply_science_style()
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    ax.plot(history.index, history.values, label="Historical", color="#1f77b4")
    ax.plot(forecast.index, forecast.values, label="Forecast", color="#d62728")
    ax.axvline(history.index[-1], color="#7f7f7f", linestyle="--", linewidth=1.0)
    set_axis_labels(ax, "Date", "Value", "Time Series Forecast")
    ax.legend()
    fig.autofmt_xdate()
    save_figure(fig, output_base)
    plt.close(fig)


def main() -> None:
    """构造带趋势和季节项的示例时间序列。"""
    dates = pd.date_range("2026-01-01", periods=72, freq="D")
    future_dates = pd.date_range(dates[-1] + pd.Timedelta(days=1), periods=14, freq="D")
    rng = np.random.default_rng(2026)
    t = np.arange(len(dates))
    history = pd.Series(100 + 0.4 * t + 8 * np.sin(t / 5) + rng.normal(0, 2, len(t)), index=dates)
    tf = np.arange(len(dates), len(dates) + len(future_dates))
    forecast = pd.Series(100 + 0.4 * tf + 8 * np.sin(tf / 5), index=future_dates)
    plot_forecast(history, forecast, Path(__file__).with_name("output") / "forecasting_result")


if __name__ == "__main__":
    main()
