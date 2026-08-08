import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

file_path = '../../sources/男胎(孕天).csv'
df = pd.read_csv(file_path)

numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
cols_to_exclude_for_analysis = ['序号', 'Y染色体浓度']  # 移除ID和因变量，保留所有潜在的自变量
variables_for_analysis = [col for col in numeric_cols if col not in cols_to_exclude_for_analysis]
df_analysis = df[variables_for_analysis]

print("VIF值越大，表示该变量与其他变量的共线性越强。")
print("通常认为VIF > 10时，该变量存在严重的多重共线性。")

# VIF的计算需要一个常数项
X_vif = sm.add_constant(df_analysis.reset_index(drop=True))

vif_data = pd.DataFrame()
vif_data["Variable"] = X_vif.columns
vif_data["VIF"] = [variance_inflation_factor(X_vif.values, i) for i in range(X_vif.shape[1])]
vif_data = vif_data[vif_data['Variable'] != 'const']
vif_data_sorted = vif_data.sort_values(by='VIF', ascending=False)

print("\n各变量的方差膨胀因子 (VIF) 如下:")
print(vif_data_sorted)
