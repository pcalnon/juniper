#!/usr/bin/env python3
"""Update juniper-data integration tests for the three-way partition.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3)

Risk R-5 -- ``full == train + test`` breakage -- fires here, at
``test_e2e_workflow.py:301``. That assertion was correct before and is wrong
now: the length identity spans three partitions.

``test_e2e_train_test_split_ratios`` is not merely re-numbered. Its subject
changed: under additive sizing the request's ``train_ratio`` no longer governs
the split at all, so an updated ratio assertion would be checking a number the
mode does not compute. It is rewritten to pin what the mode DOES promise --
decisions 2 and 8: the size knob is honoured literally as the train count, and
val/test are additional rows sized from it.
"""

from __future__ import annotations

import pathlib
import sys

BASE = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--tabular-val-emission--20260904-1830--ac7cd80d/juniper_data/tests/integration")

EDITS: dict[str, list[tuple[str, str]]] = {
    "test_e2e_workflow.py": [
        (
            '            n_total = 2 * 100\n            n_train = int(n_total * 0.8)\n            n_test = n_total - n_train\n            n_spirals = 2\n',
            '            # 2 x 100 = 200 TRAIN points under additive sizing (decisions 2 and 8),\n'
            '            # plus 80 val and 60 test -> 340 realised rows.\n'
            '            n_train = 2 * 100\n'
            '            n_val = 80\n'
            '            n_test = 60\n'
            '            n_total = n_train + n_val + n_test\n'
            '            n_spirals = 2\n',
        ),
        (
            '            assert X_test.shape == (n_test, 2)\n            assert y_test.shape == (n_test, n_spirals)\n',
            '            assert data["X_val"].shape == (n_val, 2)\n'
            '            assert data["y_val"].shape == (n_val, n_spirals)\n'
            '            assert X_test.shape == (n_test, 2)\n'
            '            assert y_test.shape == (n_test, n_spirals)\n',
        ),
        (
            '            expected_keys = ["X_train", "y_train", "X_test", "y_test", "X_full", "y_full"]\n',
            '            expected_keys = ["X_train", "y_train", "X_val", "y_val", "X_test", "y_test", "X_full", "y_full"]\n',
        ),
        (
            '            n_total = 2 * 100\n            assert X_full.shape == (n_total, 2)\n            assert y_full.shape == (n_total, 2)\n',
            '            # 200 TRAIN points plus 80 val and 60 test.\n'
            '            n_total = 200 + 80 + 60\n'
            '            assert X_full.shape == (n_total, 2)\n'
            '            assert y_full.shape == (n_total, 2)\n',
        ),
        (
            '            expected_keys = {"X_train", "y_train", "X_test", "y_test", "X_full", "y_full"}\n',
            '            expected_keys = {"X_train", "y_train", "X_val", "y_val", "X_test", "y_test", "X_full", "y_full"}\n',
        ),
        (
            '            n_train = len(data["X_train"])\n            n_test = len(data["X_test"])\n            n_full = len(data["X_full"])\n\n            assert n_train + n_test == n_full\n\n            expected_train_ratio = 0.7\n            actual_train_ratio = n_train / n_full\n            assert abs(actual_train_ratio - expected_train_ratio) < 0.05\n',
            '            n_train = len(data["X_train"])\n'
            '            n_val = len(data["X_val"])\n'
            '            n_test = len(data["X_test"])\n'
            '            n_full = len(data["X_full"])\n'
            '\n'
            '            # The length identity spans THREE partitions now. Asserting it over\n'
            '            # train + test alone -- which is what this line used to do -- would\n'
            '            # pass only while val is empty, which is the regression it must catch.\n'
            '            assert n_val > 0, "X_val must be non-empty, or the identity below holds vacuously"\n'
            '            assert n_train + n_val + n_test == n_full\n'
            '\n'
            '            # Decisions 2 and 8: the size knob (2 x 50) is the TRAIN count,\n'
            '            # honoured literally, and val/test are ADDITIONAL rows at 40 % and\n'
            '            # 30 % of it. The request\'s train_ratio does not govern additive\n'
            '            # sizing, so asserting a 0.7 train share would be checking a number\n'
            '            # this mode never computes.\n'
            '            assert n_train == 100\n'
            '            assert n_val == 40\n'
            '            assert n_test == 30\n',
        ),
    ],
    "test_api.py": [
        (
            '        assert data["meta"]["n_samples"] == 100\n',
            '        # n_samples spans all three partitions: 100 train + 40 val + 30 test.\n'
            '        assert data["meta"]["n_samples"] == 170\n',
        ),
    ],
    "test_lifecycle_api.py": [
        (
            '        assert data["total_samples"] == 600\n',
            '        # Each dataset realises 1.7x its train count under additive sizing.\n'
            '        assert data["total_samples"] == 1020\n',
        ),
    ],
    "test_mnist_real_generation.py": [
        (
            '        assert set(result) == {"X_train", "y_train", "X_test", "y_test", "X_full", "y_full"}\n',
            '        assert set(result) == {"X_train", "y_train", "X_val", "y_val", "X_test", "y_test", "X_full", "y_full"}\n',
        ),
    ],
}

# Two identical assertions in one file, so they are handled by count rather than
# by a uniqueness check.
STORAGE_WORKFLOW = (
    "test_storage_workflow.py",
    "        assert retrieved_meta.n_samples == 200\n",
    "        # 200 train + 80 val + 60 test = 340 realised rows.\n        assert retrieved_meta.n_samples == 340\n",
    2,
)


def main() -> int:
    for filename, edits in EDITS.items():
        path = BASE / filename
        src = path.read_text()
        for old, new in edits:
            if src.count(old) != 1:
                print(f"{filename}: pattern matched {src.count(old)} times, refusing:\n{old[:110]}", file=sys.stderr)
                return 1
            src = src.replace(old, new)
        path.write_text(src)
        print(f"{filename} updated")

    filename, old, new, expected = STORAGE_WORKFLOW
    path = BASE / filename
    src = path.read_text()
    if src.count(old) != expected:
        print(f"{filename}: pattern matched {src.count(old)} times, expected {expected} -- refusing", file=sys.stderr)
        return 1
    path.write_text(src.replace(old, new))
    print(f"{filename} updated ({expected} sites)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
