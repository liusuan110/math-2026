import numpy as np
from scipy.stats import fisher_exact

# 2 x 2 列联表
# [8 , 2, 10]
# [3 , 7, 10]
# [11, 9, 20]
table = np.array([[8, 2], [3, 7]])
odds_ratio, p_fisher = fisher_exact(table) # fisher_exact 会返回: 优势比 (Odds Ratio), p值
print(f"优势比: {odds_ratio:.4f} P 值: {p_fisher:.4f}")

alpha = 0.05
if p_fisher < alpha:
    print(f"在显著性水平 {alpha} 下，P-value ({p_fisher:.4f}) < {alpha}，我们拒绝原假设。")
    print("能够认为两个变量之间存在统计学关联性。")
else:
    print(f"在显著性水平 {alpha} 下，P-value ({p_fisher:.4f}) >= {alpha}，我们不能拒绝原假设。")
    print("无法证明两个变量之间有关联。")
