import pandas as pd
import matplotlib.pyplot as plt
df=pd.read_csv("preprocessed_data/整理数据/Q3/Q2Q3对比.CSV")
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
print(df)

# 将第一行作为Q2，第二行作为Q3
df.index = ['Q2', 'Q3']

# 转置DataFrame
df = df.T

# 绘制折线图
plt.figure(figsize=(10, 6))
plt.plot(df.index, df['Q2'], marker='o', label='Q2')
plt.plot(df.index, df['Q3'], marker='o', label='Q3')
for i in range(len(df)):
    plt.annotate(f'{df["Q2"][i]:.2f}', (df.index[i], df["Q2"][i]), textcoords="offset points", xytext=(0,10), ha='center')
    plt.annotate(f'{df["Q3"][i]:.2f}', (df.index[i], df["Q3"][i]), textcoords="offset points", xytext=(0,10), ha='center')

plt.xlabel('年份')
plt.ylabel('总利润')
plt.legend()

# 显示图表
plt.grid(True)
plt.savefig("preprocessed_data/整理数据/Q3/Q2Q3对比.png")
plt.show()
