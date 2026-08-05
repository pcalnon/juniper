#!/usr/bin/env python3
"""YAML-extraction rehearsal for ``agents-md-touch-up.yml`` Last Updated auto-bump.

Companion to ``tests/test_agents_md_header_schema.py`` (shape/ISO format) and the
``.github/workflows/agents-md-touch-up.yml`` workflow that keeps ``**Last Updated**:``
currency. Neither the workflow YAML nor its sed/commit shell is otherwise lint-gated,
so this unittest IS the gate.

Risky contract pinned here:

- Missing ``**Last Updated**:`` field → exit 0 with ``::warning::`` (no crash / no commit).
- Already today's UTC date → exit 0, no commit.
- Stale date → sed rewrite, commit as ``github-actions[bot]`` with ``[skip ci]``, then
  ``git pull --rebase`` + ``git push`` (never ``--force``).

Idiom matches ``tests/test_release_train_workflow_guard.py`` / ``tests/test_ci_fleet_pr_lint.py``:
extract the workflow's OWN bump shell and drive it hermetically.

Run: python3 -m unittest -v tests/test_agents_md_touch_up.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import os
import stat
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "agents-md-touch-up.yml"
JOB_NAME = "touch-up"
STEP_NAME = "Bump AGENTS.md `**Last Updated**:` to today (UTC)"
FIXED_TODAY = "2026-08-05"
STALE_DATE = "2026-01-01"
BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
SKIP_CI_MARKER = "[skip ci]"


def _find_repo_root(start: Path) -> Path:
    cur = start
    for _ in range(8):
        if (cur / ".github" / "workflows").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise AssertionError(f"could not locate repo root with .github/workflows from {start}")


def _real_git() -> str:
    proc = subprocess.run(  # nosec B603,B607 - locate system git once
        ["bash", "-lc", "command -v git"],
        capture_output=True,
        text=True,
        check=False,
    )
    path = (proc.stdout or "").strip()
    if proc.returncode != 0 or not path:
        raise unittest.SkipTest("system git not found on PATH")
    return path


class AgentsMdTouchUpStructuralTest(unittest.TestCase):
    """Pin workflow shape so a refactor cannot drop [skip ci], bot authorship, or the fork guard."""

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)
        cls.job = (cls.doc.get("jobs") or {}).get(JOB_NAME)
        if cls.job is None:
            raise unittest.SkipTest(f"{WORKFLOW_NAME} has no {JOB_NAME!r} job")
        steps = cls.job.get("steps") or []
        cls.step = next((s for s in steps if s.get("name") == STEP_NAME), None)
        if cls.step is None or "run" not in cls.step:
            raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step")
        cls.script = cls.step["run"]

    def test_paths_filter_and_fork_guard(self) -> None:
        on = self.doc.get("on") or self.doc.get(True) or {}
        pr = on.get("pull_request") or {}
        self.assertEqual(pr.get("paths"), ["AGENTS.md"])
        self.assertIn(
            "github.event.pull_request.head.repo.full_name == github.repository",
            str(self.job.get("if", "")),
        )

    def test_contents_write_permission(self) -> None:
        perms = self.doc.get("permissions") or {}
        self.assertEqual(perms.get("contents"), "write")

    def test_script_pins_bot_identity_skip_ci_and_no_force_push(self) -> None:
        script = self.script
        self.assertIn(BOT_NAME, script)
        self.assertIn(BOT_EMAIL, script)
        self.assertIn(SKIP_CI_MARKER, script)
        self.assertIn('git pull --rebase origin "$PR_HEAD_REF"', script)
        self.assertIn('git push origin HEAD:"$PR_HEAD_REF"', script)
        self.assertNotIn("--force", script)
        self.assertNotIn("git push -f", script)
        self.assertIn("PR_HEAD_REF", (self.step.get("env") or {}))


class AgentsMdTouchUpRehearsalTest(unittest.TestCase):
    """Extract and run the real bump shell over missing / current / stale AGENTS.md arms."""

    script: str
    real_git: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        job = (doc.get("jobs") or {}).get(JOB_NAME) or {}
        steps = job.get("steps") or []
        step = next((s for s in steps if s.get("name") == STEP_NAME), None)
        if step is None or "run" not in step:
            raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step")
        cls.script = step["run"]
        cls.real_git = _real_git()

    def _write_agents(self, repo: Path, *, last_updated: str | None) -> None:
        if last_updated is None:
            body = (
                "# CLAUDE.md\n\n"
                "**Project**: juniper-ml\n"
                "**Repository**: pcalnon/juniper-ml\n"
                "**Author**: Paul Calnon\n"
                "**License**: MIT License\n"
                "**Version**: 0.7.0\n"
            )
        else:
            body = (
                "# CLAUDE.md\n\n"
                "**Project**: juniper-ml\n"
                "**Repository**: pcalnon/juniper-ml\n"
                "**Author**: Paul Calnon\n"
                "**License**: MIT License\n"
                "**Version**: 0.7.0\n"
                f"**Last Updated**: {last_updated}\n"
            )
        (repo / "AGENTS.md").write_text(body, encoding="utf-8")

    def _init_repo(self, root: Path, *, last_updated: str | None) -> Path:
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(  # nosec B603,B607 - fixed git argv in temp fixture
            [self.real_git, "init"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(  # nosec B603,B607
            [self.real_git, "config", "user.email", "fixture@example.com"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(  # nosec B603,B607
            [self.real_git, "config", "user.name", "fixture"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(  # nosec B603,B607
            [self.real_git, "config", "commit.gpgsign", "false"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        self._write_agents(repo, last_updated=last_updated)
        subprocess.run(  # nosec B603,B607
            [self.real_git, "add", "AGENTS.md"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(  # nosec B603,B607
            [self.real_git, "commit", "-m", "base"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        return repo

    def _run(self, repo: Path, *, git_log: Path) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            script_path = td_path / "bump.sh"
            script_path.write_text(self.script, encoding="utf-8")

            stub_bin = td_path / "bin"
            stub_bin.mkdir()

            date = stub_bin / "date"
            date.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                # Only the workflow's `date -u +%Y-%m-%d` is used; reject other shapes.
                'if [ "$*" = "-u +%Y-%m-%d" ]; then\n'
                f'  printf "%s\\n" "{FIXED_TODAY}"\n'
                "  exit 0\n"
                "fi\n"
                'echo "unexpected date argv: $*" >&2\n'
                "exit 99\n",
                encoding="utf-8",
            )
            date.chmod(date.stat().st_mode | stat.S_IXUSR)

            git = stub_bin / "git"
            git.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                f'REAL_GIT="{self.real_git}"\n'
                f'LOG="{git_log}"\n'
                'printf "%s\\n" "$*" >>"$LOG"\n'
                'if [ "${1:-}" = "pull" ] || [ "${1:-}" = "push" ]; then\n'
                "  exit 0\n"
                "fi\n"
                'exec "$REAL_GIT" "$@"\n',
                encoding="utf-8",
            )
            git.chmod(git.stat().st_mode | stat.S_IXUSR)

            env = RedactedEnv(os.environ)
            env["PATH"] = str(stub_bin) + os.pathsep + env.get("PATH", "")
            env["PR_HEAD_REF"] = "cursor/example-branch"

            proc = subprocess.run(  # nosec B603,B607 - workflow shell, fixed argv
                ["bash", str(script_path)],
                cwd=repo,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=30,
            )
            return proc.returncode, proc.stdout + proc.stderr

    def test_missing_last_updated_warns_and_exits_0_without_commit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = self._init_repo(root, last_updated=None)
            base = subprocess.run(  # nosec B603,B607
                [self.real_git, "rev-parse", "HEAD"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            git_log = root / "git.log"
            git_log.write_text("", encoding="utf-8")
            rc, out = self._run(repo, git_log=git_log)
            self.assertEqual(rc, 0, out)
            self.assertIn("::warning::", out)
            self.assertIn("no '**Last Updated**:' field", out)
            head = subprocess.run(  # nosec B603,B607
                [self.real_git, "rev-parse", "HEAD"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(head, base)
            log = git_log.read_text(encoding="utf-8")
            self.assertNotIn("commit", log)
            self.assertNotIn("push", log)

    def test_already_today_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = self._init_repo(root, last_updated=FIXED_TODAY)
            base = subprocess.run(  # nosec B603,B607
                [self.real_git, "rev-parse", "HEAD"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            git_log = root / "git.log"
            git_log.write_text("", encoding="utf-8")
            rc, out = self._run(repo, git_log=git_log)
            self.assertEqual(rc, 0, out)
            self.assertIn(f"Last Updated already {FIXED_TODAY}", out)
            head = subprocess.run(  # nosec B603,B607
                [self.real_git, "rev-parse", "HEAD"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(head, base)
            self.assertNotIn("commit", git_log.read_text(encoding="utf-8"))

    def test_stale_date_bumps_commits_with_skip_ci_and_pushes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = self._init_repo(root, last_updated=STALE_DATE)
            git_log = root / "git.log"
            git_log.write_text("", encoding="utf-8")
            rc, out = self._run(repo, git_log=git_log)
            self.assertEqual(rc, 0, out)
            self.assertIn(f"{STALE_DATE} -> {FIXED_TODAY}", out)

            body = (repo / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(f"**Last Updated**: {FIXED_TODAY}", body)
            self.assertNotIn(STALE_DATE, body)

            msg = subprocess.run(  # nosec B603,B607
                [self.real_git, "log", "-1", "--pretty=%s"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertIn(FIXED_TODAY, msg)
            self.assertIn(SKIP_CI_MARKER, msg)

            author = subprocess.run(  # nosec B603,B607
                [self.real_git, "log", "-1", "--pretty=%an <%ae>"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(author, f"{BOT_NAME} <{BOT_EMAIL}>")

            log_lines = git_log.read_text(encoding="utf-8").splitlines()
            self.assertTrue(any(line.startswith("pull --rebase origin ") for line in log_lines), log_lines)
            self.assertTrue(any(line.startswith("push origin HEAD:") for line in log_lines), log_lines)
            self.assertFalse(any("--force" in line or line.startswith("push -f") for line in log_lines))


if __name__ == "__main__":
    unittest.main()
