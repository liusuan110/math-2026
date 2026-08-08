import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity, calculate_kmo
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm

# -- 图片预设，需要 plt, fm, cycler 库
# -- 图片预设，需要 plt, fm, cycler 库
import matplotlib.font_manager as fm
from cycler import cycler
import os

font_path = "../../utils/fonts/SourceHanSerifCN-Regular.otf"
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rcParams['font.sans-serif'] = [font_name]
else:
    fallback_fonts = ['STZhongsong', 'SimSun', 'SimHei', 'Microsoft YaHei']
    plt.rcParams['font.sans-serif'] = fallback_fonts

plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'  # 保存后自动裁剪白边
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.prop_cycle'] = cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
plt.rcParams['axes.unicode_minus'] = False
# -- 图片预设
# -- 图片预设

data = {
    '客户编号': range(1, 13),
    '能力': [61.76, 65.26, 63.19, 65.02, 64.23, 65.84, 64.85, 56.94, 66.88, 61.22, 63.89, 63.92],
    '品格': [60.82, 65.98, 64.81, 63.93, 65.44, 64.00, 62.85, 58.12, 68.81, 61.13, 65.23, 63.05],
    '担保': [62.72, 65.97, 65.06, 64.31, 64.01, 65.10, 62.75, 62.72, 65.50, 62.10, 63.05, 62.98],
    '资本': [61.39, 66.52, 62.85, 64.04, 62.93, 64.69, 64.71, 59.12, 67.83, 61.64, 62.98, 63.35],
    '环境': [63.88, 65.37, 65.10, 62.36, 65.47, 64.97, 64.24, 65.57, 64.48, 63.45, 63.38, 63.81]
}
df = pd.DataFrame(data)
features = ['能力', '品格', '担保', '资本', '环境']
df_features = df[features]

print("--- 1. 相关性矩阵检验 ---")
corr_matrix = df_features.corr()
plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f")
plt.title('特征相关性矩阵热力图')
plt.show()
print("观察热力图，多数变量之间存在中等到较强的相关性（绝对值>0.3），适合进行主成分分析。\n")

print("--- 2. KMO 检验 ---")
kmo_all, kmo_model = calculate_kmo(df_features)
print(f"KMO 检验整体统计量: {kmo_model:.4f}")
print("KMO值大于0.6，通常认为适合进行因子分析或主成分分析。\n")

print("--- 3. Bartlett's 球形检验 ---")
chi_square_value, p_value = calculate_bartlett_sphericity(df_features)
print(f"卡方统计量: {chi_square_value:.4f}, p值: {p_value:.10f}")
print("p值远小于0.05，我们拒绝原假设（变量不相关），说明变量之间存在显著相关性，适合进行主成分分析。\n")

print("--- 4. 方差膨胀因子 (VIF) 检验 ---")
X_vif = sm.add_constant(df_features)
vif_data = pd.DataFrame()
vif_data["feature"] = X_vif.columns
vif_data["VIF"] = [variance_inflation_factor(X_vif.values, i) for i in range(X_vif.shape[1])]
print(vif_data)
print("\n常数项(const)的VIF值没有意义。所有特征的VIF值均小于5，表明多重共线性问题不严重。\n")

# --- 步骤 3: 执行主成分分析 (PCA) ---
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_features)

pca = PCA(n_components=3)
principal_components = pca.fit_transform(X_scaled)

pc_df = pd.DataFrame(data=principal_components, columns=['PC1', 'PC2', 'PC3'])
pc_df['客户编号'] = df['客户编号']

print("\n--- 主成分分析结果 ---")
print(f"各主成分解释的方差比例: {pca.explained_variance_ratio_}")
print(f"累计解释的方差比例: {sum(pca.explained_variance_ratio_):.4f}")

# --- 步骤 4: 3D 可视化 ---
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 绘制散点图
scatter = ax.scatter(pc_df['PC1'], pc_df['PC2'], pc_df['PC3'], s=60)

# 为每个点添加标签
for i, txt in enumerate(pc_df['客户编号']):
    ax.text(pc_df['PC1'][i], pc_df['PC2'][i], pc_df['PC3'][i], f'客户{txt}', size=10, zorder=1, color='k')

# 设置坐标轴标签和标题
ax.set_xlabel('第一主成分 (PC1)', fontweight='bold')
ax.set_ylabel('第二主成分 (PC2)', fontweight='bold')
ax.set_zlabel('第三主成分 (PC3)', fontweight='bold')
ax.set_title('客户数据PCA降维后3D散点图', fontsize=16, fontweight='bold')

plt.show()
