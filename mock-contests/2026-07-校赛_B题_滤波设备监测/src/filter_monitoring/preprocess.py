"""把不规则高频监测值变为可建模的日级面板。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import SHORT_GAP_LIMIT_DAYS


def build_daily_panel(
    telemetry: pd.DataFrame,
    maintenance: pd.DataFrame,
    short_gap_days: int = SHORT_GAP_LIMIT_DAYS,
) -> pd.DataFrame:
    """日聚合、短缺口插值并对齐维护事件。

    `performance_median` 始终保存观测事实；`performance_model` 才允许填补不超过
    `short_gap_days` 的内部短缺口，避免长期缺测被平滑掩盖。
    """

    raw = telemetry.copy()
    raw["date"] = raw["timestamp"].dt.normalize()
    grouped = raw.groupby(["asset", "date"], observed=True)["performance"]
    daily = grouped.agg(
        performance_mean="mean",
        performance_median="median",
        performance_std="std",
        performance_min="min",
        performance_max="max",
        valid_rows="count",
    )
    daily["sample_rows"] = grouped.size()
    daily["missing_rate"] = 1.0 - daily["valid_rows"] / daily["sample_rows"]
    daily = daily.reset_index()

    completed: list[pd.DataFrame] = []
    for asset, asset_daily in daily.groupby("asset", sort=True):
        index = pd.date_range(asset_daily["date"].min(), asset_daily["date"].max(), freq="D")
        block = asset_daily.set_index("date").reindex(index)
        block.index.name = "date"
        block["asset"] = asset
        block["sample_rows"] = block["sample_rows"].fillna(0).astype(int)
        block["valid_rows"] = block["valid_rows"].fillna(0).astype(int)
        block["missing_rate"] = np.where(
            block["sample_rows"] > 0,
            1.0 - block["valid_rows"] / block["sample_rows"],
            1.0,
        )
        block["performance_model"] = block["performance_median"].interpolate(
            method="linear",
            limit=short_gap_days,
            limit_area="inside",
        )
        block["was_imputed"] = block["performance_median"].isna() & block["performance_model"].notna()
        completed.append(block.reset_index())

    panel = pd.concat(completed, ignore_index=True)

    event_rank = {"minor": 1, "medium": 2, "major": 3}
    events = maintenance.copy()
    events["event_rank"] = events["maintenance_type"].map(event_rank)
    events = (
        events.sort_values("event_rank")
        .groupby(["asset", "maintenance_date"], as_index=False)
        .tail(1)[["asset", "maintenance_date", "maintenance_type"]]
        .rename(columns={"maintenance_date": "date"})
    )
    panel = panel.merge(events, how="left", on=["asset", "date"])
    panel = panel.sort_values(["asset", "date"], kind="stable").reset_index(drop=True)

    panel["last_maintenance_date"] = panel["date"].where(panel["maintenance_type"].notna())
    panel["last_maintenance_date"] = panel.groupby("asset")["last_maintenance_date"].ffill()
    panel["days_since_maintenance"] = (
        panel["date"] - panel["last_maintenance_date"]
    ).dt.days.astype("Int64")
    return panel


def data_quality_summary(telemetry: pd.DataFrame) -> pd.DataFrame:
    """生成每台设备的数据范围、缺失率、重复和典型采样间隔。"""

    rows: list[dict[str, object]] = []
    for asset, block in telemetry.groupby("asset", sort=True):
        cadence = block["timestamp"].sort_values().diff().dt.total_seconds().div(3600)
        rows.append(
            {
                "asset": asset,
                "start": block["timestamp"].min(),
                "end": block["timestamp"].max(),
                "rows": len(block),
                "valid_performance": int(block["performance"].notna().sum()),
                "missing_performance": int(block["performance"].isna().sum()),
                "missing_rate": float(block["performance"].isna().mean()),
                "duplicate_timestamps": int(block["timestamp"].duplicated().sum()),
                "median_cadence_hours": float(cadence.median()),
            }
        )
    return pd.DataFrame(rows)

