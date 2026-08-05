#!/usr/bin/env python3
"""YAML-extraction rehearsal for ``ci.yml`` Fleet PR Lint (advisory, never fails).

Flood-remediation Proposal P2 G5-iv / §4 item 8 phase 4: the ``fleet-pr-lint`` job
runs only on ``pull_request`` heads ``cursor/*`` and writes warnings to the step
summary — commit count > 1, black --check on changed ``.py``, fan-out > 15, and
exact-path hotspots ``AGENTS.md`` / ``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md``.
It must always ``exit 0`` and never comment.

This unittest extracts the workflow's OWN ``Fleet-PR best-practices lint`` shell
(not a reimplementation) and drives it over a hermetic git fixture + stub
``black`` — the same idiom as ``tests/test_release_train_workflow_guard.py`` and
``tests/test_ci_precommit_g4.py`` (#933).

Neither the workflow YAML nor this advisory shell is otherwise lint-gated, so
this unittest IS the gate.

Run: python3 -m unittest -v tests/test_ci_fleet_pr_lint.py

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

WORKFLOW_NAME = "ci.yml"
JOB_NAME = "fleet-pr-lint"
STEP_NAME = "Fleet-PR best-practices lint (advisory, never fails)"
HOTSPOT_AGENTS = "AGENTS.md"
HOTSPOT_CHEATSHEET = "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"


def _find_repo_root(start: Path) -> Path:
    cur = start
    for _ in range(8):
        if (cur / ".github" / "workflows").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise AssertionError(f"could not locate repo root with .github/workflows from {start}")


def _git(cwd: Path, *args: str, check: bool = True) -> str:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    proc = subprocess.run(  # nosec B603,B607 - fixed git argv in temp fixture
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if check and proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout.strip()


class FleetPrLintRehearsalTest(unittest.TestCase):
    """Extract and run the real fleet-pr-lint shell over the advisory matrix."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        job = doc.get("jobs", {}).get(JOB_NAME)
        if job is None:
            raise unittest.SkipTest(f"{WORKFLOW_NAME} has no {JOB_NAME!r} job")
        steps = job.get("steps", [])
        step = next((s for s in steps if s.get("name") == STEP_NAME), None)
        if step is None or "run" not in step:
            raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step")
        cls.script = step["run"]
        cls.job = job

    def _stage_repo(
        self,
        root: Path,
        *,
        py_files: list[str] | None = None,
        extra_files: list[str] | None = None,
        hotspot_agents: bool = False,
        hotspot_cheatsheet: bool = False,
        n_extra_touch: int = 0,
    ) -> tuple[Path, str, str]:
        """Build base → tip; return (repo, base_sha, head_sha)."""
        repo = root / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")
        _git(repo, "config", "commit.gpgsign", "false")
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        _git(repo, "add", "README.md")
        _git(repo, "commit", "-m", "base")
        base = _git(repo, "rev-parse", "HEAD")

        staged = False
        for rel in py_files or []:
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x = 1\n", encoding="utf-8")
            _git(repo, "add", rel)
            staged = True
        for rel in extra_files or []:
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("note\n", encoding="utf-8")
            _git(repo, "add", rel)
            staged = True
        if hotspot_agents:
            (repo / HOTSPOT_AGENTS).write_text("# agents\n", encoding="utf-8")
            _git(repo, "add", HOTSPOT_AGENTS)
            staged = True
        if hotspot_cheatsheet:
            cheat = repo / HOTSPOT_CHEATSHEET
            cheat.parent.mkdir(parents=True, exist_ok=True)
            cheat.write_text("# cheat\n", encoding="utf-8")
            _git(repo, "add", HOTSPOT_CHEATSHEET)
            staged = True
        for i in range(n_extra_touch):
            rel = f"touch/f{i:02d}.txt"
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{i}\n", encoding="utf-8")
            _git(repo, "add", rel)
            staged = True
        if not staged:
            (repo / "noop.txt").write_text("n\n", encoding="utf-8")
            _git(repo, "add", "noop.txt")
        _git(repo, "commit", "-m", "tip")
        head = _git(repo, "rev-parse", "HEAD")
        return repo, base, head

    def _run(
        self,
        *,
        repo: Path,
        base: str,
        commits: str = "1",
        changed_files: str = "1",
        head_ref: str = "cursor/example",
        black_fails: bool = False,
    ) -> tuple[int, str]:
        """Return (exit_code, step_summary)."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            script_path = td_path / "lint.sh"
            script_path.write_text(self.script, encoding="utf-8")
            step_summary = td_path / "step_summary"
            step_summary.write_text("", encoding="utf-8")

            stub_bin = td_path / "bin"
            stub_bin.mkdir()
            black = stub_bin / "black"
            if black_fails:
                black.write_text(
                    "#!/usr/bin/env bash\n"
                    "set -euo pipefail\n"
                    "echo 'would reformat dirty.py' >&2\n"
                    "exit 1\n",
                    encoding="utf-8",
                )
            else:
                black.write_text(
                    "#!/usr/bin/env bash\n"
                    "set -euo pipefail\n"
                    "exit 0\n",
                    encoding="utf-8",
                )
            black.chmod(black.stat().st_mode | stat.S_IXUSR)

            env = RedactedEnv(os.environ)
            env["PATH"] = str(stub_bin) + os.pathsep + env.get("PATH", "")
            env["PR_BASE_SHA"] = base
            env["PR_COMMITS"] = commits
            env["PR_CHANGED"] = changed_files
            env["HEAD_REF"] = head_ref
            env["GITHUB_STEP_SUMMARY"] = str(step_summary)

            proc = subprocess.run(  # nosec B603,B607 - workflow shell, fixed argv
                ["bash", str(script_path)],
                cwd=repo,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=30,
            )
            return proc.returncode, step_summary.read_text(encoding="utf-8")

    def test_clean_single_commit_ok_and_exit_0(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, base, _head = self._stage_repo(Path(td), py_files=["ok.py"])
            rc, summary = self._run(repo=repo, base=base, commits="1")
            self.assertEqual(rc, 0, summary)
            self.assertIn("commit count: 1 (ok).", summary)
            self.assertIn("black:", summary)
            self.assertIn("formatted (ok).", summary)
            self.assertNotIn(":warning:", summary)
            self.assertNotIn(":fire:", summary)

    def test_multi_commit_warns_but_exits_0(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, base, _head = self._stage_repo(Path(td), py_files=["a.py"])
            rc, summary = self._run(repo=repo, base=base, commits="3")
            self.assertEqual(rc, 0, summary)
            self.assertIn(":warning:", summary)
            self.assertIn("**3 commits**", summary)
            self.assertIn("single tidy commit", summary)

    def test_black_failure_warns_but_exits_0(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, base, _head = self._stage_repo(Path(td), py_files=["dirty.py"])
            rc, summary = self._run(repo=repo, base=base, black_fails=True)
            self.assertEqual(rc, 0, summary)
            self.assertIn("**black --check**", summary)
            self.assertIn("would reformat dirty.py", summary)

    def test_no_py_files_skips_black(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, base, _head = self._stage_repo(Path(td), extra_files=["notes.txt"])
            rc, summary = self._run(repo=repo, base=base)
            self.assertEqual(rc, 0, summary)
            self.assertIn("black: no changed .py files.", summary)

    def test_high_fan_out_warns(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            # 16 touch files → changed_count > 15
            repo, base, _head = self._stage_repo(Path(td), n_extra_touch=16)
            rc, summary = self._run(repo=repo, base=base, changed_files="16")
            self.assertEqual(rc, 0, summary)
            self.assertIn("high fan-out (> 15 files)", summary)

    def test_agents_md_hotspot_exact_match(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, base, _head = self._stage_repo(Path(td), hotspot_agents=True)
            rc, summary = self._run(repo=repo, base=base)
            self.assertEqual(rc, 0, summary)
            self.assertIn("**AGENTS.md**", summary)
            self.assertIn(":fire:", summary)

    def test_cheatsheet_hotspot_exact_match(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, base, _head = self._stage_repo(Path(td), hotspot_cheatsheet=True)
            rc, summary = self._run(repo=repo, base=base)
            self.assertEqual(rc, 0, summary)
            self.assertIn("**docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md**", summary)

    def test_near_miss_hotspot_paths_do_not_fire(self) -> None:
        """grep -qx is exact — AGENTS.md.bak / nested cheatsheet must not hotspot."""
        with tempfile.TemporaryDirectory() as td:
            repo, base, _head = self._stage_repo(
                Path(td),
                extra_files=["AGENTS.md.bak", "docs/other/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"],
            )
            rc, summary = self._run(repo=repo, base=base)
            self.assertEqual(rc, 0, summary)
            self.assertNotIn(":fire:", summary)
            self.assertNotIn("**AGENTS.md**", summary)


class FleetPrLintStructuralTest(unittest.TestCase):
    """Pin job surface so the advisory contract cannot drift unnoticed."""

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        cls.job = doc.get("jobs", {}).get(JOB_NAME)
        if cls.job is None:
            raise unittest.SkipTest(f"no {JOB_NAME} job")
        steps = cls.job.get("steps", [])
        cls.lint_step = next((s for s in steps if s.get("name") == STEP_NAME), None)
        cls.black_step = next((s for s in steps if s.get("name") == "Install black (repo-pinned)"), None)
        if cls.lint_step is None:
            raise unittest.SkipTest(f"no {STEP_NAME} step")

    def test_job_if_is_cursor_pull_request_only(self) -> None:
        job_if = self.job.get("if", "")
        self.assertIn("pull_request", job_if)
        self.assertIn("startsWith(github.head_ref, 'cursor/')", job_if)

    def test_permissions_are_contents_read_only(self) -> None:
        self.assertEqual(self.job.get("permissions"), {"contents": "read"})

    def test_script_always_exits_0_and_pins_hotspots(self) -> None:
        run = self.lint_step["run"]
        self.assertIn("exit 0", run)
        self.assertIn("set +e", run)
        self.assertIn("grep -qx 'AGENTS.md'", run)
        self.assertIn("grep -qx 'docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md'", run)
        self.assertIn("black --check --line-length 512", run)
        self.assertIn("-gt 15", run)
        self.assertIn("-gt 1", run)

    def test_black_pin_matches_pre_commit_rev(self) -> None:
        self.assertIsNotNone(self.black_step)
        run = self.black_step["run"]
        self.assertIn('black==26.3.1', run)


if __name__ == "__main__":
    unittest.main()
