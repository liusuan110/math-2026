import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from scipy.spatial.distance import cdist

iris = load_iris()
X = pd.DataFrame(iris.data, columns=iris.feature_names)
y_true = iris.target  # 真实标签，仅用于结果对比

# -- 图片预设，需要 plt, fm, cycler 库
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

distortions = []
K_range = range(1, 10)
for k in K_range:
    model = KMeans(n_clusters=k,
                   init='k-means++',
                   n_init='auto',
                   max_iter=300,
                   tol=1e-4,
                   random_state=0
                   ).fit(X)
    distortions.append(model.inertia_)  # inertia_ 属性直接给出了簇内平方和

plt.figure(figsize=(10, 6))
plt.plot(K_range, distortions, 'bx-')
plt.xlabel('聚类数量 K')
plt.ylabel('簇内平方和 (SSE)')
plt.title('手肘法确定最佳 K 值')
# 在图上标记出“肘部”
plt.annotate('“肘部”在此，K=3', xy=(3, distortions[2]), xytext=(4, 150),
             arrowprops=dict(facecolor='black', shrink=0.05))
plt.show()

kmeans = KMeans(n_clusters=3, n_init='auto', random_state=0)
clusters = kmeans.fit_predict(X)

plt.figure(figsize=(12, 8))

sns.scatterplot(
    x=X.iloc[:, 0],  # 萼片长度
    y=X.iloc[:, 1],  # 萼片宽度
    hue=clusters,  # 根据聚类结果分配颜色
    style=y_true,  # 根据真实物种分配形状
    palette='viridis',  # 使用一个美观的色板
    s=150,  # 标记大小
    alpha=0.8,  # 透明度
    legend='full'
)

# 绘制聚类中心
centers = kmeans.cluster_centers_
plt.scatter(centers[:, 0], centers[:, 1], c='red', s=300, marker='X', label='聚类中心')

plt.title('K-Means 聚类结果 vs. 真实物种分布')
plt.xlabel('萼片长度 (cm)')
plt.ylabel('萼片宽度 (cm)')
plt.legend(title='图例')
plt.show()

# --- 6. (进阶) 使用 Pairplot 进行全维度分析 ---
# Pairplot可以展示所有特征两两之间的关系，是更高维数据可视化的利器
results_df = X.copy()
results_df['聚类标签'] = clusters
results_df['真实物种'] = [iris.target_names[i] for i in y_true]

sns.pairplot(results_df, hue='聚类标签', palette='viridis', corner=True)
plt.suptitle('所有特征的聚类分布 Pairplot', y=1.02)
plt.show()
