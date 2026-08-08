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

# --- 取送货约束条件 ---
# 定义取送货对关系：必须先访问取货点P_i，才能访问对应的送货点D_i
# 格式：(取货点, 送货点)
PICKUP_DELIVERY_PAIRS = [
    (2, 8),   # 访问点8前必须先访问点2
    (4, 1),   # 访问点1前必须先访问点4
    (9, 5),    # 访问点5前必须先访问点9
    (15, 5),
    (13, 10),
    (12, 19),
    (13, 11)
]

# 违反约束的惩罚系数
CONSTRAINT_PENALTY = 1000.0
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

def check_constraints(chromosome):
    """检查路径是否满足取送货约束条件"""
    for pickup, delivery in PICKUP_DELIVERY_PAIRS:
        pickup_idx = chromosome.index(pickup)
        delivery_idx = chromosome.index(delivery)
        if pickup_idx > delivery_idx:  # 如果送货点在取货点之前，违反约束
            return False
    return True

def calculate_constraint_penalty(chromosome):
    """计算违反约束的惩罚值"""
    penalty = 0.0
    for pickup, delivery in PICKUP_DELIVERY_PAIRS:
        pickup_idx = chromosome.index(pickup)
        delivery_idx = chromosome.index(delivery)
        if pickup_idx > delivery_idx:  # 如果送货点在取货点之前，违反约束
            penalty += CONSTRAINT_PENALTY
    return penalty

def fitness_function(chromosome, coordinates):
    # 计算路径距离
    distance = calculate_total_distance(chromosome, coordinates)
    # 计算约束惩罚
    penalty = calculate_constraint_penalty(chromosome)
    # 总成本 = 距离 + 惩罚
    total_cost = distance + penalty
    return 1.0 / total_cost

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
    # 修复可能违反的约束条件
    child = repair_constraints(child)
    return child

def repair_constraints(chromosome):
    """修复违反取送货约束的解"""
    repaired = list(chromosome)
    for pickup, delivery in PICKUP_DELIVERY_PAIRS:
        pickup_idx = repaired.index(pickup)
        delivery_idx = repaired.index(delivery)
        
        # 如果送货点在取货点之前，交换它们的位置
        if pickup_idx > delivery_idx:
            repaired[pickup_idx], repaired[delivery_idx] = repaired[delivery_idx], repaired[pickup_idx]
    
    return repaired

def inversion_mutation(chromosome, mutation_rate):
    if random.random() < mutation_rate:
        # 尝试多次找到合法的变异
        for _ in range(5):  # 最多尝试5次
            # 复制一份染色体进行变异尝试
            temp_chromosome = list(chromosome)
            start, end = sorted(random.sample(range(len(temp_chromosome)), 2))
            segment = temp_chromosome[start:end+1]
            segment.reverse()
            temp_chromosome[start:end+1] = segment
            
            # 检查变异后是否仍然满足约束
            if check_constraints(temp_chromosome):
                return temp_chromosome
        
        # 如果多次尝试都无法得到合法解，则使用修复算子
        start, end = sorted(random.sample(range(len(chromosome)), 2))
        segment = chromosome[start:end+1]
        segment.reverse()
        chromosome[start:end+1] = segment
        return repair_constraints(chromosome)
    return chromosome

# 局部搜索算子 (2-opt)，考虑约束条件
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
                
                # 检查是否满足约束条件
                if not check_constraints(new_chromosome):
                    # 如果不满足约束，尝试修复
                    new_chromosome = repair_constraints(new_chromosome)
                
                # 计算新距离，考虑约束惩罚
                new_distance = calculate_total_distance(new_chromosome, coordinates)
                penalty = calculate_constraint_penalty(new_chromosome)
                new_total_cost = new_distance + penalty
                
                current_penalty = calculate_constraint_penalty(best_chromosome)
                current_total_cost = best_distance + current_penalty
                
                if new_total_cost < current_total_cost:
                    best_chromosome = new_chromosome
                    best_distance = new_distance
                    improved = True
                    break
            if improved:
                break
    return best_chromosome

# 生成满足约束条件的初始解
def generate_valid_solution(num_cities):
    while True:
        # 生成随机排列
        solution = list(np.random.permutation(num_cities))
        # 检查是否满足约束条件
        if check_constraints(solution):
            return solution
        # 如果不满足，尝试修复
        solution = repair_constraints(solution)
        if check_constraints(solution):
            return solution

# Memetic 算法主函数
def memetic_algorithm_tsp(coordinates, pop_size, elite_size, mutation_rate, generations):
    num_cities = len(coordinates)
    # 生成满足约束条件的初始种群
    population = [generate_valid_solution(num_cities) for _ in range(pop_size)]
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
    # 生成满足约束条件的初始种群
    population = [generate_valid_solution(num_cities) for _ in range(pop_size)]
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

# 验证最终解是否满足约束条件
ga_constraints_satisfied = check_constraints(ga_route)
ma_constraints_satisfied = check_constraints(ma_route)

print(f"GA解是否满足所有约束条件: {'是' if ga_constraints_satisfied else '否'}")
print(f"MA解是否满足所有约束条件: {'是' if ma_constraints_satisfied else '否'}")

# 打印约束满足情况详情
print("\n约束满足情况详情:")
for i, (pickup, delivery) in enumerate(PICKUP_DELIVERY_PAIRS):
    ga_pickup_idx = ga_route.index(pickup)
    ga_delivery_idx = ga_route.index(delivery)
    ma_pickup_idx = ma_route.index(pickup)
    ma_delivery_idx = ma_route.index(delivery)
    
    print(f"约束 {i+1}: 点{pickup}必须在点{delivery}之前")
    print(f"  GA: 点{pickup}在位置{ga_pickup_idx}, 点{delivery}在位置{ga_delivery_idx}, {'满足' if ga_pickup_idx < ga_delivery_idx else '不满足'}")
    print(f"  MA: 点{pickup}在位置{ma_pickup_idx}, 点{delivery}在位置{ma_delivery_idx}, {'满足' if ma_pickup_idx < ma_delivery_idx else '不满足'}")

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
plt.plot(ordered_coords_ga[:, 0], ordered_coords_ga[:, 1], 's--', color='orange', markersize=8, alpha=0.8, 
         label=f'GA 路径 (距离: {ga_dist:.2f}, 约束: {"满足" if ga_constraints_satisfied else "不满足"})')

# 绘制MA路径
plot_route_ma = ma_route + [ma_route[0]]
ordered_coords_ma = cities_coordinates[plot_route_ma]
plt.plot(ordered_coords_ma[:, 0], ordered_coords_ma[:, 1], 'o-', color='blue', markersize=8, 
         label=f'MA 路径 (距离: {ma_dist:.2f}, 约束: {"满足" if ma_constraints_satisfied else "不满足"})')

# 绘制城市点和编号
plt.scatter(cities_coordinates[:, 0], cities_coordinates[:, 1], color='red', s=50, zorder=5)
for i, (x, y) in enumerate(cities_coordinates):
    plt.text(x + 1, y + 1, str(i), color="black", fontsize=12)

# 高亮显示取送货对
for pickup, delivery in PICKUP_DELIVERY_PAIRS:
    # 取货点用绿色标记
    plt.scatter(cities_coordinates[pickup, 0], cities_coordinates[pickup, 1], 
                color='green', s=100, zorder=6, alpha=0.7, edgecolor='black')
    # 送货点用蓝色标记
    plt.scatter(cities_coordinates[delivery, 0], cities_coordinates[delivery, 1], 
                color='blue', s=100, zorder=6, alpha=0.7, edgecolor='black')
    # 添加连接线表示约束关系
    plt.plot([cities_coordinates[pickup, 0], cities_coordinates[delivery, 0]],
             [cities_coordinates[pickup, 1], cities_coordinates[delivery, 1]],
             'g--', alpha=0.5, linewidth=1.5)

plt.title(f"GA vs. MA 最优路径对比 ({NUM_CITIES} 城市)\n带取送货约束")
plt.xlabel("X 坐标")
plt.ylabel("Y 坐标")
plt.legend()
plt.grid(True)
plt.gca().set_aspect('equal', adjustable='box') # 保持X和Y轴比例相同
plt.show()