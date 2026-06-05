import pandas as pd
data=pd.read_csv("preprocessed_data/拆分数据/2023年生产销售情况（附件2.2）.CSV",encoding='gbk')
data=data.iloc[0:107,0:7]
crop=pd.read_excel("preprocessed_data/拆分数据/作物情况（附件1.2）.xlsx")
crop=crop.iloc[0:41,0:3]
crop_name=crop
print(crop_name)
crop_name.to_csv("preprocessed_data/整理数据/作物名称（附件1.2）.CSV",encoding='gbk',index=False)


df1 = data[['地块类型', '种植季次']].drop_duplicates().reset_index(drop=True)
for crop in crop_name['作物名称']:
    df1[crop] = 0

# 根据 df 来对这些属性赋值 0 或 1
for index, row in data.iterrows():
    df1.loc[(df1['地块类型'] == row['地块类型']) & (df1['种植季次'] == row['种植季次']), row['作物名称']] = 1

row_to_copy = df1[(df1['地块类型'] == '普通大棚 ') & (df1['种植季次'] == '第一季')]
new_row = row_to_copy.copy()
print(new_row)
new_row['地块类型'] = '智慧大棚'
df1 = pd.concat([df1, new_row], ignore_index=True)
df1.loc[4,'水稻']=1
print(df1)
df1.to_csv("preprocessed_data/整理数据/土地可种植农作物总表.CSV",encoding='gbk',index=False)