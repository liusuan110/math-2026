import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc, roc_auc_score, \
    precision_recall_curve, f1_score
from sklearn.utils.class_weight import compute_class_weight
import warnings
import time

# 设置绘图风格和字体，以支持中文显示
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']  # 指定默认字体为黑体或微软雅黑
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

warnings.filterwarnings('ignore')


# 1. 数据加载与初步清洗
def load_and_clean_data(filepath):
    """
    加载数据，进行初步的列名清理和列删除。
    """
    # 尝试多种编码方式读取CSV文件
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
    df = None
    for encoding in encodings:
        try:
            df = pd.read_csv(filepath, encoding=encoding)
            print(f"成功使用 {encoding} 编码读取文件")
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        raise ValueError("无法使用任何编码读取文件，请检查文件格式")
    df.columns = df.columns.str.strip()
    df.drop(columns=['', 'Unnamed: 21', '序号', '孕妇代码', '末次月经', '检测日期'], inplace=True, errors='ignore')
    df['染色体的非整倍体'].fillna('正常', inplace=True)
    return df


# 2. 以患者为中心的样本重构 (核心优化)
def preprocess_patient_data(df):
    print("开始以患者为中心的样本重构...")
    df = df.copy()

    # 转换孕周为可排序的数值
    def parse_gestational_week_sortable(gw_str):
        if isinstance(gw_str, str) and 'w+' in gw_str:
            parts = gw_str.split('w+')
            return float(parts) * 7 + float(parts[1])
        elif isinstance(gw_str, str) and 'w' in gw_str:
            return float(gw_str.replace('w', '')) * 7
        return np.nan

    df['孕周_天数'] = df['检测孕周'].apply(parse_gestational_week_sortable)
    df = df.sort_values(by=['孕妇代码', '孕周_天数'])

    final_indices =
    processed_patients = set()

    for patient_id, group in df.groupby('孕妇代码'):
        if patient_id in processed_patients:
            continue

        abnormal_events = group[group['染色体的非整倍体'] != '正常']

        if not abnormal_events.empty:
            first_abnormal_event = abnormal_events.iloc
            first_abnormal_idx = first_abnormal_event.name

            # 保留首次异常记录
            final_indices.append(first_abnormal_idx)

            # 保留首次异常前的所有正常记录
            normal_before_abnormal = group.loc[:first_abnormal_idx].query("染色体的非整倍体 == '正常'")
            final_indices.extend(normal_before_abnormal.index.tolist())
        else:
            # 如果该孕妇始终正常，保留所有记录
            final_indices.extend(group.index.tolist())

        processed_patients.add(patient_id)

    df_final = df.loc[list(set(final_indices))].reset_index(drop=True)
    print(f"重构前样本数: {len(df)}, 重构后样本数: {len(df_final)}")
    return df_final

# 2. 特征工程
def feature_engineering(df):
    """
    对数据进行特征工程，包括孕周转换、分类变量编码等。
    """

    def parse_gestational_week(gw_str):
        if isinstance(gw_str, str) and 'w+' in gw_str:
            parts = gw_str.split('w+')
            if len(parts) == 2:
                return float(parts[0]) + float(parts[1]) / 7
            else:
                return float(parts[0])
        elif isinstance(gw_str, str) and 'w' in gw_str:
            return float(gw_str.replace('w', ''))
        return np.nan

    df['检测孕周_数值'] = df['检测孕周'].apply(parse_gestational_week)
    df['IVF妊娠_编码'] = df['IVF妊娠'].apply(lambda x: 1 if x == 'IVF（试管婴儿）' else 0)

    # 新增Z值交互特征
    z_cols = ['13号染色体的Z值', '18号染色体的Z值', '21号染色体的Z值', 'X染色体的Z值']
    df['Z_mean'] = df[z_cols].mean(axis=1)
    df['Z_std'] = df[z_cols].std(axis=1)
    df['Z_21_vs_18'] = df['21号染色体的Z值'] - df['18号染色体的Z值']
    df['Z_21_vs_13'] = df['21号染色体的Z值'] - df['13号染色体的Z值']
    df['Z_18_vs_13'] = df['18号染色体的Z值'] - df['13号染色体的Z值']

    
    aneuploidy_map = {
        'T13': 'T13', 'T18': 'T18', 'T21': 'T21',
        'T13T18': '其他异常', 'T18T21': '其他异常', 'T13T21': '其他异常',
        'T13T18T21': '其他异常'
    }
    df['目标类别'] = df['染色体的非整倍体'].apply(lambda x: aneuploidy_map.get(x, '正常'))

    le = LabelEncoder()
    df['目标类别_编码'] = le.fit_transform(df['目标类别'])

    print("目标类别编码映射:")
    for i, class_name in enumerate(le.classes_):
        print(f"{class_name}: {i}")

    return df, le


# 3. 探索性数据分析 (EDA)
def perform_eda(df, target_col):
    """
    执行探索性数据分析并生成可视化图表。
    """
    plt.figure(figsize=(10, 6))
    sns.countplot(x=target_col, data=df, order=df[target_col].value_counts().index)
    plt.title('目标变量类别分布', fontsize=16)
    plt.xlabel('类别', fontsize=12)
    plt.ylabel('样本数量', fontsize=12)
    plt.xticks(rotation=45)
    plt.show()

    z_scores = ['13号染色体的Z值', '18号染色体的Z值', '21号染色体的Z值']
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle('各类别下关键染色体Z值分布', fontsize=18)
    for i, z_score in enumerate(z_scores):
        sns.boxplot(x=target_col, y=z_score, data=df, ax=axes[i])
        axes[i].set_title(f'{z_score} 分布')
        axes[i].set_xlabel('类别')
        axes[i].set_ylabel('Z值')
        axes[i].tick_params(axis='x', rotation=45)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


# 4. 模型训练与评估
def train_and_evaluate_models(X_train, y_train, X_test, y_test, le):
    """
    训练和评估多个模型，包括堆叠模型。
    """
    # 定义基础模型
    base_models = {
        "加权逻辑回归": LogisticRegression(class_weight='balanced', solver='liblinear', random_state=42),
        "加权SVM": SVC(class_weight='balanced', probability=True, random_state=42),
        "随机森林": RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(objective='multi:softprob', use_label_encoder=False, eval_metric='mlogloss',
                                 random_state=42, n_jobs=-1),
        "LightGBM": LGBMClassifier(objective='multiclass', class_weight='balanced', random_state=42, n_jobs=-1),
        "CatBoost": CatBoostClassifier(loss_function='MultiClass', auto_class_weights='Balanced', random_state=42,
                                       verbose=0)
    }

    # 定义用于堆叠的基学习器
    estimators = [
        ('lr', LogisticRegression(class_weight='balanced', solver='liblinear', random_state=42)),
        ('svm', SVC(class_weight='balanced', probability=True, random_state=42)),
        ('rf', RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42, n_jobs=-1)),
        ('xgb', XGBClassifier(objective='multi:softprob', use_label_encoder=False, eval_metric='mlogloss',
                              random_state=42, n_jobs=-1)),
        ('lgbm', LGBMClassifier(objective='multiclass', class_weight='balanced', random_state=42, n_jobs=-1)),
        ('cat', CatBoostClassifier(loss_function='MultiClass', auto_class_weights='Balanced', random_state=42,
                                   verbose=0))
    ]

    # 定义堆叠模型
    stacking_model = StackingClassifier(
        estimators=estimators,
        final_estimator=LogisticRegression(class_weight='balanced', solver='liblinear', random_state=42),
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    )

    all_models = base_models.copy()
    all_models["堆叠模型"] = stacking_model

    results = {}
    performance_summary = []

    for name, model in all_models.items():
        print(f"--- 正在训练模型: {name} ---")
        start_time = time.time()

        if name in ["XGBoost", "堆叠模型"]:
            classes_weights = compute_class_weight(class_weight='balanced', classes=np.unique(y_train), y=y_train)
            sample_weights = np.array([classes_weights[label] for label in y_train])

            if name == "XGBoost":
                model.fit(X_train, y_train, sample_weight=sample_weights)
            else:  # Stacking model
                # StackingClassifier 不直接接受 sample_weight, 但其基模型和元模型已配置为处理不平衡
                model.fit(X_train, y_train)
        else:
            model.fit(X_train, y_train)

        training_time = time.time() - start_time
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)

        report = classification_report(y_test, y_pred, target_names=le.classes_, output_dict=True)
        macro_f1 = f1_score(y_test, y_pred, average='macro')
        roc_auc = roc_auc_score(y_test, y_prob, multi_class='ovr', average='macro')

        performance_summary.append({
            "模型": name,
            "宏平均精确率": report['macro avg']['precision'],
            "宏平均召回率": report['macro avg']['recall'],
            "宏平均F1分数": macro_f1,
            "ROC-AUC (宏平均)": roc_auc,
            "训练耗时(秒)": training_time
        })

        results[name] = {'model': model, 'y_pred': y_pred, 'y_prob': y_prob}

        print(f"训练耗时: {training_time:.2f} 秒")
        print(f"\n{name} 分类报告:")
        print(classification_report(y_test, y_pred, target_names=le.classes_))

        cm = confusion_matrix(y_test, y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=le.classes_, yticklabels=le.classes_)
        plt.title(f'{name} 混淆矩阵', fontsize=16)
        plt.xlabel('预测类别', fontsize=12)
        plt.ylabel('真实类别', fontsize=12)
        plt.show()

    return results, pd.DataFrame(performance_summary)


# 5. 绘制比较性ROC曲线
def plot_comparative_roc(results, y_test, le):
    """
    为所有模型绘制多分类ROC曲线。
    """
    plt.figure(figsize=(12, 10))

    for name, result in results.items():
        y_prob = result['y_prob']
        roc_auc = roc_auc_score(y_test, y_prob, multi_class='ovr', average='macro')

        fpr, tpr, _ = roc_curve(pd.get_dummies(y_test).values.ravel(), y_prob.ravel())
        plt.plot(fpr, tpr, label=f'{name} (Micro-AUC = {auc(fpr, tpr):.4f}, Macro-AUC = {roc_auc:.4f})')

    plt.plot([0, 1], [0, 1], 'k--', label='随机猜测')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('假正例率 (FPR)', fontsize=12)
    plt.ylabel('真正例率 (TPR)', fontsize=12)
    plt.title('模型ROC曲线比较', fontsize=16)
    plt.legend(loc="lower right")
    plt.grid(True)
    plt.show()


# 6. 最优模型深度分析
def analyze_best_model(model, model_name, features, X_test, y_test, le, class_to_analyze='T21'):
    """
    对最优模型进行特征重要性和敏感性分析。
    """
    print(f"\n--- 最优模型 ({model_name}) 深度分析 ---")

    # 特征重要性 (仅对有此属性的模型)
    # 如果最优模型是堆叠模型，我们分析其最重要的基学习器之一（例如XGBoost）
    model_to_analyze = model
    if isinstance(model, StackingClassifier):
        print("最优模型为堆叠模型，分析其基学习器XGBoost的特征重要性。")
        model_to_analyze = model.named_estimators_['xgb']

    if hasattr(model_to_analyze, 'feature_importances_'):
        importances = model_to_analyze.feature_importances_
        feature_importance_df = pd.DataFrame({'特征': features, '重要性': importances})
        feature_importance_df = feature_importance_df.sort_values(by='重要性', ascending=False).head(15)

        plt.figure(figsize=(12, 8))
        sns.barplot(x='重要性', y='特征', data=feature_importance_df)
        plt.title(f'特征重要性分析 (基于{type(model_to_analyze).__name__})', fontsize=16)
        plt.xlabel('重要性得分', fontsize=12)
        plt.ylabel('特征', fontsize=12)
        plt.show()

    # 敏感性分析：精确率-召回率曲线
    class_index = list(le.classes_).index(class_to_analyze)
    y_prob_class = model.predict_proba(X_test)[:, class_index]
    precision, recall, thresholds = precision_recall_curve(y_test == class_index, y_prob_class)

    plt.figure(figsize=(10, 7))
    plt.plot(recall, precision, marker='.', label=f'模型 ({class_to_analyze})')
    plt.xlabel('召回率 (Recall)', fontsize=12)
    plt.ylabel('精确率 (Precision)', fontsize=12)
    plt.title(f'精确率-召回率曲线 ({class_to_analyze})', fontsize=16)
    plt.legend()
    plt.grid(True)
    plt.show()

    # 寻找一个高召回率的阈值
    high_recall_threshold_indices = np.where(recall[:-1] >= 0.99)
    if len(high_recall_threshold_indices[0]) > 0:
        optimal_idx = high_recall_threshold_indices[0][0]
        optimal_threshold = thresholds[optimal_idx]
        print(f"为实现对 {class_to_analyze} 至少99%的召回率，建议阈值为: {optimal_threshold:.4f}")
    else:
        print(f"无法在测试集上为 {class_to_analyze} 达到99%的召回率。")


# --- 主执行流程 ---
if __name__ == '__main__':
    df = load_and_clean_data('../../sources/男女胎.csv')
    df, label_encoder = feature_engineering(df)

    perform_eda(df, '目标类别')

    features = ['检测孕周_数值', 'IVF妊娠_编码', '13号染色体的Z值', '18号染色体的Z值', '21号染色体的Z值']
    target = '目标类别_编码'

    df_model = df[features + [target]].dropna()

    X = df_model[features]
    y = df_model[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model_results, performance_df = train_and_evaluate_models(X_train_scaled, y_train, X_test_scaled, y_test,
                                                              label_encoder)

    print("\n--- 所有模型性能汇总 ---")
    performance_df_sorted = performance_df.sort_values(by='宏平均F1分数', ascending=False)
    print(performance_df_sorted.to_string())

    plot_comparative_roc(model_results, y_test, label_encoder)

    best_model_name = performance_df_sorted.iloc[0]['模型']
    best_model = model_results[best_model_name]['model']

    analyze_best_model(best_model, best_model_name, features, X_test_scaled, y_test, label_encoder,
                       class_to_analyze='T21')
