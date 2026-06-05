import pandas as pd
import matplotlib.pyplot as plt
df=pd.read_csv("preprocessed_data/整理数据/Q1/2024-2030可行解数量.CSV")
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
print(df)

# 将第一行作为Q2，第二行作为Q3
df.index = ['问题一第1小问', '问题一第2小问']

# 转置DataFrame
df = df.T

# 绘制折线图
plt.figure(figsize=(10, 6))
plt.plot(df.index, df['问题一第1小问'], marker='o', label='问题一第1小问')
plt.plot(df.index, df['问题一第2小问'], marker='o', label='问题一第2小问')
for i in range(len(df)):
    plt.annotate(f'{df["问题一第1小问"][i]:.2f}', (df.index[i], df["问题一第1小问"][i]), textcoords="offset points", xytext=(0,10), ha='center')
    plt.annotate(f'{df["问题一第2小问"][i]:.2f}', (df.index[i], df["问题一第2小问"][i]), textcoords="offset points", xytext=(0,10), ha='center')

plt.xlabel('年份')
plt.ylabel('可行解数量')
plt.legend()

# 显示图表
plt.grid(True)
plt.savefig("preprocessed_data/整理数据/Q1/2024-2030可行解数量.png")
plt.show()
