import pandas as pd
import numpy as np
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler


# --- 1. 定义最终版的、更健壮的填充函数 ---
def impute_dataframe_with_scaling(df_to_impute):
    """
    对给定的DataFrame进行归一化、填充，然后逆归一化。
    此版本能健壮地处理某些列在子组中完全为空的情况。
    """
    X_numeric = df_to_impute.select_dtypes(include=np.number)
    X_categorical = df_to_impute.select_dtypes(exclude=np.number)

    # 如果没有数字列，直接返回
    if X_numeric.empty:
        return df_to_impute

    # --- 关键修改：将数值列分为“有数据的”和“全空的”两部分 ---
    # dropna(axis=1, how='all') 会丢弃所有值都为NaN的列
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

    scaler = MinMaxScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X_numeric_with_values), columns=numeric_columns)

    imputer = IterativeImputer(
        estimator=RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_leaf=3,
                                        bootstrap=True, max_samples=0.7, n_jobs=-1, random_state=0),
        max_iter=40, tol=1e-1, random_state=0,
        verbose=0
    )
    X_filled_scaled_array = imputer.fit_transform(X_scaled)
    X_filled_inversed_array = scaler.inverse_transform(X_filled_scaled_array)
    filled_numeric_with_values = pd.DataFrame(X_filled_inversed_array, columns=numeric_columns, index=numeric_index)

    # --- 最终合并：合并非数字列、全空列和已填充的列 ---
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
print(f"数据将根据 '类型' 和 '表面风化' 被分为 {grouped.ngroups} 个子组进行精细化处理...")

# --- 4. 循环处理每一个子组 ---
filled_dfs_list = []

for group_keys, group_df in grouped:
    print(f"\n--- 正在处理子组: {group_keys} ({len(group_df)} 行) ---")
    filled_group = impute_dataframe_with_scaling(group_df.copy())
    filled_dfs_list.append(filled_group)

# --- 5. 合并所有填充好的子组并恢复原始顺序 ---
final_filled_df = pd.concat(filled_dfs_list)
final_filled_df_sorted = final_filled_df.sort_index()
print("\n已将所有处理后的子集合并，并恢复原始顺序。")

# --- 6. 保存并展示结果 ---
final_filled_df_sorted.to_csv("多层分组填充后的文物数据.csv", index=False)
print("\n处理完成！最终结果已保存到 '多层分组填充后的文物数据.csv'")
print("最终数据预览:")
pd.set_option("display.max_rows", None)
print(final_filled_df_sorted.select_dtypes(include=np.number).sum(axis=1))