import numpy as np

# =========================
# 基本参数
# =========================

g = 9.8                    # 重力加速度, m/s^2
missile_speed = 300.0      # 导弹速度, m/s
uav_speed = 120.0          # FY1速度, m/s

smoke_radius = 10.0        # 烟幕有效半径, m
smoke_sink_speed = 3.0     # 烟幕云团下沉速度, m/s
smoke_valid_time = 20.0    # 起爆后有效时间, s

# 初始位置
M1_0 = np.array([20000.0, 0.0, 2000.0])
FY1_0 = np.array([17800.0, 0.0, 1800.0])

# 假目标在原点
fake_target = np.array([0.0, 0.0, 0.0])

# 真目标：圆柱体
target_center_bottom = np.array([0.0, 200.0, 0.0])
target_radius = 7.0
target_height = 10.0

# 投放与起爆时间
drop_delay = 1.5           # 受领任务后1.5s投放
explode_delay = 3.6        # 投放后3.6s起爆
explode_time = drop_delay + explode_delay


# =========================
# 轨迹函数
# =========================

def unit_vector(v):
    """返回单位向量"""
    norm = np.linalg.norm(v)
    if norm == 0:
        raise ValueError("零向量不能归一化")
    return v / norm


# 导弹 M1 朝假目标方向飞行
missile_dir = unit_vector(fake_target - M1_0)

def missile_position(t):
    """M1在时刻t的位置"""
    return M1_0 + missile_speed * t * missile_dir


# FY1 朝假目标方向飞行，但等高度，所以只取水平面方向
fy1_horizontal_dir = np.array([-1.0, 0.0, 0.0])

def uav_position(t):
    """FY1在时刻t的位置"""
    return FY1_0 + uav_speed * t * fy1_horizontal_dir


# 投放点
drop_point = uav_position(drop_delay)

# 烟幕弹投放后，水平速度等于无人机速度，竖直方向自由落体
bomb_velocity = uav_speed * fy1_horizontal_dir

def bomb_position_after_drop(t_after_drop):
    """
    烟幕弹脱离无人机后的运动位置
    t_after_drop: 投放后的时间
    """
    return drop_point + bomb_velocity * t_after_drop + np.array(
        [0.0, 0.0, -0.5 * g * t_after_drop ** 2]
    )


# 起爆点
explode_point = bomb_position_after_drop(explode_delay)

def smoke_center(t):
    """起爆后烟幕云团中心位置"""
    if t < explode_time:
        return None
    return explode_point + np.array(
        [0.0, 0.0, -smoke_sink_speed * (t - explode_time)]
    )


# =========================
# 真目标圆柱采样
# =========================

def generate_cylinder_points(n_theta=72, n_z=11):
    """
    生成真目标圆柱体表面和上下底面边界采样点。
    为了判断整体遮蔽，这里采样圆柱侧面和上下圆周。
    """
    points = []

    cx, cy, cz = target_center_bottom

    # 侧面采样
    for z in np.linspace(0.0, target_height, n_z):
        for theta in np.linspace(0.0, 2 * np.pi, n_theta, endpoint=False):
            x = cx + target_radius * np.cos(theta)
            y = cy + target_radius * np.sin(theta)
            points.append([x, y, cz + z])

    # 上下底面圆心也加入
    points.append([cx, cy, cz])
    points.append([cx, cy, cz + target_height])

    return np.array(points)


target_points = generate_cylinder_points()


# =========================
# 几何遮蔽判定
# =========================

def distance_point_to_segment(P, A, B):
    """
    计算点P到线段AB的最短距离。
    这里A为导弹位置，B为目标采样点。
    """
    AB = B - A
    AP = P - A

    denom = np.dot(AB, AB)
    if denom == 0:
        return np.linalg.norm(P - A)

    s = np.dot(AP, AB) / denom
    s = np.clip(s, 0.0, 1.0)

    closest = A + s * AB
    return np.linalg.norm(P - closest)


def is_point_blocked(missile_pos, smoke_pos, target_point):
    """
    判断烟幕球是否遮挡导弹到目标采样点的视线。
    """
    d = distance_point_to_segment(smoke_pos, missile_pos, target_point)
    return d <= smoke_radius


def is_target_blocked(t):
    """
    判断时刻t真目标是否被有效遮蔽。
    采用严格判据：所有采样点均被烟幕遮挡。
    """
    if t < explode_time or t > explode_time + smoke_valid_time:
        return False

    m_pos = missile_position(t)
    s_pos = smoke_center(t)

    for p in target_points:
        if not is_point_blocked(m_pos, s_pos, p):
            return False

    return True


# =========================
# 数值搜索有效遮蔽时间
# =========================

def compute_blocking_time(dt=0.001):
    """
    逐步扫描烟幕有效时间段，计算总遮蔽时长。
    dt越小，结果越精确，但计算越慢。
    """
    t_start = explode_time
    t_end = explode_time + smoke_valid_time

    times = np.arange(t_start, t_end + dt, dt)
    blocked = np.array([is_target_blocked(t) for t in times])

    total_time = np.sum(blocked) * dt

    # 提取遮蔽区间
    intervals = []
    in_interval = False
    start = None

    for i in range(len(times)):
        if blocked[i] and not in_interval:
            start = times[i]
            in_interval = True

        if in_interval and (not blocked[i] or i == len(times) - 1):
            end = times[i - 1] if not blocked[i] else times[i]
            intervals.append((start, end))
            in_interval = False

    return total_time, intervals


# =========================
# 主程序
# =========================

if __name__ == "__main__":
    total_time, intervals = compute_blocking_time(dt=0.001)

    print("问题1计算结果")
    print("=" * 40)

    print(f"FY1投放点: ({drop_point[0]:.3f}, {drop_point[1]:.3f}, {drop_point[2]:.3f})")
    print(f"烟幕弹起爆点: ({explode_point[0]:.3f}, {explode_point[1]:.3f}, {explode_point[2]:.3f})")
    print(f"起爆时刻: {explode_time:.3f} s")

    print("\n有效遮蔽区间:")
    for a, b in intervals:
        print(f"[{a:.4f}, {b:.4f}] s，持续 {b - a:.4f} s")

    print(f"\n总有效遮蔽时长: {total_time:.4f} s")