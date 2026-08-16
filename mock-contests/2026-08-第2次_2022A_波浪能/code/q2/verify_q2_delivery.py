"""核验问题二最终汇总、正式图片和 Mac 写作交接文件。"""

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
    summary = load_json(models_dir / "q2_final_summary.json")
    constant = load_json(models_dir / "q2_constant_optimization.json")
    nonlinear = load_json(models_dir / "q2_nonlinear_final_validation.json")

    checks: dict[str, bool] = {}
    checks["summary_status_passed"] = summary["status"] == "passed"
    checks["constant_value_matches_source"] = (
        summary["constant_damping"]["optimal_damping_N_s_per_m"]
        == constant["bounded_optimizer"]["damping_N_s_per_m"]
        and summary["constant_damping"]["maximum_mean_power_W"]
        == constant["bounded_optimizer"]["mean_power_W"]
    )
    checks["nonlinear_value_matches_source"] = (
        summary["power_law_damping"]["optimal_coefficient"]
        == nonlinear["final_result"]["coefficient"]
        and summary["power_law_damping"]["optimal_exponent"]
        == nonlinear["final_result"]["exponent"]
        and summary["power_law_damping"]["maximum_mean_power_W"]
        == nonlinear["final_result"]["mean_power_W"]
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

    required_handoff = (
        "README.md",
        "模型与公式.md",
        "结果与结论.md",
        "问题一正文草稿.md",
        "问题二正文草稿.md",
        "图表索引.md",
        "复现说明.md",
        "写作待办.md",
    )
    checks["handoff_files_complete"] = all(
        (handoff_dir / name).exists() and (handoff_dir / name).stat().st_size > 0
        for name in required_handoff
    )
    q2_draft = (handoff_dir / "问题二正文草稿.md").read_text(encoding="utf-8")
    results_text = (handoff_dir / "结果与结论.md").read_text(encoding="utf-8")
    checks["handoff_contains_final_constant_result"] = (
        "37193.8126" in q2_draft and "229.333940" in q2_draft
    )
    checks["handoff_contains_final_nonlinear_result"] = (
        "0.415718380" in q2_draft
        and "229.994333" in q2_draft
        and "0.415718380" in results_text
    )
    checks["handoff_contains_all_q2_figure_bases"] = all(
        base in (handoff_dir / "图表索引.md").read_text(encoding="utf-8")
        for base in (
            "q2_optimization_curves",
            "q2_nonlinear_power_surface",
            "q2_optimal_period_comparison",
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
    with (models_dir / "q2_delivery_validation.json").open(
        "w", encoding="utf-8"
    ) as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    if failed:
        raise AssertionError("问题二交付核验失败：" + "、".join(failed))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
