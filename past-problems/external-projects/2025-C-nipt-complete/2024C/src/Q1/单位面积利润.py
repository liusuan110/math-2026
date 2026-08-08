import pandas as pd

df_economics = pd.read_csv('../../sources/亩产量、种植成本、销售单价.csv')

# '销售单价/(元/斤)' 列的格式是 '最低价-最高价'
price_range = df_economics['销售单价/(元/斤)'].str.split('-', expand=True).astype(float)
df_economics['平均价格'] = price_range.mean(axis=1)
df_economics['每亩利润'] = df_economics['亩产量/斤'] * df_economics['平均价格'] - df_economics['种植成本/(元/亩)']

df_economics['平均价格'] = df_economics['平均价格'].round(2)
df_economics['每亩利润'] = df_economics['每亩利润'].round(2)
df_economics.to_csv('../../sources/每亩利润.csv', index=False, encoding='utf-8-sig')