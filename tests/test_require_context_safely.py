#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/ad-hoc/2026-08-20_require_context_safely.py`` -- the ruleset writer that
promotes a status-check context to REQUIRED.

``util/`` is outside every pre-commit Python hook's scope, so this suite is the gate.
Hermetic: ``gh_json`` is monkeypatched; nothing here talks to GitHub.

What it pins, and why it mattered:

- ``find_ruleset`` must report a FAILED per-ruleset read as an error, never as an absence.
  It used to ``continue`` past a non-2xx, so a rate limit or a network blip printed
  "no ruleset carries required_status_checks" while the ruleset was intact -- seen twice in
  ten minutes during the 2026-08-27 promotion (cascor-client on the dry-run, juniper-data on
  the post-apply ``--status``). On the write path that only skipped the repo (rc 1), but on
  ``--status`` it is a false census, the same fail-into-plausible class as ml#1403.
- Genuine absence and genuine ambiguity are still reported as such -- the negative controls,
  so the fix cannot have turned every outcome into an error.
- ``--amend-integration-id`` refuses an app that has not published the exact name (57789
  onto ``Memory Budget``), mutates only that one context, and keeps the post-write drift
  assertion live for every OTHER context. Helper coverage of ``observed_context_apps`` does
  not pin any of those write-path properties.
"""

from __future__ import annotations

import copy
import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-08-20_require_context_safely.py"


def _load():
    spec = importlib.util.spec_from_file_location("require_context_safely", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()

_LIST = [{"id": 1, "name": "juniper-x-rules"}, {"id": 2, "name": "juniper-no-direct-push"}]
_CHECKS = {"id": 1, "name": "juniper-x-rules", "rules": [{"type": "required_status_checks", "parameters": {"required_status_checks": []}}]}
_NO_CHECKS = {"id": 2, "name": "juniper-no-direct-push", "rules": [{"type": "pull_request"}]}


def _fake(responses: dict):
    """A gh_json stand-in: path -> (data, err). Anything unlisted is an error."""

    def gh_json(path, method=None, body=None):
        return responses.get(path, (None, f"unexpected call {path}"))

    return gh_json


class FindRulesetTest(unittest.TestCase):
    def setUp(self):
        self._orig = mod.gh_json

    def tearDown(self):
        mod.gh_json = self._orig

    def test_failed_ruleset_read_is_an_error_not_an_absence(self):
        mod.gh_json = _fake(
            {
                "repos/o/r/rulesets": (_LIST, None),
                "repos/o/r/rulesets/1": (None, "HTTP 403: API rate limit exceeded"),
                "repos/o/r/rulesets/2": (_NO_CHECKS, None),
            }
        )
        rs, err = mod.find_ruleset("o", "r")
        self.assertIsNone(rs)
        self.assertIn("cannot read ruleset 1", err)
        self.assertIn("rate limit", err)
        self.assertNotIn("no ruleset carries", err)

    def test_intact_ruleset_is_found_by_content(self):
        mod.gh_json = _fake(
            {
                "repos/o/r/rulesets": (_LIST, None),
                "repos/o/r/rulesets/1": (_CHECKS, None),
                "repos/o/r/rulesets/2": (_NO_CHECKS, None),
            }
        )
        rs, err = mod.find_ruleset("o", "r")
        self.assertIsNone(err)
        self.assertEqual(rs["id"], 1)

    def test_genuine_absence_is_still_reported_as_absence(self):
        mod.gh_json = _fake(
            {
                "repos/o/r/rulesets": ([_LIST[1]], None),
                "repos/o/r/rulesets/2": (_NO_CHECKS, None),
            }
        )
        rs, err = mod.find_ruleset("o", "r")
        self.assertIsNone(rs)
        self.assertEqual(err, "no ruleset carries required_status_checks")

    def test_two_carrying_rulesets_are_ambiguous(self):
        second = dict(_CHECKS, id=2, name="juniper-y-rules")
        mod.gh_json = _fake(
            {
                "repos/o/r/rulesets": (_LIST, None),
                "repos/o/r/rulesets/1": (_CHECKS, None),
                "repos/o/r/rulesets/2": (second, None),
            }
        )
        rs, err = mod.find_ruleset("o", "r")
        self.assertIsNone(rs)
        self.assertIn("AMBIGUOUS", err)

    def test_failed_listing_is_an_error(self):
        mod.gh_json = _fake({"repos/o/r/rulesets": (None, "HTTP 502")})
        rs, err = mod.find_ruleset("o", "r")
        self.assertIsNone(rs)
        self.assertIn("cannot list rulesets", err)


CENSUS = REPO_ROOT / "util" / "ad-hoc" / "2026-08-26_p5_fleet_state.py"


def _census_roster() -> set[str]:
    spec = importlib.util.spec_from_file_location("p5_fleet_state", CENSUS)
    mod_c = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod_c)
    return {row[0] for row in mod_c.ROSTER}


class TargetRosterTest(unittest.TestCase):
    """`TARGETS` is the default roster for BOTH `--status` and a no-`--repo` `--apply`.

    An omission here is silent and reads as a complete census: `--status` prints a banner
    per repo it knows about and says nothing about one it does not, so 8 of 9 governed repos
    looks exactly like all of them. That is the fail-into-plausible class of ml#1403 (census
    columns) and ml#1429 (`find_ruleset` reporting a failed read as an absence) -- the third
    instance in the same tool family, and the reason these two rosters are pinned to each
    other rather than to a hand-written literal that would drift the same way.
    """

    def test_targets_matches_the_census_roster(self):
        self.assertEqual(set(mod.TARGETS), _census_roster())

    def test_recurrence_is_present(self):
        # The specific omission, from the P5 port through the 2026-08-27 promotion until
        # 2026-08-29: recurrence carries `Memory Budget` as a required check like the other
        # eight, but no no-`--repo` run ever looked at it.
        self.assertIn("juniper-recurrence", mod.TARGETS)

    def test_no_duplicates(self):
        self.assertEqual(len(mod.TARGETS), len(set(mod.TARGETS)))


class ObservedContextAppsTest(unittest.TestCase):
    """The amend path's pre-flight: WHICH app publishes this exact context name.

    ``observed_contexts`` answers "does anything publish this name", which is the right
    question for ADDING a context. Amending an ``integration_id`` asks a harder one -- "is
    THIS app the publisher" -- and a wrong answer reproduces the outage the module docstring
    records: a context pinned to an app that never reports it is never satisfied, so the PR
    sits BLOCKED with nothing red.
    """

    def setUp(self):
        self._orig = mod.gh_json

    def tearDown(self):
        mod.gh_json = self._orig

    @staticmethod
    def _runs(*pairs):
        return {"check_runs": [{"name": n, "app": {"id": i, "slug": s}} for n, i, s in pairs]}

    def test_returns_the_publishing_app_from_pr_heads(self):
        mod.gh_json = _fake(
            {
                "repos/o/r/pulls?state=all&sort=updated&direction=desc&per_page=8": (
                    [{"head": {"sha": "abc"}}],
                    None,
                ),
                "repos/o/r/commits/abc/check-runs?per_page=100": (
                    self._runs(("Memory Budget", 15368, "github-actions"), ("Other", 99, "x")),
                    None,
                ),
            }
        )
        self.assertEqual(mod.observed_context_apps("o", "r", "Memory Budget"), {15368: "github-actions"})

    def test_falls_back_to_main_when_pr_heads_show_nothing(self):
        """A job that only reports on ``main`` must not be mistaken for unpublished."""
        mod.gh_json = _fake(
            {
                "repos/o/r/pulls?state=all&sort=updated&direction=desc&per_page=8": (
                    [{"head": {"sha": "abc"}}],
                    None,
                ),
                "repos/o/r/commits/abc/check-runs?per_page=100": (self._runs(), None),
                "repos/o/r/commits/main/check-runs?per_page=100": (
                    self._runs(("Memory Budget", 15368, "github-actions")),
                    None,
                ),
            }
        )
        self.assertEqual(mod.observed_context_apps("o", "r", "Memory Budget"), {15368: "github-actions"})

    def test_a_different_context_name_does_not_count_as_a_publisher(self):
        """NEGATIVE CONTROL. The name match must be exact.

        If a near-miss counted, the refusal that protects the amend would pass on any repo
        with a similarly-named check -- and that refusal is the whole guard.
        """
        mod.gh_json = _fake(
            {
                "repos/o/r/pulls?state=all&sort=updated&direction=desc&per_page=8": (
                    [{"head": {"sha": "abc"}}],
                    None,
                ),
                "repos/o/r/commits/abc/check-runs?per_page=100": (
                    self._runs(("Memory Budget (Python 3.12)", 15368, "github-actions")),
                    None,
                ),
                "repos/o/r/commits/main/check-runs?per_page=100": (self._runs(), None),
            }
        )
        self.assertEqual(mod.observed_context_apps("o", "r", "Memory Budget"), {})

    def test_bandit_app_is_not_a_publisher_of_memory_budget(self):
        """NEGATIVE CONTROL for the concrete incident.

        57789 is the ``Bandit`` app id the module docstring names as the one that, hardcoded
        onto the wrong context, left five repos' ``main`` unmergeable. Pinning ``Memory
        Budget`` to it must NOT be reported as observed.
        """
        mod.gh_json = _fake(
            {
                "repos/o/r/pulls?state=all&sort=updated&direction=desc&per_page=8": (
                    [{"head": {"sha": "abc"}}],
                    None,
                ),
                "repos/o/r/commits/abc/check-runs?per_page=100": (
                    self._runs(("Memory Budget", 15368, "github-actions")),
                    None,
                ),
            }
        )
        publishers = mod.observed_context_apps("o", "r", "Memory Budget")
        self.assertIn(15368, publishers)
        self.assertNotIn(57789, publishers)

    def test_does_not_consult_main_when_pr_heads_already_published(self):
        """PR heads already answered. Merging main's set would let 57789 sneak in.

        The fallback exists so a main-only job is not mistaken for unpublished. It is
        NOT a union: a hit on a PR head must not pick up a different app that only
        appears on ``main``.
        """
        mod.gh_json = _fake(
            {
                "repos/o/r/pulls?state=all&sort=updated&direction=desc&per_page=8": (
                    [{"head": {"sha": "abc"}}],
                    None,
                ),
                "repos/o/r/commits/abc/check-runs?per_page=100": (
                    self._runs(("Memory Budget", 15368, "github-actions")),
                    None,
                ),
                "repos/o/r/commits/main/check-runs?per_page=100": (
                    self._runs(("Memory Budget", 57789, "bandit")),
                    None,
                ),
            }
        )
        publishers = mod.observed_context_apps("o", "r", "Memory Budget")
        self.assertEqual(publishers, {15368: "github-actions"})
        self.assertNotIn(57789, publishers)


# Contexts for the amend-path fixture: Memory Budget unpinned, Bandit on its real app,
# and an Actions-pinned neighbour. Rewriting Bandit to 15368 is the five-repo outage.
_AMEND_CONTEXTS = [
    {"context": "Memory Budget", "integration_id": None},
    {"context": "Bandit", "integration_id": 57789},
    {"context": "Guard PR base branch", "integration_id": 15368},
]


def _amend_ruleset(contexts):
    return {
        "id": 1,
        "name": "juniper-x-rules",
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "bypass_actors": [{"actor_id": None, "actor_type": "DeployKey", "bypass_mode": "always"}],
        "rules": [
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": copy.deepcopy(contexts),
                },
            },
            {"type": "pull_request", "parameters": {}},
            {"type": "code_quality"},
        ],
    }


def _contexts_of_payload(body):
    for rule in body.get("rules", []):
        if rule.get("type") == "required_status_checks":
            return (rule.get("parameters") or {}).get("required_status_checks", [])
    return []


class _AmendGH:
    """Stateful ``gh_json``: one ruleset, recorded PUTs, optional post-write override.

    ``after_contexts`` is the lie the post-write re-read returns -- used to pin the
    verification assertions that must still fire DURING an amend. A successful apply
    with ``after_contexts is None`` adopts the PUT body so the happy path verifies.
    """

    def __init__(self, contexts, pr_runs, after_contexts=None):
        self.rs = _amend_ruleset(contexts)
        self.pr_runs = pr_runs
        self.after_contexts = after_contexts
        self.puts: list[dict] = []

    def __call__(self, path, method=None, body=None):
        if method == "PUT":
            self.puts.append(copy.deepcopy(body))
            if self.after_contexts is not None:
                self.rs = _amend_ruleset(self.after_contexts)
            else:
                self.rs = copy.deepcopy(self.rs)
                self.rs["rules"] = copy.deepcopy(body["rules"])
                for key in ("name", "target", "enforcement", "conditions", "bypass_actors"):
                    if key in body:
                        self.rs[key] = copy.deepcopy(body[key])
            return {"id": 1}, None
        if path == "repos/o/r/rulesets":
            return ([{"id": 1, "name": "juniper-x-rules"}], None)
        if path == "repos/o/r/rulesets/1":
            return (copy.deepcopy(self.rs), None)
        if path.startswith("repos/o/r/pulls?"):
            return ([{"head": {"sha": "abc"}}], None)
        if "commits/abc/check-runs" in path:
            return (self.pr_runs, None)
        if "commits/main/check-runs" in path:
            return ({"check_runs": []}, None)
        return (None, f"unexpected call {path}")


class AmendPathTest(unittest.TestCase):
    """The write path ``--amend-integration-id`` actually takes. Helper tests are not enough.

    ``observed_context_apps`` answering correctly does not prove ``main()`` refuses a wrong
    id, leaves ``Bandit``'s 57789 alone, or keeps the drift assertion live for the other
    16 contexts. Those are the operations that unmerged five repos, and they had no test.
    """

    def setUp(self):
        self._orig_gh = mod.gh_json
        self._orig_snap = mod.SNAP_DIR
        self._tmp = TemporaryDirectory()
        mod.SNAP_DIR = Path(self._tmp.name)

    def tearDown(self):
        mod.gh_json = self._orig_gh
        mod.SNAP_DIR = self._orig_snap
        self._tmp.cleanup()

    def _install(self, gh):
        mod.gh_json = gh

    def _run(self, *argv: str) -> tuple[int, str]:
        buf = io.StringIO()
        old = sys.argv
        sys.argv = ["require_context_safely.py", *argv]
        try:
            with redirect_stdout(buf):
                rc = mod.main()
        finally:
            sys.argv = old
        return rc, buf.getvalue()

    @staticmethod
    def _actions_published():
        return ObservedContextAppsTest._runs(("Memory Budget", 15368, "github-actions"))

    def test_already_required_without_amend_flag_is_a_noop(self):
        """Default path must still short-circuit. The amend branch is opt-in."""
        gh = _AmendGH(_AMEND_CONTEXTS, self._actions_published())
        self._install(gh)
        rc, out = self._run("--owner", "o", "--repo", "r", "--context", "Memory Budget")
        self.assertEqual(rc, 0)
        self.assertIn("ALREADY REQUIRED", out)
        self.assertEqual(gh.puts, [])
        self.assertEqual(list(mod.SNAP_DIR.iterdir()), [])

    def test_unobserved_publisher_is_refused_and_does_not_put(self):
        """NEGATIVE CONTROL for the write path, not just the helper.

        57789 has never published ``Memory Budget``. Pinning it is the five-repo outage:
        the PR sits BLOCKED with nothing red. A dry-run must still refuse, and must not
        snapshot or PUT.
        """
        gh = _AmendGH(_AMEND_CONTEXTS, self._actions_published())
        self._install(gh)
        rc, out = self._run(
            "--owner", "o", "--repo", "r",
            "--context", "Memory Budget",
            "--amend-integration-id",
            "--integration-id", "57789",
        )
        self.assertEqual(rc, 1)
        self.assertIn("REFUSING", out)
        self.assertIn("57789", out)
        self.assertNotIn("would amend", out)
        self.assertEqual(gh.puts, [])
        self.assertEqual(list(mod.SNAP_DIR.iterdir()), [])

    def test_observed_publisher_dry_run_would_amend_without_writing(self):
        gh = _AmendGH(_AMEND_CONTEXTS, self._actions_published())
        self._install(gh)
        rc, out = self._run(
            "--owner", "o", "--repo", "r",
            "--context", "Memory Budget",
            "--amend-integration-id",
        )
        self.assertEqual(rc, 0)
        self.assertIn("would amend", out)
        self.assertIn("3 contexts, unchanged", out)
        self.assertEqual(gh.puts, [])
        self.assertEqual(list(mod.SNAP_DIR.iterdir()), [])

    def test_apply_amends_only_the_named_context(self):
        """Invariant 2: every OTHER context keeps its own integration_id.

        The PUT that retargeted ``Bandit`` at 15368 is the defect. The amend must rewrite
        ``Memory Budget`` in place and leave 57789 on ``Bandit``.
        """
        gh = _AmendGH(_AMEND_CONTEXTS, self._actions_published())
        self._install(gh)
        rc, out = self._run(
            "--owner", "o", "--repo", "r",
            "--context", "Memory Budget",
            "--amend-integration-id",
            "--apply",
        )
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(gh.puts), 1)
        pairs = {c["context"]: c.get("integration_id") for c in _contexts_of_payload(gh.puts[0])}
        self.assertEqual(pairs["Memory Budget"], 15368)
        self.assertEqual(pairs["Bandit"], 57789)
        self.assertEqual(pairs["Guard PR base branch"], 15368)
        self.assertEqual(len(pairs), 3)
        self.assertIn("all invariants held", out)
        self.assertTrue(any(mod.SNAP_DIR.iterdir()), "apply must snapshot before the PUT")

    def test_post_write_other_context_drift_still_fails_during_an_amend(self):
        """The drift check is narrowed, not disabled. Bandit moving is still a failure.

        Switching the assertion off for the one operation that rewrites ids would be
        worse than no check -- that is how a whitelist of exactly one (context, new_id)
        pair was chosen over a skip.
        """
        drifted = [
            {"context": "Memory Budget", "integration_id": 15368},
            {"context": "Bandit", "integration_id": 15368},
            {"context": "Guard PR base branch", "integration_id": 15368},
        ]
        gh = _AmendGH(_AMEND_CONTEXTS, self._actions_published(), after_contexts=drifted)
        self._install(gh)
        rc, out = self._run(
            "--owner", "o", "--repo", "r",
            "--context", "Memory Budget",
            "--amend-integration-id",
            "--apply",
        )
        self.assertEqual(rc, 1)
        self.assertIn("POST-WRITE VERIFICATION FAILED", out)
        self.assertIn("integration_id DRIFT on Bandit", out)
        self.assertIn("57789", out)

    def test_post_write_amend_did_not_take_fails(self):
        still_none = copy.deepcopy(_AMEND_CONTEXTS)
        gh = _AmendGH(_AMEND_CONTEXTS, self._actions_published(), after_contexts=still_none)
        self._install(gh)
        rc, out = self._run(
            "--owner", "o", "--repo", "r",
            "--context", "Memory Budget",
            "--amend-integration-id",
            "--apply",
        )
        self.assertEqual(rc, 1)
        self.assertIn("amend DID NOT TAKE", out)

    def test_post_write_context_count_change_fails(self):
        extra = copy.deepcopy(_AMEND_CONTEXTS)
        extra[0] = {"context": "Memory Budget", "integration_id": 15368}
        extra.append({"context": "sneaky extra", "integration_id": 15368})
        gh = _AmendGH(_AMEND_CONTEXTS, self._actions_published(), after_contexts=extra)
        self._install(gh)
        rc, out = self._run(
            "--owner", "o", "--repo", "r",
            "--context", "Memory Budget",
            "--amend-integration-id",
            "--apply",
        )
        self.assertEqual(rc, 1)
        self.assertIn("context COUNT changed during an amend", out)


if __name__ == "__main__":
    unittest.main()
