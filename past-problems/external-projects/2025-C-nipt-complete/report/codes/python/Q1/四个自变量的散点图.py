import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set_style('whitegrid')
plt.rcParams['font.sans-serif'] = ['STZhongsong']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

df = pd.read_csv('../../sources/男胎(孕天).csv', encoding='utf8')
df_clean = df.dropna(subset=['Y染色体浓度', '孕妇BMI', '孕周', '检测抽血次数'])

# 2. 创建 '孕周**2' 列
df_clean['孕周_sq'] = df_clean['孕周'] ** 2

# 3. 设置绘图区域
# 创建一个2x2的子图网格，figsize可以调整整个图的大小
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# --- 开始绘制四个散点图 ---

# 图1: Y染色体浓度 vs. 孕周
sns.regplot(ax=axes[0, 0], x='孕周', y='Y染色体浓度', data=df_clean,
            scatter_kws={'alpha': 0.3, 's': 15},  # 设置点的透明度和大小
            line_kws={'color': 'red', 'linewidth': 2})  # 设置回归线的颜色和宽度
axes[0, 0].set_title('Y染色体浓度与孕周的关系', fontsize=16)
axes[0, 0].set_xlabel('孕周', fontsize=13)
axes[0, 0].set_ylabel('Y染色体浓度', fontsize=13)
axes[0, 0].tick_params(axis='both', which='major', labelsize=11) # 设置刻度字号

# 图2: Y染色体浓度 vs. 孕周的平方
sns.regplot(ax=axes[0, 1], x='孕周_sq', y='Y染色体浓度', data=df_clean,
            scatter_kws={'alpha': 0.3, 's': 15},
            line_kws={'color': 'red', 'linewidth': 2})
axes[0, 1].set_title('Y染色体浓度与孕周的平方的关系', fontsize=16)
axes[0, 1].set_xlabel('孕周的平方', fontsize=13)
axes[0, 1].set_ylabel('Y染色体浓度', fontsize=13)
axes[0, 1].tick_params(axis='both', which='major', labelsize=11) # 设置刻度字号

# 图3: Y染色体浓度 vs. 孕妇BMI
sns.regplot(ax=axes[1, 0], x='孕妇BMI', y='Y染色体浓度', data=df_clean,
            scatter_kws={'alpha': 0.3, 's': 15},
            line_kws={'color': 'red', 'linewidth': 2})
axes[1, 0].set_title('Y染色体浓度与孕妇BMI的关系', fontsize=16)
axes[1, 0].set_xlabel('孕妇BMI', fontsize=13)
axes[1, 0].set_ylabel('Y染色体浓度', fontsize=13)
axes[1, 0].tick_params(axis='both', which='major', labelsize=11) # 设置刻度字号

# 图4: Y染色体浓度 vs. 检测抽血次数
# 由于抽血次数是离散整数，用stripplot或swarmplot可能更合适，但regplot也能展示趋势
sns.regplot(ax=axes[1, 1], x='检测抽血次数', y='Y染色体浓度', data=df_clean,
            x_jitter=0.2,  # 给x轴加上一点扰动，避免点完全重叠
            scatter_kws={'alpha': 0.3, 's': 15},
            line_kws={'color': 'red', 'linewidth': 2})
axes[1, 1].set_title('Y染色体浓度与检测抽血次数的关系', fontsize=16)
axes[1, 1].set_xlabel('检测抽血次数', fontsize=13)
axes[1, 1].set_ylabel('Y染色体浓度', fontsize=13)
axes[1, 1].tick_params(axis='both', which='major', labelsize=11) # 设置刻度字号

# 4. 保存图像
plt.savefig('四个自变量的散点图.pdf', bbox_inches='tight')  # 保存为高分辨率图像