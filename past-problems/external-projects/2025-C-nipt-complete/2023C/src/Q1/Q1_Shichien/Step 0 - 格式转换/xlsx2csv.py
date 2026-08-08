import pandas as pd

xlsx_file = '../../../../official/附件4.xlsx'
csv_file = '../../../../sources/附件4.csv'
df = pd.read_excel(xlsx_file, sheet_name="Sheet1")
df.to_csv(csv_file, index=False, encoding='utf-8')
