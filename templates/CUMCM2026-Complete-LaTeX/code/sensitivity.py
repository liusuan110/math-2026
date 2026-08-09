"""Sensitivity and robustness placeholders.

Use this file for parameter perturbation, Monte Carlo robustness checks, and
convergence diagnostics. Keep generated figures under ../figures/.
"""

from __future__ import annotations

import numpy as np


def perturb_values(base_value: float, ratios: np.ndarray | None = None) -> np.ndarray:
    """Return values after relative perturbation."""
    if ratios is None:
        ratios = np.array([-0.1, 0.0, 0.1])
    return base_value * (1 + ratios)


def monte_carlo_demo(base_value: float, n_runs: int = 100, noise_scale: float = 0.01) -> np.ndarray:
    """Generate a reproducible Monte Carlo sample for the template."""
    rng = np.random.default_rng(42)
    noise = rng.normal(loc=0.0, scale=noise_scale, size=n_runs)
    return base_value * (1 + noise)


if __name__ == "__main__":
    print(perturb_values(100.0))
    print(monte_carlo_demo(100.0)[:5])
