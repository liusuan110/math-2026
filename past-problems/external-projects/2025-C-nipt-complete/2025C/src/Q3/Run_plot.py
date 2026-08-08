import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

# --- Matplotlib 全局美化设置 ---
plt.rcParams['font.sans-serif'] = ['STZhongsong', 'SimHei']
plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
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
    df['is_y_gt_6_percent'] = (df['Y染色体浓度'] > 0.06)
    return df


def risk_function(week):
    """定义潜在风险函数。"""
    if week <= 12:
        return 1
    elif 13 <= week <= 27:
        return 10 + 3 * (week - 13)
    else:
        return 100


def predict_y_concentration(w, bmi, c=1):
    """根据第一问的模型预测Y染色体浓度。"""
    return 0.218290 - 0.011993 * w + 0.000326 * w ** 2 - 0.002045 * bmi + 0.012028 * c


def find_best_week_for_group(df_group, group_bmi_midpoint, min_window_samples=10, max_window_samples=50):
    """为数据子集找到最佳孕周。采用严格-宽松两轮搜索策略。"""
    if df_group.empty:
        return -1, 0, 0, False

    possible_weeks = range(10, 26)
    strict_valid_weeks = []

    # 严格搜索
    for week in possible_weeks:
        week_window_df = df_group[(df_group['孕周'] >= week) & (df_group['孕周'] < week + 2)]
        num_samples = len(week_window_df)
        if min_window_samples <= num_samples < max_window_samples:
            y_gt_6_proportion = week_window_df['is_y_gt_6_percent'].mean()
            if y_gt_6_proportion >= 0.50:
                predicted_y = predict_y_concentration(w=week, bmi=group_bmi_midpoint, c=1)
                if predicted_y >= 0.04:
                    success_rate = week_window_df['is_successful'].mean()
                    strict_valid_weeks.append({'week': week, 'rate': success_rate})

    if strict_valid_weeks:
        best_candidate = min(strict_valid_weeks, key=lambda x: (risk_function(x['week']), -x['rate']))
        return best_candidate['week'], best_candidate['rate'], risk_function(best_candidate['week']), True

    # 宽松搜索
    relaxed_valid_weeks = []
    for week in possible_weeks:
        week_window_df = df_group[(df_group['孕周'] >= week) & (df_group['孕周'] < week + 2)]
        num_samples = len(week_window_df)
        if min_window_samples <= num_samples < max_window_samples:
            success_rate = week_window_df['is_successful'].mean()
            relaxed_valid_weeks.append({'week': week, 'rate': success_rate})

    if not relaxed_valid_weeks:
        return -1, 0, 0, False

    best_candidate = min(relaxed_valid_weeks, key=lambda x: (risk_function(x['week']), -x['rate']))
    return best_candidate['week'], best_candidate['rate'], risk_function(best_candidate['week']), False


def plot_results(df, group_results):
    """绘制最终的优化结果散点图。"""
    plt.figure(figsize=(16, 10))
    plt.scatter(df['孕妇BMI'], df['孕周'], c=df['color'], alpha=0.6, s=50)
    ax = plt.gca()
    for result in group_results:
        bmi_min, bmi_max = result['bmi_range']
        optimal_week = result['optimal_week']
        if optimal_week == -1: continue

        rect = Rectangle((bmi_min, optimal_week), bmi_max - bmi_min, 2, linewidth=2.5, edgecolor='limegreen', facecolor='limegreen', alpha=0.4,
                         linestyle='--')
        ax.add_patch(rect)

        y_text_pos = optimal_week + 2.2 if optimal_week < 20 else optimal_week - 3.5
        text_content = (f"推荐孕周: {optimal_week}-{optimal_week + 2}\n"
                        f"窗口内成功率: {result['accuracy']:.2%}")
        plt.text((bmi_min + bmi_max) / 2, y_text_pos, text_content, ha='center', va='bottom', fontsize=12, fontweight='bold',
                 color='darkgreen', bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2'))

    plt.title('孕妇BMI与孕周关系及各组最佳NIPT时点推荐', fontsize=20)
    plt.xlabel('孕妇 BMI 指标', fontsize=16)
    plt.ylabel('检测孕周 (周)', fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.6)

    legend_elements = [Line2D([0], [0], marker='o', color='w', label='不准确样本 (红色)', markerfacecolor='red', markersize=12),
                       Line2D([0], [0], marker='o', color='w', label='Y染色体浓度 < 4% (橙色)', markerfacecolor='orange', markersize=12),
                       Line2D([0], [0], marker='o', color='w', label='正常样本 (蓝色)', markerfacecolor='royalblue', markersize=12),
                       Line2D([0], [0], color='limegreen', lw=4, label='推荐NIPT时点窗口(2周)', linestyle='--')]
    plt.legend(handles=legend_elements, title='样本分类', loc='best', fontsize=14)
    plt.savefig('BMI分组和最佳NIPT时点.pdf', dpi=300, bbox_inches='tight')
    plt.show()


def plot_error_analysis_grouped(analysis_results):
    """绘制优化前后成功率对比的条形图。"""
    group_labels = [f"分组 {i + 1}\nBMI: {res['bmi_range_str']}" for i, res in enumerate(analysis_results)]
    baseline_rates = [res['group_baseline_success_rate'] for res in analysis_results]
    optimized_rates = [res['optimized_success_rate'] for res in analysis_results]
    x = np.arange(len(group_labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 8))
    rects1 = ax.bar(x - width / 2, baseline_rates, width, label='组内基线成功率', color='gray')
    rects2 = ax.bar(x + width / 2, optimized_rates, width, label='推荐窗口成功率', color='limegreen')

    ax.set_ylabel('检测成功率 (%)', fontsize=16)
    ax.set_title('各BMI分组基线与推荐窗口的检测成功率对比', fontsize=20)
    ax.set_xticks(x)
    ax.set_xticklabels(group_labels, rotation=0, ha="center", fontsize=14)
    ax.legend(fontsize=14)
    min_rate = min(min(baseline_rates), min(optimized_rates)) if optimized_rates and any(optimized_rates) else 0
    ax.set_ylim(bottom=max(0, min_rate - 0.1), top=1.05)

    def autolabel(rects, color='black'):
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{height:.2%}', xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', color=color, fontweight='bold', fontsize=14)

    autolabel(rects1, 'dimgray')
    autolabel(rects2, 'darkgreen')
    fig.tight_layout()
    plt.savefig('组内检测成功率对比分析.pdf', dpi=300, bbox_inches='tight')
    plt.show()


def main():
    df = load_and_prepare_data('../../sources/男胎(Q2)(添加判断结果).csv')
    optimal_boundaries = [29.07, 31.57, 34.11, 36.84, 43.07]

    print("\n" + "=" * 80)
    print(" " * 18 + "已加载指定的NIPT时点推荐方案")
    print("=" * 80)
    print(f"使用的BMI分割点: {optimal_boundaries}")
    print("=" * 80 + "\n")


    # --- 后续分析与结果展示部分保持不变 ---

    # 窗口样本量约束 (用于find_best_week_for_group函数)
    min_window_samples_for_analysis = 20
    max_window_samples_for_analysis = 100

    b_max = optimal_boundaries[-1] + 0.01
    df['final_group'] = pd.cut(df['孕妇BMI'], bins=optimal_boundaries, labels=False, include_lowest=True, right=False)

    group_results_for_plot = []
    error_analysis_results = []

    for i in range(len(optimal_boundaries) - 1):
        df_group = df[df['final_group'] == i]
        if df_group.empty: continue

        group_baseline_success_rate = df_group['is_successful'].mean()
        group_bmi_midpoint = (optimal_boundaries[i] + optimal_boundaries[i + 1]) / 2

        best_week, accuracy_in_window, _, _ = find_best_week_for_group(
            df_group, group_bmi_midpoint, min_window_samples_for_analysis, max_window_samples_for_analysis
        )

        window_count = 0
        optimized_success_rate = 0.0
        if best_week != -1:
            window_df = df_group[(df_group['孕周'] >= best_week) & (df_group['孕周'] < best_week + 2)]
            window_count = len(window_df)
            optimized_success_rate = window_df['is_successful'].mean() if window_count > 0 else 0.0
        else:
            accuracy_in_window = 0.0

        bmi_range_str = f"[{optimal_boundaries[i]:.2f}, {optimal_boundaries[i + 1]:.2f})"

        group_results_for_plot.append({
            'bmi_range': (optimal_boundaries[i], optimal_boundaries[i + 1]),
            'optimal_week': best_week,
            'accuracy': accuracy_in_window,
            'window_count': window_count
        })

        error_analysis_results.append({
            'bmi_range_str': bmi_range_str,
            'group_baseline_success_rate': group_baseline_success_rate,
            'optimized_success_rate': optimized_success_rate
        })

    # --- 最终方案表格输出 ---
    print("\n" + "=" * 80)
    print(" " * 28 + "最终NIPT时点推荐方案")
    print("=" * 80)
    print(
        f"{'BMI分组':<10} | {'BMI区间':<22} | {'总样本数':<10} | {'最佳NIPT时点 (周)':<18} | {'窗口样本数':<12} | {'窗口内成功率':<15}")
    print("-" * 105)

    for i, res in enumerate(group_results_for_plot):
        bmi_range_str = f"[{res['bmi_range'][0]:.2f}, {res['bmi_range'][1]:.2f})"
        optimal_week_str = f"{res['optimal_week']} - {res['optimal_week'] + 2}" if res['optimal_week'] != -1 else "无推荐"
        total_samples = len(df[df['final_group'] == i])
        print(
            f"分组 {i + 1:<8} | {bmi_range_str:<22} | {total_samples:<10} | {optimal_week_str:<18} | {res['window_count']:<12} | {f'{res.get("accuracy", 0):.2%}':<15}")

    print("=" * 80 + "\n")

    plot_results(df, group_results_for_plot)
    plot_error_analysis_grouped(error_analysis_results)


if __name__ == '__main__':
    main()