"""
Regression tests for ``util/worktree_wipeout.bash`` and ``util/worktree_close.bash``.

These helpers are destructive (``git worktree remove``). The high-signal contract
is the pre-destroy gate: refuse missing / unknown targets without touching the
primary checkout, and only remove worktrees that match the caller's identifier.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
WIPEOUT_SCRIPT = REPO_ROOT / "util" / "worktree_wipeout.bash"
CLOSE_SCRIPT = REPO_ROOT / "util" / "worktree_close.bash"
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


def _run_script(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = RedactedEnv(os.environ)
    return subprocess.run(
        ["bash", str(script), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


def _worktree_paths(repo: Path) -> set[str]:
    out = _run_git(repo, "worktree", "list", "--porcelain").stdout
    paths: set[str] = set()
    for line in out.splitlines():
        if line.startswith("worktree "):
            paths.add(line[len("worktree ") :])
    return paths


class TestWorktreeWipeoutGates(unittest.TestCase):
    """Pre-destroy exit contract for ``worktree_wipeout.bash``."""

    def test_missing_name_exits_1_without_remove(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            before = _worktree_paths(repo)

            result = _run_script(WIPEOUT_SCRIPT, cwd=repo)

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("Worktree name not provided", result.stdout)
            self.assertEqual(_worktree_paths(repo), before)
            self.assertTrue((repo / "README.md").is_file())

    def test_invalid_worktree_exits_2_without_remove(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            _init_repo(repo)
            linked = root / "linked-wt"
            _run_git(repo, "worktree", "add", "-q", "-b", "keep-branch", str(linked), "main")
            before = _worktree_paths(repo)
            self.assertIn(str(linked), before)

            result = _run_script(WIPEOUT_SCRIPT, "definitely-not-a-worktree", cwd=repo)

            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("Provided Worktree is Invalid", result.stdout)
            self.assertEqual(_worktree_paths(repo), before)
            self.assertTrue(linked.is_dir())
            self.assertTrue((repo / "README.md").is_file())

    def test_valid_worktree_path_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            _init_repo(repo)
            linked = root / "wipe-me"
            _run_git(repo, "worktree", "add", "-q", "-b", "wipe-branch", str(linked), "main")
            self.assertIn(str(linked), _worktree_paths(repo))

            result = _run_script(WIPEOUT_SCRIPT, str(linked), cwd=repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("Received Valid Worktree", result.stdout)
            self.assertIn("Worktree Cleanup:", result.stdout)
            self.assertNotIn(str(linked), _worktree_paths(repo))
            self.assertFalse(linked.exists())
            # Primary checkout must survive the wipeout path.
            self.assertIn(str(repo), _worktree_paths(repo))
            self.assertTrue((repo / "README.md").is_file())


class TestWorktreeCloseGates(unittest.TestCase):
    """Match / not-found contract for ``worktree_close.bash``."""

    def test_unmatched_identifier_reports_not_found_and_keeps_worktrees(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            _init_repo(repo)
            linked = root / "other--worktree"
            _run_git(repo, "worktree", "add", "-q", "-b", "other-branch", str(linked), "main")
            before = _worktree_paths(repo)

            result = _run_script(CLOSE_SCRIPT, "fix--connect-canopy-cascor", cwd=repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("Worktree Not Found", result.stdout)
            self.assertNotIn("removing ", result.stdout)
            self.assertEqual(_worktree_paths(repo), before)
            self.assertTrue(linked.is_dir())

    def test_matched_identifier_removes_only_matching_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            _init_repo(repo)
            target = root / "repo--fix--connect-canopy-cascor--wt"
            keep = root / "repo--unrelated--wt"
            _run_git(repo, "worktree", "add", "-q", "-b", "target-branch", str(target), "main")
            _run_git(repo, "worktree", "add", "-q", "-b", "keep-branch", str(keep), "main")

            result = _run_script(CLOSE_SCRIPT, "fix--connect-canopy-cascor", cwd=repo)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn(f"removing {target}", result.stdout)
            self.assertIn("Worktree(s) Removed", result.stdout)
            paths = _worktree_paths(repo)
            self.assertNotIn(str(target), paths)
            self.assertFalse(target.exists())
            self.assertIn(str(keep), paths)
            self.assertTrue(keep.is_dir())
            self.assertIn(str(repo), paths)


if __name__ == "__main__":
    unittest.main()
