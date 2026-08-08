import numpy as np
import pandas as pd
from skbio.stats.composition import clr
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

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


def create_chemical_dataset(n_samples_per_cluster: int = 20) -> pd.DataFrame:
    """创建一个模拟的化学品成分数据集"""
    np.random.seed(42)
    prototypes = {
        'Iron-Copper': np.array([0.4, 0.3, 0.05, 0.05, 0.1, 0.05, 0.025, 0.025]),
        'Precious-Metals': np.array([0.05, 0.05, 0.3, 0.2, 0.1, 0.1, 0.15, 0.05]),
        'Silica-Alumina': np.array([0.1, 0.05, 0.05, 0.05, 0.3, 0.35, 0.025, 0.075])
    }
    all_data = []
    for proto in prototypes.values():
        all_data.append(np.random.dirichlet(proto * 50, size=n_samples_per_cluster))
    compositional_data = np.vstack(all_data)
    columns = ['Fe', 'Cu', 'Au', 'Ag', 'Si', 'Al', 'Pb', 'Zn']
    index = [f'Sample_{i + 1}' for i in range(compositional_data.shape[0])]
    df = pd.DataFrame(compositional_data, columns=columns, index=index)
    return df


def plot_scree(pca_explained_variance: np.ndarray) -> int:
    """绘制碎石图以帮助确定最佳主成分数量"""
    print("\n--- 步骤 3: 绘制碎石图确定主成分数量 ---")
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(pca_explained_variance) + 1), pca_explained_variance, 'o-', linewidth=2)
    plt.title('Scree Plot (碎石图)', fontsize=16)
    plt.xlabel('Principal Component (主成分)', fontsize=12)
    plt.ylabel('Explained Variance Ratio (方差解释率)', fontsize=12)
    plt.xticks(range(1, len(pca_explained_variance) + 1))
    plt.grid(True)
    recommended_k = 2
    plt.axvline(x=recommended_k + 0.5, color='r', linestyle='--', label=f'Elbow Point (拐点) at k={recommended_k}')
    plt.legend()
    plt.show()
    print(f"根据碎石图的'拐点'，推荐保留的主成分数量为: {recommended_k}")
    return recommended_k


def apply_kaiser_criterion(pca_model: PCA) -> int:
    """应用 Kaiser 准则 (特征值 > 1) 来确定主成分数量"""
    eigenvalues = pca_model.explained_variance_

    print("各主成分的特征值 (Eigenvalues):")
    for i, eig in enumerate(eigenvalues):
        print(f"  PC{i + 1}: {eig:.4f}")

    n_components = np.sum(eigenvalues > 1)
    print(f"\n根据 Kaiser 准则 (特征值 > 1)，推荐保留的主成分数量为: {n_components}")
    return n_components


def find_optimal_clusters(data: pd.DataFrame, max_k: int = 10) -> int:
    """使用轮廓系数法确定最佳的 K-Means 聚类数量"""
    print("\n--- 步骤 5: 使用轮廓系数确定最佳聚类数量 ---")
    best_k = -1
    best_score = -1
    for k in range(2, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
        kmeans.fit(data)
        score = silhouette_score(data, kmeans.labels_)
        if score > best_score:
            best_score = score
            best_k = k
    print(f"最佳 k 值为: {best_k} (因为它的轮廓系数最高)")
    return best_k


def plot_clusters(pc_df: pd.DataFrame, pca_model: PCA, kmeans_model: KMeans):
    """将 PCA 降维和 K-Means 聚类的结果可视化"""
    plt.figure(figsize=(12, 8))
    sns.scatterplot(x='PC1', y='PC2', hue='Cluster', data=pc_df, palette='viridis', s=100, alpha=0.8, legend='full')
    centroids = kmeans_model.cluster_centers_
    plt.scatter(centroids[:, 0], centroids[:, 1], c='red', s=250, marker='X', label='Centroids (聚类中心)')
    plt.title('K-Means Clustering on Principal Components (基于主成分的K-Means聚类)', fontsize=16)
    plt.xlabel(f'Principal Component 1 ({pca_model.explained_variance_ratio_[0]:.2%})', fontsize=12)
    plt.ylabel(f'Principal Component 2 ({pca_model.explained_variance_ratio_[1]:.2%})', fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_loadings(pca_model: PCA, feature_names: list):
    """绘制 PCA 载荷的热力图"""
    # 载荷矩阵 (n_features, n_components)
    loadings = pca_model.components_.T
    loadings_df = pd.DataFrame(loadings,
                               columns=[f'PC{i + 1}' for i in range(pca_model.n_components_)],
                               index=feature_names)

    plt.figure(figsize=(10, 8))
    sns.heatmap(loadings_df, annot=True, cmap='coolwarm', fmt='.2f')
    plt.title('PCA Loadings Plot (主成分载荷图)', fontsize=16)
    plt.show()


def plot_biplot(pc_df: pd.DataFrame, pca_model: PCA, feature_names: list):
    """绘制 PCA 双标图 (Biplot)"""
    fig, ax = plt.subplots(figsize=(14, 10))

    sns.scatterplot(x='PC1', y='PC2', hue='Cluster', data=pc_df, palette='viridis', s=100, alpha=0.7, ax=ax)
    loadings = pca_model.components_.T  # 载荷向量

    # 为了让箭头在图上看得清楚，通常需要乘以一个缩放因子
    scale_factor = 1.5 * np.max(pc_df[['PC1', 'PC2']].abs().values)  # 一个简单的缩放逻辑

    for i, feature in enumerate(feature_names):
        ax.arrow(0, 0, loadings[i, 0] * scale_factor, loadings[i, 1] * scale_factor,
                 color='r', alpha=0.8, head_width=0.05)
        ax.text(loadings[i, 0] * scale_factor * 1.15, loadings[i, 1] * scale_factor * 1.15,
                feature, color='r', ha='center', va='center', fontsize=12)

    ax.set_title('PCA Biplot (双标图)', fontsize=16)
    ax.set_xlabel(f'Principal Component 1 ({pca_model.explained_variance_ratio_[0]:.2%})', fontsize=12)
    ax.set_ylabel(f'Principal Component 2 ({pca_model.explained_variance_ratio_[1]:.2%})', fontsize=12)
    ax.grid(True)
    plt.show()


def main():
    df_compositional = create_chemical_dataset(n_samples_per_cluster=20)
    clr_data = clr(df_compositional.values)
    pca_full = PCA()
    pca_full.fit(clr_data)

    print("\n--- 确定最佳主成分数量 (方法一：碎石图) ---")
    n_components = plot_scree(pca_full.explained_variance_ratio_)
    print(f"根据碎石图，推荐保留的主成分数量为: {n_components}")

    print("\n--- 确定最佳主成分数量 (方法二：Kaiser准则) ---")
    n_components_kaiser = apply_kaiser_criterion(pca_full)
    print(f"根据 Kaiser 准则，推荐保留的主成分数量为: {n_components_kaiser}")

    pca = PCA(n_components=n_components)
    principal_components = pca.fit_transform(clr_data)
    pc_df = pd.DataFrame(data=principal_components,
                         columns=[f'PC{i + 1}' for i in range(n_components)],
                         index=df_compositional.index)
    print(f"已将数据降至 {n_components} 个维度。")

    # 确定最佳聚类数 k
    best_k = find_optimal_clusters(pc_df, max_k=10)
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init='auto')
    pc_df['Cluster'] = kmeans.fit_predict(pc_df)

    # 可视化聚类结果
    plot_clusters(pc_df, pca, kmeans)

    feature_names = df_compositional.columns.tolist()
    plot_loadings(pca, feature_names)
    plot_biplot(pc_df, pca, feature_names)


if __name__ == '__main__':
    main()
