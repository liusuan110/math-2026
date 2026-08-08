import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from scipy.optimize import minimize

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


def load_data(filename):
    df = pd.read_csv(filename)

    def check_acc(row):
        return '准确' if (pd.isna(row['染色体的非整倍体']) and row['胎儿是否健康'] == '是') or \
                         (not pd.isna(row['染色体的非整倍体']) and row['胎儿是否健康'] == '否') else '不准确'

    df['是否准确'] = df.apply(check_acc, axis=1)
    conds = [df['是否准确'] == '不准确', df['Y染色体浓度'] < 0.04]
    colors = ['red', 'orange']
    df['color'] = np.select(conds, colors, default='royalblue')
    df['is_ok'] = (df['color'] == 'royalblue')
    return df


def risk_function(week):
    if week <= 12:
        return 1
    elif 13 <= week <= 27:
        return 10 + 3 * (week - 13)
    else:
        return 100


def find_best_week(df_group, succ_thresh=0.95, min_samples=10, max_samples=50):
    # 为数据子集找到最佳孕周，使用2周窗口宽度
    if df_group.empty: return -1, 0, 0

    weeks = range(10, 27)  # 结束周改为27，确保 week+2 不会超出范围
    valid_weeks = []

    for week in weeks:
        week_df = df_group[(df_group['孕周'] >= week) & (df_group['孕周'] < week + 2)]

        if min_samples <= len(week_df) < max_samples:
            succ_rate = week_df['is_ok'].mean()
            valid_weeks.append({'week': week, 'rate': succ_rate})

    if not valid_weeks:
        return -1, 0, 0

    cand_weeks = [w['week'] for w in valid_weeks if w['rate'] >= succ_thresh]

    if cand_weeks:
        best_week = min(cand_weeks)
    else:
        best_week = max(valid_weeks, key=lambda x: x['rate'])['week']

    final_df = df_group[(df_group['孕周'] >= best_week) & (df_group['孕周'] < best_week + 2)]
    acc = final_df['is_ok'].mean() if not final_df.empty else 0
    risk = risk_function(best_week)  # 风险仍然由起始周决定
    return best_week, acc, risk


def obj_func(bounds, df, w_risk, w_acc, min_samples=10, max_samples=50):
    # 优化目标函数
    bounds = sorted(bounds)
    b_max = bounds[-1] + 0.01
    df['group'] = pd.cut(df['孕妇BMI'], bins=[bounds[0]] + bounds[1:-1] + [b_max], labels=False, include_lowest=True, right=False)

    tot_risk, tot_samples, succ_samples = 0, 0, 0

    for i in range(len(bounds) - 1):
        df_grp = df[df['group'] == i]
        if df_grp.empty: return 1e9

        best_week, _, risk_val = find_best_week(df_grp,
                                               min_samples=min_samples,
                                               max_samples=max_samples)

        if best_week == -1: return 1e9

        tot_risk += risk_val * len(df_grp)
        win_df = df_grp[(df_grp['孕周'] >= best_week) & (df_grp['孕周'] < best_week + 2)]
        tot_samples += len(win_df)
        succ_samples += win_df['is_ok'].sum()

    if tot_samples == 0: return 1e9

    avg_risk = tot_risk / len(df)
    tot_acc = succ_samples / tot_samples

    return w_risk * avg_risk + w_acc * (1 - tot_acc)


def plot_results(df, grp_results):
    # 绘制优化结果散点图
    plt.figure(figsize=(16, 10))
    plt.scatter(df['孕妇BMI'], df['孕周'], c=df['color'], alpha=0.6, s=50)
    ax = plt.gca()
    for res in grp_results:
        bmi_min, bmi_max = res['bmi_range']
        opt_week = res['optimal_week']
        if opt_week == -1: continue
        rect = Rectangle((bmi_min, opt_week), bmi_max - bmi_min, 2, linewidth=2.5, edgecolor='limegreen', facecolor='limegreen', alpha=0.4,
                         linestyle='--')
        ax.add_patch(rect)
        txt = f"推荐孕周: {opt_week}-{opt_week + 2}\n窗口内成功率: {res['accuracy']:.2%}"
        plt.text((bmi_min + bmi_max) / 2, opt_week + 2.2, txt, ha='center', va='bottom', fontsize=10, fontweight='bold',
                 color='darkgreen')

    plt.title('孕妇BMI与孕周关系及各组最佳NIPT时点推荐 (2周窗口)', fontsize=20)
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
    # 绘制分组对比的成功率条形图
    grp_labels = [f"分组 {i + 1}\nBMI: {res['bmi_range_str']}" for i, res in enumerate(analysis_res)]
    base_rates = [res['group_baseline_success_rate'] for res in analysis_res]
    opt_rates = [res['optimized_success_rate'] for res in analysis_res]

    x = np.arange(len(grp_labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 8))
    rects1 = ax.bar(x - width / 2, base_rates, width, label='组内基线成功率 (该BMI分组内所有样本)', color='gray')
    rects2 = ax.bar(x + width / 2, opt_rates, width, label='优化后成功率 (仅推荐2周窗口内样本)', color='limegreen')

    ax.set_ylabel('检测成功率 (%)', fontsize=16)
    ax.set_title('各BMI分组优化前后的检测成功率对比 (2周窗口)', fontsize=20)
    ax.set_xticks(x)
    ax.set_xticklabels(grp_labels, rotation=0, ha="center", fontsize=14)
    ax.legend(fontsize=14)

    # 设置Y轴的起始点，以放大顶部的趋势差异
    min_rate = min(min(base_rates), min(opt_rates))
    ax.set_ylim(bottom=max(0, min_rate - 0.1), top=1.05)  # Y轴下限设为比最小值低10%，上限设为105%

    def add_labels(rects, color='black'):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2%}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', color=color, fontweight='bold',
                        fontsize=14)

    add_labels(rects1, 'dimgray')
    add_labels(rects2, 'darkgreen')

    fig.tight_layout()
    plt.savefig('组内检测成功率对比分析.pdf', dpi=300)
    plt.show()


def main():
    # --- 数据加载 ---
    df = load_data('../../../sources/男胎(Q2)(添加判断结果).csv')

    # --- 1. 运行优化模型 ---
    bmi_min, bmi_max = df['孕妇BMI'].min(), df['孕妇BMI'].max()
    init_bounds = df['孕妇BMI'].quantile([0, 0.25, 0.5, 0.75, 1.0]).tolist()
    bounds = [(bmi_min, bmi_max) for _ in range(5)]
    constraints = [{'type': 'ineq', 'fun': lambda x, i=i: x[i + 1] - x[i] - 0.01} for i in range(4)]

    min_samples = 50
    max_samples = 100

    result = minimize(
        fun=obj_func,
        x0=init_bounds,
        args=(df, 0.7, 0.3, min_samples, max_samples),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'disp': False, 'maxiter': 200}
    )

    opt_bounds = sorted(result.x)
    print("通过优化算法得到的最优决策变量 (BMI分割点):", [round(b, 2) for b in opt_bounds])

    # --- 2. 进行组内对比的误差分析 ---
    b_max = opt_bounds[-1] + 0.01
    df['final_group'] = pd.cut(df['孕妇BMI'], bins=[opt_bounds[0]] + opt_bounds[1:-1] + [b_max], labels=False, include_lowest=True,
                               right=False)

    plot_data = []
    err_analysis = []

    for i in range(len(opt_bounds) - 1):
        df_grp = df[df['final_group'] == i]
        if df_grp.empty: continue

        base_succ_rate = df_grp['is_ok'].mean()
        best_week, acc_in_window, _ = find_best_week(df_grp,
                                                   min_samples=min_samples,
                                                   max_samples=max_samples)
        win_count = 0
        opt_succ_rate = 0

        if best_week != -1:
            win_df = df_grp[(df_grp['孕周'] >= best_week) & (df_grp['孕周'] < best_week + 2)]
            win_count = len(win_df)
            opt_succ_rate = win_df['is_ok'].mean() if win_count > 0 else 0

        bmi_range = f"[{opt_bounds[i]:.2f}, {opt_bounds[i + 1]:.2f})"
        if best_week != -1:
            opt_succ_rate = 0

        plot_data.append({
            'bmi_range': (opt_bounds[i], opt_bounds[i + 1]),
            'optimal_week': best_week,
            'accuracy': acc_in_window,
            'window_count': win_count
        })
        err_analysis.append({
            'bmi_range_str': bmi_range,
            'group_baseline_success_rate': base_succ_rate,
            'optimized_success_rate': opt_succ_rate
        })

    # --- 3. 最终决策方案总结 ---
    print("\n最终决策方案总结 (2周窗口):")
    print(f"{'BMI分组':<10} | {'BMI区间':<25} | {'总样本数':<10} | {'最佳NIPT时点':<15} | {'窗口样本数':<12} | {'窗口内成功率':<15}")
    print("-" * 105)
    for i, res in enumerate(plot_data):
        bmi_range = f"[{res['bmi_range'][0]:.2f}, {res['bmi_range'][1]:.2f})"
        week_str = f"{res['optimal_week']}-{res['optimal_week'] + 2}" if res['optimal_week'] != -1 else "无推荐"
        print(
            f"{f'分组 {i + 1}':<10} | {bmi_range:<25} | {len(df[df['final_group'] == i]):<10} | {week_str:<15} | {res['window_count']:<12} | {f'{res['accuracy']:.2%}':<15}")

    # --- 4. 生成可视化图表 ---
    plot_results(df, plot_data)
    plot_error_analysis(err_analysis)


if __name__ == '__main__':
    main()