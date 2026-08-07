"""多模型指标比较柱状图模板。"""

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

from colors import MODEL_COLORS  # noqa: E402
from science_style import apply_science_style, save_figure, set_axis_labels  # noqa: E402


def plot_model_comparison(metrics: pd.DataFrame, output_base: Path) -> None:
    """绘制模型评价指标柱状比较图。

    metrics 的 index 为模型名，columns 为指标名。
    """
    apply_science_style(figsize=(6.8, 3.8))
    fig, ax = plt.subplots()
    metrics.plot(kind="bar", ax=ax, color=MODEL_COLORS[: len(metrics.columns)], width=0.75)
    set_axis_labels(ax, "Model", "Score", "Model Comparison")
    ax.legend(title="Metric", ncol=len(metrics.columns))
    ax.set_xticklabels(metrics.index, rotation=0)
    save_figure(fig, output_base)
    plt.close(fig)


def main() -> None:
    """使用常见数模模型名称生成示例比较图。"""
    metrics = pd.DataFrame(
        {
            "RMSE": [8.2, 5.9, 4.7, 4.3],
            "MAE": [6.1, 4.6, 3.8, 3.5],
        },
        index=["LR", "RandomForest", "XGBoost", "LSTM"],
    )
    plot_model_comparison(metrics, Path(__file__).with_name("output") / "model_comparison")


if __name__ == "__main__":
    main()
