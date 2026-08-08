import pandas as pd
import numpy as np


def _calculate_gra_grade(reference_series, comparison_df, normalization_method, rho):
    """内部辅助函数，用于计算一次灰色关联度"""
    all_series = pd.concat([reference_series, comparison_df], axis=1)

    if normalization_method == 'mean':
        data_norm = all_series / all_series.mean()
    elif normalization_method == 'initial':
        data_norm = all_series / all_series.iloc[0]
    elif normalization_method == 'minmax':
        data_norm = (all_series - all_series.min()) / (all_series.max() - all_series.min())

    # 计算差值序列
    ref_norm = data_norm.iloc[:, 0]
    comp_norm = data_norm.iloc[:, 1:]
    diff_df = abs(comp_norm.subtract(ref_norm, axis=0))

    # 计算关联系数
    m_max = diff_df.values.max()
    m_min = diff_df.values.min()
    gamma_df = (m_min + rho * m_max) / (diff_df + rho * m_max)

    # 计算关联度
    gra_grade = gamma_df.mean()
    return gra_grade


def grey_relational_analysis(df, cols, analysis_type='standard', reference_col=None, normalization_method='minmax', rho=0.5):
    """
    执行灰色关联分析，支持标准模式和综合关联度模式

    参数:
    df (pd.DataFrame): 包含所有数据的DataFrame.
    cols (list): 需要分析的所有列的列表.
    analysis_type (str): 分析模式, 'standard' 或 'comprehensive'.
    reference_col (str): 在 'standard' 模式下，必须指定参考序列的列名.
    normalization_method (str): 数据初始化的方法, 'mean', 'initial', 'minmax'.
    rho (float): 分辨系数, 默认为 0.5.

    返回:
    pd.DataFrame: 包含各因素关联度及其排序的DataFrame.
    """
    if analysis_type == 'standard':
        ref_series = df[reference_col]
        comp_cols = [c for c in cols if c != reference_col]
        comp_df = df[comp_cols]

        gra_grade = _calculate_gra_grade(ref_series, comp_df, normalization_method, rho)
        result_df = pd.DataFrame(gra_grade, columns=['关联度']).sort_values(by='关联度', ascending=False)
        return result_df

    elif analysis_type == 'comprehensive':
        factor_df = df[cols]

        # 1. 构建最优和最劣参考序列
        # 注意：因为银幕数量级远大于其他，直接取最大最小值会导致参考序列完全由银幕数决定。
        # 因此，在计算综合关联度前，通常需要先对所有因子进行归一化处理。
        # 我们在这里先对所有因子进行区间值化处理，再构建最优最劣序列。
        factor_norm_df = (factor_df - factor_df.min()) / (factor_df.max() - factor_df.min())

        y_max = factor_norm_df.max(axis=1)
        y_min = factor_norm_df.min(axis=1)

        # 2. 计算各因子与最优/最劣序列的关联度
        gra_grade_max = _calculate_gra_grade(y_max, factor_norm_df, normalization_method, rho)
        gra_grade_min = _calculate_gra_grade(y_min, factor_norm_df, normalization_method, rho)

        comprehensive_grade = 1 / ((1 + gra_grade_min / gra_grade_max) ** 2)
        result_df = pd.DataFrame(comprehensive_grade, columns=['综合关联度']).sort_values(by='综合关联度', ascending=False)
        return result_df


if __name__ == "__main__":
    df = pd.read_csv('movie_data.csv')
    all_columns = ['票房(亿元)', '银幕数量', '观影人数(亿)', '票价(元)', '电影上线数量']

    print("--- 分析模式一: 标准关联度 (各因素对'票房'的影响程度) ---")
    result_standard = grey_relational_analysis(
        df=df,
        cols=all_columns,
        analysis_type='standard',
        reference_col='票房(亿元)',
        normalization_method='minmax'  # 我们选择最稳妥的 'minmax' 归一化方法
    )
    print(result_standard)

    print("--- 分析模式二: 综合关联度 (各指标发展轨迹与'理想模式'的接近程度) ---")
    result_comprehensive = grey_relational_analysis(
        df=df,
        cols=all_columns,
        analysis_type='comprehensive',
        normalization_method='minmax'  # 综合模式内部强制使用了归一化，这里选择的方法会用于后续计算
    )
    print(result_comprehensive)
