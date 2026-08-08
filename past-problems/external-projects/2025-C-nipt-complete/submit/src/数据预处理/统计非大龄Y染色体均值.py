import pandas as pd

df = pd.read_csv("../../sources/男胎(孕天).csv")
filtered_df = df[df['年龄'] <= 35]
mean_y_concentration = filtered_df['Y染色体浓度'].mean()
print(f"剔除年龄大于35岁的孕妇后，Y染色体浓度的均值为: {mean_y_concentration}")