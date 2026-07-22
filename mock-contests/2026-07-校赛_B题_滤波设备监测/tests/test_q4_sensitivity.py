from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from filter_monitoring.config import ASSETS  # noqa: E402
from filter_monitoring.q4_sensitivity import (  # noqa: E402
    build_price_grid,
    build_split_maintenance_grid,
    contiguous_interval_containing_one,
    evaluate_optimal_policy_grid,
    reprice_policy_coefficients,
)


def _toy_coefficients() -> pd.DataFrame:
    rows = []
    for asset in ASSETS:
        rows.extend(
            [
                {
                    "asset": asset,
                    "policy_id": "policy_a",
                    "policy_kind": "periodic",
                    "purchase_annuity_factor": 0.12,
                    "medium_annuity_factor": 0.10,
                    "major_annuity_factor": 0.10,
                    "mean_future_medium_events": 1.0,
                    "mean_future_major_events": 1.0,
                    "median_total_lifetime_years": 8.0,
                    "operational_feasible": True,
                },
                {
                    "asset": asset,
                    "policy_id": "policy_b",
                    "policy_kind": "periodic",
                    "purchase_annuity_factor": 0.08,
                    "medium_annuity_factor": 1.50,
                    "major_annuity_factor": 0.80,
                    "mean_future_medium_events": 5.0,
                    "mean_future_major_events": 2.0,
                    "median_total_lifetime_years": 12.0,
                    "operational_feasible": True,
                },
            ]
        )
    return pd.DataFrame(rows)


class Q4SensitivityTest(unittest.TestCase):
    def test_repricing_is_linear_and_keeps_physical_fields(self) -> None:
        coefficients = _toy_coefficients()
        repriced = reprice_policy_coefficients(coefficients, 300.0, 3.0, 12.0)
        policy_a = repriced.loc[repriced["policy_id"].eq("policy_a")].iloc[0]
        self.assertAlmostEqual(float(policy_a["mean_annual_cost"]), 37.5)
        self.assertEqual(float(policy_a["median_total_lifetime_years"]), 8.0)
        self.assertEqual(float(policy_a["mean_future_major_events"]), 1.0)

    def test_negative_price_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            reprice_policy_coefficients(_toy_coefficients(), -1.0, 3.0, 12.0)

    def test_grid_reoptimization_detects_purchase_driven_switch(self) -> None:
        coefficients = _toy_coefficients()
        grid = build_price_grid(
            purchase_ratios=(1.0, 1.4), maintenance_ratios=(1.0,)
        )
        baseline = {asset: "policy_a" for asset in ASSETS}
        result = evaluate_optimal_policy_grid(
            coefficients,
            grid,
            baseline,
            uniform_baseline_policy="policy_a",
        ).sort_values("purchase_ratio")
        self.assertTrue(bool(result.iloc[0]["q3_plan_exactly_selected"]))
        self.assertFalse(bool(result.iloc[1]["q3_plan_exactly_selected"]))
        self.assertEqual(result.iloc[1]["uniform_optimal_policy_id"], "policy_b")
        self.assertGreater(float(result.iloc[1]["q3_plan_regret_percent"]), 0.0)

    def test_contiguous_interval_must_contain_baseline(self) -> None:
        low, high = contiguous_interval_containing_one(
            [0.8, 0.9, 1.0, 1.1, 1.2],
            [False, True, True, True, False],
        )
        self.assertAlmostEqual(low, 0.9)
        self.assertAlmostEqual(high, 1.1)

    def test_split_grid_separates_medium_and_major_prices(self) -> None:
        grid = build_split_maintenance_grid(
            medium_ratios=(0.5, 1.0), major_ratios=(1.0, 2.0)
        )
        self.assertEqual(len(grid), 4)
        row = grid.loc[
            grid["medium_ratio"].eq(0.5) & grid["major_ratio"].eq(2.0)
        ].iloc[0]
        self.assertAlmostEqual(float(row["medium_cost"]), 1.5)
        self.assertAlmostEqual(float(row["major_cost"]), 24.0)


if __name__ == "__main__":
    unittest.main()
