#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for the Wilson *power* contract on ``util/soak_ledger.py``.

``tests/test_soak_ledger.py`` pins the interval at an observed rate (and that
``wilson(0, 0)`` is None). The 2026-09-04 consensus review of the per-probe
handoff (ml#1694 round 2) overturned the reconciler on a different quantity:
power over the sampling distribution. Inside the handoff's own ``n≈8–10`` band,
Wilson's low-side resolving threshold is ``k ≤ 1`` at n=8, 9 **and** 10, and
loosens to ``k ≤ 2`` only at n=11. Runs 9 and 10 therefore add trials against
an unchanged cap, and power at P21's observed rate (0.25) *falls*.

A campaign planned on "n=10 is tighter than n=8" (true of the interval, false
of power) spends billed sessions that strictly reduce the chance of an answer.
``binom_sf`` is the production estimator for that power (and for area-systematic
escalation) and had no direct tests.

``util/`` is outside every pre-commit Python hook, so this suite is the gate.
Hermetic: no ledger I/O. A test must be able to fail for the reason it exists.
"""

from __future__ import annotations

import importlib.util
import math
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "util" / "soak_ledger.py"

_spec = importlib.util.spec_from_file_location("soak_ledger", MODULE_PATH)
assert _spec and _spec.loader
sl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sl)

# A probe "resolves" on the low side when the Wilson *upper* bound drops below
# 50% — the CI no longer spans the 50% the handoff treated as unsettled.
LOW_SIDE = 0.50


def low_side_resolving_k(n: int, boundary: float = LOW_SIDE) -> int:
    """Largest k such that Wilson upper(k, n) < boundary. -1 if none resolve."""
    found = -1
    for k in range(n + 1):
        _lo, hi = sl.wilson(k, n)
        if hi is not None and hi < boundary:
            found = k
    return found


def resolve_power(n: int, p: float, boundary: float = LOW_SIDE) -> float:
    """P(resolve) at true rate p = P(X <= k*), X ~ Bin(n, p)."""
    k_star = low_side_resolving_k(n, boundary)
    if k_star < 0:
        return 0.0
    return 1.0 - sl.binom_sf(k_star + 1, n, p)


class LowSideResolvingThreshold(unittest.TestCase):
    """The table that made n=10 worse than n=8. Interval tightness is the wrong quantity."""

    def test_threshold_is_one_across_the_handoff_band(self) -> None:
        # THE pin. k<=1 at n=8, 9 AND 10. A "<=" that loosened at n=9 would
        # certify the handoff's n≈8-10 campaign as power-increasing.
        for n in (8, 9, 10):
            self.assertEqual(low_side_resolving_k(n), 1, n)
            _lo, hi_at_cap = sl.wilson(1, n)
            _lo, hi_above = sl.wilson(2, n)
            self.assertLess(hi_at_cap, LOW_SIDE, n)
            self.assertGreaterEqual(hi_above, LOW_SIDE, n)

    def test_threshold_loosens_only_at_n_eleven(self) -> None:
        self.assertEqual(low_side_resolving_k(11), 2)
        self.assertLess(sl.wilson(2, 11)[1], LOW_SIDE)
        self.assertGreaterEqual(sl.wilson(3, 11)[1], LOW_SIDE)

    def test_n_five_through_seven_cannot_resolve_once_k_is_one(self) -> None:
        # P21 already has k=1. Threshold here is k<=0, so P(resolve)=0 exactly
        # no matter what the remaining trials do.
        for n in (5, 6, 7):
            self.assertEqual(low_side_resolving_k(n), 0, n)
            self.assertGreaterEqual(sl.wilson(1, n)[1], LOW_SIDE, n)


class PowerFallsInsideTheHandoffBand(unittest.TestCase):
    """Published power table. A monotonic-increase rewrite of resolve_power must fail."""

    def test_power_at_p21_falls_then_jumps(self) -> None:
        # P21 observed p=0.25. n=8 is the ONLY value in the handoff band that
        # can resolve it at all; each further session reduces the chance until n=11.
        got = {n: resolve_power(n, 0.25) for n in (8, 9, 10, 11)}
        self.assertAlmostEqual(got[8], 0.3671, places=4)
        self.assertAlmostEqual(got[9], 0.3003, places=4)
        self.assertAlmostEqual(got[10], 0.2440, places=4)
        self.assertAlmostEqual(got[11], 0.4552, places=4)
        self.assertLess(got[9], got[8])
        self.assertLess(got[10], got[9])
        self.assertGreater(got[11], got[8])

    def test_same_shape_at_neighbouring_rates(self) -> None:
        # The fall-then-jump is not a p=0.25 curiosity. Published at 0.20 and ~1/3.
        for p, expected in (
            (0.20, (0.5033, 0.4362, 0.3758, 0.6174)),
            (1.0 / 3.0, (0.1951, 0.1431, 0.1040, 0.2341)),
        ):
            got = tuple(round(resolve_power(n, p), 4) for n in (8, 9, 10, 11))
            self.assertEqual(got, expected, p)
            self.assertLess(got[1], got[0], p)
            self.assertLess(got[2], got[1], p)
            self.assertGreater(got[3], got[0], p)


class BoundaryPrintPrecision(unittest.TestCase):
    """Round 2: a 4-decimal print cannot decide the side of 26/42, and 27/49 still fails."""

    def test_twenty_six_of_forty_two_is_not_terminal_by_parts_per_million(self) -> None:
        # +2 non-follow on main's 26/40. Printed at 4dp this is "0.7500", from
        # which a reader cannot tell which side of DECISION_BOUNDARY it falls on.
        # It is NOT terminal: clearance is 2.7e-06 and the predicate is strict <.
        _lo, hi = sl.wilson(26, 42)
        self.assertAlmostEqual(hi, 0.750002742, places=9)
        self.assertGreater(hi - sl.DECISION_BOUNDARY, 2e-6)
        self.assertLess(hi - sl.DECISION_BOUNDARY, 4e-6)
        self.assertEqual(f"{hi:.4f}", "0.7500")
        self.assertGreaterEqual(hi, sl.DECISION_BOUNDARY)

    def test_naive_twenty_seven_of_forty_nine_is_still_bet_failing(self) -> None:
        # Keying mutations on their own obs_id inflates n to 49 and follow to 27.
        # That silently destroys the 95.3% retention headline. It does NOT flip
        # the verdict — upper 0.6815 is still under the boundary. A reducer that
        # leaves the alarming number intact and rewrites the reassuring one is
        # the harder failure to notice.
        _lo, hi = sl.wilson(27, 49)
        self.assertAlmostEqual(hi, 0.6815, places=4)
        self.assertLess(hi, sl.DECISION_BOUNDARY)


class BinomSfIsTheLedgersEstimator(unittest.TestCase):
    """Direct pins. analyse() covers the area rule, not these edges."""

    def test_k_le_zero_is_certainty(self) -> None:
        self.assertEqual(sl.binom_sf(0, 10, 0.5), 1.0)
        self.assertEqual(sl.binom_sf(-1, 10, 0.5), 1.0)

    def test_k_gt_n_is_impossible(self) -> None:
        self.assertEqual(sl.binom_sf(11, 10, 0.5), 0.0)

    def test_matches_a_direct_binomial_sum(self) -> None:
        # P(X >= 2) for Bin(8, 0.25). Off-by-one (P(X > k) vs P(X >= k))
        # flips the power table by one mass point and would recertify n=10.
        expected = sum(math.comb(8, i) * (0.25**i) * (0.75 ** (8 - i)) for i in range(2, 9))
        self.assertAlmostEqual(sl.binom_sf(2, 8, 0.25), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
