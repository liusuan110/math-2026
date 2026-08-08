import pandas as pd
import xgboost as xgb
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.font_manager as fm

fm.fontManager.addfont('../../utils/fonts/SourceHanSerifCN-Regular.otf')  # 添加字体
font_name = fm.FontProperties(fname='../../utils/fonts/SourceHanSerifCN-Regular.otf').get_name()
plt.rcParams['font.sans-serif'] = [font_name]
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def xgboost_classifier_template(X, y):
    # 检查y的数据类型，如果不是数字类型，则进行标签编码
    label_encoder = None
    if y.dtype == 'object':
        label_encoder = LabelEncoder()
        y_processed = label_encoder.fit_transform(y)

    else:        # print("标签编码对应关系:")
        # for i, class_name in enumerate(label_encoder.classes_):
        #     print(f"  '{class_name}'  ->  {i}")
        y_processed = y

    X_train, X_test, y_train, y_test = train_test_split(X, y_processed, test_size=0.25, stratify=y_processed)
    print(f"训练集大小: {X_train.shape[0]}条, 测试集大小: {X_test.shape[0]}条")

    model = xgb.XGBClassifier({
        'objective': 'multi:softmax',
        'use_label_encoder': False,
        'eval_metric': 'mlogloss',
        'n_estimators': 100,
        'max_depth': 3,
        'learning_rate': 0.1,
        # 'random_state':
    })
    model.fit(X_train, y_train)

    # --- 4. 进行预测与评估 ---
    y_pred = model.predict(X_test)

    # 如果进行了编码，需要将预测结果和真实结果都解码回原始标签
    if label_encoder:
        y_pred = label_encoder.inverse_transform(y_pred)
        y_test = label_encoder.inverse_transform(y_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n模型预测准确率: {accuracy * 100:.2f}%")
    print("\n详细分类报告:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # --- 5. 可视化特征重要性 ---
    importance_df = pd.DataFrame({
        '特征': iris.feature_names,
        '重要性': model.feature_importances_
    }).sort_values(by='重要性', ascending=True)  # 改为升序，方便barh绘图

    plt.figure(figsize=(10, 6))
    sns.set_color_codes("muted")
    sns.barplot(x="重要性", y="特征", data=importance_df,
                label="重要性", color="b")
    # plt.barh(['特征'], importance_df['重要性'])
    sns.despine(left=True, bottom=True)
    plt.xlabel('重要性分数')
    plt.ylabel('特征')
    plt.title('XGBoost 特征重要性分析')
    plt.tight_layout()
    plt.show()

    return model

if __name__ == "__main__":

    # 1. 加载你的示例数据
    iris = load_iris()
    # data=pd.read_csv('../随机森林/gaokao_top10000_scores.csv')
    # columns=data.columns

    # 2. 准备特征(X)和目标(y)
    X = iris.data
    y = iris.target
    # X = data[['总分', '语文', '数学', '英语', '理综']]
    # y = data['学校档次']
    xgboost_test = xgboost_classifier_template(X, y)

