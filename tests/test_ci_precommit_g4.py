#!/usr/bin/env python3
"""YAML-extraction rehearsal for ci.yml G4 pre-commit changed-files split.

Flood-remediation §4 item 8 phase 2 / Proposal P2 §4: on ``pull_request`` /
``merge_group``, pre-commit must scope to the event's changed files
(``--from-ref <BASE> --to-ref HEAD``) so a union-non-clean main no longer paints
every open PR red (#759). On ``push`` (incl. main) it must keep ``--all-files`` —
the global union check reinforced unbypassably post-merge by G3 (main-verify).

This unittest extracts the workflow's OWN ``Run pre-commit hooks`` shell (not a
reimplementation) and drives it over a hermetic stub ``pre-commit`` + ``git`` —
the same idiom as ``tests/test_release_train_workflow_guard.py``
ModeResolutionMatrixTest and ``tests/test_pr_budget_alarm.py``.

Neither the workflow YAML nor this shell is otherwise lint-gated for the split,
so this unittest IS the gate.

Run: python3 -m unittest -v tests/test_ci_precommit_g4.py

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
STEP_NAME = "Run pre-commit hooks"
JOB_NAME = "pre-commit"


def _find_repo_root(start: Path) -> Path:
    cur = start
    for _ in range(8):
        if (cur / ".github" / "workflows").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise AssertionError(f"could not locate repo root with .github/workflows from {start}")


class PrecommitG4StructuralTest(unittest.TestCase):
    """Pin the G4 event→argv contract so a refactor cannot silently restore --all-files on PRs."""

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)
        steps = cls.doc.get("jobs", {}).get(JOB_NAME, {}).get("steps", [])
        cls.step = next((s for s in steps if s.get("name") == STEP_NAME), None)
        if cls.step is None or "run" not in cls.step:
            raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step in {WORKFLOW_NAME}")
        cls.script = cls.step["run"]
        cls.env_block = cls.step.get("env") or {}

    def test_env_wires_event_and_both_base_shas(self) -> None:
        self.assertEqual(self.env_block.get("EVENT_NAME"), "${{ github.event_name }}")
        self.assertEqual(self.env_block.get("PR_BASE_SHA"), "${{ github.event.pull_request.base.sha }}")
        self.assertEqual(self.env_block.get("MG_BASE_SHA"), "${{ github.event.merge_group.base_sha }}")

    def test_script_contains_from_ref_and_all_files_arms(self) -> None:
        script = self.script
        self.assertIn('pre-commit run --from-ref "$base" --to-ref HEAD', script)
        self.assertIn("pre-commit run --all-files", script)
        self.assertIn('"$EVENT_NAME" = "pull_request"', script)
        self.assertIn('"$EVENT_NAME" = "merge_group"', script)
        # PR uses PR_BASE_SHA; merge_group uses MG_BASE_SHA (never swap / never invent).
        self.assertIn('base="$PR_BASE_SHA"', script)
        self.assertIn('base="$MG_BASE_SHA"', script)


class PrecommitG4RehearsalTest(unittest.TestCase):
    """Extract and run the real pre-commit shell over the PR / merge_group / push matrix."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        steps = doc.get("jobs", {}).get(JOB_NAME, {}).get("steps", [])
        step = next((s for s in steps if s.get("name") == STEP_NAME), None)
        if step is None or "run" not in step:
            raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step in {WORKFLOW_NAME}")
        cls.script = step["run"]

    def _run_hooks(
        self,
        *,
        event_name: str,
        pr_base: str = "prbase1111111111111111111111111111111111",
        mg_base: str = "mgbase2222222222222222222222222222222222",
        cat_file_ok: bool = True,
    ) -> tuple[int, str, list[str]]:
        """Return (exit_code, combined_output, pre-commit argv log lines)."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            script_path = td_path / "hooks.sh"
            script_path.write_text(self.script, encoding="utf-8")
            log_path = td_path / "precommit.log"
            stub_bin = td_path / "bin"
            stub_bin.mkdir()

            precommit = stub_bin / "pre-commit"
            precommit.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                f'printf "%s\\n" "$*" >>"{log_path}"\n'
                "exit 0\n",
                encoding="utf-8",
            )
            precommit.chmod(0o755)

            # Stub git: cat-file success/fail + fetch no-op. Other git verbs unexpected → 99.
            git = stub_bin / "git"
            cat_rc = 0 if cat_file_ok else 1
            git.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                'if [ "${1:-}" = "cat-file" ]; then\n'
                f"  exit {cat_rc}\n"
                "fi\n"
                'if [ "${1:-}" = "fetch" ]; then\n'
                "  exit 0\n"
                "fi\n"
                'echo "unexpected git argv: $*" >&2\n'
                "exit 99\n",
                encoding="utf-8",
            )
            git.chmod(0o755)

            env = RedactedEnv(os.environ)
            env["PATH"] = str(stub_bin) + os.pathsep + env.get("PATH", "")
            env["EVENT_NAME"] = event_name
            env["PR_BASE_SHA"] = pr_base
            env["MG_BASE_SHA"] = mg_base

            proc = subprocess.run(  # nosec B603,B607 - workflow shell, fixed argv
                ["bash", str(script_path)],
                cwd=td_path,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=30,
            )
            combined = proc.stdout + proc.stderr
            log_lines = log_path.read_text(encoding="utf-8").splitlines() if log_path.is_file() else []
            return proc.returncode, combined, log_lines

    def test_pull_request_uses_from_ref_pr_base(self) -> None:
        rc, out, log = self._run_hooks(event_name="pull_request")
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(len(log), 1)
        self.assertEqual(
            log[0],
            "run --from-ref prbase1111111111111111111111111111111111 --to-ref HEAD --show-diff-on-failure",
        )
        self.assertIn("Changed-files scope (pull_request)", out)
        self.assertNotIn("--all-files", log[0])

    def test_merge_group_uses_from_ref_mg_base(self) -> None:
        rc, out, log = self._run_hooks(event_name="merge_group")
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(len(log), 1)
        self.assertEqual(
            log[0],
            "run --from-ref mgbase2222222222222222222222222222222222 --to-ref HEAD --show-diff-on-failure",
        )
        self.assertIn("Changed-files scope (merge_group)", out)
        # Must not accidentally prefer the PR base on a merge_group event.
        self.assertNotIn("prbase", log[0])

    def test_push_uses_all_files(self) -> None:
        rc, out, log = self._run_hooks(event_name="push")
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0], "run --all-files --show-diff-on-failure")
        self.assertIn("Full-tree scope (push)", out)
        self.assertNotIn("--from-ref", log[0])

    def test_schedule_uses_all_files_like_push(self) -> None:
        """Non-PR / non-MG events must stay full-tree (never invent a BASE)."""
        rc, out, log = self._run_hooks(event_name="schedule")
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(log, ["run --all-files --show-diff-on-failure"])
        self.assertIn("Full-tree scope (schedule)", out)

    def test_missing_local_base_triggers_defensive_fetch_then_from_ref(self) -> None:
        """When ``git cat-file`` misses the base, the shell still runs --from-ref (fetch || true)."""
        rc, out, log = self._run_hooks(event_name="pull_request", cat_file_ok=False)
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(len(log), 1)
        self.assertIn("--from-ref prbase1111111111111111111111111111111111 --to-ref HEAD", log[0])


if __name__ == "__main__":
    unittest.main()
