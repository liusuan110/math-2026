# https://github.com/TutteInstitute/fast_hdbscan/
import fast_hdbscan
import numpy as np
from sklearn.datasets import make_blobs
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
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

data, _ = make_blobs(n_samples=1000, n_features=2, centers=5, center_box=(-10, 10), random_state=42)

clusterer = fast_hdbscan.HDBSCAN(min_cluster_size=10)  # 采用 HDBSCAN 接口聚类
cluster_labels = clusterer.fit_predict(data)

df = pd.DataFrame(data, columns=['x', 'y'])
df['cluster'] = cluster_labels
df['cluster'] = df['cluster'].astype(str).replace('-1', 'Noise')  # 将噪声点标签替换为 'Noise'

plt.figure(figsize=(12, 8))
sns.scatterplot(
    data=df,
    x='x',
    y='y',
    hue='cluster',  # 根据 'cluster' 列自动着色
    style='cluster',  # 根据 'cluster' 列自动选择标记样式
    palette='deep',  # 选择一个美观的调色板
    s=50,  # 设置点的大小
    alpha=0.8
)
n_clusters_ = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
n_noise_ = np.sum(cluster_labels == -1)
plt.title(f'Fast_HDBSCAN 聚类结果 \n估计的簇数量: {n_clusters_} | 噪声点数量: {n_noise_}', fontsize=16)
plt.xlabel("特征 1", fontsize=12)
plt.ylabel("特征 2", fontsize=12)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(title='聚类标签')
plt.show()
