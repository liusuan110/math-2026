"""固化问题三已验证的 733 点主模型响应；不写 Excel。"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1]
CONTEST_DIR = CODE_DIR.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q3_dynamics import (  # noqa: E402
    Q3Parameters,
    matrix_exponential_response,
    output_time_grid,
    solve_response,
)


STATE_NAMES = (
    "float_heave_displacement",
    "float_heave_velocity",
    "oscillator_heave_displacement",
    "oscillator_heave_velocity",
    "float_pitch_displacement",
    "float_pitch_velocity",
    "oscillator_pitch_displacement",
    "oscillator_pitch_velocity",
)
KEY_TIMES = (10.0, 20.0, 40.0, 60.0, 100.0)
SAFE_SCALES = np.array([1e-3] * 4 + [1e-4] * 4, dtype=float)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    params = Q3Parameters()
    times = output_time_grid(params)
    solution = solve_response(
        params,
        (0.0, params.forty_period_end),
        times,
        rtol=1e-10,
        max_step=0.01,
    )
    states = solution.y.T.copy()
    exact = matrix_exponential_response(times, params).T
    maximum = np.max(np.abs(states - exact), axis=0)
    scales = np.maximum(np.max(np.abs(exact), axis=0), SAFE_SCALES)
    normalized = maximum / scales
    if float(np.max(normalized)) > 5e-8:
        raise AssertionError("固化前主积分未通过矩阵指数全网格复核")
    if states.shape != (733, 8) or not np.all(np.isfinite(states)):
        raise AssertionError("固化状态形状或有限性检查失败")

    key_rows: dict[str, dict[str, object]] = {}
    for key_time in KEY_TIMES:
        matches = np.flatnonzero(np.isclose(times, key_time, atol=1e-13))
        if matches.size != 1:
            raise AssertionError(f"关键时刻 {key_time} s 未唯一落在输出网格上")
        index = int(matches[0])
        key_rows[f"{key_time:.1f}"] = {
            "zero_based_index": index,
            "time": float(times[index]),
            "values": dict(zip(STATE_NAMES, states[index].tolist(), strict=True)),
        }

    models_dir = CONTEST_DIR / "results" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    npz_path = models_dir / "q3_full_response.npz"
    json_path = models_dir / "q3_full_response.json"
    np.savez_compressed(
        npz_path,
        time=times,
        states=states,
        exact_states=exact,
        state_names=np.asarray(STATE_NAMES),
    )

    payload = {
        "status": "frozen_after_full_validation",
        "model": "CUMCM 2022 A question 3",
        "shell_convention": params.shell_convention.value,
        "state_order": list(STATE_NAMES),
        "solver": {
            "method": "DOP853",
            "rtol": 1e-10,
            "max_step": 0.01,
            "initial_state": [0.0] * 8,
        },
        "time_grid": {
            "count": int(times.size),
            "first": float(times[0]),
            "last": float(times[-1]),
            "step": 0.2,
            "forty_period_end": params.forty_period_end,
        },
        "matrix_exponential_check": {
            "per_state_max_absolute": dict(
                zip(STATE_NAMES, maximum.tolist(), strict=True)
            ),
            "per_state_max_normalized": dict(
                zip(STATE_NAMES, normalized.tolist(), strict=True)
            ),
            "global_max_absolute": float(np.max(maximum)),
            "global_max_normalized": float(np.max(normalized)),
        },
        "key_rows": key_rows,
        "npz_sha256": sha256(npz_path),
        "time": times.tolist(),
        "states": states.tolist(),
    }
    with json_path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

    print(
        json.dumps(
            {
                "status": payload["status"],
                "points": int(times.size),
                "states": int(states.shape[1]),
                "global_max_normalized": float(np.max(normalized)),
                "npz_sha256": payload["npz_sha256"],
                "npz": str(npz_path),
                "json": str(json_path),
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
