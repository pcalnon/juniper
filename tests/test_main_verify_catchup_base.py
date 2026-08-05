#!/usr/bin/env python3
"""YAML-extraction rehearsal for main-verify.yml G3.1 catch-up BASE resolution.

Flood-remediation P2 gate G3 (ml#873 / §4 item 8): a quoted ``[skip ci]`` in a
merge-commit body skips THIS workflow entirely, so a window of merges can land
un-screened. The ``Resolve catch-up base`` step must prefer the head_sha of the
most recent SUCCESSFUL main-verify run on main WHEN that tip is an ancestor of
HEAD (sweeping the skipped window), else ``github.event.before``, else
``HEAD^1``.

This unittest extracts the workflow's OWN shell (not a reimplementation) and
drives it over a hermetic git fixture + stub ``gh`` — the same idiom as
``tests/test_release_train_workflow_guard.py`` ModeResolutionMatrixTest.

Neither the workflow YAML nor ``util/sequence_safety/`` is otherwise lint-gated
for this resolver, so this unittest IS the gate.

Run: python3 -m unittest -v tests/test_main_verify_catchup_base.py

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
STEP_NAME = "Resolve catch-up base"


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
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout.strip()


class CatchUpBaseRehearsalTest(unittest.TestCase):
    """Extract and run the real ``Resolve catch-up base`` shell over the G3.1 matrix."""

    script: str

    @classmethod
    def setUpClass(cls) -> None:
        repo_root = _find_repo_root(Path(__file__).resolve().parent)
        wf = repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        steps = doc.get("jobs", {}).get("symbol-screen", {}).get("steps", [])
        step = next((s for s in steps if s.get("name") == STEP_NAME or s.get("id") == "base"), None)
        if step is None or "run" not in step:
            raise unittest.SkipTest(f"could not locate {STEP_NAME!r} run step in {WORKFLOW_NAME}")
        cls.script = step["run"]

    def _stage_repo(self, root: Path) -> tuple[str, str, str]:
        """Build A -> B -> C linear history; return (sha_a, sha_b, sha_c=HEAD)."""
        repo = root / "repo"
        repo.mkdir()
        _git(repo, "init")
        _git(repo, "config", "user.email", "t@t")
        _git(repo, "config", "user.name", "t")
        # Avoid signing noise in hermetic fixtures.
        _git(repo, "config", "commit.gpgsign", "false")
        shas: list[str] = []
        for label in ("A", "B", "C"):
            (repo / "f.txt").write_text(f"{label}\n", encoding="utf-8")
            _git(repo, "add", "f.txt")
            _git(repo, "commit", "-m", f"commit {label}")
            shas.append(_git(repo, "rev-parse", "HEAD"))
        return shas[0], shas[1], shas[2]

    def _run_resolver(
        self,
        *,
        repo: Path,
        head_sha: str,
        before: str,
        last_ok: str,
        repo_name: str = "pcalnon/juniper-ml",
    ) -> tuple[str, str, str]:
        """Return (base, reason_line, step_summary)."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            script_path = td_path / "resolve.sh"
            script_path.write_text(self.script, encoding="utf-8")
            gh_out = td_path / "gh_output"
            gh_out.write_text("", encoding="utf-8")
            step_summary = td_path / "step_summary"
            step_summary.write_text("", encoding="utf-8")

            stub_bin = td_path / "bin"
            stub_bin.mkdir()
            # Stub ``gh api … --jq .workflow_runs[0].head_sha`` → last_ok.
            gh = stub_bin / "gh"
            gh.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                f'printf "%s\\n" "{last_ok}"\n',
                encoding="utf-8",
            )
            gh.chmod(0o755)

            env = RedactedEnv(os.environ)
            env["PATH"] = str(stub_bin) + os.pathsep + env.get("PATH", "")
            env["GH_TOKEN"] = "unused"
            env["BEFORE"] = before
            env["HEAD_SHA"] = head_sha
            env["REPO"] = repo_name
            env["GITHUB_OUTPUT"] = str(gh_out)
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
            combined = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, msg=combined)
            written = gh_out.read_text(encoding="utf-8")
            m = re.search(r"^base=(.*)$", written, re.MULTILINE)
            self.assertIsNotNone(m, f"no base= in GITHUB_OUTPUT:\n{written}\n---\n{combined}")
            reason_m = re.search(r"Post-merge screen base: (.+)$", combined, re.MULTILINE)
            reason = reason_m.group(1).strip() if reason_m else ""
            return m.group(1).strip(), reason, step_summary.read_text(encoding="utf-8")

    def test_ancestor_last_ok_wins_catchup(self) -> None:
        """Successful main-verify tip that is an ancestor of HEAD becomes BASE (sweep)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sha_a, sha_b, sha_c = self._stage_repo(root)
            repo = root / "repo"
            base, reason, summary = self._run_resolver(
                repo=repo,
                head_sha=sha_c,
                before=sha_b,
                last_ok=sha_a,
            )
            self.assertEqual(base, sha_a)
            self.assertIn("catch-up from", reason)
            self.assertIn(sha_a, reason)
            self.assertIn(sha_a, summary)
            self.assertIn(sha_c, summary)

    def test_non_ancestor_last_ok_falls_to_event_before(self) -> None:
        """A tip that is not an ancestor of HEAD must not invent catch-up BASE."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sha_a, sha_b, sha_c = self._stage_repo(root)
            # Divergent tip: orphan commit not on HEAD's ancestry.
            orphan = root / "orphan"
            orphan.mkdir()
            _git(orphan, "init")
            _git(orphan, "config", "user.email", "t@t")
            _git(orphan, "config", "user.name", "t")
            _git(orphan, "config", "commit.gpgsign", "false")
            (orphan / "x").write_text("x\n", encoding="utf-8")
            _git(orphan, "add", "x")
            _git(orphan, "commit", "-m", "orphan")
            foreign = _git(orphan, "rev-parse", "HEAD")
            # Fetch the foreign object into the fixture so rev-parse succeeds but
            # merge-base --is-ancestor fails (not an ancestor of HEAD).
            repo = root / "repo"
            _git(repo, "fetch", str(orphan), "HEAD:refs/heads/foreign")
            base, reason, _summary = self._run_resolver(
                repo=repo,
                head_sha=sha_c,
                before=sha_b,
                last_ok=foreign,
            )
            self.assertEqual(base, sha_b)
            self.assertIn("event.before", reason)
            self.assertIn(sha_b, reason)
            self.assertNotIn("catch-up", reason)
            # silence unused
            self.assertTrue(sha_a)

    def test_zero_before_and_empty_last_ok_uses_head_parent(self) -> None:
        """Force-push / initial / dispatch: zero BEFORE + empty last_ok → HEAD^1."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _sha_a, sha_b, sha_c = self._stage_repo(root)
            repo = root / "repo"
            zeros = "0" * 40
            base, reason, _summary = self._run_resolver(
                repo=repo,
                head_sha=sha_c,
                before=zeros,
                last_ok="",
            )
            self.assertEqual(base, sha_b)
            self.assertIn("HEAD^1 fallback", reason)

    def test_last_ok_equal_head_skips_catchup(self) -> None:
        """last_ok == HEAD must not select itself as BASE (empty screen window)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _sha_a, sha_b, sha_c = self._stage_repo(root)
            repo = root / "repo"
            base, reason, _summary = self._run_resolver(
                repo=repo,
                head_sha=sha_c,
                before=sha_b,
                last_ok=sha_c,
            )
            self.assertEqual(base, sha_b)
            self.assertIn("event.before", reason)
            self.assertNotIn("catch-up", reason)

    def test_null_last_ok_jq_token_falls_through(self) -> None:
        """gh/jq ``null`` string must not be treated as a real SHA."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _sha_a, sha_b, sha_c = self._stage_repo(root)
            repo = root / "repo"
            base, reason, _summary = self._run_resolver(
                repo=repo,
                head_sha=sha_c,
                before=sha_b,
                last_ok="null",
            )
            self.assertEqual(base, sha_b)
            self.assertIn("event.before", reason)


if __name__ == "__main__":
    unittest.main()
