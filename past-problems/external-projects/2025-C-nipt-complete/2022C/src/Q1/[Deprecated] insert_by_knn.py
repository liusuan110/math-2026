import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import seaborn as sns


# --- 1. 定义一个升级版、更健壮的KNN填充函数 ---
def impute_dataframe_with_knn(df_to_impute, k=5):
    """
    对给定的DataFrame进行归一化、KNN填充，然后逆归一化。
    此版本能健壮地处理某些列在子组中完全为空的情况。
    """
    X_numeric = df_to_impute.select_dtypes(include=np.number)
    X_categorical = df_to_impute.select_dtypes(exclude=np.number)

    if X_numeric.empty:
        return df_to_impute

    # --- 关键修改：将数值列分为“有数据的”和“全空的”两部分 ---
    X_numeric_with_values = X_numeric.dropna(axis=1, how='all')

    all_nan_columns = X_numeric.columns.difference(X_numeric_with_values.columns)
    X_numeric_all_nan = X_numeric[all_nan_columns]

    if X_numeric_with_values.empty or X_numeric_with_values.isnull().sum().sum() == 0:
        return df_to_impute

    # --- 只对“有数据的”列进行后续处理 ---
    numeric_columns = X_numeric_with_values.columns
    numeric_index = X_numeric_with_values.index

    # a. 归一化
    scaler = MinMaxScaler()
    X_scaled_array = scaler.fit_transform(X_numeric_with_values)

    # b. 在归一化数据上进行KNN填充
    imputer = KNNImputer(n_neighbors=k)
    X_filled_scaled_array = imputer.fit_transform(X_scaled_array)

    # c. 逆归一化，还原数据
    X_filled_inversed_array = scaler.inverse_transform(X_filled_scaled_array)

    filled_numeric_with_values = pd.DataFrame(X_filled_inversed_array, columns=numeric_columns, index=numeric_index)

    # d. 最终合并：合并非数字列、全空列和已填充的列
    final_filled = pd.concat([X_categorical, X_numeric_all_nan, filled_numeric_with_values], axis=1)

    # 恢复原始列顺序
    final_filled = final_filled[df_to_impute.columns]

    return final_filled


# --- 主流程代码 (无需修改) ---
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
    filled_group = impute_dataframe_with_knn(group_df.copy(), k=5)
    filled_dfs_list.append(filled_group)

# --- 5. 合并所有填充好的子组并恢复原始顺序 ---
final_filled_df = pd.concat(filled_dfs_list)
final_filled_df_sorted = final_filled_df.sort_index()
print("\n已将所有处理后的子集合并，并恢复原始顺序。")

# --- 6. 保存结果 ---
output_filename = "KNN填充后的文物数据.csv"
final_filled_df_sorted.to_csv(output_filename, index=False)
print(f"\n处理完成！结果已保存到 '{output_filename}'")