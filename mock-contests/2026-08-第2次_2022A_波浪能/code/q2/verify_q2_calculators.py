"""问题二平均功率计算器的自动验证；不执行最优参数搜索。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q2_power import (  # noqa: E402
    constant_mean_power,
    constant_system_matrices,
    periodic_mean_power,
    pto_power,
    q2_parameters,
    sample_period_from_state,
    shooting_mean_power,
)


class Q2PowerCalculatorVerification(unittest.TestCase):
    """验证问题二参数、频域公式和周期功率积分。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.params = q2_parameters()

    def test_q2_parameters(self) -> None:
        self.assertAlmostEqual(self.params.effective_float_mass, 6031.992, places=12)
        self.assertAlmostEqual(self.params.wave_omega, 2.2143, places=12)
        self.assertAlmostEqual(self.params.period, 2.83754925131174, places=12)
        self.assertAlmostEqual(self.params.radiation_damping, 167.8395, places=12)
        self.assertAlmostEqual(self.params.excitation_amplitude, 4890.0, places=12)

    def test_constant_dynamic_equilibrium(self) -> None:
        for damping in (0.0, 10000.0, 50000.0, 100000.0):
            result = constant_mean_power(damping, self.params)
            self.assertLess(result.dynamic_residual_norm, 1e-8)
            self.assertGreaterEqual(result.mean_power, 0.0)
        self.assertEqual(constant_mean_power(0.0, self.params).mean_power, 0.0)

    def test_constant_matrices_are_symmetric(self) -> None:
        mass, damping, stiffness = constant_system_matrices(10000.0, self.params)
        np.testing.assert_allclose(mass, mass.T, atol=0.0)
        np.testing.assert_allclose(damping, damping.T, atol=0.0)
        np.testing.assert_allclose(stiffness, stiffness.T, atol=0.0)
        self.assertTrue(np.all(np.linalg.eigvalsh(mass) > 0.0))
        self.assertTrue(np.all(np.linalg.eigvalsh(damping) > 0.0))
        self.assertTrue(np.all(np.linalg.eigvalsh(stiffness) > 0.0))

    def test_pto_power_is_nonnegative(self) -> None:
        velocities = np.linspace(-4.0, 4.0, 2001)
        for coefficient, exponent in ((10000.0, 0.0), (10000.0, 0.5), (80000.0, 1.0)):
            powers = pto_power(velocities, coefficient, exponent)
            self.assertGreaterEqual(float(np.min(powers)), -1e-14)

    def test_zero_coefficient_boundary(self) -> None:
        for exponent in (0.0, 0.5, 1.0):
            result = periodic_mean_power(0.0, exponent, self.params)
            self.assertEqual(result.mean_power, 0.0)
            self.assertEqual(result.cycles, 0)

    def test_p_zero_matches_frequency_domain(self) -> None:
        damping = 10000.0
        frequency = constant_mean_power(damping, self.params)
        periodic = periodic_mean_power(
            damping,
            0.0,
            self.params,
            convergence_tolerance=1e-10,
            required_consecutive_cycles=4,
            rtol=1e-10,
            atol=1e-12,
        )
        relative_error = abs(periodic.mean_power - frequency.mean_power) / frequency.mean_power
        self.assertLess(relative_error, 1e-8)
        self.assertLessEqual(periodic.convergence_error, 1e-10)

    def test_nonlinear_sample_converges(self) -> None:
        result = periodic_mean_power(
            10000.0,
            0.5,
            self.params,
            convergence_tolerance=1e-9,
            required_consecutive_cycles=3,
        )
        self.assertGreater(result.mean_power, 0.0)
        self.assertLessEqual(result.convergence_error, 1e-9)
        self.assertGreaterEqual(result.cycles, 8)
        shooting = shooting_mean_power(10000.0, 0.5, self.params)
        relative_error = abs(shooting.mean_power - result.mean_power) / result.mean_power
        self.assertLess(relative_error, 2e-7)
        self.assertLessEqual(shooting.periodicity_error, 1e-7)

    def test_shooting_p_zero_matches_frequency_domain(self) -> None:
        damping = 10000.0
        frequency = constant_mean_power(damping, self.params)
        shooting = shooting_mean_power(damping, 0.0, self.params)
        relative_error = abs(shooting.mean_power - frequency.mean_power) / frequency.mean_power
        self.assertLess(relative_error, 1e-10)
        self.assertLess(shooting.periodicity_error, 1e-10)

    def test_augmented_energy_matches_dense_quadrature(self) -> None:
        coefficient, exponent = 10000.0, 0.5
        result = periodic_mean_power(
            coefficient,
            exponent,
            self.params,
            convergence_tolerance=1e-10,
            required_consecutive_cycles=4,
            rtol=1e-10,
            atol=1e-12,
        )
        times, _, power = sample_period_from_state(
            result.periodic_state,
            coefficient,
            exponent,
            self.params,
            samples=4001,
        )
        quadrature_mean = float(np.trapezoid(power, times) / self.params.period)
        relative_error = abs(quadrature_mean - result.mean_power) / result.mean_power
        self.assertLess(relative_error, 2e-8)

    def test_invalid_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            constant_mean_power(-1.0, self.params)
        with self.assertRaises(ValueError):
            periodic_mean_power(1000.0, 1.1, self.params)
        with self.assertRaises(ValueError):
            periodic_mean_power(100001.0, 0.5, self.params)
        with self.assertRaises(ValueError):
            shooting_mean_power(1000.0, 0.5, self.params, root_tolerance=0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
