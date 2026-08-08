import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_moons, make_circles
from sklearn.cluster import KMeans, SpectralClustering, DBSCAN
from sklearn.preprocessing import StandardScaler

# -- 图片预设，需要 plt, fm, cycler 库
import matplotlib.font_manager as fm
from cycler import cycler
import os

font_path = "../../utils/fonts/SourceHanSerifCN-Regular.otf"
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rcParams['font.sans-serif'] = [font_name]
else:
    fallback_fonts = ['STZhongsong', 'SimSun', 'SimHei', 'Microsoft YaHei']
    plt.rcParams['font.sans-serif'] = fallback_fonts

plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'  # 保存后自动裁剪白边
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.prop_cycle'] = cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
plt.rcParams['axes.unicode_minus'] = False
# -- 图片预设


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
            color = '#808080'  # 使用灰色
            marker = 'x'  # 使用 'x' 标记
            size = 30  # 标记稍大一些
            label = '异常点'
        else:
            color = base_colors[k % len(base_colors)]
            marker = 'o'  # 使用圆形标记
            size = 20
            label = f'集群 {k}'

        ax.scatter(xy[:, 0], xy[:, 1], s=size, c=color, marker=marker, label=label, alpha=0.9)

    ax.set_title(title, size=16)
    ax.set_xticks(())
    ax.set_yticks(())
    ax.legend(loc='best')  # 添加图例到最佳位置
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    moons_data = generate_data('moons')
    dbscan_algorithm = get_algorithm('dbscan')
    X_scaled_moons, y_pred_moons = perform_clustering(dbscan_algorithm, moons_data)
    plot_cluster_result(
        X_scaled_moons,
        y_pred_moons,
        title="数据集: Moons | 算法: DBSCAN"
    )

    circles_data = generate_data('circles')
    kmeans_algorithm = get_algorithm('kmeans')
    X_scaled_circles, y_pred_circles = perform_clustering(kmeans_algorithm, circles_data)
    plot_cluster_result(
        X_scaled_circles,
        y_pred_circles,
        title="数据集: Circles | 算法: K-Means"
    )
