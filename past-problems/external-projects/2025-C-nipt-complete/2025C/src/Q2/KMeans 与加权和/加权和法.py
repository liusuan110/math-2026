import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from scipy.optimize import minimize

# --- Matplotlib 全局美化设置 ---
plt.rcParams['font.sans-serif'] = ['STZhongsong']
plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (16, 10)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.unicode_minus'] = False


def load_and_prepare_data(filename):
    """加载数据并进行预处理。"""
    df = pd.read_csv(filename)

    def check_accuracy(row):
        return '准确' if (pd.isna(row['染色体的非整倍体']) and row['胎儿是否健康'] == '是') or \
                         (not pd.isna(row['染色体的非整倍体']) and row['胎儿是否健康'] == '否') else '不准确'

    df['是否准确'] = df.apply(check_accuracy, axis=1)
    conditions = [df['是否准确'] == '不准确', df['Y染色体浓度'] < 0.04]
    colors = ['red', 'orange']
    df['color'] = np.select(conditions, colors, default='royalblue')
    df['is_successful'] = (df['color'] == 'royalblue')
    return df


def risk_function(week):
    """定义潜在风险函数。"""
    if week <= 12:
        return 1
    elif 13 <= week <= 27:
        return 10 + 3 * (week - 13)
    else:
        return 100


def find_best_week_for_group(df_group, success_threshold=0.95, min_window_samples=20):
    """
    为数据子集找到最佳孕周，核心约束：窗口内样本数需达标。
    """
    if df_group.empty: return -1, 0, 0

    possible_weeks = range(10, 28)
    valid_weeks_with_stats = []

    # 1. 筛选出所有满足样本数约束的窗口
    for week in possible_weeks:
        week_window_df = df_group[(df_group['孕周'] >= week) & (df_group['孕周'] < week + 1)]
        if len(week_window_df) >= min_window_samples:
            success_rate = week_window_df['is_successful'].mean()
            valid_weeks_with_stats.append({'week': week, 'rate': success_rate})

    # 2. 如果不存在任何满足样本数要求的窗口，则此分组方案失败
    if not valid_weeks_with_stats:
        return -1, 0, 0  # 返回失败信号

    # 3. 在有效窗口中，寻找满足成功率阈值的最早窗口
    candidate_weeks = [w['week'] for w in valid_weeks_with_stats if w['rate'] >= success_threshold]

    if candidate_weeks:
        best_week = min(candidate_weeks)
    else:  # 4. 如果没有窗口满足成功率，则在有效窗口中选择成功率最高的作为妥协
        best_week = max(valid_weeks_with_stats, key=lambda x: x['rate'])['week']

    final_window_df = df_group[(df_group['孕周'] >= best_week) & (df_group['孕周'] < best_week + 1)]
    accuracy = final_window_df['is_successful'].mean()
    risk = risk_function(best_week)
    return best_week, accuracy, risk


def objective_function(boundaries, df, w_risk, w_accuracy):
    """
    目标函数：检查每个分组是否都能找到有效的推荐窗口。
    """
    boundaries = sorted(boundaries)
    b_max = boundaries[-1] + 0.01
    df['group'] = pd.cut(df['孕妇BMI'], bins=[boundaries[0]] + boundaries[1:-1] + [b_max], labels=False, include_lowest=True, right=False)

    total_risk, total_samples_in_windows, successful_samples_in_windows = 0, 0, 0

    for i in range(len(boundaries) - 1):
        df_group = df[df['group'] == i]
        if df_group.empty: return 1e9  # 如果分组为空，则无效

        best_week, _, risk_value = find_best_week_for_group(df_group, min_window_samples=30)

        # --- 核心约束检查 ---
        if best_week == -1:  # 检查是否收到了失败信号
            return 1e9  # 只要有一个分组找不到有效窗口，整个边界方案就无效

        total_risk += risk_value * len(df_group)
        window_df = df_group[(df_group['孕周'] >= best_week) & (df_group['孕周'] < best_week + 1)]
        total_samples_in_windows += len(window_df)
        successful_samples_in_windows += window_df['is_successful'].sum()

    avg_risk = total_risk / len(df)
    total_accuracy = successful_samples_in_windows / total_samples_in_windows

    return w_risk * avg_risk + w_accuracy * (1 - total_accuracy)


def plot_results(df, group_results):
    """绘制散点图和最佳NIPT时点矩形。"""
    plt.figure(figsize=(16, 10))
    plt.scatter(df['孕妇BMI'], df['孕周'], c=df['color'], alpha=0.6, s=50)
    ax = plt.gca()
    for result in group_results:
        bmi_min, bmi_max = result['bmi_range']
        optimal_week = result['optimal_week']
        if optimal_week == -1: continue
        rect = Rectangle((bmi_min, optimal_week), bmi_max - bmi_min, 1, linewidth=2.5, edgecolor='limegreen', facecolor='limegreen', alpha=0.4,
                         linestyle='--')
        ax.add_patch(rect)
        text_content = f"推荐孕周: {optimal_week}-{optimal_week + 1}\n窗口样本数: {result['window_count']}\n准确率: {result['accuracy']:.2%}"
        plt.text((bmi_min + bmi_max) / 2, optimal_week + 1.5, text_content, ha='center', va='bottom', fontsize=10, fontweight='bold',
                 color='darkgreen')

    plt.title('孕妇BMI与孕周关系及各组最佳NIPT时点推荐 (窗口样本数约束)', fontsize=20)
    plt.xlabel('孕妇 BMI 指标', fontsize=16)
    plt.ylabel('检测孕周 (周)', fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.6)
    legend_elements = [Line2D([0], [0], marker='o', color='w', label='不准确样本 (红色)', markerfacecolor='red', markersize=12),
                       Line2D([0], [0], marker='o', color='w', label='Y染色体浓度 < 4% (橙色)', markerfacecolor='orange', markersize=12),
                       Line2D([0], [0], marker='o', color='w', label='正常样本 (蓝色)', markerfacecolor='royalblue', markersize=12),
                       Line2D([0], [0], color='limegreen', lw=4, label='推荐NIPT时点窗口', linestyle='--')]
    plt.legend(handles=legend_elements, title='样本分类', loc='best', fontsize=14)
    plt.savefig('BMI分组和最佳NIPT时点.pdf', dpi=300, bbox_inches='tight')
    plt.show()


def main():
    df = load_and_prepare_data('../../../sources/男胎(Q2)(添加判断结果).csv')

    print("--- 步骤1: 设置优化问题 (含窗口最小样本数硬性约束) ---")
    bmi_min, bmi_max = df['孕妇BMI'].min(), df['孕妇BMI'].max()
    initial_boundaries = df['孕妇BMI'].quantile([0, 0.25, 0.5, 0.75, 1.0]).tolist()
    bounds = [(bmi_min, bmi_max) for _ in range(5)]
    constraints = [{'type': 'ineq', 'fun': lambda x, i=i: x[i + 1] - x[i] - 0.01} for i in range(4)]

    print("优化初始边界:", [round(b, 2) for b in initial_boundaries])
    print("开始使用 scipy.optimize.minimize 进行求解...")

    result = minimize(
        fun=objective_function,
        x0=initial_boundaries,
        args=(df, 0.7, 0.3),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'disp': True, 'maxiter': 200}
    )

    optimal_boundaries = sorted(result.x)

    print("\n--- 最终决策结果 ---")
    print("通过优化算法得到的最优决策变量 (BMI分割点):")
    print([round(b, 2) for b in optimal_boundaries])

    b_max = optimal_boundaries[-1] + 0.01
    df['final_group'] = pd.cut(df['孕妇BMI'], bins=[optimal_boundaries[0]] + optimal_boundaries[1:-1] + [b_max], labels=False, include_lowest=True,
                               right=False)
    group_results = []
    for i in range(len(optimal_boundaries) - 1):
        df_group = df[df['final_group'] == i]
        best_week, accuracy, _ = find_best_week_for_group(df_group, min_window_samples=30)
        window_count = 0
        if best_week != -1:
            window_count = len(df_group[(df_group['孕周'] >= best_week) & (df_group['孕周'] < best_week + 1)])
        group_results.append({
            'bmi_range': (optimal_boundaries[i], optimal_boundaries[i + 1]),
            'optimal_week': best_week,
            'accuracy': accuracy,
            'count': len(df_group),
            'window_count': window_count
        })

    print(f"\n{'BMI分组':<10} | {'BMI区间':<25} | {'总样本数':<10} | {'最佳NIPT时点':<15} | {'窗口样本数':<12} | {'窗口内准确率':<15}")
    print("-" * 105)
    for i, res in enumerate(group_results):
        bmi_range_str = f"[{res['bmi_range'][0]:.2f}, {res['bmi_range'][1]:.2f})"
        optimal_week_str = f"{res['optimal_week']}-{res['optimal_week'] + 1}" if res['optimal_week'] != -1 else "无推荐"
        print(
            f"{f'分组 {i + 1}':<10} | {bmi_range_str:<25} | {res['count']:<10} | {optimal_week_str:<15} | {res['window_count']:<12} | {f'{res['accuracy']:.2%}':<15}")

    print("\n--- 生成可视化图表 ---")
    plot_results(df, group_results)


if __name__ == '__main__':
    main()