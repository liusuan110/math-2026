import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

sns.set_style('darkgrid')
fm.fontManager.addfont('../../../utils/fonts/SourceHanSerifCN-Regular.otf')  # 添加字体
font_name = fm.FontProperties(fname='../../../utils/fonts/SourceHanSerifCN-Regular.otf').get_name()
plt.rcParams['font.sans-serif'] = [font_name]
plt.rcParams['axes.unicode_minus'] = False


df = pd.read_csv('../../sources/男胎(修正).csv', encoding='utf8')
df_clean = df.dropna(subset=['Y染色体浓度', '孕妇BMI', '孕周', '孕妇代码', '检测抽血次数'])

formulas = {
    "模型1_当前": "Q('Y染色体浓度') ~ 孕周 + I(孕周**2) + Q('孕妇BMI') + Q('检测抽血次数')",
    "模型2_加BMI二次项": "Q('Y染色体浓度') ~ 孕周 + I(孕周**2) + Q('孕妇BMI') + I(Q('孕妇BMI')**2) + Q('检测抽血次数')",
    "模型3_加抽血次数二次项": "Q('Y染色体浓度') ~ 孕周 + I(孕周**2) + Q('孕妇BMI') + Q('检测抽血次数') + I(Q('检测抽血次数')**2)",
    "模型4_加BMI孕周交互项": "Q('Y染色体浓度') ~ 孕周 + I(孕周**2) + Q('孕妇BMI') * 孕周 + Q('检测抽血次数')"
}

results = []

for name, formula in formulas.items():
    model = smf.mixedlm(formula, df_clean, groups=df_clean["孕妇代码"])
    result = model.fit()
    llf = result.llf
    n = result.nobs
    k = len(result.fe_params) + result.cov_re.shape[0] + 1
    aic = 2 * k - 2 * llf
    bic = k * np.log(n) - 2 * llf
    results.append({
        "模型名称": name,
        "AIC": aic,
        "BIC": bic,
        "对数似然值": result.llf
    })


if results:
    results_df = pd.DataFrame(results)
    print(results_df.sort_values(by="AIC").to_string(index=False))