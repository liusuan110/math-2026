from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from filter_monitoring.q3_optimization import (  # noqa: E402
    PolicySpec,
    _select_with_tie_break,
    build_periodic_policy_frame,
    build_policy_space,
    estimate_maintenance_response,
    joint_failure_index,
    maintenance_damage_correction,
)


class Q3OptimizationTest(unittest.TestCase):
    def test_response_shrinkage_reduces_sparse_major_extreme(self) -> None:
        effects = pd.DataFrame(
            {
                "maintenance_type": ["medium", "major"],
                "recorded_events": [100, 10],
                "instant_mean": [16.0, 8.0],
                "instant_ci95_low": [14.0, 4.0],
                "instant_ci95_high": [18.0, 12.0],
                "retained_mean": [12.0, 4.0],
                "retained_ci95_low": [10.0, 1.0],
                "retained_ci95_high": [14.0, 7.0],
            }
        )
        response = estimate_maintenance_response(effects, prior_events=20.0).set_index(
            "maintenance_type"
        )
        empirical = float(response.loc["major", "retained_empirical"])
        shrunk = float(response.loc["major", "retained_shrunk"])
        pooled = float(response.loc["major", "pooled_retained"])
        self.assertGreater(shrunk, empirical)
        self.assertLess(shrunk, pooled)

    def test_periodic_calendar_respects_major_cap_and_override(self) -> None:
        maintenance = pd.DataFrame(
            {
                "asset": ["A1", "A1"],
                "maintenance_date": pd.to_datetime(["2025-12-01", "2026-03-01"]),
                "maintenance_type": ["major", "medium"],
            }
        )
        spec = PolicySpec(
            policy_id="test",
            policy_kind="periodic",
            medium_interval_days=60,
            major_interval_days=183,
            cooldown_days=30,
        )
        frame = build_periodic_policy_frame(
            spec,
            "A1",
            pd.Timestamp("2026-04-01"),
            pd.Timestamp("2027-04-01"),
            pd.Timestamp("2024-04-01"),
            maintenance,
        )
        events = frame.loc[frame["maintenance_type"].notna()].copy()
        self.assertGreater(len(events), 0)
        self.assertTrue((events["date"].diff().dropna().dt.days >= 30).all())
        majors = events.loc[events["maintenance_type"].eq("major"), "date"]
        self.assertTrue((majors.diff().dropna().dt.days <= 183).all())
        self.assertFalse(events.duplicated("date").any())

    def test_joint_failure_needs_post_crossing_major(self) -> None:
        prediction = np.full(500, 30.0)
        rolling = np.full(500, 30.0)
        no_major = np.full(500, None, dtype=object)
        crossing, failure = joint_failure_index(prediction, rolling, no_major)
        self.assertEqual(crossing, 0)
        self.assertIsNone(failure)

        with_major = no_major.copy()
        with_major[100] = "major"
        _, failure = joint_failure_index(prediction, rolling, with_major)
        self.assertEqual(failure, 130)

    def test_damage_correction_rewards_fewer_harmful_actions(self) -> None:
        dates = pd.date_range("2026-04-02", periods=365)
        frame = pd.DataFrame(
            {
                "date": dates,
                "maintenance_type": [None] * len(dates),
            }
        )
        correction = maintenance_damage_correction(
            frame,
            degradation_per_year=12.0,
            medium_rate_per_year=6.0,
            major_rate_per_year=1.0,
            forecast_origin=pd.Timestamp("2026-04-01"),
            damage_share=0.15,
        )
        self.assertGreater(float(correction[-1]), 0.0)
        zero = maintenance_damage_correction(
            frame,
            degradation_per_year=12.0,
            medium_rate_per_year=6.0,
            major_rate_per_year=1.0,
            forecast_origin=pd.Timestamp("2026-04-01"),
            damage_share=0.0,
        )
        np.testing.assert_allclose(zero, 0.0)

    def test_policy_space_respects_one_to_four_major_per_year(self) -> None:
        specs = [spec for spec in build_policy_space() if spec.policy_kind != "current"]
        self.assertGreater(len(specs), 20)
        for spec in specs:
            frequency = 365.25 / float(spec.major_interval_days)
            self.assertGreaterEqual(frequency, 1.0)
            self.assertLessEqual(frequency, 4.02)

    def test_selection_keeps_true_cost_minimum(self) -> None:
        evaluations = pd.DataFrame(
            {
                "policy_id": ["cheap", "few_events"],
                "mean_annual_cost": [50.0, 50.2],
                "mean_future_medium_events": [10.0, 5.0],
                "mean_future_major_events": [2.0, 1.0],
                "median_total_lifetime_years": [10.0, 9.0],
            }
        )
        selected = _select_with_tie_break(evaluations)
        self.assertEqual(selected["policy_id"], "cheap")


if __name__ == "__main__":
    unittest.main()
