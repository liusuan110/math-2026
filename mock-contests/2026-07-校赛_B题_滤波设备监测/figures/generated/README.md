# 自动生成图形

仅存放可由代码重建的论文图。建议按 `q1_01_...png` 的方式编号，使正文、代码与图形一一对应。

问题二当前生成：

- `q2_01_backtest.png`：三个候选模型平均时间留出 RMSE；
- `q2_02_degradation_rates.png`：设备长期退化率及结构敏感区间；
- `q2_03_lifetime_forecast.png`：十台设备滚动年均预测带；
- `q2_04_lifetime_summary.png`：总寿命中位数与 80% 区间。

问题三当前生成：

- `q3_01_cost_frontier.png`：候选策略的平均寿命—全厂年均成本前沿；
- `q3_02_current_vs_optimal.png`：各设备现行/优选成本对比；
- `q3_03_recommended_calendar.png`：预测原点后三年推荐日历；
- `q3_04_savings_uncertainty.png`：节省率与 80% 仿真区间。

问题四当前生成：

- `q4_01_price_stability_map.png`：购置价与共同维护价变化时逐设备优选方案区域；
- `q4_02_q3_plan_regret.png`：问题三逐设备方案在共同价格网格上的后悔值及 1% 边界；
- `q4_03_split_maintenance_map.png`：中、大维护价格分别变化时的方案切换；
- `q4_04_one_factor_regret.png`：四类单因素价格下逐设备和统一方案的经济稳健性。

区域图中的 `P0`—`P19` 为紧凑方案编号，完整设备策略组合见 `data/results/q4_plan_catalog.csv`。
