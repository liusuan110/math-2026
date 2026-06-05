import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import shapiro, normaltest
df=pd.read_csv("preprocessed_data/整理数据/Q1/2024实验-利润.CSV")
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题

# 将第一行作为Q2，第二行作为Q3
df.index = ['利润']

# 转置DataFrame
df = df.T
# 计算平均值
mean_profit = df['利润'].mean()
print(f"平均值: {mean_profit}")

# 计算方差
variance_profit = df['利润'].var()
print(f"方差: {variance_profit}")

# 计算标准差
std_dev_profit = df['利润'].std()
print(f"标准差: {std_dev_profit}")

# 计算中位数
median_profit = df['利润'].median()
print(f"中位数: {median_profit}")

# 计算最大值
max_profit = df['利润'].max()
print(f"最大值: {max_profit}")

# 计算最小值
min_profit = df['利润'].min()
print(f"最小值: {min_profit}")

# 使用Shapiro-Wilk检验
stat, p = shapiro(df['利润'])
print(f'Shapiro-Wilk检验统计量: {stat}, p值: {p}')

# 判断是否符合正态分布
alpha = 0.05
if p > alpha:
    print('数据符合正态分布 (接受H0假设)')
else:
    print('数据不符合正态分布 (拒绝H0假设)')
# # 打印某一列的信息
# print(df['利润'].describe())
# 绘制折线图
plt.figure(figsize=(10, 6))
plt.plot(df.index, df['利润'], marker='o', label='利润')
for i in range(len(df)):
    plt.annotate(f'{df["利润"][i]:.2f}', (df.index[i], df["利润"][i]), textcoords="offset points", xytext=(0,10), ha='center')

plt.xlabel('实验次数')
plt.ylabel('利润')
plt.legend()

# 显示图表
plt.grid(True)
plt.savefig("preprocessed_data/整理数据/Q1/2024实验-利润.png")
plt.show()