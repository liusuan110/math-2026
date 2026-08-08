import math

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
# -- 图片预设，需要 plt, fm, cycler 库
import matplotlib.gridspec as gridspec  # 引入 GridSpec 用于复杂布局
import matplotlib.font_manager as fm
from cycler import cycler
import os

font_path = "../../../utils/fonts/SourceHanSerifCN-Regular.otf"
if os.path.exists(font_path):
    # 如果字体文件存在，则加载并使用它
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rcParams['font.sans-serif'] = [font_name]
else:
    fallback_fonts = ['STZhongsong', 'SimHei', 'Microsoft YaHei', 'Heiti TC', 'PingFang SC', 'sans-serif']
    plt.rcParams['font.sans-serif'] = fallback_fonts
    print(f"警告: 字体文件 '{font_path}' 未找到, 将使用系统备选字体: {fallback_fonts}")

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
# -- 图片预设

df = pd.read_csv("../../sources/男胎(孕天).csv")
male_fetus_df = df[df['Y染色体浓度'] > 0.01].copy()

dependent_variable = 'Y染色体浓度'
independent_variables = ['孕周', '年龄', '孕妇BMI', '检测抽血次数', '生产次数']
n_vars = len(independent_variables)
n_cols = 3
n_rows = math.ceil(n_vars / n_cols)

fig = plt.figure()
gs = gridspec.GridSpec(2, 6, figure=fig)

ax1 = fig.add_subplot(gs[0, 0:2])
ax2 = fig.add_subplot(gs[0, 2:4])
ax3 = fig.add_subplot(gs[0, 4:6])
ax4 = fig.add_subplot(gs[1, 0:2]) # 修改：靠左对齐
ax5 = fig.add_subplot(gs[1, 4:6]) # 修改：靠右对齐

axes_list = [ax1, ax2, ax3, ax4, ax5]

for i, iv_col in enumerate(independent_variables):
    ax = axes_list[i]
    sns.regplot(x=iv_col, y=dependent_variable, data=male_fetus_df,
                ax=ax,
                scatter_kws={'alpha': 0.6, 's': 20, 'color': '#ff7f0e'},
                line_kws={'color': '#1f77b4', 'linestyle': '--'})

    ax.set_title(f'{iv_col} 与 Y 染色体浓度')
    ax.set_xlabel(iv_col)
    ax.set_ylabel(dependent_variable)
    ax.grid(True)

plt.tight_layout(pad=2.0)
plt.savefig("Y染色体浓度与有关系的变量的散点图.pdf")
plt.show()
