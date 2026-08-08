import pandas as pd
import matplotlib.pyplot as plt
data=pd.read_csv("preprocessed_data/整理数据/2023年生产销售表(附件2.2).csv",encoding='gbk')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
# 按作物名称和地块类型分组，计算平均值
grouped =data.groupby(['作物名称', '地块类型']).mean().reset_index()
print(grouped)
grouped.to_csv("preprocessed_data/整理数据/Q1/农作物在不同地块类型的生产情况.csv",encoding='gbk',index=False)
