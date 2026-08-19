#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/memory_budget_check.py`` (P2 of the shared-session-memory plan).

``util/`` is outside every pre-commit Python hook's scope (flake8/bandit scope to
``scripts/`` + ``tests/``), so this suite IS the gate -- the same gap that left
``tests/test_assert_release_tag.py`` unwired and its vacuous-pass guard unrun.

The load-bearing cases are the ones a well-meaning refactor silently breaks:

* the **no-worsening rule** -- over-ceiling alone must NOT fail; it must also have
  grown, or one bad file on main blocks every unrelated PR and the gate gets
  disabled rather than obeyed;
* the **ratchet never loosening**;
* the **waiver being a loan** -- it suppresses the failure without moving the
  ceiling;
* and the **machinery negative controls**. This repo has a documented class where
  a check's machinery breaks and it reports SUCCESS. A gate that cannot fail is
  not a gate, so each way this one could go blind is pinned to exit 2.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "util" / "memory_budget_check.py"

_spec = importlib.util.spec_from_file_location("memory_budget_check", MODULE_PATH)
assert _spec and _spec.loader
mbc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mbc)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin", "HOME": str(repo)},
    )


class BudgetFixture:
    """A throwaway git repo with one governed file at a known size."""

    def __init__(self, tmp: Path, base_chars: int, ceiling: int) -> None:
        self.root = tmp
        _git(self.root, "init", "-q", "-b", "main")
        self.governed = self.root / "AGENTS.md"
        self.governed.write_text("x" * base_chars, encoding="utf-8")
        self.budget_path = self.root / "budget.json"
        self.budget_path.write_text(
            json.dumps({"files": {"AGENTS.md": {"ceiling_chars": ceiling}}}),
            encoding="utf-8",
        )
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "base")

    def set_size(self, chars: int) -> None:
        self.governed.write_text("x" * chars, encoding="utf-8")

    def rows(self, waivers: set[str] | None = None) -> list[dict]:
        budget = mbc.load_budget(self.budget_path)
        return mbc.evaluate(self.root, budget, "HEAD", waivers or set())


class NoWorseningRuleTest(unittest.TestCase):
    """Rule 2 (correction C3): over-ceiling fails only if it ALSO grew."""

    def test_under_ceiling_is_ok(self):
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=200)
            self.assertEqual(fx.rows()[0]["status"], "OK")

    def test_over_ceiling_and_grew_fails(self):
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=150)
            fx.set_size(300)
            row = fx.rows()[0]
            self.assertEqual(row["status"], "FAIL")
            self.assertTrue(row["over_ceiling"] and row["grew"])

    def test_over_ceiling_but_shrank_passes(self):
        """The load-bearing case: an over-budget file being cleaned up must not
        be blocked, or the gate punishes exactly the work it wants."""
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=500, ceiling=150)
            fx.set_size(400)
            row = fx.rows()[0]
            self.assertTrue(row["over_ceiling"])
            self.assertFalse(row["grew"])
            self.assertEqual(row["status"], "OK")

    def test_over_ceiling_unchanged_passes(self):
        """main already over budget must not block an unrelated PR."""
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=500, ceiling=150)
            self.assertEqual(fx.rows()[0]["status"], "OK")


class WaiverIsALoanTest(unittest.TestCase):
    def test_trailer_waives_the_failure(self):
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=150)
            fx.set_size(300)
            self.assertEqual(fx.rows({"AGENTS.md"})[0]["status"], "WAIVED")

    def test_waiver_does_not_move_the_ceiling(self):
        """The whole point: the debt is still owed after a waiver."""
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=150)
            fx.set_size(300)
            fx.rows({"AGENTS.md"})
            reloaded = mbc.load_budget(fx.budget_path)
            self.assertEqual(reloaded["files"]["AGENTS.md"]["ceiling_chars"], 150)

    def test_waiver_for_another_path_does_not_apply(self):
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=150)
            fx.set_size(300)
            self.assertEqual(fx.rows({"docs/OTHER.md"})[0]["status"], "FAIL")

    def test_trailer_parsing(self):
        self.assertEqual(mbc.read_waivers("body\n\nAllow-Budget-Overrun: AGENTS.md\n"), {"AGENTS.md"})
        self.assertEqual(mbc.read_waivers("no trailer here"), set())


class MachineryNegativeControlTest(unittest.TestCase):
    """A gate that cannot fail is not a gate. Each blindness mode must exit 2."""

    def test_missing_governed_file_is_a_hard_failure(self):
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=200)
            fx.governed.unlink()
            with self.assertRaises(mbc.BudgetError):
                fx.rows()

    def test_empty_governed_set_is_a_hard_failure(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "b.json"
            p.write_text(json.dumps({"files": {}}), encoding="utf-8")
            with self.assertRaises(mbc.BudgetError):
                mbc.load_budget(p)

    def test_unreadable_budget_is_a_hard_failure(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "b.json"
            p.write_text("{not json", encoding="utf-8")
            with self.assertRaises(mbc.BudgetError):
                mbc.load_budget(p)

    def test_absent_budget_is_a_hard_failure(self):
        with TemporaryDirectory() as td:
            with self.assertRaises(mbc.BudgetError):
                mbc.load_budget(Path(td) / "nope.json")

    def test_nonpositive_ceiling_is_a_hard_failure(self):
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=200)
            fx.budget_path.write_text(
                json.dumps({"files": {"AGENTS.md": {"ceiling_chars": 0}}}),
                encoding="utf-8",
            )
            with self.assertRaises(mbc.BudgetError):
                fx.rows()


class RatchetTest(unittest.TestCase):
    def _run(self, root: Path, budget: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MODULE_PATH), "--repo-root", str(root), "--budget", str(budget), "--base-ref", "HEAD", *extra],
            capture_output=True,
            text=True,
        )

    def test_ratchet_tightens(self):
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=500)
            self._run(fx.root, fx.budget_path, "--ratchet")
            self.assertEqual(mbc.load_budget(fx.budget_path)["files"]["AGENTS.md"]["ceiling_chars"], 100)

    def test_ratchet_never_loosens(self):
        """Negative control: a file BELOW its ceiling may tighten it; a file
        ABOVE it must never raise it."""
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=150)
            fx.set_size(900)
            self._run(fx.root, fx.budget_path, "--ratchet")
            self.assertEqual(mbc.load_budget(fx.budget_path)["files"]["AGENTS.md"]["ceiling_chars"], 150)


class CliExitCodeTest(unittest.TestCase):
    def _run(self, root: Path, budget: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MODULE_PATH), "--repo-root", str(root), "--budget", str(budget), "--base-ref", "HEAD", *extra],
            capture_output=True,
            text=True,
        )

    def test_exit_zero_when_ok(self):
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=200)
            self.assertEqual(self._run(fx.root, fx.budget_path).returncode, 0)

    def test_exit_one_when_over_and_grew(self):
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=150)
            fx.set_size(300)
            self.assertEqual(self._run(fx.root, fx.budget_path).returncode, 1)

    def test_advisory_reports_but_exits_zero(self):
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=150)
            fx.set_size(300)
            res = self._run(fx.root, fx.budget_path, "--advisory")
            self.assertEqual(res.returncode, 0)
            self.assertIn("ADVISORY", res.stdout)
            self.assertIn("::error::", res.stdout)  # still reports the finding

    def test_exit_two_on_broken_machinery(self):
        with TemporaryDirectory() as td:
            self.assertEqual(self._run(Path(td), Path(td) / "missing.json").returncode, 2)

    def test_json_output_shape(self):
        with TemporaryDirectory() as td:
            fx = BudgetFixture(Path(td), base_chars=100, ceiling=200)
            res = self._run(fx.root, fx.budget_path, "--json")
            row = json.loads(res.stdout)["rows"][0]
            for key in ("path", "chars", "ceiling", "status", "headroom", "delta"):
                self.assertIn(key, row)


class RealRepoTest(unittest.TestCase):
    """Dogfood: the shipped budget must govern a file that actually exists."""

    def test_shipped_budget_is_valid_and_governs_agents_md(self):
        budget = mbc.load_budget(REPO_ROOT / "conf" / "memory_budget.json")
        self.assertIn("AGENTS.md", budget["files"])
        self.assertTrue((REPO_ROOT / "AGENTS.md").is_file())
        ceiling = budget["files"]["AGENTS.md"]["ceiling_chars"]
        self.assertIsInstance(ceiling, int)
        self.assertGreater(ceiling, 0)

    def test_reference_md_is_not_governed(self):
        """docs/REFERENCE.md is the migration DESTINATION; governing it would
        penalise the relocation the plan is asking for."""
        budget = mbc.load_budget(REPO_ROOT / "conf" / "memory_budget.json")
        self.assertNotIn("docs/REFERENCE.md", budget["files"])


if __name__ == "__main__":
    unittest.main()
