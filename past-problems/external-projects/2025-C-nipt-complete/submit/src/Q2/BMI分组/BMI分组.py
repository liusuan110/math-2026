import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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


def analyze_and_plot_quartiles(df, column_name, output_filename='bmi_quartiles_plot.png'):
    data_series = df[column_name].dropna()

    print(data_series.describe())

    q1 = data_series.quantile(0.25)
    q2 = data_series.quantile(0.50)
    q3 = data_series.quantile(0.75)

    plt.figure(figsize=(12, 7))
    sns.histplot(data_series, kde=True, bins=30)

    plt.axvline(q1, color='r', linestyle='--', label=f'第一四分位点 (25%): {q1:.2f}')
    plt.axvline(q2, color='g', linestyle='--', label=f'中位数 (50%): {q2:.2f}')
    plt.axvline(q3, color='b', linestyle='--', label=f'第三四分位点 (75%): {q3:.2f}')

    plt.title(f'"{column_name}" 的分布与四分位点')
    plt.xlabel(column_name)
    plt.ylabel('频数')
    plt.legend()
    plt.savefig(output_filename)
    plt.close()


if __name__ == '__main__':
    file_path = '../../../sources/男胎(修正).csv'
    main_df = pd.read_csv(file_path)
    analyze_and_plot_quartiles(main_df, column_name='孕妇BMI', output_filename='孕妇BMI的四分位点.pdf')
