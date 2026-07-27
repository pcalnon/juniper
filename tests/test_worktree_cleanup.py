"""
Tests for util/worktree_cleanup.bash

Validates argument parsing, dry-run output, and error handling for the
worktree cleanup script. Most tests use --dry-run mode or validate argument
validation failures. Phase 4 remote-delete cases drive a real fixture repo
via JUNIPER_ML_MAIN_REPO + a fake ``gh`` on PATH so the open-PR skip guard
is exercised without running the full cleanup pipeline.
"""

from __future__ import annotations

import os
import stat
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
    """git helper for the Phase 4 remote-delete guard fixtures (restored after a merge dropped it)."""
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=check,
    )


def _p3r_run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """git helper for Phase 3 reuse/non-main fixtures (name-isolated from open #755 ``_p3_*``)."""
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=check,
    )


def _init_fixture_repo(path: Path) -> None:
    """Bare-bones git repo with main + a bare origin remote."""
    path.mkdir(parents=True, exist_ok=True)
    _p3r_run_git(path, "init", "-q", "-b", "main")
    _p3r_run_git(path, "config", "user.email", "tests@example.invalid")
    _p3r_run_git(path, "config", "user.name", "Test User")
    _p3r_run_git(path, "config", "commit.gpgsign", "false")
    (path / "README.md").write_text("# test\n")
    _p3r_run_git(path, "add", "README.md")
    _p3r_run_git(path, "commit", "-q", "-m", "initial")
    _p3r_run_git(path, "update-ref", "refs/remotes/origin/main", "HEAD")


def _install_fake_gh(bin_dir: Path, log_path: Path, open_pr_count: str) -> None:
    """Install a PATH-first ``gh`` that returns open-PR length and logs argv."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    gh = bin_dir / "gh"
    # Escape for embedding in the generated bash script.
    list_payload = list_stdout.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
    gh.write_text("#!/usr/bin/env bash\n" "set -euo pipefail\n" f'printf "%s\\n" "$*" >> "{log_path}"\n' 'if [[ "${1:-}" == "pr" && "${2:-}" == "list" ]]; then\n' f'  printf "%s" "{list_payload}"\n' "  exit 0\n" "fi\n" 'if [[ "${1:-}" == "pr" && "${2:-}" == "create" ]]; then\n' '  echo "https://example.invalid/pull/1"\n' "  exit 0\n" "fi\n" 'echo "unexpected gh invocation: $*" >&2\n' "exit 99\n")
    gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
    return gh


def _run_phase4(
    *,
    main_repo: Path,
    old_worktree: Path,
    old_branch: str,
    skip_remote_delete: bool,
    gh_bin: Path | None,
) -> subprocess.CompletedProcess[str]:
    """Source worktree_cleanup.bash (skipping main) and call phase_4_cleanup only."""
    driver = r"""
set -euo pipefail
export JUNIPER_ML_MAIN_REPO="$1"
SCRIPT_PATH="$2"
# shellcheck disable=SC1090
source <(sed '/^main "/d' "${SCRIPT_PATH}")
OLD_WORKTREE="$3"
OLD_BRANCH="$4"
# Script uses TRUE=0 / FALSE=1 (exit-status style).
if [[ "$5" == "1" ]]; then
    SKIP_REMOTE_DELETE="${TRUE}"
else
    SKIP_REMOTE_DELETE="${FALSE}"
fi
DRY_RUN="${FALSE}"
phase_4_cleanup
"""
    env = RedactedEnv(os.environ)
    if gh_bin is not None:
        env["PATH"] = f"{gh_bin}{os.pathsep}{env.get('PATH', '')}"
    return subprocess.run(
        [
            "bash",
            "-c",
            driver,
            "phase4-driver",
            str(main_repo),
            str(SCRIPT_PATH),
            str(old_worktree),
            old_branch,
            "1" if skip_remote_delete else "0",
        ],
        capture_output=True,
        text=True,
        env=env,
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
    """Bare-bones git repo with main + a bare origin remote."""
    path.mkdir(parents=True, exist_ok=True)
    _run_git(path, "init", "-q", "-b", "main")
    _run_git(path, "config", "user.email", "tests@example.invalid")
    _run_git(path, "config", "user.name", "Test User")
    _run_git(path, "config", "commit.gpgsign", "false")
    (path / "README.md").write_text("# test\n")
    _run_git(path, "add", "README.md")
    _run_git(path, "commit", "-q", "-m", "initial")


def _install_fake_gh(bin_dir: Path, log_path: Path, *, open_pr_count: str | None, exit_code: int = 0) -> None:
    """Install a PATH-first ``gh`` that logs argv and returns open-PR length or fails."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    gh_path = bin_dir / "gh"
    if exit_code != 0:
        body = "#!/usr/bin/env bash\n" "set -euo pipefail\n" f'echo "$*" >> "{log_path}"\n' 'echo "fake gh hard-fail" >&2\n' f"exit {exit_code}\n"
    else:
        body = "#!/usr/bin/env bash\n" "set -euo pipefail\n" f'echo "$*" >> "{log_path}"\n' 'if [[ "${1-}" == "pr" && "${2-}" == "list" ]]; then\n' f'  echo "{open_pr_count}"\n' "  exit 0\n" "fi\n" 'echo "unexpected gh invocation: $*" >&2\n' "exit 1\n"
    gh_path.write_text(body)
    gh_path.chmod(gh_path.stat().st_mode | stat.S_IXUSR)


def _run_phase4(
    *,
    main_repo: Path,
    old_worktree: Path,
    old_branch: str,
    skip_remote_delete: bool,
    gh_bin: Path | None,
) -> subprocess.CompletedProcess[str]:
    """Source worktree_cleanup.bash (skipping main) and call phase_4_cleanup only."""
    driver = r"""
set -euo pipefail
export JUNIPER_ML_MAIN_REPO="$1"
SCRIPT_PATH="$2"
# shellcheck disable=SC1090
source <(sed '/^main "/d' "${SCRIPT_PATH}")
OLD_WORKTREE="$3"
OLD_BRANCH="$4"
# Script uses TRUE=0 / FALSE=1 (exit-status style).
if [[ "$5" == "1" ]]; then
    SKIP_REMOTE_DELETE="${TRUE}"
else
    SKIP_REMOTE_DELETE="${FALSE}"
fi
DRY_RUN="${FALSE}"
phase_4_cleanup
"""
    env = RedactedEnv(os.environ)
    if gh_bin is not None:
        env["PATH"] = f"{gh_bin}{os.pathsep}{env.get('PATH', '')}"
    return subprocess.run(
        [
            "bash",
            "-c",
            driver,
            "phase4-driver",
            str(main_repo),
            str(SCRIPT_PATH),
            str(old_worktree),
            old_branch,
            "1" if skip_remote_delete else "0",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


def _prepare_phase4_fixture(tmp: Path, branch: str = "feature/phase4-victim") -> tuple[Path, Path, Path]:
    """Return (main_repo, old_worktree, bare_remote) with ``branch`` on the remote."""
    main_repo = tmp / "main-repo"
    old_worktree = tmp / "old-worktree"
    remote = tmp / "remote.git"
    _init_fixture_repo(main_repo)
    _run_git(main_repo, "clone", "--bare", "-q", str(main_repo), str(remote))
    _run_git(main_repo, "remote", "add", "origin", str(remote))
    _run_git(main_repo, "checkout", "-q", "-b", branch)
    _run_git(main_repo, "push", "-q", "-u", "origin", branch)
    # Hold the branch in a worktree; leave MAIN_REPO on main so remove/delete can proceed.
    _run_git(main_repo, "checkout", "-q", "main")
    _run_git(main_repo, "worktree", "add", "-q", str(old_worktree), branch)
    return main_repo, old_worktree, remote


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


class TestPhase4RemoteDeleteGuard(unittest.TestCase):
    """Hermetic behavioral gates for Phase 4's open-PR remote-delete skip.

    Dry-run only proves the ``--skip-remote-delete`` flag text and the
    ``[DRY-RUN] … push origin --delete`` preview. The live ``gh pr list`` →
    skip ``push --delete`` guard (protective when a PR is still open) was
    untested — a regression that deletes the remote head under an open PR
    breaks the PR and loses the backup branch.
    """

    def test_open_pr_skips_remote_delete(self) -> None:
        """Open PR for OLD_BRANCH → warn-and-skip; remote branch stays."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/phase4-open-pr"
            main_repo, old_worktree, _remote = _prepare_phase4_fixture(root, branch)
            gh_bin = root / "bin"
            gh_log = root / "gh.log"
            _install_fake_gh(gh_bin, gh_log, open_pr_count="1")

            before = _run_git(main_repo, "ls-remote", "--heads", "origin", branch).stdout
            self.assertIn(branch, before)

            result = _run_phase4(
                main_repo=main_repo,
                old_worktree=old_worktree,
                old_branch=branch,
                skip_remote_delete=False,
                gh_bin=gh_bin,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"PR is open for branch '{branch}'", result.stderr)
            self.assertIn("skipping remote branch deletion", result.stderr.lower())
            self.assertNotIn(f"Deleting remote branch: {branch}", result.stderr)
            self.assertFalse(old_worktree.exists())
            self.assertNotEqual(
                _run_git(main_repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode,
                0,
            )
            after = _run_git(main_repo, "ls-remote", "--heads", "origin", branch).stdout
            self.assertIn(branch, after)
            self.assertTrue(gh_log.exists())
            self.assertIn("pr list", gh_log.read_text())
            self.assertIn(f"--head {branch}", gh_log.read_text())

    def test_no_open_pr_deletes_remote_branch(self) -> None:
        """No open PR → remote branch is deleted (the complementary shape)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/phase4-no-pr"
            main_repo, old_worktree, _remote = _prepare_phase4_fixture(root, branch)
            gh_bin = root / "bin"
            gh_log = root / "gh.log"
            _install_fake_gh(gh_bin, gh_log, open_pr_count="0")

            result = _run_phase4(
                main_repo=main_repo,
                old_worktree=old_worktree,
                old_branch=branch,
                skip_remote_delete=False,
                gh_bin=gh_bin,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"Deleting remote branch: {branch}", result.stderr)
            self.assertNotIn("PR is open", result.stderr)
            self.assertFalse(old_worktree.exists())
            after = _run_git(main_repo, "ls-remote", "--heads", "origin", branch).stdout
            self.assertEqual(after.strip(), "")
            self.assertIn("pr list", gh_log.read_text())

    def test_skip_remote_delete_flag_skips_gh_and_push(self) -> None:
        """``--skip-remote-delete`` must not consult gh or push --delete (live path)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/phase4-flag-skip"
            main_repo, old_worktree, _remote = _prepare_phase4_fixture(root, branch)
            gh_bin = root / "bin"
            gh_log = root / "gh.log"
            # If gh is consulted, return a non-zero length so a buggy path would skip
            # for the wrong reason — the flag path must never call gh at all.
            _install_fake_gh(gh_bin, gh_log, open_pr_count="9")

            result = _run_phase4(
                main_repo=main_repo,
                old_worktree=old_worktree,
                old_branch=branch,
                skip_remote_delete=True,
                gh_bin=gh_bin,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Skipping remote branch deletion (--skip-remote-delete)", result.stderr)
            self.assertNotIn("PR is open", result.stderr)
            self.assertNotIn(f"Deleting remote branch: {branch}", result.stderr)
            after = _run_git(main_repo, "ls-remote", "--heads", "origin", branch).stdout
            self.assertIn(branch, after)
            self.assertFalse(gh_log.exists(), msg="gh must not be invoked when --skip-remote-delete is set")


if __name__ == "__main__":
    unittest.main()


class TestPhase4RemoteDeleteGuard(unittest.TestCase):
    """Hermetic behavioral gates for Phase 4's remote-delete skip guards.

    The open-PR check must fail CLOSED: a gh/auth/network failure must not be
    treated as "0 open PRs" and proceed to ``push --delete`` (that deletes the
    remote head under a live PR and loses the Phase-1 backup branch).
    """

    def test_gh_failure_skips_remote_delete(self) -> None:
        """gh non-zero exit → warn-and-skip; remote branch stays (fail-closed)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/phase4-gh-fail"
            main_repo, old_worktree, _remote = _prepare_phase4_fixture(root, branch)
            gh_bin = root / "bin"
            gh_log = root / "gh.log"
            _install_fake_gh(gh_bin, gh_log, open_pr_count=None, exit_code=1)

            before = _run_git(main_repo, "ls-remote", "--heads", "origin", branch).stdout
            self.assertIn(branch, before)

            result = _run_phase4(
                main_repo=main_repo,
                old_worktree=old_worktree,
                old_branch=branch,
                skip_remote_delete=False,
                gh_bin=gh_bin,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Could not query open PRs", result.stderr)
            self.assertIn("skipping remote branch deletion", result.stderr.lower())
            self.assertNotIn(f"Deleting remote branch: {branch}", result.stderr)
            after = _run_git(main_repo, "ls-remote", "--heads", "origin", branch).stdout
            self.assertIn(branch, after)
            self.assertTrue(gh_log.exists())

    def test_non_numeric_gh_result_skips_remote_delete(self) -> None:
        """Malformed gh/jq payload must not fall through into push --delete."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/phase4-gh-garbage"
            main_repo, old_worktree, _remote = _prepare_phase4_fixture(root, branch)
            gh_bin = root / "bin"
            gh_log = root / "gh.log"
            _install_fake_gh(gh_bin, gh_log, open_pr_count="not-a-number")

            result = _run_phase4(
                main_repo=main_repo,
                old_worktree=old_worktree,
                old_branch=branch,
                skip_remote_delete=False,
                gh_bin=gh_bin,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Unexpected open-PR query result", result.stderr)
            self.assertNotIn(f"Deleting remote branch: {branch}", result.stderr)
            after = _run_git(main_repo, "ls-remote", "--heads", "origin", branch).stdout
            self.assertIn(branch, after)

    def test_open_pr_skips_remote_delete(self) -> None:
        """Open PR for OLD_BRANCH → warn-and-skip; remote branch stays."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/phase4-open-pr"
            main_repo, old_worktree, _remote = _prepare_phase4_fixture(root, branch)
            gh_bin = root / "bin"
            gh_log = root / "gh.log"
            _install_fake_gh(gh_bin, gh_log, open_pr_count="1")

            result = _run_phase4(
                main_repo=main_repo,
                old_worktree=old_worktree,
                old_branch=branch,
                skip_remote_delete=False,
                gh_bin=gh_bin,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"PR is open for branch '{branch}'", result.stderr)
            self.assertIn("skipping remote branch deletion", result.stderr.lower())
            self.assertNotIn(f"Deleting remote branch: {branch}", result.stderr)
            after = _run_git(main_repo, "ls-remote", "--heads", "origin", branch).stdout
            self.assertIn(branch, after)

    def test_no_open_pr_deletes_remote_branch(self) -> None:
        """Proven-zero open PRs → remote branch is deleted (complementary shape)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/phase4-no-pr"
            main_repo, old_worktree, _remote = _prepare_phase4_fixture(root, branch)
            gh_bin = root / "bin"
            gh_log = root / "gh.log"
            _install_fake_gh(gh_bin, gh_log, open_pr_count="0")

            result = _run_phase4(
                main_repo=main_repo,
                old_worktree=old_worktree,
                old_branch=branch,
                skip_remote_delete=False,
                gh_bin=gh_bin,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"Deleting remote branch: {branch}", result.stderr)
            self.assertNotIn("PR is open", result.stderr)
            self.assertNotIn("Could not query open PRs", result.stderr)
            after = _run_git(main_repo, "ls-remote", "--heads", "origin", branch).stdout
            self.assertEqual(after.strip(), "")


if __name__ == "__main__":
    unittest.main()
