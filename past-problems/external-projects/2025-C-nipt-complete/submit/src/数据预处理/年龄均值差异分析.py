import pandas as pd
import numpy as np

file_path = '../../sources/男胎(孕天).csv'
df = pd.read_csv(file_path)

# 将'生产次数'列转换为数值类型，无法转换的将变为NaN
df['生产次数'] = pd.to_numeric(df['生产次数'], errors='coerce')

# 去除分析所需列中的任何缺失值
df.dropna(subset=['Y染色体浓度', '生产次数', '年龄'], inplace=True)
print(f"用于分析的有效样本总数: {len(df)}")

print("\n--- 论证1：生产次数对Y染色体浓度的影响 ---")
mean_y_by_production = df.groupby('生产次数')['Y染色体浓度'].mean().reset_index()

print("按生产次数分组的Y染色体浓度均值：")
print(mean_y_by_production.to_string(index=False))
print("\n结论：如上表所示，不同生产次数对应的Y染色体浓度均值基本都维持在0.08左右，未显示出明显的趋势性影响。")

file_path = '../../sources/男胎(孕天).csv'
df = pd.read_csv(file_path)

df['生产次数'] = pd.to_numeric(df['生产次数'], errors='coerce')
df_clean = df[df['Y染色体浓度'] > 0.01].copy()
df_clean.dropna(subset=['Y染色体浓度', '年龄'], inplace=True)

# 定义年龄段的边界和标签
bins = [0, 25, 30, 35, float('inf')]
labels = ['≤ 25岁', '26-30岁', '31-35岁', '> 35岁']

# 创建一个新的'年龄段'列
df_clean['年龄段'] = pd.cut(df_clean['年龄'], bins=bins, labels=labels, right=True)
age_group_means = df_clean.groupby('年龄段')['Y染色体浓度'].mean().reset_index()
print(age_group_means.to_string(index=False))