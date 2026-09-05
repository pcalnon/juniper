#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/ad-hoc/2026-08-10_ruleset_context_audit.py`` -- the fleet auditor
that classifies required-status-check contexts as BLOCKING / MATCHED / TIER-1 /
PATH-GATED / ADVISORY.

``util/`` is outside every pre-commit Python hook's scope, so this suite is the gate.
Hermetic: ``_gh``, ``required_contexts`` and ``per_pr_checks`` are replaced; nothing
talks to GitHub.

What it pins, and why it mattered:

- ``is_advisory`` is exact-name or prefix, not a substring. A fleet-union of 30
  contexts (2026-08-10) made every repo's ``main`` unmergeable except by admin
  bypass -- the opposite of the headless-merge goal. Requiring an advisory or
  path-gated name is that class.
- ``advisory_predicate(required)`` subtracts whatever the repo already requires.
  Promoting ``Sequence Safety`` (ml#1011) left the name in ``ADVISORY_EXACT``;
  without the predicate the now-required context vanished from Tier-1 and looked
  missing when it was fine.
- ``per_pr_checks`` drops anomalous rollups below half the median size
  (juniper-ml#1061 merged carrying 5 of ~37). Keeping them makes EVERY context
  look path-gated and collapses Tier 1 to nothing. Genuine dependabot-vs-code
  variation (~22 vs ~37) is preserved, because those PRs must stay mergeable.
- ``audit``: required-but-never-reported is BLOCKING; always-reported non-advisory
  is TIER-1; sometimes-reported non-advisory is PATH-GATED (do not require);
  advisory names never enter Tier-1 / path-gated.
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-08-10_ruleset_context_audit.py"


def _load():
    spec = importlib.util.spec_from_file_location("ruleset_context_audit", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()

ALWAYS = {"Guard PR base branch", "Analyze (python)", "tests"}
# Dependabot ~22 vs code ~37, scaled: 4 vs 8. Half-median keeps 4; a median
# cutoff would drop it and hide the "docs/dependabot must stay mergeable" signal.
DEPBOT = ALWAYS | {"Dependabot"}
CODE = ALWAYS | {
    "CI -- juniper-doc-tools",
    "CI -- juniper-ci-tools",
    "CI -- juniper-observability",
    "Memory Budget",
}
THIN = {"Guard PR base branch"}  # the #1061 5-of-~37 class, scaled down
ADVISORY = "Cursor Automation: Missing test coverage"
SEQ = "Sequence Safety"


class AdvisoryClassificationTest(unittest.TestCase):
    def test_exact_advisory_names_are_advisory(self) -> None:
        for name in ("claude", "CodeQL", "Fleet PR Lint", "Sequence Safety", "Sequence Safety (Advisory)"):
            self.assertTrue(mod.is_advisory(name), name)

    def test_cursor_automation_prefix_is_advisory(self) -> None:
        self.assertTrue(mod.is_advisory("Cursor Automation: Missing test coverage"))

    def test_prefix_is_not_a_substring_match(self) -> None:
        """``in`` would fire on a wrapped label; only ``startswith`` is the contract."""
        self.assertFalse(mod.is_advisory("note: Cursor Automation: sidecar"))
        self.assertFalse(mod.is_advisory("Cursor Automation"))  # no trailing colon

    def test_real_gates_are_not_advisory(self) -> None:
        for name in ("Guard PR base branch", "Analyze (python)", "tests", "Quality Gate"):
            self.assertFalse(mod.is_advisory(name), name)

    def test_promoted_advisory_is_not_advisory_for_that_repo(self) -> None:
        """ml#1011 class: Sequence Safety is required, so it must stay visible as Tier-1."""
        pred = mod.advisory_predicate({SEQ, "tests"})
        self.assertFalse(pred(SEQ))
        self.assertTrue(pred("claude"))
        self.assertTrue(pred("Cursor Automation: x"))

    def test_unpromoted_advisory_stays_advisory(self) -> None:
        pred = mod.advisory_predicate({"tests"})
        self.assertTrue(pred(SEQ))


class PerPrChecksFilterTest(unittest.TestCase):
    def setUp(self) -> None:
        self._orig = mod._gh

    def tearDown(self) -> None:
        mod._gh = self._orig

    def _feed(self, groups: list[list[str]]) -> list[set[str]]:
        payload = json.dumps(groups)

        def _gh(args: list[str]) -> str:
            self.assertIn("pr", args)
            return payload

        mod._gh = _gh
        return mod.per_pr_checks("juniper-ml")

    def test_anomalous_thin_rollup_is_dropped(self) -> None:
        """#1061: a 5-check rollup next to full ones must not collapse Tier 1."""
        kept = self._feed([list(THIN), list(CODE), list(CODE), list(CODE)])
        self.assertEqual(len(kept), 3)
        self.assertTrue(all(CODE <= g for g in kept))

    def test_dependabot_vs_code_variation_is_kept(self) -> None:
        """Half-median, not median: 22-vs-37 must survive or docs/dependabot PRs vanish."""
        kept = self._feed([list(DEPBOT), list(CODE), list(CODE), list(CODE)])
        self.assertEqual(len(kept), 4)

    def test_empty_or_null_rollup_is_not_a_group(self) -> None:
        self.assertEqual(self._feed([]), [])

        def _gh_empty(args: list[str]) -> str:
            return ""

        mod._gh = _gh_empty
        self.assertEqual(mod.per_pr_checks("juniper-ml"), [])


class RequiredContextsParseTest(unittest.TestCase):
    def setUp(self) -> None:
        self._orig = mod._gh

    def tearDown(self) -> None:
        mod._gh = self._orig

    def test_empty_gh_stdout_is_an_empty_set_not_json_error(self) -> None:
        mod._gh = lambda args: "  \n"
        self.assertEqual(mod.required_contexts("juniper-ml"), set())

    def test_json_array_becomes_a_set(self) -> None:
        mod._gh = lambda args: json.dumps(["tests", "tests", "Analyze (python)"])
        self.assertEqual(mod.required_contexts("juniper-ml"), {"tests", "Analyze (python)"})


class AuditClassificationTest(unittest.TestCase):
    def setUp(self) -> None:
        self._req = mod.required_contexts
        self._prs = mod.per_pr_checks

    def tearDown(self) -> None:
        mod.required_contexts = self._req
        mod.per_pr_checks = self._prs

    def _audit(self, required: set[str], groups: list[set[str]]) -> dict:
        mod.required_contexts = lambda repo: required
        mod.per_pr_checks = lambda repo: groups
        return mod.audit("juniper-ml")

    def test_required_never_reported_is_blocking(self) -> None:
        report = self._audit({"Ghost Check", "tests"}, [ALWAYS, ALWAYS])
        self.assertEqual(report["blocking"], ["Ghost Check"])
        self.assertIn("tests", report["matched"])
        self.assertNotIn("Ghost Check", report["matched"])

    def test_always_reported_non_advisory_is_tier1(self) -> None:
        report = self._audit({"tests"}, [ALWAYS | {ADVISORY}, ALWAYS | {ADVISORY}])
        self.assertEqual(report["blocking"], [])
        self.assertIn("tests", report["tier1"])
        self.assertIn("Guard PR base branch", report["tier1"])
        self.assertNotIn(ADVISORY, report["tier1"])
        self.assertEqual(report["advisory_seen"], [ADVISORY])

    def test_sometimes_reported_non_advisory_is_path_gated(self) -> None:
        """Requiring a path-gated job blocks every PR that does not touch its paths."""
        a = ALWAYS
        b = ALWAYS | {"CI -- juniper-doc-tools"}
        report = self._audit({"tests"}, [a, b])
        self.assertEqual(report["path_gated"], ["CI -- juniper-doc-tools [1/2]"])
        self.assertNotIn("CI -- juniper-doc-tools", report["tier1"])
        self.assertIn("tests", report["tier1"])

    def test_promoted_sequence_safety_stays_in_tier1(self) -> None:
        groups = [ALWAYS | {SEQ}, ALWAYS | {SEQ}]
        vanished = self._audit(set(), groups)
        self.assertNotIn(SEQ, vanished["tier1"])
        self.assertIn(SEQ, vanished["advisory_seen"])

        promoted = self._audit({SEQ}, groups)
        self.assertIn(SEQ, promoted["tier1"])
        self.assertNotIn(SEQ, promoted["advisory_seen"])
        self.assertEqual(promoted["matched"], [SEQ])

    def test_required_path_gated_is_matched_and_flagged(self) -> None:
        """Already-required + only-sometimes-reported: matched AND path-gated."""
        a = ALWAYS
        b = ALWAYS | {"CI -- juniper-doc-tools"}
        report = self._audit({"CI -- juniper-doc-tools"}, [a, b])
        self.assertEqual(report["matched"], ["CI -- juniper-doc-tools"])
        self.assertEqual(report["path_gated"], ["CI -- juniper-doc-tools [1/2]"])
        self.assertEqual(report["blocking"], [])

    def test_advisory_sometimes_seen_is_not_path_gated(self) -> None:
        a = ALWAYS
        b = ALWAYS | {ADVISORY}
        report = self._audit(set(), [a, b])
        self.assertEqual(report["path_gated"], [])
        self.assertEqual(report["advisory_seen"], [ADVISORY])

    def test_empty_sample_is_not_a_false_census(self) -> None:
        report = self._audit({"tests"}, [])
        self.assertEqual(report["prs_sampled"], 0)
        self.assertEqual(report["blocking"], ["tests"])
        self.assertEqual(report["tier1"], [])
        self.assertEqual(report["path_gated"], [])
        self.assertEqual(report["matched"], [])


if __name__ == "__main__":
    unittest.main()
