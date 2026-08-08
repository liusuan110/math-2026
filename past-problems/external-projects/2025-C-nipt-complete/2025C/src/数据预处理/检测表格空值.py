import pandas as pd
import numpy as np


def find_empty_cells(file_path):
    df = pd.read_csv(file_path)
    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
    empty_rows, empty_cols = np.where(df.isnull())
    print(f"\n检测完成：共发现 {len(empty_rows)} 个空值：")

    locations = []
    for r, c in zip(empty_rows, empty_cols):
        row_number = r + 2
        column_name = df.columns[c]
        if column_name in ["染色体的非整倍体", "Unnamed: 20", "Unnamed: 21"]:
            continue
        locations.append({'行号': row_number, '列名': column_name})
        print(f"  - 第 {row_number} 行, 列名: '{column_name}'")


if __name__ == '__main__':
    csv_file_path = '../../sources/男胎(孕天).csv'
    find_empty_cells(csv_file_path)
