import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score


# ==============================================================================
# Part 1: 支持向量机分类 (SVC) 模板
# ==============================================================================
def svm_classifier_template(X, y):
    """
    一个通用的SVM分类器模板函数，包含网格搜索调优。
    """
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    param_grid = {
        'C': [0.1, 1, 10, 100],
        'gamma': [1, 0.1, 0.01, 0.001],
        'kernel': ['rbf']
    }
    grid_search = GridSearchCV(SVC(probability=True), param_grid, refit=True, verbose=2, cv=3)  # cv=3 for faster search
    print("开始使用网格搜索训练和调优SVM分类器...")
    grid_search.fit(X_train_scaled, y_train)
    print(f"\n找到的最佳参数: {grid_search.best_params_}")
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test_scaled)
    print("\n模型在测试集上的表现:")
    print(f"准确率 (Accuracy): {accuracy_score(y_test, y_pred):.4f}")
    print("分类报告 (Classification Report):")
    print(classification_report(y_test, y_pred))
    return best_model, scaler

# ==============================================================================
# Part 2: 主程序入口，用于测试gaokao_top10000_scores.csv
# ==============================================================================
if __name__ == "__main__":
    csv_file = '../随机森林/gaokao_top10000_scores.csv'
    df = pd.read_csv(csv_file)
    print("数据前5行预览:")
    print(df.head())
    # 2. 准备特征(X)和目标(y)
    # 我们使用分数作为特征来预测学校档次
    features = ['总分', '语文', '数学', '英语', '理综']
    target = '学校档次'

    X = df[features]
    y = df[target]

    print("\n特征 (X) 的维度:", X.shape)
    print("目标 (y) 的类别:", y.unique())

    # 其实sklearn有自带SVM算法可以使用，但是我们自己指定的C=10的这个经验值不一定是最优的，
    # 所以使用网格搜索是最精确的方法，但是速度会慢一点
    print("\n\n--- 现在运行包含网格搜索调优的完整模板 ---")
    svm_classifier_template(X, y)

