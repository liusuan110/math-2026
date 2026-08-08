import pandas as pd
import numpy as np

input_filename = '../../../sources/男胎(Q2).csv'
output_filename = '../../../sources/男胎(Q2)(添加判断结果).csv'

df = pd.read_csv(input_filename)

def check_accuracy_corrected(row):
    actual_healthy = row['胎儿是否健康']
    if pd.isna(row['染色体的非整倍体']):
        predicted_healthy = '是'
    else:
        predicted_healthy = '否'

    if predicted_healthy == actual_healthy:
        return '准确'
    else:
        return '不准确'

df['是否准确'] = df.apply(check_accuracy_corrected, axis=1)
df.to_csv(output_filename, index=False, encoding='utf-8-sig')