import pandas as pd
import numpy as np
import os

NORMALIZATION_RULES = [
    {
        'column': '生师比',
        'type': 'interval',
        'params': {'x_min': 5, 'x_max': 6, 'x_tolerant_min': 2, 'x_tolerant_max': 12}
    },
    {
        'column': '逾期毕业率',
        'type': 'min',
        'params': {}
    },
    {
        'column': '科研经费',
        'type': 'max',
        'params': {}
    },
]


def max2max(datas) -> list:
    return datas


def min2max(datas: list, offset=1e-9) -> list:
    def normalization(data) -> float:
        return 1 / (data + offset)

    return list(map(normalization, datas))


# 最佳范围被认为是中点
def middle2max(datas, x_min, x_max):
    def normalization(data):
        if data <= x_min or data >= x_max:
            return 0
        elif data > x_min and data < (x_min + x_max) / 2:
            return 2 * (data - x_min) / (x_max - x_min)
        elif data < x_max and data >= (x_min + x_max) / 2:
            return 2 * (x_max - data) / (x_max - x_min)

    return list(map(normalization, datas))


def interval2max(datas, x_min, x_max, x_tolerant_min, x_tolerant_max):
    def normalization(data):
        if data >= x_min and data <= x_max:
            return 1
        elif data <= x_tolerant_min or data >= x_tolerant_max:
            return 0
        elif data > x_max and data < x_tolerant_max:
            return 1 - (data - x_max) / (x_tolerant_max - x_max)
        elif data < x_min and data > x_tolerant_min:
            return 1 - (x_min - data) / (x_min - x_tolerant_min)

    return list(map(normalization, datas))


def batch_normalize_from_rules(df, rules: list) -> pd.DataFrame:
    """读取规则列表，批量处理数据 DataFrame"""
    for rule in rules:
        column_name = rule['column']
        datas = df[column_name].tolist()

        type_to_func = {'max': max2max, 'min': min2max, 'middle': middle2max, 'interval': interval2max}
        func_to_call = type_to_func.get(rule['type'])

        normalized_values = func_to_call(datas, **rule['params'])
        df[column_name] = normalized_values

    return df


def normalization(df: pd.DataFrame) -> pd.DataFrame:
    return df / np.sqrt((df ** 2).sum())


def entropyWeight(df):
    """计算第 j 个指标下第 i 个样本所占的比重"""
    df = np.array(df)
    P = df / df.sum(axis=0)
    E = np.nansum(-P * np.log(P) / np.log(len(df)), axis=0)
    d = (1 - E)
    W = d / d.sum()
    return W


def topsis(data, weight):
    # 最优最劣方案（Z+ 和 Z-）
    Z = pd.DataFrame([data.max(), data.min()], index=['Z+', 'Z-'])
    weight = entropyWeight(data) if weight is None else np.array(weight)
    result = data.copy()
    result['Z+'] = np.sqrt(((data - Z.loc['Z+']) ** 2 * weight).sum(axis=1))  # 评价对象与最大值的距离
    result['Z-'] = np.sqrt(((data - Z.loc['Z-']) ** 2 * weight).sum(axis=1))
    result['综合得分指数'] = result['Z-'] / (result['Z-'] + result['Z+'])
    result['排序'] = result.rank(ascending=False)['综合得分指数']

    return result, Z, weight


# 人工赋权重的结果
weight = [0.2, 0.3, 0.4, 0.1]

if __name__ == "__main__":
    df = pd.read_csv("test.csv")
    df_normalize = batch_normalize_from_rules(df, NORMALIZATION_RULES)
    print(df_normalize.head())

    # 需要挑选出数字来进行归一化运算，这里需要补充一下表头列
    numeric_cols = df_normalize.select_dtypes(include=[np.number]).columns
    normal = normalization(df_normalize[numeric_cols])
    print(normal)

    result, Z, weight = topsis(normal, weight)
    print(Z)
    print(result)
