"""Complementary guards for ``util/experiments/list_runs.py`` classify / --state.

``tests/test_list_runs.py`` covers the happy-path states and the prune
``--yes`` / ``--dry-run`` gates. It never has teardown.json and a live
pid together, never has a live pid whose cmdline does not match, never
has two pidfiles, and never exercises ``--state``. Those holes are how
``--prune --yes`` either deletes a live experiment's evidence or leaks
torn-down / recycled-PID runs forever.

Hermetic RUN_ROOT fixtures only. Live-pid arms spawn ``sleep`` the same
way the sibling suite does — no launcher, no services.
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "experiments" / "list_runs.py"

spec = importlib.util.spec_from_file_location("list_runs_classify_guards", MODULE_PATH)
list_runs = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(list_runs)


def _mk_run(root: Path, run_id: str, *, torn_down: bool = False) -> Path:
    run = root / run_id
    (run / "logs").mkdir(parents=True)
    (run / "ports.json").write_text(json.dumps({"run_id": run_id, "experiment": "exp", "data": 8110}))
    if torn_down:
        (run / "teardown.json").write_text(json.dumps({"run_id": run_id}))
    return run


def _proc_cmdline(pid: int) -> str:
    return Path(f"/proc/{pid}/cmdline").read_bytes().decode().replace("\0", " ")


class _LiveProc:
    """Own a short-lived sleep so pidfile arms can record a real /proc entry."""

    def __enter__(self) -> "_LiveProc":
        self.proc = subprocess.Popen(["sleep", "60"])
        time.sleep(0.1)
        return self

    def __exit__(self, *exc: object) -> None:
        self.proc.kill()
        self.proc.wait()

    @property
    def pid(self) -> int:
        return self.proc.pid

    @property
    def cmdline(self) -> str:
        return _proc_cmdline(self.pid)


def _record_pid(run: Path, proc: _LiveProc, *, cmdline: str | None = None, name: str = "svc") -> None:
    (run / f"{name}.pid").write_text(f"{proc.pid}\n")
    (run / f"{name}.cmdline").write_text(proc.cmdline if cmdline is None else cmdline)


class PidAliveGuardTest(unittest.TestCase):
    def test_match_is_alive(self) -> None:
        with _LiveProc() as proc:
            self.assertTrue(list_runs._pid_alive_with_cmdline(proc.pid, proc.cmdline))

    def test_mismatch_is_not_alive(self) -> None:
        with _LiveProc() as proc:
            self.assertFalse(list_runs._pid_alive_with_cmdline(proc.pid, "not-this-process"))

    def test_empty_recorded_cmdline_never_matches(self) -> None:
        with _LiveProc() as proc:
            self.assertFalse(list_runs._pid_alive_with_cmdline(proc.pid, ""))
            self.assertFalse(list_runs._pid_alive_with_cmdline(proc.pid, "   "))

    def test_dead_pid_is_not_alive(self) -> None:
        proc = subprocess.Popen(["sleep", "60"])
        pid = proc.pid
        cmdline = _proc_cmdline(pid)
        proc.kill()
        proc.wait()
        self.assertFalse(list_runs._pid_alive_with_cmdline(pid, cmdline))


class ClassifyGuardTest(unittest.TestCase):
    def test_teardown_wins_over_a_live_recorded_pid(self) -> None:
        """A leftover process must not turn a torn-down run into unprunable ``up?``."""
        with tempfile.TemporaryDirectory() as tmp, _LiveProc() as proc:
            run = _mk_run(Path(tmp), "20260801T000000Z-aaaa", torn_down=True)
            _record_pid(run, proc)
            self.assertEqual(list_runs.classify(run), "down")

    def test_recycled_pid_mismatch_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, _LiveProc() as proc:
            run = _mk_run(Path(tmp), "20260801T000001Z-bbbb")
            _record_pid(run, proc, cmdline="totally-other-process\n")
            self.assertEqual(list_runs.classify(run), "stale")

    def test_empty_cmdline_is_stale_even_when_pid_is_live(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, _LiveProc() as proc:
            run = _mk_run(Path(tmp), "20260801T000002Z-cccc")
            _record_pid(run, proc, cmdline="")
            self.assertEqual(list_runs.classify(run), "stale")

    def test_invalid_pid_text_is_skipped_not_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = _mk_run(Path(tmp), "20260801T000003Z-dddd")
            (run / "junk.pid").write_text("not-an-int\n")
            (run / "junk.cmdline").write_text("whatever")
            self.assertEqual(list_runs.classify(run), "stale")

    def test_missing_cmdline_file_is_skipped_not_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, _LiveProc() as proc:
            run = _mk_run(Path(tmp), "20260801T000004Z-eeee")
            (run / "svc.pid").write_text(f"{proc.pid}\n")
            self.assertEqual(list_runs.classify(run), "stale")

    def test_a_junk_pidfile_does_not_hide_a_live_sibling(self) -> None:
        """``continue`` on a bad pidfile, not ``return stale`` — or a leftover junk file makes a live run prunable."""
        with tempfile.TemporaryDirectory() as tmp, _LiveProc() as proc:
            run = _mk_run(Path(tmp), "20260801T000005Z-ffff")
            (run / "junk.pid").write_text("nope\n")
            (run / "junk.cmdline").write_text("whatever")
            _record_pid(run, proc, name="svc")
            self.assertEqual(list_runs.classify(run), "up?")


class ScanGuardTest(unittest.TestCase):
    def test_corrupt_ports_json_does_not_crash_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _mk_run(root, "20260801T000006Z-aaaa", torn_down=True)
            (run / "ports.json").write_text("{not-json")
            rows = list_runs.scan(root)
            self.assertEqual(len(rows), 1)
            self.assertIsNone(rows[0]["experiment"])
            self.assertEqual(rows[0]["ports"], {})

    def test_nested_cell_manifests_are_enumerated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _mk_run(root, "20260801T000007Z-bbbb", torn_down=True)
            nested = run / "cell-0" / "retry"
            nested.mkdir(parents=True)
            (nested / "manifest.json").write_text("{}")
            self.assertEqual(list_runs.scan(root)[0]["cells"], ["cell-0/retry"])


class StateFilterTest(unittest.TestCase):
    def _run(self, *argv: str) -> tuple[int, dict]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = list_runs.main(list(argv))
        return rc, json.loads(buf.getvalue())

    def test_state_up_matches_only_the_tentative_live_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, _LiveProc() as proc:
            root = Path(tmp)
            _mk_run(root, "20200101T000000Z-aaaa", torn_down=True)
            _mk_run(root, "20200101T000001Z-bbbb")
            live = _mk_run(root, "20200101T000002Z-cccc")
            _record_pid(live, proc)
            rc, out = self._run("--run-root", str(root), "--json", "--state", "up")
            self.assertEqual(rc, 0)
            self.assertEqual([r["run_id"] for r in out["runs"]], ["20200101T000002Z-cccc"])
            self.assertEqual(out["runs"][0]["state"], "up?")

    def test_state_down_does_not_include_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_run(root, "20200101T000000Z-aaaa", torn_down=True)
            _mk_run(root, "20200101T000001Z-bbbb")
            rc, out = self._run("--run-root", str(root), "--json", "--state", "down")
            self.assertEqual(rc, 0)
            self.assertEqual([r["run_id"] for r in out["runs"]], ["20200101T000000Z-aaaa"])

    def test_state_stale_does_not_include_down(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_run(root, "20200101T000000Z-aaaa", torn_down=True)
            _mk_run(root, "20200101T000001Z-bbbb")
            rc, out = self._run("--run-root", str(root), "--json", "--state", "stale")
            self.assertEqual(rc, 0)
            self.assertEqual([r["run_id"] for r in out["runs"]], ["20200101T000001Z-bbbb"])


class PruneGuardTest(unittest.TestCase):
    def _run(self, *argv: str) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = list_runs.main(list(argv))
        return rc, buf.getvalue()

    def test_teardown_plus_live_pid_is_still_prunable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, _LiveProc() as proc:
            root = Path(tmp)
            down = _mk_run(root, "20200101T000000Z-aaaa", torn_down=True)
            _record_pid(down, proc)
            rc, out = self._run("--run-root", str(root), "--prune", "--older-than", "1", "--yes")
            self.assertEqual(rc, 0)
            self.assertFalse(down.exists(), "torn-down run must prune even if a leftover pid is live")
            self.assertIn("PRUNED:", out)
            self.assertNotIn("SKIP (live recorded pid)", out)

    def test_recycled_pid_is_prunable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, _LiveProc() as proc:
            root = Path(tmp)
            stale = _mk_run(root, "20200101T000001Z-bbbb")
            _record_pid(stale, proc, cmdline="recycled-pid-other-process")
            rc, out = self._run("--run-root", str(root), "--prune", "--older-than", "1", "--yes")
            self.assertEqual(rc, 0)
            self.assertFalse(stale.exists(), "recycled-PID mismatch must not protect a stale run")
            self.assertIn("PRUNED:", out)


if __name__ == "__main__":
    unittest.main()
