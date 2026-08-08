import pandas as pd
from pprint import pprint
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer  # 导入句嵌入模型


def cluster_texts_by_cosine(data, n_clusters, random_state=0):
    data_normalized = normalize(data, norm='l2', axis=1)
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init='auto')
    kmeans.fit(data_normalized)
    return kmeans.labels_, kmeans


corpus = [
    "人工智能 深度学习 正在 改变 世界",  # 科技
    "谷歌 发布 最新 AI 模型",  # 科技
    "世界杯 决赛 精彩 进球",  # 体育
    "股市 大幅 波动 投资者 保持 谨慎",  # 财经
    "神经网络 和 自然语言处理 新 进展",  # 科技
    "奥运会 冠军 诞生 刷新 纪录",  # 体育
    "美联储 宣布 利率 政策 影响 市场",  # 财经
    "湖人队 赢得 NBA 总冠军",  # 体育
    "全球 经济 增长 预期 下调",  # 财经
    "最新 算法 提升 AI 性能",  # 科技
    "音乐 旋律 难听 徐梦圆",
    "数学建模 论文 抄袭 事件",
    "王境泽 方便面 事件",
    "蓝翔技校 挖掘机 事件",
    "我太难了 真香 社会人",
    "傻逼 逆天 拱坝 六六六",
]

# 使用 Sentence-BERT 进行文本向量化
# 模型列表: https://www.sbert.net/docs/pretrained_models.html
model_name = 'shibing624/text2vec-base-chinese'
model = SentenceTransformer(model_name)

print("--- 正在将文本编码为语义向量 ---")
# .encode() 方法可以直接将句子列表转换为向量矩阵
X_semantic = model.encode(corpus)

print("数据维度:", X_semantic.shape)  # (10个样本, 768个维度)

num_clusters = 4
labels, kmeans_model = cluster_texts_by_cosine(X_semantic, n_clusters=num_clusters)

results_df = pd.DataFrame({'text': corpus, 'cluster': labels})
print("\n--- 使用语义向量后的聚类结果 ---")
pprint(results_df.sort_values('cluster'))
