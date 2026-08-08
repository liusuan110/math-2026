import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_moons, make_circles
# 1. 导入 KMeans, DBSCAN, 和新增的 HDBSCAN
from sklearn.cluster import KMeans, SpectralClustering, DBSCAN, HDBSCAN
from sklearn.preprocessing import StandardScaler

import matplotlib.font_manager as fm
from cycler import cycler

font_path = '../../utils/fonts/SourceHanSerifCN-Regular.otf'
fm.fontManager.addfont(font_path)
font_name = fm.FontProperties(fname=font_path).get_name()
plt.rcParams['font.sans-serif'] = [font_name]

plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 200  # 稍微调低 DPI 以便在普通屏幕上更快显示
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.prop_cycle'] = cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
plt.rcParams['axes.unicode_minus'] = False


def generate_data(name, n_samples=200, random_state=42):
    if name == 'moons':
        return make_moons(n_samples=n_samples, noise=0.05, random_state=random_state)
    elif name == 'circles':
        return make_circles(n_samples=n_samples, factor=0.5, noise=0.05, random_state=random_state)


def get_algorithm(name):
    if name == 'kmeans':
        return KMeans(n_clusters=2, random_state=42, n_init='auto')
    elif name == 'spectral':
        return SpectralClustering(n_clusters=2, affinity='nearest_neighbors', random_state=42)
    elif name == 'dbscan':
        return DBSCAN(eps=0.3)
    elif name == 'hdbscan':
        # min_cluster_size 是 HDBSCAN 最重要的参数，定义了簇的最小规模
        return HDBSCAN(min_cluster_size=10, min_samples=5)


def perform_clustering(algorithm, data):
    X, y = data
    X_scaled = StandardScaler().fit_transform(X)

    algorithm.fit(X_scaled)
    if hasattr(algorithm, 'labels_'):
        y_pred = algorithm.labels_.astype(int)
    else:
        y_pred = algorithm.predict(X_scaled)

    return X_scaled, y_pred


def plot_cluster_result(data, labels, title):
    """它会为每个集群和异常点分别进行绘制，以便生成图例"""
    plt.figure(figsize=(7, 6))
    ax = plt.gca()

    unique_labels = sorted(list(set(labels)))
    base_colors = ['#377eb8', '#ff7f00', '#4daf4a', '#f781bf', '#a65628']

    for k in unique_labels:
        class_member_mask = (labels == k)
        xy = data[class_member_mask]

        if k == -1:
            color = '#808080'
            marker = 'x'
            size = 30
            label = '异常点'
        else:
            color = base_colors[k % len(base_colors)]
            marker = 'o'
            size = 20
            label = f'集群 {k}'

        ax.scatter(xy[:, 0], xy[:, 1], s=size, c=color, marker=marker, label=label, alpha=0.9)

    ax.set_title(title, size=16)
    ax.set_xticks(())
    ax.set_yticks(())
    ax.legend(loc='best')
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    moons_data = generate_data('moons')
    hdbscan_algorithm = get_algorithm('hdbscan')  # 获取 HDBSCAN 实例
    X_scaled_moons, y_pred_moons = perform_clustering(hdbscan_algorithm, moons_data)
    plot_cluster_result(
        X_scaled_moons,
        y_pred_moons,
        title="数据集: Moons | 算法: HDBSCAN"
    )

    circles_data = generate_data('circles')
    hdbscan_algorithm = get_algorithm('hdbscan')  # 获取 HDBSCAN 实例
    X_scaled_circles, y_pred_circles = perform_clustering(hdbscan_algorithm, circles_data)
    plot_cluster_result(
        X_scaled_circles,
        y_pred_circles,
        title="数据集: Circles | 算法: HDBSCAN"
    )
