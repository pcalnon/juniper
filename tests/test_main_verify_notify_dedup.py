#!/usr/bin/env python3
"""YAML-extraction rehearsal for main-verify.yml notify stable-title issue dedup.

Post-incident polish (ml#928 / main-verify 0.3.0): the notify job must upsert ONE
OPEN tracking issue titled ``main-verify: post-merge verification failing`` per
red streak. The first failure CREATES it; each subsequent failing SHA COMMENTS
on it. The prior per-SHA title scheme filed six issues in the 2026-07-31..08-01
streak (ml#883/#884/#891/#892/#896/#897).

This unittest extracts the workflow's OWN upsert shell (not a reimplementation)
and drives it over a hermetic stub ``gh`` — the same idiom as
``tests/test_release_train_workflow_guard.py`` ModeResolutionMatrixTest and
``tests/test_main_verify_catchup_base.py``.

Neither the workflow YAML nor the notify shell is otherwise lint-gated for this
contract, so this unittest IS the gate.

Run: python3 -m unittest -v tests/test_main_verify_notify_dedup.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "main-verify.yml"
STABLE_TITLE = "main-verify: post-merge verification failing"
STEP_NAME = "Upsert tracking issue (stable title, one per red streak)"


def _find_repo_root(start: Path) -> Path:
    cur = start
    for _ in range(8):
        if (cur / ".github" / "workflows").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise AssertionError(f"could not locate repo root with .github/workflows from {start}")


class NotifyDedupStructuralTest(unittest.TestCase):
    """Pin the stable-title notify contract so a refactor cannot silently reintroduce per-SHA titles."""

    repo_root: Path
    workflow_path: Path
    raw: str
    doc: dict
    notify: dict
    upsert: dict
    script: str
    env_block: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)
        cls.notify = cls.doc.get("jobs", {}).get("notify")
        if cls.notify is None:
            raise unittest.SkipTest(f"{WORKFLOW_NAME} has no notify job")
        steps = cls.notify.get("steps", [])
        cls.upsert = next(
            (s for s in steps if s.get("name") == STEP_NAME or (isinstance(s.get("name"), str) and "Upsert tracking issue" in s["name"])),
            None,
        )
        if cls.upsert is None or "run" not in cls.upsert:
            raise unittest.SkipTest(f"could not locate upsert run step in {WORKFLOW_NAME}")
        cls.script = cls.upsert["run"]
        cls.env_block = cls.upsert.get("env") or {}

    def test_notify_runs_only_on_failure(self) -> None:
        self.assertEqual(
            self.notify.get("if"),
            "failure()",
            "notify must stay failure-only so green main-verify is a no-op (not auto-close).",
        )

    def test_notify_permissions_include_issues_write(self) -> None:
        perms = self.notify.get("permissions") or {}
        self.assertEqual(perms.get("issues"), "write")
        self.assertEqual(perms.get("contents"), "read")

    def test_title_env_is_stable_without_sha(self) -> None:
        title = self.env_block.get("TITLE")
        self.assertEqual(title, STABLE_TITLE)
        # Per-SHA titles were the failure class: TITLE must not interpolate SHA.
        self.assertNotIn("SHA", title)
        self.assertNotIn("${{", title)
        self.assertNotIn("${", title)

    def test_upsert_script_exact_title_jq_and_create_comment_paths(self) -> None:
        script = self.script
        self.assertIn("select(.title == env.TITLE)", script)
        self.assertIn('gh issue create --repo "$REPO" --title "$TITLE"', script)
        self.assertIn("gh issue comment", script)
        # Must not rebuild a per-SHA title in the shell (the old failure class).
        self.assertNotRegex(script, r"title=.*\$\{?SHA")
        self.assertNotIn("failed at ${SHA}", script)
        self.assertNotIn("failed at `$SHA`", script)


class NotifyDedupRehearsalTest(unittest.TestCase):
    """Extract and run the real upsert shell over the create / comment / exact-title matrix."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        steps = doc.get("jobs", {}).get("notify", {}).get("steps", [])
        step = next(
            (s for s in steps if s.get("name") == STEP_NAME or (isinstance(s.get("name"), str) and "Upsert tracking issue" in s["name"])),
            None,
        )
        if step is None or "run" not in step:
            raise unittest.SkipTest(f"could not locate upsert run step in {WORKFLOW_NAME}")
        cls.script = step["run"]

    def _run_upsert(
        self,
        *,
        list_stdout: str,
        sha: str = "abc123def456",
        run_url: str = "https://example.test/run/1",
        symbol_result: str = "failure",
        battery_result: str = "success",
        list_exit: int = 0,
    ) -> tuple[int, str, list[str], Path]:
        """Return (exit_code, combined_output, gh_log_lines, workdir)."""
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        td_path = Path(td.name)
        script_path = td_path / "upsert.sh"
        script_path.write_text(self.script, encoding="utf-8")
        log_path = td_path / "gh.log"
        stub_bin = td_path / "bin"
        stub_bin.mkdir()
        # Stub gh: log every invocation; the creator-bound `gh api repos/.../issues?...`
        # existing-issue query prints list_stdout (already jq-shaped); label create /
        # issue edit are best-effort in the workflow (|| true) and answered as no-ops;
        # create/comment succeed. Soft-fail arm: list_exit != 0 with empty stdout.
        gh = stub_bin / "gh"
        gh.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f'LOG="{log_path}"\n'
            'printf "%s\\n" "$*" >>"$LOG"\n'
            'if [ "${1:-}" = "api" ]; then\n'
            f'  printf "%s" {json.dumps(list_stdout)}\n'
            f"  exit {int(list_exit)}\n"
            "fi\n"
            'if [ "${1:-}" = "label" ] && [ "${2:-}" = "create" ]; then\n'
            "  exit 0\n"
            "fi\n"
            'if [ "${1:-}" = "issue" ] && [ "${2:-}" = "edit" ]; then\n'
            "  exit 0\n"
            "fi\n"
            'if [ "${1:-}" = "issue" ] && [ "${2:-}" = "create" ]; then\n'
            '  echo "https://example.test/issues/99"\n'
            "  exit 0\n"
            "fi\n"
            'if [ "${1:-}" = "issue" ] && [ "${2:-}" = "comment" ]; then\n'
            '  echo "https://example.test/issues/42#issuecomment-1"\n'
            "  exit 0\n"
            "fi\n"
            'echo "unexpected gh argv: $*" >&2\n'
            "exit 99\n",
            encoding="utf-8",
        )
        gh.chmod(0o755)

        env = RedactedEnv(os.environ)
        env["PATH"] = str(stub_bin) + os.pathsep + env.get("PATH", "")
        env["GH_TOKEN"] = "unused"
        env["REPO"] = "pcalnon/juniper-ml"
        env["TITLE"] = STABLE_TITLE
        env["SHA"] = sha
        env["RUN_URL"] = run_url
        env["SYMBOL_RESULT"] = symbol_result
        env["BATTERY_RESULT"] = battery_result

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
        return proc.returncode, combined, log_lines, td_path

    def test_first_failure_creates_stable_title_issue(self) -> None:
        """Empty open-issue search → create with the stable TITLE (not a per-SHA title)."""
        sha = "deadbeef0123456789abcdef"
        code, out, log_lines, work = self._run_upsert(list_stdout="", sha=sha)
        self.assertEqual(code, 0, msg=out)
        create_lines = [ln for ln in log_lines if ln.startswith("issue create ")]
        comment_lines = [ln for ln in log_lines if ln.startswith("issue comment ")]
        self.assertEqual(len(create_lines), 1, msg=f"expected one create, got {log_lines!r}\n{out}")
        self.assertEqual(comment_lines, [], msg=f"must not comment on first failure: {log_lines!r}")
        self.assertIn(f"--title {STABLE_TITLE}", create_lines[0])
        self.assertNotIn(sha, create_lines[0])
        body = (work / "issue-body.md").read_text(encoding="utf-8")
        self.assertIn(sha, body)
        self.assertIn("First observed failing", body)
        self.assertIn("NOT auto-closed on green", body)
        self.assertIn("Opening the stable-title tracking issue", out)

    def test_subsequent_failure_comments_existing_issue(self) -> None:
        """Exact-title open issue → comment the new SHA; never open a second issue."""
        sha = "cafebabefeedface00112233"
        code, out, log_lines, work = self._run_upsert(list_stdout="42", sha=sha)
        self.assertEqual(code, 0, msg=out)
        create_lines = [ln for ln in log_lines if ln.startswith("issue create ")]
        comment_lines = [ln for ln in log_lines if ln.startswith("issue comment ")]
        self.assertEqual(create_lines, [], msg=f"must not create when #42 exists: {log_lines!r}")
        self.assertEqual(len(comment_lines), 1, msg=f"expected one comment, got {log_lines!r}\n{out}")
        self.assertIn("issue comment 42 ", comment_lines[0])
        comment_body = (work / "issue-comment.md").read_text(encoding="utf-8")
        self.assertIn(sha, comment_body)
        self.assertIn("Still failing at", comment_body)
        self.assertIn("Commenting new failing SHA on existing tracking issue #42", out)

    def test_list_soft_fail_falls_through_to_create(self) -> None:
        """The creator-bound ``gh api`` query failure is soft (``|| true``) → treat as no existing issue."""
        code, out, log_lines, _work = self._run_upsert(list_stdout="", list_exit=1)
        self.assertEqual(code, 0, msg=out)
        create_lines = [ln for ln in log_lines if ln.startswith("issue create ")]
        self.assertEqual(len(create_lines), 1, msg=f"soft-fail list must create: {log_lines!r}\n{out}")
        self.assertIn(f"--title {STABLE_TITLE}", create_lines[0])


class NotifyDedupExactTitleNarrowTest(unittest.TestCase):
    """Pin that superset hits are narrowed by exact title AND the PR filter (the jq select contract).

    The upsert shell asks ``gh`` to run
    ``map(select(.pull_request == null) | select(.title == env.TITLE)) | .[0].number // empty``
    over the creator-bound ``/issues`` listing (which includes PRs). A stub that
    returns raw JSON would not exercise gh's --jq; instead we unit-check the
    filter expression against representative payloads with the real ``jq`` binary
    (same expression the workflow embeds), so a loosened select cannot ship.
    """

    def test_jq_exact_title_select_ignores_near_misses(self) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        script = yaml.safe_load(wf.read_text(encoding="utf-8"))["jobs"]["notify"]["steps"]
        upsert = next(s for s in script if "Upsert tracking issue" in s.get("name", ""))
        run = upsert["run"]
        # Extract the jq program literally from the workflow shell.
        marker = "--jq '"
        start = run.index(marker) + len(marker)
        end = run.index("'", start)
        jq_prog = run[start:end]
        self.assertEqual(jq_prog, "map(select(.pull_request == null) | select(.title == env.TITLE)) | .[0].number // empty")

        payload = json.dumps(
            [
                {"number": 1, "title": f"{STABLE_TITLE} at deadbeef"},
                # A PR with the exact title must NOT capture the tracker (/issues includes PRs).
                {"number": 5, "title": STABLE_TITLE, "pull_request": {"url": "https://example.test/pulls/5"}},
                {"number": 7, "title": STABLE_TITLE},
                {"number": 9, "title": "main-verify: something else"},
            ]
        )
        proc = subprocess.run(  # nosec B603,B607 - fixed jq argv
            ["jq", "-r", jq_prog],
            input=payload,
            capture_output=True,
            text=True,
            env=RedactedEnv(os.environ, TITLE=STABLE_TITLE),
            check=False,
            timeout=10,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertEqual(proc.stdout.strip(), "7")

        # No exact match → empty (create path).
        proc2 = subprocess.run(  # nosec B603,B607 - fixed jq argv
            ["jq", "-r", jq_prog],
            input=json.dumps([{"number": 1, "title": f"{STABLE_TITLE} at deadbeef"}]),
            capture_output=True,
            text=True,
            env=RedactedEnv(os.environ, TITLE=STABLE_TITLE),
            check=False,
            timeout=10,
        )
        self.assertEqual(proc2.returncode, 0, msg=proc2.stderr)
        self.assertEqual(proc2.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
