#!/usr/bin/env python3
"""Complementary leftover the ``--root``-always snapshot suites cannot see.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

Every existing snapshot CLI helper injects ``--root``. ``default_root()`` and
``default_run_root()`` therefore have zero coverage. Those two resolvers are the
dual-use trap the operator docs name: ``JUNIPER_CASCOR_SNAPSHOTS_DIR`` is both
cascor's write directory AND the sidecar chain's default ``--root``. A revert
that ignores the env, treats blank as a path, prefers the env over an explicit
``--root``, or hardcodes the fallback in one of the four tools silently
retargets the ~28k archive (or writes sidecars into experiment scratch). The
chain-script grep cannot see a Python resolver change.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path

import h5py
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("snapshot_index", REPO_ROOT / "util" / "snapshot_index.py")
snapshot_index = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(snapshot_index)

CHAIN_TOOLS = (
    REPO_ROOT / "util" / "snapshot_index.py",
    REPO_ROOT / "util" / "snapshot_classify.py",
    REPO_ROOT / "util" / "snapshot_backfill.py",
    REPO_ROOT / "util" / "snapshot_attribute.py",
)


@contextmanager
def env_var(key: str, value: "str | None"):
    """Set or unset one env var, then restore the prior value."""
    previous = os.environ.get(key)
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value
    try:
        yield
    finally:
        os.environ.pop(key, None)
        if previous is not None:
            os.environ[key] = previous


def write_snapshot(root: Path, name: str, *, provenance: "dict | None" = None) -> Path:
    """A structurally plausible snapshot, written the way cascor writes attrs."""
    path = root / name
    with h5py.File(path, "w") as hf:
        hf.attrs["created"] = np.bytes_("2026-08-21T12:00:00.000000")
        hf.create_group("meta")
        hf.create_group("arch")
        if provenance:
            group = hf.create_group("provenance")
            for key, value in provenance.items():
                group.attrs[key] = np.bytes_(value)
    return path


def run_main(*argv: str) -> "tuple[int, str]":
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        rc = snapshot_index.main(list(argv))
    return rc, buf.getvalue()


class DefaultRootTest(unittest.TestCase):
    """``JUNIPER_CASCOR_SNAPSHOTS_DIR`` is blank-is-unset, matching cascor."""

    def test_env_override_wins(self) -> None:
        with env_var(snapshot_index.DEFAULT_ROOT_ENV, "/tmp/scratch-snapshots"):
            self.assertEqual(snapshot_index.default_root(), Path("/tmp/scratch-snapshots"))

    def test_blank_env_is_unset(self) -> None:
        """``export JUNIPER_CASCOR_SNAPSHOTS_DIR=`` must not resolve to Path('')."""
        with env_var(snapshot_index.DEFAULT_ROOT_ENV, ""):
            self.assertEqual(snapshot_index.default_root(), snapshot_index.DEFAULT_ROOT_FALLBACK)

    def test_whitespace_env_is_unset(self) -> None:
        with env_var(snapshot_index.DEFAULT_ROOT_ENV, "   "):
            self.assertEqual(snapshot_index.default_root(), snapshot_index.DEFAULT_ROOT_FALLBACK)

    def test_unset_uses_fallback(self) -> None:
        with env_var(snapshot_index.DEFAULT_ROOT_ENV, None):
            self.assertEqual(snapshot_index.default_root(), snapshot_index.DEFAULT_ROOT_FALLBACK)

    def test_expanduser(self) -> None:
        with env_var(snapshot_index.DEFAULT_ROOT_ENV, "~/cascor-snapshots"):
            self.assertEqual(snapshot_index.default_root(), Path("~/cascor-snapshots").expanduser())


class DefaultRootCliTest(unittest.TestCase):
    """``main()`` uses the resolver when ``--root`` is omitted, and ``--root`` wins."""

    def test_missing_env_root_is_named_in_exit_2(self) -> None:
        missing = Path("/tmp/does-not-exist-snapshot-root-061c")
        with env_var(snapshot_index.DEFAULT_ROOT_ENV, str(missing)):
            rc, text = run_main("--stats")
        self.assertEqual(rc, 2)
        self.assertIn(str(missing), text)

    def test_scan_uses_env_root_not_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_snapshot(root, "cascor_snapshot_env.h5")
            with env_var(snapshot_index.DEFAULT_ROOT_ENV, str(root)):
                rc, text = run_main("--scan")
            self.assertEqual(rc, 0, text)
            self.assertTrue((root / snapshot_index.INDEX_NAME).is_file())
            self.assertIn("indexed 1", text)

    def test_explicit_root_wins_over_env(self) -> None:
        """The documented remedy is ``--root``. If the env wins, that remedy is a no-op."""
        with tempfile.TemporaryDirectory() as env_tmp, tempfile.TemporaryDirectory() as flag_tmp:
            env_root = Path(env_tmp)
            flag_root = Path(flag_tmp)
            write_snapshot(env_root, "cascor_snapshot_env.h5")
            write_snapshot(flag_root, "cascor_snapshot_flag.h5")
            with env_var(snapshot_index.DEFAULT_ROOT_ENV, str(env_root)):
                rc, text = run_main("--root", str(flag_root), "--scan")
            self.assertEqual(rc, 0, text)
            self.assertTrue((flag_root / snapshot_index.INDEX_NAME).is_file())
            self.assertFalse((env_root / snapshot_index.INDEX_NAME).exists())


class DefaultRunRootTest(unittest.TestCase):
    """``JUNIPER_EXP_RUN_ROOT`` follows the same blank-is-unset contract."""

    def test_env_override_wins(self) -> None:
        with env_var(snapshot_index.DEFAULT_RUN_ROOT_ENV, "/tmp/scratch-runs"):
            self.assertEqual(snapshot_index.default_run_root(), Path("/tmp/scratch-runs"))

    def test_blank_env_is_unset(self) -> None:
        with env_var(snapshot_index.DEFAULT_RUN_ROOT_ENV, ""):
            self.assertEqual(snapshot_index.default_run_root(), snapshot_index.DEFAULT_RUN_ROOT_FALLBACK)

    def test_unset_uses_fallback(self) -> None:
        with env_var(snapshot_index.DEFAULT_RUN_ROOT_ENV, None):
            self.assertEqual(snapshot_index.default_run_root(), snapshot_index.DEFAULT_RUN_ROOT_FALLBACK)


class DefaultRunRootCliTest(unittest.TestCase):
    """``--dataset-id`` without ``--run-root`` must honour the env, not a hardcoded fallback."""

    def test_dataset_id_without_run_root_uses_env(self) -> None:
        with tempfile.TemporaryDirectory() as snap_tmp, tempfile.TemporaryDirectory() as run_tmp:
            snap_root = Path(snap_tmp)
            run_root = Path(run_tmp)
            write_snapshot(snap_root, "cascor_snapshot_j.h5", provenance={"run_id": "run-1"})
            manifest_dir = run_root / "run-1"
            manifest_dir.mkdir()
            (manifest_dir / "manifest.json").write_text(json.dumps({"dataset": {"dataset_id": "spiral-1.0.0-abc"}}))
            snapshot_index.scan(snap_root)
            with env_var(snapshot_index.DEFAULT_RUN_ROOT_ENV, str(run_root)):
                rc, out = run_main("--root", str(snap_root), "--dataset-id", "spiral-1.0.0-abc", "--json")
            self.assertEqual(rc, 0, out)
            rows = json.loads(out)
            self.assertEqual([row["name"] for row in rows], ["cascor_snapshot_j.h5"])
            self.assertEqual(rows[0]["dataset"]["dataset_id"], "spiral-1.0.0-abc")


class SharedContractTest(unittest.TestCase):
    """All four chain tools must keep calling the shared resolver.

    Hardcoding ``DEFAULT_ROOT_FALLBACK`` in one tool would make that stage ignore
    the env while its siblings honour it — the operator then indexes one tree
    and classifies another.
    """

    def test_all_four_tools_call_default_root(self) -> None:
        for path in CHAIN_TOOLS:
            text = path.read_text(encoding="utf-8")
            self.assertIn(
                "root = args.root or default_root()",
                text,
                f"{path.name} must resolve --root through default_root(), not a hardcoded fallback",
            )

    def test_index_run_root_uses_the_resolver(self) -> None:
        text = (REPO_ROOT / "util" / "snapshot_index.py").read_text(encoding="utf-8")
        self.assertIn("run_root = args.run_root or default_run_root()", text)


# Added on harvest. Without this block `python3 tests/test_snapshot_index_root_resolution.py`
# runs ZERO tests and exits 0 -- a silent pass indistinguishable from a real one. The
# module form finds all 14. Keep this LAST: classes defined below `unittest.main()` are
# invisible to the direct form, so the two entry points would report different counts
# while both printing OK.
if __name__ == "__main__":
    unittest.main()
