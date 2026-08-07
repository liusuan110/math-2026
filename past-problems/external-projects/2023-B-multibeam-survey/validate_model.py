############################  validate_model.py  ############################
"""
模型检验：解析法 vs 三维矢量交点法
---------------------------------
随机采样 (θ, α, D, β) 参量各 N 组，比对两方法条带总宽度 W_total，输出：
1) scatter_diff.png：误差散点图（对数坐标）
2) diff_stat.csv    ：最大/平均/95%误差
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ---------- 封装：解析计算 ----------
def width_analytic(D, theta, alpha, beta):
    """解析公式：问题1/2的覆盖宽度，theta/alpha/beta 均为弧度"""
    alpha_perp = np.arctan(np.tan(alpha) * np.abs(np.sin(beta)))
    W_left = D * np.sin(theta / 2) / np.cos(theta / 2 + alpha_perp)
    W_right = D * np.sin(theta / 2) / np.cos(theta / 2 - alpha_perp)
    return W_left + W_right


# ---------- 封装：三维矢量交点法 ----------
def width_3d(D, theta, alpha, beta):
    """
    正确的三维射线交点宽度计算
    参数均为弧度；坡降线沿 +x 方向
    """
    P = np.array([0.0, 0.0, D])  # 船下探头坐标
    n = np.array([np.sin(alpha), 0.0, np.cos(alpha)])  # 坡面法向

    # 水平航向向量
    sinb, cosb = np.sin(beta), np.cos(beta)
    hor = np.sin(theta / 2.0)  # 水平幅值
    ver = -np.cos(theta / 2.0)  # 垂直分量（向下）

    # 左、右最外束在 3-D 坐标系中的单位方向
    v_left = np.array([-hor * sinb, hor * cosb, ver])
    v_right = np.array([hor * sinb, -hor * cosb, ver])
    v_left /= np.linalg.norm(v_left)
    v_right /= np.linalg.norm(v_right)

    tL = -np.dot(n, P) / np.dot(n, v_left)
    tR = -np.dot(n, P) / np.dot(n, v_right)
    QL = P + tL * v_left
    QR = P + tR * v_right
    return np.linalg.norm(QR - QL)


# ---------- 主程序 ----------
if __name__ == "__main__":
    N = 2000  # 样本规模
    rng = np.random.default_rng(2025)

    theta = np.deg2rad(rng.uniform(90, 140, N))  # [90°,140°]
    alpha = np.deg2rad(rng.uniform(0.2, 3.0, N))  # [0.2°,3°]
    D = rng.uniform(50, 200, N)  # [50,200] m
    beta = np.deg2rad(rng.uniform(0, 360, N))  # [0°,360°]

    Wan = width_analytic(D, theta, alpha, beta)
    W3d = np.array([width_3d(D[i], theta[i], alpha[i], beta[i]) for i in range(N)])
    rel_err = np.abs(Wan - W3d) / W3d  # 相对误差

    df = pd.DataFrame({
        "theta_deg": np.rad2deg(theta),
        "alpha_deg": np.rad2deg(alpha),
        "D0": D,
        "beta_deg": np.rad2deg(beta),
        "W_analytic": Wan,
        "W_3d": W3d,
        "rel_err": rel_err,
    })

    # 结果汇总
    df.to_csv("stats/validate_diff.csv", index=False)
    print("结果已保存到 'stats/validate_diff.csv'")
    stat = pd.Series(
        [rel_err.max() * 100, rel_err.mean() * 100, np.percentile(rel_err, 95) * 100],
        index=["Max(%)", "Mean(%)", "95th(%)"],
    ).round(4)
    # stat.to_csv("stats/validate_diff_stat.csv")
    print("误差统计:\n", stat)

    # # 绘图
    # plt.figure(figsize=(6, 4))
    # plt.loglog(W3d, np.abs(Wan - W3d), ".", alpha=0.6)
    # plt.xlabel("W_total by 3-D method (m)")
    # plt.ylabel("|ΔW|  (m)")
    # plt.title("Analytic vs 3-D  width difference")
    # plt.grid(True, which="both", ls="--", alpha=0.3)
    # plt.tight_layout()
    # plt.savefig("scatter_diff.png", dpi=300)
    # print("误差统计:\n", stat)
