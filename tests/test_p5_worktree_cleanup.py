#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Hermetic gate for ``util/ad-hoc/2026-08-28_p5_worktree_cleanup.py``.

This is the sweeper that actually deletes worktrees. ``util/`` is outside every
pre-commit Python hook, so this unittest is the gate.

#1632 pins the independent second-opinion probe
(``2026-09-02_worktree_inuse_probe.py``): STRONG vs WEAK, self/parent exclusion.
Those tests cannot see this file. The load-bearing leftovers:

* ``pr_state`` must not conflate *no PR* with *the call failed*. A first version
  returned a plausible ``NONE`` for both; a false reason is what someone
  overrides, and then a live tree is removed.
* ``undisposable`` is the last line before ``worktree remove`` deletes ignored
  payload. ``*.log`` is disposable (including a nested ``logs/system.log``,
  because ``fnmatch`` ``*`` crosses ``/``); a ``logs/`` *directory* entry and
  any ``.h5`` are not — those need ``--harvest``.
* ``occupied`` is cwd-only. A cmdline mention is NOT occupancy (the ``pgrep -f``
  self-match class). A sibling prefix (``foo-extra`` vs ``foo``) is not inside.
* ``harvest`` copies, does not delete the source, and skips a missing path.

Never walks the host ``/proc``. Never calls live ``gh``.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-08-28_p5_worktree_cleanup.py"


def _load():
    spec = importlib.util.spec_from_file_location("p5_worktree_cleanup", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _proc_pid(proc_root: Path, pid: str, cwd: Path) -> None:
    entry = proc_root / pid
    entry.mkdir()
    os.symlink(str(cwd), entry / "cwd")


class PrStateNamingTest(unittest.TestCase):
    """Empty / null / failed ``gh`` must not print as each other."""

    def setUp(self) -> None:
        self.mod = _load()

    def _patch_run(self, replies: list[tuple[int, str, str]]) -> list[list]:
        calls: list[list] = []
        queue = list(replies)

        def fake_run(argv, cwd=None, check=False):  # noqa: ARG001
            calls.append(list(argv))
            rc, stdout, stderr = queue.pop(0)
            return subprocess.CompletedProcess(argv, rc, stdout, stderr)

        self.mod.run = fake_run
        return calls

    def test_empty_stdout_is_no_pr_on_head_not_none(self) -> None:
        self._patch_run([(0, "", "")])
        info, err = self.mod.pr_state("juniper-ml", "feat/x")
        self.assertEqual(info, "NO-PR-ON-HEAD")
        self.assertEqual(err, "")
        self.assertNotIn("NONE", info)

    def test_null_array_jq_is_no_pr_on_head(self) -> None:
        """``.[0] | ...`` over an empty array prints ``null null null``."""
        self._patch_run([(0, "null null null", "")])
        info, err = self.mod.pr_state("juniper-ml", "feat/x")
        self.assertEqual((info, err), ("NO-PR-ON-HEAD", ""))

    def test_three_failures_are_lookup_failed_not_no_pr(self) -> None:
        self._patch_run(
            [
                (1, "", "API rate limit"),
                (1, "", "API rate limit"),
                (1, "", "API rate limit"),
            ]
        )
        info, err = self.mod.pr_state("juniper-ml", "feat/x")
        self.assertEqual(info, "LOOKUP-FAILED")
        self.assertIn("rate limit", err)
        self.assertNotEqual(info, "NO-PR-ON-HEAD")

    def test_retries_then_accepts_a_merged_row(self) -> None:
        self._patch_run(
            [
                (1, "", "transient"),
                (1, "", "transient"),
                (0, "12 MERGED 2026-09-01T00:00:00Z", ""),
            ]
        )
        info, err = self.mod.pr_state("juniper-ml", "feat/x")
        self.assertEqual(info, "12 MERGED 2026-09-01T00:00:00Z")
        self.assertEqual(err, "")

    def test_open_is_not_merged(self) -> None:
        self._patch_run([(0, "12 OPEN ", "")])
        info, _err = self.mod.pr_state("juniper-ml", "feat/x")
        parts = info.split()
        self.assertGreaterEqual(len(parts), 2)
        self.assertNotEqual(parts[1], "MERGED")


class UndisposablePayloadTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = _load()

    def test_pycache_and_root_log_are_disposable(self) -> None:
        self.assertEqual(self.mod.undisposable(["__pycache__/", "custom.log"]), [])

    def test_nested_log_matches_star_log_because_fnmatch_crosses_slash(self) -> None:
        """``*.log`` matches ``logs/system.log``. That is current DISPOSABLE policy.

        The 2026-08-29 canopy evidence loss was a ``logs/system.log``. A later
        ``*.log`` entry makes that *file* path disposable; a ``logs/`` *directory*
        entry still blocks. Pin both so a DISPOSABLE edit is intentional.
        """
        self.assertEqual(self.mod.undisposable(["logs/system.log"]), [])
        self.assertEqual(self.mod.undisposable(["logs/"]), ["logs/"])

    def test_h5_snapshot_is_not_disposable(self) -> None:
        self.assertEqual(
            self.mod.undisposable(["artifacts/run.h5", ".pytest_cache/"]),
            ["artifacts/run.h5"],
        )

    def test_htmlcov_without_trailing_slash_still_matches_dir_pattern(self) -> None:
        self.assertEqual(self.mod.undisposable(["htmlcov"]), [])


class OccupiedCwdOnlyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = _load()

    def test_cwd_inside_is_occupied_sibling_prefix_is_not(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            wt = root / "foo"
            sibling = root / "foo-extra"
            wt.mkdir()
            sibling.mkdir()
            proc = root / "proc"
            proc.mkdir()
            _proc_pid(proc, "100", wt)
            _proc_pid(proc, "101", sibling)
            nested = wt / "src"
            nested.mkdir()
            _proc_pid(proc, "102", nested)
            held = self.mod.occupied(wt, proc_root=proc)
            self.assertEqual(sorted(held), ["100", "102"])
            self.assertNotIn("101", held)

    def test_cmdline_is_never_consulted(self) -> None:
        """``pgrep -f`` matches its own wrapper. Occupancy is cwd, never argv."""
        with TemporaryDirectory() as td:
            root = Path(td)
            wt = root / "tree"
            elsewhere = root / "elsewhere"
            wt.mkdir()
            elsewhere.mkdir()
            proc = root / "proc"
            proc.mkdir()
            entry = proc / "200"
            entry.mkdir()
            os.symlink(str(elsewhere), entry / "cwd")
            (entry / "cmdline").write_bytes(b"python\x00" + str(wt).encode() + b"\x00")
            self.assertEqual(self.mod.occupied(wt, proc_root=proc), [])

    def test_unreadable_cwd_is_skipped_not_occupied(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            wt = root / "tree"
            wt.mkdir()
            proc = root / "proc"
            proc.mkdir()
            (proc / "300").mkdir()  # no cwd symlink → OSError → skip
            self.assertEqual(self.mod.occupied(wt, proc_root=proc), [])


class HarvestCopyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = _load()

    def test_copies_file_and_dir_and_skips_missing(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            wt = root / "juniper-ml--feat--x"
            dest = root / "harvest"
            (wt / "logs").mkdir(parents=True)
            (wt / "logs" / "system.log").write_text("burst\n", encoding="utf-8")
            (wt / "keep.dat").write_text("payload", encoding="utf-8")
            saved = self.mod.harvest(
                wt,
                ["logs/", "keep.dat", "already-gone.dat"],
                dest,
            )
            self.assertEqual(sorted(saved), ["keep.dat", "logs/"])
            self.assertEqual((dest / wt.name / "keep.dat").read_text(encoding="utf-8"), "payload")
            self.assertEqual(
                (dest / wt.name / "logs" / "system.log").read_text(encoding="utf-8"),
                "burst\n",
            )
            self.assertTrue((wt / "keep.dat").exists(), "harvest must not delete the source")
            self.assertFalse((dest / wt.name / "already-gone.dat").exists())


class IgnoredEntriesParseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = _load()

    def test_strips_the_porcelain_bang_bang_prefix(self) -> None:
        def fake_run(argv, cwd=None, check=False):  # noqa: ARG001
            self.assertIn("--ignored", argv)
            return SimpleNamespace(stdout="!! logs/\n!! artifacts/run.h5\n M tracked.py\n")

        self.mod.run = fake_run
        self.assertEqual(
            self.mod.ignored_entries(Path("/unused")),
            ["logs/", "artifacts/run.h5"],
        )


if __name__ == "__main__":
    unittest.main()
