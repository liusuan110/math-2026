import pandas as pd
import numpy as np
from scipy.optimize import minimize
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- 0. 准备工作 ---
# 设置中文字体和绘图风格
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style('whitegrid')

# --- 1. 数据加载与预处理 ---
print("正在加载和预处理数据...")
# 读取数据
data = pd.read_csv('../../../sources/男胎(修正).csv')
# 将孕周转换为数值，无效值变为NaN
data['time'] = pd.to_numeric(data['孕周'])
data.dropna(subset=['Y染色体浓度', '孕妇BMI', 'time', '孕妇代码', '检测抽血次数'], inplace=True)

# 计算风险和准确性指标
data['risk'] = pd.cut(data['time'], bins=[0, 12, 28, 100], labels=[1, 2, 3], right=False).astype(int)
data['predict'] = data['染色体的非整倍体'].apply(lambda x: 0 if pd.isna(x) else 1)
data['health'] = data['胎儿是否健康'].apply(lambda x: 0 if x == '是' else 1)
data['correct'] = (data['predict'] == data['health']).astype(int)

# --- 2. 定义目标函数和优化模型 ---
# 预设固定的BMI分组边界
BMI_SPLITS = [20.70, 31.02, 33.89, 37.83, 46.88]


def objective_function(params, data):
    # params现在只包含8个时间窗口边界 [L1, U1, L2, U2, L3, U3, L4, U4]
    time_windows = params.reshape(4, 2)

    # 使用pd.cut高效地为每行数据分配BMI组别
    data['bmi_group'] = pd.cut(data['孕妇BMI'], bins=BMI_SPLITS, labels=False, right=False)

    total_samples = 0
    total_risk = 0
    total_accuracy = 0

    for i in range(4):
        time_min, time_max = time_windows[i]

        # 筛选出在当前BMI组且在对应时间窗口内的样本
        mask = (data['bmi_group'] == i) & (data['time'] >= time_min) & (data['time'] <= time_max)
        group_data = data[mask]

        if not group_data.empty:
            total_samples += len(group_data)
            total_risk += group_data['risk'].sum()
            total_accuracy += group_data['correct'].sum()

    if total_samples == 0:
        return 1e6  # 返回一个巨大的惩罚值

    # 计算总平均风险和总平均准确率
    avg_risk = total_risk / total_samples
    avg_accuracy = total_accuracy / total_samples

    return avg_risk - avg_accuracy


# --- 3. 运行优化 ---
print("开始运行优化器...")
# 决策变量只剩下4组时间窗口的8个边界
n_groups = 4

initial_params = np.array([10, 14, 12, 16, 14, 18, 16, 20])
# 变量的边界
bounds = [(10, 25)] * n_groups * 2
# 约束条件：L_k <= U_k
constraints = [{'type': 'ineq', 'fun': lambda p, i=i: p[i * 2 + 1] - p[i * 2]} for i in range(n_groups)]

result = minimize(
    fun=objective_function,
    x0=initial_params,
    args=(data,),
    method='SLSQP',
    bounds=bounds,
    constraints=constraints,
    options={'disp': True, 'maxiter': 200}
)

# --- 4. 结果整理与可视化 ---
if result.success:
    print("\n优化成功！")
    optimal_windows = result.x.reshape(n_groups, 2)

    result_table = pd.DataFrame({
        '分组': [f'分组 {i + 1}' for i in range(n_groups)],
        'BMI范围': [f'[{BMI_SPLITS[i]}, {BMI_SPLITS[i + 1]})' for i in range(n_groups)],
        '最佳NIPT时点下限': optimal_windows[:, 0],
        '最佳NIPT时点上限': optimal_windows[:, 1]
    })

    print("--- 最优分组方案 ---")
    print(result_table)

    # 可视化
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.scatterplot(data=data, x='孕妇BMI', y='time', color='lightgray', alpha=0.5, label='所有样本', ax=ax)
    sns.set_style('darkgrid')
    plt.rcParams['font.sans-serif'] = ['STZhongsong']
    colors = sns.color_palette("viridis", n_colors=n_groups)

    for i in range(n_groups):
        bmi_min, bmi_max = BMI_SPLITS[i], BMI_SPLITS[i + 1]
        time_min, time_max = optimal_windows[i]

        rect = patches.Rectangle((bmi_min, time_min), bmi_max - bmi_min, time_max - time_min,
                                 linewidth=1.5, edgecolor='black', facecolor=colors[i], alpha=0.3)
        ax.add_patch(rect)

    ax.set_title('最优BMI分组与NIPT检测时点窗口', fontsize=18)
    ax.set_xlabel('孕妇BMI', fontsize=14)
    ax.set_ylabel('检测孕周', fontsize=14)
    plt.tight_layout()
    plt.savefig("Q2_Optimization_Result.pdf")
    print("结果图已保存至 'Q2_Optimization_Result.pdf'")
    plt.show()

    plt.figure(figsize=(12, 8))
    colors = ['blue', 'green', 'orange', 'red']
    plt.scatter(data['孕妇BMI'], data['孕周'], c='lightgray', alpha=0.3, label='所有样本')
    bmi_splits = np.array([31.02, 33.89, 37.83])
    params=result.x
    time_lower = params[n_groups - 1:2 * n_groups - 1]
    time_upper = params[2 * n_groups - 1:3 * n_groups - 1]
    for i in range(n_groups):
        if i == 0:
            bmi_mask = data['孕妇BMI'] <= bmi_splits[i]
        elif i == n_groups - 1:
            bmi_mask = data['孕妇BMI'] > bmi_splits[i - 1]
        else:
            bmi_mask = (data['孕妇BMI'] > bmi_splits[i - 1]) & (data['孕妇BMI'] <= bmi_splits[i])

        # 时间窗口筛选
        time_mask = (data['孕周'] >= time_lower[i]) & (data['孕周'] <= time_upper[i])

        # 组合筛选条件
        group_mask = bmi_mask & time_mask

        # 获取该组的样本
        group_data = data[group_mask]

        # 绘制该组的数据点
        plt.scatter(group_data['孕妇BMI'], group_data['孕周'], c=colors[i], alpha=0.7, label=f'分组 {i}')

    # 绘制BMI分割线
    for split in bmi_splits:
        plt.axvline(x=split, color='black', linestyle='--', alpha=0.5)

        # 添加图例和标签
        plt.legend()
        plt.xlabel('孕妇BMI')
        plt.ylabel('孕周')
        plt.title('BMI分组和最佳NIPT时点')
        plt.grid(True, alpha=0.3)

        # 保存图形
        plt.savefig('BMI分组和最佳NIPT时点.png', dpi=300, bbox_inches='tight')
        # plt.show()  # 禁用图像显示

else:
    print("\n优化失败:", result.message)