"""Tests for ``util/experiments/list_runs.py`` (CLI experimentation plan §13.3, Wave 7.2).

``util/`` is not pre-commit-lint-gated, so this unittest is the gate. Synthetic
``RUN_ROOT`` fixtures only — no live launcher state is read or touched. The
destructive-path arms pin the ``generated_prompt_index``-style safety contract:
``--prune`` without ``--yes`` (or under ``--dry-run``) removes nothing; a run
whose recorded pid is alive with its recorded cmdline is never pruned.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "experiments" / "list_runs.py"

spec = importlib.util.spec_from_file_location("list_runs", MODULE_PATH)
list_runs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(list_runs)


def _mk_run(root: Path, run_id: str, *, torn_down: bool = False, experiment: str = "exp", ports: "dict | None" = None, cells: int = 0) -> Path:
    run = root / run_id
    (run / "logs").mkdir(parents=True)
    payload = {"run_id": run_id, "experiment": experiment, "data": 8110, "cascor": None, "recurrence": 8260, "grafana_bridge": False}
    payload.update(ports or {})
    (run / "ports.json").write_text(json.dumps(payload))
    if torn_down:
        (run / "teardown.json").write_text(json.dumps({"run_id": run_id, "services_stopped": [], "ports_released": []}))
    for i in range(cells):
        cell = run / f"cell-{i}"
        cell.mkdir()
        (cell / "manifest.json").write_text("{}")
    return run


class ScanTest(unittest.TestCase):
    def test_scan_parses_convention_dirs_and_ignores_others(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_run(root, "20260801T000000Z-aaaa", torn_down=True)
            (root / "not-a-run").mkdir()
            (root / "20260801T000000Z-zzzz").mkdir()  # non-hex suffix — not a run
            rows = list_runs.scan(root)
            self.assertEqual([r["run_id"] for r in rows], ["20260801T000000Z-aaaa"])
            self.assertEqual(rows[0]["state"], "down")
            self.assertEqual(rows[0]["created_utc"], "2026-08-01T00:00:00+00:00")
            self.assertEqual(rows[0]["experiment"], "exp")
            self.assertEqual(rows[0]["ports"], {"data": 8110, "recurrence": 8260})

    def test_states_down_stale_and_live(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_run(root, "20260801T000001Z-aaaa", torn_down=True)
            _mk_run(root, "20260801T000002Z-bbbb")  # no teardown, no pidfiles -> stale
            live = _mk_run(root, "20260801T000003Z-cccc")
            proc = subprocess.Popen(["sleep", "60"])
            try:
                time.sleep(0.1)
                (live / "juniper-recurrence.pid").write_text(f"{proc.pid}\n")
                (live / "juniper-recurrence.cmdline").write_text(Path(f"/proc/{proc.pid}/cmdline").read_bytes().decode().replace("\0", " "))
                states = {r["run_id"][-4:]: r["state"] for r in list_runs.scan(root)}
                self.assertEqual(states, {"aaaa": "down", "bbbb": "stale", "cccc": "up?"})
            finally:
                proc.kill()
                proc.wait()

    def test_dead_pid_with_recorded_cmdline_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _mk_run(root, "20260801T000004Z-dddd")
            proc = subprocess.Popen(["sleep", "60"])
            cmdline = Path(f"/proc/{proc.pid}/cmdline").read_bytes().decode().replace("\0", " ")
            proc.kill()
            proc.wait()
            (run / "svc.pid").write_text(f"{proc.pid}\n")
            (run / "svc.cmdline").write_text(cmdline)
            self.assertEqual(list_runs.scan(root)[0]["state"], "stale")

    def test_cells_enumerated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_run(root, "20260801T000005Z-eeee", torn_down=True, cells=3)
            self.assertEqual(len(list_runs.scan(root)[0]["cells"]), 3)


class CliTest(unittest.TestCase):
    def _run(self, *argv: str) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = list_runs.main(list(argv))
        self.assertEqual(rc, 0)
        return buf.getvalue()

    def test_json_shape_and_older_than_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_run(root, "20200101T000000Z-aaaa", torn_down=True)
            _mk_run(root, "20990101T000000Z-bbbb", torn_down=True)
            out = json.loads(self._run("--run-root", str(root), "--json", "--older-than", "30"))
            self.assertEqual([r["run_id"] for r in out["runs"]], ["20200101T000000Z-aaaa"])
            self.assertEqual(out["pruned"], [])

    def test_prune_without_yes_removes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _mk_run(root, "20200101T000000Z-aaaa", torn_down=True)
            out = self._run("--run-root", str(root), "--prune", "--older-than", "1")
            self.assertIn("WOULD PRUNE (missing --yes)", out)
            self.assertTrue(run.exists())

    def test_prune_dry_run_removes_nothing_even_with_yes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _mk_run(root, "20200101T000000Z-aaaa", torn_down=True)
            out = self._run("--run-root", str(root), "--prune", "--older-than", "1", "--yes", "--dry-run")
            self.assertIn("WOULD PRUNE (--dry-run)", out)
            self.assertTrue(run.exists())

    def test_prune_yes_removes_only_down_and_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            down = _mk_run(root, "20200101T000000Z-aaaa", torn_down=True)
            stale = _mk_run(root, "20200101T000001Z-bbbb")
            live = _mk_run(root, "20200101T000002Z-cccc")
            proc = subprocess.Popen(["sleep", "60"])
            try:
                time.sleep(0.1)
                (live / "svc.pid").write_text(f"{proc.pid}\n")
                (live / "svc.cmdline").write_text(Path(f"/proc/{proc.pid}/cmdline").read_bytes().decode().replace("\0", " "))
                out = self._run("--run-root", str(root), "--prune", "--older-than", "1", "--yes")
                self.assertFalse(down.exists(), "torn-down old run must be pruned")
                self.assertFalse(stale.exists(), "stale old run must be pruned")
                self.assertTrue(live.exists(), "a run with a live recorded pid must NEVER be pruned")
                self.assertIn("SKIP (live recorded pid)", out)
            finally:
                proc.kill()
                proc.wait()

    def test_empty_root_lists_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._run("--run-root", str(Path(tmp) / "missing"))
            self.assertIn("No experiment runs", out)


if __name__ == "__main__":
    unittest.main()
