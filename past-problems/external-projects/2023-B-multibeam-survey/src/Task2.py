import numpy as np
import pandas as pd

from IPython.core.interactiveshell import InteractiveShell

InteractiveShell.ast_node_interactivity = "all"

# %%
# 参数设置
theta_deg = 120  # 开角（度）
alpha_deg = 1.5  # 坡度（度）
# beta_deg = 0  # 侧向角（度）
beta_list = np.arange(0, 360, 45)  # 侧向角（度），从0到360度，每45度一个值
D0 = 120  # 中心深度（米）
d = 0.3  # 测线间距（海里）
d_range_ = np.arange(0, 2.2, d)  # 沿测线距离（海里）
d_range = d_range_ * 1852  # 1 海里 = 1852 米
print(
    f"参数设置:\n开角 θ: {theta_deg}°\n"
    f"坡度 α: {alpha_deg}°\n"
    f"侧向角 β: {beta_list}°\n"
    f"中心深度 D0: {D0} 米\n"
    f"测线间距 d: {d} 海里\n"
    f"沿测线距离范围: {d_range} 米"
)

# %%
# 转换为弧度
theta = np.radians(theta_deg)
beta_list = np.radians(beta_list)  # 侧向角（弧度）
# beta = np.radians(beta_deg)
alpha = np.radians(alpha_deg)

# %%
results = []

for beta in beta_list:
    # 坡度在当前方向的有效分量
    # alpha_ = np.arcsin(np.sin(alpha) * np.cos(beta))
    # alpha_ = np.arctan(np.tan(alpha) * np.cos(beta))
    alpha_ = np.arctan(np.tan(alpha) * np.abs(np.sin(beta)))
    print(f"\n计算侧向角 β = {np.degrees(beta)}° 时的坡度 α' = {np.degrees(alpha_)}°")
    # D = D0 + d_range * np.tan(alpha_)
    D = D0 + d_range * np.tan(alpha) * np.cos(beta)
    print(f"计算得到的深度 D:\n{D}")
    W_left = D * np.sin(theta / 2) / np.cos(theta / 2 + alpha_)
    W_right = D * np.sin(theta / 2) / np.cos(theta / 2 - alpha_)
    W_total = W_left + W_right
    # print(f"计算得到的覆盖宽度 W:\n{W_total}")

    df_beta = pd.DataFrame(
        {
            "beta": np.degrees(beta).astype(int),  # 将弧度转换为整数度数
            "d_range": d_range_,
            "D": D,
            # 'W_left': W_left,
            # 'W_right': W_right,
            "W_total": W_total,
        }
    )
    print(df_beta)
    results.append(df_beta)


# %%
df_all = pd.concat(results, ignore_index=True)
# 保证 d_range 是 float
df_all["d_range"] = df_all["d_range"].astype(float)
# 保留一位小数（注意：建议用 round 再用 astype 保证不会有浮点数精度误差导致的 0.30000000004 这类情况）
df_all["d_range"] = df_all["d_range"].round(1)
df_all

# %%
df_pivot = df_all.pivot(index="beta", columns="d_range", values="W_total")
df_pivot.columns = [f"{c:.1f}" for c in df_pivot.columns]
df_pivot.columns.name = "d_range (海里)"
df_pivot.index.name = "测线方向夹角 β/°"
df_pivot.style.format("{:.2f}")

# %%
output_file = "result2.xlsx"
df_pivot.to_excel(output_file, index=True)
print(f"结果已保存到 {output_file}")

# %%
# # 计算重叠率
# # 对于每对相邻测线（x_i, x_{i+1}），第1条的右宽度+第2条的左宽度
# W1r = W_right[:-1]    # 第i条右宽度
# W2l = W_left[1:]      # 第i+1条左宽度
# overlap = 1 - d / ((W1r + W2l) * np.cos(alpha))  # 重叠率

# print(f"计算得到的重叠率:\n{overlap}")

# %%
