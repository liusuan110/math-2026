"""全项目唯一的路径、阈值、成本和日期口径。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = PROJECT_DIR.parents[1]

RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
RESULTS_DIR = PROJECT_DIR / "data" / "results"
FIGURES_DIR = PROJECT_DIR / "figures" / "generated"

PROBLEM_DOCX = RAW_DIR / "B题.docx"
TELEMETRY_XLSX = RAW_DIR / "附件1.xlsx"
MAINTENANCE_XLSX = RAW_DIR / "附件2.xlsx"

ASSETS = tuple(f"A{i}" for i in range(1, 11))
EXPECTED_TELEMETRY_SHEETS = tuple(f"A_{i}" for i in range(1, 11))

COMMISSION_DATE = date(2022, 4, 1)
OBSERVATION_START = date(2024, 4, 1)
OBSERVATION_END = date(2026, 4, 30)
LIFETIME_THRESHOLD = 37.0
ROLLING_YEAR_DAYS = 365
SHORT_GAP_LIMIT_DAYS = 2


@dataclass(frozen=True)
class CostConfig:
    """费用单位统一为万元。"""

    purchase: float = 300.0
    medium: float = 3.0
    major: float = 12.0
    minor: float = 0.0


BASE_COSTS = CostConfig()


def ensure_output_dirs() -> None:
    """只创建可重建的输出目录，不触碰原始附件。"""

    for directory in (PROCESSED_DIR, RESULTS_DIR, FIGURES_DIR):
        directory.mkdir(parents=True, exist_ok=True)

