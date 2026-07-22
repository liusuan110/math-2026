from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from filter_monitoring.config import ASSETS  # noqa: E402
from filter_monitoring.q1_analysis import prepare_analysis_panel  # noqa: E402
from filter_monitoring.q2_lifetime import (  # noqa: E402
    build_future_frame,
    estimate_fixed_schedule,
    fit_hierarchical_state_model,
    joint_failure_dates,
)


def synthetic_q2_panel() -> pd.DataFrame:
    rng = np.random.default_rng(11)
    dates = pd.date_range("2024-01-01", periods=500, freq="D")
    rows = []
    for asset_index, asset in enumerate(ASSETS):
        last_event = None
        for day, date in enumerate(dates):
            event = None
            if day > 0 and day % 60 == 0:
                event = "major" if day % 240 == 0 else "medium"
                last_event = day
            since = day - last_event if last_event is not None else np.nan
            pollution = 0.0 if np.isnan(since) else 0.20 * min(since, 90)
            performance = (
                105.0
                + asset_index
                - 0.025 * day
                + 8.0 * np.sin(2.0 * np.pi * (day + 1) / 365.25)
                - pollution
                + rng.normal(0.0, 0.4)
            )
            rows.append(
                {
                    "asset": asset,
                    "date": date,
                    "performance_model": performance,
                    "performance_median": performance,
                    "valid_rows": 24,
                    "was_imputed": False,
                    "days_since_maintenance": since,
                    "maintenance_type": event,
                }
            )
    return pd.DataFrame(rows)


class Q2LifetimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_panel = synthetic_q2_panel()
        cls.panel = prepare_analysis_panel(cls.raw_panel)

    def test_hierarchical_degradation_is_nonnegative(self) -> None:
        model = fit_hierarchical_state_model(self.panel)
        self.assertGreater(model.r_squared, 0.8)
        self.assertEqual(model.nobs, len(self.panel))
        for asset in ASSETS:
            self.assertGreaterEqual(model.parameter(f"degradation:{asset}"), 0.0)
        prediction = model.predict(self.panel.iloc[:30])
        self.assertTrue(np.isfinite(prediction).all())

    def test_fixed_schedule_and_future_features(self) -> None:
        maintenance = self.raw_panel.loc[
            self.raw_panel["maintenance_type"].notna(),
            ["asset", "date", "maintenance_type"],
        ].rename(columns={"date": "maintenance_date"})
        policy = estimate_fixed_schedule(maintenance)
        self.assertEqual(len(policy), len(ASSETS))
        self.assertTrue((policy["interval_days"] == 60).all())
        future = build_future_frame(
            policy,
            start_date=pd.Timestamp("2025-05-14"),
            end_date=pd.Timestamp("2026-05-14"),
            reference_date=pd.Timestamp("2024-01-01"),
        )
        self.assertEqual(future["asset"].nunique(), len(ASSETS))
        self.assertTrue(future["days_since_maintenance"].notna().all())
        self.assertGreater(int(future["maintenance_type"].notna().sum()), 0)

    def test_joint_failure_requires_post_major_failure(self) -> None:
        dates = pd.date_range("2030-01-01", periods=100, freq="D")
        forecast = pd.DataFrame(
            {
                "asset": "A1",
                "date": dates,
                "performance_forecast": 36.0,
                "rolling_annual_mean": 36.0,
                "maintenance_type": None,
            }
        )
        forecast.loc[20, "maintenance_type"] = "major"
        result = joint_failure_dates(forecast).iloc[0]
        self.assertEqual(result["candidate_threshold_date"], dates[0])
        self.assertEqual(result["diagnostic_major_date"], dates[20])
        self.assertEqual(result["joint_failure_date"], dates[50])


if __name__ == "__main__":
    unittest.main()
