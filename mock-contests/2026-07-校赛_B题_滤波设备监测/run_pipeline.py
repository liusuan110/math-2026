#!/usr/bin/env python3
"""本题统一运行入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from filter_monitoring.io import audit_inputs  # noqa: E402
from filter_monitoring.q1_analysis import run_q1_formal, run_q1_scaffold  # noqa: E402
from filter_monitoring.q2_lifetime import run_q2_formal  # noqa: E402
from filter_monitoring.q3_optimization import run_q3_formal  # noqa: E402
from filter_monitoring.q4_sensitivity import run_q4_formal  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="2026 校赛 B 题运行入口")
    parser.add_argument("stage", choices=("audit", "q1-data", "q1", "q2", "q3", "q4"))
    args = parser.parse_args()

    if args.stage == "audit":
        report = audit_inputs()
        print(report[["input", "exists", "size_bytes"]].to_string(index=False))
        print("输入校验通过。")
        return 0

    if args.stage == "q1-data":
        outputs = run_q1_scaffold()
        print(f"日级面板：{len(outputs['daily_panel'])} 行")
        print(f"设备数：{outputs['data_quality']['asset'].nunique()}")
        print(f"维护汇总：{int(outputs['maintenance_summary']['events'].sum())} 条事件")
        print("问题一数据层已生成。")
        return 0

    if args.stage == "q1":
        outputs = run_q1_formal()
        diagnostics = outputs["model_diagnostics"].set_index("model")
        print(f"日级面板：{len(outputs['daily_panel'])} 行")
        print(f"设备指标：{len(outputs['device_metrics'])} 台")
        print(f"维护事件：{len(outputs['event_detail'])} 条")
        print(f"完整模型 R²：{diagnostics.loc['full', 'r_squared']:.4f}")
        print(f"论文图：{len(outputs['figures'])} 张")
        print("问题一正式分析结果已写入 data/results 和 figures/generated。")
        return 0

    if args.stage == "q2":
        outputs = run_q2_formal()
        lifetimes = outputs["lifetimes"]
        finite = lifetimes.dropna(subset=["median_total_lifetime_years"])
        print(f"回测组合：{len(outputs['backtest'])} 组")
        print(f"留一设备验证：{len(outputs['leave_one_asset'])} 台")
        print(f"寿命模拟：{outputs['key_findings']['simulation_paths']} 条路径/设备")
        if len(finite):
            print(
                "寿命中位数范围："
                f"{finite['median_total_lifetime_years'].min():.2f}—"
                f"{finite['median_total_lifetime_years'].max():.2f} 年"
            )
        print(f"论文图：{len(outputs['figures'])} 张")
        print("问题二正式结果已写入 data/results 和 figures/generated。")
        return 0

    if args.stage == "q3":
        outputs = run_q3_formal()
        comparison = outputs["comparison"]
        findings = outputs["key_findings"]
        print(f"候选策略：{findings['candidate_policies']} 组")
        print(f"正式复验：{findings['final_paths']} 条路径/设备—策略")
        print(
            "全厂年均成本："
            f"{findings['current_fleet_annual_cost']:.2f} -> "
            f"{findings['optimized_fleet_annual_cost']:.2f} 万元/年"
        )
        print(f"年均成本节省：{findings['fleet_savings_percent']:.2f}%")
        print(f"逐设备方案：{len(comparison)} 台")
        print(f"论文图：{len(outputs['figures'])} 张")
        print("问题三正式结果已写入 data/results 和 figures/generated。")
        return 0

    if args.stage == "q4":
        outputs = run_q4_formal()
        findings = outputs["key_findings"]
        print(f"问题三候选策略：{findings['point_policy_space']} 组")
        print(
            "共同价格二维网格："
            f"{findings['common_price_grid_scenarios']} 个场景"
        )
        print(
            "分拆维护价格网格："
            f"{findings['split_maintenance_grid_scenarios']} 个场景"
        )
        print(
            "问题三逐设备方案在共同价格网格内保持1%近优："
            f"{findings['q3_asset_plan_within_1pct_share_common_grid']:.1%}"
        )
        print(
            "全厂鲁棒统一策略："
            f"{findings['uniform_minimax_policy_id']}"
        )
        print(f"论文图：{len(outputs['figures'])} 张")
        print("问题四正式结果已写入 data/results 和 figures/generated。")
        return 0

    raise AssertionError(f"未处理的运行阶段：{args.stage}")


if __name__ == "__main__":
    raise SystemExit(main())
