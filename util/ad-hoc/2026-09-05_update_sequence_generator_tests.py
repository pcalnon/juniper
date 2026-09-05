#!/usr/bin/env python3
"""Update the sequence + equities generator tests for the three-way split.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3b)

Three mechanical classes:

* windower call sites gain ``val_ratio`` / ``val_cut_ordinal`` (the error-path
  tests, which pass explicit ratios);
* ``full == train + test`` identity assertions become three-way (R-5 again);
* ``EquitiesParams`` fixtures that set ``train_ratio`` + ``test_ratio`` summing
  to 1.0 now over-subscribe against the 0.1 ``val_ratio`` default, so they state
  the validation share explicitly.
"""

from __future__ import annotations

import pathlib
import re
import sys

BASE = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--sequence-val-split--20260905-0228--4b9f4b94/juniper_data/tests/unit")

# (filename, pattern, replacement, expected count). None count = "one or more".
EDITS: list[tuple[str, str, str, int | None]] = [
    # Error-path windower calls: give them the third partition's share.
    ("test_sequence_windowing_leakage.py", "sample_dt=1.0, train_ratio=0.5)", "sample_dt=1.0, train_ratio=0.5, val_ratio=0.25)", None),
    ("test_sequence_windowing_leakage.py", "horizon=1, train_ratio=0.5)", "horizon=1, train_ratio=0.5, val_ratio=0.25)", None),
    ("test_sequence_windowing_leakage.py", "horizon=0, train_ratio=0.5)", "horizon=0, train_ratio=0.5, val_ratio=0.25)", None),
    ("test_sequence_windowing_leakage.py", "lookback=0, horizon=1, train_ratio=0.5)", "lookback=0, horizon=1, train_ratio=0.5, val_ratio=0.25)", None),
    ("test_sequence_windowing_leakage.py", "lookback=0, cut_ordinal=0)", "lookback=0, cut_ordinal=0, val_cut_ordinal=0)", None),
    ("test_sequence_windowing_leakage.py", "lookback=1, cut_ordinal=0)", "lookback=1, cut_ordinal=0, val_cut_ordinal=0)", None),
]


def _apply(path: pathlib.Path, pattern: str, replacement: str, expected: int | None) -> bool:
    src = path.read_text()
    found = src.count(pattern)
    if expected is not None and found != expected:
        print(f"{path.name}: {pattern[:60]!r} matched {found}x, expected {expected}", file=sys.stderr)
        return False
    if expected is None and found == 0:
        print(f"{path.name}: {pattern[:60]!r} matched 0x", file=sys.stderr)
        return False
    path.write_text(src.replace(pattern, replacement))
    return True


def main() -> int:
    ok = True
    for filename, pattern, replacement, expected in EDITS:
        ok &= _apply(BASE / filename, pattern, replacement, expected)

    # Any remaining bare windower call in the leakage tests keeps a val share.
    leak = BASE / "test_sequence_windowing_leakage.py"
    src = leak.read_text()
    src, n = re.subn(
        r"(window_(?:regular|timed)_series\([^)]*train_ratio=train_ratio)(?!, val_ratio)",
        r"\1, val_ratio=val_ratio",
        src,
    )
    leak.write_text(src)
    print(f"leakage tests: {n} hypothesis call site(s) given val_ratio")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
