import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import AgglomerativeClustering  # 导入层次聚类
from sklearn.preprocessing import normalize
from sklearn.metrics import silhouette_score
from sentence_transformers import SentenceTransformer
from scipy.cluster.hierarchy import dendrogram, linkage  # 用于绘制树状图


# --- 1. 定义新的层次聚类函数 ---
def cluster_texts_hierarchical(data, n_clusters):
    """
    使用层次聚类（基于余弦相似度）对文本向量进行聚类。
    """
    # 同样需要先归一化，这样欧几里得距离就等价于余弦相似度
    data_normalized = normalize(data, norm='l2', axis=1)

    # linkage='ward' 是一种旨在最小化簇内方差的合并策略，非常稳健
    hac = AgglomerativeClustering(n_clusters=n_clusters, metric='euclidean', linkage='ward')
    # 在旧版本sklearn中，参数为affinity='euclidean'

    # fit_predict 直接返回聚类标签
    labels = hac.fit_predict(data_normalized)
    return labels, hac


# --- 语料库和向量化 (与您的一致) ---
corpus_large = [
    "英伟达发布了最新一代的AI图形处理芯片，其计算性能实现了翻倍增长。", "云计算服务已经成为现代企业IT基础设施的核心，提供了前所未有的弹性和可扩展性。",
    "开源社区推出了一个全新的深度学习框架，旨在简化神经网络模型的开发和部署流程。",
    "最新的软件更新修复了多个已知的安全漏洞，并优化了系统的整体运行效率。",
    "昨晚的世界杯决赛上演了惊天逆转，阿根廷队在加时赛的最后一分钟攻入制胜一球。",
    "牙买加选手在奥运会百米飞人大战中再次刷新世界纪录，巩固了其短跑霸主的地位。",
    "F1方程式赛车摩纳哥站的比赛因为突降暴雨而中断，增加了比赛结果的不确定性。", "NBA季后赛抢七大战异常激烈，湖人队凭借詹姆斯的绝杀三分球险胜对手。",
    "由于通货膨胀数据高于预期，美联储暗示可能会在下一次会议上继续加息。", "A股市场今日迎来大幅反弹，新能源和半导体板块领涨，成交量显著放大。",
    "全球供应链问题持续影响大宗商品价格，导致制造业成本普遍上升。", "最新的季度财报显示，苹果公司的营收和利润均超出了华尔街分析师的预期。",
    "备受期待的科幻大片《星际漫游者》今日上映，首日票房已突破两亿大关。", "著名导演宣布其下一部电影将聚焦历史题材，并邀请了多位实力派演员加盟。",
    "线上音乐节吸引了全球数百万观众，展示了数字时代下全新的艺术表现形式。",
    "一部关于宫廷斗争的电视剧近期爆火，其精美的服化道和紧凑的剧情引发了热烈讨论。",
    "世界卫生组织发布年度报告，强调了均衡饮食和规律运动对于预防慢性病的重要性。",
    "一种新型的癌症靶向药在临床试验中取得了突破性进展，为患者带来了新的希望。",
    "研究表明，充足的睡眠对于维持大脑功能和情绪稳定至_关重要。", "公众对心理健康问题的关注度日益提高，社会应提供更多相关的支持和咨询服务。",
    "随着旅行限制的放宽，前往东南亚海岛度假的游客数量呈现爆炸式增长。", "这篇旅游攻略详细介绍了如何在预算有限的情况下，深度体验巴黎的文化与美食。",
    "自驾穿越川西高原成为热门路线，沿途的雪山、湖泊和草原风光令人叹为观止。", "联合国教科文组织将一处古代文明遗址列入世界文化遗产名录，以促进其保护和研究。"
]
model_name = 'BAAI/bge-m3'
model = SentenceTransformer(model_name)
print("--- 正在将文本编码为语义向量 ---")
X_semantic = model.encode(corpus_large)
X_normalized = normalize(X_semantic, norm='l2', axis=1)

# --- 2. (可选但推荐) 可视化层次聚类的树状图 (Dendrogram) ---
# 树状图可以非常直观地展示数据点是如何被一步步合并的，有助于我们理解数据的结构
print("\n--- 正在生成层次聚类树状图 ---")
# 使用 'ward' 方法计算链接矩阵
linked = linkage(X_normalized, method='ward')

plt.figure(figsize=(12, 7))
sns.set_theme(style="white", font='SimHei')
dendrogram(linked,
           orientation='top',
           labels=range(len(corpus_large)),  # 用样本索引作为标签
           distance_sort='descending',
           show_leaf_counts=True)
plt.title('层次聚类树状图 (Dendrogram)')
plt.xlabel('样本索引')
plt.ylabel('距离 (Distance)')
plt.show()

# --- 3. 使用轮廓系数寻找最佳 K 值 (同样适用) ---
print("\n--- 正在计算不同K值的轮廓系数 (使用层次聚类) ---")
silhouette_scores = []
K_range = range(2, 11)

for k in K_range:
    # 调用新的层次聚类函数
    labels, _ = cluster_texts_hierarchical(X_semantic, n_clusters=k)
    score = silhouette_score(X_normalized, labels)
    silhouette_scores.append(score)
    print(f"K = {k}, 轮廓系数 = {score:.4f}")

# 找到分数最高的K值
best_k = K_range[np.argmax(silhouette_scores)]
print(f"\n最佳K值为: {best_k} (轮廓系数最高)")

# --- 4. 使用最佳K值进行最终聚类 ---
print(f"\n--- 使用最佳K值 K={best_k} 和层次聚类重新进行聚类 ---")
labels, hac_model = cluster_texts_hierarchical(X_semantic, n_clusters=best_k)

results_df = pd.DataFrame({'text': corpus_large, 'cluster': labels})
print("\n--- 最终聚类结果 (层次聚类) ---")
print(results_df.sort_values('cluster').to_string())