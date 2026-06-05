# code/ · 可复用模型脚手架

赛时「改数据就能跑」的常用模型代码。每个文件都能 `python 文件名.py` 直接看演示。

## 环境准备
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# 运行：.venv/bin/python code/evaluation/topsis.py
```

## 模块速查（按"题型→该用哪个"）

| 目录/文件 | 方法 | 什么时候用 |
|-----------|------|-----------|
| `evaluation/ahp.py` | AHP 层次分析 | 指标权重靠**主观打分**（两两比较），含一致性检验 |
| `evaluation/entropy_weight.py` | 熵权法 | 指标权重**客观**由数据离散度决定 |
| `evaluation/topsis.py` | TOPSIS | 已有权重后给**方案打分排序**（评价类题主力） |
| `optimization/linear_programming.py` | 线性/整数规划(scipy) | "约束下求最优"，决策变量离散/连续 |
| `optimization/nonlinear_programming.py` | 非线性规划(scipy) | 目标或约束含非线性项；带多初值重启 |
| `prediction/regression.py` | 多元回归(statsmodels) | 可解释的影响分析与预测，带 R²/p 值报告 |
| `prediction/arima_forecast.py` | ARIMA | **长**时间序列(≥30点)预测，自动选阶 |
| `prediction/grey_model.py` | 灰色 GM(1,1) | **小样本**(4~10点)趋势预测，带精度检验 |
| `clustering/cluster_pca.py` | KMeans + 肘部法 + PCA | 样本分组、降维可视化（C 题数据分析） |
| `common/plotting.py` | 论文级绘图模板 | 中文字体 + 统一风格 + 300dpi 导出 |

## 典型组合套路
- **评价题**：`entropy_weight`（定权）→ `topsis`（排序）→ `plotting`（出图）
- **优化题**：`linear_programming` 或 `nonlinear_programming` → 灵敏度分析（改参数循环跑）
- **预测题**：数据少用 `grey_model`，数据多用 `arima_forecast` / `regression`
- **数据分析题**：`cluster_pca`（分组/降维）→ `regression`（建关系）→ `plotting`

> 这些是**起点模板**，比赛时按题意改目标函数/约束/数据即可。进阶模型参考 `docs/资源汇总.md` 里的 Datawhale 教程。
