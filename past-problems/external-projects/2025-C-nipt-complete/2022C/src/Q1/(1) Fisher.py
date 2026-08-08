import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact

df = pd.read_csv('../../sources/原始文物类型.csv')

print("--- 1. 各变量的类别数量统计 ---")
print(df['纹饰'].value_counts())
print(df['类型'].value_counts())
print(df['颜色'].value_counts())
print(df['表面风化'].value_counts())

features_to_test = ['纹饰', '类型', '颜色', '表面风化']
alpha = 0.05

for feature in features_to_test:
    print(f"\n检验 [表面风化] 与 [{feature}] 的关系:")
    contingency_table = pd.crosstab(df['表面风化'], df[feature])
    print(contingency_table)

    chi2, p_chi2, dof, expected = chi2_contingency(contingency_table)

    if np.any(expected < 5):
        print("\n存在期望频数小于5的单元格，卡方检验可能不准确。改用 独立性检验 精确检验。")
        stat, p_value = fisher_exact(contingency_table)
        print(f"检验统计量 (Statistic/Odds Ratio): {stat:.4f}")
        print(f"P值 (p-value): {p_value:.4f}")

    else:
        print("\n所有单元格期望频数均>=5，使用卡方检验。")
        p_value = p_chi2
        print(f"卡方统计量 (Chi-Square): {chi2:.4f}")
        print(f"P值 (p-value): {p_value:.4f}")

    if p_value < alpha:
        print(f"结论: P值 < {alpha}，结果显著。可以认为 [表面风化] 与 [{feature}] 之间存在显著关系。")
    else:
        print(f"结论: P值 >= {alpha}，结果不显著。没有足够证据表明 [表面风化] 与 [{feature}] 之间存在关系。")
