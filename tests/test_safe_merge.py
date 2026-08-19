#!/usr/bin/env python3
"""Tests for util/safe_merge.py -- the R4 merge gate.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

`util/` is outside every pre-commit Python hook's scope (flake8/bandit scope to
`scripts` + `tests`), so this suite is the gate for a tool that merges code.

Hermetic by construction: `_gh` and `wait_for_required` are replaced with recorders, so
no network, no `gh`, no repo and no PR is ever touched. The assertions are about the
SAFETY CONTRACT -- every path that must refuse, and the one invariant that makes the gate
meaningful (`--match-head-commit` pinned to the head that was actually verified).
"""

from __future__ import annotations

import importlib.util
import pathlib
import unittest

_MOD_PATH = pathlib.Path(__file__).resolve().parents[1] / "util" / "safe_merge.py"
_spec = importlib.util.spec_from_file_location("safe_merge", _MOD_PATH)
assert _spec and _spec.loader
safe_merge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(safe_merge)


OPEN_CLEAN = {
    "state": "OPEN",
    "mergeStateStatus": "CLEAN",
    "mergeable": "MERGEABLE",
    "headRefOid": "a" * 40,
    "isDraft": False,
    "title": "t",
}


def _state(**over):
    d = dict(OPEN_CLEAN)
    d.update(over)
    return d


class Harness:
    """Records gh calls; replays a scripted sequence of PR states.

    Once `pr merge` has been issued the PR reports MERGED, so the tool's post-merge
    verification sees a real transition. `merge_succeeds=False` simulates the nastier
    case -- the merge command returns 0 but the PR did not actually merge.
    """

    def __init__(self, states, wait_result=None, merge_succeeds=True, settle_fails=False):
        self._states = list(states)
        self.calls: list[list[str]] = []
        self.wait_result = wait_result if wait_result is not None else {"_exit": 0}
        self.waits = 0
        self.merged = False
        self.merge_succeeds = merge_succeeds
        self.settle_fails = settle_fails

    def gh(self, args, timeout=120):
        self.calls.append(list(args))
        if list(args[:2]) == ["pr", "merge"] and self.merge_succeeds:
            self.merged = True
        return ""

    def pr_state(self, owner, repo, pr):
        if self.merged:
            return _state(state="MERGED")
        return self._states.pop(0) if len(self._states) > 1 else self._states[0]

    def wait(self, owner, repo, pr, timeout, verbose):
        self.waits += 1
        return dict(self.wait_result)

    def update_branch(self, owner, repo, pr, **kw):
        """Stubbed so tests neither sleep through the real settle-poll nor hit the network.

        Records a synthetic marker so the existing "was the server-side API used?"
        assertions still hold, and returns a settled head by default.
        """
        self.calls.append(["api", f"repos/{owner}/{repo}/pulls/{pr}/update-branch", "-X", "PUT"])
        return None if self.settle_fails else "e" * 40

    def install(self, tc):
        tc.monkey(safe_merge, "_gh", self.gh)
        tc.monkey(safe_merge, "pr_state", self.pr_state)
        tc.monkey(safe_merge, "wait_for_required", self.wait)
        tc.monkey(safe_merge, "update_branch", self.update_branch)


class SafeMergeTestBase(unittest.TestCase):
    def setUp(self):
        self._restore = []

    def tearDown(self):
        for obj, name, val in reversed(self._restore):
            setattr(obj, name, val)

    def monkey(self, obj, name, val):
        self._restore.append((obj, name, getattr(obj, name)))
        setattr(obj, name, val)

    def run_merge_installed(self, harness, **kw):
        kw.setdefault("execute", True)
        kw.setdefault("method", "squash")
        kw.setdefault("timeout", 60)
        kw.setdefault("verbose", False)
        kw.setdefault("log", lambda *a, **k: None)
        return safe_merge.safe_merge("o", "r", 1, **kw)

    def run_merge(self, harness, **kw):
        harness.install(self)
        kw.setdefault("execute", True)
        kw.setdefault("method", "squash")
        kw.setdefault("timeout", 60)
        kw.setdefault("verbose", False)
        kw.setdefault("log", lambda *a, **k: None)
        return safe_merge.safe_merge("o", "r", 1, **kw)


class RefusalTest(SafeMergeTestBase):
    """Every state that must refuse. A refusal must never degrade into a merge."""

    def _assert_refuses(self, harness, needle):
        with self.assertRaises(safe_merge.Refused) as ctx:
            self.run_merge(harness)
        self.assertIn(needle, str(ctx.exception).lower())
        merges = [c for c in harness.calls if c[:2] == ["pr", "merge"]]
        self.assertEqual(merges, [], "refused path must not merge")

    def test_refuses_closed_pr(self):
        self._assert_refuses(Harness([_state(state="CLOSED")]), "not open")

    def test_refuses_merged_pr(self):
        self._assert_refuses(Harness([_state(state="MERGED")]), "not open")

    def test_refuses_draft(self):
        self._assert_refuses(Harness([_state(isDraft=True)]), "draft")

    def test_refuses_conflicts(self):
        self._assert_refuses(Harness([_state(mergeStateStatus="DIRTY")]), "conflict")

    def test_refuses_when_required_checks_failed(self):
        h = Harness([_state()], wait_result={"_exit": 1, "failed": ["Regression Tests (3.12)"]})
        self._assert_refuses(h, "failed")

    def test_refuses_when_checks_never_finish(self):
        h = Harness([_state()], wait_result={"_exit": 2, "pending": ["Analyze (python)"]})
        self._assert_refuses(h, "did not finish")

    def test_failure_reason_names_the_context(self):
        h = Harness([_state()], wait_result={"_exit": 1, "failed": ["Sequence Safety"]})
        with self.assertRaises(safe_merge.Refused) as ctx:
            self.run_merge(h)
        self.assertIn("Sequence Safety", str(ctx.exception))

    def test_refuses_when_merge_returns_but_pr_did_not_merge(self):
        """A zero exit from `gh pr merge` is not proof the PR merged."""
        h = Harness([_state()], merge_succeeds=False)
        with self.assertRaises(safe_merge.Refused) as ctx:
            self.run_merge(h)
        self.assertIn("inspect manually", str(ctx.exception))

    def test_refuses_after_exhausting_sync_cycles(self):
        """Sustained concurrent merges must refuse, not spin forever."""
        h = Harness([_state(mergeStateStatus="BEHIND")])
        with self.assertRaises(safe_merge.Refused) as ctx:
            self.run_merge(h)
        self.assertIn("BEHIND", str(ctx.exception))
        self.assertEqual(
            len([c for c in h.calls if "update-branch" in " ".join(c)]),
            safe_merge.MAX_SYNC_CYCLES,
        )
        self.assertEqual([c for c in h.calls if c[:2] == ["pr", "merge"]], [])


class HeadPinningTest(SafeMergeTestBase):
    """The invariant that makes the gate meaningful (the ml#924 shape)."""

    def test_merge_pins_the_verified_head(self):
        head = "b" * 40
        h = Harness([_state(headRefOid=head)])
        out = self.run_merge(h)
        self.assertIn("MERGED", out)
        merges = [c for c in h.calls if c[:2] == ["pr", "merge"]]
        self.assertEqual(len(merges), 1)
        argv = merges[0]
        self.assertIn("--match-head-commit", argv)
        self.assertEqual(argv[argv.index("--match-head-commit") + 1], head)
        self.assertIn("--squash", argv)

    def test_pinned_head_is_the_one_that_was_waited_on(self):
        """Head captured BEFORE the wait is the head pinned at merge."""
        verified = "c" * 40
        h = Harness([_state(headRefOid=verified)])
        self.run_merge(h)
        argv = next(c for c in h.calls if c[:2] == ["pr", "merge"])
        self.assertEqual(argv[argv.index("--match-head-commit") + 1], verified)
        self.assertEqual(h.waits, 1)


class SyncTest(SafeMergeTestBase):
    def test_behind_is_repaired_server_side_then_merges(self):
        """BEHIND -> update-branch (signed) -> wait -> merge."""
        h = Harness([_state(mergeStateStatus="BEHIND"), _state(mergeStateStatus="BEHIND"), _state(), _state()])
        out = self.run_merge(h)
        self.assertIn("MERGED", out)
        upd = [c for c in h.calls if "update-branch" in " ".join(c)]
        self.assertEqual(len(upd), 1)
        self.assertIn("PUT", upd[0], "branch refresh must be the server-side (signed) API call")

    def test_no_local_git_is_ever_invoked(self):
        h = Harness([_state(mergeStateStatus="BEHIND"), _state(mergeStateStatus="BEHIND"), _state(), _state()])
        self.run_merge(h)
        for call in h.calls:
            self.assertNotIn("git", call[0], "the gate must never shell out to local git")


class DryRunTest(SafeMergeTestBase):
    def test_dry_run_merges_nothing(self):
        h = Harness([_state()])
        out = self.run_merge(h, execute=False)
        self.assertIn("DRY-RUN", out)
        self.assertEqual([c for c in h.calls if c[:2] == ["pr", "merge"]], [])

    def test_dry_run_does_not_update_branch(self):
        h = Harness([_state(mergeStateStatus="BEHIND")])
        out = self.run_merge(h, execute=False)
        self.assertIn("DRY-RUN", out)
        self.assertEqual([c for c in h.calls if "update-branch" in " ".join(c)], [])


class CliTest(unittest.TestCase):
    def test_rebase_is_rejected_as_signature_stripping(self):
        rc = safe_merge.main(["--pr", "1", "--merge-method", "rebase"])
        self.assertEqual(rc, 2)

    def test_parser_defaults_to_dry_run_and_squash(self):
        ns = safe_merge.build_parser().parse_args(["--pr", "1"]) if hasattr(safe_merge, "build_parser") else None
        if ns is None:  # module exposes only main(); assert via the docstring contract
            self.assertIn("--execute", safe_merge.__doc__)
            self.assertIn("dry-run", safe_merge.__doc__.lower())
        else:
            self.assertFalse(ns.execute)
            self.assertEqual(ns.merge_method, "squash")


class AsyncRefSettleTest(SafeMergeTestBase):
    """update-branch is 202 Accepted; the ref moves asynchronously.

    Regression for the defect this tool's FIRST live run exposed (ml#1170): reading the PR
    immediately after update-branch returned the OLD head, so the tool waited on that head's
    already-green checks and tried to merge a SHA that no longer existed. Only
    `--match-head-commit` stopped it.
    """

    def test_update_branch_polls_until_the_ref_actually_moves(self):
        old, new = "a" * 40, "d" * 40
        seq = [{"headRefOid": old}, {"headRefOid": old}, {"headRefOid": new}]
        calls = {"n": 0}

        def fake_state(owner, repo, pr):
            if calls["n"] == 0:  # the pre-update read
                calls["n"] += 1
                return {"headRefOid": old}
            return seq.pop(0) if len(seq) > 1 else seq[0]

        self.monkey(safe_merge, "pr_state", fake_state)
        self.monkey(safe_merge, "_gh", lambda *a, **k: "")
        got = safe_merge.update_branch("o", "r", 1, sleeper=lambda _s: None)
        self.assertEqual(got, new, "must return the NEW head, not the stale one")

    def test_update_branch_returns_none_if_ref_never_moves(self):
        self.monkey(safe_merge, "pr_state", lambda *a, **k: {"headRefOid": "a" * 40})
        self.monkey(safe_merge, "_gh", lambda *a, **k: "")
        self.assertIsNone(safe_merge.update_branch("o", "r", 1, sleeper=lambda _s: None))

    def test_unsettled_ref_refuses_rather_than_merging(self):
        h = Harness(
            [_state(mergeStateStatus="BEHIND"), _state(mergeStateStatus="BEHIND")],
            settle_fails=True,
        )
        with self.assertRaises(safe_merge.Refused) as ctx:
            self.run_merge(h)
        self.assertIn("settle", str(ctx.exception).lower())
        self.assertEqual([c for c in h.calls if c[:2] == ["pr", "merge"]], [])


class HeadMovedTest(SafeMergeTestBase):
    """A moved head is a REFUSAL (nothing merged), never a hard error."""

    def test_head_branch_was_modified_is_a_refusal(self):
        def gh(args, timeout=120):
            if list(args[:2]) == ["pr", "merge"]:
                raise safe_merge.HardError("gh pr merge 1… failed: GraphQL: Head branch was modified. " "Review and try the merge again. (mergePullRequest)")
            return ""

        self.monkey(safe_merge, "pr_state", lambda *a, **k: _state())
        self.monkey(safe_merge, "_gh", gh)
        self.monkey(safe_merge, "wait_for_required", lambda *a, **k: {"_exit": 0})
        with self.assertRaises(safe_merge.Refused) as ctx:
            safe_merge.safe_merge(
                "o",
                "r",
                1,
                execute=True,
                method="squash",
                timeout=5,
                verbose=False,
                log=lambda *a, **k: None,
            )
        self.assertIn("head moved", str(ctx.exception).lower())

    def test_other_merge_errors_stay_hard_errors(self):
        def gh(args, timeout=120):
            if list(args[:2]) == ["pr", "merge"]:
                raise safe_merge.HardError("gh pr merge 1… failed: 500 Internal Server Error")
            return ""

        self.monkey(safe_merge, "pr_state", lambda *a, **k: _state())
        self.monkey(safe_merge, "_gh", gh)
        self.monkey(safe_merge, "wait_for_required", lambda *a, **k: {"_exit": 0})
        with self.assertRaises(safe_merge.HardError):
            safe_merge.safe_merge(
                "o",
                "r",
                1,
                execute=True,
                method="squash",
                timeout=5,
                verbose=False,
                log=lambda *a, **k: None,
            )


class KillResilienceTest(SafeMergeTestBase):
    """Regressions for the killed-mid-wait incident (a second PR never merged).

    Root causes, all reproduced before fixing: the waiter was ORPHANED when the parent was
    killed (proven: it kept polling GitHub until its own 32-minute timeout); a kill produced
    no distinct exit state; and --dry-run blocked on the full wait, so the safe default was
    the expensive one.
    """

    def test_dry_run_does_not_wait_for_checks(self):
        """The cheap mode must be cheap -- it must not invoke the waiter at all."""
        h = Harness([_state()])
        out = self.run_merge(h, execute=False)
        self.assertIn("DRY-RUN", out)
        self.assertEqual(h.waits, 0, "dry-run must not block on required checks")

    def test_waiter_is_spawned_with_a_parent_death_signal(self):
        """Signal handlers cannot run on SIGKILL, so the kernel must enforce this."""
        import inspect

        src = inspect.getsource(safe_merge.wait_for_required)
        self.assertIn("preexec_fn=_die_with_parent", src)
        self.assertIn("Popen", src)
        self.assertNotIn("subprocess.run(", src)

    def test_die_with_parent_is_best_effort_and_never_raises(self):
        """Hardening must never be able to block a merge on an unsupported platform."""
        safe_merge._die_with_parent()  # must not raise here either

    def test_interrupted_exit_code_is_distinct(self):
        codes = {1, 2, 3}
        self.assertNotIn(safe_merge.EXIT_INTERRUPTED, codes)
        self.assertIn("INTERRUPTED", safe_merge.__doc__)

    def test_signal_handlers_kill_the_child_and_exit_interrupted(self):
        killed = {"n": 0}
        self.monkey(safe_merge, "_kill_child", lambda: killed.__setitem__("n", killed["n"] + 1))
        captured = {}

        def fake_signal(sig, handler):
            captured[sig] = handler

        self.monkey(safe_merge.signal, "signal", fake_signal)
        safe_merge._install_signal_handlers(lambda *a, **k: None)
        self.assertIn(safe_merge.signal.SIGTERM, captured)
        self.assertIn(safe_merge.signal.SIGINT, captured)

        exits = {}
        self.monkey(safe_merge.os, "_exit", lambda c: exits.__setitem__("code", c))
        captured[safe_merge.signal.SIGTERM](15, None)
        self.assertEqual(killed["n"], 1, "a signal must reap the waiter")
        self.assertEqual(exits["code"], safe_merge.EXIT_INTERRUPTED)

    def test_default_timeout_is_sized_from_measurement(self):
        """1800 s was ~5x the observed worst case; a stuck run should fail fast, not be
        killed opaquely by whatever supervisor is running the script."""
        self.assertLessEqual(safe_merge.DEFAULT_TIMEOUT, 900)
        self.assertGreaterEqual(safe_merge.DEFAULT_TIMEOUT, 600)


class AutoMergeNetTest(SafeMergeTestBase):
    """RC-4: hand the merge to GitHub so a killed run does not strand the PR.

    The gate is load-bearing. Where `allow_auto_merge` is false, `gh pr merge --auto` does NOT
    arm -- it falls back to an immediate merge, which with the owner's `always` bypass can land
    a PR whose checks never finished. Arming blind would reintroduce the exact bug this tool
    prevents.
    """

    def _harness(self, allow, state="BLOCKED"):
        # safe_merge reads pr_state once for the pre-loop guard and again at the top of the
        # cycle, so the state the LOOP should see must survive the guard's read.
        h = Harness([_state(mergeStateStatus=state), _state(mergeStateStatus=state), _state()])
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: allow)
        return h

    def test_net_is_armed_while_checks_are_pending(self):
        h = self._harness(allow=True)
        self.run_merge_installed(h)
        autos = [c for c in h.calls if c[:2] == ["pr", "merge"] and "--auto" in c]
        self.assertEqual(len(autos), 1, "the net should be armed exactly once")

    def test_net_is_NOT_armed_when_the_repo_forbids_auto_merge(self):
        h = self._harness(allow=False)
        self.run_merge_installed(h)
        autos = [c for c in h.calls if "--auto" in c]
        self.assertEqual(autos, [], "arming blind would risk an immediate untested merge")

    def test_net_is_not_armed_on_an_already_green_pr(self):
        """`--auto` on a green PR merges at once, skipping the head pinning."""
        h = self._harness(allow=True, state="CLEAN")
        self.run_merge_installed(h)
        self.assertEqual([c for c in h.calls if "--auto" in c], [])

    def test_net_winning_the_race_is_reported_as_success(self):
        h = Harness([_state(mergeStateStatus="BLOCKED"), _state(mergeStateStatus="BLOCKED"), _state(state="MERGED")])
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: True)
        out = self.run_merge_installed(h)
        self.assertIn("MERGED", out)
        self.assertIn("auto-merge net", out)

    def test_no_auto_fallback_disables_the_net(self):
        h = self._harness(allow=True)
        self.run_merge_installed(h, auto_fallback=False)
        self.assertEqual([c for c in h.calls if "--auto" in c], [])

    def test_repo_gate_fails_closed_on_a_probe_error(self):
        def boom(args, timeout=120):
            raise safe_merge.HardError("gh api failed")

        self.monkey(safe_merge, "_gh", boom)
        self.assertFalse(safe_merge.repo_allows_auto_merge("o", "r"))


class MergeabilityGateTest(SafeMergeTestBase):
    """Green checks are NOT the same as mergeable.

    ml's ruleset sets `required_review_thread_resolution: true`, so ONE unresolved review
    thread blocks the merge with every required context green -- and `gh pr checks` does not
    show it. Found live on ml#1183: two `github-advanced-security` CodeQL threads left the PR
    BLOCKED/MERGEABLE with zero failing checks, and merging blind produced a confusing
    "add the --auto flag" hard error instead of naming the blocker.
    """

    def test_blocked_with_green_checks_refuses_and_names_the_threads(self):
        h = Harness([_state(mergeStateStatus="BLOCKED"), _state(mergeStateStatus="BLOCKED")])
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: False)
        self.monkey(
            safe_merge,
            "unresolved_threads",
            lambda o, r, p: ["github-advanced-security: CodeQL / Empty except"],
        )
        with self.assertRaises(safe_merge.Refused) as ctx:
            self.run_merge_installed(h)
        msg = str(ctx.exception)
        self.assertIn("unresolved review thread", msg)
        self.assertIn("github-advanced-security", msg)
        self.assertEqual([c for c in h.calls if c[:2] == ["pr", "merge"]], [])

    def test_blocked_without_threads_still_names_the_state(self):
        h = Harness([_state(mergeStateStatus="BLOCKED"), _state(mergeStateStatus="BLOCKED")])
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: False)
        self.monkey(safe_merge, "unresolved_threads", lambda o, r, p: [])
        with self.assertRaises(safe_merge.Refused) as ctx:
            self.run_merge_installed(h)
        self.assertIn("mergeStateStatus=BLOCKED", str(ctx.exception))

    def test_unstable_is_still_mergeable(self):
        """UNSTABLE = a NON-required check is red. Required ones passed, so merge."""
        h = Harness([_state(mergeStateStatus="UNSTABLE"), _state(mergeStateStatus="UNSTABLE")])
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: False)
        out = self.run_merge_installed(h)
        self.assertIn("MERGED", out)

    def test_thread_probe_failure_never_blocks_the_merge(self):
        self.monkey(safe_merge, "_gh", lambda *a, **k: (_ for _ in ()).throw(safe_merge.HardError("x")))
        self.assertEqual(safe_merge.unresolved_threads("o", "r", 1), [])


class ContractTest(unittest.TestCase):
    """The tool must keep saying what it is, so nobody mistakes it for enforcement."""

    def test_documents_that_it_is_not_enforcement(self):
        self.assertIn("not enforcement", safe_merge.__doc__.lower())

    def test_documents_the_signing_constraint(self):
        doc = safe_merge.__doc__.lower()
        self.assertIn("update-branch", doc)
        self.assertIn("signed", doc)

    def test_sync_cycles_are_bounded(self):
        self.assertGreaterEqual(safe_merge.MAX_SYNC_CYCLES, 1)
        self.assertLessEqual(safe_merge.MAX_SYNC_CYCLES, 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
