import pandas as pd

input_excel_file = '../../sources/附件1.xlsx'
output_csv_file = '../../sources/附件1(2).csv'

df = pd.read_excel(input_excel_file, header=None,sheet_name=1)
df.ffill(inplace=True)
df.to_csv(output_csv_file, index=False, header=False, encoding='utf-8-sig')