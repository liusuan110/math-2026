import pandas as pd
from scipy.stats import spearmanr

df = pd.DataFrame({'student': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
                   'math': [70, 78, 90, 87, 84, 86, 91, 74, 83, 85],
                   'science': [90, 94, 79, 86, 84, 83, 88, 92, 76, 75]})

rho, p = spearmanr(df['math'], df['science'])
print(f"Rho: {rho:.4f}, p: {p:.4f}")

# 从输出中可以看到，Math 成绩和 Science 成绩之间存在负相关性
# 但是相关性的 p < 0.05，说明这种相关性并不显著。
# 这可能是因为样本量较小，或者数据中存在异常值等原因导致的。