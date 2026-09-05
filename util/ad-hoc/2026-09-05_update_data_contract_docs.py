#!/usr/bin/env python3
"""Bring juniper-data's prose docs onto the three-way NPZ contract.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3b)

Nine sites enumerate the NPZ keys, and two state ``len(X_train) + len(X_test) ==
len(X_full)`` as a guarantee. Both were true of the two-way contract and are false
now. Two are worth calling out:

* ``docs/USER_MANUAL.md`` and ``docs/api/JUNIPER_DATA_API.md`` publish the identity
  as a numbered **guarantee** a consumer may rely on -- risk R-5 stated in prose to
  the people most likely to code against it.
* "All arrays are 2-dimensional" was never true of the sequence generators, whose
  ``X`` is ``(n, lookback, n_features)``. That is plan finding S-4's premise sitting
  in the user-facing manual, and a consumer dispatching on rank per this sentence
  mishandles six generators.

``notes/history/`` is deliberately excluded -- it is the historical record and
should keep describing the contract as it was.
"""

from __future__ import annotations

import pathlib
import sys

BASE = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--sequence-val-split--20260905-0228--4b9f4b94")

KEYS_OLD = "`X_train`, `y_train`, `X_test`, `y_test`, `X_full`, `y_full`"
KEYS_NEW = "`X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test`, `X_full`, `y_full`"

GUARANTEES_OLD = """2. All arrays are 2-dimensional
3. `X_*` arrays have shape `(n, n_features)`
4. `y_*` arrays have shape `(n, n_classes)`
5. `y_*` arrays are valid one-hot encodings (each row sums to 1.0)
6. `len(X_train) + len(X_test) == len(X_full)`
"""

GUARANTEES_NEW = """2. `X_*` is 2-dimensional `(n, n_features)` for tabular generators and
   **3-dimensional** `(n, lookback, n_features)` for the sequence generators
   (`ar_p`, `delay_product`, `equities_seq`, `irregular_sine`, `mackey_glass`,
   `multi_sine`). Check `meta.sequence` rather than assuming a rank.
3. `y_*` arrays have shape `(n, n_classes)` -- or `(n, 1)` for regression targets
4. `y_*` classification arrays are valid one-hot encodings (each row sums to 1.0)
5. `X_train`, `X_val` and `X_test` are all present and all non-empty
6. `len(X_train) + len(X_val) + len(X_test) == len(X_full)`
"""

# (path, old, new, expected occurrences)
EDITS: list[tuple[str, str, str, int]] = [
    ("docs/DOCUMENTATION_OVERVIEW.md", KEYS_OLD, KEYS_NEW, 1),
    ("docs/DEVELOPER_CHEATSHEET.md", KEYS_OLD, KEYS_NEW, 1),
    ("docs/testing/TESTING_REFERENCE.md", KEYS_OLD, KEYS_NEW, 1),
    ("docs/QUICK_START.md", KEYS_OLD, KEYS_NEW, 1),
    (".github/instructions/copilot-instructions.md", KEYS_OLD, KEYS_NEW, 1),
    ("README.md", KEYS_OLD, KEYS_NEW, 1),
    (
        "README.md",
        "# dataset: dict of float32 arrays — X_train, y_train, X_test, y_test, X_full, y_full",
        "# dataset: dict of float32 arrays — X_train, y_train, X_val, y_val, X_test, y_test, X_full, y_full",
        1,
    ),
    (
        "notes/THREAD_HANDOFF_PROCEDURE.md",
        "- Verify NPZ data contract: keys X_train, y_train, X_test, y_test, X_full, y_full (float32)",
        "- Verify NPZ data contract: keys X_train, y_train, X_val, y_val, X_test, y_test, X_full, y_full (float32)",
        1,
    ),
    ("docs/USER_MANUAL.md", GUARANTEES_OLD, GUARANTEES_NEW, 1),
]


def main() -> int:
    ok = True
    for rel, old, new, expected in EDITS:
        path = BASE / rel
        src = path.read_text()
        found = src.count(old)
        if found != expected:
            print(f"{rel}: matched {found}x, expected {expected} -- refusing", file=sys.stderr)
            ok = False
            continue
        path.write_text(src.replace(old, new))
        print(f"{rel}: updated")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
