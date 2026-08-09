import os
import math
import numpy as np
from scipy.optimize import differential_evolution, brentq

# ============================================================
# 问题2：FY1投放1枚烟幕弹干扰M1
# ============================================================

# -----------------------------
# 基本参数
# -----------------------------
g = 9.8
missile_speed = 300.0

smoke_radius = 10.0
smoke_sink_speed = 3.0
smoke_valid_time = 20.0

uav_v_min = 70.0
uav_v_max = 140.0

# 初始位置
M1_0 = np.array([20000.0, 0.0, 2000.0])
FY1_0 = np.array([17800.0, 0.0, 1800.0])

# 假目标
fake_target = np.array([0.0, 0.0, 0.0])

# 真目标：下底面圆心、半径、高度
target_bottom_center = np.array([0.0, 200.0, 0.0])
target_radius = 7.0
target_height = 10.0

# M1朝假目标飞行
missile_dir = (fake_target - M1_0) / np.linalg.norm(fake_target - M1_0)
missile_flight_time = np.linalg.norm(fake_target - M1_0) / missile_speed


# ============================================================
# 目标圆柱采样
# ============================================================

def generate_target_points(n_theta=72, n_z=11):
    """
    对真目标圆柱体表面采样。
    n_theta、n_z越大，判据越严格，但计算越慢。
    """
    points = []
    cx, cy, cz = target_bottom_center

    # 圆柱侧面采样
    for z in np.linspace(0.0, target_height, n_z):
        for theta in np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False):
            x = cx + target_radius * np.cos(theta)
            y = cy + target_radius * np.sin(theta)
            points.append([x, y, cz + z])

    # 加入上、下底面圆心和中点
    points.append([cx, cy, cz])
    points.append([cx, cy, cz + target_height])
    points.append([cx, cy, cz + target_height / 2.0])

    return np.array(points, dtype=float)


# 优化时用较粗采样，最终校验用较细采样
target_points_opt = generate_target_points(n_theta=36, n_z=7)
target_points_final = generate_target_points(n_theta=144, n_z=21)


# ============================================================
# 变量说明
# ============================================================
# x = [theta, v, t_explode, tau]
#
# theta      : FY1水平飞行方向角，相对x轴正方向，单位rad
# v          : FY1飞行速度，范围[70, 140]
# t_explode  : 起爆时刻，单位s
# tau        : 投放后到起爆的延时，单位s
#
# 投放时刻：
# t_drop = t_explode - tau
#
# 必须满足：
# t_drop >= 0
# tau >= 0
# v in [70, 140]
# 起爆点高度 > 0


def missile_position(t):
    """M1在时刻t的位置"""
    return M1_0 + missile_speed * t * missile_dir


def unpack_strategy(x):
    """
    由优化变量计算：
    无人机速度向量、投放时刻、投放点、起爆点
    """
    theta, v, t_explode, tau = x

    uav_velocity = np.array([
        v * np.cos(theta),
        v * np.sin(theta),
        0.0
    ])

    t_drop = t_explode - tau

    drop_point = FY1_0 + uav_velocity * t_drop

    explode_point = (
        FY1_0
        + uav_velocity * t_explode
        + np.array([0.0, 0.0, -0.5 * g * tau ** 2])
    )

    return uav_velocity, t_drop, drop_point, explode_point


def is_feasible(x):
    """判断策略是否满足物理约束"""
    theta, v, t_explode, tau = x

    if v < uav_v_min or v > uav_v_max:
        return False

    if tau < 0:
        return False

    if t_explode < tau:
        return False

    if t_explode >= missile_flight_time:
        return False

    _, t_drop, _, explode_point = unpack_strategy(x)

    if t_drop < 0:
        return False

    if explode_point[2] <= 0:
        return False

    return True


# ============================================================
# 遮蔽判据
# ============================================================

def smoke_center(t, x):
    """烟幕云团中心在时刻t的位置"""
    theta, v, t_explode, tau = x
    _, _, _, explode_point = unpack_strategy(x)

    return explode_point + np.array([
        0.0,
        0.0,
        -smoke_sink_speed * (t - t_explode)
    ])


def max_distance_to_sight_lines(t, x, target_points):
    """
    计算时刻t下，烟幕中心到“导弹-目标采样点”视线段的最大距离。
    如果最大距离 <= 烟幕半径，则认为整个目标采样集被遮蔽。
    """
    m_pos = missile_position(t)
    c_pos = smoke_center(t, x)

    A = m_pos
    B = target_points
    P = c_pos

    AB = B - A
    AP = P - A

    s = np.sum(AP * AB, axis=1) / np.sum(AB * AB, axis=1)
    s = np.clip(s, 0.0, 1.0)

    closest = A + s[:, None] * AB

    distances = np.linalg.norm(P - closest, axis=1)

    return np.max(distances)


def is_blocked(t, x, target_points):
    """判断时刻t是否有效遮蔽"""
    theta, v, t_explode, tau = x

    if t < t_explode:
        return False

    if t > t_explode + smoke_valid_time:
        return False

    if t > missile_flight_time:
        return False

    d_max = max_distance_to_sight_lines(t, x, target_points)

    return d_max <= smoke_radius


# ============================================================
# 计算遮蔽时间
# ============================================================

def blocking_duration_scan(x, target_points, dt=0.02):
    """
    用时间扫描法快速估计遮蔽总时长。
    优化阶段使用。
    """
    if not is_feasible(x):
        return 0.0

    theta, v, t_explode, tau = x

    t_start = t_explode
    t_end = min(t_explode + smoke_valid_time, missile_flight_time)

    if t_end <= t_start:
        return 0.0

    times = np.arange(t_start, t_end + dt / 2.0, dt)

    count = 0
    for t in times:
        if is_blocked(t, x, target_points):
            count += 1

    return count * dt


def refined_blocking_intervals(x, target_points, scan_dt=0.01):
    """
    用扫描 + Brent求根精细计算遮蔽区间。
    最终输出阶段使用。
    """
    if not is_feasible(x):
        return []

    theta, v, t_explode, tau = x

    t_start = t_explode
    t_end = min(t_explode + smoke_valid_time, missile_flight_time)

    times = np.arange(t_start, t_end + scan_dt, scan_dt)

    def f(t):
        return max_distance_to_sight_lines(t, x, target_points) - smoke_radius

    f_values = np.array([f(t) for t in times])

    intervals = []
    inside = False
    start_time = None

    for i in range(len(times) - 1):
        f0 = f_values[i]
        f1 = f_values[i + 1]

        # 从未遮蔽进入遮蔽
        if not inside and f0 <= 0:
            if i == 0:
                start_time = times[i]
            else:
                start_time = brentq(f, times[i - 1], times[i])
            inside = True

        # 从遮蔽离开遮蔽
        if inside and f0 <= 0 and f1 > 0:
            end_time = brentq(f, times[i], times[i + 1])
            intervals.append((start_time, end_time))
            inside = False

    if inside:
        intervals.append((start_time, times[-1]))

    return intervals


# ============================================================
# 优化目标函数
# ============================================================

def objective(x):
    """
    差分进化最小化目标。
    我们希望遮蔽时间最大，所以返回负值。
    """
    duration = blocking_duration_scan(
        x,
        target_points_opt,
        dt=0.02
    )
    return -duration


# ============================================================
# 主程序
# ============================================================

def main():
    # 优化变量边界
    # theta: 这里限制在[-0.5, 0.5]，因为最优方向在x轴正方向附近
    # v: [70, 140]
    # t_explode: 起爆时刻
    # tau: 投放到起爆延时
    bounds = [
        (-0.5, 0.5),        # theta
        (70.0, 140.0),      # v
        (0.05, 8.0),        # t_explode
        (0.0, 8.0)          # tau
    ]

    result = differential_evolution(
        objective,
        bounds=bounds,
        maxiter=80,
        popsize=12,
        tol=1e-3,
        seed=8,
        polish=False,
        workers=1
    )

    best_x = result.x

    # 为了避免随机优化偶然偏差，加入一组已经搜索到的较优可行解作为候选
    known_good_x = np.array([
        1.11736114e-01,   # theta
        1.38141918e+02,   # v
        7.85870502e-01,   # t_explode
        6.35977650e-01    # tau
    ])

    candidates = [best_x, known_good_x]

    best_duration = -1.0
    final_x = None

    for x in candidates:
        intervals = refined_blocking_intervals(
            x,
            target_points_final,
            scan_dt=0.01
        )
        duration = sum(b - a for a, b in intervals)

        if duration > best_duration:
            best_duration = duration
            final_x = x

    intervals = refined_blocking_intervals(
        final_x,
        target_points_final,
        scan_dt=0.01
    )

    duration = sum(b - a for a, b in intervals)

    theta, v, t_explode, tau = final_x
    uav_velocity, t_drop, drop_point, explode_point = unpack_strategy(final_x)

    heading_deg = theta * 180.0 / np.pi

    print("问题2：FY1投放1枚烟幕弹干扰M1")
    print("=" * 60)

    print(f"FY1飞行方向角 theta = {heading_deg:.6f} deg")
    print(f"FY1飞行方向单位向量 = ({np.cos(theta):.6f}, {np.sin(theta):.6f}, 0)")
    print(f"FY1飞行速度 v = {v:.6f} m/s")

    print()
    print(f"投放时刻 t_drop = {t_drop:.6f} s")
    print(
        "投放点 = "
        f"({drop_point[0]:.6f}, {drop_point[1]:.6f}, {drop_point[2]:.6f})"
    )

    print()
    print(f"起爆延时 tau = {tau:.6f} s")
    print(f"起爆时刻 t_explode = {t_explode:.6f} s")
    print(
        "起爆点 = "
        f"({explode_point[0]:.6f}, {explode_point[1]:.6f}, {explode_point[2]:.6f})"
    )

    print()
    print("有效遮蔽区间：")
    for a, b in intervals:
        print(f"[{a:.6f}, {b:.6f}] s，持续 {b - a:.6f} s")

    print()
    print(f"总有效遮蔽时长 = {duration:.6f} s")

    # 题目2本身不要求输出文件。
    # 这里按你的要求，额外把结果保存到 ../output/data 里。
    output_dir = "../output/data"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "result2.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("问题2：FY1投放1枚烟幕弹干扰M1\n")
        f.write("=" * 60 + "\n")
        f.write(f"FY1飞行方向角 theta = {heading_deg:.6f} deg\n")
        f.write(
            f"FY1飞行方向单位向量 = "
            f"({np.cos(theta):.6f}, {np.sin(theta):.6f}, 0)\n"
        )
        f.write(f"FY1飞行速度 v = {v:.6f} m/s\n\n")

        f.write(f"投放时刻 t_drop = {t_drop:.6f} s\n")
        f.write(
            "投放点 = "
            f"({drop_point[0]:.6f}, {drop_point[1]:.6f}, {drop_point[2]:.6f})\n\n"
        )

        f.write(f"起爆延时 tau = {tau:.6f} s\n")
        f.write(f"起爆时刻 t_explode = {t_explode:.6f} s\n")
        f.write(
            "起爆点 = "
            f"({explode_point[0]:.6f}, {explode_point[1]:.6f}, {explode_point[2]:.6f})\n\n"
        )

        f.write("有效遮蔽区间：\n")
        for a, b in intervals:
            f.write(f"[{a:.6f}, {b:.6f}] s，持续 {b - a:.6f} s\n")

        f.write(f"\n总有效遮蔽时长 = {duration:.6f} s\n")

    print()
    print(f"结果已保存到：{output_path}")


if __name__ == "__main__":
    main()