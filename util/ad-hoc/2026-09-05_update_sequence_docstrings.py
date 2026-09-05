#!/usr/bin/env python3
"""Update the sequence windowers' docstrings for the three-way temporal split.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3b)

Risk R-5 -- ``full == train + test`` -- fires in prose here before it fires in
code: two docstrings state ``X_full == concatenate([X_train, X_test])`` as the
contract. With ``val`` carved between them that identity is false, and a reader
trusting it would conclude the windower drops rows.
"""

from __future__ import annotations

import pathlib
import sys

PATH = pathlib.Path(
    "/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--sequence-val-split--20260905-0228--4b9f4b94/juniper_data/generators/_sequence.py"
)

EDITS: list[tuple[str, str, int]] = [
    (
        "        all-ones. ``X_full == concatenate([X_train, X_test])``.",
        "        all-ones. ``X_full == concatenate([X_train, X_val, X_test])`` -- the\n"
        "        identity spans THREE partitions now, and ``test`` takes the remainder so\n"
        "        no window is lost to rounding.",
        2,
    ),
    (
        "        Flat NPZ dict mapping ``{X, y, dt, target_dt, observed_mask}_{train,test,full}``:",
        "        Flat NPZ dict mapping ``{X, y, dt, target_dt, observed_mask}_{train,val,test,full}``:",
        2,
    ),
    (
        "    :func:`~juniper_data.core.split.temporal_split_index`, so every train target\n"
        "    strictly precedes every test target -- the same no-future-leak guarantee as\n"
        "    the per-entity windower, here structural because there is a single series and\n"
        "    a single chronological cut. ``full`` is ``train`` followed by ``test``.",
        "    :func:`~juniper_data.core.split.temporal_split_indices`, so every train target\n"
        "    strictly precedes every validation target and every validation target precedes\n"
        "    every test target -- the same no-future-leak guarantee as the per-entity\n"
        "    windower, here structural because there is a single series and two chronological\n"
        "    cuts. Validation sits BETWEEN train and test in time, so early stopping never\n"
        "    sees data from after the reported window. ``full`` is ``train``, then ``val``,\n"
        "    then ``test``.",
        1,
    ),
    (
        "        train_ratio: fraction of the earliest windows used for training, ``(0, 1]``.",
        "        train_ratio: fraction of the earliest windows used for training, ``(0, 1]``.\n"
        "        val_ratio: fraction used for in-loop validation, taken from the windows\n"
        "            immediately after train, ``[0, 1)``. Test is every later window.",
        2,
    ),
]


def main() -> int:
    src = PATH.read_text()
    for old, new, expected in EDITS:
        found = src.count(old)
        if found != expected:
            print(f"pattern matched {found}x, expected {expected} -- refusing:\n{old[:100]}", file=sys.stderr)
            return 1
        src = src.replace(old, new)
    PATH.write_text(src)
    print("_sequence.py docstrings updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
