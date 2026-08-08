import pandas as pd
import numpy as np

df = pd.read_csv("../../sources/男胎.csv")

height_in_meters = df['身高'] / 100
df['计算出的BMI'] = df['体重'] / (height_in_meters ** 2)

tolerance = 0.01
incorrect_bmi_rows = df[np.abs(df['孕妇BMI'] - df['计算出的BMI']) > tolerance]

print(f"检测到 {len(incorrect_bmi_rows)} 条可能计算错误的BMI记录：")
print(incorrect_bmi_rows[['序号', '身高', '体重', '孕妇BMI', '计算出的BMI']])
