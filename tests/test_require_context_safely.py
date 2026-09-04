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
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
