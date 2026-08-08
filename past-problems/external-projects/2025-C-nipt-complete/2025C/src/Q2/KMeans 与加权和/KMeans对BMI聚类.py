import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

# --- Matplotlib 全局美化设置 ---
# (这部分保持不变，用于美化图表)
plt.rcParams['font.sans-serif'] = ['STZhongsong']
plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.unicode_minus'] = False


def load_data(filename):
    """仅加载并返回数据。"""
    df = pd.read_csv(filename)
    return df


def find_optimal_k(data):
    """使用手肘法寻找最佳的K值（使用自定义配色）。"""
    wcss = []
    bmi_data = data[['孕妇BMI']]
    for i in range(1, 11):
        kmeans = KMeans(n_clusters=i, init='k-means++', random_state=42, n_init='auto')
        kmeans.fit(bmi_data)
        wcss.append(kmeans.inertia_)

    # --- 配色修改 ---
    # 创建一个图形和坐标轴对象，方便进行更精细的样式设置
    fig, ax = plt.subplots(figsize=(10, 6))

    # 使用 color, markerfacecolor, markeredgecolor 等参数自定义颜色
    ax.plot(range(1, 11), wcss,
            color='darkcyan',  # 线条颜色：深青色
            linestyle='--',  # 线条样式：虚线
            linewidth=2.5,  # 线条宽度
            marker='o',  # 标记点样式：圆形
            markersize=9,  # 标记点大小
            markerfacecolor='skyblue',  # 标记点填充颜色：天蓝色
            markeredgecolor='darkcyan'  # 标记点边缘颜色：深青色
            )

    # --- 美化细节 ---
    # 设置更清晰的标题和标签
    ax.set_title('K-Means 手肘图确定最佳 K 值', pad=20)  # pad增加标题和图的间距
    ax.set_xlabel('聚类数量')
    ax.set_ylabel('簇内误差平方和')

    # 设置网格线
    ax.grid(True, linestyle=':', alpha=0.7)

    # 设置坐标轴刻度数字大小
    ax.tick_params(axis='both', which='major', labelsize=12)

    # 保存并显示图像
    plt.savefig('K-Means手肘法.pdf', bbox_inches='tight')
    plt.show()


def plot_clusters(df, kmeans_model):
    """绘制 BMI 聚类分析的结果。"""
    plt.figure(figsize=(16, 10))

    # 使用 'viridis' 调色盘来区分不同的聚类分组
    scatter = plt.scatter(df['孕妇BMI'], df['孕周'], c=df['BMI_Group'], cmap='viridis', alpha=0.7, s=50)

    # 获取聚类中心 (对于一维聚类，即为各个分组的BMI均值)
    centers = kmeans_model.cluster_centers_

    # 在图上用虚线标出聚类中心
    for i, center in enumerate(centers):
        plt.axvline(x=center[0], color='red', linestyle='--', linewidth=2, label=f'分组中心线' if i == 0 else "")

    plt.title('孕妇 BMI 的 K-Means 聚类结果', fontsize=20)
    plt.xlabel('孕妇 BMI 指标', fontsize=16)
    plt.ylabel('检测孕周 (周)', fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.6)

    # 新增图例
    plt.legend(loc='upper right')
    plt.colorbar(scatter, label='BMI 聚类分组').set_label('BMI 聚类分组', size=16)
    plt.savefig('BMI聚类分析结果.pdf', bbox_inches='tight')
    plt.show()


def main():
    input_filename = '../../../sources/男胎(Q2)(添加判断结果).csv'
    df = load_data(input_filename)

    find_optimal_k(df)
    print("手肘图已生成。通常选择曲线斜率变化最明显的点，例如 K=3 或 K=4。这里我们选择 K=4。 \n")

    # 2. 对BMI进行K-Means聚类
    print("--- 步骤2: 对BMI进行K-Means聚类 (K=4) ---")
    n_clusters = 4
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')

    # 对 '孕妇BMI' 列进行拟合和预测，并将结果存入新列
    df['BMI_Group'] = kmeans.fit_predict(df[['孕妇BMI']])

    # 3. 打印聚类分析的结果
    # 为了更直观，我们按BMI均值对分组进行排序
    sorted_centers = sorted(enumerate(kmeans.cluster_centers_[:, 0]), key=lambda x: x[1])

    print("\n--- 聚类分析结果 ---")
    print(f"{'分组ID':<10} | {'聚类中心 (BMI值)':<20} | {'该组样本数量':<15}")
    print("-" * 55)

    # 获取每个分组的样本数量
    group_counts = df['BMI_Group'].value_counts()

    for group_id, center_value in sorted_centers:
        print(f"{f'分组 {group_id}':<10} | {f'{center_value:.2f}':<20} | {group_counts[group_id]:<15}")

    # 4. 结果可视化
    print("\n--- 步骤3: 生成聚类结果的可视化图表 ---")
    plot_clusters(df, kmeans)
    print("图表已生成并显示。")


if __name__ == '__main__':
    main()