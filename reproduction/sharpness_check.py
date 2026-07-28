#!/usr/bin/env python3
"""Exact and seeded checks of the paper's unit-slack extremizer."""

from __future__ import annotations

import json
import hashlib
import math
import random
import sys
from fractions import Fraction


def wilson(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    p = successes / trials
    den = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / den
    radius = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / den
    return center - radius, center + radius


def simulate_coordinatewise(n: int, trials: int, rng: random.Random) -> int:
    """Simulate Xi=n+1 with probability 1/(n+1), checking S<n+1."""
    good = 0
    low_probability = n / (n + 1)
    for _ in range(trials):
        all_zero = True
        for _ in range(n):
            if rng.random() >= low_probability:
                all_zero = False
                break
        good += int(all_zero)
    return good


def main() -> None:
    seed = int(sys.argv[1])
    trials = int(sys.argv[2])
    ns = [int(value) for value in sys.argv[3].split(",")]
    rng = random.Random(seed)
    rows = []
    max_abs_z = 0.0

    for n in ns:
        exact = Fraction(n, n + 1) ** n
        successes = simulate_coordinatewise(n, trials, rng)
        observed = successes / trials
        expected = float(exact)
        se = math.sqrt(expected * (1 - expected) / trials)
        z_score = (observed - expected) / se
        ci_low, ci_high = wilson(successes, trials)
        max_abs_z = max(max_abs_z, abs(z_score))
        row = {
            "n": n,
            "coordinate_mean": "1",
            "threshold": n + 1,
            "exact_fraction": f"{exact.numerator}/{exact.denominator}",
            "exact_probability": expected,
            "observed_probability": observed,
            "successes": successes,
            "trials": trials,
            "z_score": z_score,
            "wilson95_low": ci_low,
            "wilson95_high": ci_high,
            "exact_in_wilson95": ci_low <= expected <= ci_high,
        }
        rows.append(row)
        print("SHARPNESS_ROW " + json.dumps(row, sort_keys=True))

    exact_grid_lines = []
    exact_first = None
    exact_last = None
    for n in range(1, 513):
        exact = Fraction(n, n + 1) ** n
        line = f"{n},{exact.numerator},{exact.denominator}"
        exact_grid_lines.append(line)
        if n == 1:
            exact_first = line
        exact_last = line

    summary = {
        "claim": "P(S < E[S] + 1) = (n/(n+1))^n for the Bernoulli extremizer",
        "seed": seed,
        "trials_per_n": trials,
        "simulated_n": ns,
        "exact_grid_n": [1, 512],
        "exact_grid_rows": len(exact_grid_lines),
        "exact_grid_sha256": hashlib.sha256(
            ("\n".join(exact_grid_lines) + "\n").encode("ascii")
        ).hexdigest(),
        "exact_grid_first": exact_first,
        "exact_grid_last_probability": float(Fraction(512, 513) ** 512),
        "exact_grid_last_num_digits": len(exact_last.split(",")[1]),
        "exact_grid_last_den_digits": len(exact_last.split(",")[2]),
        "all_exact_inside_wilson95": all(row["exact_in_wilson95"] for row in rows),
        "max_abs_z": max_abs_z,
        "rows": rows,
    }
    print("SHARPNESS_SUMMARY " + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
