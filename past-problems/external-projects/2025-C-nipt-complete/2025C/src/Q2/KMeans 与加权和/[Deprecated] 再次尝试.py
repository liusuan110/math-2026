import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import differential_evolution
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

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
    """加载数据，并准备is_successful列和绘图颜色。"""
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


def find_best_week_by_score(df_group, w_risk, w_acc):
    """
    【核心函数】通过计算每个窗口的“质量评分”，寻找最优孕周。
    """
    if df_group.empty:
        return -1, 0, 0, 0  # week, rate, score, num_samples

    best_score = float('inf')
    best_week = -1
    best_rate = 0
    best_window_samples = 0

    possible_weeks = range(10, 28)

    for week in possible_weeks:
        week_window_df = df_group[(df_group['孕周'] >= week) & (df_group['孕周'] < week + 1)]

        num_samples = len(week_window_df)
        if num_samples == 0:
            # 对于没有样本的窗口，可以给一个默认的中性或惩罚性评分
            # 这里我们选择跳过，因为它对加权平均没有贡献
            continue

        success_rate = week_window_df['is_successful'].mean()
        risk = risk_function(week)

        # 计算该窗口的质量评分
        score = w_risk * risk + w_acc * (1 - success_rate)

        if score < best_score:
            best_score = score
            best_week = week
            best_rate = success_rate
            best_window_samples = num_samples

    if best_week == -1:
        # 如果一个分组在所有孕周都没有任何样本，则返回失败
        return -1, 0, 0, 0

    return best_week, best_rate, best_score, best_window_samples


def objective_function_robust(boundaries, df, w_risk, w_acc):
    """
    最终稳健版的目标函数，使用样本数作为可信度进行加权。
    """
    boundaries = sorted(boundaries)
    b_max = boundaries[-1] + 0.01
    df['group'] = pd.cut(df['孕妇BMI'], bins=[boundaries[0]] + list(boundaries[1:-1]) + [b_max], labels=False, include_lowest=True, right=False)

    total_weighted_score = 0
    total_weights = 0

    for i in range(len(boundaries) - 1):
        df_group = df[df['group'] == i]
        if df_group.empty:
            # 对产生空分组的边界点施加惩罚
            return 1e9

        # 为该分组找到最优窗口及其质量评分和样本数
        _, _, best_score, window_samples = find_best_week_by_score(df_group, w_risk, w_acc)

        if window_samples > 0:
            # 核心思想：用窗口样本数作为权重，对该窗口的质量评分进行加权求和
            total_weighted_score += best_score * window_samples
            total_weights += window_samples

    if total_weights == 0:
        return 1e9  # 如果所有分组都没有任何样本，则这是一个无效的边界划分

    # 最终的目标是最小化所有分组的加权平均质量分
    return total_weighted_score / total_weights


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

    plt.title('基于质量评分与全局优化的各BMI分组最佳NIPT时点', fontsize=20)
    plt.xlabel('孕妇 BMI 指标', fontsize=16)
    plt.ylabel('检测孕周 (周)', fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.6)
    legend_elements = [Line2D([0], [0], marker='o', color='w', label='不准确样本 (红色)', markerfacecolor='red', markersize=12),
                       Line2D([0], [0], marker='o', color='w', label='Y浓度不足样本 (橙色)', markerfacecolor='orange', markersize=12),
                       Line2D([0], [0], marker='o', color='w', label='正常样本 (蓝色)', markerfacecolor='royalblue', markersize=12),
                       Line2D([0], [0], color='limegreen', lw=4, label='推荐NIPT时点窗口')]
    plt.legend(handles=legend_elements, title='图例', loc='best', fontsize=14)
    plt.savefig('Q2_BMI分组和最佳NIPT时点_final_robust.png', dpi=300)
    plt.show()


def main():
    """主函数"""
    input_filename = '../../../sources/男胎(Q2)(添加判断结果).csv'
    df = load_and_prepare_data(input_filename)

    print("--- 步骤1: 设置优化问题 (基于质量评分的稳健模型) ---")
    w_risk, w_acc = 0.7, 0.3

    bmi_min, bmi_max = df['孕妇BMI'].min(), df['孕妇BMI'].max()
    bounds = [(bmi_min, bmi_max) for _ in range(5)]

    print("开始使用 scipy.optimize.differential_evolution 进行全局优化...")
    print("这个新模型更加稳健，应该能够找到有意义的最优解。请稍候...")

    result = differential_evolution(
        func=objective_function_robust,
        bounds=bounds,
        args=(df, w_risk, w_acc),
        strategy='best1bin',
        maxiter=100,
        popsize=20,  # 适当增加种群大小以增强搜索能力
        tol=0.01,
        mutation=(0.5, 1),
        recombination=0.7,
        updating='immediate',
        disp=True
    )

    optimal_boundaries = sorted(result.x)

    print("\n--- 最终决策结果 ---")
    print("通过差分进化优化得到的最优决策变量 (BMI分割点):")
    print([round(b, 2) for b in optimal_boundaries])

    b_max = optimal_boundaries[-1] + 0.01
    df['final_group'] = pd.cut(df['孕妇BMI'], bins=[optimal_boundaries[0]] + list(optimal_boundaries[1:-1]) + [b_max], labels=False,
                               include_lowest=True, right=False)

    group_results = []
    for i in range(len(optimal_boundaries) - 1):
        df_group = df[df['final_group'] == i]
        best_week, accuracy, _, window_count = find_best_week_by_score(df_group, w_risk, w_acc)

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