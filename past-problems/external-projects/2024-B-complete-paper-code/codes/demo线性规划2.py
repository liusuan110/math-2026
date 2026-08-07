from scipy.optimize import linprog

# 数据定义（从图片中的表格中提取的值，以下为示例数据）
purchase_cost_1 = 4    # 零配件1购买单价
purchase_cost_2 = 18   # 零配件2购买单价
test_cost_1 = 2        # 零配件1检测成本
test_cost_2 = 2        # 零配件2检测成本
assembly_cost = 6      # 装配成本
test_cost_product = 3  # 成品检测成本
market_price = 56      # 市场售价
replace_cost = 6       # 调换损失
disassemble_cost = 5   # 拆解费用

defect_rate_1 = 0.1    # 零配件1次品率
defect_rate_2 = 0.1    # 零配件2次品率
defect_rate_product = 0.1  # 成品次品率

# 决策变量: x1 = 零配件1检测，x2 = 零配件2检测，x3 = 成品检测，y1 = 拆解不合格品，y2 = 调换不合格品
# 定义目标函数 (最大化利润: 市场售价 - 各种成本)
# 公式解释: 利润 = 市场售价 - (零配件1购买成本 + 零配件2购买成本 + 检测成本 + 装配成本 + 调换损失 + 拆解费用)
# 如果进行检测，可以减少不合格品的浪费，所以检测与次品率相关。

# 目标函数系数，表示总成本（我们最小化总成本的负数相当于最大化利润）
c = [test_cost_1 * defect_rate_1,           # 零配件1检测成本与次品率
     test_cost_2 * defect_rate_2,           # 零配件2检测成本与次品率
     test_cost_product * defect_rate_product,  # 成品检测成本与次品率
     disassemble_cost * defect_rate_product,   # 拆解不合格品的费用
     replace_cost * defect_rate_product]       # 调换损失
'''

'''

# 定义约束矩阵：A_eq 和 b_eq 用来表达问题中的约束关系
# 约束 1: 总成本 <= 市场售价
# 约束 2: 每个决策变量只能为0或1

# 确保决策变量不超过1
A = [[1, 1, 1, 1, 1]]  # 限制每个变量的上界（可以扩展具体的约束逻辑）
b = [1]  # 这里表示每个决策操作只能是0或1，即做或不做。

# 变量的上下界 (0到1)，每个决策变量的取值为0或1
x_bounds = [(0, 1)] * 5

# 求解线性规划问题
res = linprog(c, A_ub=A, b_ub=b, bounds=x_bounds, method='highs')

# 打印优化结果
print(f"最优解的决策变量：{res.x}")
print(f"最大化的利润为：{-res.fun}")
