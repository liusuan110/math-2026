import pandas as pd
import numpy as np
from cycler import cycler
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns

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

def main():
    df = pd.read_csv("PCA_data.csv")
    print(df.head())

    features = df.columns
    X = df[features].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    print("--- PCA 分析结果 ---")
    print(f"第一主成分解释的方差比例: {pca.explained_variance_ratio_[0]:.2%}")
    print(f"第二主成分解释的方差比例: {pca.explained_variance_ratio_[1]:.2%}")
    print(f"累计解释的方差比例: {np.sum(pca.explained_variance_ratio_):.2%}")

    pca_df = pd.DataFrame(data=X_pca, columns=['Principal Component 1', 'Principal Component 2'])

    sns.scatterplot(
        x='Principal Component 1',
        y='Principal Component 2',
        data=pca_df,
        s=80,  # 点的大小
        alpha=0.8  # 点的透明度
    )

    plt.title('128个样本的PCA降维结果', fontsize=16)
    plt.xlabel('PC1 - 整体尺寸', fontsize=12)
    plt.ylabel('PC2 - 体型胖瘦', fontsize=12)
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    main()