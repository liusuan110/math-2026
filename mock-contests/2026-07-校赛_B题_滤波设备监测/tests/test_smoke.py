from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from filter_monitoring.config import ASSETS, BASE_COSTS, LIFETIME_THRESHOLD  # noqa: E402
from filter_monitoring.q3_optimization import PolicyOutcome, annualized_lifecycle_cost  # noqa: E402
from filter_monitoring.q4_sensitivity import build_price_grid  # noqa: E402


class SkeletonSmokeTest(unittest.TestCase):
    def test_problem_constants(self) -> None:
        self.assertEqual(len(ASSETS), 10)
        self.assertEqual(LIFETIME_THRESHOLD, 37.0)
        self.assertEqual(BASE_COSTS.purchase, 300.0)

    def test_annualized_cost_units(self) -> None:
        outcome = PolicyOutcome(lifetime_days=3650, medium_events=10, major_events=2)
        self.assertAlmostEqual(annualized_lifecycle_cost(outcome), 35.4)

    def test_price_grid_contains_baseline(self) -> None:
        grid = build_price_grid()
        baseline = grid[(grid["purchase_ratio"] == 1.0) & (grid["maintenance_ratio"] == 1.0)]
        self.assertEqual(len(grid), 25)
        self.assertEqual(len(baseline), 1)
        self.assertEqual(float(baseline.iloc[0]["major_cost"]), 12.0)


if __name__ == "__main__":
    unittest.main()

