# code/ · 可复用模型脚手架

赛时「改数据就能跑」的常用模型代码。每个文件都能直接运行看演示。

## 环境准备
```bash
# Windows
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python.exe code\evaluation\topsis.py   # 跑某个模块的演示

# macOS / Linux
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python code/evaluation/topsis.py
```
一键自检（依次跑通所有模块，报告 PASS/FAIL）：
```bash
.venv\Scripts\python.exe tools\verify_env.py     # Windows
.venv/bin/python tools/verify_env.py             # macOS/Linux
```

## 模块速查（按「题型 → 该用哪个」）

### 数据预处理（几乎每题第一步）
| 文件 | 方法 | 什么时候用 |
|------|------|-----------|
| `preprocessing/data_prep.py` | 缺失/异常/归一化/相关性 | 拿到附件先跑：缺失报告、填补、异常检测、相关性热图 |
| `notebooks/数据探索模板.ipynb` | 探索式分析 | 复制改路径即用：读数→看缺失→相关→分布→记发现 |

### 评价类（打分 / 排序）
| 文件 | 方法 | 什么时候用 |
|------|------|-----------|
| `evaluation/ahp.py` | AHP 层次分析 | 权重靠**主观打分**（两两比较），含一致性检验 |
| `evaluation/entropy_weight.py` | 熵权法 | 权重**客观**由数据离散度决定 |
| `evaluation/topsis.py` | TOPSIS | 有权重后给**方案打分排序**（评价类主力） |
| `evaluation/fuzzy_grey.py` | 模糊综合评价 + 灰色关联 | 优/良/中/差等级评定（模糊）；小样本关联度排序（灰色） |

### 优化类（约束下求最优）
| 文件 | 方法 | 什么时候用 |
|------|------|-----------|
| `optimization/linear_programming.py` | 线性/整数规划(scipy) | 约束与目标都线性，决策变量离散/连续 |
| `optimization/nonlinear_programming.py` | 非线性规划(scipy) | 目标或约束含非线性项；带多初值重启 |
| `optimization/heuristic.py` | 模拟退火/遗传/粒子群 | **大规模/非凸**，求解器搞不定时（B 题主力） |

### 预测类（由历史推未来）
| 文件 | 方法 | 什么时候用 |
|------|------|-----------|
| `prediction/regression.py` | 多元回归(statsmodels) | 可解释的影响分析与预测，带 R²/p 值 |
| `prediction/arima_forecast.py` | ARIMA | **长**时间序列(≥30点)预测，自动选阶 |
| `prediction/grey_model.py` | 灰色 GM(1,1) | **小样本**(4~10点)趋势预测，带精度检验 |
| `prediction/ml_models.py` | 随机森林 / XGBoost | C 题大数据、非线性预测/分类 + 特征重要性 |

### 机理 / 图论 / 模拟（A、B 题进阶）
| 文件 | 方法 | 什么时候用 |
|------|------|-----------|
| `mechanism/ode_models.py` | 微分方程(scipy/sympy) | A 题机理：SIR、Logistic、阻尼振动；**含参数拟合到数据** |
| `graph/graph_models.py` | 图论(networkx) | 最短路/最小生成树/最大流/TSP（路径调度） |
| `simulation/monte_carlo.py` | 蒙特卡洛 | 含不确定性：积分估计、不确定性传播、置信区间 |

### 聚类 / 通用工具
| 文件 | 方法 | 什么时候用 |
|------|------|-----------|
| `clustering/cluster_pca.py` | KMeans + 肘部法 + PCA | 样本分组、降维可视化 |
| `common/sensitivity.py` | 灵敏度分析 | 论文必有一节：单因素 OAT + 龙卷风图数据 |
| `common/plotting.py` | 论文级绘图模板 | 中文字体 + 统一风格 + 300dpi 导出 |

## 典型组合套路
- **数据分析题(C)**：`data_prep`（清洗）→ `cluster_pca`（分组/降维）→ `ml_models`/`regression`（建关系）→ `plotting`
- **评价题**：`data_prep` → `entropy_weight`/`ahp`（定权）→ `topsis`/`fuzzy_grey`（排序）→ `sensitivity`（稳健性）→ `plotting`
- **优化题(B)**：`linear_programming`/`nonlinear_programming`，规模大或非凸转 `heuristic` → `sensitivity`（改参数循环跑）
- **预测题**：数据少 `grey_model`，数据多 `arima_forecast`/`regression`/`ml_models`
- **机理题(A)**：`ode_models`（建方程+数值解+参数拟合）→ `sensitivity` → `monte_carlo`（含不确定性时）

> 这些是**起点模板**，比赛时按题意改目标函数/约束/数据即可。进阶模型参考 `docs/资源汇总.md`。
