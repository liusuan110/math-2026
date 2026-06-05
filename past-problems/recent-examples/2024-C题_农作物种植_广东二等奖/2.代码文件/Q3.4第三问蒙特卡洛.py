import random
import pandas as pd
import numpy as np
bean_index_list = [1, 2, 3, 4, 5, 17, 18, 19]
shuidao_index = 16
shuijiaodi_index = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8']
LH_index = ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12', 'E13', 'E14', 'E15', 'E16', 'F1', 'F2', 'F3', 'F4']
max_iter=10000
random.seed(8)
np.random.seed(8)

for year in range(2024, 2031):
    # 得到没有种植豆类年数
    year_ans = pd.read_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年答案表.csv", encoding='gbk')
    last_year_ans = pd.read_csv(f"preprocessed_data/整理数据/Q3/{year-1}/{year-1}年答案表.csv", encoding='gbk')
    year_ans.iloc[:, 1:42] = 0
    for index, row in year_ans.iterrows():
        # 获取对应的 last_year_ans 行
        last_year_row = last_year_ans[
            (last_year_ans['地块名'] == row['地块名']) & (last_year_ans['季度'] == row['季度'])]
        if not last_year_row.empty:
            last_year_row = last_year_row.iloc[0]
            non_bean_columns = [col for col in range(1, 42) if col not in bean_index_list]
            if (last_year_row[non_bean_columns] == 0).all():
                year_ans.at[index, '没有种植豆类年数'] = 0
            else:
                year_ans.at[index, '没有种植豆类年数'] = last_year_row['没有种植豆类年数'] + 1


    year_ans.to_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年答案表.csv", encoding='gbk', index=False)
    max_profit=0
    pass_num=0

    def generate():
        random.seed(8)
        x = np.zeros((82,41))
        #遍历前25行
        for i in range(0,26):
            # 随机选择第2到第16列中的一个列索引
            if year_ans.iloc[i,45]>=2:
                col_index=np.random.randint(1, 6)
            else:
                col_index = np.random.randint(1, 16)
            # 将year_ans第i行的'地块面积/亩'的数值赋值给x的相应位置
            x[i, col_index-1] = year_ans.iloc[i,44]
        for i in range(26, 34):
            if year_ans.iloc[i,45]>=2:
                col_index=np.random.randint(17, 20)
            else:
                col_index = np.random.randint(16, 35)
            x[i, col_index-1] = year_ans.iloc[i,44]
        for i in range(34, 54):
            if year_ans.iloc[i,45]>=2:
                col_index=np.random.randint(17, 20)
                x[i, col_index - 1] = year_ans.iloc[i, 44]
            else:
                col_indices = np.random.choice(range(17, 35), 2, replace=False)
                if np.random.rand() > 0.5:
                    # 第一种情况：两个列索引的值都为0.5 * year_ans[i]['地块面积/亩']
                    x[i, col_indices[0]-1] = 0.5 * year_ans.iloc[i,44]
                    x[i, col_indices[1]-1] = 0.5 * year_ans.iloc[i,44]
                else:
                    # 第二种情况：一个列索引为year_ans[i]['地块面积/亩']，另一个为0
                    x[i, col_indices[0]-1] = year_ans.iloc[i,44]
                    x[i, col_indices[1]-1] = 0
        for i in range(54, 62):
            if x[i - 28, 16] != 0:
                x[i, :] = 0
            else:
                col_index = np.random.randint(35, 38)
                x[i, col_index-1] = year_ans.iloc[i,44]
        for i in range(62, 78):
            col_indices = np.random.choice(range(38, 42), 2, replace=False)
            if np.random.rand() > 0.5:
                # 第一种情况：两个列索引的值都为0.5 * year_ans[i]['地块面积/亩']
                x[i, col_indices[0]-1] = 0.5 * year_ans.iloc[i,44]
                x[i, col_indices[1]-1] = 0.5 * year_ans.iloc[i,44]
            else:
                # 第二种情况：一个列索引为year_ans[i]['地块面积/亩']，另一个为0
                x[i, col_indices[0]-1] = year_ans.iloc[i,44]
                x[i, col_indices[1]-1] = 0
        for i in range(78, 82):
            col_indices = np.random.choice(range(20, 35), 2, replace=False)
            if np.random.rand() > 0.5:
                # 第一种情况：两个列索引的值都为0.5 * year_ans[i]['地块面积/亩']
                x[i, col_indices[0]-1] = 0.5 * year_ans.iloc[i,44]
                x[i, col_indices[1]-1] = 0.5 * year_ans.iloc[i,44]
            else:
                # 第二种情况：一个列索引为year_ans[i]['地块面积/亩']，另一个为0
                x[i, col_indices[0]-1] = year_ans.iloc[i,44]
                x[i, col_indices[1]-1] = 0
        return x
    def evaluate(x):
        if (constraint4(x)):
            return True
        else:
            return False

    def objective(x):
        # 将 x 重新整形为二维数组
        random.seed(42)
        x = x.reshape((year_ans.shape[0], 41))
        xiaoliang = pd.read_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年_销量表.csv", encoding='gbk').iloc[:,
                    1:].values
        danjia = pd.read_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年_单价表.csv", encoding='gbk').values
        chengben = pd.read_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年_成本表.csv", encoding='gbk').iloc[:,
                   1:42].values
        chanliang=pd.read_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年_产量表.csv", encoding='gbk').iloc[:,1:42].values
        # 确保 danjia 和 chengben 中的所有数据都是数值型
        danjia = danjia.astype(float)
        chengben = chengben.astype(float)
        mu_x=x.copy()
        # x=x*chanliang
        result = np.zeros((82, 41))
        # 遍历每一行
        for i in range(0,54):
            # 获取 "没有种植豆类年数" 属性
            no_bean_years = year_ans.iloc[i]['没有种植豆类年数']
            row_result = x[i] * chanliang[i]
            if no_bean_years == 0:
                row_result *= 1.25
            # 存储结果
            result[i] = row_result
        for i in range(54,82):
            row_result = x[i] * chanliang[i]
            if (year_ans.iloc[i - 28, bean_index_list] != 0).any():
                row_result *= 1.25
            result[i] = row_result
        x=result
        # 计算 x 的列和
        x_sum_1 = np.sum(x[0:54, :], axis=0)
        x_sum_2 = np.sum(x[54:, :], axis=0)


        # 对每一列进行 min 操作并计算销售金额
        x_min_1 = np.minimum(x_sum_1, xiaoliang[0, :])
        x_min_2 = np.minimum(x_sum_2, xiaoliang[1, :])

        xiaoshou_jine = np.sum(x_min_1 * danjia[0, :]) + np.sum(x_min_2 * danjia[1, :])

        # 计算成本
        chengben_jine = np.multiply(mu_x, chengben)
        # 计算利润
        profit = xiaoshou_jine - np.sum(chengben_jine)
        # 返回负利润以进行最小化
        return profit

    def constraint4(x):
        x = x.reshape((year_ans.shape[0], 41))
        constraints = []
        yijidu_list = [i for i in range(26, 54)]
        for i in yijidu_list:
            for j in range(1, 42):
                aij = float(last_year_ans.iloc[i + 28, j])

                bij = float(year_ans.iloc[i + 28, j])
                if ((x[i, j - 1] * (aij + bij)) != 0):
                    return False
        return True

    # if year==2024:
    for j in range(1,11):
        profit=0
        pass_num_1=0
        for i in range(1000):
            x = generate()
            if (evaluate(x)):
                pass_num = pass_num + 1
                pass_num_1=pass_num_1+1
                new_profit = objective(x)
                if new_profit > max_profit:
                    print(year, ":", "new_profit", new_profit)
                    pd.DataFrame(x).to_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年解.csv", encoding='gbk',
                                               index=False)
                    max_profit = new_profit
                if new_profit>profit:
                    profit=new_profit
                    pd.DataFrame(x).to_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}_{j}年解.csv", encoding='gbk',
                                               index=False)
        with open(f"preprocessed_data/整理数据/Q3/{year}/{year}_{j}年利润.txt", 'w', encoding='utf-8') as file:
                file.write(str(profit))
                file.write('\n')
                file.write(str(pass_num_1))



    # else:
    #     for i in range(max_iter):
    #         x=generate()
    #         if(evaluate(x)):
    #             pass_num=pass_num+1
    #             new_profit=objective(x)
    #             if new_profit>max_profit:
    #                 print(year,":","new_profit",new_profit)
    #                 pd.DataFrame(x).to_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年解.csv",encoding='gbk',index=False)
    #                 max_profit=new_profit


    with open(f"preprocessed_data/整理数据/Q3/{year}/{year}年利润.txt", 'w', encoding='utf-8') as file:
        file.write(str(max_profit))
        file.write('\n')
        file.write(str(pass_num))
    jie=pd.read_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年解.csv",encoding='gbk')
    ans=pd.read_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年答案表.csv",encoding='gbk')
    # 打印形状以进行调试
    ans.iloc[:, 1:42] = jie.values
    ans.to_csv(f"preprocessed_data/整理数据/Q3/{year}/{year}年答案表.csv",encoding='gbk',index=False)












