import pandas as pd
import numpy as np


def grey_relational_analysis(df, reference_col, comparison_cols, normalization_method='mean', rho=0.5):
    """
    执行灰色关联分析
    参数:
    df (pd.DataFrame): 包含所有数据的DataFrame.
    reference_col (str): 参考序列的列名.
    comparison_cols (list): 比较序列的列名列表.
    normalization_method (str): 数据初始化的方法，可选 'mean' (均值化), 'initial' (初值化), 'minmax' (区间值化).
    rho (float): 分辨系数, 默认为 0.5.

    返回:
    pd.DataFrame: 包含各因素关联度及其排序的DataFrame.
    """
    Y = df[reference_col]
    X = df[comparison_cols]
    all_series = pd.concat([Y, X], axis=1)

    if normalization_method == 'mean':
        data_norm = all_series / all_series.mean()
    elif normalization_method == 'initial':
        data_norm = all_series / all_series.iloc[0]
    elif normalization_method == 'minmax':
        data_norm = (all_series - all_series.min()) / (all_series.max() - all_series.min())

    # 计算参考序列与比较序列的差值绝对值
    y_norm = data_norm[reference_col]
    x_norm = data_norm[comparison_cols]

    diff_df = pd.DataFrame()
    for col in x_norm.columns:
        diff_df[col] = abs(y_norm - x_norm[col])

    # 计算关联系数
    m_max = diff_df.values.max()
    m_min = diff_df.values.min()
    gamma_df = (m_min + rho * m_max) / (diff_df + rho * m_max)

    # 计算关联度并排序
    gra_grade = gamma_df.mean().sort_values(ascending=False)
    gra_grade_df = pd.DataFrame(gra_grade, columns=['关联度'])

    return gra_grade_df


if __name__ == "__main__":
    df = pd.read_csv('movie_data.csv')
    reference_column = '票房(亿元)'
    comparison_columns = ['银幕数量', '观影人数(亿)', '票价(元)', '电影上线数量']

    print("\n均值化")
    result_mean = grey_relational_analysis(
        df,
        reference_col=reference_column,
        comparison_cols=comparison_columns,
        normalization_method='mean'
    )
    print(result_mean)

    print("\n初值化")
    result_initial = grey_relational_analysis(
        df,
        reference_col=reference_column,
        comparison_cols=comparison_columns,
        normalization_method='initial'
    )
    print(result_initial)

    print("\n区间值化")
    result_minmax = grey_relational_analysis(
        df,
        reference_col=reference_column,
        comparison_cols=comparison_columns,
        normalization_method='minmax'
    )
    print(result_minmax)
