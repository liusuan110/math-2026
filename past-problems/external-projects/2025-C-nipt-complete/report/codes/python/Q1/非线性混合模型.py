import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

# --- 设置绘图样式和字体 ---
sns.set_style('darkgrid')
plt.rcParams['font.sans-serif'] = ['STZhongsong'] # 更改为您指定的字体
plt.rcParams['axes.unicode_minus'] = False


df = pd.read_csv('../../sources/男胎(修正).csv', encoding='utf8')
df_clean = df.dropna(subset=['Y染色体浓度', '孕妇BMI', '孕周', '孕妇代码', '检测抽血次数'])


# 这里进行ICC检验
icc_model = smf.mixedlm("Q('Y染色体浓度') ~ 1", df_clean, groups=df_clean["孕妇代码"])
icc_result = icc_model.fit()
# 提取随机效应方差（组间方差）和残差方差（组内方差）
var_r_icc = float(icc_result.cov_re.iloc[0,0])
var_e_icc = icc_result.scale

icc = var_r_icc / (var_r_icc + var_e_icc)
print(f"组内相关系数 (ICC) = {icc:.4f}")

# 这里开始建立模型
poly_model = smf.mixedlm("Q('Y染色体浓度') ~ 孕周 + I(孕周**2) + Q('孕妇BMI') + Q('检测抽血次数')",
                         df_clean, groups=df_clean["孕妇代码"])
poly_result = poly_model.fit()

print(poly_result.summary())
print(poly_result.fe_params)
print(poly_result.pvalues)

# --- 可视化部分 ---
y_pred = poly_result.fittedvalues
y_true = df_clean['Y染色体浓度']

plt.figure(figsize=(8, 8))
sns.scatterplot(x=y_pred, y=y_true, alpha=0.5, label='数据点')
max_val = max(y_true.max(), y_pred.max())
min_val = min(y_true.min(), y_pred.min())
plt.plot([min_val, max_val], [min_val, max_val], color='red', linestyle='--', linewidth=2, label='完美预测线')

# --- 调整字体大小 ---
plt.title('模型预测值与真实值散点图', fontsize=17)
plt.xlabel('模型预测的Y染色体浓度', fontsize=13)
plt.ylabel('真实的Y染色体浓度', fontsize=13)
plt.tick_params(axis='both', which='major', labelsize=11) # 设置刻度字号
plt.legend(fontsize=11) # 设置图例字号

plt.axis('equal')
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig('预测值与真实值.pdf', bbox_inches='tight')
plt.show()

# --- 计算R^2 ---
X_poly = poly_result.model.exog
beta_poly = poly_result.fe_params

fixed_effects_pred_poly = X_poly @ beta_poly
var_f = np.var(fixed_effects_pred_poly)

var_r = float(poly_result.cov_re.iloc[0,0])
var_e = poly_result.scale

r2_marginal = var_f / (var_f + var_r + var_e)
r2_conditional = (var_f + var_r) / (var_f + var_r + var_e)

print(f"边缘 R-squared (Marginal R²): {r2_marginal:.4f}")
print(f"条件 R-squared (Conditional R²): {r2_conditional:.4f}")