import pandas as pd
from cycler import cycler
from matplotlib import pyplot as plt

plt.rcParams['font.sans-serif'] = ['STZhongsong', 'SimHei', 'Microsoft YaHei', 'sans-serif']
plt.rcParams['font.size'] = 18  # 全局字体大小 (原为 14)
plt.rcParams['axes.titlesize'] = 24  # 标题字体大小 (原为 18)
plt.rcParams['axes.labelsize'] = 20  # 坐标轴标签字体大小 (原为 16)
plt.rcParams['xtick.labelsize'] = 16  # x轴刻度字体大小 (原为 14)
plt.rcParams['ytick.labelsize'] = 16  # y轴刻度字体大小 (原为 14)
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'  # 保存后自动裁剪白边
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.prop_cycle'] = cycler(color=['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f'])  # 更换配色
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('../../../sources/女胎(修正).csv')

# 筛选出 "染色体的非整倍体" 列中包含 "T13", "T18", "T21" 的行
aneuploidy_counts = df['染色体的非整倍体'].value_counts()
filtered_counts = aneuploidy_counts[aneuploidy_counts.index.isin(['T13', 'T18', 'T21'])]

labels = filtered_counts.index
sizes = filtered_counts.values
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(aspect="equal"))

# 移除 explode 和 shadow 参数，使其成为平面图
wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)

ax.set_title("染色体的非整倍体分布 (T13, T18, T21)")
plt.setp(autotexts, size=20, weight="bold")
ax.legend(wedges, labels,
          title="非整倍体类型",
          loc="center left",
          bbox_to_anchor=(1, 0, 0.5, 1),
          fontsize=20,  # 设置图例项字体大小
          title_fontsize=20)  # 设置图例标题字体大小

plt.savefig('非整倍体扇形图.pdf')
print(filtered_counts)
