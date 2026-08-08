import pandas as pd
import numpy as np

file_path = '../../sources/女胎(孕天).csv'
df = pd.read_csv(file_path)

df['怀孕次数'] = df['怀孕次数'].replace('≥3', '3').astype(int)
print("已将'怀孕次数'列中的 '≥3' 修正为 3。")

df['检测日期'] = pd.to_datetime(df['检测日期'], format='%Y%m%d', errors='coerce')
df['末次月经'] = pd.to_datetime(df['末次月经'], format='%Y/%m/%d', errors='coerce')

# 基于“检测日期”和“检测孕天”填补缺失的“末次月经”
missing_lmp_mask = df['末次月经'].isnull()
df.loc[missing_lmp_mask, '末次月经'] = df.loc[missing_lmp_mask, '检测日期'] - pd.to_timedelta(df.loc[missing_lmp_mask, '检测孕天'], unit='D')
print(f"根据检测孕天填补了 {missing_lmp_mask.sum()} 条缺失的'末次月经'数据。")

# 校验并修正“末次月经”与“检测孕天”差异大于15天的数据
# 基于“检测孕天”更为可靠的原则，反推修正“末次月经”
calculated_gestational_days = (df['检测日期'] - df['末次月经']).dt.days
discrepancy_mask = np.abs(calculated_gestational_days - df['检测孕天']) > 15
df.loc[discrepancy_mask, '末次月经'] = df.loc[discrepancy_mask, '检测日期'] - pd.to_timedelta(df.loc[discrepancy_mask, '检测孕天'], unit='D')
print(f"修正了 {discrepancy_mask.sum()} 条'末次月经'与'检测孕天'差异大于15天的数据。")

processed_file_path = '../../sources/女胎(修正).csv'
df.to_csv(processed_file_path, index=False, encoding='utf-8-sig')