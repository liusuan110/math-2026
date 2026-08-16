"""核验问题四最终汇总、正式图片与 Mac 写作交接文件。"""

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
    summary = load_json(models_dir / "q4_final_summary.json")
    optimization = load_json(models_dir / "q4_optimization.json")
    checks: dict[str, bool] = {}
    checks["summary_status_passed"] = summary["status"] == "passed"
    checks["final_result_matches_source"] = summary["final_result"] == optimization["final_result"]
    checks["all_optimization_checks_passed"] = all(optimization["checks"].values())

    count = 0
    hashes_match = True
    signatures_pass = True
    for figure in summary["formal_figures"]:
        for suffix, item in figure["formats"].items():
            path = CONTEST_DIR / item["relative_path"]
            count += 1
            hashes_match &= path.exists() and sha256(path) == item["sha256"]
            if not path.exists():
                signatures_pass = False
            elif suffix == "png":
                signatures_pass &= path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
            elif suffix == "pdf":
                signatures_pass &= path.read_bytes()[:5] == b"%PDF-"
            elif suffix == "svg":
                text = path.read_text(encoding="utf-8")
                signatures_pass &= "<svg" in text and "</svg>" in text
    checks["nine_formal_figure_files_present"] = count == 9
    checks["formal_figure_hashes_match"] = bool(hashes_match)
    checks["formal_figure_signatures_pass"] = bool(signatures_pass)

    required = (
        "README.md",
        "模型与公式.md",
        "结果与结论.md",
        "问题一正文草稿.md",
        "问题二正文草稿.md",
        "问题三正文草稿.md",
        "问题四正文草稿.md",
        "图表索引.md",
        "复现说明.md",
        "写作待办.md",
    )
    checks["handoff_files_complete"] = all(
        (handoff_dir / name).exists() and (handoff_dir / name).stat().st_size > 0
        for name in required
    )
    draft = (handoff_dir / "问题四正文草稿.md").read_text(encoding="utf-8")
    results = (handoff_dir / "结果与结论.md").read_text(encoding="utf-8")
    index = (handoff_dir / "图表索引.md").read_text(encoding="utf-8")
    checks["handoff_contains_final_damping"] = "59152.916113" in draft and "100000" in draft
    checks["handoff_contains_final_power"] = "318.679256" in draft and "318.679256" in results
    checks["handoff_contains_global_proof"] = "Sherman-Morrison" in draft and "差分进化" in draft
    checks["handoff_contains_all_q4_figures"] = all(
        base in index
        for base in (
            "q4_optimization_curves",
            "q4_total_power_surface",
            "q4_optimal_period_response",
        )
    )

    failed = [name for name, passed in checks.items() if not passed]
    report = {
        "status": "passed" if not failed else "failed",
        "checks": checks,
        "passed_count": sum(checks.values()),
        "total_count": len(checks),
        "failed": failed,
    }
    with (models_dir / "q4_delivery_validation.json").open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    if failed:
        raise AssertionError("问题四交付核验失败：" + "、".join(failed))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
