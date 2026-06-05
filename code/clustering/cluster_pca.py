"""聚类与降维模板（scikit-learn）：KMeans 聚类 + 肘部法 + PCA 降维可视化。

适用：C 题数据分析——给样本分组、特征压缩、降维画图。
"""
from __future__ import annotations

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


def elbow(X, k_range=range(1, 8)):
    """肘部法：返回各 k 对应的簇内平方和(inertia)，拐点即合适的 k。"""
    Xs = StandardScaler().fit_transform(X)
    return {k: KMeans(n_clusters=k, n_init=10, random_state=0).fit(Xs).inertia_
            for k in k_range}


def kmeans_cluster(X, n_clusters=3):
    """标准化后做 KMeans，返回标签与质心（质心已还原到原始量纲）。"""
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=0).fit(Xs)
    centers = scaler.inverse_transform(km.cluster_centers_)
    return {"labels": km.labels_, "centers": centers, "inertia": km.inertia_}


def pca_2d(X):
    """PCA 降到 2 维用于可视化，返回坐标与累计解释方差比。"""
    Xs = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2)
    coords = pca.fit_transform(Xs)
    return {"coords": coords, "explained": pca.explained_variance_ratio_}


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    # 构造 3 个簇
    X = np.vstack([
        rng.normal([0, 0], 0.5, (30, 2)),
        rng.normal([5, 5], 0.5, (30, 2)),
        rng.normal([0, 5], 0.5, (30, 2)),
    ])
    print("肘部法 inertia:", {k: round(v, 1) for k, v in elbow(X).items()})
    res = kmeans_cluster(X, n_clusters=3)
    print("各簇样本数:", np.bincount(res["labels"]))
    p = pca_2d(X)
    print("PCA 累计解释方差比:", np.round(p["explained"].sum(), 4))
