import pandas as pd
shengchanxiaoshou=pd.read_csv("preprocessed_data/整理数据/Q1/2023年生产销售表.csv",encoding='gbk')
yuqixiaoshou=pd.read_csv("preprocessed_data/整理数据/Q1/2023年农作物预期销量表.csv",encoding='gbk')
huiseguanlian=pd.merge(shengchanxiaoshou,yuqixiaoshou,on=['作物名称','种植季次','作物编号'],how='left')
huiseguanlian.to_csv("preprocessed_data/整理数据/Q3/灰色关联分析表.csv",encoding='gbk',index=False)

# import numpy
# import pandas
# from spsspro.algorithm import quantify_analysis
# #生成案例数据
# f = pandas.DataFrame({
#     "A": [1, 2, 3, 4, 5],
#     "D": [10, 20, 30, 40, 50]
# })
# m = pandas.Series([1, 2, 3, 4, 5], name="B")
# i = pandas.Series([1, 2, 3, 4, 5], name="C")
# #灰色关联分析，输入参数详细可以光标放置函数括号内按shift+tab查看，输出结果参考spsspro模板分析报告
# print(quantify_analysis.grey_relational_analysis(f, m, i))