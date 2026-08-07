# %%
import numpy as np
import pandas as pd

from IPython.core.interactiveshell import InteractiveShell

InteractiveShell.ast_node_interactivity = "all"


# %%
def plan_lines_deep_to_shallow(
    theta_deg=120,  # 换开角 θ
    alpha_deg=1.5,  # 坡度 α
    eta=0.10,  # 期望重叠率 η  (10 %–20 % 之间取值)
    D_center=110,  # 海域中心深度  (m)
    L_ew_nm=4.0,  # 东-西总跨度 (nmi)
):
    """
    由西(深)向东(潜)逐条布线，返回每条测线的中心横坐标 x 和水深 D。
    x=0 定义在西侧边界，正向指向东侧。
    """
    # 常量与单位换算
    nmi2m = 1852.0
    L_x = L_ew_nm * nmi2m  # 东-西长度 (m)
    theta = np.radians(theta_deg)
    alpha = np.radians(alpha_deg)

    # —— 1. 计算西端(最深)水深 D0 ——
    half_len = L_x / 2  # 西边界到中心距离
    D0 = D_center + half_len * np.tan(alpha)  # 最深处 (x=0) 水深
    # print(f"中心水深 D_center = {D_center:.2f} m")
    # print(f"西端水深 D0 = {D0:.2f} m")

    # —— 2. 第一条测线 ——
    d1 = D0 * np.tan(theta / 2)  # 与边界距离
    D1 = D0 - d1 * np.tan(alpha)  # 第一条测线中心水深
    W1_left = D1 * np.sin(theta / 2) / np.cos(theta / 2 + alpha)
    W1_right = D1 * np.sin(theta / 2) / np.cos(theta / 2 - alpha)
    W1 = W1_left + W1_right  # 第一条测线宽度

    x_list = [d1]  # 第 1 条测线横坐标
    D_list = [D1]  # 第 1 条测线水深
    Wl_list = [W1_left]  # 第 1 条测线左侧宽度
    Wr_list = [W1_right]  # 第 1 条测线右侧宽度
    W_list = [W1]  # 第 1 条测线宽度

    # —— 3. 迭代生成后续测线 ——
    while True:
        Dk = D_list[-1]  # 当前(第 k 条)水深
        Wk = W_list[-1]  # 当前(第 k 条)测线宽度
        # 间距公式  (题设给出)
        # delta = (
        #     (1 - eta)
        #     * Dk
        #     * (1 + np.cos(theta / 2 + alpha) * (1 / np.cos(theta / 2 - alpha)))
        # ) / (1 - np.tan(alpha))
        delta = (
            Wk
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
        next_x = x_list[-1] + delta

        # 到达或超出东侧边界即停止
        if next_x >= L_x:
            break

        # 下一测线水深
        D_next = D0 - next_x * np.tan(alpha)

        # 下一测线宽度
        W_next_left = D_next * np.sin(theta / 2) / np.cos(theta / 2 + alpha)
        W_next_right = D_next * np.sin(theta / 2) / np.cos(theta / 2 - alpha)
        W_next = W_next_left + W_next_right

        x_list.append(next_x)
        D_list.append(D_next)
        Wl_list.append(W_next_left)
        Wr_list.append(W_next_right)
        W_list.append(W_next)

    # ---------- 计算左右边界及重叠 ----------
    x_left = np.array(x_list) - np.array(Wl_list)
    x_right = np.array(x_list) + np.array(Wl_list)

    overlap_start = np.maximum(x_left[:-1], x_left[1:])
    overlap_end = np.minimum(x_right[:-1], x_right[1:])
    overlap_w = np.maximum(0, overlap_end - overlap_start)  # 负值即无重叠
    overlap_eta = np.divide(
        overlap_w, W_list[:-1], out=np.zeros_like(overlap_w), where=W_list[:-1] != 0
    )
    # —— 4. 汇总为 DataFrame ——
    df = pd.DataFrame(
        {
            "line_no": np.arange(1, len(x_list) + 1),
            "x_center(m)": np.round(x_list, 2),
            "depth(m)": np.round(D_list, 2),
            "W_left(m)": np.round(Wl_list, 2),
            "W_right(m)": np.round(Wr_list, 2),
            "W_total(m)": np.round(W_list, 2),
            "x_left(m)": np.round(x_left, 2),
            "x_right(m)": np.round(x_right, 2),
        }
    )

    # 把与前一条的重叠信息另存一张表，便于绘图
    df_overlap = pd.DataFrame(
        {
            "pair_k/k+1": df["line_no"][:-1],
            "ov_start(m)": np.round(overlap_start, 2),
            "ov_end(m)": np.round(overlap_end, 2),
            "ov_width(m)": np.round(overlap_w, 2),
            "ov_ratio(k)": np.round(overlap_eta * 100, 2),  # 与第 k 条条带相比的百分比
        }
    )

    return df, df_overlap


# %%
df_lines, df_ov = plan_lines_deep_to_shallow()
df_lines
df_ov.head()

L_sn_nm = 2.0  # 南-北总跨度 (nmi)
line_num = len(df_lines)
tot = L_sn_nm * line_num  # 总长度 (nmi)
print(f"测线数量 = {line_num}")
print(f"总长度 = {tot:.2f} nmi")
df_lines.to_excel("stats/result3_lines_info.xlsx", index=False)
df_ov.to_excel("stats/result3_overlap_info.xlsx", index=False)
print("Saved to result3_lines_info.xlsx and result3_overlap_info.xlsx")

# %%
