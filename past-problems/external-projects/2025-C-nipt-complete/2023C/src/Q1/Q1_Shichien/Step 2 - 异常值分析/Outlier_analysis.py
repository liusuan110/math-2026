import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

font_settings = {
    'font.family': ['Times New Roman', 'SimSun'],
    'axes.unicode_minus': False,
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'axes.titleweight': 'bold',
    'axes.labelweight': 'bold'
}
plt.rcParams.update(font_settings)

# Marker 'D'菱形，'^'上三角，'o'圆，'s'正方形，'v'下三角，'p'五边形，'*'，'+'，'x'，'.'
BOX_PROPS = {
    'boxprops': {'edgecolor': 'k', 'linewidth': 0.5},
    'medianprops': {
        'linestyle': '-', 'color': 'r', 'linewidth': 1.5
    },
    'flierprops': {
        'marker': '^', 'markersize': 6.75, 'markeredgewidth': 0.75,
        'markerfacecolor': 'green', 'markeredgecolor': 'k'
    },
    'whiskerprops': {
        'linestyle': '--', 'linewidth': 1.2, 'color': '#480656'
    },
    'capprops': {
        'linestyle': '-', 'linewidth': 1.5, 'color': '#480656'
    }
}

colors = ['pink', 'lightblue', 'lightgreen']

data = pd.read_csv('../Step 1 - 合并数据/merged_sales_data.csv')
plt.figure(figsize=(10, 8))
ax1 = sns.boxplot(
    x='单品名称',
    y='销量(千克)',
    data=data,
    notch=True,
    patch_artist=True,
    hue='单品名称',
    palette=colors, # 填充颜色
    legend=False,
    **BOX_PROPS)  # 传递预设
plt.title('不同单品销量箱线图')
plt.xlabel('单品名称', fontsize=14, fontweight='bold')
plt.ylabel('销量 (千克)', fontsize=14, fontweight='bold')
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('sales_boxplot_styled.png')


plt.figure(figsize=(10, 5))
ax2 = sns.boxplot(
    x='分类名称',
    y='销量(千克)',
    data=data,
    notch=True,
    patch_artist=True,
    hue='分类名称',
    palette=colors, # 填充颜色
    legend=False,
    **BOX_PROPS)  # 传递预设
plt.title('不同分类的销量箱线图')
plt.ylabel('销量 (千克)', fontsize=14, fontweight='bold')
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('sales_class_boxplot_styled.png')

