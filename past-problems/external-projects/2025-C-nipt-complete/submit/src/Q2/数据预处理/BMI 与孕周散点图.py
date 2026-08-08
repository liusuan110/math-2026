import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

plt.rcParams['font.sans-serif'] = ['STZhongsong']
plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'  # 保存后自动裁剪白边
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('../../../sources/男胎(Q2).csv', encoding='utf-8')
col_age = '孕周'
col_bmi = '孕妇BMI'
col_y_concentration = 'Y染色体浓度'
df['Y_below_4_percent'] = df[col_y_concentration] < 0.04
df_below_4 = df[df['Y_below_4_percent']]
df_above_4 = df[~df['Y_below_4_percent']]

plt.figure(figsize=(12, 8))

bmi_min, bmi_max = df[col_bmi].min(), df[col_bmi].max()
week_min, week_max = df[col_age].min(), df[col_age].max()

# 2. 使用 plt.xlim 和 plt.ylim 应用这个范围
#    我们可以在边界上稍微增加一点空白 (比如-1, +1)，让图更好看
plt.xlim(bmi_min - 1, bmi_max + 1)
plt.ylim(week_min - 1, week_max + 1)

plt.scatter(df_above_4[col_bmi], df_above_4[col_age],
            alpha=0.6, label='Y染色体浓度 ≥ 4%', marker='o', color='royalblue', s=50)

plt.scatter(df_below_4[col_bmi], df_below_4[col_age], alpha=0.8, marker='o', label='Y染色体浓度 < 4%', color='orange', s=25)
plt.title('孕妇BMI与孕周关系散点图', fontsize=16)
plt.xlabel('孕妇 BMI 指标', fontsize=12)
plt.ylabel('检测孕周 (周)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(title='图例', fontsize=10)
plt.savefig('BMI 与孕周散点图.pdf', bbox_inches='tight')