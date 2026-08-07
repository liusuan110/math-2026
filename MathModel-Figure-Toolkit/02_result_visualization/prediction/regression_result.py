"""模型预测结果图：真实值 vs 预测值。

输出 RMSE、MAE、MAPE，并保存折线对比图。
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".matplotlib-cache"))
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "00_style"))

from science_style import apply_science_style, save_figure, set_axis_labels  # noqa: E402


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """计算数模论文中常用的预测误差指标。"""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    eps = 1e-8
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mae = np.mean(np.abs(y_true - y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / np.maximum(np.abs(y_true), eps))) * 100
    return {"RMSE": rmse, "MAE": mae, "MAPE": mape}


def plot_prediction_result(y_true: np.ndarray, y_pred: np.ndarray, output_base: Path) -> None:
    """绘制真实值和预测值的折线对比图。"""
    apply_science_style()
    metrics = regression_metrics(y_true, y_pred)
    x = np.arange(len(y_true))

    fig, ax = plt.subplots()
    ax.plot(x, y_true, marker="o", markersize=3, label="Observed")
    ax.plot(x, y_pred, marker="s", markersize=3, label="Predicted")
    set_axis_labels(ax, "Sample index", "Target value", "Prediction Result")
    ax.legend()

    metric_text = (
        f"RMSE = {metrics['RMSE']:.3f}\n"
        f"MAE = {metrics['MAE']:.3f}\n"
        f"MAPE = {metrics['MAPE']:.2f}%"
    )
    ax.text(0.02, 0.95, metric_text, transform=ax.transAxes, va="top")

    save_figure(fig, output_base)
    plt.close(fig)
    print(metric_text)


def main() -> None:
    """使用可复现实验数据生成示例图。"""
    rng = np.random.default_rng(2026)
    x = np.linspace(0, 4 * np.pi, 80)
    y_true = 20 + 0.8 * x + 3 * np.sin(x)
    y_pred = y_true + rng.normal(0, 1.2, size=x.size)
    output_base = Path(__file__).with_name("output") / "regression_result"
    plot_prediction_result(y_true, y_pred, output_base)


if __name__ == "__main__":
    main()
