import os

# 基础路径
base_path = 'preprocessed_data/整理数据'

# 文件夹名称列表
folders = ['Q1', 'Q2', 'Q3']
subfolders = [str(year) for year in range(2023, 2031)]

# 创建文件夹
for folder in folders:
    for subfolder in subfolders:
        path = os.path.join(base_path, folder, subfolder)
        os.makedirs(path, exist_ok=True)
        print(f'文件夹已创建：{path}')