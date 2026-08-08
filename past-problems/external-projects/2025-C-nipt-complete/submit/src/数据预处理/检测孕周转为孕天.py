import pandas as pd


def convert_gestational_week_to_days(gestational_week):
    """将孕周字符串转换为总天数"""
    gestational_week = str(gestational_week).lower() # 第 210 个样本有大写
    gestational_week = str(gestational_week)
    if 'w+' in gestational_week:
        parts = gestational_week.split('w+')
        weeks = int(parts[0])
        days = int(parts[1])
        return weeks * 7 + days
    elif 'w' in gestational_week:
        # 处理只有周数的情况
        weeks = int(gestational_week.replace('w', ''))
        return weeks * 7

    return None


input_filename = '../../sources/男胎.csv'
output_filename = '../../sources/男胎(孕天).csv'

df = pd.read_csv(input_filename)
df['孕天'] = df['检测孕周'].apply(convert_gestational_week_to_days)
print(df[['检测孕周', '孕天']].head())
df.to_csv(output_filename, index=False, encoding='utf-8-sig')
