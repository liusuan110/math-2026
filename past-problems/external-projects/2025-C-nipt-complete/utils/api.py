# 重命名 DataFrame 表格某一列
origin.rename(columns={'是否打折销售': '是否打折'}, inplace=True)

# 对某一列应用规则
origin['是否退货'] = origin['销售类型'].apply(lambda x: '退货' if x == '退货' else '不退货')

# 转化为 datatime，方便提取
# 可以从 dt 工具箱中拿取 year / month / day 等属性
data['日期'] = pd.to_datetime(data['日期'])
data['年份'] = data['日期'].dt.year

# 分组操作
data.groupby(['单品编码', '年份'])['日期'].nunique().reset_index()

# groupby(...)["Key"].unique()  # 对每个小组计算不重复值的数量
# groupby(...)["Key"].sum()  # 对每个小组求和
# groupby(...)["Key"].size()  # 计算每个小组有多少行
# groupby(...)["Key"].mean() # 对每个小组求平均值

# 这里使用 reset_index() 是为了将分组结果从多级索引转化为单一索引：
