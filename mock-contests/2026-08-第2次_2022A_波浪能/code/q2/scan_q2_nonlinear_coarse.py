"""问题二幂律阻尼：执行 21×11 全参数域粗网格扫描。"""

from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path
from time import perf_counter

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1]
CONTEST_DIR = CODE_DIR.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q2_power import (  # noqa: E402
    constant_mean_power,
    q2_parameters,
    shooting_mean_power,
)


COEFFICIENTS = np.linspace(0.0, 100000.0, 21)
EXPONENTS = np.linspace(0.0, 1.0, 11)
SCREENING_SETTINGS = {
    "root_tolerance": 1e-7,
    "periodicity_tolerance": 2e-6,
    "maximum_root_evaluations": 80,
    "rtol": 2e-7,
    "atol": 2e-9,
    "max_step_fraction": 1.0 / 30.0,
}


def connected_candidate_regions(
    mask: np.ndarray,
    power: np.ndarray,
) -> list[dict[str, object]]:
    """按八邻域提取高功率掩膜中的连通候选区域。"""

    visited = np.zeros_like(mask, dtype=bool)
    regions: list[dict[str, object]] = []
    for exponent_index, coefficient_index in np.argwhere(mask):
        if visited[exponent_index, coefficient_index]:
            continue
        queue = deque([(int(exponent_index), int(coefficient_index))])
        visited[exponent_index, coefficient_index] = True
        members: list[tuple[int, int]] = []
        while queue:
            row, column = queue.popleft()
            members.append((row, column))
            for row_step in (-1, 0, 1):
                for column_step in (-1, 0, 1):
                    if row_step == 0 and column_step == 0:
                        continue
                    neighbor_row = row + row_step
                    neighbor_column = column + column_step
                    if not (
                        0 <= neighbor_row < mask.shape[0]
                        and 0 <= neighbor_column < mask.shape[1]
                    ):
                        continue
                    if mask[neighbor_row, neighbor_column] and not visited[
                        neighbor_row, neighbor_column
                    ]:
                        visited[neighbor_row, neighbor_column] = True
                        queue.append((neighbor_row, neighbor_column))

        member_power = np.array([power[row, column] for row, column in members])
        best_member = members[int(np.argmax(member_power))]
        member_rows = [row for row, _ in members]
        member_columns = [column for _, column in members]
        regions.append(
            {
                "grid_point_count": len(members),
                "coefficient_range": [
                    float(COEFFICIENTS[min(member_columns)]),
                    float(COEFFICIENTS[max(member_columns)]),
                ],
                "exponent_range": [
                    float(EXPONENTS[min(member_rows)]),
                    float(EXPONENTS[max(member_rows)]),
                ],
                "best_grid_point": {
                    "coefficient": float(COEFFICIENTS[best_member[1]]),
                    "exponent": float(EXPONENTS[best_member[0]]),
                    "mean_power_W": float(power[best_member]),
                },
                "touches_coefficient_upper_bound": max(member_columns)
                == COEFFICIENTS.size - 1,
                "touches_exponent_lower_bound": min(member_rows) == 0,
                "touches_exponent_upper_bound": max(member_rows)
                == EXPONENTS.size - 1,
            }
        )
    return sorted(
        regions,
        key=lambda item: item["best_grid_point"]["mean_power_W"],
        reverse=True,
    )


def boundary_maximum(
    coordinate: np.ndarray,
    values: np.ndarray,
    coordinate_name: str,
) -> dict[str, float]:
    index = int(np.argmax(values))
    return {
        coordinate_name: float(coordinate[index]),
        "mean_power_W": float(values[index]),
    }


def enforce_acceptance(report: dict[str, object]) -> None:
    failed = [name for name, passed in report["acceptance"].items() if not passed]
    if failed:
        raise AssertionError("幂律粗网格验收失败：" + "、".join(failed))


def main() -> None:
    params = q2_parameters()
    shape = (EXPONENTS.size, COEFFICIENTS.size)
    power = np.zeros(shape)
    periodicity_error = np.zeros(shape)
    root_success = np.ones(shape, dtype=bool)
    root_map_evaluations = np.zeros(shape, dtype=int)
    ode_function_evaluations = np.zeros(shape, dtype=int)
    periodic_states = np.zeros((*shape, 4))

    start = perf_counter()
    for exponent_index, exponent in enumerate(EXPONENTS):
        previous_state = None
        for coefficient_index in range(1, COEFFICIENTS.size):
            coefficient = COEFFICIENTS[coefficient_index]
            if previous_state is None and exponent_index > 0:
                initial_state = periodic_states[
                    exponent_index - 1, coefficient_index
                ]
            else:
                initial_state = previous_state
            result = shooting_mean_power(
                coefficient,
                exponent,
                params,
                initial_state=initial_state,
                **SCREENING_SETTINGS,
            )
            power[exponent_index, coefficient_index] = result.mean_power
            periodicity_error[exponent_index, coefficient_index] = (
                result.periodicity_error
            )
            root_success[exponent_index, coefficient_index] = result.root_success
            root_map_evaluations[exponent_index, coefficient_index] = (
                result.root_map_evaluations
            )
            ode_function_evaluations[exponent_index, coefficient_index] = (
                result.ode_function_evaluations
            )
            periodic_states[exponent_index, coefficient_index] = (
                result.periodic_state
            )
            previous_state = result.periodic_state
    elapsed = perf_counter() - start

    global_flat_index = int(np.argmax(power))
    global_index = tuple(int(value) for value in np.unravel_index(global_flat_index, shape))
    maximum_power = float(power[global_index])

    # 以粗网格最大值的 98% 作为“需要进入下一层加密”的区域定义。
    candidate_threshold = 0.98 * maximum_power
    candidate_mask = power >= candidate_threshold
    candidate_regions = connected_candidate_regions(candidate_mask, power)

    flat_descending = np.argsort(power.ravel())[::-1]
    top_points: list[dict[str, float]] = []
    for flat_index in flat_descending[:15]:
        row, column = np.unravel_index(int(flat_index), shape)
        top_points.append(
            {
                "coefficient": float(COEFFICIENTS[column]),
                "exponent": float(EXPONENTS[row]),
                "mean_power_W": float(power[row, column]),
                "periodicity_error": float(periodicity_error[row, column]),
            }
        )

    p_zero_frequency = np.array(
        [constant_mean_power(value, params).mean_power for value in COEFFICIENTS]
    )
    nonzero_p_zero = p_zero_frequency > 0.0
    p_zero_relative_error = np.zeros_like(p_zero_frequency)
    p_zero_relative_error[nonzero_p_zero] = np.abs(
        power[0, nonzero_p_zero] - p_zero_frequency[nonzero_p_zero]
    ) / p_zero_frequency[nonzero_p_zero]

    # 用无连续延拓的默认初猜复算若干已固定位置，排除路径依赖。
    audit_indices = {
        (global_index[0], global_index[1]),
        (5, 2),
        (10, 10),
        (2, 18),
        (0, 8),
    }
    continuation_audit: list[dict[str, float | bool]] = []
    for row, column in sorted(audit_indices):
        independent = shooting_mean_power(
            COEFFICIENTS[column],
            EXPONENTS[row],
            params,
            **SCREENING_SETTINGS,
        )
        reference_power = power[row, column]
        audit_error = abs(independent.mean_power - reference_power) / max(
            abs(reference_power), 1e-15
        )
        continuation_audit.append(
            {
                "coefficient": float(COEFFICIENTS[column]),
                "exponent": float(EXPONENTS[row]),
                "continued_power_W": float(reference_power),
                "independent_power_W": float(independent.mean_power),
                "relative_error": float(audit_error),
                "root_success": independent.root_success,
            }
        )

    report: dict[str, object] = {
        "status": "pending_acceptance",
        "model": "CUMCM 2022 A, question 2, power-law PTO damping coarse scan",
        "optimization_executed": False,
        "grid": {
            "coefficient_points": COEFFICIENTS.tolist(),
            "exponent_points": EXPONENTS.tolist(),
            "shape": list(shape),
            "evaluated_nonzero_points": int((COEFFICIENTS.size - 1) * EXPONENTS.size),
            "wall_time_s": elapsed,
            "total_ode_function_evaluations": int(
                np.sum(ode_function_evaluations)
            ),
            "maximum_periodicity_error": float(np.max(periodicity_error)),
        },
        "coarse_global_best": {
            "coefficient": float(COEFFICIENTS[global_index[1]]),
            "exponent": float(EXPONENTS[global_index[0]]),
            "mean_power_W": maximum_power,
            "touches_coefficient_upper_bound": global_index[1]
            == COEFFICIENTS.size - 1,
            "touches_exponent_boundary": global_index[0]
            in (0, EXPONENTS.size - 1),
        },
        "candidate_definition": {
            "fraction_of_grid_maximum": 0.98,
            "power_threshold_W": candidate_threshold,
            "grid_point_count": int(np.count_nonzero(candidate_mask)),
            "connected_region_count": len(candidate_regions),
        },
        "candidate_regions": candidate_regions,
        "top_grid_points": top_points,
        "boundary_trends": {
            "coefficient_zero": {
                "minimum_power_W": float(np.min(power[:, 0])),
                "maximum_power_W": float(np.max(power[:, 0])),
            },
            "coefficient_upper": boundary_maximum(
                EXPONENTS, power[:, -1], "exponent"
            ),
            "exponent_zero": boundary_maximum(
                COEFFICIENTS, power[0], "coefficient"
            ),
            "exponent_one": boundary_maximum(
                COEFFICIENTS, power[-1], "coefficient"
            ),
        },
        "p_zero_frequency_crosscheck": {
            "maximum_relative_error": float(np.max(p_zero_relative_error)),
        },
        "continuation_independence_audit": continuation_audit,
        "surface_diagnostics": {
            "power_minimum_W": float(np.min(power)),
            "power_maximum_W": maximum_power,
            "largest_adjacent_coefficient_change_W": float(
                np.max(np.abs(np.diff(power, axis=1)))
            ),
            "largest_adjacent_exponent_change_W": float(
                np.max(np.abs(np.diff(power, axis=0)))
            ),
            "points_above_95_percent": int(
                np.count_nonzero(power >= 0.95 * maximum_power)
            ),
            "points_above_99_percent": int(
                np.count_nonzero(power >= 0.99 * maximum_power)
            ),
        },
        "acceptance": {
            "all_values_are_finite": bool(np.all(np.isfinite(power))),
            "all_power_is_nonnegative": bool(np.min(power) >= -1e-10),
            "all_roots_report_success": bool(np.all(root_success)),
            "all_periodicity_errors_pass": bool(
                np.max(periodicity_error) <= SCREENING_SETTINGS["periodicity_tolerance"]
            ),
            "zero_coefficient_boundary_is_exact": bool(
                np.all(power[:, 0] == 0.0)
            ),
            "p_zero_matches_frequency_domain": bool(
                np.max(p_zero_relative_error) < 1e-5
            ),
            "continuation_is_path_independent_at_audit_points": all(
                item["root_success"] and item["relative_error"] < 1e-5
                for item in continuation_audit
            ),
            "candidate_region_detected": len(candidate_regions) >= 1,
        },
    }
    enforce_acceptance(report)
    report["status"] = "passed"

    models_dir = CONTEST_DIR / "results" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        models_dir / "q2_nonlinear_coarse_grid.npz",
        coefficient=COEFFICIENTS,
        exponent=EXPONENTS,
        mean_power=power,
        periodicity_error=periodicity_error,
        root_success=root_success,
        root_map_evaluations=root_map_evaluations,
        ode_function_evaluations=ode_function_evaluations,
        periodic_state=periodic_states,
    )
    with (models_dir / "q2_nonlinear_coarse_scan.json").open(
        "w", encoding="utf-8"
    ) as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
