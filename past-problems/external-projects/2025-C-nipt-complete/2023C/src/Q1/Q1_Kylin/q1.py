import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

try:
    # 1. 数据加载与合并
    df1 = pd.read_csv('附件1.csv')
    df2 = pd.read_csv('附件2.csv')
    df3 = pd.read_csv('附件3.csv')
    df4 = pd.read_csv('附件4.csv')

    data = pd.merge(df2, df1, on='单品编码', how='left')
    df3.rename(columns={'日期': '销售日期'}, inplace=True)
    data = pd.merge(data, df3, on=['销售日期', '单品编码'], how='left')
    data = pd.merge(data, df4, on='单品编码', how='left')

    # 2. 数据清洗与预处理
    data['销售日期'] = pd.to_datetime(data['销售日期'])
    numeric_cols = ['销量(千克)', '销售单价(元/千克)', '批发价格(元/千克)', '损耗率(%)']
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors='coerce')
        data[col].fillna(data[col].median(), inplace=True)

    # 剔除销量异常值
    mean = data['销量(千克)'].mean()
    std = data['销量(千克)'].std()
    data = data[(data['销量(千克)'] >= (mean - 3 * std)) & (data['销量(千克)'] <= (mean + 3 * std))]

    # 确保'分类名称'列没有缺失值
    data.dropna(subset=['分类名称'], inplace=True)

    # 3. 销售量分布规律分析
    # 3.1 各品类日销量分布规律
    # 按天和品类聚合销量
    daily_category_sales_dist = data.groupby(['销售日期', '分类名称'])['销量(千克)'].sum().reset_index()

    plt.figure(figsize=(12, 8))
    sns.boxplot(x='分类名称', y='销量(千克)', data=daily_category_sales_dist)
    plt.title('各蔬菜品类日销量分布箱形图', fontsize=16)
    plt.xlabel('蔬菜品类', fontsize=12)
    plt.ylabel('日销量 (千克)', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig('category_sales_volume_boxplot.png')
    plt.close()

    # 3.2 各单品总销量分布规律 (Top 20)
    top_20_products = data.groupby('单品名称_x')['销量(千克)'].sum().nlargest(20)

    plt.figure(figsize=(12, 10))
    top_20_products.sort_values(ascending=True).plot(kind='barh')
    plt.title('总销量最高的20个单品', fontsize=16)
    plt.xlabel('总销量 (千克)', fontsize=12)
    plt.ylabel('单品名称', fontsize=12)
    plt.savefig('top_products_sales_volume_barchart.png')
    plt.close()

    # 4. 各蔬菜品类日销量的相关性分析
    # 创建以日期为索引，品类为列的销量数据透视表
    category_pivot = data.groupby(['销售日期', '分类名称'])['销量(千克)'].sum().unstack()

    # 填充缺失值 (某天某品类可能没有销售，填充为0)
    category_pivot.fillna(0, inplace=True)

    # 计算品类日销量的相关性矩阵
    category_correlation = category_pivot.corr()

    # 可视化：相关性矩阵热力图
    mask = np.triu(np.ones_like(category_correlation, dtype=bool), k=1)
    plt.figure(figsize=(10, 8))
    sns.heatmap(category_correlation, annot=True, cmap='crest', fmt=".2f", linewidths=.5, mask=mask, annot_kws={'fontsize':15, 'color': 'white'})
    plt.title('各蔬菜品类日销量相关性热力图', fontsize=16)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.savefig('category_daily_sales_correlation_heatmap.png')
    plt.close()

    print("数据分析和可视化已完成。新生成的图片已保存到文件。")
    print(
        "生成的文件: category_sales_volume_boxplot.png, top_products_sales_volume_barchart.png, category_daily_sales_correlation_heatmap.png")

except FileNotFoundError as e:
    print(f"文件未找到: {e.filename}，请确保所有附件CSV文件都在代码运行的目录下。")
except Exception as e:
    print(f"处理过程中发生错误: {e}")