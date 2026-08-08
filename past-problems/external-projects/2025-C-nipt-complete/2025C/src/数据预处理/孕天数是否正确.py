import pandas as pd
import numpy as np

file_path = '../../sources/男胎(孕天).csv'
df = pd.read_csv(file_path)

df['检测日期_dt'] = pd.to_datetime(df['检测日期'].astype(str), errors='coerce')
df['末次月经_dt'] = pd.to_datetime(df['末次月经'], errors='coerce')

df_workable = df.dropna(subset=['检测日期_dt', '末次月经_dt', '孕天']).copy()
print(f"共有 {len(df_workable)} 条记录可用于日期一致性检验。")
df_workable['孕天_验证值'] = (df_workable['检测日期_dt'] - df_workable['末次月经_dt']).dt.days
df_workable['天数差异'] = df_workable['孕天'] - df_workable['孕天_验证值']

TOLERANCE_DAYS = 15
df_errors = df_workable[df_workable['天数差异'].abs() > TOLERANCE_DAYS]
error_indices = df_errors.index  # 获取这些错误记录的索引

if df_errors.empty:
    print(f"【检验通过】: 所有记录的'孕天'数值均在±{TOLERANCE_DAYS}天的容差范围内，无需修正。")
else:
    print(f"【发现不一致】: 共找到 {len(df_errors)} 条记录的'孕天'与日期差值的差异超过了 {TOLERANCE_DAYS} 天！")
    print("以下是这些记录在【修正前】的状态：")
    display_cols = [
        '孕妇代码',
        '末次月经',
        '检测日期',
        '孕天',  # 数据中原始的孕天
        '孕天_验证值',  # 我们计算出的验证孕天
        '天数差异'
    ]
    print(df_errors[display_cols].to_string(index=False))
    # 使用.loc和错误记录的索引，将原DataFrame中的'孕天'值替换为我们计算出的'孕天_验证值'
    df.loc[error_indices, '孕天'] = df_errors['孕天_验证值']
    df_after_update = df.loc[error_indices]
    print(df_after_update[['孕妇代码', '末次月经', '检测日期', '孕天']].to_string(index=False))
    df.to_csv('../../sources/男胎(修正).csv', index=False, encoding='utf_8_sig')
