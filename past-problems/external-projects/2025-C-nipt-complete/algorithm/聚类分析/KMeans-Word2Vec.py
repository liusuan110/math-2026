import numpy as np
from gensim.models import Word2Vec
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
import warnings

# 忽略 gensim 的一些警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- 准备数据和词向量模型 ---

# 1. 示例文本数据
documents = [
    "the cat sat on the mat",
    "a dog was chasing the cat",
    "the dog is a loyal animal",
    "I love my pet animal",
    "the mat is on the floor",
    "the floor is clean"
]

# 将文档分词
tokenized_docs = [doc.split() for doc in documents]

# 2. 训练一个简单的 Word2Vec 模型 (实际应用中通常加载预训练好的大型模型)
# size: 向量维度, window: 上下文窗口大小, min_count: 忽略低频词, workers: 并行线程数
print("正在训练 Word2Vec 模型...")
word2vec_model = Word2Vec(sentences=tokenized_docs, vector_size=100, window=5, min_count=1, workers=4)
print("模型训练完成！\n")


# --- 核心实现步骤 ---

# 3. 定义文档向量化函数 (平均法)
def vectorize_document(doc, model):
    """将单个文档转换为平均词向量"""
    words = doc.split()
    # 获取文档中所有在模型词汇表里的词向量
    word_vectors = [model.wv[word] for word in words if word in model.wv]

    if not word_vectors:
        # 如果文档中所有词都不在词汇表里，返回一个零向量
        return np.zeros(model.vector_size)

    # 计算平均向量
    doc_vector = np.mean(word_vectors, axis=0)
    return doc_vector


# 4. 将所有文档转换为向量矩阵
print("正在将文档转换为向量...")
vectorized_docs = np.array([vectorize_document(doc, word2vec_model) for doc in documents])
print(f"向量化完成！矩阵形状: {vectorized_docs.shape}\n")

# 5. ⚠️ 关键步骤：对向量进行 L2 归一化
# 这使得欧几里得距离等价于余弦距离
normalized_vectors = normalize(vectorized_docs, norm='l2')

# 6. 使用标准的 KMeans 进行聚类
# n_clusters 是你希望分成的簇数
kmeans = KMeans(n_clusters=2, random_state=42, n_init='auto')
kmeans.fit(normalized_vectors)

# --- 查看聚类结果 ---

# 7. 获取每个文档的聚类标签
labels = kmeans.labels_

# 8. 将文档按聚类结果分组打印
clusters = {}
for i, doc in enumerate(documents):
    cluster_id = labels[i]
    if cluster_id not in clusters:
        clusters[cluster_id] = []
    clusters[cluster_id].append(doc)

print("--- 聚类结果 ---")
for cluster_id, docs_in_cluster in clusters.items():
    print(f"\nCluster {cluster_id}:")
    for doc in docs_in_cluster:
        print(f"  - {doc}")