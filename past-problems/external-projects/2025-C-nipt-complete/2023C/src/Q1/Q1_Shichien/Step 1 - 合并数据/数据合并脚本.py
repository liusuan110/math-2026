import pandas as pd

item_class_csv = '../../../../sources/附件1.csv' # 物品分类表格
sale_csv = '../../../../sources/附件2.csv' # 物品销售表格
output_file = 'merged_sales_data.csv'

# 使用 UTF-8 编码读取文件，确保中文显示正常
df_sales = pd.read_csv(item_class_csv, encoding='utf-8')
df_items = pd.read_csv(sale_csv, encoding='gbk') # 从 Excel 转化来的是 GBK 编码的

# 2. 基于“单品编码”合并两个 DataFrame
merged_df = pd.merge(df_sales, df_items, on='单品编码', how='left') # left 方案会保留其他的数据

# index=False 表示不将 DataFrame 的索引写入文件
merged_df.to_csv(output_file, index=False, encoding='utf-8')