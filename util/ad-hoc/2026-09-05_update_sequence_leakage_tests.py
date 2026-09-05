#!/usr/bin/env python3
"""Extend the sequence-windowing leakage property tests to three partitions.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3b)

These are the invariant tests (I1-I5 / RR1-RR5 / TR1-TR5) that exist so a future
vectorized rewrite cannot silently reintroduce a leak. With ``val`` carved
between train and test, the no-future-leak invariant has to become TRANSITIVE:
asserting only ``train < test`` would leave the validation split free to overlap
either neighbour -- and the validation split is the one early stopping reads, so
an overlap there is the most consequential leak of the three.

The ``full == train + test`` identities (RR4 and its timed sibling) are R-5 in
its most literal form: they are correct today and false the moment ``val``
exists.
"""

from __future__ import annotations

import pathlib
import sys

PATH = pathlib.Path(
    "/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--sequence-val-split--20260905-0228--4b9f4b94/juniper_data/tests/unit/test_sequence_windowing_leakage.py"
)

EDITS: list[tuple[str, str, int]] = [
    # Hypothesis strategies gain a val_ratio, bounded so train + val < 1.
    (
        "    train_ratio=st.floats(0.5, 0.95),\n",
        "    train_ratio=st.floats(0.5, 0.8),\n    val_ratio=st.floats(0.05, 0.15),\n",
        2,
    ),
    (
        "def test_regular_windowing_invariants(n_steps, lookback, horizon, sample_dt, train_ratio):",
        "def test_regular_windowing_invariants(n_steps, lookback, horizon, sample_dt, train_ratio, val_ratio):",
        1,
    ),
    (
        "def test_timed_windowing_invariants(n_steps, lookback, horizon, gaps, train_ratio):",
        "def test_timed_windowing_invariants(n_steps, lookback, horizon, gaps, train_ratio, val_ratio):",
        1,
    ),
    # Three windows are needed for a non-empty three-way split, not two.
    (
        "    if n_steps - lookback - horizon + 1 < 2:\n        return  # too short for two windows; the windower raises (covered in the unit tests)",
        "    if n_steps - lookback - horizon + 1 < 3:\n        return  # too short for a three-way split; the windower raises (covered in the unit tests)",
        2,
    ),
    (
        "out = window_regular_series(series, lookback=lookback, horizon=horizon, sample_dt=sample_dt, train_ratio=train_ratio)",
        "out = window_regular_series(series, lookback=lookback, horizon=horizon, sample_dt=sample_dt, train_ratio=train_ratio, val_ratio=val_ratio)",
        1,
    ),
    (
        "out = window_timed_series(values, times, lookback=lookback, horizon=horizon, train_ratio=train_ratio)",
        "out = window_timed_series(values, times, lookback=lookback, horizon=horizon, train_ratio=train_ratio, val_ratio=val_ratio)",
        1,
    ),
    # RR4 / RR5: the identity and the leak check both span three partitions.
    (
        '    # RR4 -- full == train + test, chronological.\n'
        '    assert n_windows == out["X_train"].shape[0] + out["X_test"].shape[0]\n'
        '    np.testing.assert_array_equal(out["X_full"], np.concatenate([out["X_train"], out["X_test"]]))\n'
        '\n'
        '    # RR5 -- no future leak: every train target strictly precedes every test target.\n'
        '    if out["y_train"].shape[0] and out["y_test"].shape[0]:\n'
        '        assert out["y_train"][:, 0].max() < out["y_test"][:, 0].min()',
        '    # RR4 -- full == train + val + test, chronological. The identity spans THREE\n'
        '    # partitions now; over train + test alone it would pass only while val is empty.\n'
        '    assert out["X_val"].shape[0] > 0, "X_val must be non-empty, or RR4/RR5 hold vacuously"\n'
        '    assert n_windows == out["X_train"].shape[0] + out["X_val"].shape[0] + out["X_test"].shape[0]\n'
        '    np.testing.assert_array_equal(out["X_full"], np.concatenate([out["X_train"], out["X_val"], out["X_test"]]))\n'
        '\n'
        '    # RR5 -- no future leak, TRANSITIVE: train targets precede val targets, which\n'
        '    # precede test targets. Values encode their step index, so a plain max/min\n'
        '    # comparison is exactly the chronological ordering.\n'
        '    for earlier, later in (("train", "val"), ("val", "test"), ("train", "test")):\n'
        '        if out[f"y_{earlier}"].shape[0] and out[f"y_{later}"].shape[0]:\n'
        '            assert out[f"y_{earlier}"][:, 0].max() < out[f"y_{later}"][:, 0].min()',
        1,
    ),
]


def main() -> int:
    src = PATH.read_text()
    for old, new, expected in EDITS:
        found = src.count(old)
        if found != expected:
            print(f"pattern matched {found}x, expected {expected} -- refusing:\n{old[:110]}", file=sys.stderr)
            return 1
        src = src.replace(old, new)
    PATH.write_text(src)
    print("test_sequence_windowing_leakage.py updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
