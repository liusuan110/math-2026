import math

from cycler import cycler
from platypus import NSGAII, Problem, Real
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

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

# 定义多目标问题
def ZDT3_problem(vars):
    x1 = vars[0]
    x2 = vars[1]
    f1 = x1
    g = 1.0 + 9.0 * x2
    h = 1.0 - math.sqrt(f1 / g) - (f1 / g) * math.sin(10.0 * math.pi * f1)
    f2 = g * h

    cons = (x1 - 0.5)**2 + (x2 - 0.5)**2 - 0.25**2
    return [f1, f2], [cons]

problem = Problem(2, 2, 1) # 2个决策变量, 2个目标函数, 1个约束
problem.types[:] = [Real(0, 1), Real(0, 1)] # 决策变量范围
problem.function = ZDT3_problem
problem.constraints[:] = "<=0"
algorithm = NSGAII(problem, population_size=200)
algorithm.run(20000)

best_solution = algorithm.result
for solution in best_solution:
    print(solution.objectives)


# 提取帕累托前沿上所有解的目标函数值
objectives = [s.objectives for s in algorithm.result]
f1_values = [obj[0] for obj in objectives]
f2_values = [obj[1] for obj in objectives]

plt.figure(figsize=(10, 8))
plt.scatter(f1_values, f2_values, c='b', marker='o', label='Pareto Front Solutions')
plt.title('ZDT3 Problem with Constraints - Pareto Front')
plt.xlabel('$f_1(x)$')
plt.ylabel('$f_2(x)$')
plt.grid(True)
plt.legend()
plt.show()