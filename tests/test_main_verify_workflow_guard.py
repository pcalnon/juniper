#!/usr/bin/env python3
"""Structural trust-binding guard for .github/workflows/main-verify.yml's notify job (#928 review).

The notify job upserts the STABLE-TITLE dedup tracking issue ("main-verify: post-merge verification
failing" -- one OPEN issue per red streak). A stable title is a public, forgeable string: on this
public repo any third party can pre-create an OPEN issue with that exact title and capture the
tracker -- suppressing the bot-owned issue on the create path and diverting every subsequent
streak update on the comment path. An issue TITLE is therefore never a trust boundary.

This lint pins the fix by parsing the workflow with PyYAML and asserting, on the upsert step:

  (a) the dedup lookup binds to the workflow's own identity -- a REST ``gh api`` /issues query with
      ``creator=github-actions%5Bbot%5D`` (unforgeable authorship) and ``state=open``;
  (b) the lookup narrows by EXACT title (``env.TITLE`` jq compare), filters PRs out of the REST
      /issues surface (``.pull_request == null``), and streak updates comment on that bot-authored
      issue only;
  (c) the lookup does NOT use the old any-author ``gh issue list`` search, and does NOT filter by
      label (``labels=`` absent from the lookup) -- the bot-applied label is defense-in-depth for
      operator filtering only; making it part of the match would let a failed label application
      fork a streak into duplicate issues;
  (d) the create path ensure-creates the ``main-verify`` label idempotently and best-effort applies
      it AFTER create (bot-applied label), while a failed issue CREATE still fails the step loudly;
  (e) the notify job's elevation stays exactly {contents: read, issues: write} (R7 pattern) and the
      stable TITLE env value is the documented string.

Companion to ``tests/test_release_train_workflow_guard.py`` (same YAML-structural guard idiom).
The workflow shell is not pre-commit-lint-gated for these properties, so this unittest IS the gate.

Portable: locates the repo root by walking up for ``.github/workflows/`` (mirrors
``test_workflow_script_paths.py``) and skips loudly if ``main-verify.yml`` is absent.

Run: python3 -m unittest -v tests/test_main_verify_workflow_guard.py

Project: juniper-ml
Sub-Project: post-merge main verification (flood P2 gate G3)
Author: Paul Calnon
Created: 2026-08-06
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

WORKFLOW_NAME = "main-verify.yml"
STABLE_TITLE = "main-verify: post-merge verification failing"
CREATOR_BINDING = "creator=github-actions%5Bbot%5D"


def _find_repo_root(start: Path) -> Path:
    """First ancestor of ``start`` containing a ``.github/workflows/`` directory (the repo root)."""
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


class MainVerifyNotifyTrustBindingTest(unittest.TestCase):
    """Pin the notify upsert's authorship binding so a refactor cannot regress to title-only trust."""

    repo_root: Path
    workflow_path: Path
    doc: dict
    notify: dict
    step: dict
    run_text: str

    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.doc = yaml.safe_load(cls.workflow_path.read_text(encoding="utf-8"))
        notify = (cls.doc.get("jobs") or {}).get("notify")
        if notify is None:
            raise RuntimeError("main-verify.yml has no `notify` job -- the guard's subject moved; update this test together with the workflow")
        cls.notify = notify
        upserts = [step for step in notify.get("steps", []) if str(step.get("name", "")).startswith("Upsert tracking issue")]
        if len(upserts) != 1:
            raise RuntimeError(f"expected exactly one 'Upsert tracking issue' step in the notify job, found {len(upserts)}")
        cls.step = upserts[0]
        cls.run_text = cls.step.get("run") or ""

    def _lookup_line(self) -> str:
        """The single ``existing=`` dedup-lookup line of the upsert step's shell."""
        for line in self.run_text.splitlines():
            if line.strip().startswith("existing="):
                return line
        self.fail("notify upsert step has no `existing=` dedup lookup line")

    # (a) --------------------------------------------------------------------------------------
    def test_lookup_binds_to_bot_creator(self):
        lookup = self._lookup_line()
        self.assertIn("gh api", lookup, "dedup lookup must be a REST `gh api` /issues query (creator= binding), not a search")
        self.assertIn(CREATOR_BINDING, lookup, "dedup lookup must bind authorship via creator=github-actions[bot] -- an issue title is never a trust boundary (#928 review)")
        self.assertIn("state=open", lookup, "dedup lookup must match OPEN issues only (one issue per red streak)")

    # (b) --------------------------------------------------------------------------------------
    def test_lookup_narrows_exact_title_and_filters_prs(self):
        lookup = self._lookup_line()
        self.assertIn("env.TITLE", lookup, "dedup lookup must narrow by EXACT title (env.TITLE jq compare)")
        self.assertIn(".pull_request == null", lookup, "dedup lookup must filter PRs out of the REST /issues surface")
        self.assertIn('gh issue comment "$existing"', self.run_text, "streak updates must comment on the (bot-authored) existing issue")

    # (c) --------------------------------------------------------------------------------------
    def test_lookup_rejects_title_only_and_label_gating(self):
        self.assertNotIn("gh issue list", self.run_text, "the any-author `gh issue list` title search must be gone from the upsert step (title-only trust, #928 review)")
        self.assertNotIn("labels=", self._lookup_line(), "the label is defense-in-depth only -- a labels= filter in the dedup match would let a failed label application fork the streak into duplicate issues")

    # (d) --------------------------------------------------------------------------------------
    def test_create_path_applies_bot_label_and_fails_loudly(self):
        label_lines = [line for line in self.run_text.splitlines() if "gh label create main-verify" in line]
        self.assertEqual(len(label_lines), 1, "create path must ensure-create the main-verify label exactly once")
        self.assertIn("|| true", label_lines[0], "label ensure-create must be idempotent / non-fatal (`|| true`)")
        self.assertIn('gh issue create --repo "$REPO" --title "$TITLE"', self.run_text, "create path must open the issue with the stable TITLE")
        self.assertIn("--add-label main-verify", self.run_text, "create path must best-effort apply the bot-owned main-verify label AFTER create")
        self.assertIn("::error::failed to open the stable-title tracking issue", self.run_text, "a failed issue create must fail the step loudly (the tracker is the point of notify)")

    # (e) --------------------------------------------------------------------------------------
    def test_notify_permissions_and_stable_title(self):
        self.assertEqual(self.notify.get("permissions"), {"contents": "read", "issues": "write"}, "notify may elevate to issues:write ONLY (R7 pattern)")
        self.assertEqual((self.step.get("env") or {}).get("TITLE"), STABLE_TITLE, "the stable tracking-issue title must stay the documented string")


if __name__ == "__main__":
    unittest.main()
