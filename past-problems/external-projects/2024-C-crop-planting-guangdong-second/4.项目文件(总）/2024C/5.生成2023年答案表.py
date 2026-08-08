import pandas as pd

temple=pd.read_csv("preprocessed_data/整理数据/答案总表模板.csv",encoding='gbk')
temple.iloc[:,1:42]=0
zhongzhiqingkuang=pd.read_csv("preprocessed_data/整理数据/Q1/2023年情况总表.CSV",encoding='gbk')
# 将 "种植季次" 为 "单季" 的改为 "第一季"，并重命名列名为 "季度"
zhongzhiqingkuang['种植季次'] =zhongzhiqingkuang['种植季次'].replace('单季', '第一季')
zhongzhiqingkuang.rename(columns={'种植季次': '季度'}, inplace=True)
# 遍历 df2 每一行，更新作物名称列的值
for index, row in temple.iterrows():
    matching_records = zhongzhiqingkuang[(zhongzhiqingkuang['季度'] == row['季度']) & (zhongzhiqingkuang['地块名称'] == row['地块名'])]
    if not matching_records.empty:
        for _, record in matching_records.iterrows():
            temple.at[index, record['作物名称']] = record['种植面积/亩']
print(temple)
temple.to_csv("preprocessed_data/整理数据/Q1/2023/2023_答案表_1.csv",encoding='gbk',index=False)
temple.to_csv("preprocessed_data/整理数据/Q1/2023/2023_答案表_2.csv",encoding='gbk',index=False)