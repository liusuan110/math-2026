import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.font_manager as fm

sns.set_style('darkgrid')
fm.fontManager.addfont('../../../utils/fonts/SourceHanSerifCN-Regular.otf')  # 添加字体
font_name = fm.FontProperties(fname='../../../utils/fonts/SourceHanSerifCN-Regular.otf').get_name()
plt.rcParams['font.sans-serif'] = [font_name]
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


def plot_measurement_distribution(file_path):
    """
    加载NIPT数据，分析并可视化男胎孕妇的测量次数分布。

    参数:
    file_path (str): NIPT数据文件的路径
    """
    # --- 1. 加载并预处理数据 ---
    try:
        data = pd.read_csv(file_path, encoding='utf8')
        print(f"成功加载数据文件: {file_path}")
    except FileNotFoundError:
        print(f"错误：未找到数据文件 '{file_path}'。请确保文件名正确且路径无误。")
        return
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return

    # --- 2. 筛选男胎数据 ---
    # 假设男胎的'Y染色体浓度'列不为空
    male_data = data[data['Y染色体浓度'].notna()].copy()
    if male_data.empty:
        print("数据中未找到有效的男胎样本。")
        return
    print(f"筛选出 {len(male_data)} 条男胎数据记录。")

    # --- 3. 统计每个孕妇的测量次数 ---
    # 根据 '孕妇代码' 列进行分组计数
    # 附录中说明 '孕妇代码' 是B列，请确保你的CSV文件中列名正确
    try:
        measurement_counts = male_data['孕妇代码'].value_counts()
    except KeyError:
        print("错误: 在文件中未找到名为 '孕妇代码' 的列。")
        print(f"文件中的实际列名为: {data.columns.tolist()}")
        return

    print("\n测量次数统计（部分数据预览）:")
    print(measurement_counts.head())

    # --- 4. 使用 seaborn 绘制分布直方图 ---
    plt.figure(figsize=(12, 7))

    # 使用 countplot 来直接统计每个测量次数出现的频次
    # 例如，统计有多少个孕妇测量了1次，多少个测量了2次，以此类推
    ax = sns.countplot(x=measurement_counts, palette='crest_r')

    # 在每个柱状图上添加数值标签
    for p in ax.patches:
        ax.annotate(f'{int(p.get_height())}',
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center',
                    xytext=(0, 9),
                    textcoords='offset points')

    plt.title('男胎孕妇测量次数分布直方图', fontsize=16)
    plt.xlabel('每位孕妇的测量次数', fontsize=12)
    plt.ylabel('孕妇数量', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('检测次数.pdf')
    plt.show()


if __name__ == "__main__":
    # 将 '附件数据.csv' 替换为你的实际文件名
    file_name = '../../sources/男胎(孕天).csv'
    plot_measurement_distribution(file_name)
