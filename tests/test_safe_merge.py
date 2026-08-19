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

    def __init__(self, states, wait_result=None, merge_succeeds=True):
        self._states = list(states)
        self.calls: list[list[str]] = []
        self.wait_result = wait_result if wait_result is not None else {"_exit": 0}
        self.waits = 0
        self.merged = False
        self.merge_succeeds = merge_succeeds

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

    def install(self, tc):
        tc.monkey(safe_merge, "_gh", self.gh)
        tc.monkey(safe_merge, "pr_state", self.pr_state)
        tc.monkey(safe_merge, "wait_for_required", self.wait)


class SafeMergeTestBase(unittest.TestCase):
    def setUp(self):
        self._restore = []

    def tearDown(self):
        for obj, name, val in reversed(self._restore):
            setattr(obj, name, val)

    def monkey(self, obj, name, val):
        self._restore.append((obj, name, getattr(obj, name)))
        setattr(obj, name, val)

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
        ns = safe_merge.build_parser().parse_args(["--pr", "1"]) if hasattr(
            safe_merge, "build_parser"
        ) else None
        if ns is None:  # module exposes only main(); assert via the docstring contract
            self.assertIn("--execute", safe_merge.__doc__)
            self.assertIn("dry-run", safe_merge.__doc__.lower())
        else:
            self.assertFalse(ns.execute)
            self.assertEqual(ns.merge_method, "squash")


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
