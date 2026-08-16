r"""问题三公共动力学模块的基础自动验证。

运行方式：
    .venv\Scripts\python.exe code\q3\verify_q3_foundation.py

本脚本只执行短时与哨兵测试，不生成正式 40 周期结果。
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q3_dynamics import (  # noqa: E402
    FloatShellConvention,
    Q3Parameters,
    diagnostic_time_grid,
    heave_matrices,
    instantaneous_powers,
    matrix_exponential_response,
    mechanical_energy,
    output_time_grid,
    pitch_matrices,
    solve_response,
    state_rhs,
    system_matrices,
)


class Q3FoundationVerification(unittest.TestCase):
    """验证问题三参数、矩阵、能量和短时积分。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.params = Q3Parameters()

    def test_01_primary_derived_parameters(self) -> None:
        geometry = self.params.float_geometry
        self.assertAlmostEqual(self.params.period, 3.663237702413465, places=12)
        self.assertAlmostEqual(
            self.params.forty_period_end, 146.5295080965386, places=11
        )
        self.assertAlmostEqual(self.params.effective_float_mass, 5894.876, places=12)
        self.assertAlmostEqual(
            self.params.hydrostatic_heave_stiffness,
            31557.29820530947,
            places=9,
        )
        self.assertAlmostEqual(
            self.params.spring_equilibrium_length, 0.2019575, places=12
        )
        self.assertAlmostEqual(
            self.params.oscillator_centroid_to_hinge, 0.4519575, places=12
        )
        self.assertAlmostEqual(
            self.params.oscillator_centroid_inertia, 202.75, places=12
        )
        self.assertAlmostEqual(
            self.params.oscillator_hinge_inertia, 699.7281605346062, places=10
        )
        self.assertAlmostEqual(geometry.centroid_to_hinge, 1.4079251572674458, places=12)
        self.assertAlmostEqual(
            geometry.inertia_about_centroid, 8398.776059760505, places=9
        )
        self.assertAlmostEqual(
            geometry.side_mass + geometry.top_mass + geometry.cone_mass,
            self.params.float_mass,
            places=10,
        )

    def test_02_alternative_shell_parameters(self) -> None:
        alternative = replace(
            self.params, shell_convention=FloatShellConvention.LATERAL_ONLY
        )
        geometry = alternative.float_geometry
        self.assertEqual(geometry.top_mass, 0.0)
        self.assertAlmostEqual(geometry.centroid_to_hinge, 1.1892523268328201, places=12)
        self.assertAlmostEqual(
            geometry.inertia_about_centroid, 7458.519992582904, places=9
        )

    def test_03_matrices_match_sealed_values_and_are_positive(self) -> None:
        mz, cz, kz = heave_matrices(self.params)
        mt, ct, kt = pitch_matrices(self.params)
        np.testing.assert_allclose(
            mt,
            [
                [20223.512213279653, -1548.172239268452],
                [-1548.172239268452, 699.7281605346062],
            ],
            rtol=0.0,
            atol=2e-10,
        )
        np.testing.assert_allclose(
            kt,
            [
                [292460.42269479064, -250000.0],
                [-250000.0, 239223.7965445],
            ],
            rtol=0.0,
            atol=2e-9,
        )
        for matrix in (mz, cz, kz, mt, ct, kt):
            np.testing.assert_allclose(matrix, matrix.T, rtol=0.0, atol=0.0)
            self.assertGreater(float(np.min(np.linalg.eigvalsh(matrix))), 0.0)

        mass, damping, stiffness = system_matrices(self.params)
        self.assertEqual(mass.shape, (4, 4))
        self.assertEqual(damping.shape, (4, 4))
        self.assertEqual(stiffness.shape, (4, 4))
        np.testing.assert_array_equal(mass[:2, 2:], np.zeros((2, 2)))
        np.testing.assert_array_equal(mass[2:, :2], np.zeros((2, 2)))

    def test_04_output_and_diagnostic_grids(self) -> None:
        output = output_time_grid(self.params)
        self.assertEqual(output.size, 733)
        self.assertEqual(output[0], 0.0)
        self.assertAlmostEqual(output[-1], 146.4, places=12)
        np.testing.assert_allclose(np.diff(output), 0.2, rtol=0.0, atol=3e-14)
        self.assertLess(output[-1], self.params.forty_period_end)
        for requested in (10.0, 20.0, 40.0, 60.0, 100.0):
            self.assertEqual(
                np.flatnonzero(np.isclose(output, requested, atol=1e-13)).size,
                1,
            )

        diagnostic = diagnostic_time_grid(self.params)
        self.assertEqual(diagnostic[0], 0.0)
        self.assertEqual(diagnostic[-1], self.params.forty_period_end)
        self.assertTrue(np.all(np.diff(diagnostic) > 0.0))
        np.testing.assert_allclose(np.diff(diagnostic[:-1]), 0.01, atol=2e-14)

    def test_05_initial_acceleration_and_zero_excitation(self) -> None:
        derivative = state_rhs(0.0, np.zeros(8), self.params)
        np.testing.assert_allclose(
            derivative,
            [
                0.0,
                0.6174854229334086,
                0.0,
                0.0,
                0.0,
                0.10060644414367718,
                0.0,
                0.22259516294978385,
            ],
            rtol=0.0,
            atol=2e-12,
        )
        times = np.linspace(0.0, 0.5 * self.params.period, 51)
        solution = solve_response(
            self.params,
            (0.0, times[-1]),
            times,
            excitation_scale=0.0,
        )
        np.testing.assert_array_equal(solution.y, np.zeros_like(solution.y))

    def test_06_pto_and_radiation_powers_are_nonnegative(self) -> None:
        rng = np.random.default_rng(202208)
        for time in np.linspace(0.0, self.params.period, 21):
            state = rng.normal(size=8)
            powers = instantaneous_powers(time, state, self.params)
            self.assertGreaterEqual(float(np.min(powers[1:])), 0.0)

    def test_07_energy_quadratic_forms_match_expansion(self) -> None:
        rng = np.random.default_rng(202209)
        for _ in range(20):
            state = rng.normal(size=8)
            qz = state[[0, 2]]
            vz = state[[1, 3]]
            qt = state[[4, 6]]
            vt = state[[5, 7]]
            mz, _, kz = heave_matrices(self.params)
            mt, _, kt = pitch_matrices(self.params)
            expanded = 0.5 * (
                vz @ mz @ vz
                + vt @ mt @ vt
                + qz @ kz @ qz
                + qt @ kt @ qt
            )
            self.assertAlmostEqual(
                mechanical_energy(state, self.params), expanded, places=8
            )

    def test_08_matrix_exponential_matches_short_integration(self) -> None:
        times = np.linspace(0.0, 2.0 * self.params.period, 81)
        numerical = solve_response(
            self.params,
            (0.0, times[-1]),
            times,
            rtol=2e-12,
            atol=2e-14,
            max_step=0.0025,
        ).y
        analytic = matrix_exponential_response(times, self.params)
        difference = np.max(np.abs(numerical - analytic), axis=1)
        np.testing.assert_array_less(
            difference,
            np.array([2e-10, 2e-10, 2e-10, 2e-10, 2e-11, 2e-11, 2e-11, 2e-11]),
        )

    def test_09_short_time_step_convergence(self) -> None:
        times = np.linspace(0.0, 2.0 * self.params.period, 401)
        standard = solve_response(
            self.params,
            (0.0, times[-1]),
            times,
            rtol=1e-10,
            max_step=0.01,
        )
        reference = solve_response(
            self.params,
            (0.0, times[-1]),
            times,
            rtol=2e-12,
            atol=2e-14,
            max_step=0.0025,
        )
        difference = np.max(np.abs(standard.y - reference.y), axis=1)
        scales = np.maximum(
            np.max(np.abs(reference.y), axis=1),
            np.array([1e-3] * 4 + [1e-4] * 4),
        )
        self.assertLess(float(np.max(difference / scales)), 5e-8)

    def test_10_short_time_energy_balance(self) -> None:
        times = np.linspace(0.0, 2.0 * self.params.period, 1201)
        solution = solve_response(
            self.params,
            (0.0, times[-1]),
            times,
            track_energy=True,
        )
        energies = np.array(
            [mechanical_energy(solution.y[:8, index], self.params) for index in range(times.size)]
        )
        input_work = solution.y[8]
        losses = solution.y[9:13]
        residual = energies - input_work + np.sum(losses, axis=0)
        scale = max(
            1.0,
            float(np.max(np.abs(energies))),
            float(np.max(np.abs(input_work))),
            float(np.max(np.sum(losses, axis=0))),
        )
        self.assertLess(float(np.max(np.abs(residual))) / scale, 1e-8)
        self.assertGreaterEqual(float(np.min(losses)), -1e-10)
        self.assertGreaterEqual(float(np.min(np.diff(losses, axis=1))), -1e-9)

    def test_11_both_shell_conventions_integrate(self) -> None:
        times = np.linspace(0.0, self.params.period, 101)
        for convention in FloatShellConvention:
            params = replace(self.params, shell_convention=convention)
            solution = solve_response(params, (0.0, times[-1]), times)
            self.assertTrue(np.all(np.isfinite(solution.y)))
            self.assertGreater(float(np.max(np.abs(solution.y))), 0.0)

    def test_12_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            replace(self.params, linear_spring_stiffness=1000.0)
        with self.assertRaises(TypeError):
            replace(self.params, shell_convention="sealed_with_top")
        with self.assertRaises(ValueError):
            diagnostic_time_grid(self.params, step=0.0)
        with self.assertRaises(ValueError):
            state_rhs(0.0, np.zeros(7), self.params)
        with self.assertRaises(ValueError):
            matrix_exponential_response([-1.0], self.params)


if __name__ == "__main__":
    unittest.main(verbosity=2)
