import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import math

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

df = pd.read_csv('../../../sources/女胎(有效特征修正版).csv')

# 分离正常与异常样本
normal_df = df[df['是否异常'] == 0]
abnormal_df = df[df['是否异常'] == 1]


def create_and_save_subplots(features_list, filename, main_title):
    """
    一个通用的函数，用于为给定的特征列表创建并保存子图网格。

    参数:
    features_list (list): 需要绘图的特征名称列表。
    filename (str): 输出图片的文件名。
    main_title (str): 图表的总标题。
    """
    # --- 计算网格布局 ---
    n_features = len(features_list)
    n_cols = 3
    n_rows = math.ceil(n_features / n_cols)
    figsize = (18, n_rows * 5)  # 根据行数动态调整图表高度

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    axes = axes.flatten()

    print(f"正在生成图表: {filename}...")

    # --- 遍历特征并在每个子图上绘图 ---
    for i, feature in enumerate(features_list):
        ax = axes[i]
        sns.kdeplot(normal_df[feature], label='正常样本 (0)', color='blue', fill=True, alpha=0.1, ax=ax)
        sns.kdeplot(abnormal_df[feature], label='异常样本 (1)', color='red', fill=True, alpha=0.2, ax=ax)

        ax.set_title(f'特征: {feature}', fontsize=12)
        ax.set_xlabel('')
        ax.set_ylabel('密度')
        ax.legend()
        ax.grid(linestyle='--', alpha=0.6)

    # --- 隐藏多余的子图 ---
    for i in range(n_features, len(axes)):
        axes[i].set_visible(False)

    # --- 调整整体布局并保存 ---
    fig.suptitle(main_title, fontsize=20, y=1.0)
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    plt.savefig(filename, bbox_inches='tight')
    plt.close()
    print(f"图表已成功保存为 '{filename}'")


# --- 3. 定义两组特征 ---
# 第一组：核心测序质量和Z值
features_group_1 = [
    '原始读段数', '在参考基因组上比对的比例', '重复读段的比例',
    '唯一比对的读段数', '13号染色体的Z值', 'X染色体的Z值',
    '18号染色体的Z值', '21号染色体的Z值', '被过滤掉读段数的比例'
]

# 第二组：其余特征
all_features = [
    '孕妇BMI', '原始读段数', '在参考基因组上比对的比例', '重复读段的比例',
    '唯一比对的读段数', 'GC含量', '13号染色体的Z值', '18号染色体的Z值',
    '21号染色体的Z值', 'X染色体的Z值', 'X染色体浓度', '13号染色体的GC含量',
    '18号染色体的GC含量', '21号染色体的GC含量', '被过滤掉读段数的比例'
]
features_group_2 = [f for f in all_features if f not in features_group_1]

# --- 4. 调用函数生成并保存两张图表 ---
create_and_save_subplots(
    features_list=features_group_1,
    filename='其他指标对比图.pdf',
    main_title='其他测序质量与Z值 - 分布对比总览'
)

create_and_save_subplots(
    features_list=features_group_2,
    filename='核心指标对比图.pdf',
    main_title='核心辅助指标 - 分布对比总览'
)