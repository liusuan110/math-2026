"""PCA 二维降维可视化模板。"""

from __future__ import annotations

import sys
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".matplotlib-cache"))
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "00_style"))

from science_style import apply_science_style, save_figure, set_axis_labels  # noqa: E402


def plot_pca_projection(X, y, output_base: Path) -> None:
    """标准化后进行 PCA，并绘制二维投影。"""
    X_scaled = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2)
    Z = pca.fit_transform(X_scaled)
    ratio = pca.explained_variance_ratio_

    apply_science_style(figsize=(5.6, 4.2))
    fig, ax = plt.subplots()
    scatter = ax.scatter(Z[:, 0], Z[:, 1], c=y, cmap="tab10", s=28, edgecolor="k", linewidth=0.2)
    set_axis_labels(
        ax,
        f"PC1 ({ratio[0] * 100:.1f}%)",
        f"PC2 ({ratio[1] * 100:.1f}%)",
        "PCA Projection",
    )
    ax.legend(*scatter.legend_elements(), title="Class", loc="best")
    save_figure(fig, output_base)
    plt.close(fig)


def main() -> None:
    """示例：分类数据的 PCA 可视化。"""
    X, y = make_classification(
        n_samples=160,
        n_features=8,
        n_informative=5,
        n_classes=3,
        random_state=2026,
    )
    plot_pca_projection(X, y, Path(__file__).with_name("output") / "PCA_visualization")


if __name__ == "__main__":
    main()
