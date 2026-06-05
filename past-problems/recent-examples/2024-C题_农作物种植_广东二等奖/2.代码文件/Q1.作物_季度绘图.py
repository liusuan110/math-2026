import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
# 读取数据
df = pd.read_csv('preprocessed_data/整理数据/2023年生产销售表(附件2.2).csv', encoding='gbk')
filtered_df = df[df['作物名称'].isin(['豇豆','刀豆','芸豆','土豆','西红柿','茄子'])]

plt.rcParams.update({'font.size': 14})
# 设置作物名称为x轴，地块类型为hue，亩产量为y轴
plt.figure(figsize=(12, 6))
sns.barplot(data=filtered_df, x='作物名称', y='亩产量/斤', hue='种植季次',ci=None)
plt.savefig(f"preprocessed_data/整理数据/Q1/作物_季度_亩产量")
plt.show()

# 设置作物名称为x轴，地块类型为hue，种植成本为y轴
plt.figure(figsize=(12, 6))
sns.barplot(data=filtered_df, x='作物名称', y='种植成本/(元/亩)', hue='种植季次',ci=None)

plt.savefig(f"preprocessed_data/整理数据/Q1/作物_季度_种植成本")
plt.show()

# 设置作物名称为x轴，地块类型为hue，种植成本为y轴
plt.figure(figsize=(12, 6))
sns.barplot(data=filtered_df, x='作物名称', y='确切销售单价/(元/斤)', hue='种植季次',ci=None)
plt.ylabel('期望销售单价')
plt.savefig(f"preprocessed_data/整理数据/Q1/作物_季度_销售单价")
plt.show()