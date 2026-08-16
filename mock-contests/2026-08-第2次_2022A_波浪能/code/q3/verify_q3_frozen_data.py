"""回读并核验问题三固化的 733 点数据；不写 Excel。"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
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


MODELS_DIR = CONTEST_DIR / "results" / "models"
NPZ_PATH = MODELS_DIR / "q3_full_response.npz"
JSON_PATH = MODELS_DIR / "q3_full_response.json"
FULL_VALIDATION_PATH = MODELS_DIR / "q3_full_validation.json"
FREEZE_VALIDATION_PATH = MODELS_DIR / "q3_data_freeze_validation.json"
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class Q3FrozenDataVerification(unittest.TestCase):
    """验证文件结构、数值来源、关键行和完整性。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.params = Q3Parameters()
        with np.load(NPZ_PATH) as archive:
            cls.time = archive["time"].copy()
            cls.states = archive["states"].copy()
            cls.exact_states = archive["exact_states"].copy()
            cls.state_names = tuple(archive["state_names"].tolist())
        cls.payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        cls.full_validation = json.loads(
            FULL_VALIDATION_PATH.read_text(encoding="utf-8")
        )

    def test_01_files_and_status(self) -> None:
        self.assertTrue(NPZ_PATH.is_file())
        self.assertTrue(JSON_PATH.is_file())
        self.assertTrue(FULL_VALIDATION_PATH.is_file())
        self.assertEqual(self.payload["status"], "frozen_after_full_validation")
        self.assertEqual(self.full_validation["status"], "passed")
        self.assertTrue(self.full_validation["checks"]["all_passed"])

    def test_02_shape_state_order_and_finite_values(self) -> None:
        self.assertEqual(self.time.shape, (733,))
        self.assertEqual(self.states.shape, (733, 8))
        self.assertEqual(self.exact_states.shape, (733, 8))
        self.assertEqual(self.state_names, STATE_NAMES)
        self.assertEqual(tuple(self.payload["state_order"]), STATE_NAMES)
        self.assertTrue(np.all(np.isfinite(self.states)))

    def test_03_time_grid_matches_fresh_construction(self) -> None:
        fresh = output_time_grid(self.params)
        np.testing.assert_array_equal(self.time, fresh)
        self.assertEqual(self.time[0], 0.0)
        self.assertAlmostEqual(self.time[-1], 146.4, places=12)
        np.testing.assert_allclose(np.diff(self.time), 0.2, rtol=0.0, atol=3e-14)

    def test_04_json_round_trip_is_exact(self) -> None:
        np.testing.assert_array_equal(np.asarray(self.payload["time"]), self.time)
        np.testing.assert_array_equal(np.asarray(self.payload["states"]), self.states)

    def test_05_npz_hash_matches_manifest(self) -> None:
        self.assertEqual(sha256(NPZ_PATH), self.payload["npz_sha256"])

    def test_06_stored_exact_solution_matches_fresh_matrix_exponential(self) -> None:
        fresh_exact = matrix_exponential_response(self.time, self.params).T
        np.testing.assert_allclose(
            self.exact_states, fresh_exact, rtol=0.0, atol=2e-14
        )

    def test_07_frozen_main_solution_matches_fresh_integration(self) -> None:
        fresh = solve_response(
            self.params,
            (0.0, self.params.forty_period_end),
            self.time,
            rtol=1e-10,
            max_step=0.01,
        ).y.T
        np.testing.assert_allclose(self.states, fresh, rtol=0.0, atol=2e-13)

    def test_08_frozen_main_solution_matches_exact_reference(self) -> None:
        maximum = np.max(np.abs(self.states - self.exact_states), axis=0)
        scales = np.maximum(
            np.max(np.abs(self.exact_states), axis=0),
            np.array([1e-3] * 4 + [1e-4] * 4),
        )
        self.assertLess(float(np.max(maximum / scales)), 5e-8)

    def test_09_key_rows_match_payload_and_full_validation(self) -> None:
        validation_keys = self.full_validation["key_time_values"]
        for key_time in (10.0, 20.0, 40.0, 60.0, 100.0):
            label = f"{key_time:.1f}"
            index = int(round(key_time / 0.2))
            row = self.states[index]
            self.assertEqual(self.payload["key_rows"][label]["zero_based_index"], index)
            self.assertEqual(self.payload["key_rows"][label]["time"], key_time)
            payload_values = np.array(
                [self.payload["key_rows"][label]["values"][name] for name in STATE_NAMES]
            )
            np.testing.assert_array_equal(payload_values, row)
            np.testing.assert_allclose(
                row,
                np.asarray(validation_keys[label]),
                rtol=0.0,
                atol=2e-13,
            )

    def test_10_initial_row_is_exactly_zero(self) -> None:
        np.testing.assert_array_equal(self.states[0], np.zeros(8))


def write_validation_record(result: unittest.result.TestResult) -> None:
    payload = {
        "status": "passed" if result.wasSuccessful() else "failed",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "npz_sha256": sha256(NPZ_PATH),
        "json_sha256": sha256(JSON_PATH),
        "source_full_validation_sha256": sha256(FULL_VALIDATION_PATH),
    }
    with FREEZE_VALIDATION_PATH.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Q3FrozenDataVerification)
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)
    write_validation_record(test_result)
    raise SystemExit(0 if test_result.wasSuccessful() else 1)
