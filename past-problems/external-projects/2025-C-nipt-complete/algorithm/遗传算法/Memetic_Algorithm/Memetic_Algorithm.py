import numpy as np
import random
import matplotlib.pyplot as plt
import time
import matplotlib.font_manager as fm
from cycler import cycler

# --- 1. 参数调整 ---
NUM_CITIES = 20

POP_SIZE = 150       # 种群大小
GENERATIONS = 150    # 迭代代数
ELITE_SIZE = 15      # 精英个体数量 (10% of POP_SIZE)
MUTATION_RATE = 0.05 # 变异率
# --- 参数调整结束 ---


# -- 图片预设
font_path = '../../../utils/fonts/SourceHanSerifCN-Regular.otf'
fm.fontManager.addfont(font_path)
font_name = fm.FontProperties(fname=font_path).get_name()
plt.rcParams['font.sans-serif'] = [font_name]
print("成功加载思源宋体字体。")

plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.prop_cycle'] = cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
plt.rcParams['axes.unicode_minus'] = False
# -- 图片预设结束


# --- 2. 生成坐标 ---
np.random.seed(42) # 固定的随机种子
cities_coordinates = np.random.randint(0, 100, size=(NUM_CITIES, 2))


# 距离和适应度函数
def calculate_total_distance(chromosome, coordinates):
    total_dist = 0
    num_points = len(chromosome)
    for i in range(num_points):
        current_city = chromosome[i]
        next_city = chromosome[(i + 1) % num_points]
        total_dist += np.linalg.norm(coordinates[current_city] - coordinates[next_city])
    return total_dist

def fitness_function(chromosome, coordinates):
    return 1.0 / calculate_total_distance(chromosome, coordinates)

# GA算子
def tournament_selection(population, fitnesses, k=3):
    selected_indices = np.random.choice(len(population), k, replace=False)
    best_index = -1
    max_fitness = -1.0
    for index in selected_indices:
        if fitnesses[index] > max_fitness:
            max_fitness = fitnesses[index]
            best_index = index
    return population[best_index]

def ordered_crossover(parent1, parent2):
    size = len(parent1)
    child = [-1] * size
    start, end = sorted(random.sample(range(size), 2))
    child[start:end+1] = parent1[start:end+1]
    p2_genes = [gene for gene in parent2 if gene not in child]
    child_idx = 0
    for i in range(size):
        if child[i] == -1:
            child[i] = p2_genes[child_idx]
            child_idx += 1
    return child

def inversion_mutation(chromosome, mutation_rate):
    if random.random() < mutation_rate:
        start, end = sorted(random.sample(range(len(chromosome)), 2))
        segment = chromosome[start:end+1]
        segment.reverse()
        chromosome[start:end+1] = segment
    return chromosome

# 局部搜索算子 (2-opt)
def two_opt_local_search(chromosome, coordinates):
    best_chromosome = list(chromosome)
    improved = True
    while improved:
        improved = False
        best_distance = calculate_total_distance(best_chromosome, coordinates)
        for i in range(len(best_chromosome) - 1):
            for j in range(i + 1, len(best_chromosome)):
                new_chromosome = best_chromosome[:]
                segment = new_chromosome[i:j+1]
                segment.reverse()
                new_chromosome[i:j+1] = segment
                new_distance = calculate_total_distance(new_chromosome, coordinates)
                if new_distance < best_distance:
                    best_chromosome = new_chromosome
                    best_distance = new_distance
                    improved = True
                    break
            if improved:
                break
    return best_chromosome

# Memetic 算法主函数
def memetic_algorithm_tsp(coordinates, pop_size, elite_size, mutation_rate, generations):
    num_cities = len(coordinates)
    population = [list(np.random.permutation(num_cities)) for _ in range(pop_size)]
    best_distance_history = []
    print("开始进化 (MA)...")
    for gen in range(generations):
        fitnesses = [fitness_function(chromo, coordinates) for chromo in population]
        distances = [1.0 / f for f in fitnesses]
        best_distance = min(distances)
        best_distance_history.append(best_distance)

        if (gen + 1) % 50 == 0 or gen == 0:
            print(f"MA 第 {gen + 1}/{generations} 代: 最短距离 = {best_distance:.2f}")

        new_population = []
        elite_indices = np.argsort(fitnesses)[-elite_size:]
        for index in elite_indices:
            new_population.append(population[index])

        for _ in range(pop_size - elite_size):
            parent1 = tournament_selection(population, fitnesses)
            parent2 = tournament_selection(population, fitnesses)
            child = ordered_crossover(parent1, parent2)
            child = inversion_mutation(child, mutation_rate)
            # 核心区别：对每个新生成的子代进行局部优化
            child = two_opt_local_search(child, coordinates)
            new_population.append(child)
        population = new_population

    final_fitnesses = [fitness_function(chromo, coordinates) for chromo in population]
    best_index = np.argmax(final_fitnesses)
    best_chromosome = population[best_index]
    best_distance = calculate_total_distance(best_chromosome, coordinates)
    return best_chromosome, best_distance, best_distance_history

# 标准GA函数
def standard_genetic_algorithm_tsp(coordinates, pop_size, elite_size, mutation_rate, generations):
    num_cities = len(coordinates)
    population = [list(np.random.permutation(num_cities)) for _ in range(pop_size)]
    best_distance_history = []
    print("开始进化 (GA)...")
    for gen in range(generations):
        fitnesses = [fitness_function(chromo, coordinates) for chromo in population]
        distances = [1.0 / f for f in fitnesses]
        best_distance_history.append(min(distances))

        if (gen + 1) % 50 == 0 or gen == 0:
              print(f"GA 第 {gen + 1}/{generations} 代: 最短距离 = {min(distances):.2f}")

        new_population = []
        elite_indices = np.argsort(fitnesses)[-elite_size:]
        for index in elite_indices:
            new_population.append(population[index])
        for _ in range(pop_size - elite_size):
            parent1 = tournament_selection(population, fitnesses)
            parent2 = tournament_selection(population, fitnesses)
            child = ordered_crossover(parent1, parent2)
            child = inversion_mutation(child, mutation_rate)
            new_population.append(child)
        population = new_population

    final_fitnesses = [fitness_function(chromo, coordinates) for chromo in population]
    best_index = np.argmax(final_fitnesses)
    best_chromosome = population[best_index]
    best_distance = calculate_total_distance(best_chromosome, coordinates)
    return best_chromosome, best_distance, best_distance_history


# --- 运行与对比 ---
print(f"--- 运行标准遗传算法 (GA) for {NUM_CITIES} cities ---")
start_time_ga = time.time()
ga_route, ga_dist, ga_hist = standard_genetic_algorithm_tsp(
    cities_coordinates, POP_SIZE, ELITE_SIZE, MUTATION_RATE, GENERATIONS
)
end_time_ga = time.time()
print(f"GA 最终最短距离: {ga_dist:.2f}")
print(f"GA 运行时间: {end_time_ga - start_time_ga:.2f} 秒")

print(f"\n--- 运行Memetic算法 (MA) for {NUM_CITIES} cities ---")
start_time_ma = time.time()
ma_route, ma_dist, ma_hist = memetic_algorithm_tsp(
    cities_coordinates, POP_SIZE, ELITE_SIZE, MUTATION_RATE, GENERATIONS
)
end_time_ma = time.time()
print(f"MA 最終最短距離: {ma_dist:.2f}")
print(f"MA 运行时间: {end_time_ma - start_time_ma:.2f} 秒")


# --- 3. 结果可视化 ---

# 图1: 绘制对比收敛曲线
plt.figure(figsize=(12, 7))
plt.plot(ga_hist, label=f"标准遗传算法 (GA)", color='orange', alpha=0.8, linestyle='--')
plt.plot(ma_hist, label=f"Memetic算法 (MA)", color='blue', linewidth=2.5)
plt.title(f"GA vs. MA 收敛曲线对比 ({NUM_CITIES} 城市)")
plt.xlabel("迭代代数 (Generation)")
plt.ylabel("最短距离 (Distance)")
plt.legend()
plt.grid(True)
plt.show()

# 图2: 绘制MA和GA找到的最优路径对比图
plt.figure(figsize=(10, 10))
# 绘制GA路径
plot_route_ga = ga_route + [ga_route[0]]
ordered_coords_ga = cities_coordinates[plot_route_ga]
plt.plot(ordered_coords_ga[:, 0], ordered_coords_ga[:, 1], 's--', color='orange', markersize=8, alpha=0.8, label=f'GA 路径 (距离: {ga_dist:.2f})')

# 绘制MA路径
plot_route_ma = ma_route + [ma_route[0]]
ordered_coords_ma = cities_coordinates[plot_route_ma]
plt.plot(ordered_coords_ma[:, 0], ordered_coords_ma[:, 1], 'o-', color='blue', markersize=8, label=f'MA 路径 (距离: {ma_dist:.2f})')

# 绘制城市点和编号
plt.scatter(cities_coordinates[:, 0], cities_coordinates[:, 1], color='red', s=50, zorder=5)
for i, (x, y) in enumerate(cities_coordinates):
    plt.text(x + 1, y + 1, str(i), color="black", fontsize=12)

plt.title(f"GA vs. MA 最优路径对比 ({NUM_CITIES} 城市)")
plt.xlabel("X 坐标")
plt.ylabel("Y 坐标")
plt.legend()
plt.grid(True)
plt.gca().set_aspect('equal', adjustable='box') # 保持X和Y轴比例相同
plt.show()