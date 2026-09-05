#!/usr/bin/env python3
"""Update mnist / csv_import / normaliser-fit-scope tests for the third partition.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3)

These three generators are carve-only, and their default carve is now
0.8 / 0.1 / 0.1. Two consequences show up in the tests:

* the default ``test_ratio`` assertion moves from 0.2 to 0.1, and gains the
  ``val_ratio`` it now sits beside;
* tests that pass an explicit ``train_ratio`` / ``test_ratio`` summing to 1.0
  must now also say ``val_ratio=0.0``, or the cross-field validator rejects them
  at 1.1. Setting it to 0 rather than rebalancing is deliberate: those tests are
  about normaliser fit scope and split arithmetic, and giving them a validation
  partition they never asked for would change what they measure.
"""

from __future__ import annotations

import pathlib
import sys

BASE = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--tabular-val-emission--20260904-1830--ac7cd80d/juniper_data/tests/unit")

EDITS: dict[str, list[tuple[str, str]]] = {
    "test_mnist_generator.py": [
        (
            '        assert params.train_ratio == 0.8\n        assert params.test_ratio == 0.2\n',
            '        assert params.train_ratio == 0.8\n'
            '        # The default carve is three-way now: 0.8 / 0.1 / 0.1.\n'
            '        assert params.val_ratio == 0.1\n'
            '        assert params.test_ratio == 0.1\n'
            '        assert params.sizing_mode == "carve"\n',
        ),
        (
            '            seed=42,\n            train_ratio=0.7,\n            test_ratio=0.3,\n        )\n        assert params.n_samples == 100\n',
            '            seed=42,\n'
            '            train_ratio=0.7,\n'
            '            test_ratio=0.3,\n'
            '            # 0.7 + 0.3 already accounts for every row, so the validation share\n'
            '            # must be stated as 0 rather than left at the 0.1 default (which\n'
            '            # would over-subscribe the dataset at 1.1).\n'
            '            val_ratio=0.0,\n'
            '        )\n'
            '        assert params.n_samples == 100\n',
        ),
        (
            '        n_total = 20\n        n_train = int(n_total * 0.8)\n        n_test = n_total - n_train\n\n        assert result["X_train"].shape[0] == n_train\n        assert result["X_test"].shape[0] == n_test\n',
            '        # Default carve is 0.8 / 0.1 / 0.1, and the last partition absorbs the\n'
            '        # rounding remainder so no row is dropped.\n'
            '        n_total = 20\n'
            '        n_train = int(n_total * 0.8)\n'
            '        n_val = int(n_total * 0.1)\n'
            '        n_test = n_total - n_train - n_val\n'
            '\n'
            '        assert result["X_train"].shape[0] == n_train\n'
            '        assert result["X_val"].shape[0] == n_val\n'
            '        assert result["X_test"].shape[0] == n_test\n'
            '        assert n_train + n_val + n_test == n_total\n',
        ),
    ],
    "test_csv_import_generator.py": [
        (
            '            train_ratio=0.5,\n            test_ratio=0.5,\n            seed=42,\n        )\n',
            '            train_ratio=0.5,\n'
            '            test_ratio=0.5,\n'
            '            # 0.5 + 0.5 accounts for every row; state the validation share as 0\n'
            '            # rather than leaving the 0.1 default to over-subscribe at 1.1.\n'
            '            val_ratio=0.0,\n'
            '            seed=42,\n'
            '        )\n',
        ),
    ],
    "test_normaliser_fit_scope.py": [
        (
            'normalize_features=True, shuffle=False, train_ratio=0.5, test_ratio=0.5))\n        train = out["X_train"]',
            'normalize_features=True, shuffle=False, train_ratio=0.5, test_ratio=0.5, val_ratio=0.0))\n        train = out["X_train"]',
        ),
        (
            'normalize_features=True, shuffle=False, train_ratio=0.5, test_ratio=0.5))\n        assert out["X_test"].max() > 1.0 + 1e-6',
            'normalize_features=True, shuffle=False, train_ratio=0.5, test_ratio=0.5, val_ratio=0.0))\n        assert out["X_test"].max() > 1.0 + 1e-6',
        ),
        (
            '        common = {"file_path": "d.csv", "label_column": "label", "shuffle": False, "train_ratio": 0.5, "test_ratio": 0.5}\n',
            '        common = {"file_path": "d.csv", "label_column": "label", "shuffle": False, "train_ratio": 0.5, "test_ratio": 0.5, "val_ratio": 0.0}\n',
        ),
        (
            '        for key in ("X_train", "X_test", "X_full", "y_train", "y_test", "y_full"):\n',
            '        for key in ("X_train", "X_val", "X_test", "X_full", "y_train", "y_val", "y_test", "y_full"):\n',
        ),
    ],
}


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
