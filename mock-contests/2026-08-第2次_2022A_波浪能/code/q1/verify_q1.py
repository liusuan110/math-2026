r"""问题一公共动力学模块的自动验证。

运行方式：
    .venv\Scripts\python.exe code\q1\verify_q1.py

此脚本只做短时核验，不生成正式 40 周期结果。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q1_dynamics import (  # noqa: E402
    DampingLaw,
    Q1Parameters,
    constant_system_matrices,
    coupling_forces,
    damping_force,
    mechanical_energy,
    output_time_grid,
    solve_response,
    state_rhs,
)


class Q1DynamicsVerification(unittest.TestCase):
    """对公式装配、耗散性质和短时积分精度进行自动检查。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.params = Q1Parameters()

    def test_derived_parameters(self) -> None:
        self.assertAlmostEqual(self.params.effective_float_mass, 6201.535, places=12)
        self.assertAlmostEqual(
            self.params.hydrostatic_stiffness, 31557.29820530947, places=9
        )
        self.assertAlmostEqual(self.params.period, 4.486387223976855, places=12)
        self.assertAlmostEqual(
            self.params.static_cylinder_draft, 2.0000102691923463, places=12
        )
        self.assertAlmostEqual(
            self.params.spring_equilibrium_length, 0.2019575, places=12
        )

    def test_initial_acceleration(self) -> None:
        expected_float = 6250.0 / 6201.535
        for law in DampingLaw:
            derivative = state_rhs(0.0, np.zeros(4), self.params, law)
            np.testing.assert_allclose(
                derivative,
                [0.0, expected_float, 0.0, 0.0],
                rtol=0.0,
                atol=1e-14,
            )

    def test_zero_excitation_preserves_equilibrium(self) -> None:
        times = np.linspace(0.0, 2.0 * self.params.period, 101)
        for law in DampingLaw:
            solution = solve_response(
                self.params,
                law,
                (0.0, times[-1]),
                times,
                excitation_scale=0.0,
            )
            np.testing.assert_array_equal(solution.y, np.zeros_like(solution.y))

    def test_internal_forces_are_equal_and_opposite(self) -> None:
        sample_states = [(-0.4, -1.2), (0.0, 0.0), (0.7, 2.1), (1.3, -0.6)]
        for law in DampingLaw:
            for displacement, velocity in sample_states:
                force_float, force_oscillator = coupling_forces(
                    displacement, velocity, law, self.params
                )
                self.assertAlmostEqual(force_float + force_oscillator, 0.0, places=12)

    def test_pto_always_dissipates_energy(self) -> None:
        velocities = np.linspace(-5.0, 5.0, 1001)
        for law in DampingLaw:
            powers = damping_force(velocities, law, self.params) * velocities
            self.assertGreaterEqual(float(np.min(powers)), -1e-14)

    def test_constant_matrices_are_physically_admissible(self) -> None:
        mass, damping, stiffness = constant_system_matrices(self.params)
        np.testing.assert_allclose(mass, mass.T, atol=0.0)
        np.testing.assert_allclose(damping, damping.T, atol=0.0)
        np.testing.assert_allclose(stiffness, stiffness.T, atol=0.0)
        self.assertTrue(np.all(np.linalg.eigvalsh(mass) > 0.0))
        self.assertTrue(np.all(np.linalg.eigvalsh(damping) > 0.0))
        self.assertTrue(np.all(np.linalg.eigvalsh(stiffness) > 0.0))

    def test_output_grid(self) -> None:
        times = output_time_grid(self.params)
        self.assertEqual(times.size, 898)
        self.assertAlmostEqual(times[0], 0.0, places=15)
        self.assertAlmostEqual(times[-1], 179.4, places=12)
        np.testing.assert_allclose(np.diff(times), 0.2, rtol=0.0, atol=3e-14)
        for requested_time in (10.0, 20.0, 40.0, 60.0, 100.0):
            matches = np.flatnonzero(np.isclose(times, requested_time, atol=1e-13))
            self.assertEqual(matches.size, 1)

    def test_short_time_energy_balance(self) -> None:
        times = np.linspace(0.0, 2.0 * self.params.period, 1201)
        for law in DampingLaw:
            solution = solve_response(
                self.params,
                law,
                (0.0, times[-1]),
                times,
                track_energy=True,
            )
            energies = np.array(
                [mechanical_energy(solution.y[:4, i], self.params) for i in range(times.size)]
            )
            wave_work, radiation_loss, pto_loss = solution.y[4:7]
            residual = energies - wave_work + radiation_loss + pto_loss
            scale = np.maximum(
                1.0,
                np.abs(energies)
                + np.abs(wave_work)
                + np.abs(radiation_loss)
                + np.abs(pto_loss),
            )
            relative_residual = np.max(np.abs(residual) / scale)
            self.assertLess(relative_residual, 1e-9)

    def test_short_time_step_convergence(self) -> None:
        times = np.linspace(0.0, 2.0 * self.params.period, 301)
        for law in DampingLaw:
            standard = solve_response(
                self.params,
                law,
                (0.0, times[-1]),
                times,
                rtol=1e-10,
                atol=1e-12,
                max_step=0.02,
            )
            reference = solve_response(
                self.params,
                law,
                (0.0, times[-1]),
                times,
                rtol=1e-12,
                atol=1e-14,
                max_step=0.01,
            )
            max_difference = float(np.max(np.abs(standard.y - reference.y)))
            self.assertLess(max_difference, 1e-7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
