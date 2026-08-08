import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

sns.set_style('darkgrid')
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
plt.rcParams['axes.prop_cycle'] = cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
plt.rcParams['axes.unicode_minus'] = False


def load_and_preprocess(filepath, fetus_type, column_names):
    """加载数据，提取GC含量，并添加胎儿类型标签"""
    try:
        df_raw = pd.read_csv(filepath, on_bad_lines='skip', encoding='utf-8', header=None, skiprows=2)
    except UnicodeDecodeError:
        df_raw = pd.read_csv(filepath, on_bad_lines='skip', encoding='gbk', header=None, skiprows=2)

    # 确保列名数量与数据列数匹配
    num_cols = df_raw.shape[1]
    df_raw.columns = column_names[:num_cols]

    # 提取GC含量并转换为数值
    df_gc = pd.to_numeric(df_raw['GC含量'], errors='coerce').dropna()

    # 创建新的DataFrame
    df_processed = pd.DataFrame({
        'GC含量': df_gc,
        '胎儿性别': fetus_type
    })
    return df_processed


column_names = [
    '序号', '孕妇代码', '年龄', '身高', '体重', '末次月经', 'IVF妊娠', '检测日期',
    '检测抽血次数', '检测孕周', '孕妇BMI', '原始读段数', '在参考基因组上比对的比例',
    '重复读段的比例', '唯一比对的读段数', 'GC含量', '13号染色体的Z值', '18号染色体的Z值',
    '21号染色体的Z值', 'X染色体的Z值', 'Y染色体的Z值', 'Y染色体浓度', 'X染色体浓度',
    '13号染色体的GC含量', '18号染色体的GC含量', '21号染色体的GC含量', '被过滤掉读段数的比例',
    '染色体的非整倍体', '怀孕次数', '生产次数', '胎儿是否健康'
]

df_male = load_and_preprocess('../../sources/男胎.csv', '男胎', column_names)
df_female = load_and_preprocess('../../sources/女胎.csv', '女胎', column_names)
df_combined = pd.concat([df_male, df_female])

plt.figure(figsize=(10, 7))
sns.violinplot(x='胎儿性别', y='GC含量', data=df_combined, linewidth=3, palette='Blues')
plt.axhline(0.4, color='red', linestyle='--', linewidth=1.5, label='40% (正常范围下限)')
plt.title('男胎与女胎的 GC 含量分布图', fontsize=16)
plt.ylabel('GC 含量 (%)', fontsize=14)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.savefig('GC值小提琴图.pdf')
plt.show()
