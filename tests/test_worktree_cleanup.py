"""
Tests for util/worktree_cleanup.bash

Validates argument parsing, dry-run output, and error handling for the
worktree cleanup script. Most tests use --dry-run mode or validate argument
validation failures. Phase 6/7 ``pull --ff-only`` warn-and-skip cases drive a
real fixture repo via ``JUNIPER_ML_MAIN_REPO`` without running the full cleanup
pipeline.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "worktree_cleanup.bash"

# Subprocess timeout for worktree_cleanup.bash invocations (seconds).
SCRIPT_TIMEOUT_SECONDS: int = 30


def run_script(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run worktree_cleanup.bash with the given arguments."""
    return subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


def _run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=check,
    )


def _init_fixture_repo(path: Path) -> None:
    """Bare-bones git repo on main, ready for Phase 6/7 fixture setup."""
    path.mkdir(parents=True, exist_ok=True)
    _run_git(path, "init", "-q", "-b", "main")
    _run_git(path, "config", "user.email", "tests@example.invalid")
    _run_git(path, "config", "user.name", "Test User")
    _run_git(path, "config", "commit.gpgsign", "false")
    (path / "README.md").write_text("# test\n")
    _run_git(path, "add", "README.md")
    _run_git(path, "commit", "-q", "-m", "initial")


def _prepare_ff_divergent_repo(tmp: Path) -> Path:
    """Return a MAIN_REPO on main whose ``pull --ff-only origin main`` cannot FF.

    Local main and origin/main each have a unique commit (siblings), so
    ``--ff-only`` refuses. Models a primary checkout that drifted during a
    concurrent push to origin/main.
    """
    main_repo = tmp / "main-repo"
    remote = tmp / "remote.git"
    side = tmp / "side-clone"
    _init_fixture_repo(main_repo)
    _run_git(main_repo, "clone", "--bare", "-q", str(main_repo), str(remote))
    _run_git(main_repo, "remote", "add", "origin", str(remote))

    # Remote-only tip via a side clone (keeps main_repo's object db clean until
    # fetch/pull).
    subprocess.run(
        ["git", "clone", "-q", str(remote), str(side)],
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=True,
    )
    _run_git(side, "config", "user.email", "tests@example.invalid")
    _run_git(side, "config", "user.name", "Test User")
    _run_git(side, "config", "commit.gpgsign", "false")
    (side / "remote-only.txt").write_text("remote\n")
    _run_git(side, "add", "remote-only.txt")
    _run_git(side, "commit", "-q", "-m", "remote-only")
    _run_git(side, "push", "-q", "origin", "main")

    # Local-only tip on MAIN_REPO main → diverged from origin/main.
    (main_repo / "local-only.txt").write_text("local\n")
    _run_git(main_repo, "add", "local-only.txt")
    _run_git(main_repo, "commit", "-q", "-m", "local-only")
    return main_repo


def _run_phase6(main_repo: Path, new_worktree: Path, new_branch: str) -> subprocess.CompletedProcess[str]:
    """Source worktree_cleanup.bash (skipping main) and call phase_6 only."""
    driver = r"""
set -euo pipefail
export JUNIPER_ML_MAIN_REPO="$1"
SCRIPT_PATH="$2"
# shellcheck disable=SC1090
source <(sed '/^main "/d' "${SCRIPT_PATH}")
NEW_WORKTREE="$3"
NEW_BRANCH="$4"
DRY_RUN="${FALSE}"
phase_6_sync_main
"""
    env = RedactedEnv(os.environ)
    return subprocess.run(
        [
            "bash",
            "-c",
            driver,
            "phase6-driver",
            str(main_repo),
            str(SCRIPT_PATH),
            str(new_worktree),
            new_branch,
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


def _run_phase7(main_repo: Path) -> subprocess.CompletedProcess[str]:
    """Source worktree_cleanup.bash (skipping main) and call phase_7 only."""
    driver = r"""
set -euo pipefail
export JUNIPER_ML_MAIN_REPO="$1"
SCRIPT_PATH="$2"
# shellcheck disable=SC1090
source <(sed '/^main "/d' "${SCRIPT_PATH}")
DRY_RUN="${FALSE}"
phase_7_restore_main_checkout
"""
    env = RedactedEnv(os.environ)
    return subprocess.run(
        ["bash", "-c", driver, "phase7-driver", str(main_repo), str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


class TestArgumentParsing(unittest.TestCase):
    """Test argument parsing and validation."""

    def test_no_args_prints_usage_and_fails(self):
        result = run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--old-worktree", result.stderr)

    def test_help_flag_prints_usage(self):
        result = run_script("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
        self.assertIn("--old-worktree", result.stdout)

    def test_h_flag_prints_usage(self):
        result = run_script("-h")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)

    def test_missing_old_worktree_fails(self):
        result = run_script("--old-branch", "test-branch")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--old-worktree is required", result.stderr)

    def test_missing_old_branch_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script("--old-worktree", tmpdir)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--old-branch is required", result.stderr)

    def test_nonexistent_worktree_dir_fails(self):
        result = run_script(
            "--old-worktree",
            "/nonexistent/path/to/worktree",
            "--old-branch",
            "test-branch",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not exist", result.stderr)

    def test_unknown_argument_fails(self):
        result = run_script("--bogus-flag")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown argument", result.stderr)


class TestDryRun(unittest.TestCase):
    """Test --dry-run mode produces expected commands without executing."""

    def test_dry_run_shows_git_commands(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--parent-branch",
                "main",
                "--skip-pr",
                "--dry-run",
            )
            # Dry run should log the commands it would execute
            self.assertIn("[DRY-RUN]", result.stderr)
            # Should mention worktree operations
            self.assertIn("worktree", result.stderr.lower())

    def test_dry_run_outputs_new_worktree_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--new-worktree",
                "/tmp/test-new-worktree",
                "--new-branch",
                "worktree-test-new",
                "--skip-pr",
                "--dry-run",
            )
            # stdout should contain the new worktree path
            self.assertIn("/tmp/test-new-worktree", result.stdout.strip())

    def test_dry_run_with_custom_parent_branch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "feature-branch",
                "--parent-branch",
                "develop",
                "--skip-pr",
                "--dry-run",
            )
            self.assertIn("develop", result.stderr)

    def test_dry_run_default_parent_is_main(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--skip-pr",
                "--dry-run",
            )
            self.assertIn("Parent branch:  main", result.stderr)


class TestFlags(unittest.TestCase):
    """Test optional flag behaviors."""

    def test_skip_pr_flag_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--skip-pr",
                "--dry-run",
            )
            self.assertIn("Skipping PR creation", result.stderr)

    def test_skip_remote_delete_flag_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--skip-pr",
                "--skip-remote-delete",
                "--dry-run",
            )
            self.assertIn("Skipping remote branch deletion", result.stderr)

    def test_custom_new_branch_used(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--new-branch",
                "worktree-custom-name",
                "--skip-pr",
                "--dry-run",
            )
            self.assertIn("worktree-custom-name", result.stderr)

    def test_custom_new_worktree_path_used(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--new-worktree",
                "/tmp/my-custom-worktree",
                "--new-branch",
                "worktree-custom",
                "--skip-pr",
                "--dry-run",
            )
            self.assertIn("/tmp/my-custom-worktree", result.stderr)
            self.assertEqual(result.stdout.strip(), "/tmp/my-custom-worktree")


class TestPhaseOrdering(unittest.TestCase):
    """Verify that dry-run output shows phases in the correct order."""

    def test_phases_execute_in_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--skip-pr",
                "--dry-run",
            )
            stderr = result.stderr
            # Phase 1 should appear before Phase 2, etc.
            phase1_pos = stderr.find("Phase 1")
            phase2_pos = stderr.find("Phase 2")
            phase3_pos = stderr.find("Phase 3")
            phase4_pos = stderr.find("Phase 4")
            phase5_pos = stderr.find("Phase 5")

            self.assertGreater(phase1_pos, -1, "Phase 1 not found")
            self.assertGreater(phase2_pos, -1, "Phase 2 not found")
            self.assertGreater(phase3_pos, -1, "Phase 3 not found")
            self.assertGreater(phase4_pos, -1, "Phase 4 not found")
            self.assertGreater(phase5_pos, -1, "Phase 5 not found")

            self.assertLess(phase1_pos, phase2_pos, "Phase 1 should come before Phase 2")
            self.assertLess(phase2_pos, phase3_pos, "Phase 2 should come before Phase 3")
            self.assertLess(phase3_pos, phase4_pos, "Phase 3 should come before Phase 4")
            self.assertLess(phase4_pos, phase5_pos, "Phase 4 should come before Phase 5")

            # Phase 7 (restore MAIN_REPO checkout to main) runs last, after Phase 6.
            phase6_pos = stderr.find("Phase 6")
            phase7_pos = stderr.find("Phase 7")
            self.assertGreater(phase6_pos, -1, "Phase 6 not found")
            self.assertGreater(phase7_pos, -1, "Phase 7 not found")
            self.assertLess(phase5_pos, phase6_pos, "Phase 5 should come before Phase 6")
            self.assertLess(phase6_pos, phase7_pos, "Phase 6 should come before Phase 7")

    def test_dry_run_phase_7_restores_main_checkout(self):
        """Phase 7 previews the guarded main-checkout restore (F-6 stale-checkout class):
        checkout main in MAIN_REPO plus a --ff-only pull, and never a bare pull."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--skip-pr",
                "--dry-run",
            )
            stderr = result.stderr
            phase7_pos = stderr.find("Phase 7")
            self.assertGreater(phase7_pos, -1, "Phase 7 not found in dry-run output")
            phase7_out = stderr[phase7_pos:]
            self.assertIn("checkout main", phase7_out)
            self.assertIn("pull --ff-only origin main", phase7_out)

    def test_new_worktree_created_before_old_removed(self):
        """The critical safety property: new worktree add happens before old worktree remove."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--skip-pr",
                "--dry-run",
            )
            stderr = result.stderr
            add_pos = stderr.find("worktree add")
            remove_pos = stderr.find("worktree remove")

            self.assertGreater(add_pos, -1, "worktree add not found in dry-run output")
            self.assertGreater(remove_pos, -1, "worktree remove not found in dry-run output")
            self.assertLess(add_pos, remove_pos, "worktree add MUST happen before worktree remove (CWD safety)")


class TestSyncToMain(unittest.TestCase):
    """Verify cleanup syncs to the latest origin/main after the old worktree is removed (Phase 6)."""

    def test_dry_run_syncs_to_main(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--skip-pr",
                "--dry-run",
            )
            self.assertIn("Phase 6", result.stderr)
            self.assertIn("pull --ff-only origin main", result.stderr)

    def test_sync_runs_after_old_worktree_removed(self):
        """Sync to main is the final step: it runs after Phase 4 removes the old worktree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "test-branch",
                "--skip-pr",
                "--dry-run",
            )
            stderr = result.stderr
            remove_pos = stderr.find("worktree remove")
            sync_pos = stderr.find("pull --ff-only origin main")

            self.assertGreater(remove_pos, -1, "worktree remove not found in dry-run output")
            self.assertGreater(sync_pos, -1, "sync (pull --ff-only origin main) not found")
            self.assertLess(remove_pos, sync_pos, "sync to main must run after the old worktree is removed")


class TestPhasePullFfOnlyWarnSkip(unittest.TestCase):
    """Hermetic coverage for Phase 6/7 ``pull --ff-only`` warn-and-skip.

    Dry-run only pins the preview text. Open #731 covers Phase 7 dirty-tree /
    checkout-refusal; these cases pin the remaining best-effort pull failure
    path — a regression that treats non-ffable history as fatal aborts cleanup
    after the old worktree is already gone.
    """

    def test_phase7_pull_ff_only_failure_warns_and_skips(self) -> None:
        """Diverged MAIN_REPO main must warn-and-skip — never exit non-zero."""
        with tempfile.TemporaryDirectory() as tmp:
            main_repo = _prepare_ff_divergent_repo(Path(tmp))
            before = _run_git(main_repo, "rev-parse", "HEAD").stdout.strip()

            result = _run_phase7(main_repo)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Could not fast-forward MAIN_REPO main", result.stderr)
            self.assertIn("skipping", result.stderr.lower())

            after_branch = _run_git(main_repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
            after_sha = _run_git(main_repo, "rev-parse", "HEAD").stdout.strip()
            self.assertEqual(after_branch, "main")
            self.assertEqual(after_sha, before)
            self.assertTrue((main_repo / "local-only.txt").exists())
            self.assertFalse((main_repo / "remote-only.txt").exists())

    def test_phase6_pull_ff_only_failure_warns_and_skips(self) -> None:
        """Diverged continuity worktree must warn-and-skip — never abort cleanup."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_repo = _prepare_ff_divergent_repo(root)
            new_worktree = root / "continuity-worktree"
            new_branch = "worktree-cleanup-ff-fail"
            # Continuity branch tip shares the diverged local main; pull of
            # origin/main into it cannot fast-forward.
            _run_git(main_repo, "worktree", "add", "-q", "-b", new_branch, str(new_worktree), "main")
            before = _run_git(new_worktree, "rev-parse", "HEAD").stdout.strip()

            result = _run_phase6(main_repo, new_worktree, new_branch)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"Could not fast-forward '{new_branch}' to origin/main", result.stderr)
            self.assertIn("skipping", result.stderr.lower())

            after_branch = _run_git(new_worktree, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
            after_sha = _run_git(new_worktree, "rev-parse", "HEAD").stdout.strip()
            self.assertEqual(after_branch, new_branch)
            self.assertEqual(after_sha, before)
            self.assertTrue((new_worktree / "local-only.txt").exists())
            self.assertFalse((new_worktree / "remote-only.txt").exists())


if __name__ == "__main__":
    unittest.main()
