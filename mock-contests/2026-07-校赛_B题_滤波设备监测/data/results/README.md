# 结果表

四问的可引用数值结果统一放在这里，文件名以 `q1_`、`q2_`、`q3_`、`q4_` 开头。论文不得手工抄写未经本目录结果文件验证的数字。

问题二主要结果：

- `q2_model_backtest.csv`：三个候选模型的 90/180/270 日时间留出；
- `q2_leave_one_asset_validation.csv`：留一设备并用前 120 日校准后的外推误差；
- `q2_state_parameters.csv`：分层退化状态参数及近似区间；
- `q2_fixed_schedule.csv`：现行维护间隔和大维护频率外推口径；
- `q2_lifetime_summary.csv`：每台设备寿命中位数、80%/95%区间和删失率；
- `q2_lifetime_sensitivity.csv`：维护后恢复线 35/37/39 的判据敏感性；
- `q2_structural_sensitivity.csv`、`q2_outlier_sensitivity.csv`：模型结构与残差异常点敏感性；
- `q2_forecast_paths.csv`、`q2_forecast_bands.csv`：日级点预测和月末预测带；
- `q2_key_findings.json`：论文引用的关键口径与数字。

问题三主要结果：

- `q3_policy_space.csv`：129 组候选周期/状态触发策略参数；
- `q3_maintenance_response.csv`、`q3_response_validation.csv`：分类维护响应与留一设备误差；
- `q3_q2_baseline_check.csv`：现行日历在问题二/三中的寿命衔接检查；
- `q3_policy_evaluation.csv`：点估计、筛选和正式复验摘要；
- `q3_optimal_policy_by_asset.csv`、`q3_current_vs_optimal.csv`：逐设备最优方案与成本节省；
- `q3_recommended_calendar.csv`：预测原点后三年建议日历；
- `q3_robustness.csv`：独立种子、维护损伤/效果和约束放宽情景；
- `q3_key_findings.json`：正式费用、节省率和统一方案。

问题四主要结果：

- `q4_policy_coefficients.csv`：经 2,000 路径复验的购置、中维护和大维护年化成本系数；
- `q4_price_grid.csv`、`q4_asset_selection.csv`：购置价与共同维护价 17×17 网格的全厂摘要和逐设备选择；
- `q4_split_maintenance_grid.csv`、`q4_split_asset_selection.csv`：中、大维护价格分别变化时的 16×16 网格结果；
- `q4_plan_catalog.csv`：价格区域图中 `P0`—`P19` 方案编号的完整设备策略映射；
- `q4_one_factor_sensitivity.csv`、`q4_switch_intervals.csv`：0.25—3.00 倍单因素扫描和包含基准点的连续稳定区间；
- `q4_robust_policy.csv`：共同价格网格上的逐设备与统一最小最大后悔方案；
- `q4_scenario_uncertainty.csv`：9 个代表场景中基准、重优化和鲁棒方案的均值及 10%/90% 分位数；
- `q4_key_findings.json`：问题四范围、稳定比例、边界、后悔值和限制条件的关键摘要。
