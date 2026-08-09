"""Placeholder for problem 1.

Replace this file with the final contest code. Keep inputs, outputs, and
random seeds clear so the appendix can reproduce the paper results.
"""

from __future__ import annotations

import numpy as np


def solve_q1(data: np.ndarray) -> np.ndarray:
    """Return a simple baseline statistic for the template."""
    return np.mean(data, axis=0)


if __name__ == "__main__":
    demo = np.array([[1.0, 2.0], [3.0, 4.0]])
    print(solve_q1(demo))
