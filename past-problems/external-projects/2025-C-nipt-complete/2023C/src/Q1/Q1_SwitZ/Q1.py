

# 导入所有需要的库
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import os
# --- 准备工作: 设置matplotlib以正确显示中文 ---
# 确保你的环境中安装了支持中文的字体，例如'SimHei' (黑体), 'Microsoft YaHei' (微软雅黑) 等
plt.rcParams['font.sans-serif'] = ['SimHei']
# 解决负号'-'在图中显示为方块的问题
plt.rcParams['axes.unicode_minus'] = False

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

# --- 第一步: 加载数据 ---
# 使用 try-except 结构来增强代码的健壮性，方便定位问题
try:
    # 使用正确的'utf-8'编码读取附件1，因为我们已经侦察到这是正确的编码
    product_info_df = pd.read_csv(os.path.join(parent_dir, 'sources','附件1.csv'), encoding='utf-8')

    # 读取销售流水数据
    sales_df = pd.read_csv(os.path.join(parent_dir, 'sources', '附件2.csv'), encoding='utf-8')

    files_loaded = True
    print("文件加载成功!")

except Exception as e:
    print(f"文件加载失败，错误信息: {e}")
    files_loaded = False


# 确保文件成功加载后才执行后续步骤
if files_loaded:
    # --- 第二步: 数据预处理和合并 ---
    
    # 1. 从商品信息表中，只筛选我们需要的列，并使用正确的列名'分类名称'
    product_info_df = product_info_df[['单品编码', '分类名称','单品名称']]

    # 2. 将'销售日期'列从普通的文本格式转换为pandas的datetime对象，这是进行时间序列分析的基础
    sales_df['销售日期'] = pd.to_datetime(sales_df['销售日期'])

    # 3. 使用 'merge' 函数将销售流水表和商品信息表合并
    #    合并的依据是共同的'单品编码'列
    #    'how='left'' 表示以左边的销售流水表为基础进行合并
    merged_df = pd.merge(sales_df, product_info_df, on='单品编码', how='left')
    
    # 4. 检查合并后是否有未能匹配到分类的数据（表现为'分类名称'列为空值）
    if merged_df['分类名称'].isnull().any():
        print(f"警告: 合并后存在 {merged_df['分类名称'].isnull().sum()} 条未匹配到分类的数据，将予以忽略。")
        # 移除这些无法匹配的行，确保数据干净
        merged_df.dropna(subset=['分类名称'], inplace=True)

    merged_df.to_csv('merged_df.csv', encoding='utf-8-sig', index=False)

    # ==================================================================
    # --- 新增：异常值分析 ---
    # ==================================================================
    print("\n--- 开始进行异常值分析 ---")

    # --- 销量异常值分析 ---
    # 1. 首先，按“天”和“单品”聚合，计算出每个单品每一天的总销量
    daily_sales_by_item = merged_df.groupby(['销售日期', '分类名称', '单品名称'])['销量(千克)'].sum().reset_index()
    print("已将数据聚合为各单品的日销量。")

    # 2. 基于聚合后的数据，绘制箱线图，分析各品类下“单品日销量”的分布情况
    plt.figure(figsize=(16, 9))
    sns.boxplot(x='分类名称', y='销量(千克)', data=daily_sales_by_item,
                linewidth=3,
                notch=True,
                palette='Blues'
                )

    plt.title('各品类下【单品日销量】的箱线图分布', fontsize=18)  # 标题更新
    plt.xlabel('蔬菜品类', fontsize=14)
    plt.ylabel('单品日销量(千克)', fontsize=14)  # y轴标签更新
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('daily_volume_outliers_boxplot.png')  # 文件名更新
    print("已生成【单品日销量】异常值箱线图: daily_volume_outliers_boxplot.png")

    # --- 单价异常值分析 (保持不变) ---
    # 分析各品类“销售单价(元/千克)”的分布情况，这部分逻辑不变
    plt.figure(figsize=(16, 9))
    sns.boxplot(x='分类名称', y='销售单价(元/千克)', data=merged_df,
                linewidth=3,
                notch=True,
                palette='Blues'
                )
    plt.title('各品类销售单价的箱线图分布', fontsize=18)
    plt.xlabel('蔬菜品类', fontsize=14)
    plt.ylabel('销售单价(元/千克)', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('price_outliers_boxplot.png')
    print("已生成单价异常值箱线图: price_outliers_boxplot.png")

    print("--- 异常值分析完成 ---\n")
    # ==================================================================
    # --- 结束新增部分 ---
    # ==================================================================

    # --- 第三步: 数据聚合 ---
    
    # 使用 'groupby' 按'销售日期'和'分类名称'对数据进行分组
    # 然后对每个组内的'销量(千克)'进行求和（.sum()）
    # .reset_index() 将分组结果重新变回一个标准的DataFrame
    daily_sales_by_category = merged_df.groupby(['销售日期', '分类名称'])['销量(千克)'].sum().reset_index()



    # --- 第四步: 数据转换与相关性分析 ---

    # 1. 为了计算品类之间的相关性，需要将数据从“长格式”转换为“宽格式”
    #    使用 'pivot_table' 可以轻松实现，索引是日期，列是蔬菜分类，值是销量
    #    .fillna(0) 将表格中的空值（NaN，表示当天该品类无销售）填充为0
    category_pivot_table = daily_sales_by_category.pivot_table(
        index='销售日期',
        columns='分类名称',
        values='销量(千克)'
    ).fillna(0)

    # 2. 调用 .corr() 方法计算皮尔逊相关系数矩阵
    correlation_matrix = category_pivot_table.corr(method='pearson')


    # --- 第五步: 可视化 ---

    # 1. 设置画布大小，让图片更清晰
    plt.figure(figsize=(12, 10))
    
    # 2. 使用 seaborn 的 heatmap 函数绘制热力图
    sns.heatmap(
        correlation_matrix,
        annot=True,          # 在每个格子上显示数值
        mask=np.triu(np.ones_like(correlation_matrix, dtype=bool),k=1),
        cmap=plt.get_cmap('Blues'),     # 使用'coolwarm'颜色方案，正相关为暖色，负相关为冷色
        annot_kws={'size': 16, 'weight': 'normal'},
        linewidths=.5,       # 在格子之间留出少量白色空隙，方便观察
        fmt='.2f'            # 将数值格式化为保留两位小数的浮点数
    )

    # 3. 添加图表的标题和坐标轴标签
    plt.title('各蔬菜品类日销量的相关性分析热力图', fontsize=16)
    plt.xticks(rotation=45, ha='right',fontsize=16) # 将x轴的标签（品类名称）旋转45度，防止重叠
    plt.yticks(rotation=0,fontsize=16) # y轴标签不旋转
    plt.xlabel('分类名称',fontsize=16)
    plt.ylabel('分类名称', fontsize=16)
    plt.tight_layout() # 自动调整布局，确保所有元素都能完整显示

    # 4. 将生成的热力图保存为图片文件
    heatmap_path = 'correlation_heatmap.png'
    plt.savefig(heatmap_path)
    
    print("\n任务完成！相关性热力图已成功保存为: correlation_heatmap.png")
    print("相关性矩阵如下：")
    print(correlation_matrix)


