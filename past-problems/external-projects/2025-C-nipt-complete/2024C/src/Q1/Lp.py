from pprint import pprint
import pandas as pd
import pulp

YEARS = 7

plot_info = {
    '地块ID': ['A1', 'A2', 'A3', 'A4', 'A5', 'A6',
               'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'B13', 'B14',
               'C1', 'C2', 'C3', 'C4', 'C5', 'C6',
               'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8',
               'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12', 'E13', 'E14', 'E15', 'E16',
               'F1', 'F2', 'F3', 'F4'],
    '地块类型': ['平旱地', '平旱地', '平旱地', '平旱地', '平旱地', '平旱地',
                 '梯田', '梯田', '梯田', '梯田', '梯田', '梯田', '梯田', '梯田', '梯田', '梯田', '梯田', '梯田', '梯田', '梯田',
                 '山坡地', '山坡地', '山坡地', '山坡地', '山坡地', '山坡地',
                 '水浇地', '水浇地', '水浇地', '水浇地', '水浇地', '水浇地', '水浇地', '水浇地',
                 '普通大棚', '普通大棚', '普通大棚', '普通大棚', '普通大棚', '普通大棚', '普通大棚', '普通大棚',
                 '普通大棚', '普通大棚', '普通大棚', '普通大棚', '普通大棚', '普通大棚', '普通大棚', '普通大棚',
                 '智慧大棚', '智慧大棚', '智慧大棚', '智慧大棚'],
    '面积': [80, 55, 35, 72, 68, 55,
             60, 46, 40, 28, 25, 86, 55, 44, 50, 25, 60, 45, 35, 20,
             15, 13, 15, 18, 27, 20, 15, 10, 14, 6, 10, 12, 22, 20,
             0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6,
             0.6, 0.6, 0.6, 0.6]
}
df_plots = pd.DataFrame(plot_info).set_index('地块ID')

crop_info = {
    '作物ID': list(range(1, 42)),
    '作物名称': ['黄豆', '黑豆', '红豆', '绿豆', '豌豆', '小米', '玉米', '谷子', '高粱', '黍子', '荞麦', '南瓜', '红薯', '小麦', '大麦',
                 '水稻', '豇豆', '刀豆', '毛豆', '土豆', '西红柿', '茄子', '菠菜', '育椒', '菜花', '包菜', '油麦菜', '小青菜', '黄瓜',
                 '生菜', '辣椒', '空心菜', '黄心菜', '芹菜', '大白菜', '白萝卜', '红萝卜', '榆黄菇', '香菇', '白灵菇', '羊肚菌'],
    '作物类型': ['粮食（豆类）', '粮食（豆类）', '粮食（豆类）', '粮食（豆类）', '粮食（豆类）', '粮食', '粮食', '粮食', '粮食', '粮食',
                 '粮食', '粮食', '粮食', '粮食', '粮食', '粮食', '蔬菜（豆类）', '蔬菜（豆类）', '蔬菜（豆类）', '蔬菜', '蔬菜', '蔬菜',
                 '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜',
                 '食用菌', '食用菌', '食用菌', '食用菌'],
}
df_crops = pd.DataFrame(crop_info).set_index('作物ID')

plot_data = df_plots.to_dict('index')
crop_data = df_crops.to_dict('index')

# 读取利润数据
df_profit = pd.read_csv('../../sources/每亩利润.csv')
crop_name_to_id = df_crops.reset_index().set_index('作物名称')['作物ID'].to_dict()
season_map = {'第一季': 1, '第二季': 2}
profit_dict = {}
for _, row in df_profit.iterrows():
    crop_name = row['作物名称']
    plot_type = row['地块类型']
    season_str = row['种植季次']
    profit_per_mu = row['每亩利润']
    if crop_name in crop_name_to_id and season_str in season_map:
        crop_id = crop_name_to_id[crop_name]
        season = season_map[season_str]
        profit_dict[(crop_id, plot_type, season)] = profit_per_mu

allowed_plantings = {}
VEG_EXCLUDED = [35, 36, 37] # 大白菜、白萝卜、红萝卜

# 循环变量 i - 年, j - 地块, k - 作物, s - 季节
for i in range(1, YEARS + 1):
    for j, j_info in plot_data.items():
        plot_type = j_info['地块类型']
        num_seasons = 2 if plot_type in ['水浇地', '普通大棚', '智慧大棚'] else 1
        for s in range(1, num_seasons + 1):
            for k, k_info in crop_data.items():
                crop_type = k_info['作物类型']
                is_allowed = False

                if plot_type in ['平旱地', '梯田', '山坡地']:
                    if '粮食' in crop_type and k != 16:
                        is_allowed = True
                elif plot_type == '水浇地':
                    if k == 16 and s == 1:
                        is_allowed = True
                    elif '蔬菜' in crop_type:
                        if s == 1 and k not in VEG_EXCLUDED:
                            is_allowed = True
                        elif s == 2 and k in VEG_EXCLUDED:
                            is_allowed = True
                elif plot_type == '普通大棚':
                    if s == 1 and '蔬菜' in crop_type and k not in VEG_EXCLUDED:
                        is_allowed = True
                    elif s == 2 and '食用菌' in crop_type:
                        is_allowed = True
                elif plot_type == '智慧大棚':
                    if '蔬菜' in crop_type and k not in VEG_EXCLUDED:
                        is_allowed = True
                if '食用菌' in crop_type and plot_type != '普通大棚':
                    is_allowed = False

                if is_allowed:
                    # 关键改动：索引顺序变为 (i, j, k, s)
                    allowed_plantings[(i, j, k, s)] = True

model = pulp.LpProblem("作物种植规划", pulp.LpMaximize)

# B_ijks: 第 i 年在第 j 地块上第 s 季度是否种植 k 号作物
# x_ijks: 种植面积
B_indices = allowed_plantings.keys()
B = pulp.LpVariable.dicts("B", B_indices, cat='Binary')
x = pulp.LpVariable.dicts("x", B_indices, lowBound=0, cat='Continuous')

# 定义目标函数：最大化总利润
# Sum(x_ijks * P_ksj)
model += pulp.lpSum(x[i, j, k, s] * profit_dict.get((k, plot_data[j]['地块类型'], s), 0)
                    for (i, j, k, s) in B_indices), "总利润"

# 定义约束条件
plot_ids = df_plots.index
crop_ids = df_crops.index

# 约束1: 面积约束 Sum(x_ijks) <= S_j, for each i, j, s
for i in range(1, YEARS + 1):
    for j in plot_ids:
        num_seasons = 2 if plot_data[j]['地块类型'] in ['水浇地', '普通大棚', '智慧大棚'] else 1
        for s in range(1, num_seasons + 1):
            model += pulp.lpSum(x.get((i, j, k, s), 0) for k in crop_ids) \
                     <= plot_data[j]['面积'], f"面积约束_{i}_{j}_{s}"

        # 约束2: 水稻占用约束
        if num_seasons == 2 and (i, j, 16, 1) in B_indices:
            model += pulp.lpSum(B.get((i, j, k, 2), 0) for k in crop_ids) <= (1 - B[i, j, 16, 1]), f"水稻占用约束_{i}_{j}"

# 约束3: 逻辑约束 x_ijks <= S_j * B_ijks
for (i, j, k, s) in B_indices:
    model += x[i, j, k, s] <= plot_data[j]['面积'] * B[i, j, k, s], f"逻辑约束_{i}_{j}_{k}_{s}"

# 约束4: 免重茬约束 B_ijks + B_(i+1)jks <= 1
for i in range(1, YEARS):
    for j in plot_ids:
        for k in crop_ids:
            # i 年种植 k 作物
            B_year1 = pulp.lpSum(B.get((i, j, k, s), 0) for s in [1, 2])
            # i+1 年种植 k 作物
            B_year2 = pulp.lpSum(B.get((i + 1, j, k, s), 0) for s in [1, 2])
            model += B_year1 + B_year2 <= 1, f"免重茬约束_{i}_{j}_{k}"

# 约束5: 豆类轮作约束
bean_crop_ids = df_crops[df_crops['作物类型'].str.contains('豆类')].index
if YEARS >= 3:
    # 注意：这里的 i 是起始年份
    for i in range(1, YEARS - 1):
        for j in plot_ids:
            model += pulp.lpSum(B.get((i_sub, j, k, s_sub), 0)
                                for i_sub in range(i, i + 3)
                                for s_sub in [1, 2]
                                for k in bean_crop_ids
                                if (i_sub, j, k, s_sub) in B_indices) >= 1, f"豆类轮作约束_{i}_{j}"

model.solve()

if pulp.LpStatus[model.status] == 'Optimal':
    print(f"\n最大总利润 = {pulp.value(model.objective):,.2f}")
    print("\n--- 最优种植计划 ---")

    results = []
    # 循环变量与建模符号对应
    for (i, j, k, s), B_var in B.items():
        if B_var.varValue > 0.99:
            area = x[i, j, k, s].varValue
            if area > 0.01:
                results.append({
                    '年份': i,
                    '季节': s,
                    '地块ID': j,
                    '地块类型': plot_data[j]['地块类型'],
                    '作物名称': crop_data[k]['作物名称'],
                    '种植面积(亩)': area
                })

    df_results = pd.DataFrame(results).sort_values(by=['年份', '地块ID', '季节'])
    pd.set_option('display.max_rows', None)
    print(df_results.to_string())
else:
    print(f"未能找到最优解。模型状态：{pulp.LpStatus[model.status]}")