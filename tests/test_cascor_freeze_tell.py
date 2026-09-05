#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/ad-hoc/cascor_freeze_tell.py`` -- the cascor-primary freeze tell.

``util/`` is outside every pre-commit Python hook's scope, so this suite is the gate.
Hermetic: every ``/proc`` walk is a TemporaryDirectory; ``glob.glob("/proc/[0-9]*")``
is patched so ``main()`` never reads the host process table.

What it pins, and why it mattered:

- ``"juniper-cascor" in cwd`` is a substring test. It false-freezes
  ``juniper-cascor-client`` / ``juniper-cascor-worker`` and centralized
  ``worktrees/juniper-cascor--*``. The tell must use an exact path prefix plus
  ``os.sep``, and must exclude both worktree roots.
- cwd is not sufficient. A process can import the primary from ``/tmp`` via the
  editable finder; cmdline / environ / fd / maps each independently produce
  evidence. An unreadable cwd must not abandon the rest of the scan.
- ``main()`` exits 1 iff any hold is found, 0 when none -- operators treat a
  clean result as "no user-owned importer", never as "no importer exists".
"""

from __future__ import annotations

import importlib.util
import io
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "cascor_freeze_tell.py"


def _load():
    spec = importlib.util.spec_from_file_location("cascor_freeze_tell", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


tell = _load()
PRIMARY = tell.PRIMARY
CLIENT = PRIMARY + "-client"
WORKER = PRIMARY + "-worker"
WORKTREE = os.path.join("/home/pcalnon/Development/python/Juniper/worktrees", "juniper-cascor--task")
CLAUDE_WORKTREE = os.path.join(PRIMARY, ".claude", "worktrees", "agent-1")


class FakeProc:
    """A /proc/<pid> lookalike. Targets do not need to exist on disk."""

    def __init__(self, root: Path, pid: str = "4242") -> None:
        self.dir = root / pid
        self.dir.mkdir()
        (self.dir / "comm").write_text("python\n", encoding="utf-8")

    def set_cwd(self, target: str) -> None:
        os.symlink(target, self.dir / "cwd")

    def set_cmdline(self, *tokens: str) -> None:
        (self.dir / "cmdline").write_bytes(b"\0".join(t.encode() for t in tokens) + b"\0")

    def set_environ(self, mapping: dict[str, str]) -> None:
        (self.dir / "environ").write_text("".join(f"{k}={v}\0" for k, v in mapping.items()), encoding="utf-8")

    def add_fd(self, target: str, fd: str = "3") -> None:
        fd_dir = self.dir / "fd"
        fd_dir.mkdir(exist_ok=True)
        os.symlink(target, fd_dir / fd)

    def set_maps(self, path: str) -> None:
        (self.dir / "maps").write_text(f"7f00-7f01 r-xp 00000000 00:00 0 {path}\n", encoding="utf-8")


class IsPrimaryPathTest(unittest.TestCase):
    def test_primary_root_and_src_are_holds(self) -> None:
        self.assertTrue(tell._is_primary_path(PRIMARY))
        self.assertTrue(tell._is_primary_path(os.path.join(PRIMARY, "src", "cascade_correlation.py")))

    def test_sibling_repos_are_not_holds(self) -> None:
        # ``"juniper-cascor" in cwd`` and ``startswith(PRIMARY)`` without os.sep
        # both false-freeze these two siblings.
        self.assertFalse(tell._is_primary_path(CLIENT))
        self.assertFalse(tell._is_primary_path(os.path.join(CLIENT, "src")))
        self.assertFalse(tell._is_primary_path(WORKER))
        self.assertFalse(tell._is_primary_path(os.path.join(WORKER, "src")))

    def test_both_worktree_roots_are_excluded(self) -> None:
        self.assertFalse(tell._is_primary_path(WORKTREE))
        self.assertFalse(tell._is_primary_path(os.path.join(WORKTREE, "src")))
        self.assertFalse(tell._is_primary_path(CLAUDE_WORKTREE))
        self.assertFalse(tell._is_primary_path(os.path.join(CLAUDE_WORKTREE, "src")))

    def test_empty_and_unrelated_paths_are_not_holds(self) -> None:
        self.assertFalse(tell._is_primary_path(""))
        self.assertFalse(tell._is_primary_path("/tmp"))
        self.assertFalse(tell._is_primary_path("/home/pcalnon/Development/python/Juniper"))

    def test_normpath_collapses_dotdot_inside_primary(self) -> None:
        self.assertTrue(tell._is_primary_path(os.path.join(PRIMARY, "src", "..", "pyproject.toml")))


class ReadTest(unittest.TestCase):
    def test_missing_file_is_empty_not_raised(self) -> None:
        self.assertEqual(tell._read("/no/such/cascor-freeze-tell-file"), [])

    def test_nul_split_drops_empty_tokens(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "cmdline"
            path.write_bytes(b"python\0\0" + PRIMARY.encode() + b"\0")
            self.assertEqual(tell._read(str(path), split_nul=True), ["python", PRIMARY])


class EvidenceTest(unittest.TestCase):
    def test_cwd_on_primary_is_evidence_client_is_not(self) -> None:
        with TemporaryDirectory() as tmp:
            hit = FakeProc(Path(tmp), "1")
            hit.set_cwd(PRIMARY)
            miss = FakeProc(Path(tmp), "2")
            miss.set_cwd(CLIENT)
            self.assertEqual(tell._evidence(str(hit.dir)), [f"cwd={PRIMARY}"])
            self.assertEqual(tell._evidence(str(miss.dir)), [])

    def test_unreadable_cwd_still_scans_cmdline(self) -> None:
        # No cwd symlink -- readlink raises. The documented first-version miss
        # abandoned the process here and would miss a /tmp importer.
        with TemporaryDirectory() as tmp:
            proc = FakeProc(Path(tmp))
            proc.set_cmdline("python", "-c", "import cascade_correlation", os.path.join(PRIMARY, "src"))
            found = tell._evidence(str(proc.dir))
            self.assertTrue(any(item.startswith("argv=") for item in found), found)

    def test_environ_fd_and_maps_each_independently_catch(self) -> None:
        with TemporaryDirectory() as tmp:
            env_proc = FakeProc(Path(tmp), "10")
            env_proc.set_environ({"PATH": f"/usr/bin:{os.path.join(PRIMARY, 'src')}"})
            fd_proc = FakeProc(Path(tmp), "11")
            fd_proc.add_fd(os.path.join(PRIMARY, "src", "cascade_correlation.py"))
            map_proc = FakeProc(Path(tmp), "12")
            map_proc.set_maps(os.path.join(PRIMARY, "src", "cascade_correlation.cpython-so"))
            self.assertTrue(any(item.startswith("env=PATH") for item in tell._evidence(str(env_proc.dir))))
            self.assertTrue(any(item.startswith("fd=") for item in tell._evidence(str(fd_proc.dir))))
            self.assertTrue(any(item.startswith("map=") for item in tell._evidence(str(map_proc.dir))))

    def test_maps_relative_path_is_not_evidence(self) -> None:
        with TemporaryDirectory() as tmp:
            proc = FakeProc(Path(tmp))
            proc.set_maps("juniper-cascor/src/foo.so")
            self.assertEqual(tell._evidence(str(proc.dir)), [])


class MainTest(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_glob = tell.glob.glob

    def tearDown(self) -> None:
        tell.glob.glob = self._orig_glob

    def _scan_only(self, *proc_dirs: Path) -> None:
        real = self._orig_glob

        def fake(pattern, *args, **kwargs):
            if pattern == "/proc/[0-9]*":
                return [str(p) for p in proc_dirs]
            return real(pattern, *args, **kwargs)

        tell.glob.glob = fake

    def test_main_exits_1_when_a_process_holds_primary(self) -> None:
        with TemporaryDirectory() as tmp:
            proc = FakeProc(Path(tmp))
            proc.set_cwd(PRIMARY)
            self._scan_only(proc.dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = tell.main()
            self.assertEqual(rc, 1)
            self.assertIn("FREEZE IN FORCE", buf.getvalue())
            self.assertIn("HOLDS-PRIMARY", buf.getvalue())

    def test_main_exits_0_when_only_siblings_match_the_old_substring(self) -> None:
        with TemporaryDirectory() as tmp:
            client = FakeProc(Path(tmp), "7")
            client.set_cwd(CLIENT)
            worker = FakeProc(Path(tmp), "8")
            worker.set_cmdline("python", WORKER)
            empty = FakeProc(Path(tmp), "9")
            self._scan_only(client.dir, worker.dir, empty.dir)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = tell.main()
            self.assertEqual(rc, 0)
            self.assertIn("freeze NOT in force", buf.getvalue())
            self.assertNotIn("HOLDS-PRIMARY", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
