"""Hermetic tests for scripts/cleanup_session_worktrees.py.

The session-worktree cleaner force-removes ``.claude/worktrees/*`` plus local
and remote branches when a tip is on ``origin/main`` or a MERGED PR exists.
Wrong fail-open on ``_has_merged_pr`` (gh failure / bad JSON treated as
merged) would delete unmerged session work. Dirty / self-cwd / detached-HEAD
keeps prevent data loss mid-session.

Distinct from contested ``util/worktree_cleanup.bash`` (V2 orchestrator).
Policy / keep arms use real temp git worktrees + monkeypatched ``_run`` for
gh under ``dry_run=True``. Live ``_remove_worktree`` (``dry_run=False``) is
covered separately: unit matrix stubs every ``_run`` call; integration arms
exercise real ``git worktree remove --force`` + ``branch -D`` while stubbing
only ``fetch`` / ``push`` / ``gh`` (no network).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "cleanup_session_worktrees.py"
SCRIPT_TIMEOUT_SECONDS = 30


def _load_module():
    spec = importlib.util.spec_from_file_location("cleanup_session_worktrees", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # dataclasses reads sys.modules[cls.__module__] during decoration.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


cleanup = _load_module()


def _run_git(cwd: Path, *args: str) -> str:
    env = RedactedEnv(
        os.environ,
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@example.invalid",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@example.invalid",
    )
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=True,
        env=env,
    )
    return result.stdout.strip()


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    env = RedactedEnv(
        os.environ,
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@example.invalid",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@example.invalid",
    )
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True, env=env, timeout=SCRIPT_TIMEOUT_SECONDS)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=path, check=True, env=env, timeout=SCRIPT_TIMEOUT_SECONDS)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True, env=env, timeout=SCRIPT_TIMEOUT_SECONDS)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=path, check=True, env=env, timeout=SCRIPT_TIMEOUT_SECONDS)
    (path / "README.md").write_text("# test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True, env=env, timeout=SCRIPT_TIMEOUT_SECONDS)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=path, check=True, env=env, timeout=SCRIPT_TIMEOUT_SECONDS)
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", "HEAD"],
        cwd=path,
        check=True,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


def _add_worktree(repo: Path, name: str, branch: str) -> Path:
    root = repo / ".claude" / "worktrees"
    root.mkdir(parents=True, exist_ok=True)
    wt = root / name
    _run_git(repo, "worktree", "add", "-q", "-b", branch, str(wt), "main")
    return wt


class HasMergedPrTest(unittest.TestCase):
    """Fail-closed degrade for the gh MERGED-PR gate."""

    def test_gh_nonzero_rc_is_false(self) -> None:
        fake = mock.Mock(return_value=subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="auth"))
        with mock.patch.object(cleanup, "_run", fake):
            self.assertFalse(cleanup._has_merged_pr("pcalnon/juniper-ml", "worktree-x"))

    def test_invalid_json_is_false(self) -> None:
        fake = mock.Mock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="not-json{", stderr=""))
        with mock.patch.object(cleanup, "_run", fake):
            self.assertFalse(cleanup._has_merged_pr("pcalnon/juniper-ml", "worktree-x"))

    def test_merged_state_is_true(self) -> None:
        payload = json.dumps([{"state": "MERGED", "number": 1}, {"state": "OPEN", "number": 2}])
        fake = mock.Mock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=payload, stderr=""))
        with mock.patch.object(cleanup, "_run", fake):
            self.assertTrue(cleanup._has_merged_pr("pcalnon/juniper-ml", "worktree-x"))

    def test_open_only_is_false(self) -> None:
        payload = json.dumps([{"state": "OPEN", "number": 3}])
        fake = mock.Mock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=payload, stderr=""))
        with mock.patch.object(cleanup, "_run", fake):
            self.assertFalse(cleanup._has_merged_pr("pcalnon/juniper-ml", "worktree-x"))


class CleanupSessionWorktreesTest(unittest.TestCase):
    def _patch_fetch_and_gh(self, repo: Path, *, gh_side_effect=None):
        """Keep real git helpers; stub fetch/prune noise and optional gh."""
        real_run = cleanup._run

        def wrapper(args, cwd=None):
            if args[:3] == ["git", "-C", str(repo)] and len(args) > 3 and args[3] == "fetch":
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")
            if args and args[0] == "gh":
                if gh_side_effect is not None:
                    return gh_side_effect(args)
                return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="no-gh")
            return real_run(args, cwd=cwd)

        return mock.patch.object(cleanup, "_run", side_effect=wrapper)

    def test_dirty_worktree_kept(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-dirty", "worktree-dirty")
            (wt / "dirty.txt").write_text("x\n", encoding="utf-8")
            root = repo / ".claude" / "worktrees"
            with self._patch_fetch_and_gh(repo):
                report = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=root,
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=True,
                    allow_cwd=True,
                )
            self.assertEqual(report.kept_dirty, ["sess-dirty"])
            self.assertEqual(report.removed, [])
            self.assertTrue(wt.exists())

    def test_unmerged_clean_without_merged_pr_kept(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-unmerged", "worktree-unmerged")
            # Advance the worktree tip past origin/main so it is not an ancestor.
            (wt / "extra.txt").write_text("y\n", encoding="utf-8")
            _run_git(wt, "add", "extra.txt")
            _run_git(wt, "commit", "-q", "-m", "unmerged tip")
            root = repo / ".claude" / "worktrees"
            with self._patch_fetch_and_gh(repo):
                report = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=root,
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=True,
                    allow_cwd=True,
                )
            self.assertEqual(report.kept_unmerged, ["sess-unmerged"])
            self.assertEqual(report.removed, [])

    def test_main_ancestor_clean_dry_run_would_remove(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-merged", "worktree-merged")
            root = repo / ".claude" / "worktrees"
            with self._patch_fetch_and_gh(repo):
                report = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=root,
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=True,
                    allow_cwd=True,
                )
            self.assertEqual(report.removed, ["sess-merged"])
            self.assertEqual(report.kept_dirty, [])
            self.assertEqual(report.kept_unmerged, [])
            # dry-run must not delete the worktree or branch
            self.assertTrue(wt.exists())
            self.assertTrue((repo / ".git").exists())
            branches = _run_git(repo, "branch", "--list", "worktree-merged")
            self.assertIn("worktree-merged", branches)

    def test_merged_pr_allows_dry_run_remove_when_not_on_main(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-pr", "worktree-pr")
            (wt / "extra.txt").write_text("z\n", encoding="utf-8")
            _run_git(wt, "add", "extra.txt")
            _run_git(wt, "commit", "-q", "-m", "pr tip")
            root = repo / ".claude" / "worktrees"

            def gh_ok(args):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout=json.dumps([{"state": "MERGED", "number": 9}]),
                    stderr="",
                )

            with self._patch_fetch_and_gh(repo, gh_side_effect=gh_ok):
                report = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=root,
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=True,
                    allow_cwd=True,
                )
            self.assertEqual(report.removed, ["sess-pr"])
            self.assertTrue(wt.exists())

    def test_self_cwd_skipped_unless_allow_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-self", "worktree-self")
            root = repo / ".claude" / "worktrees"
            with self._patch_fetch_and_gh(repo):
                with mock.patch.object(cleanup, "_is_self_cwd", return_value=True):
                    report = cleanup.cleanup_session_worktrees(
                        repo=repo,
                        root=root,
                        gh_repo="pcalnon/juniper-ml",
                        dry_run=True,
                        allow_cwd=False,
                    )
            self.assertEqual(report.skipped_self, ["sess-self"])
            self.assertEqual(report.removed, [])
            self.assertTrue(wt.exists())

    def test_detached_head_kept_unmerged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-detach", "worktree-detach")
            tip = _run_git(wt, "rev-parse", "HEAD")
            _run_git(wt, "checkout", "--detach", tip)
            root = repo / ".claude" / "worktrees"
            with self._patch_fetch_and_gh(repo):
                report = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=root,
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=True,
                    allow_cwd=True,
                )
            self.assertEqual(report.kept_unmerged, ["sess-detach"])
            self.assertEqual(report.removed, [])

    def test_missing_root_exits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            with self.assertRaises(SystemExit) as ctx:
                cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=repo / ".claude" / "worktrees" / "missing",
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=True,
                    allow_cwd=True,
                )
            self.assertIn("worktree root does not exist", str(ctx.exception))


class IsSelfCwdTest(unittest.TestCase):
    def test_cwd_inside_worktree_is_self(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wt = Path(tmp) / "wt"
            nested = wt / "sub"
            nested.mkdir(parents=True)
            prev = Path.cwd()
            try:
                os.chdir(nested)
                self.assertTrue(cleanup._is_self_cwd(wt))
            finally:
                os.chdir(prev)

    def test_unrelated_cwd_is_not_self(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wt = Path(tmp) / "wt"
            wt.mkdir()
            other = Path(tmp) / "other"
            other.mkdir()
            prev = Path.cwd()
            try:
                os.chdir(other)
                self.assertFalse(cleanup._is_self_cwd(wt))
            finally:
                os.chdir(prev)


class RemoveWorktreeUnitTest(unittest.TestCase):
    """Stubbed ``_run`` matrix for live ``_remove_worktree`` (dry_run=False)."""

    def _cp(self, args, *, rc: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(args=args, returncode=rc, stdout=stdout, stderr=stderr)

    def test_dry_run_short_circuits_without_git(self) -> None:
        fake = mock.Mock(side_effect=AssertionError("_run must not be called under dry_run"))
        with mock.patch.object(cleanup, "_run", fake):
            ok, message = cleanup._remove_worktree(Path("/repo"), Path("/wt"), "worktree-x", dry_run=True)
        self.assertTrue(ok)
        self.assertIn("DRY-RUN", message)
        fake.assert_not_called()

    def test_worktree_remove_failure_is_hard_fail(self) -> None:
        def wrapper(args, cwd=None):
            if "worktree" in args and "remove" in args:
                return self._cp(args, rc=1, stderr="fatal: 'wt' is not a working tree\n")
            raise AssertionError(f"unexpected argv after failed remove: {args}")

        with mock.patch.object(cleanup, "_run", side_effect=wrapper):
            ok, message = cleanup._remove_worktree(Path("/repo"), Path("/wt"), "worktree-x", dry_run=False)
        self.assertFalse(ok)
        self.assertIn("worktree remove failed", message)
        self.assertIn("not a working tree", message)

    def test_happy_path_deletes_local_and_remote(self) -> None:
        seen: list[list[str]] = []

        def wrapper(args, cwd=None):
            seen.append(list(args))
            return self._cp(args, rc=0)

        with mock.patch.object(cleanup, "_run", side_effect=wrapper):
            ok, message = cleanup._remove_worktree(Path("/repo"), Path("/wt"), "worktree-x", dry_run=False)
        self.assertTrue(ok)
        self.assertEqual(message, "local-branch:deleted, remote-branch:deleted")
        self.assertEqual(
            seen,
            [
                ["git", "-C", "/repo", "worktree", "remove", "/wt", "--force"],
                ["git", "-C", "/repo", "branch", "-D", "worktree-x"],
                ["git", "-C", "/repo", "push", "origin", "--delete", "worktree-x"],
            ],
        )

    def test_remote_ref_already_gone_is_soft_success(self) -> None:
        def wrapper(args, cwd=None):
            if "push" in args and "--delete" in args:
                return self._cp(
                    args,
                    rc=1,
                    stderr="error: unable to delete 'worktree-x': remote ref does not exist\n",
                )
            return self._cp(args, rc=0)

        with mock.patch.object(cleanup, "_run", side_effect=wrapper):
            ok, message = cleanup._remove_worktree(Path("/repo"), Path("/wt"), "worktree-x", dry_run=False)
        self.assertTrue(ok)
        self.assertIn("local-branch:deleted", message)
        self.assertIn("remote-branch:already-gone", message)
        self.assertNotIn("remote-branch-failed", message)

    def test_remote_delete_other_failure_still_succeeds(self) -> None:
        def wrapper(args, cwd=None):
            if "push" in args and "--delete" in args:
                return self._cp(args, rc=1, stderr="fatal: could not read Username for 'https://github.com'\n")
            return self._cp(args, rc=0)

        with mock.patch.object(cleanup, "_run", side_effect=wrapper):
            ok, message = cleanup._remove_worktree(Path("/repo"), Path("/wt"), "worktree-x", dry_run=False)
        self.assertTrue(ok)
        self.assertIn("remote-branch-failed:", message)
        self.assertIn("could not read Username", message)

    def test_local_branch_delete_failure_is_best_effort(self) -> None:
        def wrapper(args, cwd=None):
            if "branch" in args and "-D" in args:
                return self._cp(args, rc=1, stderr="error: branch 'worktree-x' not found.\n")
            return self._cp(args, rc=0)

        with mock.patch.object(cleanup, "_run", side_effect=wrapper):
            ok, message = cleanup._remove_worktree(Path("/repo"), Path("/wt"), "worktree-x", dry_run=False)
        self.assertTrue(ok)
        self.assertIn("local-branch:error: branch 'worktree-x' not found.", message)
        self.assertIn("remote-branch:deleted", message)


class LiveRemoveWorktreeTest(unittest.TestCase):
    """Integration: real worktree remove + branch -D; stub fetch/push/gh only."""

    def _patch_fetch_push_gh(
        self,
        repo: Path,
        *,
        push_rc: int = 0,
        push_stderr: str = "",
        gh_side_effect=None,
    ):
        real_run = cleanup._run
        push_calls: list[list[str]] = []

        def wrapper(args, cwd=None):
            if args[:3] == ["git", "-C", str(repo)] and len(args) > 3 and args[3] == "fetch":
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")
            if args[:3] == ["git", "-C", str(repo)] and len(args) > 3 and args[3] == "push":
                push_calls.append(list(args))
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=push_rc,
                    stdout="",
                    stderr=push_stderr,
                )
            if args and args[0] == "gh":
                if gh_side_effect is not None:
                    return gh_side_effect(args)
                return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="no-gh")
            return real_run(args, cwd=cwd)

        return mock.patch.object(cleanup, "_run", side_effect=wrapper), push_calls

    def test_live_remove_main_ancestor_deletes_worktree_and_local_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-live", "worktree-live")
            root = repo / ".claude" / "worktrees"
            patcher, push_calls = self._patch_fetch_push_gh(repo)
            with patcher:
                report = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=root,
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=False,
                    allow_cwd=True,
                )
            self.assertEqual(report.removed, ["sess-live"])
            self.assertEqual(report.skipped_remove_failed, [])
            self.assertFalse(wt.exists(), "git worktree remove --force must delete the directory")
            branches = _run_git(repo, "branch", "--list", "worktree-live")
            self.assertEqual(branches, "", msg="local branch -D must run after a successful remove")
            self.assertEqual(
                push_calls,
                [["git", "-C", str(repo), "push", "origin", "--delete", "worktree-live"]],
            )

    def test_live_remove_remote_already_gone_still_removes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-gone", "worktree-gone")
            root = repo / ".claude" / "worktrees"
            patcher, push_calls = self._patch_fetch_push_gh(
                repo,
                push_rc=1,
                push_stderr="error: unable to delete 'worktree-gone': remote ref does not exist\n",
            )
            with patcher:
                report = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=root,
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=False,
                    allow_cwd=True,
                )
            self.assertEqual(report.removed, ["sess-gone"])
            self.assertEqual(report.skipped_remove_failed, [])
            self.assertFalse(wt.exists())
            self.assertEqual(len(push_calls), 1)

    def test_live_remove_failure_records_skipped_remove_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-fail", "worktree-fail")
            root = repo / ".claude" / "worktrees"
            real_run = cleanup._run

            def wrapper(args, cwd=None):
                if args[:3] == ["git", "-C", str(repo)] and len(args) > 3 and args[3] == "fetch":
                    return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")
                if args[:3] == ["git", "-C", str(repo)] and "worktree" in args and "remove" in args:
                    return subprocess.CompletedProcess(
                        args=args,
                        returncode=1,
                        stdout="",
                        stderr="fatal: injected worktree remove failure\n",
                    )
                if args and args[0] == "gh":
                    return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="no-gh")
                return real_run(args, cwd=cwd)

            with mock.patch.object(cleanup, "_run", side_effect=wrapper):
                report = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=root,
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=False,
                    allow_cwd=True,
                )
            self.assertEqual(report.skipped_remove_failed, ["sess-fail"])
            self.assertEqual(report.removed, [])
            self.assertTrue(wt.exists(), "failed remove must leave the worktree directory intact")


if __name__ == "__main__":
    unittest.main()
