import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
import seaborn as sns


def impute_dataframe_with_mean(df_to_impute):
    """
    对给定的DataFrame使用分组均值进行填充。
    此版本能健壮地处理某些列在子组中完全为空的情况。
    """
    X_numeric = df_to_impute.select_dtypes(include=np.number)
    X_categorical = df_to_impute.select_dtypes(exclude=np.number)

    # 如果没有数字列，直接返回
    if X_numeric.empty:
        return df_to_impute

    # --- 关键修改：将数值列分为“有数据的”和“全空的”两部分 ---
    # .dropna(axis=1, how='all') 会丢弃所有值都为NaN的列
    X_numeric_with_values = X_numeric.dropna(axis=1, how='all')

    # 找出那些被丢弃的、完全为空的列
    all_nan_columns = X_numeric.columns.difference(X_numeric_with_values.columns)
    X_numeric_all_nan = X_numeric[all_nan_columns]

    # 如果有数据的部分为空，或者不再有任何缺失值，则无需处理
    if X_numeric_with_values.empty or X_numeric_with_values.isnull().sum().sum() == 0:
        return df_to_impute

    # --- 只对“有数据的”列进行后续处理 ---
    numeric_columns = X_numeric_with_values.columns
    numeric_index = X_numeric_with_values.index

    imputer = SimpleImputer(strategy='mean')
    filled_array = imputer.fit_transform(X_numeric_with_values)
    filled_numeric_with_values = pd.DataFrame(filled_array, columns=numeric_columns, index=numeric_index)

    # --- 最终合并：合并非数字列、全空列和已填充的列 ---
    final_filled = pd.concat([X_categorical, X_numeric_all_nan, filled_numeric_with_values], axis=1)

    # 恢复原始列顺序
    final_filled = final_filled[df_to_impute.columns]

    return final_filled

# --- 2. 读取数据 ---
X_missing = pd.read_csv("文物统计数据.csv")
print(f"原始数据共 {len(X_missing)} 行。")

# --- 3. 使用 groupby 对数据进行多层分组 ---
group_columns = ['类型', '表面风化']
grouped = X_missing.groupby(group_columns)
print(f"数据将根据 '类型' 和 '表面风化' 被分为 {grouped.ngroups} 个子组进行处理...")

# --- 4. 循环处理每一个子组 ---
filled_dfs_list = []

for group_keys, group_df in grouped:
    print(f"\n--- 正在处理子组: {group_keys} ({len(group_df)} 行) ---")
    # 调用新的均值填充函数
    filled_group = impute_dataframe_with_mean(group_df.copy())
    filled_dfs_list.append(filled_group)

# --- 5. 合并所有填充好的子组并恢复原始顺序 ---
final_filled_df = pd.concat(filled_dfs_list)
final_filled_df_sorted = final_filled_df.sort_index()
print("\n已将所有处理后的子集合并，并恢复原始顺序。")

# --- 6. 保存结果 ---
output_filename = "均值填充后的文物数据.csv"
final_filled_df_sorted.to_csv(output_filename, index=False)
print(f"\n处理完成！结果已保存到 '{output_filename}'")


# --- 7. 对成分总和进行详细分析和可视化 ---
print("\n" + "="*50)
print("         对均值填充后结果的成分总和进行分析")
print("="*50)

# 计算所有数值列的总和
sums = final_filled_df_sorted.select_dtypes(include=np.number).sum(axis=1)

# a. 打印完整的总和列表
print("\n--- 1. 成分总和的完整列表 ---")
pd.set_option("display.max_rows", None)
print(sums)
pd.reset_option("display.max_rows") # 恢复默认设置

# b. 打印统计摘要
print("\n--- 2. 成分总和的统计摘要 ---")
print(sums.describe())

# c. 统计超出范围的样本数量
LOWER_BOUND = 85.0
UPPER_BOUND = 105.0
total_samples = len(sums)
valid_range_count = ((sums >= LOWER_BOUND) & (sums <= UPPER_BOUND)).sum()
too_high_count = (sums > UPPER_BOUND).sum()
too_low_count = (sums < LOWER_BOUND).sum()

print("\n--- 3. 各区间样本数量统计 ---")
print(f"总样本数: {total_samples}")
print(f"总和在 [{LOWER_BOUND}, {UPPER_BOUND}] 区间内: {valid_range_count} 个 ({(valid_range_count/total_samples):.2%})")
print(f"总和 > {UPPER_BOUND}: {too_high_count} 个 ({(too_high_count/total_samples):.2%})")
print(f"总和 < {LOWER_BOUND}: {too_low_count} 个 ({(too_low_count/total_samples):.2%})")

# d. 绘制分布直方图
print("\n--- 4. 生成成分总和分布直方图 ---")

plt.rcParams['font.sans-serif'] = ['SimHei'] # 设置全局字体以支持中文
plt.rcParams['axes.unicode_minus'] = False   # 解决负号显示问题

plt.figure(figsize=(12, 6))
sns.histplot(sums, kde=True, bins=30) # 绘制直方图和核密度曲线

# 添加标记线和文字
plt.axvline(LOWER_BOUND, color='red', linestyle='--', label=f'下限: {LOWER_BOUND}')
plt.axvline(UPPER_BOUND, color='red', linestyle='--', label=f'上限: {UPPER_BOUND}')
plt.title('均值填充后各样本化学成分总和的分布')
plt.xlabel('化学成分总和')
plt.ylabel('样本数量')
plt.legend()
plt.grid(axis='y', alpha=0.5)
plt.show()