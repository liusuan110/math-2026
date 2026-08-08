import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from cycler import cycler

plt.rcParams['font.sans-serif'] = ['STZhongsong', 'SimHei', 'Microsoft YaHei', 'sans-serif']
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
plt.rcParams['axes.prop_cycle'] = cycler(color=['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f'])  # 更换配色
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('../../../sources/女胎(有效特征).csv', encoding='utf-8')

imbalance_ratio = df['是否异常'].value_counts(normalize=True)
print("样本不平衡情况分析:")
print(imbalance_ratio)
print("\n")

numeric_cols = df.select_dtypes(include=['number'])
correlation_matrix = numeric_cols.corr()
target_correlation = correlation_matrix['是否异常'].sort_values(ascending=False)
print("各特征与“是否异常”的相关性分析:")
print(target_correlation)
features_to_plot = [
    '21号染色体的Z值',
    '18号染色体的Z值',
    '13号染色体的Z值',
    'X染色体的Z值',
    '孕妇BMI',
    'GC含量'
]
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('不同特征在检验正确/错误样本中的分布对比 (0=正确, 1=错误)', fontsize=16)
axes = axes.flatten()

for i, feature in enumerate(features_to_plot):
    sns.boxplot(x='是否异常', y=feature, data=df,
                ax=axes[i],
                palette='Blues',
                notch=True,
                width=0.3)
    axes[i].set_title(f'{feature} 分布')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig('不同特征在检验正确或错误样本中的分布对比.pdf', bbox_inches='tight')
plt.show()