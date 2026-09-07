#!/usr/bin/env python3
"""Decision 11: take ``*_full`` out of juniper-data's published docs.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, decision 11)
Created:     2026-09-05
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     juniper-data#369

Fifteen sites. Twelve are key lists and schema-table rows, which come out.

The interesting two are the numbered GUARANTEE in ``docs/api/JUNIPER_DATA_API.md`` and
``docs/USER_MANUAL.md``: ``len(X_train) + len(X_val) + len(X_test) == len(X_full)``.
That was written HOURS ago in the 0.13.0 release, replacing a two-way form that had
just become false -- and it is now false itself, because its right-hand side no longer
exists. It is replaced with the statement the identity was really making: the three
partitions are the whole dataset, and ``meta.n_samples`` is their sum.

That is the third revision of the same guarantee in one day. The lesson written into
the replacement is to state the invariant over the PARTITIONS rather than over a
derived array, so the next contract change cannot invalidate the sentence again.
"""

from __future__ import annotations

import pathlib
import sys

WT = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--drop-full-family--20260905-1330--cc15640c")

KEYS_OLD = "`X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test`, `X_full`, `y_full`"
KEYS_NEW = "`X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test`"

GUARANTEE_OLD = """6. `len(X_train) + len(X_val) + len(X_test) == len(X_full)`
"""
GUARANTEE_NEW = """6. The three partitions ARE the dataset: there is no whole-set array to compare them
   against, and `meta.n_samples` equals `n_train + n_val + n_test`. A consumer that
   wants the whole set concatenates the three, in that order.
"""

EDITS: list[tuple[str, str, str, int]] = [
    ("docs/DEVELOPER_CHEATSHEET.md", KEYS_OLD, KEYS_NEW, 1),
    ("README.md", KEYS_OLD, KEYS_NEW, 1),
    (
        "README.md",
        "# dataset: dict of float32 arrays — X_train, y_train, X_val, y_val, X_test, y_test, X_full, y_full",
        "# dataset: dict of float32 arrays — X_train, y_train, X_val, y_val, X_test, y_test",
        1,
    ),
    ("AGENTS.md", KEYS_OLD, KEYS_NEW, 1),
    (".github/instructions/copilot-instructions.md", KEYS_OLD, KEYS_NEW, 1),
    ("docs/DOCUMENTATION_OVERVIEW.md", KEYS_OLD, KEYS_NEW, 1),
    ("docs/testing/TESTING_REFERENCE.md", KEYS_OLD, KEYS_NEW, 1),
    ("docs/QUICK_START.md", KEYS_OLD, KEYS_NEW, 1),
    (
        "docs/USER_MANUAL.md",
        "| `X_full` | `(n_samples, n_features)` | `float32` | Full dataset features |\n| `y_full` | `(n_samples, n_classes)` | `float32` | Full dataset labels (one-hot) |\n",
        "",
        1,
    ),
    (
        "docs/api/JUNIPER_DATA_API.md",
        "| `X_full`  | `(n_samples, n_features)` | `float32` | Full dataset features         |\n| `y_full`  | `(n_samples, n_classes)`  | `float32` | Full dataset labels (one-hot) |\n",
        "",
        1,
    ),
    ("docs/USER_MANUAL.md", GUARANTEE_OLD, GUARANTEE_NEW, 1),
    ("docs/api/JUNIPER_DATA_API.md", GUARANTEE_OLD, GUARANTEE_NEW, 1),
    (
        "docs/api/JUNIPER_DATA_API.md",
        """Guarantee 6 replaced `len(X_train) + len(X_test) == len(X_full)`, which held only
while the contract was two-way. Any consumer still asserting the two-way form will
fail against every three-way artifact. Artifacts are distinguishable without
unpacking them: every generator that gained the `val` partition also bumped its
`generator_version` to `2.0.0`, and that version is hashed into the `dataset_id`,
so a cached two-way artifact can never be served for a three-way request.
""",
        """Guarantee 6 has now been rewritten twice in one day, and the second rewrite is the
reason it is stated over the partitions rather than over an array. It read
`len(X_train) + len(X_test) == len(X_full)` while the contract was two-way; 0.13.0
made that `len(X_train) + len(X_val) + len(X_test) == len(X_full)`; decision 11 then
removed `X_full`, invalidating the right-hand side. An invariant expressed over a
DERIVED array is only as durable as that array.

`X_full` / `y_full` are no longer emitted. Stored artifacts produced before
2026-09-05 still carry them and readers tolerate that — but nothing requires them,
and no new artifact has them. Artifacts remain distinguishable without unpacking:
every generator that gained the `val` partition bumped its `generator_version` to
`2.0.0`, and that version is hashed into the `dataset_id`.
""",
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
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
