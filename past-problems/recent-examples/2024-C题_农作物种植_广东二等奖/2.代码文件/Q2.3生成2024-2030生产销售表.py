import pandas as pd
import numpy as np
from scipy.stats import truncnorm
for year in range(2024,2031):
    last_year = pd.read_csv(f"preprocessed_data/整理数据/Q2/{year - 1}/{year - 1}年生产销售表.csv",
                            encoding='gbk')
    #亩产量处理
    # 定义截断正态分布的参数
    mu = 0
    sigma = 0.1 / 3
    a, b = -0.1, 0.1
    # 标准化截断区间
    a_standard = (a - mu) / sigma
    b_standard = (b - mu) / sigma
    # 生成标准正态分布的随机数
    size = len(last_year)  # 生成随机数的数量与 DataFrame 的行数相同
    z = truncnorm.rvs(a_standard, b_standard, size=size)
    # 反标准化
    r = mu + sigma * z
    # 将 df 中的亩产量/斤列乘以 (1 + r)
    last_year['亩产量/斤'] = last_year['亩产量/斤'] * (1 + r)


    #种植成本处理
    last_year['种植成本/(元/亩)']=last_year['种植成本/(元/亩)']*(1+0.05)
    r_list = np.zeros(len(last_year))
    # 对于作物编号在[1,16]区间内，不变
    # 对于作物编号在[17,37]区间内，增长5%
    r_list[(last_year['作物编号'] >= 17) & (last_year['作物编号'] <= 37)] = 0.05
    # 对于作物编号在[38,40]区间内，使用截断正态分布生成随机数 r
    mu2 = -0.03
    sigma2 = 0.02 / 3
    a2, b2 = -0.05, -0.01
    # 标准化截断区间
    a2_standard = (a2 - mu2) / sigma2
    b2_standard = (b2 - mu2) / sigma2
    # 生成标准正态分布的随机数
    size = len(last_year[(last_year['作物编号'] >= 38) & (last_year['作物编号'] <= 40)])  # 生成随机数的数量
    z2 = truncnorm.rvs(a2_standard, b2_standard, size=size)
    # 反标准化
    r2 = mu2 + sigma2 * z2
    # 将 r_list 中的对应位置设置为生成的 r 值
    r_list[(last_year['作物编号'] >= 38) & (last_year['作物编号'] <= 40)] = r2
    # 对于作物编号在[41,41]区间内，减少5%
    r_list[(last_year['作物编号'] == 41)] = -0.05
    # 将 df 中的确切销售单价/(元/斤) 列乘以 (1 + r_list)
    last_year['确切销售单价/(元/斤)'] = last_year['确切销售单价/(元/斤)'] * (1 + r_list)
    this_year=last_year
    this_year.to_csv(f"preprocessed_data/整理数据/Q2/{year}/{year}年生产销售表.csv", encoding='gbk', index=False)


