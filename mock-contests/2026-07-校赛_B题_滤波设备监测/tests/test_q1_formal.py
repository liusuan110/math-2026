from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from filter_monitoring.config import ASSETS  # noqa: E402
from filter_monitoring.q1_analysis import (  # noqa: E402
    build_device_metrics,
    fit_panel_models,
    maintenance_event_effects,
    model_diagnostics,
    prepare_analysis_panel,
    summarize_maintenance_effects,
)


def synthetic_panel() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    dates = pd.date_range("2024-01-01", periods=400, freq="D")
    event_days = {60: "medium", 120: "medium", 180: "major", 240: "medium", 300: "major", 360: "medium"}
    rows = []
    for asset_index, asset in enumerate(ASSETS):
        last_event = None
        for day, date in enumerate(dates):
            maintenance_type = event_days.get(day)
            if maintenance_type is not None:
                last_event = day
            since = day - last_event if last_event is not None else np.nan
            fouling = 0.0 if np.isnan(since) else 0.28 * min(since, 90)
            performance = (
                105.0
                + asset_index
                - 0.008 * day
                + 7.0 * np.sin(2.0 * np.pi * (day + 1) / 365.25)
                - fouling
                + rng.normal(0.0, 0.35)
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
                    "maintenance_type": maintenance_type,
                }
            )
    return pd.DataFrame(rows)


class Q1FormalAnalysisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.panel = prepare_analysis_panel(synthetic_panel())
        cls.models = fit_panel_models(cls.panel)

    def test_panel_models_and_metrics(self) -> None:
        diagnostics = model_diagnostics(self.models).set_index("model")
        metrics = build_device_metrics(self.panel, self.models)
        self.assertEqual(len(metrics), 10)
        self.assertGreater(float(diagnostics.loc["full", "r_squared"]), 0.8)
        self.assertLess(float(metrics["residual_rmse"].max()), 2.0)

    def test_adjusted_maintenance_effects(self) -> None:
        detail = maintenance_event_effects(self.panel, self.models["trend_season"])
        summary = summarize_maintenance_effects(detail).set_index("maintenance_type")
        self.assertEqual(len(detail), 60)
        self.assertGreater(float(summary.loc["medium", "instant_median"]), 5.0)
        self.assertGreater(float(summary.loc["major", "instant_median"]), 5.0)
        self.assertGreater(int(summary.loc["medium", "usable_retained_events"]), 0)


if __name__ == "__main__":
    unittest.main()
