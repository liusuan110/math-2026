"""汇总问题四最终优化、验证状态与正式图片。"""

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


def metadata(path: Path) -> dict[str, object]:
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
    optimization = load_json(models_dir / "q4_optimization.json")
    if optimization["status"] != "passed" or not all(optimization["checks"].values()):
        raise AssertionError("问题四优化尚未通过全部验收")

    figure_bases = (
        "q4_optimization_curves",
        "q4_total_power_surface",
        "q4_optimal_period_response",
    )
    figures: list[dict[str, object]] = []
    for base in figure_bases:
        figures.append(
            {
                "base_name": base,
                "formats": {
                    suffix: metadata(figures_dir / f"{base}.{suffix}")
                    for suffix in ("png", "svg", "pdf")
                },
            }
        )
    summary = {
        "status": "passed",
        "model": optimization["model"],
        "parameter_case": 4,
        "shell_convention": optimization["shell_convention"],
        "wave_period_s": optimization["wave_period_s"],
        "optimization_bounds": optimization["optimization_bounds"],
        "final_result": optimization["final_result"],
        "analytic_unconstrained_damping": optimization["analytic_unconstrained_damping"],
        "periodic_time_domain_validation": optimization["periodic_time_domain_validation"],
        "joint_differential_evolution": optimization["joint_differential_evolution"],
        "acceptance": {
            "passed_count": optimization["passed_count"],
            "total_count": optimization["total_count"],
            "all_passed": all(optimization["checks"].values()),
        },
        "formal_figures": figures,
    }
    with (models_dir / "q4_final_summary.json").open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
