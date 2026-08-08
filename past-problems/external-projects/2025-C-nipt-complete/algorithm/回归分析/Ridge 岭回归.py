import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import io

# -- 图片预设，需要 plt, fm, cycler 库
import matplotlib.font_manager as fm
from cycler import cycler

fm.fontManager.addfont('../../utils/fonts/SourceHanSerifCN-Regular.otf')  # 添加字体
font_name = fm.FontProperties(fname='../../utils/fonts/SourceHanSerifCN-Regular.otf').get_name()
plt.rcParams['font.sans-serif'] = [font_name]
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

# --- 1. 创建并加载数据 ---
# 为了方便演示，我们直接在代码中创建CSV数据
# 在实际应用中，您会使用 pd.read_csv('house_prices.csv') 来读取文件
csv_data = """size_sqft,bedrooms,age,crime_rate,price
1500,3,10,0.5,300000
1600,3,5,0.4,350000
1450,3,15,0.6,280000
2000,4,8,0.3,450000
1800,3,12,0.55,380000
2200,4,3,0.2,500000
2100,4,6,0.25,480000
1700,3,20,0.7,320000
2500,5,2,0.1,600000
1300,2,25,0.8,250000
1900,4,9,0.45,420000
2300,4,7,0.35,510000
1550,3,11,0.52,310000
2050,4,7,0.33,465000
1750,3,18,0.65,340000
"""

df = pd.read_csv(io.StringIO(csv_data))

# --- 2. 特征相关性热力图 (Heatmap) ---
# 这是建模前的重要步骤，用来观察特征间的相关性
plt.figure(figsize=(10, 8))
sns.heatmap(df.corr(), annot=True, cmap='coolwarm', fmt=".2f")
plt.title('Feature Correlation Heatmap')
plt.show()

# --- 3. 数据准备 ---
# 定义特征 (X) 和目标 (y)
X = df[['size_sqft', 'bedrooms', 'age', 'crime_rate']]
y = df['price']

# 数据标准化：正则化模型通常需要标准化来保证所有特征在同一尺度上
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# --- 4. 训练岭回归模型 ---
# 选择一个alpha值，alpha是正则化强度的超参数
alpha_val = 1.0
ridge_model = Ridge(alpha=alpha_val)

# 训练模型
ridge_model.fit(X_train, y_train)

# --- 5. 模型评估 ---
# 在测试集上进行预测
y_pred = ridge_model.predict(X_test)

# 计算均方误差 (MSE)
mse = mean_squared_error(y_test, y_pred)
print(f"模型的系数 (Coefficients): {ridge_model.coef_}")
print(f"模型的截距 (Intercept): {ridge_model.intercept_:.2f}")
print(f"在测试集上的均方误差 (MSE): {mse:.2f}")
print("-" * 30)

# --- 6. 岭回归相关图表 ---

# 图表一：真实值 vs. 预测值
plt.figure(figsize=(8, 8))
plt.scatter(y_test, y_pred, alpha=0.7)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], '--r', linewidth=2)
plt.xlabel('Actual Prices')
plt.ylabel('Predicted Prices')
plt.title('Actual vs. Predicted Prices')
plt.grid(True)
plt.show()

# 图表二：残差图 (Residuals Plot)
# 残差 = 真实值 - 预测值
residuals = y_test - y_pred
plt.figure(figsize=(10, 6))
plt.scatter(y_pred, residuals)
plt.axhline(y=0, color='r', linestyle='--')
plt.xlabel('Predicted Values')
plt.ylabel('Residuals')
plt.title('Residuals vs. Predicted Values')
plt.grid(True)
plt.show()

# 图表三：岭迹图 (Ridge Trace) - 系数随 alpha 变化的曲线
# 这是岭回归中最重要的图表
print("正在生成岭迹图...")
# 创建一系列的 alpha 值
alphas = np.logspace(-4, 4, 100)
coefs = []
feature_names = X.columns

for a in alphas:
    ridge = Ridge(alpha=a)
    ridge.fit(X_scaled, y)  # 使用全部数据来观察系数变化趋势
    coefs.append(ridge.coef_)

plt.figure(figsize=(12, 8))
ax = plt.gca()
ax.plot(alphas, coefs)
ax.set_xscale('log')  # alpha通常在对数尺度上观察
plt.xlabel('Alpha (Regularization Strength)')
plt.ylabel('Coefficient Value')
plt.title('Ridge Coefficients as a Function of Alpha')
plt.legend(feature_names, loc='upper right')
plt.grid(True)
plt.axis('tight')
plt.show()
