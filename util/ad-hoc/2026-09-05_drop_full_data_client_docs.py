#!/usr/bin/env python3
"""Decision 11: take ``*_full`` out of juniper-data-client's published docs.

Project:     Juniper
Sub-Project: juniper-data-client
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, decision 11)
Created:     2026-09-05
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     juniper-data-client#190

The docs are the contract as consumers read it, so they move in the same change as the
code. Two of these lines say ``retained`` -- one adds ``decision 11 drops *_full
later``. That "later" is now, and leaving the word in place would tell a reader the key
is still coming back.

The key TABLE rows are deleted rather than annotated: a schema table lists what an
artifact contains, and a row for a key nothing emits is wrong however it is footnoted.
The tolerance rule is stated once, in prose, where it belongs.
"""

from __future__ import annotations

import pathlib
import sys

WT = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data-client--feature--drop-full-family--20260905-1215--7d5b2f60")

TOLERANCE_NOTE = "A stored artifact produced before 2026-09-05 also carries `X_full` / `y_full`; readers tolerate them and no reader requires them (decision 11)."

EDITS: list[tuple[str, str, str, int]] = [
    (
        "README.md",
        "`X_test` / `y_test` / `X_full` / `y_full` NPZ schema (all `float32`). `val` is",
        "`X_test` / `y_test` NPZ schema (all `float32`). `val` is",
        1,
    ),
    (
        "docs/DOCUMENTATION_OVERVIEW.md",
        "- **Data contract**: NPZ artifacts with keys `X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test`, `X_full`, `y_full` (all `float32`). `val` is presence-conditional",
        "- **Data contract**: NPZ artifacts with keys `X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test` (all `float32`). `val` is presence-conditional",
        1,
    ),
    (
        "docs/DEVELOPER_CHEATSHEET.md",
        "| `X_full`  | `(n_total, n_features)` | Full dataset features (retained) |\n| `y_full`  | `(n_total, n_classes)`  | Full dataset labels (one-hot) |\n",
        "",
        1,
    ),
    (
        "docs/REFERENCE.md",
        "NPZ artifacts with keys: `X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test`, `X_full`, `y_full` (all `float32`). `val` is presence-conditional",
        "NPZ artifacts with keys: `X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test` (all `float32`). `val` is presence-conditional",
        1,
    ),
    (
        "docs/REFERENCE.md",
        "All four generators return `Dict[str, np.ndarray]` with keys `X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test`, `X_full`, `y_full` (all `float32`).",
        "All four generators return `Dict[str, np.ndarray]` with keys `X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test` (all `float32`).",
        1,
    ),
    (
        "docs/REFERENCE.md",
        "| `X_full` | `(n_total, n_features)` | Full dataset features (retained; decision 11 drops `*_full` later) |\n| `y_full` | `(n_total, n_classes)` | Full dataset labels (one-hot) |\n",
        "",
        1,
    ),
]


def main() -> int:
    ok = True
    for rel, old, new, expected in EDITS:
        path = WT / rel
        src = path.read_text()
        found = src.count(old)
        if found != expected:
            print(f"{rel}: matched {found}x, expected {expected} -- refusing", file=sys.stderr)
            ok = False
            continue
        path.write_text(src.replace(old, new))
        print(f"{rel}: updated")

    # State the tolerance rule once, next to the schema, rather than in every table.
    ref = WT / "docs/REFERENCE.md"
    src = ref.read_text()
    anchor = "NPZ artifacts with keys: `X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test` (all `float32`)."
    if anchor in src and TOLERANCE_NOTE not in src:
        ref.write_text(src.replace(anchor, anchor + " " + TOLERANCE_NOTE, 1))
        print("docs/REFERENCE.md: tolerance rule stated")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
