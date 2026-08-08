import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs

def main():
    np.random.seed(233)
    X, y = make_blobs(n_samples=300, n_features=4, centers=3, cluster_std=2.0, random_state=42)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    components = pca.components_
    print("\n每个主成分对应的原始特征权重：")
    print(components)

    explained_variance_ratio = pca.explained_variance_ratio_
    print("\nPCA 保留的方差比例：")
    print(explained_variance_ratio)

    print("\n降维前的形状：", X_scaled.shape)
    print("降维后的形状：", X_pca.shape)

    plt.figure(figsize=(10, 6))

    # 绘制降维后的数据，按类别着色
    plt.scatter(X_pca[:, 0], X_pca[:, 1], c=y, cmap='viridis', edgecolor='k')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.title('PCA reduced data')
    plt.colorbar(label='category')
    plt.show()

    X_pca_2d = X_pca[:, :2]
    print("\n降维后的二维数据：")
    print(X_pca_2d)


if __name__ == '__main__':
    main()