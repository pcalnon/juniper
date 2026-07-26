"""
Regression tests for the ad-hoc worktree sweep scripts.

The scripts are intentionally one-shot utilities, but ``worktree_sweep_apply``
is destructive outside ``--dry-run``. These tests pin the safety contract that
only SAFE rows produced by the survey are eligible for removal.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SURVEY_SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "worktree_sweep_survey.bash"
APPLY_SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "worktree_sweep_apply.bash"
SCRIPT_TIMEOUT_SECONDS = 30

REPO_KEYS = (
    "juniper-ml",
    "juniper-canopy",
    "juniper-cascor",
    "juniper-data",
    "juniper-deploy",
    "juniper-cascor-worker",
    "juniper-data-client",
    "juniper-cascor-client",
)


def _run_git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=True,
    )
    return result.stdout.strip()


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(path, "init", "-q", "-b", "main")
    _run_git(path, "config", "user.email", "tests@example.invalid")
    _run_git(path, "config", "user.name", "Test User")
    _run_git(path, "config", "commit.gpgsign", "false")
    (path / "README.md").write_text("# test\n")
    _run_git(path, "add", "README.md")
    _run_git(path, "commit", "-q", "-m", "initial")
    _run_git(path, "update-ref", "refs/remotes/origin/main", "HEAD")


class WorktreeSweepTestCase(unittest.TestCase):
    def _env(self, worktrees_root: Path, repo_base: Path) -> dict[str, str]:
        env = RedactedEnv(os.environ)
        env["JUNIPER_WORKTREE_SWEEP_ROOT"] = str(worktrees_root)
        env["JUNIPER_WORKTREE_SWEEP_REPO_BASE"] = str(repo_base)
        return env


class TestApplySafety(WorktreeSweepTestCase):
    def test_dry_run_removes_only_safe_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            main_repo = repo_base / "juniper-ml"
            _init_repo(main_repo)
            _run_git(
                main_repo,
                "worktree",
                "add",
                "-q",
                "-b",
                "safe-branch",
                str(worktrees_root / "juniper-ml--safe--20260604-0000--aaaa1111"),
                "main",
            )
            for name in ("juniper-ml--dirty--20260604-0000--bbbb2222", "juniper-ml--active--20260604-0000--cccc3333"):
                (worktrees_root / name).mkdir()

            rows = "\n".join(
                (
                    "# STATUS\tREPO\tBRANCH\tWORKTREE",
                    "SAFE\tjuniper-ml\tsafe-branch\tjuniper-ml--safe--20260604-0000--aaaa1111",
                    "DIRTY\tjuniper-ml\tdirty-branch\tjuniper-ml--dirty--20260604-0000--bbbb2222",
                    "ACTIVE\tjuniper-ml\tactive-branch\tjuniper-ml--active--20260604-0000--cccc3333",
                    "",
                )
            )

            result = subprocess.run(
                ["bash", str(APPLY_SCRIPT), "--dry-run"],
                input=rows,
                capture_output=True,
                text=True,
                env=self._env(worktrees_root, repo_base),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("DRY: git -C juniper-ml worktree remove", result.stdout)
            self.assertIn("safe-branch", result.stdout)
            self.assertIn("skipped (status DIRTY not safe): juniper-ml--dirty", result.stdout)
            self.assertIn("skipped (status ACTIVE not safe): juniper-ml--active", result.stdout)
            self.assertNotIn("branch -D dirty-branch", result.stdout)
            self.assertNotIn("branch -D active-branch", result.stdout)

    def test_unknown_repo_key_is_skipped_without_assoc_array_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()
            (worktrees_root / "unknown--safe--20260604-0000--aaaa1111").mkdir()

            result = subprocess.run(
                ["bash", str(APPLY_SCRIPT), "--dry-run"],
                input="SAFE\tunknown-repo\tbranch\tunknown--safe--20260604-0000--aaaa1111\n",
                capture_output=True,
                text=True,
                env=self._env(worktrees_root, repo_base),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("skipped (unknown repo): unknown-repo / unknown--safe", result.stdout)

    def test_stale_safe_row_is_revalidated_before_removal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            main_repo = repo_base / "juniper-ml"
            _init_repo(main_repo)
            worktree_name = "juniper-ml--active-after-survey--20260604-0000--dddd4444"
            worktree_path = worktrees_root / worktree_name
            _run_git(main_repo, "worktree", "add", "-q", "-b", "active-after-survey", str(worktree_path), "main")

            (worktree_path / "new-work.txt").write_text("not in origin/main\n")
            _run_git(worktree_path, "add", "new-work.txt")
            _run_git(worktree_path, "commit", "-q", "-m", "new local work")

            result = subprocess.run(
                ["bash", str(APPLY_SCRIPT), "--dry-run"],
                input=f"SAFE\tjuniper-ml\tactive-after-survey\t{worktree_name}\n",
                capture_output=True,
                text=True,
                env=self._env(worktrees_root, repo_base),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"skipped (no longer safe; ahead=1): {worktree_name}", result.stdout)
            self.assertNotIn("worktree remove", result.stdout)

    def test_stale_safe_row_cannot_delete_different_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            main_repo = repo_base / "juniper-ml"
            _init_repo(main_repo)
            _run_git(main_repo, "switch", "-q", "-c", "victim-branch")
            (main_repo / "victim.txt").write_text("unmerged local work\n")
            _run_git(main_repo, "add", "victim.txt")
            _run_git(main_repo, "commit", "-q", "-m", "victim work")
            _run_git(main_repo, "switch", "-q", "main")

            worktree_name = "juniper-ml--safe-current--20260604-0000--eeee5555"
            worktree_path = worktrees_root / worktree_name
            _run_git(main_repo, "worktree", "add", "-q", "-b", "safe-current", str(worktree_path), "main")

            result = subprocess.run(
                ["bash", str(APPLY_SCRIPT)],
                input=f"SAFE\tjuniper-ml\tvictim-branch\t{worktree_name}\n",
                capture_output=True,
                text=True,
                env=self._env(worktrees_root, repo_base),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(
                f"skipped (branch mismatch: row=victim-branch current=safe-current): {worktree_name}",
                result.stdout,
            )
            self.assertTrue(worktree_path.exists())
            _run_git(main_repo, "show-ref", "--verify", "--quiet", "refs/heads/victim-branch")

    def test_ignored_local_files_are_not_removed_as_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            main_repo = repo_base / "juniper-ml"
            _init_repo(main_repo)
            (main_repo / ".gitignore").write_text("*.secret\n")
            _run_git(main_repo, "add", ".gitignore")
            _run_git(main_repo, "commit", "-q", "-m", "ignore local secrets")
            _run_git(main_repo, "update-ref", "refs/remotes/origin/main", "HEAD")

            worktree_name = "juniper-ml--ignored-local--20260604-0000--ffff6666"
            worktree_path = worktrees_root / worktree_name
            _run_git(main_repo, "worktree", "add", "-q", "-b", "ignored-local", str(worktree_path), "main")
            (worktree_path / "local.secret").write_text("local-only data\n")

            result = subprocess.run(
                ["bash", str(APPLY_SCRIPT)],
                input=f"SAFE\tjuniper-ml\tignored-local\t{worktree_name}\n",
                capture_output=True,
                text=True,
                env=self._env(worktrees_root, repo_base),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"skipped (ignored files present; rerun with --include-ignored to sweep them): {worktree_name}", result.stdout)
            self.assertTrue((worktree_path / "local.secret").exists())
            _run_git(main_repo, "show-ref", "--verify", "--quiet", "refs/heads/ignored-local")

    def test_ignored_guard_not_blinded_by_show_untracked_files_no(self) -> None:
        """status.showUntrackedFiles=no must not fail-open the ignored guard.

        Plain `git status --porcelain --ignored` returns empty under that
        config even when ignored files exist; `git worktree remove` still
        succeeds on ignored-only debris, so a blinded guard deletes secrets.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            main_repo = repo_base / "juniper-ml"
            _init_repo(main_repo)
            (main_repo / ".gitignore").write_text("*.secret\n")
            _run_git(main_repo, "add", ".gitignore")
            _run_git(main_repo, "commit", "-q", "-m", "ignore local secrets")
            _run_git(main_repo, "update-ref", "refs/remotes/origin/main", "HEAD")

            worktree_name = "juniper-ml--ignored-blind--20260604-0000--9a9a9999"
            worktree_path = worktrees_root / worktree_name
            _run_git(main_repo, "worktree", "add", "-q", "-b", "ignored-blind", str(worktree_path), "main")
            (worktree_path / "local.secret").write_text("decrypted secret, must survive default apply\n")
            # Operator/repo config that blinds default porcelain --ignored.
            _run_git(worktree_path, "config", "status.showUntrackedFiles", "no")
            self.assertEqual(
                _run_git(worktree_path, "status", "--porcelain", "--ignored"),
                "",
                msg="precondition: config must blind plain --ignored visibility",
            )

            result = subprocess.run(
                ["bash", str(APPLY_SCRIPT)],
                input=f"SAFE\tjuniper-ml\tignored-blind\t{worktree_name}\n",
                capture_output=True,
                text=True,
                env=self._env(worktrees_root, repo_base),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(
                f"skipped (ignored files present; rerun with --include-ignored to sweep them): {worktree_name}",
                result.stdout,
            )
            self.assertTrue((worktree_path / "local.secret").exists())
            _run_git(main_repo, "show-ref", "--verify", "--quiet", "refs/heads/ignored-blind")

    def test_include_ignored_flag_sweeps_ignored_only_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            main_repo = repo_base / "juniper-ml"
            _init_repo(main_repo)
            (main_repo / ".gitignore").write_text("*.secret\n")
            _run_git(main_repo, "add", ".gitignore")
            _run_git(main_repo, "commit", "-q", "-m", "ignore local secrets")
            _run_git(main_repo, "update-ref", "refs/remotes/origin/main", "HEAD")

            worktree_name = "juniper-ml--ignored-optin--20260604-0000--abab7777"
            worktree_path = worktrees_root / worktree_name
            _run_git(main_repo, "worktree", "add", "-q", "-b", "ignored-optin", str(worktree_path), "main")
            (worktree_path / "local.secret").write_text("derived data, explicitly approved for sweep\n")

            result = subprocess.run(
                ["bash", str(APPLY_SCRIPT), "--include-ignored"],
                input=f"SAFE\tjuniper-ml\tignored-optin\t{worktree_name}\n",
                capture_output=True,
                text=True,
                env=self._env(worktrees_root, repo_base),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("removed: juniper-ml / ignored-optin", result.stdout)
            self.assertFalse(worktree_path.exists())
            with self.assertRaises(subprocess.CalledProcessError):
                _run_git(main_repo, "show-ref", "--verify", "--quiet", "refs/heads/ignored-optin")

    def test_include_ignored_still_hard_skips_untracked_dirt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            main_repo = repo_base / "juniper-ml"
            _init_repo(main_repo)
            worktree_name = "juniper-ml--untracked-dirt--20260604-0000--cdcd8888"
            worktree_path = worktrees_root / worktree_name
            _run_git(main_repo, "worktree", "add", "-q", "-b", "untracked-dirt", str(worktree_path), "main")
            (worktree_path / "precious.txt").write_text("untracked, never sweep\n")

            result = subprocess.run(
                ["bash", str(APPLY_SCRIPT), "--include-ignored"],
                input=f"SAFE\tjuniper-ml\tuntracked-dirt\t{worktree_name}\n",
                capture_output=True,
                text=True,
                env=self._env(worktrees_root, repo_base),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"skipped (no longer safe; dirty): {worktree_name}", result.stdout)
            self.assertTrue((worktree_path / "precious.txt").exists())
            _run_git(main_repo, "show-ref", "--verify", "--quiet", "refs/heads/untracked-dirt")

    def test_include_ignored_still_hard_skips_tracked_modification(self) -> None:
        """Tracked edits remain a hard skip even when --include-ignored is set."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            main_repo = repo_base / "juniper-ml"
            _init_repo(main_repo)
            worktree_name = "juniper-ml--tracked-dirt--20260604-0000--efef9999"
            worktree_path = worktrees_root / worktree_name
            _run_git(main_repo, "worktree", "add", "-q", "-b", "tracked-dirt", str(worktree_path), "main")
            (worktree_path / "README.md").write_text("# modified tracked file\n")

            result = subprocess.run(
                ["bash", str(APPLY_SCRIPT), "--include-ignored"],
                input=f"SAFE\tjuniper-ml\ttracked-dirt\t{worktree_name}\n",
                capture_output=True,
                text=True,
                env=self._env(worktrees_root, repo_base),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"skipped (no longer safe; dirty): {worktree_name}", result.stdout)
            self.assertTrue(worktree_path.exists())
            _run_git(main_repo, "show-ref", "--verify", "--quiet", "refs/heads/tracked-dirt")

    def test_unknown_flag_exits_2(self) -> None:
        """Arg parsing fail-closes on unknown flags (was single-flag before #715)."""
        result = subprocess.run(
            ["bash", str(APPLY_SCRIPT), "--force"],
            input="",
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown flag: --force", result.stderr)
        self.assertNotIn("removed:", result.stdout)
        self.assertNotIn("DRY:", result.stdout)

    def test_dry_run_and_include_ignored_can_combine(self) -> None:
        """Both new flags parse together; dry-run never deletes ignored-only worktrees."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            main_repo = repo_base / "juniper-ml"
            _init_repo(main_repo)
            (main_repo / ".gitignore").write_text("*.secret\n")
            _run_git(main_repo, "add", ".gitignore")
            _run_git(main_repo, "commit", "-q", "-m", "ignore local secrets")
            _run_git(main_repo, "update-ref", "refs/remotes/origin/main", "HEAD")

            worktree_name = "juniper-ml--ignored-combo--20260604-0000--1010bbbb"
            worktree_path = worktrees_root / worktree_name
            _run_git(main_repo, "worktree", "add", "-q", "-b", "ignored-combo", str(worktree_path), "main")
            (worktree_path / "local.secret").write_text("would be swept only without --dry-run\n")

            # Flag order must not matter for the multi-flag parser.
            for argv in (
                ["bash", str(APPLY_SCRIPT), "--dry-run", "--include-ignored"],
                ["bash", str(APPLY_SCRIPT), "--include-ignored", "--dry-run"],
            ):
                with self.subTest(argv=argv[2:]):
                    result = subprocess.run(
                        argv,
                        input=f"SAFE\tjuniper-ml\tignored-combo\t{worktree_name}\n",
                        capture_output=True,
                        text=True,
                        env=self._env(worktrees_root, repo_base),
                        timeout=SCRIPT_TIMEOUT_SECONDS,
                    )

                    self.assertEqual(result.returncode, 0, msg=result.stderr)
                    self.assertIn("DRY: git -C juniper-ml worktree remove", result.stdout)
                    self.assertIn("ignored-combo", result.stdout)
                    self.assertNotIn("removed:", result.stdout)
                    self.assertTrue(worktree_path.exists())
                    self.assertTrue((worktree_path / "local.secret").exists())
                    _run_git(main_repo, "show-ref", "--verify", "--quiet", "refs/heads/ignored-combo")


class TestSurveyApplyContract(WorktreeSweepTestCase):
    def test_survey_classifies_ignored_only_worktree_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            for repo_key in REPO_KEYS:
                _init_repo(repo_base / repo_key)

            main_repo = repo_base / "juniper-ml"
            (main_repo / ".gitignore").write_text("*.secret\n")
            _run_git(main_repo, "add", ".gitignore")
            _run_git(main_repo, "commit", "-q", "-m", "ignore local secrets")
            _run_git(main_repo, "update-ref", "refs/remotes/origin/main", "HEAD")

            worktree_name = "juniper-ml--ignored-survey--20260604-0000--9999aaaa"
            worktree_path = worktrees_root / worktree_name
            _run_git(main_repo, "worktree", "add", "-q", "-b", "ignored-survey", str(worktree_path), "main")
            (worktree_path / "local.secret").write_text("local-only data\n")

            survey = subprocess.run(
                ["bash", str(SURVEY_SCRIPT)],
                capture_output=True,
                text=True,
                env=self._env(worktrees_root, repo_base),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(survey.returncode, 0, msg=survey.stderr)
            data_rows = [line for line in survey.stdout.splitlines() if line and not line.startswith("#")]
            # Gitignored debris is not dirt (2026-07-25 triage: counting it made
            # SAFE unreachable); the apply script still guards ignored content
            # at removal time (default skip; --include-ignored to sweep).
            self.assertEqual(data_rows, [f"SAFE\tjuniper-ml\tignored-survey\t{worktree_name}"])

    def test_survey_classifies_untracked_dirt_as_dirty(self) -> None:
        """Plain --porcelain still marks real untracked dirt DIRTY (not loosened with ignored)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            for repo_key in REPO_KEYS:
                _init_repo(repo_base / repo_key)

            main_repo = repo_base / "juniper-ml"
            worktree_name = "juniper-ml--untracked-survey--20260604-0000--2020cccc"
            worktree_path = worktrees_root / worktree_name
            _run_git(main_repo, "worktree", "add", "-q", "-b", "untracked-survey", str(worktree_path), "main")
            (worktree_path / "precious.txt").write_text("untracked dirt must stay DIRTY\n")

            survey = subprocess.run(
                ["bash", str(SURVEY_SCRIPT)],
                capture_output=True,
                text=True,
                env=self._env(worktrees_root, repo_base),
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(survey.returncode, 0, msg=survey.stderr)
            data_rows = [line for line in survey.stdout.splitlines() if line and not line.startswith("#")]
            self.assertEqual(data_rows, [f"DIRTY\tjuniper-ml\tuntracked-survey\t{worktree_name}"])

    def test_survey_safe_row_can_feed_apply_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            worktrees_root = root / "worktrees"
            repo_base = root / "repos"
            worktrees_root.mkdir()
            repo_base.mkdir()

            for repo_key in REPO_KEYS:
                _init_repo(repo_base / repo_key)

            main_repo = repo_base / "juniper-ml"
            worktree_name = "juniper-ml--safe-sweep--20260604-0000--aaaa1111"
            _run_git(
                main_repo,
                "worktree",
                "add",
                "-q",
                "-b",
                "safe-sweep",
                str(worktrees_root / worktree_name),
                "main",
            )

            env = self._env(worktrees_root, repo_base)
            survey = subprocess.run(
                ["bash", str(SURVEY_SCRIPT)],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )
            self.assertEqual(survey.returncode, 0, msg=survey.stderr)

            data_rows = [line for line in survey.stdout.splitlines() if line and not line.startswith("#")]
            self.assertEqual(len(data_rows), 1, msg=survey.stdout)
            fields = data_rows[0].split("\t")
            self.assertEqual(fields, ["SAFE", "juniper-ml", "safe-sweep", worktree_name])

            apply = subprocess.run(
                ["bash", str(APPLY_SCRIPT), "--dry-run"],
                input=survey.stdout,
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

            self.assertEqual(apply.returncode, 0, msg=apply.stderr)
            self.assertIn(f"worktree remove {worktrees_root / worktree_name}", apply.stdout)
            self.assertIn("branch -D safe-sweep", apply.stdout)


if __name__ == "__main__":
    unittest.main()
