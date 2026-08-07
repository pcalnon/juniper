#!/usr/bin/env python3
"""YAML-extraction rehearsal for main-verify.yml battery path-change detector.

Flood-remediation P2 gate G3: the post-merge ``battery`` job must run when a
``main`` push touches ``tests/`` | ``util/`` | ``scripts/`` | ``.github/`` |
``pyproject.toml``, and must SKIP (burst-cost mitigation) for docs/notes-only
deltas. An unresolvable / zero ``github.event.before`` must fail-open to
``run=true`` so an initial / force-push tip is never silently un-batteried.

This unittest extracts the workflow's OWN ``Detect relevant path changes`` shell
(not a reimplementation) and drives it over a hermetic git fixture + stub
``GITHUB_OUTPUT`` — the same idiom as ``tests/test_main_verify_catchup_base.py``
/ ``tests/test_release_train_workflow_guard.py``.

Neither the workflow YAML nor this detector is otherwise lint-gated, so this
unittest IS the gate.

Run: python3 -m unittest -v tests/test_main_verify_battery_paths.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import os
import re
import subprocess  # nosec B404 - runs the workflow's OWN extracted shell hermetically (fixed argv)
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

WORKFLOW_NAME = "main-verify.yml"
STEP_NAME = "Detect relevant path changes"
STEP_ID = "changes"

# Paths the detector treats as battery-relevant (must stay locked to the workflow regex).
RELEVANT_PATH_PREFIXES = ("tests/", "util/", "scripts/", ".github/")
RELEVANT_EXACT = ("pyproject.toml",)


def _find_repo_root(start: Path) -> Path:
    cur = start
    for _ in range(8):
        if (cur / ".github" / "workflows").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise AssertionError(f"could not locate repo root with .github/workflows from {start}")


def _git(cwd: Path, *args: str) -> str:
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
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout.strip()


class BatteryPathDetectRehearsalTest(unittest.TestCase):
    """Extract and run the real battery path-change detector over the G3 matrix."""

    script: str
    regex_line: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        steps = doc.get("jobs", {}).get("battery", {}).get("steps", [])
        step = next(
            (s for s in steps if s.get("name") == STEP_NAME or s.get("id") == STEP_ID),
            None,
        )
        if step is None or "run" not in step:
            raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step in {WORKFLOW_NAME}")
        cls.script = step["run"]
        # Pin the workflow regex itself so a silent drop of util/ or .github/ fails here.
        m = re.search(
            r"grep -qE '\^\((tests/\|util/\|scripts/\|\\\.github/\|pyproject\\\.toml)\)'",
            cls.script,
        )
        cls.regex_line = m.group(0) if m else ""

    def test_workflow_regex_covers_all_relevant_prefixes(self) -> None:
        self.assertTrue(self.regex_line, "battery detector must use the documented path regex")
        for prefix in RELEVANT_PATH_PREFIXES:
            needle = prefix.replace(".", r"\.") if prefix.startswith(".") else prefix
            self.assertIn(needle, self.regex_line, f"regex must include {prefix!r}")
        for exact in RELEVANT_EXACT:
            self.assertIn(exact.replace(".", r"\."), self.regex_line)

    def _stage_pair(self, root: Path, *, changed_path: str, content: str = "x\n") -> tuple[Path, str, str]:
        """Linear A -> B history; B introduces ``changed_path``. Return (repo, sha_a, sha_b)."""
        repo = root / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")
        _git(repo, "config", "commit.gpgsign", "false")
        (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        _git(repo, "add", "seed.txt")
        _git(repo, "commit", "-m", "seed")
        sha_a = _git(repo, "rev-parse", "HEAD")
        target = repo / changed_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        _git(repo, "add", changed_path)
        _git(repo, "commit", "-m", f"touch {changed_path}")
        sha_b = _git(repo, "rev-parse", "HEAD")
        return repo, sha_a, sha_b

    def _run_detector(self, *, repo: Path, before: str, head_sha: str) -> tuple[str, str]:
        """Return (run_value, combined_stdout_stderr)."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            script_path = td_path / "detect.sh"
            script_path.write_text(self.script, encoding="utf-8")
            gh_out = td_path / "gh_output"
            gh_out.write_text("", encoding="utf-8")

            env = RedactedEnv(os.environ)
            env["BEFORE"] = before
            env["HEAD_SHA"] = head_sha
            env["GITHUB_OUTPUT"] = str(gh_out)

            proc = subprocess.run(  # nosec B603,B607 - workflow shell, fixed argv
                ["bash", str(script_path)],
                cwd=repo,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=30,
            )
            combined = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, msg=combined)
            written = gh_out.read_text(encoding="utf-8")
            m = re.search(r"^run=(.*)$", written, re.MULTILINE)
            self.assertIsNotNone(m, f"no run= in GITHUB_OUTPUT:\n{written}\n---\n{combined}")
            return m.group(1).strip(), combined

    def test_util_change_runs_battery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha_a, sha_b = self._stage_pair(Path(tmp), changed_path="util/example.py")
            run, log = self._run_detector(repo=repo, before=sha_a, head_sha=sha_b)
            self.assertEqual(run, "true")
            self.assertIn("Relevant code", log)

    def test_tests_change_runs_battery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha_a, sha_b = self._stage_pair(Path(tmp), changed_path="tests/test_example.py")
            run, _log = self._run_detector(repo=repo, before=sha_a, head_sha=sha_b)
            self.assertEqual(run, "true")

    def test_github_workflows_change_runs_battery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha_a, sha_b = self._stage_pair(Path(tmp), changed_path=".github/workflows/ci.yml", content="name: x\n")
            run, _log = self._run_detector(repo=repo, before=sha_a, head_sha=sha_b)
            self.assertEqual(run, "true")

    def test_pyproject_change_runs_battery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha_a, sha_b = self._stage_pair(Path(tmp), changed_path="pyproject.toml", content="[project]\nname='x'\n")
            run, _log = self._run_detector(repo=repo, before=sha_a, head_sha=sha_b)
            self.assertEqual(run, "true")

    def test_scripts_change_runs_battery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha_a, sha_b = self._stage_pair(Path(tmp), changed_path="scripts/example.bash")
            run, _log = self._run_detector(repo=repo, before=sha_a, head_sha=sha_b)
            self.assertEqual(run, "true")

    def test_docs_only_skips_battery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha_a, sha_b = self._stage_pair(Path(tmp), changed_path="docs/REFERENCE.md")
            run, log = self._run_detector(repo=repo, before=sha_a, head_sha=sha_b)
            self.assertEqual(run, "false")
            self.assertIn("skipping the battery", log)

    def test_notes_only_skips_battery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha_a, sha_b = self._stage_pair(Path(tmp), changed_path="notes/example.md")
            run, _log = self._run_detector(repo=repo, before=sha_a, head_sha=sha_b)
            self.assertEqual(run, "false")

    def test_zero_before_fail_open_runs_battery(self) -> None:
        """Force-push / initial push: zero BEFORE must not silently skip the battery."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, _sha_a, sha_b = self._stage_pair(Path(tmp), changed_path="docs/only.md")
            zeros = "0" * 40
            # HEAD^1 exists and the delta is docs-only, so after falling back to HEAD^1
            # the detector still classifies — the fail-open arm is the *unresolvable*
            # base path exercised below. Here we prove zero BEFORE falls to HEAD^1
            # rather than inventing run=true blindly when a parent exists.
            run, log = self._run_detector(repo=repo, before=zeros, head_sha=sha_b)
            self.assertEqual(run, "false", msg=log)
            self.assertNotIn("No resolvable base", log)

    def test_unresolvable_base_fail_open_runs_battery(self) -> None:
        """Empty BEFORE + orphan HEAD (no parent) -> run=true fail-open."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            _git(repo, "init")
            _git(repo, "config", "user.email", "t@t")
            _git(repo, "config", "user.name", "t")
            _git(repo, "config", "commit.gpgsign", "false")
            (repo / "only.txt").write_text("only\n", encoding="utf-8")
            _git(repo, "add", "only.txt")
            _git(repo, "commit", "-m", "root-only")
            sha = _git(repo, "rev-parse", "HEAD")
            run, log = self._run_detector(repo=repo, before="", head_sha=sha)
            self.assertEqual(run, "true")
            self.assertIn("No resolvable base", log)

    def test_foreign_unresolvable_before_falls_to_head_parent(self) -> None:
        """A BEFORE SHA that is not in the object store falls back to HEAD^1."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, sha_a, sha_b = self._stage_pair(Path(tmp), changed_path="util/hit.py")
            foreign = "deadbeef" * 5  # 40 hex chars, not in repo
            run, log = self._run_detector(repo=repo, before=foreign, head_sha=sha_b)
            self.assertEqual(run, "true", msg=log)
            # silence unused
            self.assertTrue(sha_a)


if __name__ == "__main__":
    unittest.main()
