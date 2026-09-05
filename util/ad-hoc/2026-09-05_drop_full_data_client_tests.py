#!/usr/bin/env python3
"""Decision 11: re-point juniper-data-client's tests off the ``*_full`` family.

Project:     Juniper
Sub-Project: juniper-data-client
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, decision 11)
Created:     2026-09-05
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     juniper-data-client#190

24 tests asserted the family exists. Most are mechanical -- a shape or dtype read off
``X_full`` that any partition answers identically -- but three are not, and those are
the reason this is a script with named edits rather than a regex:

* ``test_full_dataset_is_union_of_the_three_partitions`` measured
  ``len(X_full) == n_train + n_val + n_test``. With no ``X_full`` there is no union to
  measure, so the test becomes what the identity was actually FOR: the metadata's
  ``n_full`` must equal the partition sum. The property survives; its subject moves
  from an array to a number.
* ``test_train_test_split_ratio`` divided ``n_train`` by ``len(X_full)``. The
  denominator becomes the partition sum -- same ratio, no array.
* ``_NPZ_KEYS`` is the contract's own key set. Dropping two names from it is the
  single edit that makes "the fake emits the contract" mean the new contract.

Deliberately NOT changed: nothing here starts asserting that ``X_full`` is ABSENT.
Design section 9.5 says consumers must keep tolerating the key, and a test demanding
its absence would convert "not required" back into a requirement pointing the other
way -- which would fail against all 39 stored artifacts.
"""

from __future__ import annotations

import pathlib
import re
import sys

WT = pathlib.Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data-client--feature--drop-full-family--20260905-1215--7d5b2f60")
TESTS = WT / "tests/test_fake_client.py"

EDITS: list[tuple[str, str, int]] = [
    (
        '(X_train, y_train, X_test, y_test, X_full, y_full — all float32,',
        '(X_train, y_train, X_val, y_val, X_test, y_test — all float32,',
        1,
    ),
    (
        '_NPZ_KEYS = {"X_train", "y_train", "X_val", "y_val", "X_test", "y_test", "X_full", "y_full"}',
        '# The contract\'s key set. ``X_full`` / ``y_full`` left it with decision 11; a stored\n'
        '# artifact may still carry them and that is fine -- this is what the fake EMITS, not\n'
        '# what a reader must reject.\n'
        '_NPZ_KEYS = {"X_train", "y_train", "X_val", "y_val", "X_test", "y_test"}',
        1,
    ),
    # Feature / class dimension consistency: read val instead of full.
    (
        '        n_features_full = arrays["X_full"].shape[1]',
        '        n_features_val = arrays["X_val"].shape[1]',
        1,
    ),
    (
        '        assert n_features_train == n_features_test == n_features_full, f"Feature dimensions inconsistent: train={n_features_train}, " f"test={n_features_test}, full={n_features_full}"',
        '        assert n_features_train == n_features_test == n_features_val, f"Feature dimensions inconsistent: train={n_features_train}, " f"test={n_features_test}, val={n_features_val}"',
        1,
    ),
    (
        '        n_classes_full = arrays["y_full"].shape[1]',
        '        n_classes_val = arrays["y_val"].shape[1]',
        1,
    ),
    (
        '        assert n_classes_train == n_classes_test == n_classes_full, f"Class dimensions inconsistent: train={n_classes_train}, " f"test={n_classes_test}, full={n_classes_full}"',
        '        assert n_classes_train == n_classes_test == n_classes_val, f"Class dimensions inconsistent: train={n_classes_train}, " f"test={n_classes_test}, val={n_classes_val}"',
        1,
    ),
    # Split ratio: denominator is the partition sum, not an array length.
    (
        '        n_full = arrays["X_full"].shape[0]\n        actual_ratio = n_train / n_full',
        '        n_full = arrays["X_train"].shape[0] + arrays["X_val"].shape[0] + arrays["X_test"].shape[0]\n        actual_ratio = n_train / n_full',
        1,
    ),
    (
        '    for key in ("y_train", "y_test", "y_full"):',
        '    for key in ("y_train", "y_val", "y_test"):',
        1,
    ),
    (
        '        n_classes = arrays["y_full"].shape[1]',
        '        n_classes = arrays["y_train"].shape[1]',
        1,
    ),
]

UNION_OLD = '''    def test_full_dataset_is_union_of_the_three_partitions(self, fake_client: FakeDataClient) -> None:
        """X_full/y_full hold as many samples as X_train + X_val + X_test.
'''


def _replace(src: str, old: str, new: str, expected: int, label: str) -> str:
    found = src.count(old)
    if found != expected:
        print(f"REFUSING: {label} matched {found}x, expected {expected}", file=sys.stderr)
        raise SystemExit(1)
    return src.replace(old, new)


def main() -> int:
    src = TESTS.read_text()
    for old, new, expected in EDITS:
        src = _replace(src, old, new, expected, old.strip()[:60])

    # The union test: same property, new subject.
    if UNION_OLD in src:
        start = src.index(UNION_OLD)
        end = src.index("\n    def ", start + len(UNION_OLD))
        replacement = '''    def test_metadata_total_equals_the_partition_sum(self, fake_client: FakeDataClient) -> None:
        """``n_full`` is the partition sum -- there is no array left to compare against.

        This measured ``len(X_full) == n_train + n_val + n_test`` until decision 11
        removed ``X_full`` from the contract. The property it was really pinning is that
        the metadata's total agrees with the partitions, and that survives the array's
        removal: it just has to be read off the number rather than the array.
        """
        dataset_id = fake_client.create_dataset("spiral", {"n_points_per_spiral": 60, "seed": 5})["dataset_id"]
        arrays = fake_client.download_artifact_npz(dataset_id)
        meta = fake_client.get_dataset(dataset_id)["meta"]

        n_train = arrays["X_train"].shape[0]
        n_val = arrays["X_val"].shape[0]
        n_test = arrays["X_test"].shape[0]
        assert meta["n_full"] == n_train + n_val + n_test, f"n_full ({meta['n_full']}) != {n_train} + {n_val} + {n_test}"
        assert n_val > 0, "a zero validation partition would make the sum agree vacuously"
'''
        src = src[:start] + replacement + src[end:]
    else:
        print("REFUSING: the union test was not found", file=sys.stderr)
        return 1

    # Remaining shape reads on X_full/y_full in the generator tests: the fakes produce a
    # 0.8 / 0.1 / 0.1 carve, so a total is the sum and a width is any partition's width.
    src = re.sub(r'arrays\["X_full"\]\.shape\[1\]', 'arrays["X_train"].shape[1]', src)
    src = re.sub(r'arrays\["y_full"\]\.shape\[1\]', 'arrays["y_train"].shape[1]', src)
    src = re.sub(
        r'arrays\["X_full"\]\.shape\[0\]',
        '(arrays["X_train"].shape[0] + arrays["X_val"].shape[0] + arrays["X_test"].shape[0])',
        src,
    )
    src = re.sub(
        r'arrays\["y_full"\]\.shape\[0\]',
        '(arrays["y_train"].shape[0] + arrays["y_val"].shape[0] + arrays["y_test"].shape[0])',
        src,
    )
    TESTS.write_text(src)
    leftover = src.count("_full\"")
    print(f'tests updated; remaining `_full"` string literals: {leftover}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
