#!/usr/bin/env python3
"""Update test_circles_generator.py for the three-way partition.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3)

Three distinct edits, not one:

* size expectations grow by the additive factor (n_samples now denotes TRAIN,
  so a 150-row request realises 150 + 60 + 45 = 255 rows);
* the two geometry tests stop slicing ``X_full`` positionally and select by
  class mask instead -- they were only ever asking "do the class-k points lie
  on circle k", and a mask says that directly without depending on where the
  class boundary happens to fall;
* ``test_train_test_split_ratio`` moves to ``sizing_mode="carve"``, because
  ratio-driven splitting IS carve mode now. Leaving it in additive would have
  left it asserting a number the mode does not compute.
"""

from __future__ import annotations

import pathlib
import sys

PATH = pathlib.Path(
    "/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--tabular-val-emission--20260904-1830--ac7cd80d/juniper_data/tests/unit/test_circles_generator.py"
)

EDITS: list[tuple[str, str]] = [
    # Shapes: 150 train + 60 val + 45 test = 255 realised rows.
    (
        '        assert result["X_full"].shape == (150, 2)\n        assert result["y_full"].shape == (150, 2)\n',
        '        # n_samples denotes the TRAIN count under additive sizing, so the\n'
        '        # realised dataset is 150 + 60 + 45 = 255 rows.\n'
        '        assert result["X_train"].shape == (150, 2)\n'
        '        assert result["X_val"].shape == (60, 2)\n'
        '        assert result["X_test"].shape == (45, 2)\n'
        '        assert result["X_full"].shape == (255, 2)\n'
        '        assert result["y_full"].shape == (255, 2)\n',
    ),
    # inner_ratio 0.5 over 170 realised rows.
    (
        '        class_counts = result["y_full"].sum(axis=0)\n        assert class_counts[0] == 50\n        assert class_counts[1] == 50\n',
        '        class_counts = result["y_full"].sum(axis=0)\n'
        '        # 100 train + 40 val + 30 test = 170 realised rows, split evenly.\n'
        '        assert class_counts[0] == 85\n'
        '        assert class_counts[1] == 85\n',
    ),
    # inner_ratio 0.3 over 170 realised rows.
    (
        '        class_counts = result["y_full"].sum(axis=0)\n        assert class_counts[0] == 70\n        assert class_counts[1] == 30\n',
        '        class_counts = result["y_full"].sum(axis=0)\n'
        '        # 170 realised rows at inner_ratio 0.3 -> 51 inner, 119 outer.\n'
        '        assert class_counts[0] == 119\n'
        '        assert class_counts[1] == 51\n',
    ),
    # Ratio-driven splitting is carve mode.
    (
        '            test_ratio=0.3,\n            seed=42,\n        )\n        result = CirclesGenerator.generate(params)\n\n        assert len(result["X_train"]) == 70\n        assert len(result["X_test"]) == 30\n',
        '            test_ratio=0.3,\n'
        '            seed=42,\n'
        '            # Ratios divide a fixed N -- that is carve mode by definition.\n'
        '            sizing_mode="carve",\n'
        '        )\n'
        '        result = CirclesGenerator.generate(params)\n'
        '\n'
        '        assert len(result["X_train"]) == 70\n'
        '        assert len(result["X_test"]) == 30\n',
    ),
    # Geometry by class mask, not position.
    (
        '        outer_points = result["X_full"][:50]\n        inner_points = result["X_full"][50:]\n\n        outer_distances = np.linalg.norm(outer_points, axis=1)\n        inner_distances = np.linalg.norm(inner_points, axis=1)\n\n        np.testing.assert_array_almost_equal(outer_distances, np.full(50, 2.0))\n        np.testing.assert_array_almost_equal(inner_distances, np.full(50, 1.0))\n',
        '        # Select by CLASS rather than by position. The original slice assumed\n'
        '        # the class boundary sat at row 50, which tied a geometry assertion to\n'
        '        # the partition sizing; a mask asks the question directly.\n'
        '        labels = np.argmax(result["y_full"], axis=1)\n'
        '        outer_points = result["X_full"][labels == 0]\n'
        '        inner_points = result["X_full"][labels == 1]\n'
        '\n'
        '        assert outer_points.shape[0] > 0 and inner_points.shape[0] > 0\n'
        '\n'
        '        outer_distances = np.linalg.norm(outer_points, axis=1)\n'
        '        inner_distances = np.linalg.norm(inner_points, axis=1)\n'
        '\n'
        '        np.testing.assert_array_almost_equal(outer_distances, np.full(outer_points.shape[0], 2.0))\n'
        '        np.testing.assert_array_almost_equal(inner_distances, np.full(inner_points.shape[0], 1.0))\n',
    ),
    (
        '        inner_points = result["X_full"][50:]\n        inner_distances = np.linalg.norm(inner_points, axis=1)\n\n        np.testing.assert_array_almost_equal(inner_distances, np.full(50, 1.0))\n',
        '        labels = np.argmax(result["y_full"], axis=1)\n'
        '        inner_points = result["X_full"][labels == 1]\n'
        '\n'
        '        assert inner_points.shape[0] > 0\n'
        '\n'
        '        inner_distances = np.linalg.norm(inner_points, axis=1)\n'
        '\n'
        '        np.testing.assert_array_almost_equal(inner_distances, np.full(inner_points.shape[0], 1.0))\n',
    ),
]


def main() -> int:
    src = PATH.read_text()
    for old, new in EDITS:
        if src.count(old) != 1:
            print(f"pattern matched {src.count(old)} times, refusing:\n{old[:90]}", file=sys.stderr)
            return 1
        src = src.replace(old, new)
    PATH.write_text(src)
    print("test_circles_generator.py updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
