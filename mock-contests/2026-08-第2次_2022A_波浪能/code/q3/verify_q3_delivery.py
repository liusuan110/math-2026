"""核验问题三最终汇总、正式图片、工作簿与 Mac 写作交接文件。"""

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


def main() -> None:
    models_dir = CONTEST_DIR / "results" / "models"
    handoff_dir = CONTEST_DIR / "paper" / "handoff"
    summary = load_json(models_dir / "q3_final_summary.json")
    validation = load_json(models_dir / "q3_full_validation.json")
    checks: dict[str, bool] = {}
    checks["summary_status_passed"] = summary["status"] == "passed"
    checks["key_values_match_validation"] = (
        summary["key_time_values"] == validation["key_time_values"]
    )
    checks["energy_matches_validation"] = (
        summary["energy_at_40_period_end_J"] == validation["energy_at_40_period_end"]
    )

    figure_count = 0
    hashes_match = True
    signatures_pass = True
    for figure in summary["formal_figures"]:
        for suffix, metadata in figure["formats"].items():
            path = CONTEST_DIR / metadata["relative_path"]
            figure_count += 1
            hashes_match &= path.exists() and sha256(path) == metadata["sha256"]
            if not path.exists():
                signatures_pass = False
                continue
            header = path.read_bytes()[:16]
            if suffix == "png":
                signatures_pass &= header.startswith(b"\x89PNG\r\n\x1a\n")
            elif suffix == "pdf":
                signatures_pass &= header.startswith(b"%PDF-")
            elif suffix == "svg":
                text = path.read_text(encoding="utf-8")
                signatures_pass &= "<svg" in text and "</svg>" in text
    checks["nine_formal_figure_files_present"] = figure_count == 9
    checks["formal_figure_hashes_match"] = bool(hashes_match)
    checks["formal_figure_signatures_pass"] = bool(signatures_pass)

    workbook = CONTEST_DIR / summary["official_workbook"]["relative_path"]
    checks["official_workbook_hash_matches"] = (
        workbook.exists() and sha256(workbook) == summary["official_workbook"]["sha256"]
    )
    required_handoff = (
        "README.md",
        "模型与公式.md",
        "结果与结论.md",
        "问题一正文草稿.md",
        "问题二正文草稿.md",
        "问题三正文草稿.md",
        "图表索引.md",
        "复现说明.md",
        "写作待办.md",
    )
    checks["handoff_files_complete"] = all(
        (handoff_dir / name).exists() and (handoff_dir / name).stat().st_size > 0
        for name in required_handoff
    )
    draft = (handoff_dir / "问题三正文草稿.md").read_text(encoding="utf-8")
    results = (handoff_dir / "结果与结论.md").read_text(encoding="utf-8")
    figure_index = (handoff_dir / "图表索引.md").read_text(encoding="utf-8")
    checks["handoff_contains_model_convention"] = (
        "均匀封闭薄壳" in draft and "顶部圆盖" in draft
    )
    checks["handoff_contains_energy_results"] = (
        "6935.244394" in draft and "1.928170" in draft and "6935.244394" in results
    )
    checks["handoff_contains_all_q3_figure_bases"] = all(
        base in figure_index
        for base in (
            "q3_heave_response",
            "q3_pitch_response",
            "q3_pto_and_sensitivity",
        )
    )

    failed = [name for name, passed in checks.items() if not passed]
    report: dict[str, object] = {
        "status": "passed" if not failed else "failed",
        "checks": checks,
        "passed_count": sum(checks.values()),
        "total_count": len(checks),
        "failed": failed,
    }
    with (models_dir / "q3_delivery_validation.json").open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    if failed:
        raise AssertionError("问题三交付核验失败：" + "、".join(failed))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
