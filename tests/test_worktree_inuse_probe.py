#!/usr/bin/env python3
"""Hermetic coverage for the #1579 worktree in-use probe.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/2026-09-02_worktree_inuse_probe.py`` is the independent second
opinion for the worktree sweep. A false CLEAR deletes a live tree. A false
REFUSE from the probe's own argv trains operators to ignore it. The first run
reported every tree IN USE because the checker named the paths as arguments.

These pins walk a fake ``proc_root``, never the host ``/proc``. ``util/`` is
not pre-commit-lint-gated, so this unittest is the gate.
"""

from __future__ import annotations

import importlib.util
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-09-02_worktree_inuse_probe.py"

_spec = importlib.util.spec_from_file_location("worktree_inuse_probe", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(mod)


def _write_proc(
    proc_root: Path,
    pid: str,
    *,
    cwd: Path | None = None,
    cmdline: str | None = None,
    fds: list[Path] | None = None,
    make_fd_dir: bool = True,
) -> None:
    d = proc_root / pid
    d.mkdir()
    if cwd is not None:
        os.symlink(str(cwd), d / "cwd")
    if cmdline is not None:
        (d / "cmdline").write_bytes(cmdline.replace(" ", "\0").encode() + b"\0")
    if make_fd_dir:
        fd_dir = d / "fd"
        fd_dir.mkdir()
        for i, target in enumerate(fds or [], start=3):
            os.symlink(str(target), fd_dir / str(i))


def _run(targets: list[Path], proc_root: Path) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.probe(targets, proc_root=str(proc_root))
    return rc, buf.getvalue()


class WorktreeInuseProbeTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.proc = self.root / "proc"
        self.proc.mkdir()
        self.tree = (self.root / "worktrees" / "juniper-ml--feat--20260902-0000--abcd1234").resolve()
        self.tree.mkdir(parents=True)
        (self.tree / "held.py").write_text("# fixture\n", encoding="utf-8")
        self.elsewhere = (self.root / "elsewhere").resolve()
        self.elsewhere.mkdir()
        self.sibling = Path(str(self.tree) + "-extra")
        self.sibling.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_cwd_exact_or_nested_is_strong_refuse(self) -> None:
        nested = self.tree / "src"
        nested.mkdir()
        _write_proc(self.proc, "1001", cwd=self.tree, cmdline="python worker.py")
        _write_proc(self.proc, "1002", cwd=nested, cmdline="bash")
        rc, out = _run([self.tree], self.proc)
        self.assertEqual(rc, 1, msg=out)
        self.assertIn("REFUSE:", out)
        self.assertIn("IN USE", out)
        self.assertIn("STRONG pid 1001  via cwd", out)
        self.assertIn("STRONG pid 1002  via cwd", out)
        self.assertNotIn("CAUTION:", out)

    def test_sibling_prefix_near_miss_is_not_strong(self) -> None:
        # ``cwd.startswith(t)`` without ``+ sep`` would treat foo-extra as inside foo.
        _write_proc(self.proc, "1100", cwd=self.sibling, cmdline="python")
        rc, out = _run([self.tree], self.proc)
        self.assertEqual(rc, 0, msg=out)
        self.assertIn("CLEAR:", out)
        self.assertNotIn("REFUSE:", out)
        self.assertNotIn("STRONG", out)
        self.assertIn("0 strong", out)

    def test_open_fd_inside_target_is_strong_refuse(self) -> None:
        held = self.tree / "held.py"
        _write_proc(
            self.proc,
            "1200",
            cwd=self.elsewhere,
            cmdline="vim held.py",
            fds=[held],
        )
        rc, out = _run([self.tree], self.proc)
        self.assertEqual(rc, 1, msg=out)
        self.assertIn("REFUSE:", out)
        self.assertIn("open fd 3 ->", out)
        self.assertIn(str(held), out)

    def test_cmdline_mention_alone_is_weak_caution_not_refuse(self) -> None:
        _write_proc(
            self.proc,
            "1300",
            cwd=self.elsewhere,
            cmdline=f"python {self.tree}/util/foo.py",
        )
        rc, out = _run([self.tree], self.proc)
        self.assertEqual(rc, 0, msg=out)
        self.assertIn("CAUTION:", out)
        self.assertNotIn("REFUSE:", out)
        self.assertIn("review", out)
        self.assertIn("weak   pid 1300  via cmdline mention", out)
        self.assertIn("0 strong", out)
        self.assertIn("1 weak", out)

    def test_self_and_parent_cmdline_mentions_are_excluded_from_weak(self) -> None:
        _write_proc(
            self.proc,
            str(os.getpid()),
            cwd=self.elsewhere,
            cmdline=f"python {SCRIPT} {self.tree}",
        )
        _write_proc(
            self.proc,
            str(os.getppid()),
            cwd=self.elsewhere,
            cmdline=f"bash -c python {SCRIPT} {self.tree}",
        )
        rc, out = _run([self.tree], self.proc)
        self.assertEqual(rc, 0, msg=out)
        self.assertIn("CLEAR:", out)
        self.assertNotIn("CAUTION:", out)
        self.assertNotIn("REFUSE:", out)
        self.assertIn("0 weak", out)
        self.assertNotIn(f"pid {os.getpid()}", out)
        self.assertNotIn(f"pid {os.getppid()}", out)

    def test_unreadable_proc_is_counted_not_treated_as_in_use(self) -> None:
        _write_proc(self.proc, "1400", make_fd_dir=False)
        rc, out = _run([self.tree], self.proc)
        self.assertEqual(rc, 0, msg=out)
        self.assertIn("CLEAR:", out)
        self.assertNotIn("REFUSE:", out)
        self.assertIn("1 process(es) unreadable", out)
        self.assertIn("NOT checked", out)

    def test_no_argv_returns_usage_exit_2(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = mod.main([])
        self.assertEqual(rc, 2)
        self.assertIn("INDEPENDENT second opinion", buf.getvalue())

    def test_no_hits_is_clear(self) -> None:
        _write_proc(self.proc, "1500", cwd=self.elsewhere, cmdline="sleep 1")
        rc, out = _run([self.tree], self.proc)
        self.assertEqual(rc, 0, msg=out)
        self.assertIn("CLEAR:", out)
        self.assertRegex(out, r"\[\s*free\s*\]")
        self.assertNotIn("REFUSE:", out)
        self.assertNotIn("CAUTION:", out)


if __name__ == "__main__":
    unittest.main()
