# 导入基础库
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from cycler import cycler

# 从 scikit-learn 中导入所需模块
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# -- 图片预设，需要 plt, fm, cycler 库
fm.fontManager.addfont('../../utils/fonts/SourceHanSerifCN-Regular.otf')  # 添加字体
font_name = fm.FontProperties(fname='../../utils/fonts/SourceHanSerifCN-Regular.otf').get_name()
plt.rcParams['font.sans-serif'] = [font_name]
plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'  # 保存后自动裁剪白边
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.prop_cycle'] = cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
plt.rcParams['axes.unicode_minus'] = False
# -- 图片预设

# 加载鸢尾花数据集
iris = load_iris()
X = pd.DataFrame(iris.data, columns=iris.feature_names)
y = pd.Series(iris.target, name='species')

# 打印数据概览
print("特征数据前5行:")
print(X.head())
print("\n目标数据概览:")
print(y.value_counts())

# 将数据划分为训练集和测试集
# random_state=42 确保每次划分结果一致，保证实验的可复现性
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

print(f"\n训练集大小: {X_train.shape} 样本")
print(f"测试集大小: {X_test.shape} 样本")

# -- 训练开始
# 1. 使用默认参数初始化随机森林分类器
# 可选，设置 random_state=42
rf_baseline = RandomForestClassifier(random_state=42)

# 2. 在训练数据上拟合模型
rf_baseline.fit(X_train, y_train)

print("基准随机森林模型训练完成。")
print(f"模型使用的树的数量 (n_estimators): {rf_baseline.n_estimators}")
print(f"模型使用的分裂准则 (criterion): {rf_baseline.criterion}")
# -- 训练结束

# -- 预测和评估开始
# 1. 使用训练好的基准模型对测试集进行预测
y_pred_baseline = rf_baseline.predict(X_test)

# 2. 计算并打印准确率
accuracy_baseline = accuracy_score(y_test, y_pred_baseline)
print(f"基准模型准确率: {accuracy_baseline:.4f}")

# 3. 打印详细的分类报告
print("\n基准模型分类报告:")
print(classification_report(y_test, y_pred_baseline, target_names=iris.target_names))

# 4. 生成并可视化混淆矩阵
cm_baseline = confusion_matrix(y_test, y_pred_baseline)

plt.figure(figsize=(8, 6))
sns.heatmap(cm_baseline, annot=True, fmt='d', cmap='Blues',
            xticklabels=iris.target_names, yticklabels=iris.target_names)
plt.title('基准模型混淆矩阵')
plt.ylabel('真实类别')
plt.xlabel('预测类别')
plt.show()
# -- 预测和评估结束

# -- 调优开始
from sklearn.model_selection import GridSearchCV

# 1. 定义要搜索的超参数网格
# 这个字典的键是超参数名称，值是待测试的候选列表
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 10, 20],
    'max_features': ['sqrt', 'log2', None],
    'min_samples_leaf': [1, 2, 4],
    'criterion': ['gini', 'entropy']
}

# 2. 初始化网格搜索模型
# estimator: 待调优的模型
# param_grid: 超参数网格
# cv=5: 使用5折交叉验证
# n_jobs=-1: 使用所有可用的CPU核心并行计算，加快搜索速度
# verbose=2: 打印详细的搜索过程信息
grid_search = GridSearchCV(estimator=RandomForestClassifier(random_state=42),
                           param_grid=param_grid,
                           cv=5,
                           n_jobs=-1,
                           verbose=2)

# 3. 在训练数据上执行网格搜索
print("开始进行超参数网格搜索...")
grid_search.fit(X_train, y_train)
print("网格搜索完成。")

# 4. 打印找到的最佳超参数组合
print(f"\n最佳超参数组合: {grid_search.best_params_}")

# 5. 使用最佳超参数的模型进行预测和评估
best_rf = grid_search.best_estimator_
y_pred_tuned = best_rf.predict(X_test)

# 评估调优后的模型
accuracy_tuned = accuracy_score(y_test, y_pred_tuned)
print(f"\n调优后模型准确率: {accuracy_tuned:.4f}")
print("\n调优后模型分类报告:")
print(classification_report(y_test, y_pred_tuned, target_names=iris.target_names))
# -- 调优结束

# -- 特征重要性分析开始
# 1. 从调优后的最佳模型中获取特征重要性
importances = best_rf.feature_importances_
feature_names = X.columns

# 2. 创建一个包含特征名称和其重要性分数的 Pandas Series
forest_importances = pd.Series(importances, index=feature_names).sort_values(ascending=False)

# 3. 绘制条形图进行可视化
plt.figure(figsize=(10, 6))
sns.barplot(x=forest_importances.values, y=forest_importances.index)
plt.title('基于平均不纯度减少的特征重要性')
plt.xlabel('重要性分数')
plt.ylabel('特征')
plt.tight_layout()
plt.show()

print("各特征的重要性分数:")
print(forest_importances)
# -- 特征重要性分析结束