import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
from cycler import cycler

fm.fontManager.addfont('../../../utils/fonts/SourceHanSerifCN-Regular.otf')  # 添加字体
font_name = fm.FontProperties(fname='../../../utils/fonts/SourceHanSerifCN-Regular.otf').get_name()
plt.rcParams['font.sans-serif'] = [font_name]
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
plt.rcParams['axes.prop_cycle'] = cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
plt.rcParams['axes.unicode_minus'] = False

input_filename = "填充后的文物统计数据.csv"
final_filled_df_sorted = pd.read_csv(input_filename)
sums = final_filled_df_sorted.select_dtypes(include=np.number).sum(axis=1)

print("\n成分总和的完整列表")
pd.set_option("display.max_rows", None)
print(sums)
pd.reset_option("display.max_rows")  # 恢复默认设置

print(sums.describe())

LOWER_BOUND = 85.0
UPPER_BOUND = 105.0
total_samples = len(sums)
valid_range_count = ((sums >= LOWER_BOUND) & (sums <= UPPER_BOUND)).sum()
too_high_count = (sums > UPPER_BOUND).sum()
too_low_count = (sums < LOWER_BOUND).sum()

print(f"总样本数: {total_samples}")
print(f"总和在 [{LOWER_BOUND}, {UPPER_BOUND}] 区间内: {valid_range_count} 个 ({(valid_range_count / total_samples):.2%})")
print(f"总和 > {UPPER_BOUND}: {too_high_count} 个 ({(too_high_count / total_samples):.2%})")
print(f"总和 < {LOWER_BOUND}: {too_low_count} 个 ({(too_low_count / total_samples):.2%})")

sns.histplot(sums, kde=True, bins=30)  # 绘制直方图和核密度曲线

# 添加标记线和文字
plt.axvline(LOWER_BOUND, color='red', linestyle='--', label=f'下限: {LOWER_BOUND}')
plt.axvline(UPPER_BOUND, color='red', linestyle='--', label=f'上限: {UPPER_BOUND}')
plt.title('当前表格各样本化学成分总和的分布')  # <-- 修改了标题
plt.xlabel('化学成分总和')
plt.ylabel('样本数量')
plt.legend()
plt.grid(axis='y', alpha=0.5)
plt.show()
