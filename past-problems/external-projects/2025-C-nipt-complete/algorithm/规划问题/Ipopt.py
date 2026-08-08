import pyomo.environ as pyo

# 1. 创建一个具体的模型实例
model = pyo.ConcreteModel(name="Quadratic Maximization Problem")

# 2. 定义决策变量 x1 和 x2
# domain=pyo.NonNegativeReals 直接处理了 x >= 0 的约束
model.x1 = pyo.Var(domain=pyo.NonNegativeReals, initialize=0) # initialize 设置一个初始值
model.x2 = pyo.Var(domain=pyo.NonNegativeReals, initialize=0)

# 3. 定义目标函数
# 直接将您图片中的公式 (5.9) 写入
objective_expr = (
    -0.01 * model.x1**2
    - 0.007 * model.x1 * model.x2
    - 0.01 * model.x2**2
    + 144 * model.x1
    + 174 * model.x2
    - 400000
)

# sense=pyo.maximize 指明这是一个最大化问题
model.objective = pyo.Objective(expr=objective_expr, sense=pyo.maximize)

# 4. 创建求解器实例并求解
# 确保您已经安装了 ipopt
solver = pyo.SolverFactory('ipopt')
results = solver.solve(model, tee=True) # tee=True 会打印求解器的详细日志

# 5. 打印结果
print("\n" + "="*40)
print("             求解结果")
print("="*40)

# 检查求解器状态
if (results.solver.status == pyo.SolverStatus.ok) and (results.solver.termination_condition == pyo.TerminationCondition.optimal):
    print("求解成功，找到最优解！")
    print(f"最优解 x1 = {pyo.value(model.x1):.4f}")
    print(f"最优解 x2 = {pyo.value(model.x2):.4f}")
    print(f"目标函数最大值 y = {pyo.value(model.objective):,.4f}")
else:
    print("求解失败！")
    print(f"求解器状态: {results.solver.status}")
    print(f"终止条件: {results.solver.termination_condition}")

print("="*40)