import numpy as np
from scipy.stats import chi2_contingency

# 2 x 2 列联表
# [8 , 2, 10]
# [3 , 7, 10]
# [11, 9, 20]
table = np.array([[8, 2], [3, 7]])

# chi2_contingency 会返回: 卡方值, p值, 自由度, 期望频数表
chi2, p_chi2, dof, expected = chi2_contingency(table)

print(expected)
if np.any(expected < 5):
    print("期望频数表中有单元格的值小于 5，卡方检验的结果可能不准确。推荐使用 独立性检验 精准检验。")

print(f"K^2: {chi2:.4f}, P 值: {p_chi2:.4f} \n")
