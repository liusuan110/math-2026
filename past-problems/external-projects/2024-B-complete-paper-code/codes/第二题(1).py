from scipy.optimize import linprog

# 数据定义
purchase_cost_1 = 4    # 零配件1购买单价
purchase_cost_2 = 18   # 零配件2购买单价
assembly_cost = 6      # 装配成本
market_price = 56      # 市场售价



test_cost_1 = 8        # 零配件1检测成本
test_cost_2 = 1        # 零配件2检测成本
test_cost_product = 2  # 成品检测成本

replace_cost = 10       # 调换损失
disassemble_cost = 5   # 拆解费用

defect_rate_1 = 0.1    # 零配件1次品率
defect_rate_2 = 0.2    # 零配件2次品率
defect_rate_product = 0.1  # 成品次品率


# 买到第一件好零件的期望
expectation1 = 1 + defect_rate_1/2
expectation2 = 1 + defect_rate_2/2
# 购买到第一件正品的期望
expectation3 = 1 + defect_rate_product/2

# 初期成本 = 购买成本 + 装配 + 拆解成本
former_cost_1 = purchase_cost_1 + purchase_cost_2 + assembly_cost + + replace_cost

# 目标函数：检测与否对于成本影响的期望
# 由于线性规划求解的是最小化问题，因此我们直接使用各项决策进行与否对成本期望的影响，作为目标函数
# x1, x2 表示是否检测零配件1和2，x3表示是否检测成品
c = [
    expectation1 * (purchase_cost_1 + test_cost_1) - defect_rate_1 * (1-defect_rate_product) * (former_cost_1 + replace_cost),   # 零配件1 对成本总成本影响的期望
    expectation2 * (purchase_cost_2 + test_cost_2) - defect_rate_2 * (1-defect_rate_product) * (former_cost_1 + replace_cost),   # 零配件2 对总成本影响的期望
    expectation3 * (test_cost_product + former_cost_1) - former_cost_1 - defect_rate_product * (former_cost_1 + replace_cost)     # 成品检测对总成本影响的期望
]

# 定义约束矩阵和约束条件
A = [[1, 1, 1]]  # 表示每个检测和操作是独立进行的
b = [3]  # 允许五项操作独立进行

# 变量的上下界 (0到1)，每个决策变量的取值为0或1
x_bounds = [(0, 1)] * 3

# 求解线性规划问题
res = linprog(c, A_ub=A, b_ub=b, bounds=x_bounds, method='highs')

# 打印优化结果
print(f"最优解的决策变量：{res.x}")

# 后续的讨论：计算总成本以及确定是否拆解
y = res.x



# 处理成本计算，防止出现0
def bio2(x):
    if x==1:
        return 0
    else:
        return x


# 最后根据拆解与否带来的成本期望变化决定是否拆解
if y[2] == 0:  # 表示不对成品检测，次品可能流入消费者手中
    print("次品会进入消费者手中")
    potential_cost = (1 - defect_rate_product)*(1 - pow(1 - defect_rate_1, y[0]) * pow(1 - defect_rate_2, y[1])) * former_cost_1
    if potential_cost < disassemble_cost:
        print("不拆解")
        print("预期成本", former_cost_1++purchase_cost_1*y[0] + purchase_cost_2 * y[1] - replace_cost + defect_rate_product*replace_cost)
    else:
        print("拆解")
        print("预期成本",former_cost_1 + +purchase_cost_1 * y[0] + purchase_cost_2 * y[1] - replace_cost + defect_rate_product * (replace_cost+disassemble_cost))

else:
    print("次品不会进入消费者手中,决定是否拆解")
    if former_cost_1 - replace_cost > disassemble_cost:
        print("拆解")
    else:
        print("不拆解，丢掉")
        pass
    pass
