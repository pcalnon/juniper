#!/usr/bin/env python3
"""Structural + YAML-extraction rehearsal for ci.yml archive-guard merge_group short-circuit.

Flood-remediation §4 item 1: the ``release-train-archive-guard`` job must re-post its
required context on ``merge_group`` or the merge queue stalls. A queued merge commit has
no PR ``base_ref`` to diff, so the job short-circuits with a green notice *before* any
checkout / base-ref diffing. The ``pull_request`` path stays the real guard.

Risky contract pinned here:

- Job ``if`` admits ``pull_request`` OR ``merge_group`` (never push-only).
- First step is merge_group-only and prints the short-circuit notice (exit 0).
- Checkout / install / run steps are pull_request-only (skipped on the queue).
- Job is ABSENT from the Quality Gate ``needs:`` (skip-on-push must not fail QG).

Idiom matches ``tests/test_ci_precommit_g4.py`` / ``tests/test_release_train_workflow_guard.py``.

Run: python3 -m unittest -v tests/test_ci_archive_guard_merge_group.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import os
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "ci.yml"
JOB_NAME = "release-train-archive-guard"
SHORT_CIRCUIT_STEP = "Report success on merge queue (validation already ran on the PR)"
PR_ONLY_STEP_NAMES = (
    "Checkout Code",
    "Install guard dependencies",
    "Run archive guard",
)
NOTICE_SNIPPET = "merge_group run — Release-Train Archive Guard already validated on the PR"


def _find_repo_root(start: Path) -> Path:
    cur = start
    for _ in range(8):
        if (cur / ".github" / "workflows").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise AssertionError(f"could not locate repo root with .github/workflows from {start}")


class ArchiveGuardMergeGroupStructuralTest(unittest.TestCase):
    """Pin merge_group short-circuit wiring so a refactor cannot stall the merge queue."""

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.doc = yaml.safe_load(cls.workflow_path.read_text(encoding="utf-8"))
        jobs = cls.doc.get("jobs") or {}
        cls.job = jobs.get(JOB_NAME)
        if cls.job is None:
            raise unittest.SkipTest(f"{WORKFLOW_NAME} has no {JOB_NAME!r} job")
        cls.steps = cls.job.get("steps") or []
        cls.qg = jobs.get("required-checks") or {}

    def test_job_if_admits_pull_request_and_merge_group(self) -> None:
        job_if = str(self.job.get("if", ""))
        self.assertIn("pull_request", job_if)
        self.assertIn("merge_group", job_if)

    def test_short_circuit_step_is_first_and_merge_group_only(self) -> None:
        self.assertGreaterEqual(len(self.steps), 1)
        first = self.steps[0]
        self.assertEqual(first.get("name"), SHORT_CIRCUIT_STEP)
        self.assertEqual(first.get("if"), "github.event_name == 'merge_group'")
        run = first.get("run") or ""
        self.assertIn(NOTICE_SNIPPET, run)
        self.assertIn("::notice::", run)

    def test_pr_path_steps_gated_to_pull_request(self) -> None:
        by_name = {s.get("name"): s for s in self.steps if s.get("name")}
        for name in PR_ONLY_STEP_NAMES:
            self.assertIn(name, by_name, f"missing step {name!r}")
            self.assertEqual(
                by_name[name].get("if"),
                "github.event_name == 'pull_request'",
                f"{name!r} must stay pull_request-only",
            )

    def test_absent_from_quality_gate_needs(self) -> None:
        needs = self.qg.get("needs") or []
        self.assertNotIn(
            JOB_NAME,
            needs,
            "archive-guard must stay out of Quality Gate needs (skip-on-push would fail QG)",
        )
        # Advisory siblings share the same exclusion contract.
        for advisory in ("sequence-safety", "fleet-pr-lint"):
            self.assertNotIn(advisory, needs)


class ArchiveGuardMergeGroupRehearsalTest(unittest.TestCase):
    """Extract and run the real merge_group short-circuit shell (exit 0 + notice)."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        steps = ((doc.get("jobs") or {}).get(JOB_NAME) or {}).get("steps") or []
        step = next((s for s in steps if s.get("name") == SHORT_CIRCUIT_STEP), None)
        if step is None or "run" not in step:
            raise unittest.SkipTest(f"could not locate {SHORT_CIRCUIT_STEP!r} run step")
        cls.script = step["run"]

    def test_short_circuit_shell_exits_0_with_notice(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            script_path = Path(td) / "short_circuit.sh"
            script_path.write_text(self.script, encoding="utf-8")
            env = RedactedEnv(os.environ)
            proc = subprocess.run(  # nosec B603,B607 - workflow shell, fixed argv
                ["bash", str(script_path)],
                cwd=td,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=10,
            )
            combined = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, combined)
            self.assertIn(NOTICE_SNIPPET, combined)
            self.assertIn("::notice::", combined)


if __name__ == "__main__":
    unittest.main()
