import pandas as pd
gengdi=pd.read_excel("preprocessed_data/拆分数据/耕地情况(附件1.1）.xlsx")
gengdi=gengdi.iloc[:,0:3]
gengdi.to_csv("preprocessed_data/整理数据/耕地名称-亩数.csv",encoding='gbk',index=False)
gengdi=pd.read_csv("preprocessed_data/整理数据/耕地名称-亩数.csv",encoding='gbk')
gengdi.loc[:,'种植地块']=gengdi.iloc[:,0]

zhongzhi=pd.read_csv("preprocessed_data/拆分数据/2023年种植情况（附件2.1）.CSV",encoding='gbk')
# 使用 ffill 方法填充空值
zhongzhi['种植地块'] =zhongzhi['种植地块'].fillna(method='ffill')
zhongzhi.to_csv("preprocessed_data/整理数据/2023年种植情况(附件2.1).CSV",encoding='gbk',index=False)
new_df=pd.merge(gengdi,zhongzhi,on='种植地块')



shengchangxiaoshou=pd.read_csv("preprocessed_data/拆分数据/2023年生产销售情况（附件2.2）.CSV",encoding='gbk')
shengchangxiaoshou=shengchangxiaoshou.iloc[0:107,:]
#更新生产销售情况
# 找到地块类型为“普通大棚”且种植季次为“第一季”的数据
rows_to_copy = shengchangxiaoshou[(shengchangxiaoshou['地块类型'] == '普通大棚 ') & (shengchangxiaoshou['种植季次'] == '第一季')]

new_rows = rows_to_copy.copy()
# 修改地块类型为“智慧大棚”
new_rows['地块类型'] = '智慧大棚'
# 将新数据添加到 df 中
shengchangxiaoshou = pd.concat([shengchangxiaoshou, new_rows], ignore_index=True)
shengchangxiaoshou=shengchangxiaoshou.iloc[:,:-2]

# 计算确切销售单价
shengchangxiaoshou['确切销售单价/(元/斤)'] = shengchangxiaoshou['销售单价/(元/斤)'].apply(lambda x: (float(x.split('-')[0]) + float(x.split('-')[1])) / 2)

# 计算亩利润
shengchangxiaoshou['亩利润/(元/亩)'] = shengchangxiaoshou['亩产量/斤'] * shengchangxiaoshou['确切销售单价/(元/斤)'] - shengchangxiaoshou['种植成本/(元/亩)']

shengchangxiaoshou.to_csv("preprocessed_data/整理数据/2023年生产销售表(附件2.2).csv",encoding='gbk')
shengchangxiaoshou.to_csv("preprocessed_data/整理数据/Q1/2023年生产销售表.csv",encoding='gbk',index=False)

new_df.to_csv("preprocessed_data/整理数据/Q1/2023年种植-土地情况.CSV",encoding='gbk',index=False)
# 将需要合并的列转换为相同类型
new_df['作物编号'] = new_df['作物编号'].astype(str)
shengchangxiaoshou['作物编号'] = shengchangxiaoshou['作物编号'].astype(str)

total_df=pd.merge(new_df,shengchangxiaoshou,on=['作物名称','地块类型','种植季次','作物编号'])

# 计算每一组中的“产量”值
total_df['产量'] = total_df['种植面积/亩'] * total_df['亩产量/斤']
total_df.to_csv("preprocessed_data/整理数据/Q1/2023年情况总表.CSV",encoding='gbk',index=False)

# 按照作物名称和种植季次来分组，统计产量
grouped_df = total_df.groupby(['作物名称', '种植季次']).agg({'产量': 'sum'}).reset_index()

# 将作物编号添加到新的 DataFrame 中
grouped_df = grouped_df.merge(total_df[['作物名称', '作物编号']].drop_duplicates(), on='作物名称', how='left')


look_data=pd.read_csv("preprocessed_data/整理数据/Q1/2023年生产销售表.csv",encoding='gbk')
look_data['作物编号']=look_data['作物编号'].astype(int)
grouped_df['作物编号']=grouped_df['作物编号'].astype(int)
# 检查作物编号在 [17, 34] 之间的记录
for crop_id in range(17, 35):
    if not ((grouped_df['作物编号'] == crop_id) & (grouped_df['种植季次'] == '第二季')).any():
        # 查找对应的亩产量
        yield_per_acre = look_data[(look_data['作物编号'] == crop_id) & (look_data['种植季次'] == '第二季')]['亩产量/斤'].values[0]
        # 计算新的产量
        new_yield = yield_per_acre * 0.3
        # 获取作物名称
        crop_name = grouped_df[grouped_df['作物编号'] == crop_id]['作物名称'].values[0]
        # 增加新的记录
        new_record = {'作物编号': crop_id, '作物名称': crop_name, '种植季次': '第二季',  '产量': new_yield}
        grouped_df = grouped_df.append(new_record, ignore_index=True)

# 按作物编号升序排序
grouped_df = grouped_df.sort_values(by=['作物编号','种植季次']).reset_index(drop=True)

print(grouped_df)
#
grouped_df.to_csv("preprocessed_data/整理数据/Q1/2023年农作物预期销量表.csv",encoding='gbk',index=False)