#!/usr/bin/env python3
"""Give cascor's auto-start test stubs a three-way artifact.

Project:     Juniper
Sub-Project: juniper-cascor
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 4)

Four stubbed ``download_artifact_npz`` return values carried only
``X_train`` / ``y_train``. §6.1 rule 3 now refuses a train-only artifact -- there
is nothing held out to early-stop on or report from -- so these stubs describe an
artifact the service is no longer willing to train on.

Each gains a ``val`` and a ``test`` pair at the same feature count. Their row
counts DIFFER from train and from each other so a test cannot pass by binding the
wrong partition to the wrong slot.
"""

from __future__ import annotations

import pathlib
import re
import sys

PATH = pathlib.Path(
    "/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--feature--consume-x-val--20260905-0133--90071c56/src/tests/unit/api/test_api_app_coverage_deep.py"
)

BLOCK = re.compile(
    r'( *)"X_train": __import__\("numpy"\)\.random\.randn\((?P<n>\d+), 2\)\.astype\("float32"\),\n'
    r' *"y_train": __import__\("numpy"\)\.random\.randn\((?P=n), 2\)\.astype\("float32"\),\n'
)


def _replacement(match: re.Match) -> str:
    indent = match.group(1)
    n = int(match.group("n"))
    n_val = max(2, n // 4)
    n_test = max(1, n // 5)
    np_call = '__import__("numpy").random.randn'
    lines = [
        f'{indent}"X_train": {np_call}({n}, 2).astype("float32"),',
        f'{indent}"y_train": {np_call}({n}, 2).astype("float32"),',
        f'{indent}# §6.1: a train-only artifact is refused -- there is nothing held out.',
        f'{indent}# Distinct row counts so a mis-bound partition cannot pass silently.',
        f'{indent}"X_val": {np_call}({n_val}, 2).astype("float32"),',
        f'{indent}"y_val": {np_call}({n_val}, 2).astype("float32"),',
        f'{indent}"X_test": {np_call}({n_test}, 2).astype("float32"),',
        f'{indent}"y_test": {np_call}({n_test}, 2).astype("float32"),',
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    src = PATH.read_text()
    new, count = BLOCK.subn(_replacement, src)
    if count != 4:
        print(f"expected 4 stub blocks, matched {count} -- refusing", file=sys.stderr)
        return 1
    PATH.write_text(new)
    print(f"test_api_app_coverage_deep.py updated ({count} stubs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
