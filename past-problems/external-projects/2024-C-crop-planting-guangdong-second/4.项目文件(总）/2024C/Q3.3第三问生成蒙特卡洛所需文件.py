import pandas as pd

for year in range(2024,2031):
    ans_total_sheet=pd.read_csv("preprocessed_data/整理数据/答案总表模板.csv",encoding='gbk')
    ans_total_sheet.to_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年答案表.csv",encoding='gbk',index=False)
    shengchangqingkuang=pd.read_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年生产销售表.csv",encoding='gbk')
    yuqixiaoshou=pd.read_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年农作物预期销量表.csv",encoding='gbk')

    #销量表
    yuqixiaoshou['种植季次'] =yuqixiaoshou['种植季次'].replace('单季', '第一季')
    pivot_df = yuqixiaoshou.pivot_table(index='种植季次', columns='作物名称', values='产量', aggfunc='sum')
    # 重置列索引
    pivot_df.reset_index(inplace=True)
    pivot_df.fillna(0,inplace=True)
    crop_order = yuqixiaoshou[['作物名称', '作物编号']].drop_duplicates().sort_values('作物编号')['作物名称'].tolist()
    pivot_df = pivot_df[['种植季次'] + crop_order]
    pivot_df.to_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年_销量表.csv",encoding='gbk',index=False)


    #单价表
    shengchangqingkuang['种植季次']=shengchangqingkuang['种植季次'].replace('单季','第一季')
    shengchangqingkuang['种植季次'] = shengchangqingkuang['种植季次'].replace('单季', '第一季')
    df_unique = shengchangqingkuang.drop_duplicates(subset=['种植季次', '作物名称'])
    danjia_df = df_unique.pivot(index='种植季次', columns='作物名称', values='确切销售单价/(元/斤)')
    danjia_df = danjia_df.reindex(
        sorted(danjia_df.columns, key=lambda x: shengchangqingkuang[shengchangqingkuang['作物名称'] == x]['作物编号'].values[0]), axis=1)
    danjia_df.fillna(0,inplace=True)
    danjia_df.to_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年_单价表.csv", encoding='gbk', index=False)


    #成本表
    df2=pd.read_csv("preprocessed_data/整理数据/答案总表模板.csv",encoding='gbk')
    df2.fillna(0,inplace=True)
    df1=pd.read_csv(f'preprocessed_data/整理数据/Q3/{year}/{year}年生产销售表.csv',encoding='gbk')
    df1['种植季次']=df1['种植季次'].replace('单季', '第一季')
    df1.rename(columns={'种植季次': '季度'}, inplace=True)
    for index, row in df2.iterrows():
        matching_records = df1[(df1['地块类型'] == row['地块类型']) & (df1['季度'] == row['季度'])]

        for _, record in matching_records.iterrows():
            crop_name = record['作物名称']
            planting_cost = record['种植成本/(元/亩)']

            # 更新 df2 中对应列的数据
            if crop_name in df2.columns:
                df2.at[index, crop_name] = planting_cost

    # 保存更新后的 df2
    df2.to_csv(f'preprocessed_data/整理数据/Q3/{year}/{year}年_成本表.csv', encoding='gbk', index=False)


    #产量表
    df2=pd.read_csv("preprocessed_data/整理数据/答案总表模板.csv",encoding='gbk')
    df2.fillna(0,inplace=True)
    df1=pd.read_csv(f'preprocessed_data/整理数据/Q3/{year}/{year}年生产销售表.csv',encoding='gbk')
    df1['种植季次']=df1['种植季次'].replace('单季', '第一季')
    df1.rename(columns={'种植季次': '季度'}, inplace=True)
    for index, row in df2.iterrows():
        matching_records = df1[(df1['地块类型'] == row['地块类型']) & (df1['季度'] == row['季度'])]
        for _, record in matching_records.iterrows():
            crop_name = record['作物名称']
            mu_chanliang = record['亩产量/斤']

            # 更新 df2 中对应列的数据
            if crop_name in df2.columns:
                df2.at[index, crop_name] = mu_chanliang

    # 保存更新后的 df2
    df2.to_csv(f'preprocessed_data/整理数据/Q3/{year}/{year}年_产量表.csv', encoding='gbk', index=False)