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


if __name__ == "__main__":
    unittest.main()
