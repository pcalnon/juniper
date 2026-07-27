"""Regression tests for destructive open/stale worktree helpers.

Covers:
- ``util/remove_stale_worktrees.bash`` — removes only worktree paths whose
  ``git worktree list`` line contains the substring ``worktrees`` (the
  centralized Juniper worktree root convention). Primary checkout and
  non-matching linked worktrees must survive.
- ``util/cleanup_open_worktrees.bash`` — selects only ``+ worktree-*`` linked
  branches and skips inferred ``.claude/`` dirs that do not exist (never
  invents a pull/push target). Non-``worktree-*`` branches are untouched.

Hermetic temp repos only — never the real checkout.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
REMOVE_STALE_SCRIPT = REPO_ROOT / "util" / "remove_stale_worktrees.bash"
CLEANUP_OPEN_SCRIPT = REPO_ROOT / "util" / "cleanup_open_worktrees.bash"
SCRIPT_TIMEOUT_SECONDS = 30


def _run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=check,
    )


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(path, "init", "-q", "-b", "main")
    _run_git(path, "config", "user.email", "tests@example.invalid")
    _run_git(path, "config", "user.name", "Test User")
    _run_git(path, "config", "commit.gpgsign", "false")
    (path / "README.md").write_text("# test\n")
    _run_git(path, "add", "README.md")
    _run_git(path, "commit", "-q", "-m", "initial")


def _worktree_paths(repo: Path) -> set[str]:
    out = _run_git(repo, "worktree", "list", "--porcelain").stdout
    paths: set[str] = set()
    for line in out.splitlines():
        if line.startswith("worktree "):
            paths.add(line[len("worktree ") :])
    return paths


def _run_script(script: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = RedactedEnv(os.environ)
    return subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


class TestRemoveStaleWorktrees(unittest.TestCase):
    """Path-filter contract for ``remove_stale_worktrees.bash``."""

    def test_removes_only_worktrees_substring_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            _init_repo(repo)
            stale_root = root / "worktrees"
            stale_root.mkdir()
            stale = stale_root / "stale-wt"
            keep = root / "keep-wt"
            _run_git(repo, "worktree", "add", "-q", "-b", "stale-branch", str(stale), "main")
            _run_git(repo, "worktree", "add", "-q", "-b", "keep-branch", str(keep), "main")
            self.assertIn(str(stale), _worktree_paths(repo))
            self.assertIn(str(keep), _worktree_paths(repo))

            result = _run_script(REMOVE_STALE_SCRIPT, cwd=repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            paths = _worktree_paths(repo)
            self.assertNotIn(str(stale), paths)
            self.assertFalse(stale.exists())
            self.assertIn(str(keep), paths)
            self.assertTrue(keep.is_dir())
            # Primary checkout must never be selected (path lacks "worktrees").
            self.assertIn(str(repo), paths)
            self.assertTrue((repo / "README.md").is_file())

    def test_noop_when_no_worktrees_substring_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            _init_repo(repo)
            linked = root / "linked-wt"
            _run_git(repo, "worktree", "add", "-q", "-b", "linked-branch", str(linked), "main")
            before = _worktree_paths(repo)

            result = _run_script(REMOVE_STALE_SCRIPT, cwd=repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(_worktree_paths(repo), before)
            self.assertTrue(linked.is_dir())
            self.assertTrue((repo / "README.md").is_file())

    def test_empty_repo_exits_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)

            result = _run_script(REMOVE_STALE_SCRIPT, cwd=repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(_worktree_paths(repo), {str(repo)})


class TestCleanupOpenWorktrees(unittest.TestCase):
    """Selection / skip contract for ``cleanup_open_worktrees.bash``."""

    def test_skips_missing_inferred_claude_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            _init_repo(repo)
            linked = root / "linked-wt"
            _run_git(repo, "worktree", "add", "-q", "-b", "worktree-demo", str(linked), "main")
            before = _worktree_paths(repo)

            result = _run_script(CLEANUP_OPEN_SCRIPT, cwd=repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("Skipping Invalid Work Dir", result.stdout)
            self.assertNotIn("Found Valid Work Dir", result.stdout)
            # Skip path must not remove the linked worktree or primary checkout.
            self.assertEqual(_worktree_paths(repo), before)
            self.assertTrue(linked.is_dir())
            self.assertTrue((repo / "README.md").is_file())

    def test_ignores_non_worktree_prefixed_linked_branches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            _init_repo(repo)
            linked = root / "feature-wt"
            _run_git(repo, "worktree", "add", "-q", "-b", "feature/other", str(linked), "main")

            result = _run_script(CLEANUP_OPEN_SCRIPT, cwd=repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            # No ``+ worktree-*`` branch → loop body never runs.
            self.assertNotIn("Skipping Invalid Work Dir", result.stdout)
            self.assertNotIn("Found Valid Work Dir", result.stdout)
            self.assertIn(str(linked), _worktree_paths(repo))
            self.assertTrue(linked.is_dir())

    def test_valid_inferred_dir_is_entered(self) -> None:
        """When ``.claude/worktrees/<name>`` exists, the script takes the Valid Dir arm.

        ``git pull`` / ``git push`` are allowed to fail (no remote in the fixture);
        the contract under test is that the inferred path is recognized and entered
        rather than skipped. Network side effects are swallowed by the script
        (``2>/dev/null``) and must not flip the exit code.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            _init_repo(repo)
            linked = root / "linked-wt"
            _run_git(repo, "worktree", "add", "-q", "-b", "worktree-demo", str(linked), "main")
            # Mirror the script's first-dash rewrite: worktree-demo -> worktrees/demo
            inferred = repo / ".claude" / "worktrees" / "demo"
            inferred.mkdir(parents=True)
            _run_git(inferred, "init", "-q", "-b", "main")
            _run_git(inferred, "config", "user.email", "tests@example.invalid")
            _run_git(inferred, "config", "user.name", "Test User")
            _run_git(inferred, "config", "commit.gpgsign", "false")
            (inferred / "README.md").write_text("# inferred\n")
            _run_git(inferred, "add", "README.md")
            _run_git(inferred, "commit", "-q", "-m", "inferred initial")

            result = _run_script(CLEANUP_OPEN_SCRIPT, cwd=repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("Found Valid Work Dir", result.stdout)
            self.assertIn(str(inferred), result.stdout)
            self.assertNotIn("Skipping Invalid Work Dir", result.stdout)
            # Still must not destroy the real linked worktree / primary checkout.
            self.assertIn(str(linked), _worktree_paths(repo))
            self.assertIn(str(repo), _worktree_paths(repo))
            self.assertTrue((repo / "README.md").is_file())


if __name__ == "__main__":
    unittest.main()
