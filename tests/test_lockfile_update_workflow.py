#!/usr/bin/env python3
"""Structural gate for lockfile-update.yml weekly dep-docs refresh.

Companion to ``tests/test_ci_tools_drift.py`` (which pins the
``juniper-ci-tools>=X,<Y`` range inside this workflow). That drift check
does NOT pin the operator contract of the refresh itself:

  - invoke ``juniper-generate-dep-docs`` (not a resurrected inline script)
  - open a PR via SHA-pinned ``peter-evans/create-pull-request`` onto
    ``chore/lockfile-update`` with ``dependencies`` + ``automated`` labels
  - permissions exactly ``{contents: write, pull-requests: write}``

A rewrite that swaps the console script for a deleted ``util/generate_dep_docs.sh``
(removed in ml#298) or drops PR open would silently stall lockfile hygiene.
Neither the workflow YAML nor ``util/`` is otherwise lint-gated for these
properties, so this unittest IS the gate.

Run: python3 -m unittest -v tests/test_lockfile_update_workflow.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

WORKFLOW_NAME = "lockfile-update.yml"
JOB_NAME = "update"
GENERATE_STEP = "Regenerate dependency lockfiles"
PR_STEP = "Open PR if lockfiles changed"
CREATE_PR_ACTION_PREFIX = "peter-evans/create-pull-request@"
EXPECTED_BRANCH = "chore/lockfile-update"
EXPECTED_LABELS = frozenset({"dependencies", "automated"})


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


class LockfileUpdateWorkflowStructuralTest(unittest.TestCase):
    """Pin lockfile-update.yml so the weekly refresh cannot silently lose PR open."""

    repo_root: Path
    workflow_path: Path
    raw: str
    doc: dict
    job: dict
    steps: list

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)
        cls.job = (cls.doc.get("jobs") or {}).get(JOB_NAME)
        if cls.job is None:
            raise unittest.SkipTest(f"{WORKFLOW_NAME} has no {JOB_NAME} job")
        cls.steps = cls.job.get("steps") or []

    def _step(self, name: str) -> dict:
        step = next((s for s in self.steps if s.get("name") == name), None)
        if step is None:
            raise unittest.SkipTest(f"could not locate step {name!r} in {WORKFLOW_NAME}")
        return step

    def test_schedule_and_dispatch_triggers(self) -> None:
        on = self.doc.get("on") or self.doc.get(True) or {}
        self.assertIn("workflow_dispatch", on)
        schedule = on.get("schedule") or []
        self.assertTrue(any(isinstance(s, dict) and s.get("cron") for s in schedule))

    def test_permissions_are_exactly_contents_and_pull_requests_write(self) -> None:
        # Least privilege for opening the lockfile PR — no id-token / issues / etc.
        self.assertEqual(
            self.doc.get("permissions"),
            {"contents": "write", "pull-requests": "write"},
        )

    def test_installs_ci_tools_pin_then_generate_dep_docs(self) -> None:
        install = self._step("Install juniper-ci-tools")
        install_run = install.get("run") or ""
        self.assertIn("juniper-ci-tools>=", install_run)
        # Pin-range shape is also enforced by test_ci_tools_drift; keep a local
        # presence check so this gate fails even if that suite is skipped.
        self.assertRegex(install_run, r"juniper-ci-tools\s*>=\s*[0-9.]+,\s*<\s*[0-9.]+")

        generate = self._step(GENERATE_STEP)
        generate_run = (generate.get("run") or "").strip()
        self.assertEqual(generate_run, "juniper-generate-dep-docs")
        # The legacy inline script was deleted in ml#298 — must not return.
        self.assertNotIn("generate_dep_docs.sh", self.raw)
        self.assertNotIn("util/generate_dep_docs", self.raw)

    def test_create_pull_request_action_sha_pinned(self) -> None:
        pr = self._step(PR_STEP)
        uses = pr.get("uses") or ""
        self.assertTrue(uses.startswith(CREATE_PR_ACTION_PREFIX), msg=uses)
        # Full 40-char commit SHA after @ (fleet convention; floating tags drift).
        sha = uses.split("@", 1)[1]
        self.assertRegex(sha, r"^[0-9a-f]{40}$", msg=f"create-pull-request must be SHA-pinned, got {uses!r}")

    def test_pr_branch_labels_and_commit_message(self) -> None:
        pr = self._step(PR_STEP)
        with_block = pr.get("with") or {}
        self.assertEqual(with_block.get("branch"), EXPECTED_BRANCH)
        self.assertTrue(with_block.get("delete-branch"))
        self.assertEqual(with_block.get("commit-message"), "chore(deps): refresh CI lockfiles")
        self.assertEqual(with_block.get("title"), "chore(deps): refresh CI lockfiles")
        labels_raw = with_block.get("labels") or ""
        labels = {line.strip() for line in str(labels_raw).splitlines() if line.strip()}
        self.assertEqual(labels, EXPECTED_LABELS)
        body = with_block.get("body") or ""
        self.assertIn("juniper-generate-dep-docs", body)
        self.assertIn("juniper-ci-tools", body)

    def test_step_order_install_then_generate_then_pr(self) -> None:
        names = [s.get("name") for s in self.steps if s.get("name")]
        i_install = names.index("Install juniper-ci-tools")
        i_generate = names.index(GENERATE_STEP)
        i_pr = names.index(PR_STEP)
        self.assertLess(i_install, i_generate)
        self.assertLess(i_generate, i_pr)


if __name__ == "__main__":
    unittest.main()
