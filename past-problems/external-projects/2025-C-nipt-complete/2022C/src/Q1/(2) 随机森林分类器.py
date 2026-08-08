import pandas as pd
import io
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Set Matplotlib to use a font that supports Chinese characters
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

csv_data = """文物采样点,二氧化硅(SiO2),氧化钠(Na2O),氧化钾(K2O),氧化钙(CaO),氧化镁(MgO),氧化铝(Al2O3),氧化铁(Fe2O3),氧化铜(CuO),氧化铅(PbO),氧化钡(BaO),五氧化二磷(P2O5),氧化锶(SrO),氧化锡(SnO2),二氧化硫(SO2),纹饰,类型,颜色,表面风化
8,20.14,0.04,0.04,1.48,0.04,1.34,0.04,10.41,28.68,31.23,3.59,0.37,0.04,2.58,C,铅钡,紫,风化
08严重风化点,4.61,0.04,0.04,3.19,0.04,1.11,0.04,3.14,32.45,30.62,7.56,0.53,0.04,15.03,C,铅钡,紫,风化
26,19.79,0.04,0.04,1.44,0.04,0.7,0.04,10.57,29.53,32.25,3.13,0.45,0.04,1.96,C,铅钡,紫,风化
26严重风化点,3.72,0.04,0.4,3.01,0.04,1.18,0.04,3.6,29.92,35.45,6.04,0.62,0.04,15.95,C,铅钡,紫,风化
28未风化点,68.08,0.04,0.26,1.34,1.0,4.7,0.41,0.33,17.14,4.04,1.04,0.12,0.23,0.04,A,铅钡,浅蓝,未风化
29未风化点,63.3,0.92,0.3,2.98,1.49,14.34,0.81,0.74,12.31,2.03,0.41,0.25,0.04,0.04,A,铅钡,浅蓝,未风化
42未风化点1,51.26,5.74,0.15,0.79,1.09,3.53,0.04,2.67,21.88,10.47,0.08,0.35,0.04,0.04,A,铅钡,浅蓝,未风化
42未风化点2,51.33,5.68,0.35,0.04,1.16,5.66,0.04,2.72,20.12,10.88,0.04,0.04,0.04,0.04,A,铅钡,浅蓝,未风化
44未风化点,60.74,3.06,0.2,2.14,0.04,12.69,0.77,0.43,13.61,5.22,0.04,0.26,0.04,0.04,A,铅钡,浅蓝,未风化
49,28.79,0.04,0.04,4.58,1.47,5.38,2.74,0.7,34.18,6.1,11.1,0.46,0.04,0.04,A,铅钡,黑,风化
49未风化点,54.61,0.04,0.3,2.08,1.2,6.5,1.27,0.45,23.02,4.19,4.32,0.3,0.04,0.04,A,铅钡,黑,未风化
50,17.98,0.04,0.04,3.19,0.47,1.87,0.33,1.13,44.0,14.2,6.34,0.66,0.04,0.04,A,铅钡,黑,风化
50未风化点,45.02,0.04,0.04,3.12,0.54,4.16,0.04,0.7,30.61,6.22,6.34,0.23,0.04,0.04,A,铅钡,黑,未风化
52,25.74,1.22,0.04,2.27,0.55,1.16,0.23,0.7,47.42,8.64,5.71,0.44,0.04,0.04,C,铅钡,浅蓝,风化
53未风化点,63.66,3.04,0.11,0.78,1.14,6.06,0.04,0.54,13.66,8.99,0.04,0.27,0.04,0.04,A,铅钡,浅蓝,未风化
"""

df = pd.read_csv(io.StringIO(csv_data))

# Step 1: Preprocessing
df['风化与否'] = df['表面风化'].apply(lambda x: '未风化' if x == '未风化' else '风化')
y = df['风化与否']

# Identify chemical component columns
chemical_cols = ['氧化钠(Na2O)','氧化钾(K2O)','氧化钙(CaO)','氧化镁(MgO)','氧化铝(Al2O3)','氧化铁(Fe2O3)','氧化铜(CuO)','氧化铅(PbO)','氧化钡(BaO)','五氧化二磷(P2O5)','氧化锶(SrO)','氧化锡(SnO2)','二氧化硫(SO2)']
X_raw = df[chemical_cols]

# Step 2: CLR Transformation
# Handle zeros by replacing them with a small value
X_imputed = X_raw.replace(0, 0.01)

# Calculate geometric mean for each row
g_mean = np.exp(np.mean(np.log(X_imputed), axis=1))

# Apply CLR transformation
X_clr = np.log(X_imputed.div(g_mean, axis=0))
print("CLR 变换后的数据 (前5行):")
print(X_clr.head())

# Step 3: Re-analysis on CLR-transformed data
# Descriptive Statistics
clr_df_with_weathering = pd.concat([X_clr, y], axis=1)
clr_comparison = clr_df_with_weathering.groupby('风化与否').mean()
print("\n按风化与否分组的CLR变换后化学成分平均值:")
print(clr_comparison)


# Visualization of CLR-transformed data
# Let's select a few components that show significant differences in the mean CLR values
# Based on the new mean table, P2O5, SO2, PbO, BaO seem interesting.
key_components_clr = ['五氧化二磷(P2O5)', '二氧化硫(SO2)', '氧化铅(PbO)', '氧化钡(BaO)']

plt.figure(figsize=(15, 10))
for i, component in enumerate(key_components_clr, 1):
    plt.subplot(2, 2, i)
    sns.boxplot(x='风化与否', y=component, data=clr_df_with_weathering)
    plt.title(f'CLR变换后 {component} 与风化关系')
    plt.ylabel('CLR 值')
plt.tight_layout()
plt.savefig("clr_weathering_comparison.png")
print("\n已生成CLR变换后风化与化学成分含量对比图: clr_weathering_comparison.png")

# Feature Importance using RandomForest on CLR data
le = LabelEncoder()
y_encoded = le.fit_transform(y)

model_clr = RandomForestClassifier(random_state=42)
model_clr.fit(X_clr, y_encoded)

importances_clr = model_clr.feature_importances_
feature_importance_clr_df = pd.DataFrame({'特征': X_clr.columns, '重要性': importances_clr})
feature_importance_clr_df = feature_importance_clr_df.sort_values(by='重要性', ascending=False)

print("\n使用CLR变换数据预测风化与否的特征重要性排序:")
print(feature_importance_clr_df)

# Plot feature importances
plt.figure(figsize=(12, 8))
sns.barplot(x='重要性', y='特征', data=feature_importance_clr_df)
plt.title('使用CLR变换数据预测风化与否的特征重要性')
plt.savefig("clr_feature_importances.png")
print("\n已生成CLR变换后特征重要性图: clr_feature_importances.png")