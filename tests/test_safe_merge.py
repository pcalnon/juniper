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


class NetWonRaceTest(SafeMergeTestBase):
    """ml#1228: the armed net merging DURING the local `gh pr merge` was reported as exit 3.

    Observed verbatim -- "all required checks green — merging 188a5259 (squash)" followed by
    "ERROR: … Pull Request is not mergeable (mergePullRequest)" -- on a PR that had in fact
    merged correctly (14e7af41, 23:30:06Z). The armed net won.

    The pre-merge state check already covers the net winning EARLIER. This is the window
    between that check and the merge call, and D1 widened it: arming on BLOCKED/BEHIND/UNKNOWN
    keeps a net live far more often than arming on BLOCKED alone did. The cost is trust rather
    than correctness -- the merge lands either way -- which is exactly why it needs pinning:
    a tool that reports its successes as failures stops being believed about its failures.
    """

    NOT_MERGEABLE = "gh pr merge 1… failed: GraphQL: Pull Request is not mergeable (mergePullRequest)"
    VERIFIED = "a" * 40  # OPEN_CLEAN's headRefOid -- the head this run vouches for
    OTHER = "b" * 40

    def _install(self, *, merge_error=NOT_MERGEABLE, probe=None, probe_raises=False, arm=True):
        """Serve pre-merge states until `gh pr merge` is attempted, then serve `probe`.

        `arm=True` drives the real arming path (BLOCKED at the cycle top) rather than poking
        `_ARMED` directly, so the message wording is asserted against a net this run actually
        armed. `arm=False` leaves every state CLEAN, which is not ARMABLE -- so nothing arms.
        """
        box: dict = {"attempted": False, "merges": []}
        pre = [_state(mergeStateStatus="BLOCKED"), _state(mergeStateStatus="BLOCKED"), _state()] if arm else [_state()]

        def gh(args, timeout=120):
            if list(args[:2]) == ["pr", "merge"]:
                box["merges"].append(list(args))
                if "--auto" in args:
                    return ""  # arming the net succeeds
                box["attempted"] = True
                raise safe_merge.HardError(merge_error)
            return ""

        def pr_state(owner, repo, pr):
            if box["attempted"]:
                if probe_raises:
                    raise safe_merge.HardError("gh pr view 1… failed: network is unreachable")
                return probe
            return pre.pop(0) if len(pre) > 1 else pre[0]

        # Restored on tearDown: the success path deliberately does NOT disarm, so without
        # this a leaked `_ARMED` would short-circuit `arm_auto_merge` in a later test.
        self.monkey(safe_merge, "_ARMED", None)
        self.monkey(safe_merge, "_gh", gh)
        self.monkey(safe_merge, "pr_state", pr_state)
        self.monkey(safe_merge, "wait_for_required", lambda *a, **k: {"_exit": 0})
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: True)
        return box

    def test_net_winning_inside_the_merge_call_is_a_success(self):
        box = self._install(probe=_state(state="MERGED", headRefOid=self.VERIFIED))
        out = self.run_merge_installed(None)
        self.assertIn("MERGED", out)
        self.assertTrue(box["attempted"], "the local merge must actually have been attempted")

    def test_the_success_names_the_armed_net_and_the_verified_head(self):
        self._install(probe=_state(state="MERGED", headRefOid=self.VERIFIED))
        out = self.run_merge_installed(None)
        self.assertIn("auto-merge net", out)
        self.assertIn(self.VERIFIED[:8], out)

    def test_success_never_claims_a_net_that_was_not_armed(self):
        """The message is read off `_ARMED`, not assumed -- see `_merged_by_other`."""
        box = self._install(arm=False, probe=_state(state="MERGED", headRefOid=self.VERIFIED))
        out = self.run_merge_installed(None)
        self.assertEqual([c for c in box["merges"] if "--auto" in c], [], "nothing should arm on CLEAN")
        self.assertIn("MERGED", out)
        self.assertNotIn("armed auto-merge net", out)
        self.assertIn("armed no net", out)

    def test_a_merge_at_an_unverified_head_is_a_hard_error(self):
        """MERGED is not enough. It has to be merged at the head this run waited on."""
        self._install(probe=_state(state="MERGED", headRefOid=self.OTHER))
        with self.assertRaises(safe_merge.HardError) as ctx:
            self.run_merge_installed(None)
        msg = str(ctx.exception)
        self.assertIn(self.OTHER[:8], msg)
        self.assertIn(self.VERIFIED[:8], msg)
        self.assertNotIn("MERGED #1 by", msg)

    def test_any_merge_failure_is_re_checked_not_just_not_mergeable(self):
        """A merge that landed and then failed to REPORT is the same situation, same answer."""
        self._install(
            merge_error="gh pr merge 1… failed: 502 Bad Gateway",
            probe=_state(state="MERGED", headRefOid=self.VERIFIED),
        )
        self.assertIn("MERGED", self.run_merge_installed(None))

    def test_a_still_open_pr_keeps_the_hard_error(self):
        """The probe must not become a swallow-everything: an unmerged PR still fails loudly."""
        self._install(merge_error="gh pr merge 1… failed: 502 Bad Gateway", probe=_state())
        with self.assertRaises(safe_merge.HardError) as ctx:
            self.run_merge_installed(None)
        self.assertIn("502", str(ctx.exception))

    def test_a_failed_probe_never_masks_the_original_error(self):
        self._install(probe_raises=True)
        with self.assertRaises(safe_merge.HardError) as ctx:
            self.run_merge_installed(None)
        self.assertIn("not mergeable", str(ctx.exception))


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
        """A stuck run should fail fast, not be killed opaquely by its supervisor.

        This assertion used to read `DEFAULT_TIMEOUT <= 900`. The INTENT (fail fast) is
        kept; the literal 900 is not, because it was derived from one workflow on one repo
        (ml's `ci.yml` median) and re-measurement across all required contexts showed it sat
        at juniper-canopy's MEDIAN -- turning roughly half of canopy's healthy merges into
        "checks did not finish" refusals. Fast failure is now expressed per repo, as a ratio
        to that repo's own measured p90, which is what "fast" actually meant.
        """
        measured_p90 = {
            # ml re-measured 2026-09-05 (n=12); was 263 on 2026-08-20. The upper bound below
            # is what forced the new budget to be chosen rather than guessed: it must clear
            # the observed max (823 s) AND stay inside 4x p90 (1820 s).
            "juniper-ml": 455,
            "juniper-data": 1100,
            "juniper-cascor": 1065,
            "juniper-canopy": 1371,
            "juniper-cascor-worker": 1122,
        }
        for repo, p90 in measured_p90.items():
            with self.subTest(repo=repo):
                budget = safe_merge.timeout_for(repo)
                self.assertGreater(budget, p90, f"{repo} would refuse healthy CI")
                self.assertLessEqual(budget, 4 * p90, f"{repo} budget is so loose a stuck run looks slow")
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


class AutoMergeNetDefectTest(SafeMergeTestBase):
    """D1-D4 from the kill-forensics doc section 4.

    NAMING, deliberately: this must NOT be called `AutoMergeNetTest` -- that name is already
    taken at line ~419 (the RC-4 arming/gating suite). A second class of the same name does
    not merge with the first, it REPLACES it in the module namespace, and unittest then
    discovers only the survivor. Six existing tests silently stopped running that way before
    mypy's `no-redef` caught it; the suite still reported OK, just with less in it.

    These four shipped together in ml#1183's RC-4 net and three of them are in the net
    itself. The ORDERING matters and is encoded here: D1 (arm on more paths) strictly
    INCREASES the number of refusals that would leave a live net, so the D3 disarm has to
    hold before D1 widens the exposure. A regression that reverts D3 while keeping D1 is
    worse than the original bug, so `test_refusal_disarms_the_net` is the load-bearing one.
    """

    def _arming(self, harness):
        return [c for c in harness.calls if c[:2] == ["pr", "merge"] and "--auto" in c]

    def _disarming(self, harness):
        return [c for c in harness.calls if "--disable-auto" in c]

    # ---- D3: a refusal must never leave a live net ------------------------
    def test_refusal_disarms_the_net(self):
        """Observed live on ml#1185: refused, then merged itself once checks passed."""
        h = Harness(
            [_state(mergeStateStatus="BLOCKED"), _state(mergeStateStatus="BLOCKED")],
            wait_result={"_exit": 1},
        )
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: True)
        with self.assertRaises(safe_merge.Refused):
            self.run_merge_installed(h)
        self.assertTrue(self._arming(h), "expected a net to be armed on BLOCKED")
        self.assertTrue(self._disarming(h), "a refusal MUST take the net back down")

    def test_refusal_that_cannot_disarm_says_so_loudly(self):
        """The one state where a refusal and a live net coexist must never be silent."""
        h = Harness(
            [_state(mergeStateStatus="BLOCKED"), _state(mergeStateStatus="BLOCKED")],
            wait_result={"_exit": 1},
        )
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: True)

        real_gh = h.gh

        def gh(args, timeout=120):
            if "--disable-auto" in list(args):
                raise safe_merge.HardError("boom")
            return real_gh(args, timeout=timeout)

        self.monkey(safe_merge, "_gh", gh)
        with self.assertRaises(safe_merge.Refused) as ctx:
            self.run_merge_installed(h)
        msg = str(ctx.exception)
        self.assertIn("could NOT be disarmed", msg)
        self.assertIn("still", msg.lower())

    def test_no_net_armed_means_no_disarm_call(self):
        h = Harness(
            [_state(mergeStateStatus="BLOCKED"), _state(mergeStateStatus="BLOCKED")],
            wait_result={"_exit": 1},
        )
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: False)
        with self.assertRaises(safe_merge.Refused):
            self.run_merge_installed(h)
        self.assertEqual(self._disarming(h), [])

    def test_armed_state_does_not_leak_between_invocations(self):
        """`_ARMED` is module-global so the signal handler can read it.

        That makes it survive across calls in one process. A stale entry would make
        `arm_auto_merge` short-circuit and report a net that was never armed for the NEW
        pr -- a silent loss of the guarantee. Found by cross-test contamination.
        """
        h1 = Harness(
            [_state(mergeStateStatus="BLOCKED"), _state(mergeStateStatus="BLOCKED")],
            wait_result={"_exit": 1},
        )
        h1.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: True)
        with self.assertRaises(safe_merge.Refused):
            self.run_merge_installed(h1)

        # Second invocation, net UNAVAILABLE. It must not inherit the first run's net.
        h2 = Harness(
            [_state(mergeStateStatus="BLOCKED"), _state(mergeStateStatus="BLOCKED")],
            wait_result={"_exit": 1},
        )
        h2.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: False)
        with self.assertRaises(safe_merge.Refused):
            self.run_merge_installed(h2)
        self.assertEqual(self._disarming(h2), [], "second run disarmed a net it never armed")
        self.assertIsNone(safe_merge._ARMED)

    # ---- D1: arm on the BEHIND -> UNKNOWN path ----------------------------
    def test_behind_path_arms_the_net_before_syncing(self):
        """The post-sync CI re-run is the longest, most kill-exposed wait there is.

        It was also the only one entered with no net: the BEHIND branch `continue`d past
        the arming site. This is the exact shape of the incident.
        """
        # NOTE the doubled first state: the preflight `pr_state` consumes one before the
        # cycle loop ever runs. A single BEHIND here makes the loop see CLEAN, and the test
        # passes without exercising the BEHIND path at all.
        h = Harness(
            [
                _state(mergeStateStatus="BEHIND"),
                _state(mergeStateStatus="BEHIND"),
                _state(),
                _state(),
            ],
        )
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: True)
        self.run_merge_installed(h)
        armed = self._arming(h)
        self.assertTrue(armed, "BEHIND must arm a net before the sync")
        sync = [i for i, c in enumerate(h.calls) if c[:1] == ["api"]]
        self.assertTrue(sync, "expected an update-branch call")
        first_arm = h.calls.index(armed[0])
        self.assertLess(first_arm, sync[0], "arm BEFORE the update-branch, not after")

    def test_unknown_state_arms_the_net(self):
        """GitHub reports UNKNOWN while recomputing -- routinely right after a sync."""
        h = Harness(
            [
                _state(mergeStateStatus="UNKNOWN"),
                _state(mergeStateStatus="UNKNOWN"),
                _state(),
                _state(),
            ],
        )
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: True)
        self.run_merge_installed(h)
        self.assertTrue(self._arming(h), "UNKNOWN was armable-but-unarmed (D1)")

    def test_clean_pr_is_never_armed(self):
        """On a green PR `--auto` merges on the spot, skipping the head pin. Keep it local."""
        h = Harness([_state(mergeStateStatus="CLEAN")])
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: True)
        self.run_merge_installed(h)
        self.assertEqual(self._arming(h), [])

    def test_arming_is_idempotent_across_cycles(self):
        """Genuinely crosses a BEHIND sync into a second cycle -- otherwise 'armed once' is
        trivially true because only one cycle ever ran."""
        h = Harness(
            [
                _state(mergeStateStatus="BEHIND"),  # consumed by preflight
                _state(mergeStateStatus="BEHIND"),  # cycle 1 -> arm + sync + continue
                _state(mergeStateStatus="BLOCKED"),  # cycle 2 -> arm again (no-op)
                _state(),
                _state(),
            ],
        )
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: True)
        self.run_merge_installed(h)
        self.assertTrue([c for c in h.calls if c[:1] == ["api"]], "expected the BEHIND sync to run")
        self.assertEqual(len(self._arming(h)), 1, "net must be armed once, not per cycle")

    def test_armable_states_cover_the_three_waiting_states(self):
        self.assertEqual(set(safe_merge.ARMABLE_STATES), {"BLOCKED", "BEHIND", "UNKNOWN"})

    def test_the_armed_net_pins_the_head_it_was_armed_on(self):
        """D4: arming must not be based on a head this run never read.

        Measured enable-time-only (probe ml#1225), so pinning is safe -- the net survives
        the base-sync that follows on the BEHIND path.
        """
        head = "c" * 40
        h = Harness([_state(mergeStateStatus="BLOCKED", headRefOid=head), _state(mergeStateStatus="BLOCKED", headRefOid=head), _state(headRefOid=head)])
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: True)
        self.run_merge_installed(h)
        armed = self._arming(h)
        self.assertTrue(armed, "expected a net")
        argv = armed[0]
        self.assertIn("--match-head-commit", argv)
        self.assertEqual(argv[argv.index("--match-head-commit") + 1], head)

    def test_behind_path_pins_the_pre_sync_head(self):
        """The BEHIND arm fires before update-branch, so it pins the pre-sync head.

        That is correct BECAUSE the pin is enable-time only: the sync moves the head
        moments later and the net survives it. If the pin were continuous this would be
        the bug that silently disarms every BEHIND merge.
        """
        head = "d" * 40
        h = Harness(
            [
                _state(mergeStateStatus="BEHIND", headRefOid=head),
                _state(mergeStateStatus="BEHIND", headRefOid=head),
                _state(),
                _state(),
            ]
        )
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: True)
        self.run_merge_installed(h)
        armed = self._arming(h)
        self.assertTrue(armed)
        argv = armed[0]
        self.assertEqual(argv[argv.index("--match-head-commit") + 1], head)

    # ---- D2: UNKNOWN at the merge gate is not a verdict -------------------
    def test_unknown_at_the_gate_repolls_instead_of_refusing(self):
        """A spurious refusal here reads exactly like a real blocker, and did."""
        # The UNKNOWN must land on the POST-wait read (`after`), which is where the gate
        # lives. Sequence: preflight, cycle-1 state, then `after` -> UNKNOWN -> re-poll.
        seq = [
            _state(mergeStateStatus="BLOCKED"),  # preflight
            _state(mergeStateStatus="BLOCKED"),  # cycle 1 state
            _state(mergeStateStatus="UNKNOWN"),  # `after` -- the gate
            _state(mergeStateStatus="CLEAN"),  # re-poll resolves
        ]
        h = Harness(seq)
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: False)
        self.monkey(safe_merge.time, "sleep", lambda s: None)
        out = self.run_merge_installed(h)
        self.assertIn("MERGED", out)

    def test_unknown_stuck_at_the_gate_eventually_refuses(self):
        h = Harness(
            [
                _state(mergeStateStatus="BLOCKED"),
                _state(mergeStateStatus="BLOCKED"),
                _state(mergeStateStatus="UNKNOWN"),
            ],
        )
        h.install(self)
        self.monkey(safe_merge, "repo_allows_auto_merge", lambda o, r: False)
        self.monkey(safe_merge.time, "sleep", lambda s: None)
        with self.assertRaises(safe_merge.Refused) as ctx:
            self.run_merge_installed(h)
        self.assertIn("UNKNOWN", str(ctx.exception))

    def test_mergeability_repoll_is_bounded(self):
        self.assertGreaterEqual(safe_merge.MERGEABILITY_POLLS, 1)
        self.assertLessEqual(safe_merge.MERGEABILITY_POLLS * safe_merge.MERGEABILITY_INTERVAL, 120)


class NetGuaranteeDocTest(unittest.TestCase):
    """D4: the net's guarantee differs from the local path's. Say exactly how.

    This class previously asserted the net was NOT pinned at all, which was true of the
    code and is no longer. The complaint D4 records was never "the trade is wrong" -- it was
    that the trade was made SILENTLY. So these assertions keep the *current* trade stated,
    and are updated with it rather than being deleted.
    """

    def test_docstring_states_the_net_is_pinned_at_ARMING_time_only(self):
        doc = safe_merge.__doc__
        self.assertIn("--match-head-commit", doc)
        self.assertIn("expectedHeadOid", doc)
        # the enable-time-vs-continuous distinction is the whole finding
        self.assertRegex(doc, r"enable-time|ARMING time")
        self.assertRegex(doc, r"does \*\*not\*\* keep pinning|not .*continuous")

    def test_docstring_cites_the_measurement_not_an_assumption(self):
        """A guess here is silent and total, so the docstring must show its evidence.

        The wrong answer -- assuming the pin is continuous -- would have meant NOT pinning,
        leaving the stale-read hole open forever on reasoning nobody ever checked.
        """
        doc = safe_merge.__doc__
        self.assertRegex(doc, r"measured|probe ml#1225")

    def test_arm_auto_merge_accepts_and_forwards_a_head_pin(self):
        """Structural: the parameter exists and reaches the gh argv."""
        import inspect

        sig = inspect.signature(safe_merge.arm_auto_merge)
        self.assertIn("head", sig.parameters)
        self.assertEqual(sig.parameters["head"].default, "")
        src = inspect.getsource(safe_merge.arm_auto_merge)
        self.assertIn("--match-head-commit", src)

    def test_docstring_states_refusal_disarms(self):
        self.assertIn("--disable-auto", safe_merge.__doc__)

    def test_interrupt_path_is_documented_as_leaving_the_net_up(self):
        """Exit 4 deliberately does NOT disarm -- surviving the kill is the whole point."""
        doc = safe_merge.__doc__
        self.assertIn("INTERRUPTED", doc)
        self.assertIn("left up", doc.lower())


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


class TimeoutSizingTest(unittest.TestCase):
    """The CI budget is per-repo because fleet CI spans differ by ~6x.

    Measured 2026-08-20 (all required contexts on one head, not one workflow):
    ml max 273 s, data 1196 s, cascor 1547 s, canopy 1719 s. The prior single 900 s sat at
    canopy's MEDIAN, so about half of canopy's merges would have refused with "checks did
    not finish" while the checks were healthy.

    ml RE-MEASURED 2026-09-05, n=12: p90 455 s, **max 823 s** -- 3.0x the August max, on a
    repo then carrying 103 open PRs. The pin below moves with it. Leaving the stale 273
    would have made this assertion VACUOUS for ml: any budget over 273 passes, including
    the 900 s that refused a healthy ml#1754 in production.
    """

    def test_every_repo_budget_clears_its_measured_max(self):
        """cascor-client is deliberately absent: its max (15,616 s) is a QUEUED check, not
        CI working, and a budget that absorbed it could no longer tell stuck from slow."""
        measured_max = {
            "juniper-ml": 823,  # re-measured 2026-09-05 (was 273 on 2026-08-20)
            "juniper-data": 1196,
            "juniper-cascor": 1547,
            "juniper-cascor-worker": 1717,
            "juniper-canopy": 1719,
        }
        for repo, observed in measured_max.items():
            with self.subTest(repo=repo):
                self.assertGreater(
                    safe_merge.timeout_for(repo),
                    observed,
                    f"{repo} budget is below its own observed worst case",
                )

    def test_unmeasured_repo_falls_back_to_the_standard_tier(self):
        self.assertEqual(safe_merge.timeout_for("juniper-nonesuch"), safe_merge.DEFAULT_TIMEOUT)
        self.assertGreater(safe_merge.DEFAULT_TIMEOUT, 1196)

    def test_ceiling_is_actually_ENFORCED_not_merely_declared(self):
        """`TIMEOUT_CEILING` was a dead constant: defined, asserted against, never used.

        The other tests in this class check the TABLE's values, which is exactly the shape
        of assertion that passes while the runtime guarantee does not exist -- an explicit
        `--timeout 7200` went through unclamped. Test the code path, not the data.
        """
        msgs = []
        self.assertEqual(safe_merge.clamp_timeout(7200, log=msgs.append), safe_merge.TIMEOUT_CEILING)
        self.assertTrue(msgs, "clamping must be announced, not silent")
        self.assertIn("clamping", " ".join(msgs))
        # under the ceiling passes through untouched and says nothing
        quiet = []
        self.assertEqual(safe_merge.clamp_timeout(900, log=quiet.append), 900)
        self.assertEqual(quiet, [])

    def test_no_budget_exceeds_the_worker_lease_ceiling(self):
        """A local wait cannot outlive the process doing it.

        Kill forensics section 3.4: `[bg]` spare workers hold a ~3600 s lease and a task
        cannot outlive its host worker, so a budget above that is unreachable for any
        background-run invocation. Past the ceiling the armed net is the answer, not a
        longer wait.
        """
        self.assertLessEqual(safe_merge.TIMEOUT_CEILING, 3600)
        for repo, budget in safe_merge.REPO_TIMEOUTS.items():
            with self.subTest(repo=repo):
                self.assertLessEqual(budget, safe_merge.TIMEOUT_CEILING)
        self.assertLessEqual(safe_merge.DEFAULT_TIMEOUT, safe_merge.TIMEOUT_CEILING)

    def test_omitted_timeout_resolves_per_repo_not_to_a_constant(self):
        self.assertNotEqual(
            safe_merge.timeout_for("juniper-ml"),
            safe_merge.timeout_for("juniper-canopy"),
            "a single fleet-wide budget is the bug this table replaces",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
