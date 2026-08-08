import numpy as np
import matplotlib.pyplot as plt
import random
import math
from tqdm import tqdm
import seaborn as sns
import matplotlib.font_manager as fm
import pandas as pd

# 随机生成15个客户的坐标
num_cities = 15
cities_coords = np.random.rand(num_cities, 2) * 100

print("随机生成的客户坐标点 (x, y):")
print(cities_coords)

fm.fontManager.addfont('../../utils/fonts/SourceHanSerifCN-Regular.otf')  # 添加字体
font_name = fm.FontProperties(fname='../../utils/fonts/SourceHanSerifCN-Regular.otf').get_name()
plt.rcParams['font.sans-serif'] = [font_name]
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
    """使用 Seaborn 绘制路线图"""

    # 1. 将坐标数据转换为 Pandas DataFrame，方便 Seaborn 调用
    df_coords = pd.DataFrame(coords, columns=['x', 'y'])

    # 2. 准备路线数据，注意要加上起点来闭合路径
    route_to_plot = route + [route[0]]
    df_path = df_coords.iloc[route_to_plot]

    # 3. 遵循“最佳实践”：先用 plt.subplots 创建 Figure 和 Axes
    # 这样可以完全继承你在 rcParams 中设置的样式
    fig, ax = plt.subplots()

    # 4. 使用 Seaborn 的 Axes-level 函数绘图，并传入 ax
    sns.set_theme(style="darkgrid")
    plt.rcParams['font.sans-serif'] = [font_name]
    plt.rcParams['font.size'] = 14
    plt.rcParams['axes.titlesize'] = 18
    plt.rcParams['axes.labelsize'] = 16
    plt.rcParams['xtick.labelsize'] = 14
    plt.rcParams['ytick.labelsize'] = 14
    # 绘制所有客户位置点
    sns.scatterplot(data=df_coords, x='x', y='y', color='red', s=100, label='客户位置', ax=ax)

    # 突出绘制起点/仓库
    start_node_data = df_coords.iloc[[route[0]]] # 注意用 [[]] 来保持DataFrame格式
    sns.scatterplot(data=start_node_data, x='x', y='y', color='blue', s=250, marker='*', label='起点/仓库', ax=ax, ec='white', zorder=5)

    # 绘制路线
    sns.lineplot(data=df_path, x='x', y='y', color='g', sort=False, ax=ax) # <<< sort=False 是关键！

    # 添加城市编号 (这里仍然可以用 Matplotlib 的 ax 对象来操作，完美兼容)
    for i, row in df_coords.iterrows():
        ax.text(row['x'], row['y'] + 1, str(i))

    # 5. 使用 ax 对象设置标题、标签等
    ax.set_title(title)
    ax.set_xlabel("X 坐标")
    ax.set_ylabel("Y 坐标")
    ax.legend()
    ax.grid(True)

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


# ==================== 2. 新增：蒙特卡洛模拟部分 ====================
def run_monte_carlo_simulation(base_coords, num_simulations, uncertainty_std):
    """
    运行蒙特卡洛模拟进行敏感性分析

    参数:
    base_coords (np.array): 基础的客户坐标
    num_simulations (int): 模拟次数
    uncertainty_std (float): 坐标不确定性的标准差 (可以理解为定位误差的范围)
    """
    print(f"\n===== 开始进行蒙特卡洛模拟 (共 {num_simulations} 次) =====")
    print(f"假设客户位置有标准差为 {uncertainty_std} 的随机扰动...")

    # 存储每次模拟得到的最优距离
    results_distances = []

    # 使用 tqdm 创建一个进度条
    for _ in tqdm(range(num_simulations), desc="蒙特卡洛模拟进度"):
        # 1. 生成新的随机场景：给每个坐标点加上高斯噪声
        noise = np.random.normal(loc=0, scale=uncertainty_std, size=base_coords.shape)
        perturbed_coords = base_coords + noise

        # 2. 在新场景下求解：运行模拟退火算法
        _, best_dist, _ = simulated_annealing(perturbed_coords)

        # 3. 记录结果
        results_distances.append(best_dist)

    return np.array(results_distances)


def plot_mc_results(distances):
    """可视化蒙特卡洛模拟的结果"""
    plt.figure(figsize=(12, 7))
    sns.set_theme(style="darkgrid")
    plt.rcParams['font.sans-serif'] = [font_name]
    plt.rcParams['font.size'] = 14
    plt.rcParams['axes.titlesize'] = 18
    plt.rcParams['axes.labelsize'] = 16
    plt.rcParams['xtick.labelsize'] = 14
    plt.rcParams['ytick.labelsize'] = 14
    sns.histplot(distances, bins=30, edgecolor='black', alpha=0.7)

    mean_dist = np.mean(distances)
    std_dist = np.std(distances)

    plt.axvline(mean_dist, color='r', linestyle='--', linewidth=2, label=f'平均距离: {mean_dist:.2f}')
    plt.title("蒙特卡洛模拟结果：最优总距离的分布")
    plt.xlabel("计算出的最优总距离")
    plt.ylabel("概率密度")
    plt.legend()
    plt.grid(True)

    print("\n===== 蒙特卡洛模拟结果分析 =====")
    print(f"平均最优距离: {mean_dist:.2f}")
    print(f"最优距离的标准差: {std_dist:.2f}")
    print(f"最短可能距离 (Min): {np.min(distances):.2f}")
    print(f"最长可能距离 (Max): {np.max(distances):.2f}")

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

    print("\n--- 步骤 2: 运行蒙特卡洛模拟进行敏感性分析 ---")
    # 运行模拟，假设坐标有1.0个单位的标准差误差
    mc_distances = run_monte_carlo_simulation(cities_coords, num_simulations=500, uncertainty_std=1.0)


    # --- 最后，分析并可视化模拟结果 ---
    print("\n--- 步骤 3: 分析并可视化模拟结果 ---")
    plot_mc_results(mc_distances)