import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, chi2

#        康复  未康复
# 用药组   14     6
# 安慰剂组  4     15
obs_data = np.array([[14, 6],
                     [4, 15]])

# 将 correction 参数设置为 True
print("--- 卡方检验的结果 (Yates 校正) ---")
chi2_yates, p_yates, dof, expected_yates = chi2_contingency(obs_data, correction=True)
print(f"卡方统计量: {chi2_yates:.4f}")
print(f"P-value: {p_yates:.4f}")
print(f"自由度: {dof}")

print("\n--- 标准皮尔逊卡方检验的结果 (无校正) ---")
chi2_pearson, p_pearson, dof, expected_pearson = chi2_contingency(obs_data, correction=False)
print(f"卡方统计量: {chi2_pearson:.4f}")
print(f"P-value: {p_pearson:.4f}")

if p_yates < 0.05:
    print("P<0.05): 新药效果与康复情况存在显著关联。")
else:
    print("P>=0.05): 无法认为新药效果与康复情况存在显著关联。")
