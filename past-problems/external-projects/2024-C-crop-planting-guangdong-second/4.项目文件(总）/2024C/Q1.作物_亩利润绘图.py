import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
# 读取数据
df = pd.read_csv('preprocessed_data/整理数据/2023年生产销售表(附件2.2).csv', encoding='gbk')

plot_types = df['地块类型'].unique()

for plot_type in plot_types:
    # 筛选出当前地块类型的数据
    df_plot = df[df['地块类型'] == plot_type]
    # 绘制柱形图
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_plot, x='作物名称', y='亩利润/(元/亩)', hue='种植季次', ci=None)
    plt.xlabel("作物名称",fontsize=14)
    plt.ylabel("亩利润/(元/亩)",fontsize=14)
    # 显示图表
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f"preprocessed_data/整理数据/Q1/{plot_type}_亩利润图")
    plt.show()
