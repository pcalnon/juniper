#!/usr/bin/env python3
"""YAML-extraction rehearsal for ``agents-md-touch-up.yml`` Last Updated VERIFICATION.

Companion to ``tests/test_agents_md_header_schema.py`` (shape/ISO format) and the
``.github/workflows/agents-md-touch-up.yml`` workflow that keeps ``**Last Updated**:``
current. Neither the workflow YAML nor its verify shell is otherwise lint-gated, so
this unittest IS the gate.

Contract pinned here (juniper-ml#1099 -- the lane VERIFIES, it never mutates):

- Missing ``**Last Updated**:`` field -> exit 0 with ``::warning::``.
- Malformed (non ``YYYY-MM-DD``) value -> exit 1.
- Value in the future -> exit 1.
- AGENTS.md changed but the date line NOT changed in this PR -> exit 1 with the
  exact line to write.
- AGENTS.md changed AND the date line changed -> exit 0.
- ANTI-RESURRECTION: the shell must never ``sed -i`` / ``git commit`` / ``git push``.
  It used to do exactly that, which produced two failure classes under the
  2026-08-12 ``required_signatures`` normalization -- an UNSIGNED commit (rejected,
  unmergeable branch) and a ``[skip ci]`` orphan head (no required context ever
  reports, PR permanently BLOCKED). See juniper-cascor#515 / #518.

Idiom matches ``tests/test_release_train_workflow_guard.py`` / ``tests/test_ci_fleet_pr_lint.py``:
extract the workflow's OWN verify shell and drive it hermetically.

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
JOB_NAME = "verify-date"
STEP_NAME = "Verify AGENTS.md `**Last Updated**:` was bumped in this PR"
FIXED_TODAY = "2026-08-14"
STALE_DATE = "2026-01-01"
FUTURE_DATE = "2027-03-04"


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


def _load_step() -> tuple:
    repo_root = _find_repo_root(Path(__file__).resolve().parent)
    wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
    if not wf.is_file():
        raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
    raw = wf.read_text(encoding="utf-8")
    doc = yaml.safe_load(raw)
    job = (doc.get("jobs") or {}).get(JOB_NAME)
    if job is None:
        raise unittest.SkipTest(f"{WORKFLOW_NAME} has no {JOB_NAME!r} job")
    steps = job.get("steps") or []
    step = next((s for s in steps if s.get("name") == STEP_NAME), None)
    if step is None or "run" not in step:
        raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step")
    return raw, doc, job, step


class AgentsMdDateCheckStructuralTest(unittest.TestCase):
    """Pin workflow shape so the lane cannot regain write access or start mutating again."""

    raw: str
    doc: dict
    job: dict
    step: dict
    script: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw, cls.doc, cls.job, cls.step = _load_step()
        cls.script = cls.step["run"]

    def test_paths_filter(self) -> None:
        on = self.doc.get("on") or self.doc.get(True) or {}
        pr = on.get("pull_request") or {}
        self.assertEqual(pr.get("paths"), ["AGENTS.md"])

    def test_permissions_are_read_only(self) -> None:
        """Verification needs no write scope -- the whole point of juniper-ml#1099."""
        perms = self.doc.get("permissions") or {}
        self.assertEqual(perms.get("contents"), "read")
        self.assertNotIn("write", str(perms.values()).lower())

    def test_script_never_mutates(self) -> None:
        """ANTI-RESURRECTION: the unsigned-commit / [skip ci]-orphan class must not come back."""
        script = self.script
        for forbidden in ("git commit", "git push", "sed -i", "git add", "git config user."):
            self.assertNotIn(forbidden, script, f"verify lane must never run {forbidden!r}")

    def test_step_receives_base_sha(self) -> None:
        self.assertIn("BASE_SHA", (self.step.get("env") or {}))

    def test_checkout_has_full_history(self) -> None:
        """The three-dot diff needs a resolvable merge base."""
        steps = self.job.get("steps") or []
        checkout = next((s for s in steps if str(s.get("uses", "")).startswith("actions/checkout")), None)
        self.assertIsNotNone(checkout, "verify lane must check out the PR head")
        self.assertEqual((checkout.get("with") or {}).get("fetch-depth"), 0)


class AgentsMdDateCheckRehearsalTest(unittest.TestCase):
    """Extract and run the real verify shell over every arm of the contract."""

    script: str
    real_git: str

    @classmethod
    def setUpClass(cls) -> None:
        _raw, _doc, _job, step = _load_step()
        cls.script = step["run"]
        cls.real_git = _real_git()

    def _agents_body(self, *, last_updated: str | None, version: str = "0.7.1") -> str:
        head = "# CLAUDE.md\n\n" "**Project**: juniper-ml\n" "**Repository**: pcalnon/juniper-ml\n" "**Author**: Paul Calnon\n" "**License**: MIT License\n" f"**Version**: {version}\n"
        if last_updated is None:
            return head
        return head + f"**Last Updated**: {last_updated}\n"

    def _git(self, repo: Path, *args: str) -> str:
        return subprocess.run(  # nosec B603,B607 - fixed git argv in temp fixture
            [self.real_git, *args],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def _init_repo(self, root: Path, *, base_body: str) -> tuple:
        """Create a repo whose FIRST commit is the PR base, and return (repo, base_sha)."""
        repo = root / "repo"
        repo.mkdir()
        self._git(repo, "init")
        self._git(repo, "config", "user.email", "fixture@example.com")
        self._git(repo, "config", "user.name", "fixture")
        self._git(repo, "config", "commit.gpgsign", "false")
        (repo / "AGENTS.md").write_text(base_body, encoding="utf-8")
        self._git(repo, "add", "AGENTS.md")
        self._git(repo, "commit", "-m", "base")
        return repo, self._git(repo, "rev-parse", "HEAD")

    def _pr_commit(self, repo: Path, body: str) -> None:
        (repo / "AGENTS.md").write_text(body, encoding="utf-8")
        self._git(repo, "add", "AGENTS.md")
        self._git(repo, "commit", "-m", "pr change")

    def _run(self, repo: Path, base_sha: str, *, git_log: Path) -> tuple:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            script_path = td_path / "verify.sh"
            script_path.write_text(self.script, encoding="utf-8")

            stub_bin = td_path / "bin"
            stub_bin.mkdir()

            date = stub_bin / "date"
            date.write_text(
                "#!/usr/bin/env bash\n" "set -euo pipefail\n" 'if [ "$*" = "-u +%Y-%m-%d" ]; then\n' f'  printf "%s\\n" "{FIXED_TODAY}"\n' "  exit 0\n" "fi\n" 'echo "unexpected date argv: $*" >&2\n' "exit 99\n",
                encoding="utf-8",
            )
            date.chmod(date.stat().st_mode | stat.S_IXUSR)

            # Real git underneath, but every invocation is logged so the
            # anti-mutation assertions can prove no commit/push was attempted.
            git = stub_bin / "git"
            git.write_text(
                "#!/usr/bin/env bash\n" "set -euo pipefail\n" f'REAL_GIT="{self.real_git}"\n' f'LOG="{git_log}"\n' 'printf "%s\\n" "$*" >>"$LOG"\n' 'exec "$REAL_GIT" "$@"\n',
                encoding="utf-8",
            )
            git.chmod(git.stat().st_mode | stat.S_IXUSR)

            env = RedactedEnv(os.environ)
            env["PATH"] = str(stub_bin) + os.pathsep + env.get("PATH", "")
            env["BASE_SHA"] = base_sha

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

    def _assert_no_mutation(self, repo: Path, head_before: str, git_log: Path) -> None:
        self.assertEqual(self._git(repo, "rev-parse", "HEAD"), head_before, "verify lane moved HEAD")
        self.assertEqual(self._git(repo, "status", "--porcelain"), "", "verify lane dirtied the tree")
        log = git_log.read_text(encoding="utf-8")
        for verb in ("commit", "push", "add "):
            self.assertNotIn(verb, log, f"verify lane invoked git {verb!r}")

    def test_missing_last_updated_warns_and_passes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, base = self._init_repo(root, base_body=self._agents_body(last_updated=None))
            self._pr_commit(repo, self._agents_body(last_updated=None, version="0.7.2"))
            head = self._git(repo, "rev-parse", "HEAD")
            git_log = root / "git.log"
            git_log.write_text("", encoding="utf-8")
            rc, out = self._run(repo, base, git_log=git_log)
            self.assertEqual(rc, 0, out)
            self.assertIn("::warning::", out)
            self.assertIn("no '**Last Updated**:' field", out)
            self._assert_no_mutation(repo, head, git_log)

    def test_malformed_date_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, base = self._init_repo(root, base_body=self._agents_body(last_updated=STALE_DATE))
            self._pr_commit(repo, self._agents_body(last_updated="Aug 14 2026"))
            head = self._git(repo, "rev-parse", "HEAD")
            git_log = root / "git.log"
            git_log.write_text("", encoding="utf-8")
            rc, out = self._run(repo, base, git_log=git_log)
            self.assertEqual(rc, 1, out)
            self.assertIn("not a YYYY-MM-DD date", out)
            self._assert_no_mutation(repo, head, git_log)

    def test_future_date_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, base = self._init_repo(root, base_body=self._agents_body(last_updated=STALE_DATE))
            self._pr_commit(repo, self._agents_body(last_updated=FUTURE_DATE))
            head = self._git(repo, "rev-parse", "HEAD")
            git_log = root / "git.log"
            git_log.write_text("", encoding="utf-8")
            rc, out = self._run(repo, base, git_log=git_log)
            self.assertEqual(rc, 1, out)
            self.assertIn("is in the future", out)
            self._assert_no_mutation(repo, head, git_log)

    def test_changed_without_bump_fails_with_guidance(self) -> None:
        """The core case: AGENTS.md edited, date left stale."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, base = self._init_repo(root, base_body=self._agents_body(last_updated=STALE_DATE))
            self._pr_commit(repo, self._agents_body(last_updated=STALE_DATE, version="0.7.2"))
            head = self._git(repo, "rev-parse", "HEAD")
            git_log = root / "git.log"
            git_log.write_text("", encoding="utf-8")
            rc, out = self._run(repo, base, git_log=git_log)
            self.assertEqual(rc, 1, out)
            self.assertIn("does not bump", out)
            self.assertIn(f"**Last Updated**: {FIXED_TODAY}", out)
            self._assert_no_mutation(repo, head, git_log)

    def test_bumped_date_passes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, base = self._init_repo(root, base_body=self._agents_body(last_updated=STALE_DATE))
            self._pr_commit(repo, self._agents_body(last_updated=FIXED_TODAY, version="0.7.2"))
            head = self._git(repo, "rev-parse", "HEAD")
            git_log = root / "git.log"
            git_log.write_text("", encoding="utf-8")
            rc, out = self._run(repo, base, git_log=git_log)
            self.assertEqual(rc, 0, out)
            self.assertNotIn("does not bump", out)
            self._assert_no_mutation(repo, head, git_log)

    def test_already_today_and_unchanged_passes(self) -> None:
        """A second PR on the same UTC day has nothing to bump, so the date line
        legitimately does not appear in its diff. Requiring 'changed' alone would
        fail every such PR -- including the one that introduced this check."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, base = self._init_repo(root, base_body=self._agents_body(last_updated=FIXED_TODAY))
            self._pr_commit(repo, self._agents_body(last_updated=FIXED_TODAY, version="0.7.2"))
            head = self._git(repo, "rev-parse", "HEAD")
            git_log = root / "git.log"
            git_log.write_text("", encoding="utf-8")
            rc, out = self._run(repo, base, git_log=git_log)
            self.assertEqual(rc, 0, out)
            self.assertIn("already today's UTC date", out)
            self._assert_no_mutation(repo, head, git_log)

    def test_backdated_but_changed_passes(self) -> None:
        """A PR opened days ago keeps passing on re-run -- the reason the predicate is
        'the line changed', not 'the line equals today'. This arm is the one that
        exercises the diff branch (the date is deliberately NOT today)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, base = self._init_repo(root, base_body=self._agents_body(last_updated=STALE_DATE))
            self._pr_commit(repo, self._agents_body(last_updated="2026-08-10", version="0.7.2"))
            head = self._git(repo, "rev-parse", "HEAD")
            git_log = root / "git.log"
            git_log.write_text("", encoding="utf-8")
            rc, out = self._run(repo, base, git_log=git_log)
            self.assertEqual(rc, 0, out)
            self.assertIn("was bumped in this PR", out)
            self._assert_no_mutation(repo, head, git_log)


if __name__ == "__main__":
    unittest.main()
