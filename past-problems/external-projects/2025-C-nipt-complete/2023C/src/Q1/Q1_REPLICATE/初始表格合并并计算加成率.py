import pandas as pd

file_path_1 = '../../../sources/附件1.csv'
file_path_2 = '../../../sources/附件2.csv'
file_path_3 = '../../../sources/附件3.csv'
file_path_4 = '../../../sources/附件4.csv'

df1 = pd.read_csv(file_path_1)
df2 = pd.read_csv(file_path_2)
df3 = pd.read_csv(file_path_3)
df4 = pd.read_csv(file_path_4)

# 转换日期格式为datetime对象，便于后续操作
df2['销售日期'] = pd.to_datetime(df2['销售日期'])
df3['日期'] = pd.to_datetime(df3['日期'])

# 重命名附件 3 的日期列，使其与附件 2 的列名一致，方便合并
df3.rename(columns={'日期': '销售日期'}, inplace=True)

# 使用'销售日期'和'单品编码'同时作为连接键
sales_with_cost = pd.merge(df2, df3, on=['销售日期', '单品编码'], how='left')  # Left 方案可以保留其他信息，最常用
df_info = pd.merge(df1, df4.drop(columns=['单品名称'], errors='ignore'), on='单品编码', how='left')
final_df = pd.merge(sales_with_cost, df_info, on='单品编码', how='left')

# 检查合并后批发价格的缺失情况
missing_prices = final_df['批发价格(元/千克)'].isnull().sum()
print(f"合并完成。共有 {len(final_df)} 条销售记录。")
if missing_prices > 0:
    print(f"其中有 {missing_prices} 条记录未能匹配到当日的批发价格。")

# 论文思路：通过计算加成率来发现异常定价数据。
# 公式: 加成率 = (销售单价 - 批发价格) / 批发价格
print("\n--- 正在计算加成率... ---")
final_df['加成率'] = (final_df['销售单价(元/千克)'] - final_df['批发价格(元/千克)']) / final_df['批发价格(元/千克)']

# 保存包含加成率的中间文件
final_df.to_csv("初始数据合并表格(含加成率).csv", index=False, encoding='utf_8_sig')

# # --- 步骤 4(新增): 3σ法则异常值检验 ---
# print("\n--- 正在根据3σ法则清洗【加成率】的极端异常值 ---")
#
# # 计算前需排除空值
# markup_rate = sales_with_cost['加成率'].dropna()
# mean = markup_rate.mean()
# std = markup_rate.std()
#
# # 定义3σ的上下界
# upper_bound = mean + 3 * std
# lower_bound = mean - 3 * std
# print(f"加成率的均值为: {mean:.4f}")
# print(f"加成率的标准差为: {std:.4f}")
# print(f"3σ法则的有效范围为: [{lower_bound:.4f}, {upper_bound:.4f}]")
#
# # 识别在范围之外的异常值
# outliers = sales_with_cost[
#     (sales_with_cost['加成率'] < lower_bound) | (sales_with_cost['加成率'] > upper_bound)
#     ]
# num_outliers_3sigma = len(outliers)
#
# # 剔除异常值
# data_after_3sigma = sales_with_cost[
#     (sales_with_cost['加成率'] >= lower_bound) & (sales_with_cost['加成率'] <= upper_bound) | (sales_with_cost['加成率'].isnull())
#     ].copy()
# print(f"根据3σ法则，共发现并剔除了 {num_outliers_3sigma} 条统计学上的极端异常记录。")
# print(f"剔除后剩余记录数: {len(data_after_3sigma)}")
#
# # --- 步骤 5: 修正处理 (业务规则) ---
# # 论文思路：在统计规则基础上，再用业务规则进行修正
# print("\n--- 正在根据业务规则(加成率 > 2)进行二次清洗... ---")
# rows_before_rule = len(data_after_3sigma)
#
# # 在经过3σ筛选后的数据上，再应用 > 2 的规则
# cleaned_sales_data = data_after_3sigma[
#     (data_after_3sigma['加成率'] <= 2) | (data_after_3sigma['加成率'].isnull())
#     ].copy()
#
# rows_removed_rule = rows_before_rule - len(cleaned_sales_data)
# print(f"根据“加成率 > 2”的业务规则，共剔除了 {rows_removed_rule} 条记录。")

# df_info = pd.merge(df1, df4.drop(columns=['单品名称'], errors='ignore'), on='单品编码', how='left')
# final_df = pd.merge(cleaned_sales_data, df_info, on='单品编码', how='left')
# print("最终数据整合完成！")
#
# # --- 步骤 7: 保存结果 ---
# output_filename = 'cleaned_sales_data_final.csv'
# final_df.to_csv(output_filename, index=False, encoding='utf_8_sig')
# print(f"\n--- 预处理完成！---")
# print(f"所有数据已通过【3σ检验】和【业务规则】清洗，并保存为文件: {output_filename}")
# print("\n最终数据预览（前5条）：")
# print(final_df.head())
