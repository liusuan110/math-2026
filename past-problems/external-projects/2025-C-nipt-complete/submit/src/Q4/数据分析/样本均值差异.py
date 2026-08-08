import pandas as pd

# 设置pandas显示选项，以便更清晰地查看表格
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# 加载数据
df = pd.read_csv('../../../sources/女胎(有效特征修正版).csv')

# 按'是否异常'分组
grouped = df.groupby('是否异常')

# 分别获取正常(0)和异常(1)组的描述性统计数据
stats_normal = grouped.get_group(0).describe()
stats_abnormal = grouped.get_group(1).describe()

# 将我们关心的统计量（均值、标准差、中位数）合并到一个DataFrame中
comparison_df = pd.DataFrame({
    '正常样本-均值': stats_normal.loc['mean'],
    '异常样本-均值': stats_abnormal.loc['mean'],
    '正常样本-标准差': stats_normal.loc['std'],
    '异常样本-标准差': stats_abnormal.loc['std'],
    '正常样本-中位数': stats_normal.loc['50%'],
    '异常样本-中位数': stats_abnormal.loc['50%']
}).drop(['序号','检测抽血次数']) # 移除不太关心的行

print("--- 正常样本 vs 异常样本统计数据对比 ---")
# 使用.round(4)让输出的数字更易读
print(comparison_df.round(4))