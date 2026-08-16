"""问题四频域功率计算器基础自动测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from common.q4_power import (  # noqa: E402
    RELATIVE_VECTOR,
    axis_data,
    axis_mean_power,
    constrained_analytic_optimum,
    q4_parameters,
    total_mean_power,
    unconstrained_optimal_damping,
)


class Q4CalculatorVerification(unittest.TestCase):
    def setUp(self) -> None:
        self.params = q4_parameters()

    def test_01_case_four_parameters(self) -> None:
        expected = (1.9806, 1091.099, 7142.493, 528.5018, 1655.909, 1760.0, 2140.0)
        actual = (
            self.params.wave_omega,
            self.params.added_mass,
            self.params.added_rotational_inertia,
            self.params.heave_radiation_damping,
            self.params.pitch_radiation_damping,
            self.params.excitation_force_amplitude,
            self.params.excitation_moment_amplitude,
        )
        np.testing.assert_allclose(actual, expected, rtol=0.0, atol=0.0)

    def test_02_axis_matrices_are_symmetric_positive(self) -> None:
        for axis in ("heave", "pitch"):
            mass, damping, stiffness, forcing = axis_data(axis, self.params)
            np.testing.assert_allclose(mass, mass.T, rtol=0.0, atol=1e-13)
            np.testing.assert_allclose(stiffness, stiffness.T, rtol=0.0, atol=1e-13)
            self.assertGreater(np.min(np.linalg.eigvalsh(mass)), 0.0)
            self.assertGreater(np.min(np.linalg.eigvalsh(stiffness)), 0.0)
            self.assertGreaterEqual(np.min(np.linalg.eigvalsh(damping)), 0.0)
            self.assertGreater(forcing[0], 0.0)
            self.assertEqual(forcing[1], 0.0)

    def test_03_zero_damping_gives_zero_pto_power(self) -> None:
        self.assertEqual(axis_mean_power("heave", 0.0, self.params).mean_power, 0.0)
        self.assertEqual(axis_mean_power("pitch", 0.0, self.params).mean_power, 0.0)

    def test_04_total_power_is_exactly_separable(self) -> None:
        for linear, rotational in ((0.0, 0.0), (25000.0, 75000.0), (100000.0, 100000.0)):
            expected = (
                axis_mean_power("heave", linear, self.params).mean_power
                + axis_mean_power("pitch", rotational, self.params).mean_power
            )
            self.assertEqual(total_mean_power(linear, rotational, self.params), expected)

    def test_05_phasor_dynamic_residuals_are_small(self) -> None:
        for axis, damping in (("heave", 59152.9), ("pitch", 100000.0)):
            result = axis_mean_power(axis, damping, self.params)
            scale = axis_data(axis, self.params)[3][0]
            self.assertLess(result.dynamic_residual / scale, 1e-11)

    def test_06_power_matches_period_quadrature(self) -> None:
        time = np.linspace(0.0, self.params.period, 20001)
        phase = np.exp(1j * self.params.wave_omega * time)
        for axis, damping in (("heave", 42000.0), ("pitch", 83000.0)):
            result = axis_mean_power(axis, damping, self.params)
            relative_velocity = np.real(
                1j
                * self.params.wave_omega
                * complex(RELATIVE_VECTOR @ result.displacement_phasor)
                * phase
            )
            quadrature = np.trapezoid(damping * relative_velocity**2, time) / self.params.period
            self.assertAlmostEqual(quadrature, result.mean_power, places=10)

    def test_07_heave_analytic_optimum_is_interior_and_local_maximum(self) -> None:
        optimum = unconstrained_optimal_damping("heave", self.params)
        self.assertGreater(optimum, 0.0)
        self.assertLess(optimum, 100000.0)
        center = axis_mean_power("heave", optimum, self.params).mean_power
        self.assertGreater(center, axis_mean_power("heave", optimum - 10.0, self.params).mean_power)
        self.assertGreater(center, axis_mean_power("heave", optimum + 10.0, self.params).mean_power)

    def test_08_pitch_constraint_is_active(self) -> None:
        unconstrained = unconstrained_optimal_damping("pitch", self.params)
        self.assertGreater(unconstrained, 100000.0)
        constrained = constrained_analytic_optimum("pitch", self.params)
        self.assertEqual(constrained.damping, 100000.0)
        self.assertGreater(constrained.mean_power, axis_mean_power("pitch", 99990.0, self.params).mean_power)

    def test_09_expected_optimum_scale(self) -> None:
        heave = constrained_analytic_optimum("heave", self.params)
        pitch = constrained_analytic_optimum("pitch", self.params)
        self.assertAlmostEqual(heave.damping, 59152.91611296622, places=7)
        self.assertAlmostEqual(heave.mean_power, 318.336439591652, places=9)
        self.assertAlmostEqual(pitch.mean_power, 0.3428168749606963, places=12)

    def test_10_invalid_inputs_are_rejected(self) -> None:
        for value in (-1.0, 100001.0, np.nan, np.inf):
            with self.assertRaises(ValueError):
                axis_mean_power("heave", value, self.params)
        with self.assertRaises(ValueError):
            axis_data("invalid", self.params)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main(verbosity=2)
