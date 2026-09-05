#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/ad-hoc/e2e_f037_render_census.py`` -- the multi-session
F-CANOPY-037 render census.

``util/`` is outside every pre-commit Python hook's scope, so this suite is
the gate. Hermetic: ``subprocess.run`` and ``run_session`` are replaced;
nothing talks to a live canopy stack or a browser.

What it pins, and why it mattered:

- ``_topology_conditions`` must declare a run INVALID when every session saw
  ``hidden_units`` 0 / absent. That is the real vacuity: there was nothing to
  draw, so neither PASS nor FAIL can be read. Conflating this with ``varied``
  produced a wrong claim once already -- an idle *populated* census is VALID
  (it tests the single mount-time rebuild) and must not be thrown out.
- ``_find_juniper_root`` must walk UP until a directory contains BOTH
  ``juniper-canopy`` and ``juniper-cascor``. The old three-hop form, run from
  a worktree nested inside the repo, landed on ``worktrees/`` and recorded
  ``sha=None`` for canopy -- the field the provenance block exists to capture.
  A directory with only one sibling must not satisfy the walk.
- Session verdicts come from the structured ``topodiag`` JSON, never from
  stdout. A missing or corrupt results file is ``verdict is None`` (census
  failed to measure), not FAIL, and ``main`` exits 2. A completed census of
  all-FAIL sessions still exits 0 -- the tool does not judge the render rate.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "e2e_f037_render_census.py"


def _load():
    spec = importlib.util.spec_from_file_location("e2e_f037_render_census", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()


def _entry(hidden=None, *, key="hidden_units", server=True):
    """One census session row. ``server=False`` omits the server block entirely."""
    row = {"session": 1, "verdict": "FAIL", "wall_s": 0.1}
    if not server:
        return row
    payload = {} if hidden is None else {key: hidden}
    row["server"] = payload
    return row


class TopologyConditionsTest(unittest.TestCase):
    def test_all_zero_hidden_units_is_invalid_not_idle(self):
        """The vacuity: nothing to paint. ``bool(["0"])`` is True -- that is the conflation."""
        cond = mod._topology_conditions([_entry(0), _entry("0")])
        self.assertFalse(cond["populated"])
        self.assertFalse(cond["varied"])
        self.assertEqual(cond["scope"], "invalid")
        self.assertTrue(cond["note"].startswith("INVALID"), cond["note"])

    def test_absent_hidden_units_is_invalid(self):
        cond = mod._topology_conditions([_entry(server=False), _entry(None)])
        self.assertFalse(cond["populated"])
        self.assertEqual(cond["scope"], "invalid")

    def test_idle_populated_is_valid_and_must_not_be_invalid(self):
        """The documented wrong claim: idle was treated as 'census tested nothing'."""
        cond = mod._topology_conditions([_entry(5), _entry("5"), _entry(5, key="hidden")])
        self.assertTrue(cond["populated"])
        self.assertFalse(cond["varied"])
        self.assertEqual(cond["scope"], "idle")
        self.assertIn("VALID, IDLE SCOPE", cond["note"])
        self.assertNotIn("INVALID", cond["note"])

    def test_distinct_nonzero_hidden_is_growth(self):
        cond = mod._topology_conditions([_entry(3), _entry(7)])
        self.assertTrue(cond["populated"])
        self.assertTrue(cond["varied"])
        self.assertEqual(cond["scope"], "growth")
        self.assertIn("VALID, GROWTH SCOPE", cond["note"])

    def test_zero_plus_nonzero_is_populated_and_varied(self):
        """A 0 observation does not wipe a later real topology, and it *is* variation."""
        cond = mod._topology_conditions([_entry(0), _entry(5)])
        self.assertTrue(cond["populated"])
        self.assertTrue(cond["varied"])
        self.assertEqual(cond["scope"], "growth")


class FindJuniperRootTest(unittest.TestCase):
    def test_walk_up_from_nested_worktree_finds_both_siblings(self):
        """The sha=None incident: three hops from ad-hoc/ lands on worktrees/."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "juniper-canopy").mkdir()
            (root / "juniper-cascor").mkdir()
            start = root / "juniper-ml" / ".claude" / "worktrees" / "nested" / "util" / "ad-hoc"
            start.mkdir(parents=True)
            found = mod._find_juniper_root(str(start))
            self.assertEqual(found, str(root))
            three_hop = os.path.dirname(os.path.dirname(os.path.dirname(str(start))))
            self.assertEqual(Path(three_hop).name, "worktrees")
            self.assertNotEqual(found, three_hop)

    def test_one_sibling_does_not_satisfy_the_walk(self):
        """Four hops under the one-sibling dir, so the three-hop fallback cannot land on it."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "juniper-canopy").mkdir()
            start = root / "w" / "x" / "y" / "z"
            start.mkdir(parents=True)
            found = mod._find_juniper_root(str(start))
            self.assertNotEqual(found, str(root))
            self.assertFalse(os.path.isdir(os.path.join(found, "juniper-cascor")))
            self.assertEqual(found, os.path.dirname(os.path.dirname(os.path.dirname(str(start)))))


class RunSessionVerdictTest(unittest.TestCase):
    def test_verdict_comes_from_topodiag_json_not_stdout(self):
        def fake_run(cmd, cwd=None, env=None, **_kw):
            path = env["JUNIPER_E2E_SEG17_RESULTS"]
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"topodiag": {"verdict": "FAIL", "server": {"hidden_units": 4}}}, fh)
            self.assertEqual(env.get("LIBTORCH"), "")
            self.assertEqual(env.get("LD_LIBRARY_PATH"), "")
            return subprocess.CompletedProcess(cmd, 0, stdout="session PASS all painted\n", stderr="")

        with mock.patch.object(mod.subprocess, "run", fake_run):
            with tempfile.TemporaryDirectory() as tmp:
                entry = mod.run_session(1, sys.executable, str(REPO_ROOT), tmp, 5.0)
        self.assertEqual(entry["verdict"], "FAIL")
        self.assertNotEqual(entry["verdict"], "PASS")

    def test_missing_results_file_is_no_verdict_not_fail(self):
        def fake_run(cmd, cwd=None, env=None, **_kw):
            return subprocess.CompletedProcess(cmd, 0, stdout="PASS\n", stderr="")

        with mock.patch.object(mod.subprocess, "run", fake_run):
            with tempfile.TemporaryDirectory() as tmp:
                entry = mod.run_session(1, sys.executable, str(REPO_ROOT), tmp, 5.0)
        self.assertIsNone(entry["verdict"])

    def test_corrupt_results_json_is_no_verdict(self):
        def fake_run(cmd, cwd=None, env=None, **_kw):
            path = env["JUNIPER_E2E_SEG17_RESULTS"]
            Path(path).write_text("{", encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with mock.patch.object(mod.subprocess, "run", fake_run):
            with tempfile.TemporaryDirectory() as tmp:
                entry = mod.run_session(1, sys.executable, str(REPO_ROOT), tmp, 5.0)
        self.assertIsNone(entry["verdict"])


class MainExitTest(unittest.TestCase):
    def test_default_sessions_is_the_finding_sample_size(self):
        """2/11 vs 1/1 is not a claim. Changing the default silently vacuates the census."""
        self.assertEqual(mod.DEFAULT_SESSIONS, 11)

    def _run_main(self, sessions):
        argv = ["e2e_f037_render_census.py", "--sessions", str(len(sessions))]
        idx = {"n": 0}

        def fake_session(*_a, **_k):
            row = sessions[idx["n"]]
            idx["n"] += 1
            return row

        with mock.patch.object(mod, "run_session", fake_session):
            with mock.patch.object(mod, "_find_juniper_root", return_value="/no-such-juniper"):
                with mock.patch.object(mod, "_repo_provenance", return_value={"sha": None}):
                    with mock.patch.object(sys, "argv", argv):
                        with mock.patch.object(sys, "stdout", io.StringIO()):
                            return mod.main()

    def test_all_fail_still_exits_0_the_census_does_not_judge(self):
        rc = self._run_main(
            [
                {"session": 1, "verdict": "FAIL", "wall_s": 0.1, "server": {"hidden_units": 5}},
                {"session": 2, "verdict": "FAIL", "wall_s": 0.1, "server": {"hidden_units": 5}},
            ]
        )
        self.assertEqual(rc, 0)

    def test_missing_verdict_exits_2(self):
        rc = self._run_main(
            [
                {"session": 1, "verdict": "PASS", "wall_s": 0.1, "elapsed_s": 1, "server": {"hidden_units": 5}},
                {"session": 2, "verdict": None, "wall_s": 0.1},
            ]
        )
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
