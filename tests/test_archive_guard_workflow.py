#!/usr/bin/env python3
"""Structural pin for ci.yml release-train-archive-guard merge_group short-circuit.

The archive-guard job is a required merge-queue context (flood-remediation §4
item 1). On ``pull_request`` it runs ``util/release_train/archive_guard.py``
against the PR's three-dot diff. On ``merge_group`` there is no
``github.base_ref`` to fetch, so the job MUST short-circuit to a green notice
*before* any checkout / base-ref diffing — every real work step stays gated
``if: github.event_name == 'pull_request'``.

Drift modes this gate catches:

1. Job ``if`` drops ``merge_group`` → merge queue never gets the required
   context and stalls.
2. Short-circuit step loses its ``merge_group`` gate (or is deleted) → queue
   run either no-ops without reporting, or falls through into base-ref work
   that cannot succeed.
3. A work step loses its ``pull_request`` gate → merge_group tries
   ``git fetch origin "${{ github.base_ref }}"`` with an empty base and fails
   the required check.

Companion behavioural coverage lives in ``tests/test_release_train_archive_guard.py``
(the Python classifier). Workflow YAML is not otherwise lint-gated for this
wiring, so this unittest IS the gate.

Run: python3 -m unittest -v tests/test_archive_guard_workflow.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

WORKFLOW_NAME = "ci.yml"
JOB_ID = "release-train-archive-guard"
SHORT_CIRCUIT_STEP = "Report success on merge queue (validation already ran on the PR)"
WORK_STEP_NAMES = (
    "Checkout Code",
    "Set up Python",
    "Install guard dependencies",
    "Run archive guard",
)


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


class ArchiveGuardWorkflowWiringTest(unittest.TestCase):
    """Pin merge_group short-circuit + pull_request-only work steps."""

    repo_root: Path
    workflow_path: Path
    doc: dict
    job: dict
    steps: list
    steps_by_name: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.doc = yaml.safe_load(cls.workflow_path.read_text(encoding="utf-8"))
        cls.job = (cls.doc.get("jobs") or {}).get(JOB_ID)
        if cls.job is None:
            raise unittest.SkipTest(f"{JOB_ID} job missing from {WORKFLOW_NAME}")
        cls.steps = cls.job.get("steps") or []
        cls.steps_by_name = {s.get("name"): s for s in cls.steps if isinstance(s, dict) and s.get("name")}

    def test_job_runs_on_pull_request_and_merge_group(self) -> None:
        cond = str(self.job.get("if", ""))
        self.assertIn("pull_request", cond)
        self.assertIn("merge_group", cond)
        self.assertIn(
            "||",
            cond,
            "job if must OR pull_request with merge_group so the required context posts on the queue",
        )

    def test_short_circuit_step_is_first_and_merge_group_only(self) -> None:
        self.assertGreaterEqual(len(self.steps), 1, "archive-guard job has no steps")
        first = self.steps[0]
        self.assertEqual(
            first.get("name"),
            SHORT_CIRCUIT_STEP,
            "merge_group short-circuit must be the FIRST step (before any checkout/base-ref work)",
        )
        self.assertEqual(
            str(first.get("if", "")).strip(),
            "github.event_name == 'merge_group'",
            "short-circuit step must gate exclusively on merge_group",
        )
        run = str(first.get("run") or "")
        self.assertIn("merge_group", run)
        self.assertIn("::notice::", run)

    def test_work_steps_are_pull_request_only(self) -> None:
        for name in WORK_STEP_NAMES:
            with self.subTest(step=name):
                step = self.steps_by_name.get(name)
                self.assertIsNotNone(step, f"expected work step {name!r} missing from {JOB_ID}")
                self.assertEqual(
                    str(step.get("if", "")).strip(),
                    "github.event_name == 'pull_request'",
                    f"{name!r} must stay pull_request-only so merge_group never base-ref diffs",
                )

    def test_run_step_invokes_archive_guard_script(self) -> None:
        step = self.steps_by_name.get("Run archive guard")
        self.assertIsNotNone(step)
        run = str(step.get("run") or "")
        self.assertIn("util/release_train/archive_guard.py", run)
        self.assertIn("--base FETCH_HEAD", run)
        self.assertIn("--head HEAD", run)

    def test_absent_from_quality_gate_needs(self) -> None:
        """Archive-guard skips on push; folding it into QG needs would fail every push:main."""
        qg = (self.doc.get("jobs") or {}).get("required-checks") or {}
        needs = qg.get("needs") or []
        if isinstance(needs, str):
            needs = [needs]
        self.assertNotIn(
            JOB_ID,
            needs,
            f"{JOB_ID} must stay ABSENT from Quality Gate needs (PR/merge_group-only; skips on push)",
        )


if __name__ == "__main__":
    unittest.main()
