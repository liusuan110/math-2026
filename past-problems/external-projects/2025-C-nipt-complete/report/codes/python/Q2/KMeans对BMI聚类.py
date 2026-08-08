import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

# --- Matplotlib 全局美化设置 ---
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


def load_data(fname):
    df = pd.read_csv(fname)
    return df


def find_best_k(data):
    # 使用手肘法寻找最佳的K值
    wcss = []
    bmi_data = data[['孕妇BMI']]
    for i in range(1, 11):
        km = KMeans(n_clusters=i, init='k-means++', random_state=42, n_init='auto')
        km.fit(bmi_data)
        wcss.append(km.inertia_)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(range(1, 11), wcss,
            color='darkcyan',
            linestyle='--',
            linewidth=2.5,
            marker='o',
            markersize=9,
            markerfacecolor='skyblue',
            markeredgecolor='darkcyan'
            )

    ax.set_title('K-Means 手肘图确定最佳 K 值', pad=20)
    ax.set_xlabel('聚类数量')
    ax.set_ylabel('簇内误差平方和')

    ax.grid(True, linestyle=':', alpha=0.7)
    ax.tick_params(axis='both', which='major', labelsize=12)

    plt.savefig('K-Means手肘法.pdf', bbox_inches='tight')
    plt.show()


def plot_clusters(df, km_model):
    # 绘制 BMI 聚类分析的结果
    plt.figure(figsize=(16, 10))

    sct = plt.scatter(df['孕妇BMI'], df['孕周'], c=df['BMI_Group'], cmap='viridis', alpha=0.7, s=50)

    ctrs = km_model.cluster_centers_

    for i, ctr in enumerate(ctrs):
        plt.axvline(x=ctr[0], color='red', linestyle='--', linewidth=2, label=f'分组中心线' if i == 0 else "")

    plt.title('孕妇 BMI 的 K-Means 聚类结果', fontsize=20)
    plt.xlabel('孕妇 BMI 指标', fontsize=16)
    plt.ylabel('检测孕周 (周)', fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.6)

    plt.legend(loc='upper right')
    plt.colorbar(sct, label='BMI 聚类分组').set_label('BMI 聚类分组', size=16)
    plt.savefig('BMI聚类分析结果.pdf', bbox_inches='tight')
    plt.show()


def main():
    # 1. 加载数据
    in_file = '../../../sources/男胎(Q2)(添加判断结果).csv'
    df = load_data(in_file)

    # 2. 寻找最佳K值
    find_best_k(df)

    # 3. 对BMI进行K-Means聚类
    k_num = 4
    km = KMeans(n_clusters=k_num, random_state=42, n_init='auto')
    df['BMI_Group'] = km.fit_predict(df[['孕妇BMI']])

    # 4. 打印聚类分析的结果
    sort_ctrs = sorted(enumerate(km.cluster_centers_[:, 0]), key=lambda x: x[1])

    print("--- 聚类分析结果 ---")
    print(f"{'分组ID':<10} | {'聚类中心 (BMI值)':<20} | {'该组样本数量':<15}")
    print("-" * 55)

    grp_cnt = df['BMI_Group'].value_counts()

    for gid, ctr_val in sort_ctrs:
        print(f"{f'分组 {gid}':<10} | {f'{ctr_val:.2f}':<20} | {grp_cnt[gid]:<15}")

    # 5. 结果可视化
    plot_clusters(df, km)


if __name__ == '__main__':
    main()