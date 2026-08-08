import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from scipy.optimize import differential_evolution, NonlinearConstraint

plt.rcParams['font.sans-serif'] = ['SimHei']
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


def load_data(filename):
    # 加载数据并进行预处理
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


def risk_func(week):
    if week <= 12:
        return 1
    elif 13 <= week <= 27:
        return 10 + 3 * (week - 13)
    else:
        return 100


def predict_y(w, bmi, c=1):
    return 0.218290 - 0.011993 * w + 0.000326 * w ** 2 - 0.002045 * bmi + 0.012028 * c


def find_best_week(df_group, bmi_mid, min_samples=10, max_samples=50):
    # 为数据子集找到最佳孕周
    if df_group.empty:
        return -1, 0, 0, False

    possible_weeks = range(10, 26)
    strict_valid_weeks = []

    # 严格搜索
    for week in possible_weeks:
        week_df = df_group[(df_group['孕周'] >= week) & (df_group['孕周'] < week + 2)]
        n_samples = len(week_df)
        if min_samples <= n_samples < max_samples:
            y_gt_6_rate = week_df['is_y_gt_6_percent'].mean()
            if y_gt_6_rate >= 0.50:
                pred_y = predict_y(w=week, bmi=bmi_mid, c=1)
                if pred_y >= 0.04:
                    success_rate = week_df['is_successful'].mean()
                    strict_valid_weeks.append({'week': week, 'rate': success_rate})

    if strict_valid_weeks:
        best_candidate = min(strict_valid_weeks, key=lambda x: (risk_func(x['week']), -x['rate']))
        return best_candidate['week'], best_candidate['rate'], risk_func(best_candidate['week']), True

    # 宽松搜索
    relaxed_valid_weeks = []
    for week in possible_weeks:
        week_df = df_group[(df_group['孕周'] >= week) & (df_group['孕周'] < week + 2)]
        n_samples = len(week_df)
        if min_samples <= n_samples < max_samples:
            success_rate = week_df['is_successful'].mean()
            relaxed_valid_weeks.append({'week': week, 'rate': success_rate})

    if not relaxed_valid_weeks:
        return -1, 0, 0, False

    best_candidate = min(relaxed_valid_weeks, key=lambda x: (risk_func(x['week']), -x['rate']))
    return best_candidate['week'], best_candidate['rate'], risk_func(best_candidate['week']), False


def obj_func(bounds, df, w_risk, w_acc, min_samples=10, max_samples=50):
    # 目标函数
    bounds = sorted(bounds)
    b_max = bounds[-1] + 0.01
    df['group'] = pd.cut(df['孕妇BMI'], bins=[bounds[0]] + bounds[1:-1] + [b_max], labels=False, include_lowest=True, right=False)

    total_risk, total_samples, success_samples = 0, 0, 0
    penalty = 0
    n_groups = len(bounds) - 1

    for i in range(n_groups):
        df_group = df[df['group'] == i]
        if df_group.empty: return 1e9

        bmi_mid = (bounds[i] + bounds[i+1]) / 2
        best_week, _, risk_value, is_strict_pass = find_best_week(
            df_group, bmi_mid, min_samples, max_samples
        )

        if best_week == -1: return 1e9

        # 若解不满足严格约束，则施加惩罚
        if not is_strict_pass:
            penalty += 1000

        total_risk += risk_value * len(df_group)
        window_df = df_group[(df_group['孕周'] >= best_week) & (df_group['孕周'] < best_week + 2)]
        total_samples += len(window_df)
        success_samples += window_df['is_successful'].sum()

    if total_samples == 0: return 1e9

    avg_risk = total_risk / len(df)
    total_acc = success_samples / total_samples
    return w_risk * avg_risk + w_acc * (1 - total_acc) + penalty


def plot_res(df, group_res):
    # 绘制结果散点图
    plt.figure(figsize=(16, 10))
    plt.scatter(df['孕妇BMI'], df['孕周'], c=df['color'], alpha=0.6, s=50)
    ax = plt.gca()
    for res in group_res:
        bmi_min, bmi_max = res['bmi_range']
        opt_week = res['optimal_week']
        if opt_week == -1: continue

        rect = Rectangle((bmi_min, opt_week), bmi_max - bmi_min, 2, linewidth=2.5, edgecolor='limegreen', facecolor='limegreen', alpha=0.4,
                         linestyle='--')
        ax.add_patch(rect)

        y_text_pos = opt_week + 2.2 if opt_week < 20 else opt_week - 3.5
        text_content = (f"推荐孕周: {opt_week}-{opt_week + 2}\n"
                        f"窗口内成功率: {res['accuracy']:.2%}")
        plt.text((bmi_min + bmi_max) / 2, y_text_pos, text_content, ha='center', va='bottom', fontsize=12, fontweight='bold',
                 color='darkgreen', bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2'))

    plt.title('孕妇BMI与孕周关系及各组最佳NIPT时点推荐 (全局优化)', fontsize=20)
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


def plot_error_analysis(analysis_res):
    # 绘制成功率对比图
    group_labels = [f"分组 {i + 1}\nBMI: {res['bmi_range_str']}" for i, res in enumerate(analysis_res)]
    base_rates = [res['group_baseline_success_rate'] for res in analysis_res]
    opt_rates = [res['optimized_success_rate'] for res in analysis_res]
    x = np.arange(len(group_labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 8))
    rects1 = ax.bar(x - width / 2, base_rates, width, label='组内基线成功率', color='gray')
    rects2 = ax.bar(x + width / 2, opt_rates, width, label='优化后成功率', color='limegreen')

    ax.set_ylabel('检测成功率 (%)', fontsize=16)
    ax.set_title('各BMI分组优化前后的检测成功率对比 (全局优化)', fontsize=20)
    ax.set_xticks(x)
    ax.set_xticklabels(group_labels, rotation=0, ha="center", fontsize=14)
    ax.legend(fontsize=14)
    min_rate = min(min(base_rates), min(opt_rates)) if opt_rates and any(opt_rates) else 0
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
    # 主函数
    df = load_data('../../sources/男胎(Q2)(添加判断结果).csv')

    bmi_min, bmi_max = df['孕妇BMI'].min(), df['孕妇BMI'].max()
    bounds = [(bmi_min, bmi_max) for _ in range(5)]

    # 约束：BMI分组最小宽度 b_i+1 - b_i >= 2.5
    def min_width_constraint_func(x):
        return np.array(x)[1:] - np.array(x)[:-1]

    nonlinear_constraint = NonlinearConstraint(min_width_constraint_func, 2.5, np.inf)

    # 优化时使用的窗口样本量约束
    min_samples_opt = 20
    max_samples_opt = 100

    res = differential_evolution(
        func=obj_func,
        bounds=bounds,
        args=(df, 0.7, 0.3, min_samples_opt, max_samples_opt),
        constraints=nonlinear_constraint,
        maxiter=100,
        popsize=30,
        polish=True,
        updating='deferred',
        workers=4,
        disp=True
    )

    opt_bounds = sorted(res.x)

    # --- 优化结果输出 ---
    print(f"最优决策变量 (BMI分割点): {[round(float(b), 2) for b in opt_bounds]}")

    b_max = opt_bounds[-1] + 0.01
    df['final_group'] = pd.cut(df['孕妇BMI'], bins=[opt_bounds[0]] + opt_bounds[1:-1] + [b_max], labels=False, include_lowest=True,
                               right=False)

    plot_results = []
    error_results = []

    for i in range(len(opt_bounds) - 1):
        df_group = df[df['final_group'] == i]
        if df_group.empty: continue

        group_baseline_success_rate = df_group['is_successful'].mean()
        bmi_mid = (opt_bounds[i] + opt_bounds[i + 1]) / 2

        best_week, acc_window, _, _ = find_best_week(
            df_group, bmi_mid, min_samples_opt, max_samples_opt
        )

        win_count = 0
        opt_success_rate = 0.0
        if best_week != -1:
            window_df = df_group[(df_group['孕周'] >= best_week) & (df_group['孕周'] < best_week + 2)]
            win_count = len(window_df)
            opt_success_rate = window_df['is_successful'].mean() if win_count > 0 else 0.0
        else:
            acc_window = 0.0

        bmi_range_str = f"{opt_bounds[i]:.2f}, {opt_bounds[i + 1]:.2f})"

        plot_results.append({
            'bmi_range': (opt_bounds[i], opt_bounds[i + 1]),
            'optimal_week': best_week,
            'accuracy': acc_window,
            'window_count': win_count
        })

        error_results.append({
            'bmi_range_str': bmi_range_str,
            'group_baseline_success_rate': group_baseline_success_rate,
            'optimized_success_rate': opt_success_rate
        })

    print(f"{'BMI分组':<10} | {'BMI区间':<22} | {'最佳NIPT时点 (周)':<18} | {'窗口内成功率':<15}")

    for i, res in enumerate(plot_results):
        bmi_range_str = f"[{res['bmi_range'][0]:.2f}, {res['bmi_range'][1]:.2f})"
        optimal_week_str = f"{res['optimal_week']} - {res['optimal_week'] + 2}" if res['optimal_week'] != -1 else "无推荐"
        print(f"分组 {i + 1:<8} | {bmi_range_str:<22} | {optimal_week_str:<18} | {f'{res["accuracy"]:.2%}':<15}")

    plot_res(df, plot_results)
    plot_error_analysis(error_results)


if __name__ == '__main__':
    main()
