"""Placeholder for problem 3.

Replace this file with final scheme generation and sensitivity analysis code.
"""

from __future__ import annotations


def sensitivity_check(base_value: float, ratio: float = 0.1) -> tuple[float, float, float]:
    """Return low, baseline, and high perturbation values."""
    return base_value * (1 - ratio), base_value, base_value * (1 + ratio)


if __name__ == "__main__":
    print(sensitivity_check(100.0))
