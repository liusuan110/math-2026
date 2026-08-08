import pandas as pd

X_missing = pd.read_csv("文物统计数据.csv")
X_filled = X_missing.fillna(0.04)
X_filled.to_csv("填充后的文物统计数据.csv", index=False, encoding="utf-8")
