import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns
import matplotlib.font_manager as fm

fm.fontManager.addfont('../../utils/fonts/SourceHanSerifCN-Regular.otf')  # 添加字体
font_name = fm.FontProperties(fname='../../utils/fonts/SourceHanSerifCN-Regular.otf').get_name()
plt.rcParams['font.sans-serif'] = [font_name]
plt.rcParams['axes.unicode_minus'] = False


def logistic_regression_demo(X,y):
    """
    一个展示逻辑回归完整流程的函数，包括数据生成、训练、评估和可视化。
    """



    # ==================== 2. 划分训练集和测试集 ====================
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # ==================== 4. 在测试集上进行预测与评估 ====================
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"模型在测试集上的准确率: {accuracy * 100:.2f}%")

    print("\n详细分类报告:")
    print(classification_report(y_test, y_pred))

    # 绘制混淆矩阵，更直观地看分类结果
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['预测为0', '预测为1'], yticklabels=['实际为0', '实际为1'])
    plt.title('混淆矩阵')
    plt.ylabel('实际类别')
    plt.xlabel('预测类别')
    plt.show()

    # ==================== 5. 结果可视化：绘制决策边界 ====================
    print("\n--- 5. 正在生成决策边界可视化图... ---")
    plt.figure(figsize=(10, 7))

    # 绘制训练集的数据点
    plt.scatter(X_train[:, 0], X_train[:, 1], c=y_train, cmap=plt.cm.RdYlBu,
                edgecolor='k', marker='o', s=80, label='训练数据')
    # 绘制测试集的数据点 (用不同的标记)
    plt.scatter(X_test[:, 0], X_test[:, 1], c=y_test, cmap=plt.cm.RdYlBu,
                edgecolor='k', marker='x', s=100, linewidth=1.5, label='测试数据')

    # 创建一个网格来绘制决策边界
    ax = plt.gca()
    x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
    y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.02),
                         np.arange(y_min, y_max, 0.02))

    # 使用模型对网格上每个点进行预测
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    # 绘制决策边界和两个类别的区域
    # contourf 会用颜色填充两个区域
    plt.contourf(xx, yy, Z, cmap=plt.cm.RdYlBu, alpha=0.3)

    # 还可以用contour画出那条分界线
    plt.contour(xx, yy, Z, colors='k', linewidths=0.5)

    plt.title('逻辑回归决策边界可视化', fontsize=16)
    plt.xlabel('特征 1', fontsize=12)
    plt.ylabel('特征 2', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(
        'logistic_regression_decision.pdf',format='pdf'
    )
    plt.show()



if __name__ == '__main__':
    # ==================== 1. 生成一个用于二分类的合成数据集 ====================
    # 我们创建200个样本，2个特征，这样方便在二维平面上可视化
    # n_informative=2 表示2个特征都有用
    # n_clusters_per_class=1 表示每个类别的数据点都聚集在一起，使问题线性可分
    X, y = make_classification(n_samples=200, n_features=2, n_redundant=0,
                               n_informative=2,
                               # random_state=42,
                               n_clusters_per_class=1)
    logistic_regression_demo(X,y)