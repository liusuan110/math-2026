import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D # 用于创建自定义图例

plt.rcParams['font.sans-serif'] = ['STZhongsong']
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
plt.rcParams['axes.unicode_minus'] = False

input_filename = '../../../sources/男胎(Q2)(剔除Y小于4).csv'

df = pd.read_csv(input_filename)

# --- 1. 为每个点分配颜色 ---
# 根据“是否准确”列来决定颜色
# 如果值为'不准确'，则为红色；否则为蓝色
df['color'] = np.where(df['是否准确'] == '不准确', 'red', 'royalblue')

# --- 2. 绘制散点图 ---
print("正在根据'是否准确'列生成散点图...")
plt.figure(figsize=(12, 8)) # 设置画布大小

# 绘制散点图
# x轴: 孕妇BMI, y轴: 孕周, c: 颜色
plt.scatter(df['孕妇BMI'], df['孕周'], c=df['color'], alpha=0.7, s=50)

# --- 3. 添加标题、坐标轴标签和图例 ---
plt.title('孕妇BMI与孕周关系散点图', fontsize=16)
plt.xlabel('孕妇BMI', fontsize=12)
plt.ylabel('孕周', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.5)

# 创建自定义图例来解释颜色
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='不准确样本', markerfacecolor='red', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='准确样本', markerfacecolor='royalblue', markersize=10)
]
plt.legend(handles=legend_elements, title='图例')

output_image_filename = '剔除Y小于4的散点图（标注不正确点）.pdf'
plt.savefig(output_image_filename, bbox_inches='tight')
