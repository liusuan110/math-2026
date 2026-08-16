"""汇总问题二最终参数、功率、验证状态与正式图片。"""

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
    figures_dir = CONTEST_DIR / "figures" / "final"
    constant = load_json(models_dir / "q2_constant_optimization.json")
    nonlinear = load_json(models_dir / "q2_nonlinear_final_validation.json")
    if constant["status"] != "passed":
        raise AssertionError("常量阻尼结果尚未通过验收")
    if nonlinear["status"] != "passed" or not nonlinear["final_answer_ready"]:
        raise AssertionError("幂律阻尼结果尚未通过最终验收")

    constant_result = constant["bounded_optimizer"]
    nonlinear_result = nonlinear["final_result"]
    power_difference = (
        nonlinear_result["mean_power_W"] - constant_result["mean_power_W"]
    )
    relative_improvement = power_difference / constant_result["mean_power_W"]

    figure_bases = (
        "q2_optimization_curves",
        "q2_nonlinear_power_surface",
        "q2_optimal_period_comparison",
    )
    figure_files: list[dict[str, object]] = []
    for base in figure_bases:
        formats: dict[str, object] = {}
        for suffix in ("png", "svg", "pdf"):
            path = figures_dir / f"{base}.{suffix}"
            if not path.exists() or path.stat().st_size == 0:
                raise FileNotFoundError(path)
            formats[suffix] = {
                "relative_path": str(path.relative_to(CONTEST_DIR)).replace("\\", "/"),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        figure_files.append({"base_name": base, "formats": formats})

    summary: dict[str, object] = {
        "status": "passed",
        "model": "CUMCM 2022 A, question 2",
        "parameter_case": 2,
        "wave": {
            "angular_frequency_per_s": 2.2143,
            "period_s": 2.83754925131174,
            "added_mass_kg": 1165.992,
            "radiation_damping_N_s_per_m": 167.8395,
            "excitation_amplitude_N": 4890.0,
        },
        "constant_damping": {
            "optimal_damping_N_s_per_m": constant_result[
                "damping_N_s_per_m"
            ],
            "maximum_mean_power_W": constant_result["mean_power_W"],
            "acceptance_passed": all(constant["acceptance"].values()),
            "acceptance_count": len(constant["acceptance"]),
        },
        "power_law_damping": {
            "optimal_coefficient": nonlinear_result["coefficient"],
            "optimal_exponent": nonlinear_result["exponent"],
            "maximum_mean_power_W": nonlinear_result["mean_power_W"],
            "pto_energy_per_period_J": nonlinear_result[
                "pto_energy_per_period_J"
            ],
            "acceptance_passed": all(nonlinear["acceptance"].values()),
            "acceptance_count": len(nonlinear["acceptance"]),
        },
        "comparison": {
            "power_difference_W": power_difference,
            "relative_improvement": relative_improvement,
            "relative_improvement_percent": 100.0 * relative_improvement,
        },
        "formal_figures": figure_files,
    }

    with (models_dir / "q2_final_summary.json").open(
        "w", encoding="utf-8"
    ) as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
