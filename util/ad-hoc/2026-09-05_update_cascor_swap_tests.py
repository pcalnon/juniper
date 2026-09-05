#!/usr/bin/env python3
"""Update cascor's reload-dataset swap tests for the three-way partition.

Project:     Juniper
Sub-Project: juniper-cascor
Author:      Paul Calnon
Status:      ad-hoc, single-use (partition arc, Chunk 4)

Three edits, and only one of them is a renumbering:

* ``test_happy_path_without_validation_arrays`` asserted that a train-only
  artifact loads happily. Under §6.1 rule 3 that is now a refusal, so the test's
  premise is gone and its name would be a lie -- it becomes
  ``test_train_only_artifact_is_refused``.
* the two "validation" guard tests drove ``X_test`` / ``y_test``, because before
  the third partition existed ``X_test`` WAS what cascor validated on. They are
  repointed at ``X_val`` / ``y_val``, which makes their existing names true, and
  ``test``-split siblings are added so both partitions are guarded.
"""

from __future__ import annotations

import pathlib
import sys

PATH = pathlib.Path(
    "/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--feature--consume-x-val--20260905-0133--90071c56/src/tests/unit/api/test_lifecycle_manager_swap.py"
)

EDITS: list[tuple[str, str]] = [
    (
        '''    def test_happy_path_without_validation_arrays(self, mgr):
        arrays = {
            "X_train": np.zeros((5, 2), dtype=np.float32),
            "y_train": np.zeros((5, 2), dtype=np.float32),
        }
        mod, client = _fake_data_client_module(arrays=arrays)
        with patch.dict(sys.modules, {"juniper_data_client": mod}), patch("api.secrets.get_secret", return_value=None), patch("api.settings.Settings"):
            mgr._reload_dataset(dataset_type="xor")
        assert mgr._val_x is None and mgr._val_y is None
''',
        '''    def test_train_only_artifact_is_refused(self, mgr):
        """§6.1 rule 3: no val AND no test means nothing held out to report from.

        This previously asserted the opposite -- that a train-only artifact loads
        happily with ``_val_x`` left None. It did, and then scored the training
        rows under an evaluation label, which is the defect the three-way
        partition removes. No switch re-enables it.
        """
        arrays = {
            "X_train": np.zeros((5, 2), dtype=np.float32),
            "y_train": np.zeros((5, 2), dtype=np.float32),
        }
        mod, client = _fake_data_client_module(arrays=arrays)
        with patch.dict(sys.modules, {"juniper_data_client": mod}), patch("api.secrets.get_secret", return_value=None), patch("api.settings.Settings"):
            with pytest.raises(RuntimeError, match="NEITHER a validation split"):
                mgr._reload_dataset(dataset_type="xor")
''',
    ),
    (
        '''    def test_partial_validation_split_raises(self, mgr):
        """One of X_test/y_test without the other is a malformed artifact."""
        arrays = {
            "X_train": np.zeros((4, 2), dtype=np.float32),
            "y_train": np.zeros((4, 2), dtype=np.float32),
            "X_test": np.zeros((2, 2), dtype=np.float32),
        }
''',
        '''    def test_partial_validation_split_raises(self, mgr):
        """One of X_val/y_val without the other is a malformed artifact.

        Repointed from X_test to X_val: this test's NAME was already the right
        one, but before the third partition existed the split cascor validated on
        was the artifact's ``X_test``. Now it is ``X_val``, and the test-split
        sibling below covers the other half.
        """
        arrays = {
            "X_train": np.zeros((4, 2), dtype=np.float32),
            "y_train": np.zeros((4, 2), dtype=np.float32),
            "X_val": np.zeros((2, 2), dtype=np.float32),
        }
''',
    ),
    (
        '''    def test_validation_sample_count_mismatch_raises(self, mgr):
        arrays = {
            "X_train": np.zeros((4, 2), dtype=np.float32),
            "y_train": np.zeros((4, 2), dtype=np.float32),
            "X_test": np.zeros((2, 2), dtype=np.float32),
            "y_test": np.zeros((1, 2), dtype=np.float32),
        }
        mod, _ = _fake_data_client_module(arrays=arrays)
        with patch.dict(sys.modules, {"juniper_data_client": mod}), patch("api.secrets.get_secret", return_value=None), patch("api.settings.Settings"):
            with pytest.raises(RuntimeError, match="validation sample count mismatch"):
                mgr._reload_dataset(dataset_type="spiral")
        assert mgr._train_x is None and mgr._val_x is None
''',
        '''    def test_validation_sample_count_mismatch_raises(self, mgr):
        arrays = {
            "X_train": np.zeros((4, 2), dtype=np.float32),
            "y_train": np.zeros((4, 2), dtype=np.float32),
            "X_val": np.zeros((2, 2), dtype=np.float32),
            "y_val": np.zeros((1, 2), dtype=np.float32),
        }
        mod, _ = _fake_data_client_module(arrays=arrays)
        with patch.dict(sys.modules, {"juniper_data_client": mod}), patch("api.secrets.get_secret", return_value=None), patch("api.settings.Settings"):
            with pytest.raises(RuntimeError, match="validation sample count mismatch"):
                mgr._reload_dataset(dataset_type="spiral")
        assert mgr._train_x is None and mgr._val_x is None

    def test_partial_test_split_raises(self, mgr):
        """The reported partition gets the same guard as the in-loop one.

        Both run through one helper precisely so they cannot drift; this is the
        half that would silently stop being checked if they ever did.
        """
        arrays = {
            "X_train": np.zeros((4, 2), dtype=np.float32),
            "y_train": np.zeros((4, 2), dtype=np.float32),
            "X_val": np.zeros((2, 2), dtype=np.float32),
            "y_val": np.zeros((2, 2), dtype=np.float32),
            "X_test": np.zeros((2, 2), dtype=np.float32),
        }
        mod, _ = _fake_data_client_module(arrays=arrays)
        with patch.dict(sys.modules, {"juniper_data_client": mod}), patch("api.secrets.get_secret", return_value=None), patch("api.settings.Settings"):
            with pytest.raises(RuntimeError, match="partial test split"):
                mgr._reload_dataset(dataset_type="spiral")

    def test_validation_feature_count_mismatch_raises(self, mgr):
        """§6a: a val split whose feature count differs from train is malformed.

        A forward pass on it would fail mid-run, or worse, succeed on a
        coincidentally-broadcastable shape.
        """
        arrays = {
            "X_train": np.zeros((4, 2), dtype=np.float32),
            "y_train": np.zeros((4, 2), dtype=np.float32),
            "X_val": np.zeros((2, 5), dtype=np.float32),
            "y_val": np.zeros((2, 2), dtype=np.float32),
        }
        mod, _ = _fake_data_client_module(arrays=arrays)
        with patch.dict(sys.modules, {"juniper_data_client": mod}), patch("api.secrets.get_secret", return_value=None), patch("api.settings.Settings"):
            with pytest.raises(RuntimeError, match="validation feature count mismatch"):
                mgr._reload_dataset(dataset_type="spiral")
''',
    ),
]


def main() -> int:
    src = PATH.read_text()
    for old, new in EDITS:
        if src.count(old) != 1:
            print(f"pattern matched {src.count(old)} times, refusing:\n{old[:120]}", file=sys.stderr)
            return 1
        src = src.replace(old, new)
    PATH.write_text(src)
    print("test_lifecycle_manager_swap.py updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
