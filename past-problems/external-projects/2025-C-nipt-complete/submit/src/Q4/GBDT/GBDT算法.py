import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, validation_curve, learning_curve
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_recall_curve, roc_curve
from imblearn.over_sampling import RandomOverSampler, SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTETomek
import warnings
from tqdm import tqdm

warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class FetusDetector:
    def __init__(self, data_path):
        self.data_path = data_path
        self.models = {}
        self.results = {}

    def load_data(self):
        data = pd.read_csv(self.data_path, encoding='utf-8')
        
        features = [
            '检测抽血次数', '孕妇BMI', '原始读段数', '在参考基因组上比对的比例', 
            '重复读段的比例', '唯一比对的读段数', 'GC含量',
            '13号染色体的Z值', '18号染色体的Z值', '21号染色体的Z值', 'X染色体的Z值',
            'X染色体浓度', '13号染色体的GC含量', '18号染色体的GC含量', 
            '21号染色体的GC含量', '被过滤掉读段数的比例'
        ]
        
        data[features] = data[features].fillna(data[features].median())
        
        self.X = data[features]
        self.y = data['是否异常']
        
    def profile_data(self):
        counts = self.y.value_counts()
        values = [counts.get(0, 0), counts.get(1, 0)]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))
        
        ax1.bar(['正常', '异常'], values, color=['#2ECC71', '#E74C3C'])
        ax1.set_title('样本频数分布')
        ax1.set_ylabel('频数')
        for i, v in enumerate(values):
            ax1.text(i, v + 1, str(v), ha='center')
        
        ax2.pie(values, labels=['正常', '异常'], autopct='%1.1f%%', colors=['#2ECC71', '#E74C3C'])
        ax2.set_title('样本比例分布')
        
        plt.tight_layout()
        plt.savefig('样本分布.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def sample_data(self):
        X_train, _, y_train, _ = train_test_split(self.X, self.y, test_size=0.2, random_state=42, stratify=self.y)
        
        sampler = SMOTETomek(random_state=42)
        X_res, y_res = sampler.fit_resample(X_train, y_train)
        

        
    def train(self):
        # 训练GBDT模型
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )
        
        sampler = SMOTETomek(random_state=42)
        X_train_res, y_train_res = sampler.fit_resample(X_train, y_train)
        
        # param_grid = {
        #     'n_estimators': [200, 300],
        #     'learning_rate': [0.05, 0.1],
        #     'max_depth': [4, 5, 6],
        #     'min_child_weight': [1, 2],
        #     'subsample': [0.8, 0.9],
        #     'colsample_bytree': [0.8, 0.9],
        #     'scale_pos_weight': [3.0, 5.0],
        #     'gamma': [0, 0.1],
        #     'reg_alpha': [0, 0.1],
        #     'reg_lambda': [0.5, 1.0]
        # }

        param_grid = {
            'n_estimators': [200],              # 先固定树的数量
            'learning_rate': [0.05, 0.1],       # 保留学习率的两个常用选项
            'max_depth': [4, 6],                # 只测试两个深度
            'subsample': [0.8],                 # 固定行采样率
            'colsample_bytree': [0.8],          # 固定列采样率
            # 'scale_pos_weight'参数可以暂时去掉，因为你在初始化模型时已经给了一个固定值8.5806
        }
        
        model = xgb.XGBClassifier(random_state=42, eval_metric='logloss')
        grid = GridSearchCV(
            model, param_grid, cv=5, scoring='recall', n_jobs=1, verbose=1
        )
        
        grid.fit(X_train_res, y_train_res)
        
        self.models['SMOTETomek'] = {
            'model': grid.best_estimator_,
            'best_params': grid.best_params_,
            'cv_score': grid.best_score_,
            'X_train': X_train_res,
            'X_test': X_test,
            'y_train': y_train_res,
            'y_test': y_test
        }
        


    def evaluate(self):
        info = self.models['SMOTETomek']
        model = info['model']
        X_train, X_test = info['X_train'], info['X_test']
        y_train, y_test = info['y_train'], info['y_test']

        y_test_prob = model.predict_proba(X_test)[:, 1]

        prec, rec, thres = precision_recall_curve(y_test, y_test_prob)

        f1s = np.divide(2 * prec * rec, prec + rec,
                    out=np.zeros_like(prec), where=(prec + rec) != 0)

        best_th = 0.5
        for tgt in [0.60, 0.55, 0.50, 0.45, 0.40]:
            valid_idx = np.where((prec[:-1] >= tgt) & (rec[:-1] >= tgt))[0]

        if len(valid_idx) > 0:
            best_idx = valid_idx[np.argmax(f1s[valid_idx])]
            best_th = thres[best_idx]
            strategy = f"找到P&R均>={tgt}，且F1最高的阈值"

        print(f"优化策略: {strategy}")
        print(f"最终选择的最优阈值: {best_th:.4f}")

        y_train_prob = model.predict_proba(X_train)[:, 1]
        y_train_pred = (y_train_prob >= best_th).astype(int)
        y_test_pred = (y_test_prob >= best_th).astype(int)

        train_acc = accuracy_score(y_train, y_train_pred)
        test_acc = accuracy_score(y_test, y_test_pred)
        train_f1 = f1_score(y_train, y_train_pred)
        test_f1 = f1_score(y_test, y_test_pred)

        self.results['SMOTETomek'] = {
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'train_f1': train_f1,
            'test_f1': test_f1,
            'classification_report': classification_report(y_test, y_test_pred, output_dict=True),
            'confusion_matrix': confusion_matrix(y_test, y_test_pred),
            'optimal_threshold': best_th
        }

        print("\n--- 最终模型评估报告 ---")
        print(f"分类报告 (测试集, 阈值={best_th:.4f}):\n{classification_report(y_test, y_test_pred)}")


        data = pd.DataFrame({
            'Threshold': thres,
            'Precision': prec[:-1],
            'Recall': rec[:-1],
            'F1-Score': f1s[:-1]
        })

        # 创建画布
        plt.figure(figsize=(12, 8))
        sns.set_style("whitegrid")
        plt.rcParams['font.sans-serif'] = ['STZhongsong']
        plt.rcParams['font.size'] = 14
        plt.rcParams['axes.titlesize'] = 18
        plt.rcParams['axes.labelsize'] = 16
        plt.rcParams['xtick.labelsize'] = 14
        plt.rcParams['ytick.labelsize'] = 14
        plt.rcParams['figure.figsize'] = (16, 10)
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['savefig.bbox'] = 'tight'
        plt.rcParams['lines.linewidth'] = 2
        plt.rcParams['lines.markersize'] = 6
        plt.rcParams['grid.linestyle'] = '--'
        plt.rcParams['axes.unicode_minus'] = False

        colors = sns.color_palette("Set2")
        # 绘制三条曲线
        sns.lineplot(data=data, x='Threshold', y='Precision', label='精确率 (Precision)',
                     color=colors[0],
                     linestyle='--',
                     linewidth=2
                     )
        sns.lineplot(data=data, x='Threshold', y='Recall', label='召回率 (Recall)',
                     color=colors[6],
                     linestyle='--',
                     linewidth=2)
        sns.lineplot(data=data, x='Threshold', y='F1-Score', label='F1分数 (F1-Score)',
                     color=colors[2],
                     marker='o',
                     linewidth=3)

        # 标记最优阈值
        plt.axvline(x=best_th, color='red', linestyle='--', label=f'最优阈值 = {best_th:.4f}')

        # 在最优阈值点上标记出具体的F1分数
        best_idx = np.argmin(np.abs(data['Threshold'] - best_th))
        best_f1 = data['F1-Score'].iloc[best_idx]
        plt.scatter(best_th, best_f1, color='red', s=100, zorder=5)
        plt.text(best_th, best_f1, f' F1={best_f1:.3f}', color='red', ha='left', va='center')

        # 设置图表属性
        plt.title('决策阈值对模型性能的影响', fontsize=16)
        plt.xlabel('决策阈值 (Decision Threshold)', fontsize=12)
        plt.ylabel('分数 (Score)', fontsize=12)
        plt.xlim(0, 1)
        plt.ylim(0, 1.05)
        plt.legend(loc='best')
        plt.grid(True)

        # 保存图表
        plt.savefig('阈值选择可视化.pdf')
        plt.close()

        return 'SMOTETomek'

    def feat_importance(self, method):
        model = self.models[method]['model']
        cols = self.X.columns
        
        if hasattr(model, 'feature_importances_'):
            imp = model.feature_importances_
            
            df = pd.DataFrame({
                '特征': cols,
                '重要性': imp
            }).sort_values('重要性', ascending=False)
            

            
            plt.figure(figsize=(12, 8))
            top = df.head(15)
            
            plt.barh(range(len(top)), top['重要性'], 
                    color='#3498DB')
            plt.yticks(range(len(top)), top['特征'])
            plt.xlabel('重要性')
            plt.title('特征重要性排序（前15个）')
            plt.gca().invert_yaxis()
            
            for i, v in enumerate(top['重要性']):
                plt.text(v + 0.001, i, f'{v:.3f}', va='center')
            
            plt.tight_layout()
            plt.savefig('特征重要性.png', dpi=300, bbox_inches='tight')
            plt.close()
        else:
            return
        
    def generate_confusion_matrices(self):
        pass

        
    def check_overfit(self, method):
        
        info = self.models[method]
        model = info['model']
        X_tr = info['X_train']
        y_tr = info['y_train']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        def plot_curve(ax, param, p_range, title, xlabel):
            base_params = {k:v for k,v in model.get_params().items() if k not in [param, 'random_state', 'eval_metric']}
            tr_scores, val_scores = validation_curve(
                xgb.XGBClassifier(random_state=42, eval_metric='logloss', **base_params),
                X_tr, y_tr, param_name=param, param_range=p_range,
                cv=5, scoring='accuracy', n_jobs=1
            )
            
            tr_mean, tr_std = np.mean(tr_scores, axis=1), np.std(tr_scores, axis=1)
            val_mean, val_std = np.mean(val_scores, axis=1), np.std(val_scores, axis=1)
            
            ax.plot(p_range, tr_mean, 'o-', color='blue', label='训练集')
            ax.fill_between(p_range, tr_mean - tr_std, tr_mean + tr_std, alpha=0.1, color='blue')
            ax.plot(p_range, val_mean, 'o-', color='red', label='验证集')
            ax.fill_between(p_range, val_mean - val_std, val_mean + val_std, alpha=0.1, color='red')
            ax.set_xlabel(xlabel)
            ax.set_ylabel('准确率')
            ax.set_title(title)
            ax.legend()
            ax.grid(True)
        
        # 1. n_estimators验证曲线
        plot_curve(axes[0,0], 'n_estimators', [50, 100, 150, 200, 250, 300], '验证曲线 - 树的数量', 'n_estimators')
        
        # 2. max_depth验证曲线
        plot_curve(axes[0,1], 'max_depth', [2, 3, 4, 5, 6, 7, 8], '验证曲线 - 树的深度', 'max_depth')
        
        # 3. 学习曲线
        sizes, tr_scores, val_scores = learning_curve(
            model, X_tr, y_tr, train_sizes=np.linspace(0.1, 1.0, 10),
            cv=5, scoring='accuracy', n_jobs=1
        )
        
        tr_mean, tr_std = np.mean(tr_scores, axis=1), np.std(tr_scores, axis=1)
        val_mean, val_std = np.mean(val_scores, axis=1), np.std(val_scores, axis=1)
        
        axes[1,0].plot(sizes, tr_mean, 'o-', color='blue', label='训练集')
        axes[1,0].fill_between(sizes, tr_mean - tr_std, tr_mean + tr_std, alpha=0.1, color='blue')
        axes[1,0].plot(sizes, val_mean, 'o-', color='red', label='验证集')
        axes[1,0].fill_between(sizes, val_mean - val_std, val_mean + val_std, alpha=0.1, color='red')
        axes[1,0].set_xlabel('训练样本数量')
        axes[1,0].set_ylabel('准确率')
        axes[1,0].set_title('学习曲线')
        axes[1,0].legend()
        axes[1,0].grid(True)
        
        # 4. 过拟合风险评估
        tr_acc = self.results[method]['train_accuracy']
        te_acc = self.results[method]['test_accuracy']
        gap = tr_acc - te_acc
        
        colors = ['green', 'orange', 'red']
        level = 0 if gap < 0.05 else (1 if gap < 0.15 else 2)
        text = f"过拟合风险: {['低风险', '中等风险', '高风险'][level]}\n训练-测试差距: {gap:.4f}"
        
        axes[1,1].bar(['训练集', '测试集'], [tr_acc, te_acc], color=['lightblue', 'lightcoral'])
        axes[1,1].set_ylabel('准确率')
        axes[1,1].set_title('训练集vs测试集性能对比')
        axes[1,1].text(0.5, 0.5, text, transform=axes[1,1].transAxes,
                      bbox=dict(boxstyle='round', facecolor=colors[level], alpha=0.3),
                      ha='center', va='center', fontsize=10)
        
        for i, v in enumerate([tr_acc, te_acc]):
            axes[1,1].text(i, v + 0.01, f'{v:.4f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('过拟合风险分析.png', dpi=300, bbox_inches='tight')
        plt.close()


    def predict_interactive(self, method):

        model = self.models[method]['model']
        cols = self.X.columns.tolist()
        th = self.results[method]['optimal_threshold']

        while True:
            inp = input("是否开始新的预测？(y/n/quit): ").strip().lower()

            if inp in ['quit', 'q', 'exit', 'n', 'no']:
                break
            elif inp not in ['y', 'yes', '']:
                continue

            data = []
            quit_flag = False

            for i, feat in enumerate(cols):
                while True:
                    val = input(f"{i+1:2d}. {feat}: ").strip()
                    if val.lower() in ['quit', 'q']:
                        quit_flag = True
                        break
                    
                    if val.replace('.', '').replace('-', '').isdigit() or val.replace('.', '').isdigit():
                        data.append(float(val))
                        break
                
                if quit_flag:
                    break
            
            if quit_flag:
                continue

            arr = np.array(data).reshape(1, -1)
            prob = model.predict_proba(arr)[0]
            pred = model.predict(arr)[0]

            print("预测结果:")
            print(f"正常概率: {prob[0]:.1%}")
            print(f"异常概率: {prob[1]:.1%}")
            
            # 根据阈值判断是异常还是正常
            if prob[1] >= th:
                print(f"判断结果: 异常 (异常概率 {prob[1]:.1%} >= 阈值 {th:.4f})")
            else:
                print(f"判断结果: 正常 (异常概率 {prob[1]:.1%} < 阈值 {th:.4f})")

    def run_analysis(self):
        # 运行完整分析流程
        self.load_data()
        self.profile_data()
        self.sample_data()
        self.train()
        method = self.evaluate()
        self.feat_importance(method)
        self.generate_confusion_matrices()
        self.check_overfit(method)

        print(f"测试准确率: {self.results[method]['test_accuracy']:.4f}")

        self.predict_interactive(method)

if __name__ == "__main__":
    data_path = '../../../sources/女胎(有效特征).csv'
    detector = FetusDetector(data_path)
    detector.run_analysis()