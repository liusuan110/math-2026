import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- 0. 准备工作 ---

sns.set_style('darkgrid')
plt.rcParams['font.sans-serif'] = ['STZhongsong']
plt.rcParams['axes.unicode_minus'] = False

# --- 1. 加载数据和优化结果 ---
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
# 加载优化结果
result_table = pd.read_csv('BMI分组和最佳NIPT时点.csv')


# --- 2. 检测误差影响分析 ---
print("正在进行检测误差分析...")
# 根据优化结果筛选样本
selected_samples_list = []
bmi_splits = [float(val) for val in result_table['BMI范围'].str.strip('[]()').str.split(', ').str[0].tolist() + [
    result_table['BMI范围'].str.strip('[]()').str.split(', ').str[1].iloc[-1]]]

for i, row in result_table.iterrows():
    bmi_min, bmi_max = bmi_splits[i], bmi_splits[i + 1]
    time_min, time_max = row['最佳NIPT时点下限'], row['最佳NIPT时点上限']

    mask = (data['孕妇BMI'] >= bmi_min) & (data['孕妇BMI'] < bmi_max) & \
           (data['time'] >= time_min) & (data['time'] <= time_max)
    selected_samples_list.append(data[mask])

selected_data = pd.concat(selected_samples_list)
reliable_data = selected_data[selected_data['Y染色体浓度'] >= 0.04]

# 结果汇总
print("\n--- 检测误差分析结果 ---")
print(f"第一轮筛选后（符合窗口），样本数: {len(selected_data)}")
print(f"第二轮筛选后（Y浓度达标），样本数: {len(reliable_data)}")
print(f"因“检测误差”（Y浓度不达标）被剔除的样本数: {len(selected_data) - len(reliable_data)}")

# 可视化误差影响
plt.figure(figsize=(12, 8))
plt.scatter(data['孕妇BMI'], data['Y染色体浓度'], c='lightgray', alpha=0.3, label='所有样本')
plt.scatter(selected_data['孕妇BMI'], selected_data['Y染色体浓度'], c='blue', alpha=0.5,
            label=f'选中样本 ({len(selected_data)}个)')
plt.scatter(reliable_data['孕妇BMI'], reliable_data['Y染色体浓度'], c='red', alpha=0.7,
            label=f'达标样本 ({len(reliable_data)}个)')

for split in bmi_splits[1:-1]:
    plt.axvline(x=split, color='black', linestyle='--', alpha=0.5)
plt.axhline(y=0.04, color='green', linestyle='--', label='Y染色体浓度达标线(4%)')

plt.legend()
plt.xlabel('孕妇BMI')
plt.ylabel('Y染色体浓度')
plt.title('检测误差影响分析', fontsize=16)
plt.savefig('Q2_Error_Analysis_Impact.pdf')
print("误差分析图已保存至 'Q2_Error_Analysis_Impact.pdf'")
plt.show()

# --- 3. BMI与实际达标时间关系探索 ---
print("\n正在分析BMI与实际达标时间的关系...")
# 找到每个孕妇首次达标的记录
first_pass_records = data[data['Y染色体浓度'] >= 0.04].sort_values('孕周').drop_duplicates(subset='孕妇代码',
                                                                                           keep='first')

if not first_pass_records.empty:
    plt.figure(figsize=(12, 8))
    sns.regplot(data=first_pass_records, x='孕妇BMI', y='孕周', scatter_kws={'alpha': 0.6}, line_kws={'color': 'red'})
    plt.xlabel('孕妇BMI', fontsize=14)
    plt.ylabel('Y染色体浓度首次达标孕周', fontsize=14)
    plt.title('BMI与实际Y染色体浓度达标时间的关系', fontsize=16)
    plt.savefig('Q2_BMI_vs_PassTime.pdf')
    print("BMI与达标时间关系图已保存至 'Q2_BMI_vs_PassTime.pdf'")
    plt.show()
else:
    print("数据中没有Y染色体浓度达标的样本，无法进行此项分析。")

print("\n所有分析已完成！")