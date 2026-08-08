import pandas as pd

yuqi_2023=pd.read_csv("preprocessed_data/整理数据/Q2/2023/2023年农作物预期销量表.csv",encoding='gbk')
shengchan2023=pd.read_csv("preprocessed_data/整理数据/Q2/2023/2023年生产销售表.csv",encoding='gbk')
yuqi_2023.to_csv("preprocessed_data/整理数据/Q3/2023/2023年农作物预期销量表.csv",encoding='gbk',index=False)
shengchan2023.to_csv("preprocessed_data/整理数据/Q3/2023/2023年生产销售表.csv",encoding='gbk',index=False)
ans_sheet=pd.read_csv("preprocessed_data/整理数据/Q1/2023/2023_答案表_1.csv",encoding='gbk')
ans_sheet.to_csv(f"preprocessed_data/整理数据/Q3/2023/2023年答案表.csv",encoding='gbk',index=False)
for year in range(2024,2031):
    shengchan=pd.read_csv(f"preprocessed_data/整理数据/Q2/{year}/{year}年生产销售表.csv",encoding='gbk')
    shengchan.to_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年生产销售表.csv",encoding='gbk',index=False)