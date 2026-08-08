import pandas as pd
import numpy as np
from scipy.optimize import differential_evolution
from tqdm import tqdm


# --- 目标函数 (无需修改) ---
def objective_function(params, data):
    """
    计算给定参数下的目标函数值 (平均风险 - 准确率)

    参数 (params) 结构 (共8个):
    - params[0:4]: 4个时间窗口的下限 (Lk)
    - params[4:8]: 4个时间窗口的持续时长 (Uk - Lk)
    """
    time_lower_bounds = params[0:4]
    time_durations = params[4:8]
    time_upper_bounds = time_lower_bounds + time_durations

    selected_samples_mask = pd.Series([False] * len(data), index=data.index)

    for k in range(4):  # 遍历4个组
        group_k_mask = (data['bmi_group'] == k)
        time_window_mask = (data['孕周'] >= time_lower_bounds[k]) & (data['孕周'] <= time_upper_bounds[k])
        selected_samples_mask |= (group_k_mask & time_window_mask)

    selected_df = data[selected_samples_mask]

    if len(selected_df) == 0:
        return 1e6

    mean_risk = selected_df['risk'].mean()
    accuracy = selected_df['correct'].mean()
    objective_value = mean_risk - accuracy

    return objective_value


# --- 主程序逻辑 ---
if __name__ == '__main__':
    # --- 1. 加载数据并进行“等频分箱” ---
    try:
        df = pd.read_csv('../男胎_preprocessed.csv')
    except FileNotFoundError:
        print("错误：未找到 '男胎_preprocessed.csv' 文件。")
        exit()

    # ★★★ 核心改动：使用 pd.qcut 进行等频分箱 ★★★
    # q=4 表示分为4组，labels=False 表示返回组的编号 (0, 1, 2, 3)
    # duplicates='drop' 可以处理分割点上数值相同的情况
    df['bmi_group'] = pd.qcut(df['孕妇BMI'], q=4, labels=False, duplicates='drop')

    print("已根据数据分布完成“等频分箱”(每组人数基本相同)：")
    print(df['bmi_group'].value_counts().sort_index())

    # 为了报告结果，我们计算并保存每个组的实际BMI范围
    group_bmi_ranges = df.groupby('bmi_group')['孕妇BMI'].agg(['min', 'max'])
    print("\n各分组实际BMI范围：")
    print(group_bmi_ranges)
    print("-" * 30)

    MIN_WEEK, MAX_WEEK = df['孕周'].min(), df['孕周'].max()

    # --- 2. 设置优化问题的边界 (8个变量) ---
    bounds = []
    for _ in range(4):  # 4个时间下限
        bounds.append((MIN_WEEK, MAX_WEEK))
    week_range = MAX_WEEK - MIN_WEEK
    for _ in range(4):  # 4个时间时长
        bounds.append((0, week_range))

    # --- 3. 运行差分进化算法求解 ---
    print("开始进行优化求解 (4个等频分组，8个变量)...")

    MAX_ITERATIONS = 100
    pbar = tqdm(total=MAX_ITERATIONS, desc="优化进度")


    def progress_callback(xk, convergence):
        pbar.update(1)


    result = differential_evolution(
        func=objective_function,
        bounds=bounds,
        args=(df,),
        maxiter=MAX_ITERATIONS,
        popsize=15,
        disp=False,
        workers=-1,
        callback=progress_callback
    )
    pbar.close()

    # --- 4. 格式化并输出最终结果 ---
    print("\n-------------------- 优化结果 --------------------")
    if result.success:
        print(f"优化成功！找到最优解。")
        print(f"最终目标函数值 F = (平均风险 - 准确率) = {result.fun:.4f}")

        optimal_params = result.x
        time_lower_bounds = optimal_params[0:4]
        time_durations = optimal_params[4:8]
        time_upper_bounds = time_lower_bounds + time_durations

        print("\n【各BMI分组对应的最优NIPT检测时间窗口】\n")
        print(f"{'组号':<5} {'BMI区间 (根据实际数据划分)':<35} {'最佳检测时间窗口 (孕周)'}")
        print("-" * 80)
        for k in range(4):
            min_bmi = group_bmi_ranges.loc[k, 'min']
            max_bmi = group_bmi_ranges.loc[k, 'max']
            bmi_range_str = f"[{min_bmi:.2f}, {max_bmi:.2f}]"
            time_window_str = f"[{time_lower_bounds[k]:.2f}, {time_upper_bounds[k]:.2f}]"
            print(f"{k + 1:<5} {bmi_range_str:<35} {time_window_str}")
        print("-" * 80)
    else:
        print("优化未成功，可能未找到满足条件的最优解。")