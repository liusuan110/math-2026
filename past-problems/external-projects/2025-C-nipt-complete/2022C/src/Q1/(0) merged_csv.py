import pandas as pd
import numpy as np

def merge_csv_files(file1, file2, output_file):
    # Read the CSV files into DataFrames
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # Merge the DataFrames on the 'id' column
    merged_df = pd.merge(df1, df2, on='文物采样点', how='left')

    # Save the merged DataFrame to a new CSV file
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')


def main():
    merge_csv_files('../../sources/文物采样.csv', '../../sources/文物采样点类型.csv', '文物统计数据.csv')

if __name__ == "__main__":
    main()