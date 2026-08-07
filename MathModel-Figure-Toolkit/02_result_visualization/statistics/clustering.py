"""KMeans 与 DBSCAN 聚类结果可视化模板。"""

from __future__ import annotations

import sys
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".matplotlib-cache"))
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN, KMeans
from sklearn.datasets import make_blobs
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "00_style"))

from science_style import apply_science_style, save_figure  # noqa: E402


def plot_clustering(X, labels_kmeans, labels_dbscan, output_base: Path) -> None:
    """并排绘制 KMeans 与 DBSCAN 聚类结果。"""
    apply_science_style(figsize=(7.2, 3.4))
    fig, axes = plt.subplots(1, 2, sharex=True, sharey=True)
    configs = [("KMeans", labels_kmeans), ("DBSCAN", labels_dbscan)]
    for ax, (title, labels) in zip(axes, configs):
        ax.scatter(X[:, 0], X[:, 1], c=labels, cmap="tab10", s=24, edgecolor="k", linewidth=0.2)
        ax.set_title(title)
        ax.set_xlabel("Feature 1")
        ax.set_ylabel("Feature 2")
    save_figure(fig, output_base)
    plt.close(fig)


def main() -> None:
    """示例：二维样本聚类。"""
    X, _ = make_blobs(n_samples=220, centers=4, cluster_std=0.75, random_state=2026)
    X = StandardScaler().fit_transform(X)
    labels_kmeans = KMeans(n_clusters=4, n_init=10, random_state=2026).fit_predict(X)
    labels_dbscan = DBSCAN(eps=0.35, min_samples=5).fit_predict(X)
    plot_clustering(X, labels_kmeans, labels_dbscan, Path(__file__).with_name("output") / "clustering")


if __name__ == "__main__":
    main()
