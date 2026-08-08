import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Matplotlib 全局美化设置 ---
plt.rcParams['font.sans-serif'] = ['STZhongsong']
plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('../../sources/男胎(Q2)(添加判断结果).csv')

# --- 数据处理 ---
# 定义Y染色体浓度的分箱（bins），宽度仍然是0.005
bin_width = 0.005
bins = np.arange(0, 0.15 + bin_width, bin_width)

# 使用pd.cut将连续的浓度值分配到各个离散的区间中
df['concentration_bin'] = pd.cut(df['Y染色体浓度'], bins=bins, right=False)

# 创建一个新列，'准确'为1，'不准确'为0
df['is_accurate'] = (df['是否准确'] == '准确').astype(int)

# 按浓度区间进行分组，并计算每个区间的总样本数和准确样本数
grouped = df.groupby('concentration_bin').agg(
    total_count=('是否准确', 'count'),
    accurate_count=('is_accurate', 'sum')
)

# 计算核心指标：每个区间内，准确样本的比例
grouped['accurate_proportion'] = (grouped['accurate_count'] / grouped['total_count']).fillna(0)

# 使用 >10 的样本数标准进行过滤
reliable_data = grouped[grouped['total_count'] > 10].copy()

# 准备绘图数据
bin_labels = [f'{interval.left:.3f}' for interval in reliable_data.index]
proportions = reliable_data['accurate_proportion']

# --- 【修改部分 1：颜色渐变】 ---
# 选择一个颜色映射（Colormap），例如 'plasma', 'viridis', 'cividis' 等
cmap = plt.get_cmap('plasma')
# 根据条形图的数量，从颜色映射中生成一个颜色列表，实现从左到右的平滑渐变
# 我们从0.2到0.95取色，避免使用最深和最浅、不易区分的颜色
colors = cmap(np.linspace(0.2, 0.95, len(bin_labels)))

# --- 绘图 ---
# --- 【修改部分 2：调整画布尺寸】 ---
plt.figure(figsize=(16, 7))

# 绘制条形图，并应用渐变颜色
bars = plt.bar(bin_labels, proportions, width=0.8, color=colors)  # 此处label已移除，因为渐变色本身不代表单一图例

# 在每个条形图上标注具体的比例值
for bar in bars:
    yval = bar.get_height()
    if yval > 0:
        plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.005, f'{yval:.1%}', ha='center', va='bottom', fontsize=14)

# 找到 '0.040' 这个标签在 x 轴标签列表中的数字索引位置
try:
    line_position = bin_labels.index('0.040')
    plt.axvline(x=line_position, color='red', linestyle='--', linewidth=2.5, label='Y染色体浓度达标线 (Y=4%)')
except ValueError:
    print("注意：'0.040' 区间因样本量不足(<=10)未在图中显示，因此未绘制标准线。")

# --- 【修改部分 3：再次放大所有字体】 ---
plt.xlabel('Y染色体浓度区间 (区间的起始值)', fontsize=18)
plt.ylabel('准确样本的比例', fontsize=18)
plt.title('各Y染色体浓度区间下，准确样本的比例分布', fontsize=24)
plt.xticks(rotation=45, fontsize=14)
plt.yticks(fontsize=14)
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
plt.ylim(0.6, 1.05)
plt.legend(fontsize=16)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

output_filename = 'Y染色体浓度与预测准确的关系.pdf'
plt.savefig(output_filename, dpi=300, bbox_inches='tight')  # 使用更高的DPI保存，使图片更清晰
