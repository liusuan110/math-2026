import pandas as pd
from scipy.stats import truncnorm
import numpy as np
for year in range(2024,2031):
    last_year=pd.read_csv(f"preprocessed_data/整理数据/Q2/{year-1}/{year-1}年农作物预期销量表.csv",encoding='gbk')
    # 定义截断正态分布的参数
    mu_default = 0
    sigma_default = 0.05 / 3
    a_default, b_default = -0.05, 0.05

    mu_6 = 0.075
    sigma_6 = 0.025 / 3
    a_6, b_6 = 0.05, 0.1
    size = last_year.shape[0]
    results = []


    for i in range(5):
        a_standard = (a_default - mu_default) / sigma_default
        b_standard = (b_default - mu_default) / sigma_default
        z = truncnorm.rvs(a_standard, b_standard, size=1)
        r = mu_default + sigma_default * z
        results.append(r)

    a_standard_6 = (a_6 - mu_6) / sigma_6
    b_standard_6 = (b_6 - mu_6) / sigma_6
    z_6 = truncnorm.rvs(a_standard_6, b_standard_6, size=1)
    r_6 = mu_6 + sigma_6 * z_6
    results.append(r_6)

    a_standard_7 = (a_6 - mu_6) / sigma_6
    b_standard_7 = (b_6 - mu_6) / sigma_6
    z_7 = truncnorm.rvs(a_standard_7, b_standard_7, size=1)
    r_7 = mu_6 + sigma_6 * z_7
    results.append(r_7)

    for i in range(6, size-1):
        a_standard = (a_default - mu_default) / sigma_default
        b_standard = (b_default - mu_default) / sigma_default
        z = truncnorm.rvs(a_standard, b_standard, size=1)
        r = mu_default + sigma_default * z
        results.append(r)

    # 将结果转换为numpy数组
    results = np.array(results).flatten()
    last_year.iloc[:, 2] = last_year.iloc[:, 2] * (results + 1)
    this_year=last_year
    this_year.to_csv(f"preprocessed_data/整理数据/Q2/{year}/{year}年农作物预期销量表.csv",encoding='gbk',index=False)

