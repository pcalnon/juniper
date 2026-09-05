#!/usr/bin/env python3
"""Update spiral / gaussian generator tests for the three-way partition.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3)

Same four edit kinds as the checkerboard/moon/xor pass. The per-class mean
tests in gaussian move from positional slices to class masks: they were asking
"is the mean of class k near centre k", and the slice only expressed that while
each class happened to occupy a fixed 100-row block. A mask says it directly and
survives any sizing.
"""

from __future__ import annotations

import pathlib
import sys

BASE = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--tabular-val-emission--20260904-1830--ac7cd80d/juniper_data/tests/unit")

EDITS: dict[str, list[tuple[str, str]]] = {
    "test_spiral_generator.py": [
        (
            '        assert result["X_full"].shape == (200, 2)\n        assert result["y_full"].shape == (200, 2)\n',
            '        # 2 x 100 = 200 TRAIN points under additive sizing, plus 80 val and 60 test.\n'
            '        assert result["X_train"].shape == (200, 2)\n'
            '        assert result["X_val"].shape == (80, 2)\n'
            '        assert result["X_test"].shape == (60, 2)\n'
            '        assert result["X_full"].shape == (340, 2)\n'
            '        assert result["y_full"].shape == (340, 2)\n',
        ),
        (
            '        assert result["X_full"].shape == (150, 2)\n        assert result["y_full"].shape == (150, 3)\n',
            '        # 3 x 50 = 150 TRAIN points, plus 60 val and 45 test.\n'
            '        assert result["X_full"].shape == (255, 2)\n'
            '        assert result["y_full"].shape == (255, 3)\n',
        ),
        (
            '        total_points = two_spiral_params.total_points()\n        expected_train = int(np.round(total_points * two_spiral_params.train_ratio))\n        expected_test = int(np.round(total_points * two_spiral_params.test_ratio))\n\n        assert abs(result["X_train"].shape[0] - expected_train) <= 1\n        assert abs(result["y_train"].shape[0] - expected_train) <= 1\n        assert abs(result["X_test"].shape[0] - expected_test) <= 1\n        assert abs(result["y_test"].shape[0] - expected_test) <= 1\n',
            '        # Additive sizing honours the requested train count LITERALLY -- the size\n'
            '        # knob is the train count, not a total to be divided -- so this is an\n'
            '        # equality now rather than a +/-1 rounding tolerance.\n'
            '        total_points = two_spiral_params.total_points()\n'
            '        expected_train = total_points\n'
            '        expected_val = int(round(total_points * two_spiral_params.val_percent / 100.0))\n'
            '        expected_test = int(round(total_points * two_spiral_params.test_percent / 100.0))\n'
            '\n'
            '        assert result["X_train"].shape[0] == expected_train\n'
            '        assert result["y_train"].shape[0] == expected_train\n'
            '        assert result["X_val"].shape[0] == expected_val\n'
            '        assert result["y_val"].shape[0] == expected_val\n'
            '        assert result["X_test"].shape[0] == expected_test\n'
            '        assert result["y_test"].shape[0] == expected_test\n',
        ),
        (
            '            train_ratio=0.6,\n            test_ratio=0.3,\n            seed=42,\n        )\n        result = SpiralGenerator.generate(params)\n',
            '            train_ratio=0.6,\n'
            '            test_ratio=0.3,\n'
            '            seed=42,\n'
            '            # Ratios divide a fixed N -- that is carve mode by definition.\n'
            '            sizing_mode="carve",\n'
            '        )\n'
            '        result = SpiralGenerator.generate(params)\n',
        ),
        (
            '        expected_counts = np.array([50, 50, 50])\n',
            '        # 3 x 50 = 150 train + 60 val + 45 test = 255 realised rows, 85 per spiral.\n'
            '        expected_counts = np.array([85, 85, 85])\n',
        ),
        (
            '        assert result["X_full"].shape == (100, 2)\n',
            '        # 100 TRAIN points, plus 40 val and 30 test.\n'
            '        assert result["X_full"].shape == (170, 2)\n',
        ),
        (
            '        assert result["X_full"].shape == (50, 2)\n',
            '        # 50 TRAIN points, plus 20 val and 15 test.\n'
            '        assert result["X_full"].shape == (85, 2)\n',
        ),
    ],
    "test_gaussian_generator.py": [
        (
            '        total_samples = 3 * 40\n        assert result["X_full"].shape == (total_samples, 5)\n        assert result["y_full"].shape == (total_samples, 3)\n',
            '        # 3 x 40 = 120 TRAIN samples under additive sizing, plus 48 val and 36 test.\n'
            '        n_train = 3 * 40\n'
            '        total_samples = n_train + 48 + 36\n'
            '        assert result["X_train"].shape == (n_train, 5)\n'
            '        assert result["X_full"].shape == (total_samples, 5)\n'
            '        assert result["y_full"].shape == (total_samples, 3)\n',
        ),
        (
            '        class_counts = result["y_full"].sum(axis=0)\n        np.testing.assert_array_equal(class_counts, [50, 50, 50])\n',
            '        class_counts = result["y_full"].sum(axis=0)\n'
            '        # 3 x 50 = 150 train + 60 val + 45 test = 255 realised rows, 85 per class.\n'
            '        np.testing.assert_array_equal(class_counts, [85, 85, 85])\n',
        ),
        (
            '            n_samples_per_class=50,\n            train_ratio=0.7,\n            test_ratio=0.3,\n            seed=42,\n        )\n',
            '            n_samples_per_class=50,\n'
            '            train_ratio=0.7,\n'
            '            test_ratio=0.3,\n'
            '            seed=42,\n'
            '            # Ratios divide a fixed N -- that is carve mode by definition.\n'
            '            sizing_mode="carve",\n'
            '        )\n',
        ),
        (
            '        class_0_samples = result["X_full"][:100]\n        class_1_samples = result["X_full"][100:]\n',
            '        # Select by CLASS rather than position: the per-class block size follows\n'
            '        # the realised row count, and a mask asks the question directly.\n'
            '        labels = np.argmax(result["y_full"], axis=1)\n'
            '        class_0_samples = result["X_full"][labels == 0]\n'
            '        class_1_samples = result["X_full"][labels == 1]\n'
            '\n'
            '        assert class_0_samples.shape[0] > 0 and class_1_samples.shape[0] > 0\n',
        ),
        (
            '        for i in range(4):\n            start = i * 100\n            end = start + 100\n            class_mean = result["X_full"][start:end].mean(axis=0)\n',
            '        labels = np.argmax(result["y_full"], axis=1)\n'
            '        for i in range(4):\n'
            '            class_rows = result["X_full"][labels == i]\n'
            '            assert class_rows.shape[0] > 0\n'
            '            class_mean = class_rows.mean(axis=0)\n',
        ),
        (
            '        assert result["X_full"].shape == (300, 2)\n',
            '        # 3 x 100 = 300 TRAIN samples, plus 120 val and 90 test.\n'
            '        assert result["X_full"].shape == (510, 2)\n',
        ),
        (
            '        assert result["X_full"].shape == (100, 1)\n',
            '        # 100 TRAIN samples, plus 40 val and 30 test.\n'
            '        assert result["X_full"].shape == (170, 1)\n',
        ),
    ],
}


def main() -> int:
    for filename, edits in EDITS.items():
        path = BASE / filename
        src = path.read_text()
        for old, new in edits:
            if src.count(old) != 1:
                print(f"{filename}: pattern matched {src.count(old)} times, refusing:\n{old[:100]}", file=sys.stderr)
                return 1
            src = src.replace(old, new)
        path.write_text(src)
        print(f"{filename} updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
