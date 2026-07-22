"""原始附件读取与结构校验。"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import (
    ASSETS,
    EXPECTED_TELEMETRY_SHEETS,
    MAINTENANCE_XLSX,
    PROBLEM_DOCX,
    TELEMETRY_XLSX,
)


def normalize_asset(value: object) -> str:
    """把 A_1、a1 等写法统一为 A1。"""

    text = str(value).strip().upper().replace("_", "").replace(" ", "")
    return text


def audit_inputs() -> pd.DataFrame:
    """检查三份输入是否存在，并校验 Excel 的基本结构。"""

    rows: list[dict[str, object]] = []
    for label, path in (
        ("problem", PROBLEM_DOCX),
        ("telemetry", TELEMETRY_XLSX),
        ("maintenance", MAINTENANCE_XLSX),
    ):
        rows.append(
            {
                "input": label,
                "path": str(path),
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else 0,
            }
        )

    report = pd.DataFrame(rows)
    missing = report.loc[~report["exists"], "path"].tolist()
    if missing:
        raise FileNotFoundError("缺少原始附件：" + "；".join(missing))

    telemetry_sheets = tuple(pd.ExcelFile(TELEMETRY_XLSX).sheet_names)
    if telemetry_sheets != EXPECTED_TELEMETRY_SHEETS:
        raise ValueError(
            "附件1工作表不符合预期："
            f"expected={EXPECTED_TELEMETRY_SHEETS}, actual={telemetry_sheets}"
        )

    maintenance_columns = set(pd.read_excel(MAINTENANCE_XLSX, nrows=3).columns)
    required = {"编号", "日期", "维护类型"}
    if not required.issubset(maintenance_columns):
        raise ValueError(f"附件2缺少字段：{sorted(required - maintenance_columns)}")
    return report


def load_telemetry(path: Path = TELEMETRY_XLSX) -> pd.DataFrame:
    """读取 10 个工作表并合并，保留性能缺失值供质量审计。"""

    frames: list[pd.DataFrame] = []
    with pd.ExcelFile(path) as workbook:
        for sheet in workbook.sheet_names:
            frame = pd.read_excel(workbook, sheet_name=sheet, usecols=["time", "per"])
            frame = frame.rename(columns={"time": "timestamp", "per": "performance"})
            frame.insert(0, "asset", normalize_asset(sheet))
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
            frame["performance"] = pd.to_numeric(frame["performance"], errors="coerce")
            frames.append(frame)

    telemetry = pd.concat(frames, ignore_index=True)
    telemetry = telemetry.dropna(subset=["timestamp"])
    telemetry = telemetry.sort_values(["asset", "timestamp"], kind="stable").reset_index(drop=True)
    unknown = sorted(set(telemetry["asset"]) - set(ASSETS))
    if unknown:
        raise ValueError(f"附件1出现未知设备：{unknown}")
    return telemetry


def load_maintenance(path: Path = MAINTENANCE_XLSX) -> pd.DataFrame:
    """读取维护记录，把中文维护类型转为稳定的英文枚举。"""

    frame = pd.read_excel(path, usecols=["编号", "日期", "维护类型"])
    frame = frame.rename(
        columns={"编号": "asset", "日期": "maintenance_date", "维护类型": "maintenance_type"}
    )
    frame["asset"] = frame["asset"].map(normalize_asset)
    frame["maintenance_date"] = pd.to_datetime(frame["maintenance_date"], errors="coerce").dt.normalize()
    type_map = {"中维护": "medium", "大维护": "major", "小维护": "minor"}
    frame["maintenance_type_raw"] = frame["maintenance_type"]
    frame["maintenance_type"] = frame["maintenance_type"].astype(str).str.strip().map(type_map)

    if frame[["asset", "maintenance_date", "maintenance_type"]].isna().any().any():
        bad = frame[frame[["asset", "maintenance_date", "maintenance_type"]].isna().any(axis=1)]
        raise ValueError(f"附件2存在无法解析的维护记录，共 {len(bad)} 行")
    unknown = sorted(set(frame["asset"]) - set(ASSETS))
    if unknown:
        raise ValueError(f"附件2出现未知设备：{unknown}")
    return frame.sort_values(["asset", "maintenance_date"], kind="stable").reset_index(drop=True)

