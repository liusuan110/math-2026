# %%
import numpy as np
import pandas as pd

from IPython.core.interactiveshell import InteractiveShell

InteractiveShell.ast_node_interactivity = "all"

# %%
# 参数设置
theta_deg = 120  # 开角（度）
alpha_deg = 1.5  # 坡度（度）
D0 = 70  # 中心深度（米）
d = 200  # 测线间距（米）
d_range = np.arange(-800, 801, d)  # 沿测线距离（米）
print(
    f"参数设置:\n开角 θ: {theta_deg}°\n"
    f"坡度 α: {alpha_deg}°\n"
    f"中心深度 D0: {D0} 米\n"
    f"测线间距 d: {d} 米\n"
    f"沿测线距离范围: {d_range} 米\n"
)

theta = np.radians(theta_deg)  # 转换为弧度
alpha = np.radians(alpha_deg)  # 转换为弧度

D = D0 - d_range * np.tan(alpha)  # 水的深度（米）
print(f"计算得到的深度 D:\n{D}")

# %%
# 覆盖宽度
W_left = D * np.sin(theta / 2) / np.cos(theta / 2 + alpha)
W_right = D * np.sin(theta / 2) / np.cos(theta / 2 - alpha)
W = W_left + W_right  # 总覆盖宽度（米）
print(f"计算得到的覆盖宽度 W:\n{W}")

# %%
# 计算重叠率
# 对于每对相邻测线（x_i, x_{i+1}），第1条的右宽度+第2条的左宽度
W1r = W_right[:-1]  # 第i条右宽度
W2l = W_left[1:]  # 第i+1条左宽度
overlap = 1 - d / ((W1r + W2l) * np.cos(alpha))  # 重叠率

print(f"计算得到的重叠率:\n{overlap}")


# %%
data = {
    "D": D,
    "W_left": W_left,
    "W_right": W_right,
    "W_total": W,
    "overlap": np.append(np.nan, overlap) * 100,  # 重叠率转换为百分比
}

df = pd.DataFrame(data, index=d_range).T
df.columns = d_range
df.columns.name = "d_range"
df
df.style.format("{:.2f}")

# 保存结果到CSV文件
output_file = "result1.xlsx"
df.to_excel(output_file, index=True)
print(f"结果已保存到 {output_file}")
