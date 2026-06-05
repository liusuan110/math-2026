import pandas as pd
yuqi2023=pd.read_csv("preprocessed_data/整理数据/Q1/2023年农作物预期销量表.csv",encoding='gbk')
shengchang2023=pd.read_csv("preprocessed_data/整理数据/2023年生产销售表(附件2.2).csv",encoding='gbk')
yuqi2023.to_csv("preprocessed_data/整理数据/Q2/2023/2023年农作物预期销量表.csv",encoding='gbk',index=False)
shengchang2023.to_csv("preprocessed_data/整理数据/Q2/2023/2023年生产销售表.csv",encoding='gbk',index=False)
ans_sheet=pd.read_csv("preprocessed_data/整理数据/Q1/2023/2023_答案表_1.csv",encoding='gbk')
ans_sheet.to_csv("preprocessed_data/整理数据/Q2/2023/2023年答案表.csv",encoding='gbk',index=False)