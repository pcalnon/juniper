"""Hermetic tests for scripts/cleanup_session_worktrees.py.

The session-worktree cleaner removes ``.claude/worktrees/*`` plus local
and remote branches when a tip is on ``origin/main`` or a MERGED PR exists.
Wrong fail-open on ``_has_merged_pr`` (gh failure / bad JSON treated as
merged) would delete unmerged session work. Locked / dirty / self-cwd /
detached-HEAD keeps prevent data loss mid-session -- the LOCK gate landed
2026-08-21 and is the one that recognises a LIVE session (see LockGateTest).

Distinct from contested ``util/worktree_cleanup.bash`` (V2 orchestrator).
Policy / keep arms use real temp git worktrees + monkeypatched ``_run`` for
gh under ``dry_run=True``. Live ``_remove_worktree`` (``dry_run=False``) is
covered separately: unit matrix stubs every ``_run`` call; integration arms
exercise real ``git worktree remove`` (no ``--force``) + ``branch -D`` while
stubbing only ``fetch`` / ``push`` / ``gh`` (no network).
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
        # No --force (2026-08-21): dirty and locked are both refused by the
        # caller, so force could only mask a surprise git is right to raise --
        # and it is one step from `-f -f`, which DOES delete a live session.
        self.assertEqual(
            seen,
            [
                ["git", "-C", "/repo", "worktree", "remove", "/wt"],
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


class LockGateTest(unittest.TestCase):
    """The gate this script shipped without.

    Claude Code locks a live session's worktree, naming the session and pid in
    the lock reason -- so git's lock flag is this fleet's liveness signal, and
    the cleaner never read it. Measured against the real worktree set on
    2026-08-21: the old code reported ``removed=8``, three of which were LOCKED
    live sessions, one of them holding the head branch of an OPEN pull request.

    A single ``--force`` does not defeat a lock (git refuses), so a live run
    could not actually delete a session. The damage was to the PLAN: ``--dry-run``
    said "WOULD REMOVE" for trees a real run refuses, and the operator who
    reconciles that contradiction reaches for ``-f -f`` or unlocks by hand.
    """

    def _stub_net(self, repo: Path):
        real_run = cleanup._run

        def wrapper(args, cwd=None):
            if args[:4] == ["git", "-C", str(repo), "fetch"]:
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")
            if args[:4] == ["git", "-C", str(repo), "push"]:
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")
            if args and args[0] == "gh":
                return subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr="no-gh")
            return real_run(args, cwd=cwd)

        return mock.patch.object(cleanup, "_run", side_effect=wrapper)

    def test_locked_worktree_is_parsed_with_its_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-lock", "worktree-lock")
            _run_git(repo, "worktree", "lock", str(wt), "--reason", "claude session (pid 4242)")
            locked = cleanup._locked_worktrees(repo)
            self.assertIn(wt.resolve(), locked)
            self.assertIn("pid 4242", locked[wt.resolve()])

    def test_bare_locked_line_without_a_reason_still_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-bare", "worktree-bare")
            _run_git(repo, "worktree", "lock", str(wt))
            locked = cleanup._locked_worktrees(repo)
            self.assertIn(wt.resolve(), locked)
            self.assertTrue(locked[wt.resolve()])

    def test_an_otherwise_removable_locked_worktree_is_kept(self) -> None:
        # THE regression. Clean + merged, so every pre-existing gate passes.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-live-session", "worktree-live-session")
            _run_git(repo, "worktree", "lock", str(wt), "--reason", "claude session (pid 99)")
            with self._stub_net(repo):
                report = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=repo / ".claude" / "worktrees",
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=False,
                    allow_cwd=True,
                )
            self.assertEqual(report.kept_locked, ["sess-live-session"])
            self.assertEqual(report.removed, [])
            self.assertTrue(wt.exists())

    def test_the_dry_run_plan_does_not_promise_to_remove_a_locked_tree(self) -> None:
        # The actual defect: a live run refuses, but the PLAN said it would go.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-plan", "worktree-plan")
            _run_git(repo, "worktree", "lock", str(wt), "--reason", "claude session (pid 7)")
            with self._stub_net(repo):
                report = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=repo / ".claude" / "worktrees",
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=True,
                    allow_cwd=True,
                )
            self.assertNotIn("sess-plan", report.removed)
            self.assertEqual(report.kept_locked, ["sess-plan"])

    def test_unlocking_makes_the_same_worktree_removable(self) -> None:
        # Proves the lock is what held it, not some unrelated gate.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "juniper-ml"
            _init_repo(repo)
            wt = _add_worktree(repo, "sess-unlock", "worktree-unlock")
            _run_git(repo, "worktree", "lock", str(wt), "--reason", "held")
            root = repo / ".claude" / "worktrees"
            with self._stub_net(repo):
                held = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=root,
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=False,
                    allow_cwd=True,
                )
            self.assertEqual(held.kept_locked, ["sess-unlock"])
            _run_git(repo, "worktree", "unlock", str(wt))
            with self._stub_net(repo):
                freed = cleanup.cleanup_session_worktrees(
                    repo=repo,
                    root=root,
                    gh_repo="pcalnon/juniper-ml",
                    dry_run=False,
                    allow_cwd=True,
                )
            self.assertEqual(freed.removed, ["sess-unlock"])
            self.assertFalse(wt.exists())

    def test_remove_is_never_called_with_force(self) -> None:
        # Anti-resurrection. Dirty and locked are both refused above the call,
        # so --force can only mask a surprise -- and it is one step from `-f -f`,
        # which DOES delete a live session's tree.
        src = (REPO_ROOT / "scripts" / "cleanup_session_worktrees.py").read_text(encoding="utf-8")
        self.assertNotIn('"--force"', src)
        self.assertNotIn("'-f'", src)
        self.assertNotIn('"-f"', src)

    def test_summary_line_reports_the_locked_bucket(self) -> None:
        # A held live session must be visible in the one line an operator reads.
        r = cleanup.CleanupReport(kept_locked=["a", "b"])
        self.assertIn("kept_locked=2", r.summary_line())
        self.assertEqual(r.total(), 2)


if __name__ == "__main__":
    unittest.main()
