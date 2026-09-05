#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Launch / capture guards for ``util/soak_run_probe.py``. Complementary to
``tests/test_soak_run_probe.py`` (retrieval channel + parse_events),
``tests/test_soak_run_probe_terminal.py`` (BET-FAILING stopping rule), and
``tests/test_soak_run_probe_scorer_redaction.py`` (coverage tally in the
scoring packet). Those suites never resolve the ``claude`` binary, never
write a reaper pidfile, never scrub the child env, and never build a
TIMEOUT status.

``util/`` is outside every pre-commit Python hook, so this suite is the
only check on the unattended survival path. Hermetic: nothing here
launches ``claude`` or spends a probe.

What it pins
------------
1. **``resolve_claude`` does not use a bare name.** systemd --user and cron
   PATH omit ``~/.local/bin``. The first version raised FileNotFoundError
   after creating the run dir, so debris read as a crashed probe.
2. **The reaper guard is under ``JUNIPER_EXP_RUN_ROOT/soak-probes``.**
   ``collect_protected_pids`` never scans ``reports/soak/runs/``. A pidfile
   written only there grants zero protection. A reaped probe is a lost run,
   not a miss. AGENTS.md hazard.
3. **A stale ``ANTHROPIC_API_KEY`` is dropped** before the child starts, or
   the run dies with "Credit balance is too low" and never answers.
4. **A TIMEOUT status keeps ``stderr_tail``.** An earlier version bound
   ``err`` and dropped it -- the only place a timeout's last words could be
   read afterwards.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "soak_run_probe.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("soak_run_probe_launch", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = load_mod()


def _executable(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


class ClaudeSearchPaths(unittest.TestCase):
    def test_order_is_user_local_then_system(self) -> None:
        home = Path("/tmp/fake-home-does-not-need-to-exist")
        paths = mod.claude_search_paths(home=home)
        self.assertEqual(
            paths,
            (home / ".local/bin/claude", Path("/usr/local/bin/claude")),
        )

    def test_default_home_is_path_home(self) -> None:
        paths = mod.claude_search_paths()
        self.assertEqual(paths[0], Path.home() / ".local/bin/claude")
        self.assertEqual(paths[1], Path("/usr/local/bin/claude"))


class ResolveClaude(unittest.TestCase):
    def test_which_hit_wins_over_fallback(self) -> None:
        with mock.patch.object(mod.shutil, "which", return_value="/opt/claude"):
            self.assertEqual(mod.resolve_claude(), "/opt/claude")

    def test_user_local_fallback_when_which_misses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            claude = _executable(home / ".local/bin/claude")
            with mock.patch.object(mod.shutil, "which", return_value=None):
                self.assertEqual(
                    mod.resolve_claude(search_paths=(claude, Path(tmp) / "missing")),
                    str(claude),
                )

    def test_second_search_path_is_used_when_first_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            system = _executable(root / "usr/local/bin/claude")
            missing = root / "missing/claude"
            with mock.patch.object(mod.shutil, "which", return_value=None):
                self.assertEqual(
                    mod.resolve_claude(search_paths=(missing, system)),
                    str(system),
                )

    def test_non_executable_fallback_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cand = Path(tmp) / "claude"
            cand.write_text("#!/bin/sh\n", encoding="utf-8")
            cand.chmod(0o644)
            with mock.patch.object(mod.shutil, "which", return_value=None):
                with self.assertRaises(SystemExit) as ctx:
                    mod.resolve_claude(search_paths=(cand,))
            self.assertIn("cannot find the `claude` binary", str(ctx.exception))

    def test_missing_binary_exits_with_path_dump(self) -> None:
        with mock.patch.object(mod.shutil, "which", return_value=None):
            with mock.patch.dict(os.environ, {"PATH": "/usr/bin:/bin"}, clear=False):
                with self.assertRaises(SystemExit) as ctx:
                    mod.resolve_claude(search_paths=())
        self.assertIn("/usr/bin:/bin", str(ctx.exception))

    def test_unset_path_is_named_in_the_exit(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "PATH"}
        with mock.patch.object(mod.shutil, "which", return_value=None):
            with mock.patch.dict(os.environ, env, clear=True):
                with self.assertRaises(SystemExit) as ctx:
                    mod.resolve_claude(search_paths=())
        self.assertIn("(unset)", str(ctx.exception))


class ReaperGuardPath(unittest.TestCase):
    def test_uses_exp_run_root_soak_probes_not_reports_soak(self) -> None:
        path = mod.reaper_guard_path(4242, exp_run_root="/var/exp-runs")
        self.assertEqual(path, Path("/var/exp-runs/soak-probes/soak-probe-4242.pid"))
        self.assertNotIn("reports/soak", str(path))

    def test_default_root_is_juniper_experiments_under_home(self) -> None:
        home = Path("/tmp/fake-home-reaper")
        path = mod.reaper_guard_path(7, home=home)
        self.assertEqual(
            path,
            home / ".local/state/juniper-experiments/soak-probes/soak-probe-7.pid",
        )

    def test_filename_embeds_the_pid(self) -> None:
        path = mod.reaper_guard_path(99, exp_run_root="/r")
        self.assertEqual(path.name, "soak-probe-99.pid")

    def test_a_reports_soak_runs_location_would_fail_this(self) -> None:
        # THE historical defect: pidfile under the repo run dir, which
        # collect_protected_pids never walks.
        path = mod.reaper_guard_path(1, exp_run_root="/exp")
        self.assertNotEqual(path.parent.name, "runs")
        self.assertEqual(path.parent.name, "soak-probes")


class ProbeChildEnv(unittest.TestCase):
    def test_stale_api_key_is_dropped(self) -> None:
        env = mod.probe_child_env({"ANTHROPIC_API_KEY": "sk-test-not-real", "HOME": "/x"})
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertEqual(env["HOME"], "/x")

    def test_caller_dict_is_not_mutated(self) -> None:
        src = {"ANTHROPIC_API_KEY": "sk-test-not-real", "OTHER": "1"}
        mod.probe_child_env(src)
        self.assertEqual(src["ANTHROPIC_API_KEY"], "sk-test-not-real")

    def test_absent_key_is_fine(self) -> None:
        env = mod.probe_child_env({"HOME": "/x"})
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertEqual(env["HOME"], "/x")


class TimeoutStatus(unittest.TestCase):
    def test_state_is_timeout_not_complete(self) -> None:
        st = mod.timeout_status("P19", "sess", 900, "boom", "2026-09-04T00:00:00Z")
        self.assertEqual(st["state"], "TIMEOUT")
        self.assertEqual(st["probe_id"], "P19")
        self.assertEqual(st["session_id"], "sess")
        self.assertEqual(st["timeout_s"], 900)

    def test_stderr_tail_is_kept(self) -> None:
        st = mod.timeout_status("P19", "sess", 900, "last words of the child", "t")
        self.assertEqual(st["stderr_tail"], "last words of the child")

    def test_stderr_tail_is_the_last_400_chars(self) -> None:
        st = mod.timeout_status("P19", "sess", 900, "x" * 450, "t")
        self.assertEqual(len(st["stderr_tail"]), 400)
        self.assertTrue(st["stderr_tail"].startswith("x"))
        self.assertEqual(st["stderr_tail"], "x" * 400)

    def test_none_stderr_becomes_empty_string(self) -> None:
        st = mod.timeout_status("P19", "sess", 900, None, "t")
        self.assertEqual(st["stderr_tail"], "")


class LaunchGuardCallSites(unittest.TestCase):
    """A helper that is never called is the reports/soak-runs class again."""

    def test_main_uses_the_extracted_guards(self) -> None:
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("reaper_guard_path(", src)
        self.assertIn("probe_child_env(", src)
        self.assertIn("timeout_status(", src)
        self.assertIn("resolve_claude()", src)


if __name__ == "__main__":
    unittest.main()
