#!/usr/bin/env python3
"""YAML-extraction rehearsal for ``.github/workflows/pr-budget-alarm.yml``.

Flood-remediation P1 guardrail (#870 / analysis §4 item 9): the daily open-PR budget
alarm counts total open PRs + ``cursor/``-headed open PRs against repo variables
``PR_BUDGET_WARN`` (default 15) / ``PR_BUDGET_ALARM`` (default 30), always writes a
step-summary table, and posts Slack only on WARN/ALARM. Report-only by construction —
a budget breach stays green, and a hard ``gh`` failure is downgraded to ``::warning::``
+ ``level=OK`` so a transient API blip cannot page the owner.

This unittest extracts the workflow's OWN ``Count open PRs and evaluate the budget``
shell (not a reimplementation) and drives it over a hermetic stub ``gh`` + ``jq`` —
the same idiom as ``tests/test_release_train_workflow_guard.py`` ModeResolutionMatrixTest
and ``tests/test_main_verify_catchup_base.py``.

Neither the workflow YAML nor the threshold shell is otherwise lint-gated, so this
unittest IS the gate.

Run: python3 -m unittest -v tests/test_pr_budget_alarm.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "pr-budget-alarm.yml"
STEP_NAME = "Count open PRs and evaluate the budget"
STEP_ID = "count"


def _find_repo_root(start: Path) -> Path:
    cur = start
    for _ in range(8):
        if (cur / ".github" / "workflows").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise AssertionError(f"could not locate repo root with .github/workflows from {start}")


class PrBudgetAlarmRehearsalTest(unittest.TestCase):
    """Extract and run the real budget-count shell over the OK/WARN/ALARM + gh-fail matrix."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        steps = doc.get("jobs", {}).get("budget-alarm", {}).get("steps", [])
        step = next(
            (s for s in steps if s.get("name") == STEP_NAME or s.get("id") == STEP_ID),
            None,
        )
        if step is None or "run" not in step:
            raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step in {WORKFLOW_NAME}")
        cls.script = step["run"]

    def _run_count(
        self,
        *,
        prs: list | None,
        warn: str = "15",
        alarm: str = "30",
        gh_fails: bool = False,
    ) -> tuple[dict[str, str], str, int]:
        """Return (GITHUB_OUTPUT map, step_summary, exit_code)."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            script_path = td_path / "count.sh"
            script_path.write_text(self.script, encoding="utf-8")
            gh_out = td_path / "gh_output"
            gh_out.write_text("", encoding="utf-8")
            step_summary = td_path / "step_summary"
            step_summary.write_text("", encoding="utf-8")

            stub_bin = td_path / "bin"
            stub_bin.mkdir()
            payload = td_path / "prs.json"
            if prs is None:
                payload.write_text("[]", encoding="utf-8")
            else:
                payload.write_text(json.dumps(prs), encoding="utf-8")

            gh = stub_bin / "gh"
            if gh_fails:
                gh.write_text(
                    "#!/usr/bin/env bash\n"
                    "echo 'API rate limit' >&2\n"
                    "exit 1\n",
                    encoding="utf-8",
                )
            else:
                gh.write_text(
                    "#!/usr/bin/env bash\n"
                    "set -euo pipefail\n"
                    f'cat "{payload}"\n',
                    encoding="utf-8",
                )
            gh.chmod(gh.stat().st_mode | stat.S_IXUSR)

            env = RedactedEnv(os.environ)
            env["PATH"] = str(stub_bin) + os.pathsep + env.get("PATH", "")
            env["GH_TOKEN"] = "unused"
            env["GH_REPO"] = "pcalnon/juniper-ml"
            env["PR_BUDGET_WARN"] = warn
            env["PR_BUDGET_ALARM"] = alarm
            env["GITHUB_OUTPUT"] = str(gh_out)
            env["GITHUB_STEP_SUMMARY"] = str(step_summary)

            proc = subprocess.run(  # nosec B603,B607 - workflow shell, fixed argv
                ["bash", str(script_path)],
                cwd=td_path,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=30,
            )
            written = gh_out.read_text(encoding="utf-8")
            out_map: dict[str, str] = {}
            for line in written.splitlines():
                if "=" in line:
                    key, _, val = line.partition("=")
                    out_map[key] = val
            return out_map, step_summary.read_text(encoding="utf-8"), proc.returncode

    @staticmethod
    def _prs(total: int, cursor: int) -> list:
        """Build a synthetic open-PR list with ``cursor`` ``cursor/`` heads and the rest plain."""
        items = []
        for i in range(total):
            head = f"cursor/branch-{i}" if i < cursor else f"feature/branch-{i}"
            items.append({"number": i + 1, "headRefName": head})
        return items

    def test_defaults_when_budget_vars_empty(self) -> None:
        """Unset / empty repo variables must fall back to warn=15 / alarm=30."""
        out, _summary, rc = self._run_count(prs=self._prs(0, 0), warn="", alarm="")
        self.assertEqual(rc, 0)
        self.assertEqual(out.get("warn"), "15")
        self.assertEqual(out.get("alarm"), "30")
        self.assertEqual(out.get("level"), "OK")
        self.assertEqual(out.get("total"), "0")
        self.assertEqual(out.get("cursor"), "0")

    def test_ok_below_warn(self) -> None:
        out, summary, rc = self._run_count(prs=self._prs(5, 2), warn="15", alarm="30")
        self.assertEqual(rc, 0)
        self.assertEqual(out.get("level"), "OK")
        self.assertEqual(out.get("total"), "5")
        self.assertEqual(out.get("cursor"), "2")
        self.assertIn("**OK**", summary)

    def test_warn_on_total_crossing_warn(self) -> None:
        # total == warn fires WARN; alarm still higher.
        out, summary, rc = self._run_count(prs=self._prs(15, 0), warn="15", alarm="30")
        self.assertEqual(rc, 0)
        self.assertEqual(out.get("level"), "WARN")
        self.assertIn("**WARN**", summary)

    def test_warn_on_cursor_crossing_warn(self) -> None:
        # cursor subset alone crossing warn is enough (analysis §5).
        out, summary, rc = self._run_count(prs=self._prs(10, 15), warn="15", alarm="30")
        self.assertEqual(rc, 0)
        self.assertEqual(out.get("total"), "10")
        self.assertEqual(out.get("cursor"), "15")
        self.assertEqual(out.get("level"), "WARN")
        self.assertIn("**WARN**", summary)

    def test_alarm_on_total_crossing_alarm(self) -> None:
        out, summary, rc = self._run_count(prs=self._prs(30, 0), warn="15", alarm="30")
        self.assertEqual(rc, 0)
        self.assertEqual(out.get("level"), "ALARM")
        self.assertIn("**ALARM**", summary)

    def test_alarm_on_cursor_crossing_alarm(self) -> None:
        out, summary, rc = self._run_count(prs=self._prs(20, 30), warn="15", alarm="30")
        self.assertEqual(rc, 0)
        self.assertEqual(out.get("cursor"), "30")
        self.assertEqual(out.get("level"), "ALARM")
        self.assertIn("**ALARM**", summary)

    def test_alarm_beats_warn_when_both_thresholds_crossed(self) -> None:
        out, _summary, rc = self._run_count(prs=self._prs(40, 40), warn="15", alarm="30")
        self.assertEqual(rc, 0)
        self.assertEqual(out.get("level"), "ALARM")

    def test_gh_failure_stays_green_with_level_ok(self) -> None:
        """Hard ``gh`` failure must not page: exit 0, level=OK (Slack step skipped)."""
        out, summary, rc = self._run_count(prs=None, gh_fails=True)
        self.assertEqual(rc, 0, "report-only alarm must stay green on a gh blip")
        self.assertEqual(out.get("level"), "OK")
        # Soft-fail path writes only level=OK (no total/cursor) and a summary note.
        self.assertNotIn("total", out)
        self.assertIn("Could not query open PRs", summary)


class PrBudgetAlarmStructuralTest(unittest.TestCase):
    """Pin the report-only / least-privilege surface so a refactor cannot widen it."""

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)

    def test_permissions_are_read_only(self) -> None:
        perms = self.doc.get("permissions") or {}
        self.assertEqual(set(perms), {"contents", "pull-requests"})
        self.assertEqual(perms.get("contents"), "read")
        self.assertEqual(perms.get("pull-requests"), "read")

    def test_slack_step_gates_on_non_ok_and_continues_on_error(self) -> None:
        steps = self.doc["jobs"]["budget-alarm"]["steps"]
        slack = next(s for s in steps if "Slack" in s.get("name", ""))
        self.assertIn("steps.count.outputs.level != 'OK'", slack.get("if", ""))
        self.assertTrue(slack.get("continue-on-error"), "Slack POST must never fail the run")

    def test_only_slack_webhook_secret_is_referenced(self) -> None:
        secrets = set(re.findall(r"secrets\.([A-Z0-9_]+)", self.raw))
        self.assertEqual(secrets, {"SLACK_WEBHOOK_URL"})


if __name__ == "__main__":
    unittest.main()
