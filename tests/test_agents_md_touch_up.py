#!/usr/bin/env python3
"""YAML-extraction rehearsal for agents-md-touch-up.yml Last Updated bump.

Companion to ``tests/test_agents_md_header_schema.py`` (shape + ISO date format).
That lint does NOT exercise the workflow that keeps the date current. This
unittest extracts the bump step's OWN shell and proves:

  1. Structural wiring (paths filter, fork guard, contents:write, bot identity,
     ``[skip ci]`` commit trailer, sed rewrite of ``**Last Updated**:``).
  2. Behavioural arms over a hermetic git fixture + stubbed ``date`` /
     ``git pull`` / ``git push``:
       - already-today → no-op (no commit)
       - stale date → rewrite + commit whose message contains ``[skip ci]``
       - missing ``**Last Updated**:`` field → exit 0, no commit

The ``[skip ci]`` trailer is the load-bearing contract: without it the bump
commit re-triggers this workflow (and others) in a loop. Neither the workflow
YAML nor the bump shell is otherwise lint-gated for these properties, so this
unittest IS the gate.

Run: python3 -m unittest -v tests/test_agents_md_touch_up.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "agents-md-touch-up.yml"
STEP_NAME = "Bump AGENTS.md `**Last Updated**:` to today (UTC)"
FIXED_TODAY = "2099-01-15"
STALE_DATE = "2020-01-01"
SKIP_CI_TOKEN = "[skip ci]"
BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"

_AGENTS_HEADER = """\
# CLAUDE.md

**Project**: juniper-ml — Meta-package for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Version**: 0.7.0
**Last Updated**: {date}

---

Body text.
"""


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(  # nosec B603,B607 - fixed git argv in temp fixture
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t",
        },
    )
    if check and proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc


def _bump_step_run(doc: dict) -> str:
    steps = (doc.get("jobs") or {}).get("touch-up", {}).get("steps") or []
    step = next((s for s in steps if s.get("name") == STEP_NAME), None)
    if step is None or "run" not in step:
        raise unittest.SkipTest(f"could not locate {STEP_NAME!r} in {WORKFLOW_NAME}")
    return step["run"]


class AgentsMdTouchUpStructuralTest(unittest.TestCase):
    """Pin agents-md-touch-up.yml wiring so a casual edit cannot drop [skip ci] or the fork guard."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.raw = cls.workflow_path.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.raw)
        cls.script = _bump_step_run(cls.doc)
        cls.job = (cls.doc.get("jobs") or {}).get("touch-up")
        if cls.job is None:
            raise unittest.SkipTest(f"{WORKFLOW_NAME} has no touch-up job")

    def test_triggers_only_on_agents_md_path(self) -> None:
        on = self.doc.get("on") or self.doc.get(True) or {}
        pr = on.get("pull_request") or {}
        paths = pr.get("paths") or []
        self.assertIn("AGENTS.md", paths)
        types = pr.get("types") or []
        for required in ("opened", "reopened", "synchronize"):
            with self.subTest(event_type=required):
                self.assertIn(required, types)

    def test_fork_guard_and_contents_write(self) -> None:
        # Fork PRs get a read-only GITHUB_TOKEN; pushing the bump back would fail.
        self.assertIn(
            "github.event.pull_request.head.repo.full_name == github.repository",
            str(self.job.get("if") or ""),
        )
        perms = self.job.get("permissions") or self.doc.get("permissions") or {}
        self.assertEqual(perms.get("contents"), "write")

    def test_concurrency_cancels_superseded_runs(self) -> None:
        conc = self.doc.get("concurrency") or {}
        self.assertIn("agents-md-touch-up-", str(conc.get("group") or ""))
        self.assertTrue(conc.get("cancel-in-progress"))

    def test_script_reads_and_rewrites_last_updated_via_sed(self) -> None:
        self.assertIn("date -u +%Y-%m-%d", self.script)
        self.assertIn(r"^\*\*Last Updated\*\*:", self.script)
        self.assertIn("sed -i", self.script)
        self.assertIn(r"**Last Updated**: ${today}", self.script)

    def test_commit_message_includes_skip_ci(self) -> None:
        # Without [skip ci] the bump commit re-fires this workflow (and others) in a loop.
        self.assertIn(SKIP_CI_TOKEN, self.script)
        self.assertIn('git commit -m "chore(agents-md): bump Last Updated to ${today} [skip ci]"', self.script)

    def test_bot_identity_and_no_force_push(self) -> None:
        self.assertIn(BOT_NAME, self.script)
        self.assertIn(BOT_EMAIL, self.script)
        self.assertIn('git pull --rebase origin "$PR_HEAD_REF"', self.script)
        self.assertIn('git push origin HEAD:"$PR_HEAD_REF"', self.script)
        # Comment may say "rather than force-pushing"; pin that no push flag does it.
        self.assertNotRegex(self.script, r"git\s+push\b[^\n]*--force")
        self.assertNotRegex(self.script, r"git\s+push\b[^\n]*\s-f\b")

    def test_noop_when_already_today_and_missing_field_exit_zero(self) -> None:
        self.assertIn('if [ "$current" = "$today" ]; then', self.script)
        self.assertIn("nothing to do", self.script)
        self.assertIn("has no '**Last Updated**:' field", self.script)


class AgentsMdTouchUpRehearsalTest(unittest.TestCase):
    """Run the extracted bump shell over hermetic AGENTS.md fixtures."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        cls.script = _bump_step_run(yaml.safe_load(wf.read_text(encoding="utf-8")))

    def _stage_repo(self, root: Path, *, agents_body: str) -> Path:
        repo = root / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "fixture@t")
        _git(repo, "config", "user.name", "fixture")
        _git(repo, "config", "commit.gpgsign", "false")
        (repo / "AGENTS.md").write_text(agents_body, encoding="utf-8")
        _git(repo, "add", "AGENTS.md")
        _git(repo, "commit", "-m", "seed")
        # Local branch name matching PR_HEAD_REF so pull/push stubs have a target.
        _git(repo, "checkout", "-b", "feature/touch-up-fixture")
        return repo

    def _write_stubs(self, bindir: Path, *, real_git: str, git_log: Path) -> None:
        date = bindir / "date"
        date.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            # Only the workflow's ``date -u +%Y-%m-%d`` is pinned; anything else fails loud.
            'if [ "${1-}" = "-u" ] && [ "${2-}" = "+%Y-%m-%d" ]; then\n'
            f'  printf "%s\\n" "{FIXED_TODAY}"\n'
            "  exit 0\n"
            "fi\n"
            'echo "unexpected date argv: $*" >&2\n'
            "exit 2\n",
            encoding="utf-8",
        )
        date.chmod(0o755)

        git = bindir / "git"
        git.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f'printf "%s\\n" "$*" >> "{git_log}"\n'
            # Intercept network-touching verbs; everything else delegates to real git.
            'if [ "${1-}" = "pull" ] || [ "${1-}" = "push" ]; then\n'
            "  exit 0\n"
            "fi\n"
            f'exec "{real_git}" "$@"\n',
            encoding="utf-8",
        )
        git.chmod(0o755)

    def _run_bump(self, repo: Path) -> subprocess.CompletedProcess[str]:
        real_git = shutil.which("git")
        if not real_git:
            self.skipTest("git not on PATH")
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            script_path = td_path / "bump.sh"
            script_path.write_text(self.script, encoding="utf-8")
            bindir = td_path / "bin"
            bindir.mkdir()
            git_log = td_path / "git.log"
            git_log.write_text("", encoding="utf-8")
            self._write_stubs(bindir, real_git=real_git, git_log=git_log)

            env = RedactedEnv(os.environ)
            env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
            env["PR_HEAD_REF"] = "feature/touch-up-fixture"

            proc = subprocess.run(  # nosec B603,B607 - workflow shell, fixed argv
                ["bash", str(script_path)],
                cwd=repo,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=30,
            )
            # Attach the stub git log for assertion helpers.
            proc.git_log = git_log.read_text(encoding="utf-8")  # type: ignore[attr-defined]
            return proc

    def test_noop_when_last_updated_already_today(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._stage_repo(Path(tmp), agents_body=_AGENTS_HEADER.format(date=FIXED_TODAY))
            head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()
            proc = self._run_bump(repo)
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
            self.assertIn("nothing to do", proc.stdout + proc.stderr)
            head_after = _git(repo, "rev-parse", "HEAD").stdout.strip()
            self.assertEqual(head_before, head_after, "already-today must not create a commit")
            body = (repo / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(f"**Last Updated**: {FIXED_TODAY}", body)
            # No commit → no push/pull of a bump (stubs may still be unused).
            self.assertNotIn("commit -m", proc.git_log)  # type: ignore[attr-defined]

    def test_stale_date_rewrites_and_commits_with_skip_ci(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._stage_repo(Path(tmp), agents_body=_AGENTS_HEADER.format(date=STALE_DATE))
            head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()
            proc = self._run_bump(repo)
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
            body = (repo / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(f"**Last Updated**: {FIXED_TODAY}", body)
            self.assertNotIn(STALE_DATE, body)
            head_after = _git(repo, "rev-parse", "HEAD").stdout.strip()
            self.assertNotEqual(head_before, head_after, "stale date must produce a bump commit")
            msg = _git(repo, "log", "-1", "--pretty=%B").stdout
            self.assertIn(SKIP_CI_TOKEN, msg)
            self.assertIn(FIXED_TODAY, msg)
            self.assertIn(f"bump Last Updated to {FIXED_TODAY}", msg)
            # Prove the workflow actually attempted the post-commit sync (not force).
            git_log = proc.git_log  # type: ignore[attr-defined]
            self.assertIn("pull --rebase origin feature/touch-up-fixture", git_log)
            self.assertIn("push origin HEAD:feature/touch-up-fixture", git_log)
            self.assertNotIn("--force", git_log)

    def test_missing_last_updated_field_skips_without_commit(self) -> None:
        missing = (
            "# CLAUDE.md\n\n"
            "**Project**: juniper-ml\n"
            "**Version**: 0.7.0\n\n"
            "No Last Updated field here.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._stage_repo(Path(tmp), agents_body=missing)
            head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()
            proc = self._run_bump(repo)
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
            combined = proc.stdout + proc.stderr
            self.assertIn("has no '**Last Updated**:' field", combined)
            head_after = _git(repo, "rev-parse", "HEAD").stdout.strip()
            self.assertEqual(head_before, head_after)
            self.assertEqual((repo / "AGENTS.md").read_text(encoding="utf-8"), missing)


if __name__ == "__main__":
    unittest.main()
