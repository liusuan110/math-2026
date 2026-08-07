####################### sobol_analysis_fast.py ########################
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# from SALib.sample import sobol
from SALib.sample import saltelli
from SALib.analyze import sobol

# ---- 1. 参数与问题定义 ----
problem = {
    "num_vars": 4,
    "names": ["theta_deg", "alpha_deg", "eta", "D0"],
    "bounds": [[90, 140], [0.2, 3.0], [0.10, 0.20], [50, 200]],  # θ  # α  # η  # D0
}


# ---- 2. 快速递推：单组参数下测线总长 ----
def plan_len_batch(D0, theta, alpha, eta, Lx=4 * 1852, max_lines=60):
    """
    矢量化批量递推，输入 shape=(N,) 的参数组，返回每组的测线条数和总长度(海里)
    """
    N = D0.size
    d1 = D0 * np.tan(theta / 2)
    x = np.zeros((max_lines, N))
    D = np.zeros((max_lines, N))
    x[0, :] = d1
    D[0, :] = D0 - d1 * np.tan(alpha)
    lines = np.ones(N, dtype=int)
    done = np.zeros(N, dtype=bool)
    for k in range(1, max_lines):
        W = (
            D[k - 1, :]
            * np.sin(theta / 2)
            * (1 / np.cos(theta / 2 + alpha) + 1 / np.cos(theta / 2 - alpha))
        )
        delta = (
            W
            * (1 - eta)
            * np.cos(alpha)
            / (
                1
                + np.sin(alpha)
                * np.sin(theta / 2)
                / np.cos(theta / 2 + alpha)
                * (1 - eta)
            )
        )
        x[k, :] = x[k - 1, :] + delta
        D[k, :] = D[k - 1, :] - delta * np.tan(alpha)
        not_done = (x[k, :] < Lx) & (~done)
        lines += not_done
        done |= ~not_done
    # 最后加上尾段
    tail = Lx - x[lines - 1, np.arange(N)]
    lengths = np.sum(
        np.diff(np.vstack([np.zeros(N), x[: max(lines), :]]), axis=0), axis=0
    )
    lengths += tail
    return lines, lengths / 1852


# ---- 3. 样本生成与模型输出 ----
N_base = 2048  # Sobol序列基础规模，2^n 推荐
param_values = saltelli.sample(problem, N_base, calc_second_order=False)
theta = np.deg2rad(param_values[:, 0])
alpha = np.deg2rad(param_values[:, 1])
eta = param_values[:, 2]
D0 = param_values[:, 3]
Nall = theta.size

# 中心条带宽度（矢量化直接算）
Wmid = (
    D0
    * np.sin(theta / 2)
    * (1 / np.cos(theta / 2 + alpha) + 1 / np.cos(theta / 2 - alpha))
)

# 总测线长度和数量
lines, Lsum = plan_len_batch(D0, theta, alpha, eta)

# ---- 4. Sobol灵敏度分析 ----
Si_W = sobol.analyze(problem, Wmid, calc_second_order=False, print_to_console=False)
Si_L = sobol.analyze(problem, Lsum, calc_second_order=False, print_to_console=False)
index = ["θ", "α", "η", "D₀"]
sobol_df = pd.DataFrame(
    {
        "S1_Wmid": Si_W["S1"],
        "ST_Wmid": Si_W["ST"],
        "S1_Lsum": Si_L["S1"],
        "ST_Lsum": Si_L["ST"],
    },
    index=index,
).round(4)
output_path = "stats/sobol_indices.csv"
sobol_df.to_csv(output_path)
print("Sobol 指数:\n", sobol_df)
print(f"Sobol 指数已保存到 {output_path}")


# # ---- 5. 可视化 ----
# def plot_bar(ax, S1, ST, title):
#     pos = np.arange(len(index))
#     ax.bar(pos - 0.15, S1, width=0.3, label="S1")
#     ax.bar(pos + 0.15, ST, width=0.3, label="ST")
#     ax.set_xticks(pos)
#     ax.set_xticklabels(index)
#     ax.set_ylim(0, 1)
#     ax.set_ylabel("Sobol index")
#     ax.set_title(title)
#     ax.grid(ls="--", alpha=0.3)


# fig, ax = plt.subplots(1, 2, figsize=(9, 3.5))
# plot_bar(ax[0], sobol_df["S1_Wmid"], sobol_df["ST_Wmid"], "Wmid")
# plot_bar(ax[1], sobol_df["S1_Lsum"], sobol_df["ST_Lsum"], "Lsum (nmi)")
# ax[1].legend()
# plt.tight_layout()
# plt.savefig("sobol_Wmid_Lsum.png", dpi=300)
