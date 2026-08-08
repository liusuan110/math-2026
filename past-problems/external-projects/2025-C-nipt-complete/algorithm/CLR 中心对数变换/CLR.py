import numpy as np
from skbio.stats.composition import clr

data = np.array([0.1, 0.2, 0.4, 0.1, 0.2])  # 成分数据的总和是 1.0
lr_data_func = clr(data)
print("CLR 变换后的数据")
print(lr_data_func)

# print("\n手动计算验证")
# log_data = np.log(data)  # 计算数据的对数
# mean_log_data = np.mean(log_data)  # 计算对数数据的算术平均值 (这等价于原始数据的对数几何平均值)
# clr_data_manual = log_data - mean_log_data
# print(clr_data_manual)
