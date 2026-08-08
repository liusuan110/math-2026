import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from cycler import cycler

fm.fontManager.addfont('../../utils/fonts/SourceHanSerifCN-Regular.otf')  # 添加字体
font_name = fm.FontProperties(fname='../../utils/fonts/SourceHanSerifCN-Regular.otf').get_name()
plt.rcParams['font.sans-serif'] = [font_name, "SimHei", 'Microsoft YaHei', 'Times New Roman']
plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight' # 保存后自动裁剪白边
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.prop_cycle'] = cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
plt.rcParams['axes.unicode_minus'] = False

np.random.seed(42)
data = {
    '学习时长': np.arange(1, 11),  # 线性增长: 1, 2, ..., 10
    '考试分数': [10, 15, 20, 35, 50, 65, 75, 80, 82, 83], # 非线性增长（前期快，后期慢）
    '分心次数': [9, 10, 8, 7, 6, 5, 3, 4, 2, 1], # 负相关
    '无关噪音': np.random.rand(10) * 100 # 一个完全随机的列
}
df = pd.DataFrame(data)

print(df)
pearson_corr_matrix = df.corr(method='pearson') # 改成 Pearson 就能用另一个算法了
print(pearson_corr_matrix)

plt.figure(figsize=(8, 6)) # 设置画布大小
heatmap = sns.heatmap(
    pearson_corr_matrix,
    annot=True,        # 在格子里显示数字
    cmap='coolwarm',   # 设置配色方案，coolwarm很适合相关性（红正蓝负）
    fmt='.2f'          # 格式化数字，保留两位小数
)
plt.title('Spearman 相关系数热力图', fontsize=16)
plt.show()