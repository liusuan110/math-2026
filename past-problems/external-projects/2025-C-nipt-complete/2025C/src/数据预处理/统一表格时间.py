import pandas as pd

df = pd.read_csv("../../sources/男胎(孕天).csv")

df['检测日期'] = pd.to_datetime(df['检测日期'], format='%Y%m%d').dt.strftime('%Y/%m/%d')
df['末次月经'] = pd.to_datetime(df['末次月经']).dt.strftime('%Y/%m/%d')
df.to_csv('男胎(孕天).csv', index=False, encoding='utf_8_sig')