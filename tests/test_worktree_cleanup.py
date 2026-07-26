"""
Tests for util/worktree_cleanup.bash

Validates argument parsing, dry-run output, and error handling for the
worktree cleanup script. Most tests use --dry-run mode or validate argument
validation failures. Phase 3 existing-PR reuse / non-main parent cases drive a
real fixture repo (via JUNIPER_ML_MAIN_REPO) with a fake ``gh`` on PATH —
without the full cleanup pipeline.

Open coverage ownership (do not collide):
  * #747 / #753 — Phase 1 dirty / push / Phase 2 collision
  * #755 — Phase 3 no-ahead skip + ahead→create (helpers ``_p3_*`` / ``_run_phase3``)
  * this file — Phase 3 existing-PR reuse + non-main parent merge→PR
    (helpers ``_p3r_*`` / ``_run_phase3_reuse``; name-isolated from #755)
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


def _p3r_run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """git helper for Phase 3 reuse/non-main fixtures (name-isolated from open #755 ``_p3_*``)."""
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=check,
    )


def _p3r_init_repo(path: Path) -> None:
    """Bare-bones git repo with main + origin/main, ready for phase sourcing."""
    path.mkdir(parents=True, exist_ok=True)
    _p3r_run_git(path, "init", "-q", "-b", "main")
    _p3r_run_git(path, "config", "user.email", "tests@example.invalid")
    _p3r_run_git(path, "config", "user.name", "Test User")
    _p3r_run_git(path, "config", "commit.gpgsign", "false")
    (path / "README.md").write_text("# test\n")
    _p3r_run_git(path, "add", "README.md")
    _p3r_run_git(path, "commit", "-q", "-m", "initial")
    _p3r_run_git(path, "update-ref", "refs/remotes/origin/main", "HEAD")


def _p3r_attach_bare_origin(repo: Path, remote: Path) -> None:
    """Clone ``repo`` to a bare remote and wire ``origin`` so push/fetch work offline."""
    _p3r_run_git(repo, "clone", "--bare", "-q", str(repo), str(remote))
    _p3r_run_git(repo, "remote", "add", "origin", str(remote))


def _p3r_install_fake_gh(bin_dir: Path, log_path: Path, *, list_stdout: str = "") -> Path:
    """Install a recording fake ``gh``.

    ``list_stdout`` is printed for ``gh pr list`` (empty = no open PR; a bare
    number like ``42`` simulates ``--jq .[0].number`` finding an existing PR).
    Real ``gh`` prints nothing for an empty list — never ``[]`` — because
    phase_3 treats any non-empty value as an existing PR number.
    """
    bin_dir.mkdir(parents=True, exist_ok=True)
    gh = bin_dir / "gh"
    # Escape for embedding in the generated bash script.
    list_payload = list_stdout.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
    gh.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f'printf "%s\\n" "$*" >> "{log_path}"\n'
        'if [[ "${1:-}" == "pr" && "${2:-}" == "list" ]]; then\n'
        f'  printf "%s" "{list_payload}"\n'
        "  exit 0\n"
        "fi\n"
        'if [[ "${1:-}" == "pr" && "${2:-}" == "create" ]]; then\n'
        '  echo "https://example.invalid/pull/1"\n'
        "  exit 0\n"
        "fi\n"
        'echo "unexpected gh invocation: $*" >&2\n'
        "exit 99\n"
    )
    gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
    return gh


def _run_phase3_reuse(
    main_repo: Path,
    old_branch: str,
    *,
    path_prefix: str,
    parent_branch: str = "main",
) -> subprocess.CompletedProcess[str]:
    """Source the script and invoke ``phase_3_merge_and_pr`` (not dry-run).

    OLD_BRANCH / PARENT_BRANCH / SKIP_PR / DRY_RUN must be assigned *after*
    sourcing — the script body resets those globals. ``path_prefix`` must put
    the fake ``gh`` ahead of any real one. Name-isolated from open #755's
    ``_run_phase3``.
    """
    driver = r"""
set -euo pipefail
export JUNIPER_ML_MAIN_REPO="$1"
SCRIPT_PATH="$2"
# shellcheck disable=SC1090
source <(sed '/^main "/d' "${SCRIPT_PATH}")
OLD_BRANCH="$3"
PARENT_BRANCH="$4"
SKIP_PR="${FALSE}"
DRY_RUN="${FALSE}"
phase_3_merge_and_pr
"""
    env = RedactedEnv(os.environ, PATH=f"{path_prefix}:{os.environ.get('PATH', '')}")
    return subprocess.run(
        [
            "bash",
            "-c",
            driver,
            "phase3-reuse-driver",
            str(main_repo),
            str(SCRIPT_PATH),
            old_branch,
            parent_branch,
        ],
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


class TestPhase3ReuseAndNonMainBehavioral(unittest.TestCase):
    """Hermetic Phase 3 existing-PR reuse + non-main parent merge→PR arm.

    Open #755 covers no-ahead skip and ahead→create against ``main``. This class
    owns the leftover edges: a non-empty ``gh pr list`` must suppress
    ``gh pr create``, and a non-``main`` parent must merge locally then open the
    PR for the *parent* head (not the feature branch).
    """

    def test_existing_open_pr_skips_create(self) -> None:
        """Non-empty ``gh pr list`` stdout is treated as an existing PR number — never create."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_repo = root / "main-repo"
            remote = root / "remote.git"
            gh_log = root / "gh.log"
            bin_dir = root / "bin"
            _p3r_init_repo(main_repo)
            _p3r_attach_bare_origin(main_repo, remote)
            _p3r_run_git(main_repo, "push", "-q", "origin", "main")
            _p3r_run_git(main_repo, "checkout", "-q", "-b", "feature/reuse-pr")
            (main_repo / "more.txt").write_text("ahead\n")
            _p3r_run_git(main_repo, "add", "more.txt")
            _p3r_run_git(main_repo, "commit", "-q", "-m", "ahead for reuse")
            _p3r_run_git(main_repo, "push", "-u", "-q", "origin", "feature/reuse-pr")
            _p3r_run_git(main_repo, "fetch", "-q", "origin")
            _p3r_install_fake_gh(bin_dir, gh_log, list_stdout="42")

            result = _run_phase3_reuse(main_repo, "feature/reuse-pr", path_prefix=str(bin_dir))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("PR #42 already exists", result.stderr)
            self.assertTrue(gh_log.exists(), msg=result.stderr)
            logged = gh_log.read_text()
            self.assertIn("pr list", logged)
            self.assertNotIn("pr create", logged)
            self.assertIn("--head feature/reuse-pr", logged)

    def test_non_main_parent_merges_then_creates_pr_for_parent(self) -> None:
        """Parent != main: merge feature → parent, push parent, ``gh pr create --head <parent>``."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_repo = root / "main-repo"
            remote = root / "remote.git"
            gh_log = root / "gh.log"
            bin_dir = root / "bin"
            _p3r_init_repo(main_repo)
            _p3r_attach_bare_origin(main_repo, remote)
            _p3r_run_git(main_repo, "push", "-q", "origin", "main")
            # Parent branch on remote + local tracking ref.
            _p3r_run_git(main_repo, "checkout", "-q", "-b", "develop")
            (main_repo / "develop.txt").write_text("develop base\n")
            _p3r_run_git(main_repo, "add", "develop.txt")
            _p3r_run_git(main_repo, "commit", "-q", "-m", "develop base")
            _p3r_run_git(main_repo, "push", "-u", "-q", "origin", "develop")
            # Feature ahead of develop (and therefore of origin/develop).
            _p3r_run_git(main_repo, "checkout", "-q", "-b", "feature/onto-develop")
            (main_repo / "feature.txt").write_text("feature work\n")
            _p3r_run_git(main_repo, "add", "feature.txt")
            _p3r_run_git(main_repo, "commit", "-q", "-m", "feature onto develop")
            _p3r_run_git(main_repo, "push", "-u", "-q", "origin", "feature/onto-develop")
            _p3r_run_git(main_repo, "fetch", "-q", "origin")
            # Leave HEAD on main so phase_3's checkout develop is a real switch.
            _p3r_run_git(main_repo, "checkout", "-q", "main")
            _p3r_install_fake_gh(bin_dir, gh_log, list_stdout="")

            result = _run_phase3_reuse(
                main_repo,
                "feature/onto-develop",
                path_prefix=str(bin_dir),
                parent_branch="develop",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Merging feature/onto-develop into develop", result.stderr)
            self.assertIn("Creating PR: develop → main", result.stderr)
            self.assertTrue(gh_log.exists(), msg=result.stderr)
            logged = gh_log.read_text()
            self.assertIn("pr list", logged)
            self.assertIn("pr create", logged)
            self.assertIn("--head develop", logged)
            self.assertIn("--base main", logged)
            self.assertNotIn("--head feature/onto-develop", logged)
            # Parent tip on the bare remote must now include the feature commit.
            tip = _p3r_run_git(remote, "log", "-1", "--oneline", "develop")
            self.assertIn("feature onto develop", tip.stdout)
            # Working tree ends on the parent after the merge arm.
            head = _p3r_run_git(main_repo, "rev-parse", "--abbrev-ref", "HEAD")
            self.assertEqual(head.stdout.strip(), "develop")

    def test_dry_run_non_main_parent_previews_merge_then_parent_pr(self) -> None:
        """Dry-run (no --skip-pr) for a non-main parent must preview merge + parent→main PR."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(
                "--old-worktree",
                tmpdir,
                "--old-branch",
                "feature/onto-develop",
                "--parent-branch",
                "develop",
                "--dry-run",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("[DRY-RUN]", result.stderr)
            self.assertIn("merge feature/onto-develop", result.stderr)
            self.assertIn("push origin develop", result.stderr)
            self.assertIn("gh pr create", result.stderr)
            self.assertIn("--head develop", result.stderr)
            self.assertNotIn("--head feature/onto-develop", result.stderr)


if __name__ == "__main__":
    unittest.main()
