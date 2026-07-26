"""
Tests for util/worktree_cleanup.bash

Validates argument parsing, dry-run output, and error handling for the
worktree cleanup script. Does NOT execute actual git operations — all tests
use --dry-run mode or validate argument validation failures.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
