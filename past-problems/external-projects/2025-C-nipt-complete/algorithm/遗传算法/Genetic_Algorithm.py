import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from cycler import cycler

# -- 图片预设，需要 plt, fm, cycler 库
fm.fontManager.addfont('../../utils/fonts/SourceHanSerifCN-Regular.otf')  # 添加字体
font_name = fm.FontProperties(fname='../../utils/fonts/SourceHanSerifCN-Regular.otf').get_name()
plt.rcParams['font.sans-serif'] = [font_name]
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
plt.rcParams['axes.prop_cycle'] = cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
plt.rcParams['axes.unicode_minus'] = False
# -- 图片预设

# 城市坐标
# 随机生成15个城市的坐标，范围在 (0, 100)
# cities_coordinates = np.array([
#     [random.randint(0, 100), random.randint(0, 100)] for _ in range(15)
# ])

# 固定坐标
cities_coordinates = np.array([
    [18, 65], [73, 22], [39, 88], [91, 47], [5, 53],
    [68, 93], [27, 14], [85, 76], [42, 31], [11, 80],
    [79, 10], [33, 59], [96, 68], [54, 28], [20, 41],
    [45, 60], [55, 55], [23, 78], [67, 25], [89, 34],
    [38, 29], [17, 63], [59, 16], [24, 51], [90, 40],
    [15, 90], [64, 95], [88, 72], [50, 19], [34, 39],
    [92, 17], [13, 54], [47, 42], [82, 57], [56, 22],
    [69, 44], [40, 86], [72, 50], [37, 94], [99, 87],
    [51, 30], [28, 69], [81, 11], [24, 37], [77, 63]
])

num_cities = len(cities_coordinates)

# 计算两个城市间的欧氏距离
def calculate_distance(p1, p2):
    return np.sqrt(np.sum((p1 - p2)**2))

# 计算染色体（路径）的总距离
def calculate_total_distance(chromosome, coordinates):
    total_dist = 0
    for i in range(len(chromosome)):
        current_city = chromosome[i]
        next_city = chromosome[(i + 1) % len(chromosome)] # 回到起点
        total_dist += calculate_distance(coordinates[current_city], coordinates[next_city])
    return total_dist

# 适应度函数
def fitness_function(chromosome, coordinates):
    return 1.0 / calculate_total_distance(chromosome, coordinates)


# 锦标赛选择
def tournament_selection(population, fitnesses, k=3):
    selected_indices = np.random.choice(len(population), k, replace=False)
    best_index = -1
    max_fitness = -1
    for index in selected_indices:
        if fitnesses[index] > max_fitness:
            max_fitness = fitnesses[index]
            best_index = index
    return population[best_index]


# 顺序交叉 (Ordered Crossover - OX)
def ordered_crossover(parent1, parent2):
    size = len(parent1)
    child = [-1] * size

    start, end = sorted(random.sample(range(size), 2))

    child[start:end + 1] = parent1[start:end + 1]

    p2_genes = [gene for gene in parent2 if gene not in child]

    child_idx = 0
    for i in range(size):
        if child[i] == -1:
            child[i] = p2_genes[child_idx]
            child_idx += 1

    return child


# 反转变异 (Inversion Mutation)
def inversion_mutation(chromosome, mutation_rate):
    if random.random() < mutation_rate:
        start, end = sorted(random.sample(range(len(chromosome)), 2))
        segment = chromosome[start:end + 1]
        segment.reverse()
        chromosome[start:end + 1] = segment
    return chromosome


# GA 主函数
def genetic_algorithm_tsp(coordinates, pop_size=400, elite_size=20, mutation_rate=0.05, generations=4500):
    num_cities = len(coordinates)

    # 1. 初始化种群
    population = []
    for _ in range(pop_size):
        chromosome = list(np.random.permutation(num_cities))
        population.append(chromosome)

    best_distance_history = []
    avg_distance_history = []

    print("开始进化...")

    for gen in range(generations):
        # 2. 计算适应度
        fitnesses = [fitness_function(chromo, coordinates) for chromo in population]

        # 记录当前代的统计信息
        distances = [1.0 / f for f in fitnesses]
        best_distance = min(distances)
        avg_distance = np.mean(distances)
        best_distance_history.append(best_distance)
        avg_distance_history.append(avg_distance)

        if (gen + 1) % 50 == 0:
            print(f"第 {gen + 1} 代: 最短距离 = {best_distance:.2f}, 平均距离 = {avg_distance:.2f}")

        # 3. 生成新一代
        new_population = []

        # 精英保留
        elite_indices = np.argsort(fitnesses)[-elite_size:]
        for index in elite_indices:
            new_population.append(population[index])

        # 填充剩余种群
        for _ in range(pop_size - elite_size):
            # 选择
            parent1 = tournament_selection(population, fitnesses)
            parent2 = tournament_selection(population, fitnesses)
            # 交叉
            child = ordered_crossover(parent1, parent2)
            # 变异
            child = inversion_mutation(child, mutation_rate)
            new_population.append(child)

        population = new_population

    # 找到最终的最优解
    final_fitnesses = [fitness_function(chromo, coordinates) for chromo in population]
    best_index = np.argmax(final_fitnesses)
    best_chromosome = population[best_index]
    best_distance = calculate_total_distance(best_chromosome, coordinates)

    return best_chromosome, best_distance, best_distance_history, avg_distance_history


# 运行GA
best_route, best_dist, best_hist, avg_hist = genetic_algorithm_tsp(cities_coordinates)

print("\n进化结束.")
print(f"最优路径: {best_route}")
print(f"最短距离: {best_dist:.2f}")

# 绘制收敛曲线
plt.figure(figsize=(12, 6))
plt.plot(best_hist, label="当代引最优距离 (Best Distance)")
plt.plot(avg_hist, label="当代引平均距离 (Average Distance)")
plt.title("GA for TSP Convergence Curve")
plt.xlabel("Generation")
plt.ylabel("Distance")
plt.legend()
plt.grid(True)
plt.show()

# 绘制最优路径图
plt.figure(figsize=(8, 8))
# 按照最优路径重新排序坐标
ordered_coords = cities_coordinates[best_route]
# 添加回到起点的路径，形成闭环
ordered_coords = np.vstack([ordered_coords, ordered_coords[0]])

plt.plot(ordered_coords[:, 0], ordered_coords[:, 1], 'o-', label='Optimal Route')
for i, (x, y) in enumerate(cities_coordinates):
    plt.text(x, y, str(i), color="red", fontsize=12)
plt.title(f"Optimal TSP Route Found by GA (Distance: {best_dist:.2f})")
plt.xlabel("X Coordinate")
plt.ylabel("Y Coordinate")
plt.legend()
plt.grid(True)
plt.show()