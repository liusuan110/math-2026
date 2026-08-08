import numpy as np
import matplotlib.pyplot as plt
import random
import math


# 随机生成15个客户的坐标
num_cities = 15
cities_coords = np.random.rand(num_cities, 2) * 100

print("随机生成的客户坐标点 (x, y):")
print(cities_coords)

plt.rcParams['font.sans-serif'] = 'SimHei'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'  # 保存后自动裁剪白边
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'


def calculate_total_distance(route, coords):
    """计算一条路线的总距离"""
    total_dist = 0
    num = len(route)
    for i in range(num):
        # 从当前城市到下一个城市
        current_city_idx = route[i]
        # 如果是最后一个城市，则下一个是起点
        next_city_idx = route[(i + 1) % num]

        # 使用欧几里得距离 (勾股定理)
        # 这里用了线性代数里的二范数，其实二范数就是代表两点之间的距离，这样写更简洁
        dist = np.linalg.norm(coords[current_city_idx] - coords[next_city_idx])
        total_dist += dist
    return total_dist


def simulated_annealing(coords):
    """模拟退火算法主函数"""

    num = len(coords)
    T_initial = 1000.0  # 初始温度 (能量很足的弹球)
    T_final = 1e-8  # 最终温度 (几乎静止的弹球)
    alpha = 0.99  # 降温速率

    # 生成一条随机的初始路线 (0, 1, 2, ..., 14)
    current_route = list(range(num))
    random.shuffle(current_route)
    current_distance = calculate_total_distance(current_route, coords)

    # 记录历史最佳路线
    best_route = current_route.copy()
    best_distance = current_distance

    # 用于绘图，记录每次迭代的距离
    history_distances = [current_distance]

    T = T_initial

    # --- (2) 核心退火循环 ---
    while T > T_final:
        # 在当前温度下迭代一定次数 (这里简化为1次，也可以设置内循环)

        # --- (2.1) 生成新解：随机交换两个城市的位置 ---
        # 这种方法叫 "2-opt"，简单来说就是把交叉的路线解开，逐渐逼近最短路径
        new_route = current_route.copy()
        i, j = random.sample(range(num), 2)  # 随机取两个不同的索引
        new_route[i], new_route[j] = new_route[j], new_route[i]  # 交换

        new_distance = calculate_total_distance(new_route, coords)

        # --- (2.2) 判断是否接受新解 ---
        # 计算能量差 (距离差)
        delta_E = new_distance - current_distance

        # 如果新解更优 (距离更短)，直接接受
        if delta_E < 0:
            current_route = new_route
            current_distance = new_distance
            # 如果比历史最佳还好，更新历史最佳
            if new_distance < best_distance:
                best_route = new_route
                best_distance = new_distance
        # 如果新解更差，以一定概率接受 (模拟高温时的跳出)
        else:
            # 计算接受概率
            acceptance_prob = math.exp(-delta_E / T)
            if random.random() < acceptance_prob:
                current_route = new_route
                current_distance = new_distance

        # --- (2.3) 降温 ---
        T *= alpha
        history_distances.append(best_distance)

    return best_route, best_distance, history_distances


def plot_route(route, coords, title):
    """绘制路线图"""
    plt.figure(figsize=(8, 8))

    # 绘制城市点
    plt.scatter(coords[:, 0], coords[:, 1], c='red', s=100, label='客户位置')
    plt.scatter(coords[route[0], 0], coords[route[0], 1], c='blue', s=200, marker='*', label='起点/仓库')

    # 绘制路线
    ordered_coords = coords[route]
    # 闭合路线
    path_coords = np.vstack([ordered_coords, ordered_coords[0]])

    plt.plot(path_coords[:, 0], path_coords[:, 1], 'g-')

    # 添加城市编号
    for i, (x, y) in enumerate(coords):
        plt.text(x, y + 1, str(i))

    plt.title(title)
    plt.xlabel("X 坐标")
    plt.ylabel("Y 坐标")
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_convergence(history):
    """绘制收敛曲线"""
    plt.figure(figsize=(10, 5))
    plt.plot(history)
    plt.title("算法收敛过程")
    plt.xlabel("迭代次数")
    plt.ylabel("最短总距离")
    plt.grid(True)
    plt.show()


# ==================== 3. 运行算法并可视化 ====================
if __name__ == "__main__":
    # 计算初始随机路线的距离并绘图
    initial_route = list(range(num_cities))
    initial_distance = calculate_total_distance(initial_route, cities_coords)
    print(f"初始随机路线的总距离: {initial_distance:.2f}")
    plot_route(initial_route, cities_coords, f"初始随机路线 (总距离: {initial_distance:.2f})")

    # 运行模拟退火算法
    print("\n开始运行模拟退火算法...")
    best_route_sa, best_distance_sa, history = simulated_annealing(cities_coords)
    print(f"模拟退火找到的最优路线: {best_route_sa}")
    print(f"最优路线的总距离: {best_distance_sa:.2f}")

    # 绘制优化后的路线和收敛曲线
    plot_route(best_route_sa, cities_coords, f"模拟退火优化后路线 (总距离: {best_distance_sa:.2f})")
    plot_convergence(history)