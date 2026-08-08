import pygmo as pg

# 定义多目标优化问题
class MyProblem:
    def __init__(self):
        self.dim = 1

    def fitness(self, x):
        return [x[0]**2, (x[0]-2)**2]

    def get_bounds(self):
        return ([-5.0], [5.0])

problem = pg.problem(MyProblem())

# 运行多目标优化算法
algorithm = pg.algorithm(pg.nsga2(gen=10000))
population = pg.population(problem, 100)
population = algorithm.evolve(population)

# 输出最优解
best_solution = population.champion_f
print(best_solution)
