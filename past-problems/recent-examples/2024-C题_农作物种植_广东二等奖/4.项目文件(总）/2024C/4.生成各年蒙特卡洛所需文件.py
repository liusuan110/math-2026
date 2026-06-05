import pandas as pd
import cvxpy
ans_sheet=pd.read_excel("preprocessed_data/拆分数据/答案表格.xlsx")
ans_sheet=ans_sheet.iloc[0:82,1:]

#增加季度属性
# 找到第一个 'F4' 的索引
index_F4 = ans_sheet[ans_sheet['地块名'] == 'F4'].index[0]
# 在第一个 'F4' 之前的行（包含 'F4'）设为 '第一季'
ans_sheet.loc[:index_F4, '季度'] = '第一季'
# 在第一个 'F4' 之后的行设为 '第二季'
ans_sheet.loc[index_F4+1:, '季度'] = '第二季'


#增加亩数和土地类型属性
gengdi=pd.read_csv("preprocessed_data/整理数据/耕地名称-亩数.csv",encoding='gbk')
gengdi_new=gengdi.rename(columns={'地块名称': '地块名'},inplace=False)
ans_total_sheet=pd.merge(ans_sheet,gengdi_new,on='地块名',how='left')


#增加没有种植豆类年数属性
ans_total_sheet.loc[:,'没有种植豆类年数']=0

ans_total_sheet.to_csv("preprocessed_data/整理数据/答案总表模板.csv",encoding='gbk',index=False)
shengchangqingkuang=pd.read_csv("preprocessed_data/整理数据/Q1/2023年生产销售表.csv",encoding='gbk')
yuqixiaoshou=pd.read_csv("preprocessed_data/整理数据/Q1/2023年农作物预期销量表.csv",encoding='gbk')


for year in range(2024,2031):
    ans_total_sheet.to_csv(f"preprocessed_data/整理数据/Q1/{year}/{year}_答案表_1.csv",encoding='gbk',index=False)
    ans_total_sheet.to_csv(f"preprocessed_data/整理数据/Q1/{year}/{year}_答案表_2.csv", encoding='gbk', index=False)
    shengchangqingkuang.to_csv(f"preprocessed_data/整理数据/Q1/{year}/{year}_生产销售表.csv",encoding='gbk',index=False)
    yuqixiaoshou.to_csv(f"preprocessed_data/整理数据/Q1/{year}/{year}_预期销量表.csv",encoding='gbk',index=False)

    #销量表
    yuqixiaoshou['种植季次'] =yuqixiaoshou['种植季次'].replace('单季', '第一季')
    pivot_df = yuqixiaoshou.pivot_table(index='种植季次', columns='作物名称', values='产量', aggfunc='sum')
    pivot_df.reset_index(inplace=True)
    pivot_df.fillna(0,inplace=True)
    crop_order = yuqixiaoshou[['作物名称', '作物编号']].drop_duplicates().sort_values('作物编号')['作物名称'].tolist()
    pivot_df = pivot_df[['种植季次'] + crop_order]
    pivot_df.to_csv(f"preprocessed_data/整理数据/Q1/{year}/{year}_销量表.csv",encoding='gbk',index=False)


    #单价表
    shengchangqingkuang['种植季次']=shengchangqingkuang['种植季次'].replace('单季','第一季')
    shengchangqingkuang['种植季次'] = shengchangqingkuang['种植季次'].replace('单季', '第一季')
    df_unique = shengchangqingkuang.drop_duplicates(subset=['种植季次', '作物名称'])
    danjia_df = df_unique.pivot(index='种植季次', columns='作物名称', values='销售单价/(元/斤)')
    danjia_df = danjia_df.reindex(
        sorted(danjia_df.columns, key=lambda x: shengchangqingkuang[shengchangqingkuang['作物名称'] == x]['作物编号'].values[0]), axis=1)
    # 定义一个函数来计算区间的平均值
    def calculate_average(value):
        if isinstance(value, str) and '-' in value:
            low, high = map(float, value.split('-'))
            return (low + high) / 2
        return value
    # 应用函数到 DataFrame 的每个元素
    danjia_df = danjia_df.applymap(calculate_average)
    danjia_df.fillna(0,inplace=True)
    danjia_df.to_csv(f"preprocessed_data/整理数据/Q1/{year}/{year}_单价表.csv", encoding='gbk', index=False)


    #成本表
    df2=pd.read_csv("preprocessed_data/整理数据/答案总表模板.csv",encoding='gbk')
    df2.fillna(0,inplace=True)
    df1=pd.read_csv(f'preprocessed_data/整理数据/Q1/{year}/{year}_生产销售表.csv',encoding='gbk')
    df1['种植季次']=df1['种植季次'].replace('单季', '第一季')
    df1.rename(columns={'种植季次': '季度'}, inplace=True)
    for index, row in df2.iterrows():

        matching_records = df1[(df1['地块类型'] == row['地块类型']) & (df1['季度'] == row['季度'])]
        for _, record in matching_records.iterrows():
            crop_name = record['作物名称']
            planting_cost = record['种植成本/(元/亩)']
            if crop_name in df2.columns:
                df2.at[index, crop_name] = planting_cost

    # 保存更新后的 df2
    df2.to_csv(f'preprocessed_data/整理数据/Q1/{year}/{year}_成本表.csv', encoding='gbk', index=False)


    #产量表
    df2=pd.read_csv("preprocessed_data/整理数据/答案总表模板.csv",encoding='gbk')
    df2.fillna(0,inplace=True)
    df1=pd.read_csv(f'preprocessed_data/整理数据/Q1/{year}/{year}_生产销售表.csv',encoding='gbk')
    df1['种植季次']=df1['种植季次'].replace('单季', '第一季')
    df1.rename(columns={'种植季次': '季度'}, inplace=True)
    for index, row in df2.iterrows():
        matching_records = df1[(df1['地块类型'] == row['地块类型']) & (df1['季度'] == row['季度'])]
        for _, record in matching_records.iterrows():
            crop_name = record['作物名称']
            mu_chanliang = record['亩产量/斤']
            if crop_name in df2.columns:
                df2.at[index, crop_name] = mu_chanliang

    # 保存更新后的 df2
    df2.to_csv(f'preprocessed_data/整理数据/Q1/{year}/{year}_产量表.csv', encoding='gbk', index=False)



