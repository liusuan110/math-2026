import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D  # 用于创建自定义图例

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

input_filename = '../../../sources/男胎(Q2)(添加判断结果).csv'

df = pd.read_csv(input_filename)


def check_accuracy(row):
    """
    判断逻辑：
    - '染色体的非整倍体'为空 -> 预测健康 ('是')
    - '染色体的非整倍体'不为空 -> 预测不健康 ('否')
    - 比较预测结果和实际'胎儿是否健康'列的结果
    """
    actual_healthy = row['胎儿是否健康']
    if pd.isna(row['染色体的非整倍体']):
        predicted_healthy = '是'
    else:
        predicted_healthy = '否'

    if predicted_healthy == actual_healthy:
        return '准确'
    else:
        return '不准确'


df['是否准确'] = df.apply(check_accuracy, axis=1)

conditions = [
    df['是否准确'] == '不准确',  # 红色条件：检测结果不准确
    df['Y染色体浓度'] < 0.04  # 橙色条件：Y染色体浓度 < 4% (0.04)
]
colors = ['red', 'orange']

df['color'] = np.select(conditions, colors, default='royalblue')

plt.figure(figsize=(12, 8))  # 创建画布

plt.scatter(df['孕妇BMI'], df['孕周'], c=df['color'], alpha=0.7, s=50)

plt.title('孕妇BMI与孕周关系散点图', fontsize=16)
plt.xlabel('孕妇 BMI 指标', fontsize=12)
plt.ylabel('检测孕周 (周)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)

legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='不准确样本 (红色)', markerfacecolor='red', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Y染色体浓度 < 4% (橙色)', markerfacecolor='orange', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='正常样本 (蓝色)', markerfacecolor='royalblue', markersize=10)
]
plt.legend(handles=legend_elements, title='样本分类', loc='best')

output_image_filename = '标注全部不准确散点图.pdf'
plt.savefig(output_image_filename, dpi=300)  # dpi=300 保存为高分辨率图像
