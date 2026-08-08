import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import fisher_exact, chi2_contingency  # 独立性检验、K^2 检验库

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def discount_and_return_relationship(origin: pd.DataFrame):
    """第一部分：打折与退货关系分析"""
    square_table = pd.crosstab(origin['销售类型'], origin['是否打折销售'])
    print(square_table)  # 构造 2 x 2 列联表
    p_value = chi2_contingency(square_table)
    print(f"P-Value: {p_value:.8f}")  # 执行 K^2 检验


def classify_vegetable(data: pd.DataFrame):
    def get_season(date):
        """根据月份判断季节"""
        month = date.month
        if month in [3, 4, 5]:
            return '春'
        elif month in [6, 7, 8]:
            return '夏'
        elif month in [9, 10, 11]:
            return '秋'
        else:  # 12, 1, 2
            return '冬'

    data['日期'] = pd.to_datetime(data['日期'])
    data['年份'] = data['日期'].dt.year
    data['季节'] = data['日期'].apply(get_season)

    seasonal_days = data.groupby(['单品名称', '季节'])['日期'].nunique().reset_index()
    seasonal_days.rename(columns={'日期': '季节出现天数'}, inplace=True)

    # 按单品名称聚合季节性数据，用于后续判断
    seasonal_summary = seasonal_days.groupby('单品名称').agg(
        num_seasons=('季节', 'nunique'),  # 出现过的季节数量
        min_seasonal_days=('季节出现天数', 'min'),  # 各季节中最少的出现天数
        max_seasonal_days=('季节出现天数', 'max')  # 各季节中最多的出现天数
    ).reset_index()

    yearly_days = data.groupby(['单品名称', '年份'])['日期'].nunique().reset_index()
    yearly_days.rename(columns={'日期': '出现天数'}, inplace=True)

    yearly_summary = yearly_days.groupby('单品名称').agg(
        年最大出现天数=('出现天数', 'max'),
        年最小出现天数=('出现天数', 'min')
    ).reset_index()

    final_data = pd.merge(yearly_summary, seasonal_summary, on='单品名称', how='left')

    conditions = [
        (final_data['num_seasons'] == 4) & (final_data['min_seasonal_days'] > 20),
        final_data['max_seasonal_days'] < 20,
        final_data['年最大出现天数'] > 300,
        final_data['年最大出现天数'] < 15
    ]

    choices = [
        '常年性蔬菜',
        '时令性蔬菜',
        '常年性蔬菜',
        '时令性蔬菜'
    ]

    final_data['类型'] = np.select(conditions, choices, default='季节性蔬菜')
    output_columns = ['单品名称', '年最大出现天数', '年最小出现天数', '类型']
    final_data = final_data[output_columns]
    print(final_data)
    final_data.to_csv("不同品类蔬菜分类.csv", index=False, encoding='utf_8_sig')
    return final_data


def draw_pie_chart():
    """绘制饼图"""
    df = pd.read_csv('不同品类蔬菜分类.csv')
    type_counts = df['类型'].value_counts()
    plt.figure(figsize=(8, 8))
    plt.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%', startangle=140)
    plt.title('不同种类蔬菜占比')
    plt.ylabel('')  # 隐藏 Y 轴标签
    plt.savefig('不同种类蔬菜的占比.png')


if __name__ == "__main__":
    # origin = pd.read_csv('初始数据合并表格(含加成率).csv')
    # discount_and_return_relationship(origin)

    data = pd.read_csv('../../../sources/附件3(带品类名).csv')
    classify_vegetable(data)
    draw_pie_chart()

# # 生成图2：关系热力图
# plt.figure(figsize=(8, 6))
# sns.heatmap(square_table, annot=True, fmt='d', cmap='Blues', linewidths=.5, cbar=True, annot_kws={"size": 14})
# plt.title('打折与退货的关系', fontsize=16)
# plt.ylabel('')
# plt.xlabel('')
# plt.xticks(fontsize=12)
# plt.yticks(fontsize=12, rotation=0)
# plt.savefig("图2_打折与退货关系热力图.png", dpi=300, bbox_inches='tight')
# print("图2 已保存为 '图2_打折与退货关系热力图.png'")
#
# # --- 第二部分：蔬菜按供应时间分类 ---
# print("\n[Part 2 & 图1] 正在根据供应时间对蔬菜进行分类...")
# df_purchase['日期'] = pd.to_datetime(df_purchase['日期'])
# df_purchase['年份'] = df_purchase['日期'].dt.year
#
# # 计算每个单品每年的供应天数
# supply_days_per_year = df_purchase.groupby(['单品编码', '年份'])['日期'].nunique().reset_index()
# supply_days_per_year.rename(columns={'日期': '供应天数'}, inplace=True)
#
# # 找到每个单品在所有年份中最大的供应天数
# max_supply_days = supply_days_per_year.groupby('单品编码')['供应天数'].max().reset_index()
# max_supply_days.rename(columns={'供应天数': '年最大供应天数'}, inplace=True)
#
#
# # 定义分类函数
# def classify_vegetable(days):
#     if days > 300:
#         return '常年性蔬菜'
#     elif days < 15:
#         return '时令性蔬菜'
#     else:
#         return '季节性蔬菜'
#
#
# max_supply_days['类型'] = max_supply_days['年最大供应天数'].apply(classify_vegetable)
#
# # 合并分类结果并保存
# classification_result = pd.merge(df_info, max_supply_days, on='单品编码', how='left')
# classification_result['类型'].fillna('未分类(无进货记录)', inplace=True)
# classification_result.to_csv('vegetable_classification.csv', index=False, encoding='utf_8_sig')
# print("蔬菜分类完成，结果已保存到 'vegetable_classification.csv'")
#
# # 生成图1：各类型蔬菜占比
# print("\n正在生成各类型蔬菜占比饼图...")
# type_counts = classification_result['类型'].value_counts()
# main_types = ['常年性蔬菜', '季节性蔬菜', '时令性蔬菜']
# type_counts_main = type_counts.reindex(main_types).dropna()
#
# plt.figure(figsize=(8, 8))
# colors = ['#4682B4', '#FFA500', '#8FBC8F']
# wedges, texts, autotexts = plt.pie(
#     type_counts_main,
#     labels=type_counts_main.index,
#     autopct='%1.0f%%',
#     startangle=90,
#     colors=colors,
#     pctdistance=0.85,
#     wedgeprops={'edgecolor': 'w', 'linewidth': 2}
# )
# plt.title('各类型蔬菜占比', fontsize=16)
# # 调整字体样式
# for text in texts:
#     text.set_fontsize(12)
# for autotext in autotexts:
#     autotext.set_fontsize(12)
#     autotext.set_color('white')
#     autotext.set_fontweight('bold')
#
# plt.savefig("图1_各类型蔬菜占比.png", dpi=300, bbox_inches='tight')
# print("图1 已保存为 '图1_各类型蔬菜占比.png'")
#
# # --- 第三部分：商品加成率分布图 ---
# print("\n[Part 3 & 图3] 正在生成商品加成率分布直方图...")
#
# plt.figure(figsize=(10, 6))
# # 筛选加成率在合理范围的数据进行绘图
# markup_to_plot = origin['加成率'].dropna()
# markup_to_plot = markup_to_plot[(markup_to_plot > -1) & (markup_to_plot < 5)]
#
# plt.hist(markup_to_plot, bins=50, edgecolor='white', color='#4682B4')
# plt.title('商品加成率分布图', fontsize=16)
# plt.xlabel('加成率', fontsize=12)
# plt.ylabel('频数', fontsize=12)
# plt.grid(axis='y', linestyle='--', alpha=0.7)
# plt.savefig("图3_商品加成率分布图.png", dpi=300, bbox_inches='tight')
# print("图3 已保存为 '图3_商品加成率分布图.png'")
#
# print("\n--- 所有任务执行完毕！---")
