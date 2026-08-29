"""Hermetic tests for util/prune_git_branches_without_working_dirs.bash.

The script hard-codes BRANCH_TYPE=fix and deletes matching local branches whose
inferred ``.claude/<transformed-name>`` worktree directory is missing. That is a
destructive branch-hygiene path with no prior regression coverage.

Coverage (fixture repo only — never the real checkout):
- Stale merged ``fix/*`` without a tree dir → ``git branch -d``
- Force path (``-D`` / ``-F``) for unmerged stale ``fix/*``
- Present tree dir → branch kept (status path, no delete)
- Non-``fix`` branches never selected
- Currently checked-out ``fix/*`` tip is not deleted
- ``fix/*`` checked out in a linked worktree is not deleted
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "prune_git_branches_without_working_dirs.bash"
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


def _branches(cwd: Path) -> set[str]:
    result = _run_git(cwd, "branch", "--format=%(refname:short)")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _run_script(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = RedactedEnv(os.environ)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


def _claude_tree_dir(repo: Path, branch: str) -> Path:
    """Mirror the script's ``${i/-/s\\/}`` first-dash rewrite under ``.claude/``."""
    transformed = branch.replace("-", "s/", 1)
    return repo / ".claude" / transformed


class PruneGitBranchesWithoutWorkingDirsTest(unittest.TestCase):
    def test_deletes_stale_merged_fix_branch_without_tree_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            _run_git(repo, "branch", "fix/stale-merged")
            _run_git(repo, "branch", "feature/keep-me")
            self.assertIn("fix/stale-merged", _branches(repo))

            result = _run_script(repo)
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            branches = _branches(repo)
            self.assertNotIn("fix/stale-merged", branches)
            self.assertIn("feature/keep-me", branches)
            self.assertIn("main", branches)
            self.assertIn("closing branch", result.stdout)
            self.assertIn("Performing Standard Branch Delete", result.stdout)

    def test_keeps_fix_branch_when_inferred_tree_dir_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            _run_git(repo, "branch", "fix/kept-one")
            tree_dir = _claude_tree_dir(repo, "fix/kept-one")
            tree_dir.mkdir(parents=True)
            # Minimal nested git dir so ``git status`` in the script does not explode.
            _run_git(tree_dir, "init", "-q", "-b", "main")

            result = _run_script(repo)
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertIn("fix/kept-one", _branches(repo))
            self.assertIn("Valid Dir:", result.stdout)
            self.assertNotIn("closing branch", result.stdout)

    def test_force_flag_deletes_unmerged_stale_fix_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            _run_git(repo, "checkout", "-q", "-b", "fix/unmerged-stale")
            (repo / "extra.txt").write_text("unmerged\n")
            _run_git(repo, "add", "extra.txt")
            _run_git(repo, "commit", "-q", "-m", "unmerged change")
            _run_git(repo, "checkout", "-q", "main")

            # Standard -d must refuse an unmerged branch.
            soft = _run_script(repo)
            self.assertIn("fix/unmerged-stale", _branches(repo))
            self.assertIn("Performing Standard Branch Delete", soft.stdout)

            result = _run_script(repo, "-D")
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertNotIn("fix/unmerged-stale", _branches(repo))
            self.assertIn("Deleting Branch with --Force", result.stdout)

    def test_force_alias_f_matches_d(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            _run_git(repo, "checkout", "-q", "-b", "fix/force-f")
            (repo / "extra.txt").write_text("unmerged\n")
            _run_git(repo, "add", "extra.txt")
            _run_git(repo, "commit", "-q", "-m", "unmerged change")
            _run_git(repo, "checkout", "-q", "main")

            result = _run_script(repo, "-F")
            self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
            self.assertNotIn("fix/force-f", _branches(repo))
            self.assertIn("Deleting Branch with --Force", result.stdout)

    def test_does_not_delete_currently_checked_out_fix_branch(self) -> None:
        # Destructive hygiene must not remove the branch the operator is on.
        # ``git branch -d/-D`` refuses the current branch; pin that the script
        # leaves it intact (and that a failed delete does not wipe the tip).
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            _run_git(repo, "checkout", "-q", "-b", "fix/current-tip")
            (repo / "work.txt").write_text("on current\n")
            _run_git(repo, "add", "work.txt")
            _run_git(repo, "commit", "-q", "-m", "current tip work")

            result = _run_script(repo)
            combined = result.stdout + result.stderr
            self.assertIn("fix/current-tip", _branches(repo))
            # Current tip must still be checked out with its tip commit intact.
            head = _run_git(repo, "rev-parse", "--abbrev-ref", "HEAD")
            self.assertEqual(head.stdout.strip(), "fix/current-tip")
            self.assertTrue((repo / "work.txt").exists())
            # Standard -d against HEAD is a non-zero git failure; script must
            # not have force-deleted past that refusal.
            self.assertNotIn("Deleting Branch with --Force", combined)

    def test_does_not_delete_fix_branch_checked_out_in_linked_worktree(self) -> None:
        # A ``fix/*`` tip checked out in another worktree must survive a prune
        # from the primary checkout (``git branch -d`` refuses worktree-open
        # branches). Hermetic: linked worktree under the temp dir only.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _init_repo(repo)
            _run_git(repo, "branch", "fix/open-worktree")
            worktree = Path(tmp) / "wt-open"
            _run_git(repo, "worktree", "add", str(worktree), "fix/open-worktree")
            self.assertIn("fix/open-worktree", _branches(repo))

            result = _run_script(repo)
            combined = result.stdout + result.stderr
            # ``git branch -d`` refuses a worktree-open tip (nonzero). The
            # contract under test is that the branch/worktree survive — not
            # that the script masks git's refusal as exit 0.
            self.assertIn("fix/open-worktree", _branches(repo))
            self.assertIn("used by worktree", combined)
            self.assertTrue(worktree.is_dir())
            wt_head = _run_git(worktree, "rev-parse", "--abbrev-ref", "HEAD")
            self.assertEqual(wt_head.stdout.strip(), "fix/open-worktree")
            self.assertNotIn("Deleting Branch with --Force", combined)


if __name__ == "__main__":
    unittest.main()
