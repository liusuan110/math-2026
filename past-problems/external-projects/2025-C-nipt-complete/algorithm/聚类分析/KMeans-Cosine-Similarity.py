import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize # 导入归一化函数
from sklearn.metrics.pairwise import cosine_similarity # 导入余弦相似度计算函数

# doc1 和 doc3 主题相似 (前两个词权重高)
# doc2 主题不同 (后两个词权重高)
X = np.array([
    [1.0, 0.8, 0.1, 0.0], # doc1
    [0.0, 0.1, 1.0, 0.9], # doc2
    [0.5, 0.4, 0.0, 0.1], # doc3 (doc1的短版本)
])

# 对数据进行 L2 归一化
X_normalized = normalize(X, norm='l2', axis=1)
print(X_normalized)

# 在归一化后的数据上运行标准 K-Means
# 算法内部仍然使用欧几里得距离，但因为数据已被归一化，
# 其效果等同于在原始数据上使用余弦相似度
kmeans = KMeans(n_clusters=2, random_state=0, n_init='auto')
kmeans.fit(X_normalized)
labels = kmeans.labels_
centers_normalized = kmeans.cluster_centers_
print(f"各样本的聚类标签: {labels}")

# 计算原始样本两两之间的余弦相似度
original_similarity_matrix = cosine_similarity(X)
print("\n原始样本间的余弦相似度矩阵:")
print(pd.DataFrame(original_similarity_matrix,
                 index=['doc1', 'doc2', 'doc3'],
                 columns=['doc1', 'doc2', 'doc3']).round(2))

# 计算每个样本与其所属簇质心的余弦相似度
for i, label in enumerate(labels):
    sample = X_normalized[i].reshape(1, -1)
    center = centers_normalized[label].reshape(1, -1)
    sim = cosine_similarity(sample, center)[0][0]
    print(f"样本 {i+1} (属于簇 {label}) 与其质心的余弦相似度: {sim:.4f}")