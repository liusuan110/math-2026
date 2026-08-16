"""汇总问题三最终响应、验证状态、工作簿与正式图片。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


CODE_DIR = Path(__file__).resolve().parents[1]
CONTEST_DIR = CODE_DIR.parent


def load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_metadata(path: Path) -> dict[str, object]:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(path)
    return {
        "relative_path": str(path.relative_to(CONTEST_DIR)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def main() -> None:
    models_dir = CONTEST_DIR / "results" / "models"
    figures_dir = CONTEST_DIR / "figures" / "final"
    validation = load_json(models_dir / "q3_full_validation.json")
    freeze_validation = load_json(models_dir / "q3_data_freeze_validation.json")
    workbook_validation = load_json(models_dir / "q3_workbook_validation.json")
    plot_metrics = load_json(models_dir / "q3_plot_metrics.json")
    if any(
        report["status"] != "passed"
        for report in (validation, freeze_validation, workbook_validation, plot_metrics)
    ):
        raise AssertionError("问题三存在尚未通过的上游验收")

    figure_bases = (
        "q3_heave_response",
        "q3_pitch_response",
        "q3_pto_and_sensitivity",
    )
    figures: list[dict[str, object]] = []
    for base in figure_bases:
        formats = {
            suffix: file_metadata(figures_dir / f"{base}.{suffix}")
            for suffix in ("png", "svg", "pdf")
        }
        figures.append({"base_name": base, "formats": formats})

    summary: dict[str, object] = {
        "status": "passed",
        "model": "CUMCM 2022 A, question 3",
        "parameter_case": 3,
        "shell_convention": validation["shell_convention"],
        "state_order": validation["state_order"],
        "time_grid": validation["official_grid"],
        "wave_period_s": validation["wave_period"],
        "forty_period_end_s": validation["forty_period_end"],
        "key_time_values": validation["key_time_values"],
        "peak_absolute_responses": validation["physical_ranges"],
        "energy_at_40_period_end_J": validation["energy_at_40_period_end"],
        "sensitivity": validation["sensitivity"],
        "numerical_errors": validation["errors"],
        "plot_metrics": plot_metrics,
        "official_workbook": file_metadata(CONTEST_DIR / "results" / "tables" / "result3.xlsx"),
        "frozen_response": file_metadata(models_dir / "q3_full_response.npz"),
        "formal_figures": figures,
    }
    with (models_dir / "q3_final_summary.json").open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
