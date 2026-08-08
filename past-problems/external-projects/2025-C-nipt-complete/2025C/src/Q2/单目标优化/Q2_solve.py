import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 读取数据
data=pd.read_csv('../../../sources/男胎(Q2)(添加判断结果).csv')
n_groups=4

# 数据预处理
def preprocess_data(data):
    # 确保Y染色体浓度列为数值型
    def calculate_risk(row):
        if row['孕周'] <= 12:
            return 1
        elif row['孕周'] < 28:
            # 12-28周之间线性变化，从1增长到3
            return 1 + (row['孕周'] - 12) * (3 - 1) / (28 - 12)
        else:
            return 3
    data['风险'] = data.apply(calculate_risk, axis=1)

    # 添加预测结果列（根据染色体非整倍体判断）
    data['预测结果'] = data['染色体的非整倍体'].apply(lambda x: 0 if pd.isna(x) else 1)
    # 添加实际结果列（根据胎儿是否健康判断）
    data['实际结果'] = data['胎儿是否健康'].apply(lambda x: 0 if x == '是' else 1)
    # 添加准确性列
    data['准确性'] = (data['预测结果'] == data['实际结果']).astype(int)

    return data

processed_data = preprocess_data(data)

def objective_function(params, data):
    n_groups = 4

    time_lower = params[n_groups-1 : 2*n_groups-1]  # 时间下限
    time_upper = params[2*n_groups-1 : 3*n_groups-1]  # 时间上限

    # 初始化各组的统计数据
    group_risks = []
    group_accuracies = []
    group_samples = []
    group_window_widths = []

    # 为每个BMI分组计算风险和准确性
    for i in range(n_groups):
        if i == 0:
            bmi_mask = data['孕妇BMI'] <= 31.02
        elif i == 1:
            bmi_mask = (data['孕妇BMI'] > 31.02) & (data['孕妇BMI'] <= 33.89)
        elif i == 2:
            bmi_mask = (data['孕妇BMI'] > 33.89) & (data['孕妇BMI'] <= 37.83)
        else:
            bmi_mask = data['孕妇BMI'] >= 38.22

        # 时间窗口筛选
        time_mask = (data['孕周'] >= time_lower[i]) & (data['孕周'] <= time_upper[i])
        group_data = data[bmi_mask & time_mask]

        # 记录时间窗口宽度
        window_width = time_upper[i] - time_lower[i]
        group_window_widths.append(window_width)

        if len(group_data) > 0:
            group_risk = group_data['风险'].mean()
            group_accuracy = group_data['准确性'].mean()
            
            # 添加准确性惩罚：对"不准确"的样本进行惩罚
            accuracy_penalty = 0
            if '是否准确' in group_data.columns:
                inaccurate_count = (group_data['是否准确'] == '不准确').sum()
                accuracy_penalty = inaccurate_count / len(group_data) * 8.0  # 增加惩罚权重为8.0
            
            # 添加Y染色体浓度惩罚：对小于0.04的样本进行惩罚
            concentration_penalty = 0
            if 'Y染色体浓度' in group_data.columns:
                low_concentration_count = (group_data['Y染色体浓度'] < 0.04).sum()
                concentration_penalty = low_concentration_count / len(group_data) * 6.0  # 增加惩罚权重为6.0
            
            # 计算准确样本的奖励（降低风险）
            accuracy_reward = 0
            if '是否准确' in group_data.columns:
                accurate_count = (group_data['是否准确'] == '准确').sum()
                accuracy_reward = accurate_count / len(group_data) * 0.5  # 奖励权重为0.5
            
            # 计算高浓度样本的奖励（降低风险）
            concentration_reward = 0
            if 'Y染色体浓度' in group_data.columns:
                high_concentration_count = (group_data['Y染色体浓度'] >= 0.04).sum()
                concentration_reward = high_concentration_count / len(group_data) * 0.3  # 奖励权重为0.3
            
            # 将惩罚和奖励加入到风险中
            adjusted_risk = group_risk + accuracy_penalty + concentration_penalty - accuracy_reward - concentration_reward
            
            # 记录详细的惩罚和奖励信息（用于调试）
            if hasattr(objective_function, 'debug_mode') and objective_function.debug_mode:
                print(f"分组 {i}: 原始风险={group_risk:.4f}, 准确性惩罚={accuracy_penalty:.4f}, 浓度惩罚={concentration_penalty:.4f}")
                print(f"        准确性奖励={accuracy_reward:.4f}, 浓度奖励={concentration_reward:.4f}, 调整后风险={adjusted_risk:.4f}")
            
            group_risks.append(adjusted_risk)
            group_accuracies.append(group_accuracy)
            group_samples.append(len(group_data))
        else:
            # 如果某组没有样本，给予高惩罚
            group_risks.append(5.0)  # 高风险惩罚
            group_accuracies.append(0.0)  # 低准确率惩罚
            group_samples.append(0)

    # 如果任何一组没有样本，返回一个很大的惩罚值
    if 0 in group_samples:
        return 1000

    # 计算总体指标
    total_samples = sum(group_samples)
    weighted_risk = sum(r * s for r, s in zip(group_risks, group_samples)) / total_samples
    weighted_accuracy = sum(a * s for a, s in zip(group_accuracies, group_samples)) / total_samples
    
    # 计算样本分布均衡性指标（标准差/平均值）
    sample_mean = np.mean(group_samples)
    sample_std = np.std(group_samples)
    sample_cv = sample_std / sample_mean if sample_mean > 0 else 1000
    
    # 计算窗口宽度的均衡性
    width_mean = np.mean(group_window_widths)
    width_std = np.std(group_window_widths)
    width_cv = width_std / width_mean if width_mean > 0 else 1000
    
    # 目标函数：最小化风险，最大化准确性，同时考虑样本分布均衡性和窗口宽度均衡性
    # 权重可以根据需要调整
    risk_weight = 1.0
    accuracy_weight = 1.0
    balance_weight = 0.5
    width_weight = 0.3
    
    objective = (risk_weight * weighted_risk) - (accuracy_weight * weighted_accuracy) + \
               (balance_weight * sample_cv) + (width_weight * width_cv)
    
    return objective

# 定义约束条件
def constraint_time_window(params):
    n_groups = 4
    time_lower = params[n_groups-1:2*n_groups-1]
    time_upper = params[2*n_groups-1:3*n_groups-1]

    # 确保每个组的时间窗口有效（下限 <= 上限）且窗口宽度合理
    window_widths = time_upper - time_lower
    return np.min(window_widths)

# 定义窗口最小宽度约束
def constraint_min_window_width(params):
    n_groups = 4
    time_lower = params[n_groups-1:2*n_groups-1]
    time_upper = params[2*n_groups-1:3*n_groups-1]
    
    # 确保每个窗口至少有2周宽度
    min_width = 2.0
    window_widths = time_upper - time_lower
    return np.min(window_widths) - min_width

# 定义窗口最大宽度约束
def constraint_max_window_width(params):
    n_groups = 4
    time_lower = params[n_groups-1:2*n_groups-1]
    time_upper = params[2*n_groups-1:3*n_groups-1]
    
    # 确保每个窗口最多有3周宽度
    max_width = 3.0
    window_widths = time_upper - time_lower
    return max_width - np.max(window_widths)

# 定义BMI分组间时间窗口的递增约束
def constraint_increasing_windows(params):
    n_groups = 4
    time_lower = params[n_groups-1:2*n_groups-1]
    
    # 确保随着BMI增加，时间窗口下限也递增
    # 返回所有相邻下限差值的最小值，应该大于等于0
    return np.min(np.diff(time_lower))

# 优化模型
def optimize_model(data):
    n_groups = 4
    initial_bmi_splits = np.array([31.02, 33.89, 37.83])

    # 尝试多组不同的初始值，选择最优结果
    best_result = None
    best_objective = float('inf')
    
    # 定义多组初始值（使用更精细的时间粒度，确保窗口宽度在1-3周之间）
    initial_values = [
        # 初始值1：2.1周宽度窗口（精细调整）
        {
            'time_lower': np.array([9.1, 11.2, 13.3, 15.1]),
            'time_upper': np.array([11.2, 13.3, 15.4, 17.2])
        },
        # 初始值2：2.8周宽度窗口（精细调整）
        {
            'time_lower': np.array([8.3, 10.1, 12.2, 14.1]),
            'time_upper': np.array([11.1, 12.9, 15.0, 16.9])
        },
        # 初始值3：1.3周宽度窗口（精细调整）
        {
            'time_lower': np.array([10.2, 12.1, 14.3, 16.1]),
            'time_upper': np.array([11.5, 13.4, 15.6, 17.4])
        },
        # 初始值4：2.4周宽度窗口（精细调整）
        {
            'time_lower': np.array([9.6, 11.7, 13.8, 15.4]),
            'time_upper': np.array([12.0, 14.1, 16.2, 17.8])
        },
        # 初始值5：1.7周宽度窗口（精细调整）
        {
            'time_lower': np.array([9.3, 11.4, 13.1, 15.2]),
            'time_upper': np.array([11.0, 13.1, 14.8, 16.9])
        },
        # 初始值6：2.6周宽度窗口（精细调整）
        {
            'time_lower': np.array([8.7, 10.8, 12.9, 14.6]),
            'time_upper': np.array([11.3, 13.4, 15.5, 17.2])
        },
        # 初始值7：1.1周宽度窗口（精细调整）
        {
            'time_lower': np.array([10.4, 12.3, 14.5, 16.2]),
            'time_upper': np.array([11.5, 13.4, 15.6, 17.3])
        }
    ]
    
    # 为不同BMI分组设置不同的时间边界（使用更精细的时间粒度）
    # 低BMI组（分组0）：较早的时间窗口范围
    # 高BMI组（分组3）：较晚的时间窗口范围
    time_lower_bounds = [
        (8.0, 12.5),   # 分组0：BMI较低，时间窗口下限较早，支持小数精度
        (9.5, 14.5),   # 分组1：BMI中低，时间窗口下限适中偏早，支持小数精度
        (11.5, 16.5),  # 分组2：BMI中高，时间窗口下限适中偏晚，支持小数精度
        (13.5, 20.5)   # 分组3：BMI较高，时间窗口下限较晚，支持小数精度
    ]
    
    time_upper_bounds = [
        (11.5, 16.5),  # 分组0：BMI较低，时间窗口上限较早，支持小数精度
        (13.5, 18.5),  # 分组1：BMI中低，时间窗口上限适中偏早，支持小数精度
        (15.5, 20.5),  # 分组2：BMI中高，时间窗口上限适中偏晚，支持小数精度
        (17.5, 24.5)   # 分组3：BMI较高，时间窗口上限较晚，支持小数精度
    ]
    
    bmi_bounds = [(20, 50)] * (n_groups - 1)  # BMI分割点的边界
    bounds = bmi_bounds + time_lower_bounds + time_upper_bounds
    
    # 约束条件
    constraints = [
        {'type': 'ineq', 'fun': constraint_time_window},       # 时间窗口有效性约束
        {'type': 'ineq', 'fun': constraint_min_window_width},   # 窗口最小宽度约束
        {'type': 'ineq', 'fun': constraint_max_window_width},   # 窗口最大宽度约束
        {'type': 'ineq', 'fun': constraint_increasing_windows}  # BMI分组间时间窗口递增约束
    ]
    
    # 尝试多组初始值
    for i, init_vals in enumerate(initial_values):
        print(f"\n尝试初始值组合 {i+1}/{len(initial_values)}...")
        
        initial_time_lower = init_vals['time_lower']
        initial_time_upper = init_vals['time_upper']
        
        initial_params = np.concatenate([initial_bmi_splits, initial_time_lower, initial_time_upper])
        
        # 优化（使用更小的时间粒度，提高精度）
        result = minimize(
            objective_function,
            initial_params,
            args=(data,),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 5000, 'ftol': 1e-12, 'disp': True}
        )
        
        # 评估优化结果
        current_objective = result.fun
        print(f"初始值组合 {i+1} 的目标函数值: {current_objective}")
        
        # 如果当前结果更好，则更新最佳结果
        if current_objective < best_objective:
            best_objective = current_objective
            best_result = result
            print(f"找到更好的解，目标函数值: {best_objective}")
    
    # 使用最佳结果
    print(f"\n最终选择的最佳解，目标函数值: {best_objective}")
    return best_result

# 运行优化
optimization_result = optimize_model(processed_data)

# 解析优化结果
def parse_optimization_result(result, n_groups=4):
    params = result.x
    # 使用指定的BMI分割点
    bmi_splits = np.array([31.02, 33.89, 37.83])
    time_lower = params[n_groups-1:2*n_groups-1]
    time_upper = params[2*n_groups-1:3*n_groups-1]

    # 使用指定的BMI分组范围
    bmi_ranges = [
        '[20.70, 31.02]',
        '[31.03, 33.89]',
        '[33.91, 37.83]',
        '[38.22, 46.88]'
    ]

    # 创建结果表格（保持数值类型用于后续计算）
    result_table = pd.DataFrame({
        '分组': [f'分组 {i}' for i in range(n_groups)],
        'BMI范围': bmi_ranges,
        '最佳NIPT时点下限': time_lower,
        '最佳NIPT时点上限': time_upper
    })
    
    # 创建显示用的表格（格式化为2位小数）
    display_table = result_table.copy()
    display_table['最佳NIPT时点下限'] = [f'{val:.2f}' for val in time_lower]
    display_table['最佳NIPT时点上限'] = [f'{val:.2f}' for val in time_upper]

    return result_table, display_table, bmi_splits, time_lower, time_upper

# 解析优化结果
result_table, display_table, bmi_splits, time_lower, time_upper = parse_optimization_result(optimization_result)

# 打印结果表格
print("优化结果：")
print(display_table)

# 可视化结果
plt.figure(figsize=(12, 8))
colors = ['blue', 'green', 'orange', 'red']
plt.scatter(data['孕妇BMI'], data['孕周'], c='lightgray', alpha=0.3, label='所有样本')

for i in range(n_groups):
    if i == 0:
        bmi_mask = data['孕妇BMI'] <= bmi_splits[i]
    elif i == n_groups - 1:
        bmi_mask = data['孕妇BMI'] > bmi_splits[i-1]
    else:
        bmi_mask = (data['孕妇BMI'] > bmi_splits[i-1]) & (data['孕妇BMI'] <= bmi_splits[i])

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


# 分析检测误差的影响
def analyze_error_impact(data, bmi_splits, time_lower, time_upper, n_groups=4):
    # 第一次筛选：根据优化模型得到的分组和时间窗口
    selected_samples = []

    for i in range(n_groups):
        if i == 0:
            bmi_mask = data['孕妇BMI'] <= 31.02
        elif i == 1:
            bmi_mask = (data['孕妇BMI'] > 31.02) & (data['孕妇BMI'] <= 33.89)
        elif i == 2:
            bmi_mask = (data['孕妇BMI'] > 33.89) & (data['孕妇BMI'] <= 37.83)
        else:  # i == 3
            bmi_mask = data['孕妇BMI'] >= 38.22

        # 时间窗口筛选
        time_mask = (data['孕周'] >= time_lower[i]) & (data['孕周'] <= time_upper[i])

        # 获取该组的样本
        group_data = data[bmi_mask & time_mask]
        selected_samples.append(group_data)

    # 合并所有选中的样本
    selected_data = pd.concat(selected_samples)

    # 第二次筛选：模拟检测误差，只保留Y染色体浓度达到或超过4%的样本
    reliable_data = selected_data[selected_data['Y染色体浓度'] >= 0.04]

    # 计算筛选前后的样本数量和比例
    total_samples = len(data)
    selected_count = len(selected_data)
    reliable_count = len(reliable_data)

    # 计算各组的准确率
    group_accuracy = []
    for i in range(n_groups):
        if i == 0:
            bmi_mask = reliable_data['孕妇BMI'] <= 31.02
        elif i == 1:
            bmi_mask = (reliable_data['孕妇BMI'] > 31.02) & (reliable_data['孕妇BMI'] <= 33.89)
        elif i == 2:
            bmi_mask = (reliable_data['孕妇BMI'] > 33.89) & (reliable_data['孕妇BMI'] <= 37.83)
        else:  # i == 3
            bmi_mask = reliable_data['孕妇BMI'] >= 38.22

        group_data = reliable_data[bmi_mask]
        if len(group_data) > 0:
            accuracy = group_data['准确性'].mean()
        else:
            accuracy = 0
        group_accuracy.append(accuracy)

    # 创建结果表格
    error_analysis = pd.DataFrame({
        '分组': [f'分组 {i}' for i in range(n_groups)],
        'BMI范围': result_table['BMI范围'],
        '样本数量': [len(selected_samples[i]) for i in range(n_groups)],
        '达标样本数量': [
            len(reliable_data[reliable_data['孕妇BMI'] <= 31.02]) if i == 0 else
            len(reliable_data[(reliable_data['孕妇BMI'] > 31.02) & (reliable_data['孕妇BMI'] <= 33.89)]) if i == 1 else
            len(reliable_data[(reliable_data['孕妇BMI'] > 33.89) & (reliable_data['孕妇BMI'] <= 37.83)]) if i == 2 else
            len(reliable_data[reliable_data['孕妇BMI'] >= 38.22])
            for i in range(n_groups)
        ],
        '达标比例': [
            len(reliable_data[reliable_data['孕妇BMI'] <= 31.02]) / len(selected_samples[0]) if i == 0 and len(selected_samples[0]) > 0 else
            len(reliable_data[(reliable_data['孕妇BMI'] > 31.02) & (reliable_data['孕妇BMI'] <= 33.89)]) / len(selected_samples[1]) if i == 1 and len(selected_samples[1]) > 0 else
            len(reliable_data[(reliable_data['孕妇BMI'] > 33.89) & (reliable_data['孕妇BMI'] <= 37.83)]) / len(selected_samples[2]) if i == 2 and len(selected_samples[2]) > 0 else
            len(reliable_data[reliable_data['孕妇BMI'] >= 38.22]) / len(selected_samples[3]) if i == 3 and len(selected_samples[3]) > 0 else 0
            for i in range(n_groups)
        ],
        '准确率': group_accuracy
    })

    # 添加总计行
    error_analysis.loc[len(error_analysis)] = ['总计', '', sum(error_analysis['样本数量']),
                                           sum(error_analysis['达标样本数量']),
                                           sum(error_analysis['达标样本数量']) / sum(error_analysis['样本数量']) if sum(error_analysis['样本数量']) > 0 else 0,
                                           reliable_data['准确性'].mean() if len(reliable_data) > 0 else 0]

    return error_analysis, selected_data, reliable_data

error_analysis, selected_data, reliable_data = analyze_error_impact(processed_data, bmi_splits, time_lower, time_upper)

print("\n检测误差分析：")
print(error_analysis)

# 添加惩罚和奖励效果分析
def analyze_penalty_reward_effects(data, bmi_splits, time_lower, time_upper, n_groups=4):
    penalty_reward_analysis = []
    
    for i in range(n_groups):
        if i == 0:
            bmi_mask = data['孕妇BMI'] <= bmi_splits[i]
        elif i == n_groups - 1:
            bmi_mask = data['孕妇BMI'] > bmi_splits[i-1]
        else:
            bmi_mask = (data['孕妇BMI'] > bmi_splits[i-1]) & (data['孕妇BMI'] <= bmi_splits[i])
        
        time_mask = (data['孕周'] >= time_lower[i]) & (data['孕周'] <= time_upper[i])
        group_data = data[bmi_mask & time_mask]
        
        if len(group_data) > 0:
            # 计算准确性统计
            accurate_count = (group_data['是否准确'] == '准确').sum()
            inaccurate_count = (group_data['是否准确'] == '不准确').sum()
            accuracy_rate = accurate_count / len(group_data)
            
            # 计算Y染色体浓度统计
            high_concentration_count = (group_data['Y染色体浓度'] >= 0.04).sum()
            low_concentration_count = (group_data['Y染色体浓度'] < 0.04).sum()
            high_concentration_rate = high_concentration_count / len(group_data)
            
            # 计算惩罚和奖励值
            accuracy_penalty = inaccurate_count / len(group_data) * 8.0
            concentration_penalty = low_concentration_count / len(group_data) * 6.0
            accuracy_reward = accurate_count / len(group_data) * 0.5
            concentration_reward = high_concentration_count / len(group_data) * 0.3
            
            penalty_reward_analysis.append({
                '分组': f'分组 {i}',
                'BMI范围': f'[{bmi_splits[i-1] if i > 0 else data["孕妇BMI"].min():.2f}, {bmi_splits[i] if i < n_groups-1 else data["孕妇BMI"].max():.2f}]',
                '样本数量': len(group_data),
                '准确样本数': accurate_count,
                '不准确样本数': inaccurate_count,
                '准确率': f'{accuracy_rate:.3f}',
                '高浓度样本数': high_concentration_count,
                '低浓度样本数': low_concentration_count,
                '高浓度比例': f'{high_concentration_rate:.3f}',
                '准确性惩罚': f'{accuracy_penalty:.4f}',
                '浓度惩罚': f'{concentration_penalty:.4f}',
                '准确性奖励': f'{accuracy_reward:.4f}',
                '浓度奖励': f'{concentration_reward:.4f}',
                '净惩罚': f'{accuracy_penalty + concentration_penalty - accuracy_reward - concentration_reward:.4f}'
            })
    
    return pd.DataFrame(penalty_reward_analysis)

penalty_reward_df = analyze_penalty_reward_effects(processed_data, bmi_splits, time_lower, time_upper)
print("\n惩罚和奖励效果分析：")
print(penalty_reward_df)

def visualize_error_impact(data, selected_data, reliable_data, bmi_splits):

    plt.figure(figsize=(12, 8))
    plt.scatter(data['孕妇BMI'], data['Y染色体浓度'], c='lightgray', alpha=0.3, label='所有样本')
    plt.scatter(selected_data['孕妇BMI'], selected_data['Y染色体浓度'], c='blue', alpha=0.5, label='选中样本')
    plt.scatter(reliable_data['孕妇BMI'], reliable_data['Y染色体浓度'], c='red', alpha=0.7, label='达标样本')

    for split in bmi_splits:
        plt.axvline(x=split, color='black', linestyle='--', alpha=0.5)

    plt.axhline(y=0.04, color='green', linestyle='--', alpha=0.7, label='Y染色体浓度达标线(4%)')

    plt.legend()
    plt.xlabel('孕妇BMI')
    plt.ylabel('Y染色体浓度')
    plt.title('检测误差影响分析')
    plt.grid(True, alpha=0.3)

    plt.savefig('检测误差影响分析.png', dpi=300, bbox_inches='tight')
    plt.show()

visualize_error_impact(processed_data, selected_data, reliable_data, bmi_splits)

# 分析BMI与Y染色体浓度达标时间的关系
def analyze_bmi_vs_time(data):
    # 按孕妇代码分组
    grouped_data = data.groupby('孕妇代码')

    # 存储每个孕妇的BMI和Y染色体浓度首次达标时间
    bmi_time_data = []

    for name, group in grouped_data:
        # 按孕周排序
        group = group.sort_values('孕周')

        # 找到Y染色体浓度首次达到或超过4%的记录
        reached_threshold = group[group['Y染色体浓度'] >= 0.04]

        if len(reached_threshold) > 0:
            # 获取首次达标的记录
            first_record = reached_threshold.iloc[0]

            # 存储BMI和达标时间
            bmi_time_data.append({
                '孕妇代码': name,
                '孕妇BMI': first_record['孕妇BMI'],
                '达标时间': first_record['孕周']
            })

    # 创建DataFrame
    bmi_time_df = pd.DataFrame(bmi_time_data)

    # 创建一个新的图形
    plt.figure(figsize=(12, 8))

    # 绘制散点图
    plt.scatter(bmi_time_df['孕妇BMI'], bmi_time_df['达标时间'], alpha=0.7)

    # 添加趋势线
    z = np.polyfit(bmi_time_df['孕妇BMI'], bmi_time_df['达标时间'], 1)
    p = np.poly1d(z)
    plt.plot(bmi_time_df['孕妇BMI'], p(bmi_time_df['孕妇BMI']), "r--", alpha=0.7)

    # 添加标签和标题
    plt.xlabel('孕妇BMI')
    plt.ylabel('Y染色体浓度首次达标时间（孕周）')
    plt.title('BMI与Y染色体浓度达标时间的关系')
    plt.grid(True, alpha=0.3)

    # 保存图形
    plt.savefig('BMI与Y染色体浓度达标时间的关系.png', dpi=300, bbox_inches='tight')
    # plt.show()  # 禁用图像显示

    return bmi_time_df

# 分析BMI与Y染色体浓度达标时间的关系
bmi_time_df = analyze_bmi_vs_time(processed_data)

# 创建矩形图表示BMI分组和最佳NIPT时点
def visualize_results_rectangle(result_table):
    # 创建一个新的图形
    plt.figure(figsize=(12, 8))

    # 设置与散点图一致的颜色（从左到右：蓝、绿、黄、红）
    colors = ['blue', 'green', 'orange', 'red']

    # 绘制矩形
    for i, row in result_table.iterrows():
        # 解析BMI范围
        bmi_range = row['BMI范围'].strip('[]').split(', ')
        bmi_min = float(bmi_range[0])
        bmi_max = float(bmi_range[1])

        # 获取时间窗口
        time_min = row['最佳NIPT时点下限']
        time_max = row['最佳NIPT时点上限']

        # 绘制矩形
        rect = plt.Rectangle((bmi_min, time_min), bmi_max - bmi_min, time_max - time_min,
                           facecolor=colors[i], alpha=0.7, edgecolor='black', linewidth=1)
        plt.gca().add_patch(rect)

        # 在矩形中添加标签
        plt.text(bmi_min + (bmi_max - bmi_min)/2, time_min + (time_max - time_min)/2,
                f'{i+1}', ha='center', va='center', fontsize=12, fontweight='bold')

    # 设置坐标轴范围
    plt.xlim(20, 47)
    plt.ylim(8, 22)

    # 添加标签和标题
    plt.xlabel('孕妇BMI')
    plt.ylabel('孕周')
    plt.title('BMI分组和最佳NIPT时点矩形图')
    plt.grid(True, alpha=0.3)

    # 添加图例
    legend_elements = [plt.Rectangle((0, 0), 1, 1, facecolor=colors[i], alpha=0.7, edgecolor='black', linewidth=1,
                                   label=f'分组 {i}: {result_table.iloc[i]["BMI范围"]}')
                      for i in range(len(result_table))]
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))

    # 保存图形
    plt.savefig('BMI分组和最佳NIPT时点矩形图.png', dpi=300, bbox_inches='tight')
    # plt.show()  # 禁用图像显示

# 创建矩形图
visualize_results_rectangle(result_table)

# 保存结果到CSV文件
result_table.to_csv('BMI分组和最佳NIPT时点.csv', index=False)
error_analysis.to_csv('检测误差分析.csv', index=False)
bmi_time_df.to_csv('BMI与Y染色体浓度达标时间.csv', index=False)
penalty_reward_df.to_csv('惩罚和奖励效果分析.csv', index=False)

# 创建惩罚和奖励效果的可视化
def visualize_penalty_reward_effects(penalty_reward_df):
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    groups = penalty_reward_df['分组']
    
    # 1. 准确率和高浓度比例对比
    accuracy_rates = [float(x) for x in penalty_reward_df['准确率']]
    concentration_rates = [float(x) for x in penalty_reward_df['高浓度比例']]
    
    x = np.arange(len(groups))
    width = 0.35
    
    ax1.bar(x - width/2, accuracy_rates, width, label='准确率', color='skyblue', alpha=0.8)
    ax1.bar(x + width/2, concentration_rates, width, label='高浓度比例', color='lightcoral', alpha=0.8)
    ax1.set_xlabel('BMI分组')
    ax1.set_ylabel('比例')
    ax1.set_title('各分组准确率与高浓度比例对比')
    ax1.set_xticks(x)
    ax1.set_xticklabels(groups)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 惩罚值对比
    accuracy_penalties = [float(x) for x in penalty_reward_df['准确性惩罚']]
    concentration_penalties = [float(x) for x in penalty_reward_df['浓度惩罚']]
    
    ax2.bar(x - width/2, accuracy_penalties, width, label='准确性惩罚', color='orange', alpha=0.8)
    ax2.bar(x + width/2, concentration_penalties, width, label='浓度惩罚', color='red', alpha=0.8)
    ax2.set_xlabel('BMI分组')
    ax2.set_ylabel('惩罚值')
    ax2.set_title('各分组惩罚值对比')
    ax2.set_xticks(x)
    ax2.set_xticklabels(groups)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 奖励值对比
    accuracy_rewards = [float(x) for x in penalty_reward_df['准确性奖励']]
    concentration_rewards = [float(x) for x in penalty_reward_df['浓度奖励']]
    
    ax3.bar(x - width/2, accuracy_rewards, width, label='准确性奖励', color='lightgreen', alpha=0.8)
    ax3.bar(x + width/2, concentration_rewards, width, label='浓度奖励', color='green', alpha=0.8)
    ax3.set_xlabel('BMI分组')
    ax3.set_ylabel('奖励值')
    ax3.set_title('各分组奖励值对比')
    ax3.set_xticks(x)
    ax3.set_xticklabels(groups)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 净惩罚值
    net_penalties = [float(x) for x in penalty_reward_df['净惩罚']]
    colors = ['green' if x < 0 else 'red' for x in net_penalties]
    
    bars = ax4.bar(groups, net_penalties, color=colors, alpha=0.7)
    ax4.set_xlabel('BMI分组')
    ax4.set_ylabel('净惩罚值')
    ax4.set_title('各分组净惩罚值（负值表示净奖励）')
    ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax4.grid(True, alpha=0.3)
    
    # 添加数值标签
    for bar, value in zip(bars, net_penalties):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + (0.01 if height >= 0 else -0.02),
                f'{value:.4f}', ha='center', va='bottom' if height >= 0 else 'top')
    
    plt.tight_layout()
    plt.savefig('惩罚和奖励效果分析.png', dpi=300, bbox_inches='tight')
    plt.show()

visualize_penalty_reward_effects(penalty_reward_df)

print("\n分析完成，结果已保存到CSV文件和图像文件。")
print("\n惩罚和奖励机制说明：")
print("- 准确性惩罚：对'不准确'样本的惩罚，权重8.0")
print("- 浓度惩罚：对Y染色体浓度<0.04样本的惩罚，权重6.0")
print("- 准确性奖励：对'准确'样本的奖励，权重0.5")
print("- 浓度奖励：对Y染色体浓度≥0.04样本的奖励，权重0.3")
print("- 净惩罚：总惩罚减去总奖励，负值表示该分组获得净奖励")