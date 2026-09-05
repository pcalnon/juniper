#!/usr/bin/env python3
"""Update checkerboard / moon / xor generator tests for the three-way partition.

Project:     Juniper
Sub-Project: juniper-data
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 3)

Four edit kinds:

* key-set assertions gain the val pair;
* size expectations grow by the additive factor (the size knob now denotes
  TRAIN, so N realises N + 0.4N + 0.3N rows);
* ratio-driven split tests move to ``sizing_mode="carve"``, because dividing a
  fixed N by ratios IS carve mode -- left in additive they would assert numbers
  the mode does not compute;
* positional slices derive their boundary from the realised array instead of a
  hardcoded row index.

The xor class-balance assertion becomes a BOUND rather than an equality, and
that is not a weakening to make it pass. Additive sizing rounds the per-quadrant
knob UP, so up to ``n_units - 1`` surplus rows are dropped from the shuffled
tail; exact per-class equality is therefore no longer guaranteed by
construction, and asserting it would be asserting something the code does not
promise. The bound is the real invariant, and the total is still exact.
"""

from __future__ import annotations

import pathlib
import sys

BASE = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--feature--tabular-val-emission--20260904-1830--ac7cd80d/juniper_data/tests/unit")

EDITS: dict[str, list[tuple[str, str]]] = {
    "test_checkerboard_generator.py": [
        (
            '        assert result["X_full"].shape == (150, 2)\n        assert result["y_full"].shape == (150, 2)\n',
            '        # n_samples is the TRAIN count under additive sizing: 150 + 60 + 45 = 255.\n'
            '        assert result["X_train"].shape == (150, 2)\n'
            '        assert result["X_val"].shape == (60, 2)\n'
            '        assert result["X_test"].shape == (45, 2)\n'
            '        assert result["X_full"].shape == (255, 2)\n'
            '        assert result["y_full"].shape == (255, 2)\n',
        ),
        (
            '            n_samples=100,\n            train_ratio=0.7,\n            test_ratio=0.3,\n            seed=42,\n        )\n        result = CheckerboardGenerator.generate(params)\n\n        assert len(result["X_train"]) == 70\n        assert len(result["X_test"]) == 30\n',
            '            n_samples=100,\n'
            '            train_ratio=0.7,\n'
            '            test_ratio=0.3,\n'
            '            seed=42,\n'
            '            # Ratios divide a fixed N -- that is carve mode by definition.\n'
            '            sizing_mode="carve",\n'
            '        )\n'
            '        result = CheckerboardGenerator.generate(params)\n'
            '\n'
            '        assert len(result["X_train"]) == 70\n'
            '        assert len(result["X_test"]) == 30\n',
        ),
    ],
    "test_moon_generator.py": [
        (
            '        assert set(result.keys()) == {"X_train", "y_train", "X_test", "y_test", "X_full", "y_full"}\n',
            '        assert set(result.keys()) == {"X_train", "y_train", "X_val", "y_val", "X_test", "y_test", "X_full", "y_full"}\n',
        ),
        (
            '        assert result["X_full"].shape == (150, 2)\n        assert result["y_full"].shape == (150, 2)\n',
            '        # n_samples is the TRAIN count under additive sizing: 150 + 60 + 45 = 255.\n'
            '        assert result["X_train"].shape == (150, 2)\n'
            '        assert result["X_val"].shape == (60, 2)\n'
            '        assert result["X_test"].shape == (45, 2)\n'
            '        assert result["X_full"].shape == (255, 2)\n'
            '        assert result["y_full"].shape == (255, 2)\n',
        ),
        (
            '        counts = result["y_full"].sum(axis=0)\n        assert counts[0] == 100\n        assert counts[1] == 100\n',
            '        counts = result["y_full"].sum(axis=0)\n'
            '        # 200 train + 80 val + 60 test = 340 realised rows, evenly halved.\n'
            '        assert counts[0] == 170\n'
            '        assert counts[1] == 170\n',
        ),
        (
            '        params = MoonParams(n_samples=100, train_ratio=0.7, test_ratio=0.3, seed=42)\n',
            '        # Ratios divide a fixed N -- that is carve mode by definition.\n'
            '        params = MoonParams(n_samples=100, train_ratio=0.7, test_ratio=0.3, seed=42, sizing_mode="carve")\n',
        ),
        (
            '        upper = result["X_full"][:50]\n        # Upper moon: y = sin(theta), x = cos(theta) — satisfies x^2 + y^2 == 1\n        radii = np.linalg.norm(upper, axis=1)\n        np.testing.assert_array_almost_equal(radii, np.ones(50), decimal=5)\n\n        lower = result["X_full"][50:]\n',
            '        # The boundary is derived from the realised array rather than hardcoded:\n'
            '        # n_samples now denotes TRAIN, so the realised row count is larger and the\n'
            '        # two moons meet at its midpoint, not at row 50.\n'
            '        n_upper = result["X_full"].shape[0] // 2\n'
            '        upper = result["X_full"][:n_upper]\n'
            '        # Upper moon: y = sin(theta), x = cos(theta) — satisfies x^2 + y^2 == 1\n'
            '        radii = np.linalg.norm(upper, axis=1)\n'
            '        np.testing.assert_array_almost_equal(radii, np.ones(n_upper), decimal=5)\n'
            '\n'
            '        lower = result["X_full"][n_upper:]\n',
        ),
        (
            '        lower_radii = np.linalg.norm(centered, axis=1)\n        np.testing.assert_array_almost_equal(lower_radii, np.ones(50), decimal=5)\n',
            '        lower_radii = np.linalg.norm(centered, axis=1)\n'
            '        np.testing.assert_array_almost_equal(lower_radii, np.ones(lower.shape[0]), decimal=5)\n',
        ),
    ],
    "test_xor_generator.py": [
        (
            '        n_total = 4 * 25\n        n_train = int(n_total * 0.8)\n        n_test = n_total - n_train\n',
            '        # The per-quadrant knob names the TRAIN count under additive sizing:\n'
            '        # 4 * 25 = 100 train, plus 40 val and 30 test.\n'
            '        n_train = 4 * 25\n'
            '        n_val = 40\n'
            '        n_test = 30\n'
            '        n_total = n_train + n_val + n_test\n',
        ),
        (
            '        assert result["X_test"].shape == (n_test, 2)\n        assert result["y_test"].shape == (n_test, 2)\n',
            '        assert result["X_val"].shape == (n_val, 2)\n'
            '        assert result["y_val"].shape == (n_val, 2)\n'
            '        assert result["X_test"].shape == (n_test, 2)\n'
            '        assert result["y_test"].shape == (n_test, 2)\n',
        ),
        (
            '        y_full = result["y_full"]\n        class_0_count = y_full[:, 0].sum()\n        class_1_count = y_full[:, 1].sum()\n\n        assert class_0_count == 50\n        assert class_1_count == 50\n',
            '        y_full = result["y_full"]\n'
            '        class_0_count = y_full[:, 0].sum()\n'
            '        class_1_count = y_full[:, 1].sum()\n'
            '\n'
            '        # 100 train + 40 val + 30 test = 170 realised rows. Additive sizing rounds\n'
            '        # the per-quadrant knob UP (ceil(170/4) = 43, so 172 generated), and the\n'
            '        # 2 surplus rows are dropped from the SHUFFLED tail -- so exact per-class\n'
            '        # equality is not guaranteed by construction and must not be asserted.\n'
            '        # The bound below is what the code actually promises.\n'
            '        n_generated = 4 * -(-170 // 4)\n'
            '        n_surplus = n_generated - 170\n'
            '\n'
            '        assert class_0_count + class_1_count == 170\n'
            '        assert abs(class_0_count - class_1_count) <= n_surplus\n',
        ),
        (
            '        X = result["X_full"]\n        y = result["y_full"]\n        n = 50\n',
            '        X = result["X_full"]\n'
            '        y = result["y_full"]\n'
            '        # Quadrants are equal-sized blocks of the unshuffled array; the block size\n'
            '        # follows the realised row count rather than the requested per-quadrant knob.\n'
            '        n = X.shape[0] // 4\n',
        ),
    ],
}


def main() -> int:
    for filename, edits in EDITS.items():
        path = BASE / filename
        src = path.read_text()
        for old, new in edits:
            if src.count(old) != 1:
                print(f"{filename}: pattern matched {src.count(old)} times, refusing:\n{old[:90]}", file=sys.stderr)
                return 1
            src = src.replace(old, new)
        path.write_text(src)
        print(f"{filename} updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
