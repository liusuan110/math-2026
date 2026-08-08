import pandas as pd

file_path_1 = '../../../sources/附件1.csv'
file_path_3 = '../../../sources/附件3.csv'

df1 = pd.read_csv(file_path_1)
df3 = pd.read_csv(file_path_3)

merged = pd.merge(df1, df3, on=['单品编码'], how='left')  # Left 方案可以保留其他信息，最常用
merged.to_csv("附件3(带品类名).csv", index=False, encoding='utf_8_sig')