#!/usr/bin/env python3
"""Hermetic regression tests for util/release_train/archive_guard.py (plan S7.2, Phase 3 step 3.1).

NO network, NO real gh, NO git process: the pure classifier (`classify_diff`) is driven directly
with synthetic `git diff --name-status` change sets, and the CLI is exercised through the
`--name-status-file` seam against the REAL registry.yaml (so the name-valid rule is checked against
the actual 18 registered pypi_names). `util/` is not pre-commit-lint-gated, so this unittest IS the
gate (the `env_floor_drift_check` precedent, shared with the sibling detectors). Imported via the
house `sys.path.insert` idiom.

Covers (task acceptance list, plan S7.2):
  * a PURE notes-add diff PASSES (meta form + sub-package form)
  * a non-archive PR (no notes/releases/ path) SKIPs -- the guard never blocks a normal PR
  * MODIFY, DELETE, OUT-OF-PATH, BAD-NAME, and MIXED diffs each FAIL (the four synthetic negatives)
  * slash-in-basename nested under notes/releases/ (ARCHIVE_PATH_RE match + ``/`` in basename) FAILs
    rule2 flat-archive — distinct from a non-matching ``notes/releases/<dir>/...`` path
  * the fallback semantic: a FAIL merely fails the check (exit 1), no side effect
  * filename convention (rule 3): meta bare-`v` vs `<pkg>_v`, the meta wrong-form reject, unknown
    package + non-semver rejects
  * parse_name_status (rename two-path form, similarity score stripped, blank/short lines ignored)
  * CLI exit codes 0 (SKIP/OK) / 1 (FAIL) / 2 (no diff source) and the --json shape

Run: python3 -m unittest -v tests/test_release_train_archive_guard.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-07-17
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UTIL_DIR = REPO_ROOT / "util" / "release_train"
sys.path.insert(0, str(UTIL_DIR))

import archive_guard as ag  # noqa: E402

REAL_REGISTRY = UTIL_DIR / "registry.yaml"

# A convention-valid sub-package archive add (the canonical exempt-PR payload the ceremony opens).
GOOD_SUB = "notes/releases/RELEASE_NOTES_juniper-service-core_v0.5.0.md"
GOOD_META = "notes/releases/RELEASE_NOTES_v0.6.0.md"


def _changes(*rows) -> list:
    """Build Change records from (status, path) or (status, old, new) tuples."""
    out = []
    for row in rows:
        out.append(ag.Change(status=row[0], paths=list(row[1:])))
    return out


class ArchiveGuardKnownNamesTest(unittest.TestCase):
    """The registered pypi_name set the rule-3 name check resolves against (from the real registry)."""

    @classmethod
    def setUpClass(cls):
        cls.known = ag.load_known_pypi_names(None)

    def test_registry_resolves_expected_packages(self):
        # A representative in-repo sub-package + the meta must be present (the pilot family).
        self.assertIn("juniper-service-core", self.known)
        self.assertIn("juniper-ml", self.known)
        self.assertGreaterEqual(len(self.known), 18)


class FilenameConventionTest(unittest.TestCase):
    """Rule 3 (plan S7.2 / procedure S11.3): the two archive filename forms and their rejects."""

    KNOWN = frozenset({"juniper-ml", "juniper-service-core", "juniper-ci-tools"})

    def test_meta_bare_v_form_valid(self):
        self.assertTrue(ag.filename_valid("RELEASE_NOTES_v0.6.0.md", self.KNOWN))

    def test_subpackage_form_valid(self):
        self.assertTrue(ag.filename_valid("RELEASE_NOTES_juniper-service-core_v0.5.0.md", self.KNOWN))

    def test_meta_wrong_form_rejected(self):
        # The meta MUST use the bare `v` form; RELEASE_NOTES_juniper-ml_v*.md is a deliberate reject.
        self.assertFalse(ag.filename_valid("RELEASE_NOTES_juniper-ml_v0.6.0.md", self.KNOWN))

    def test_unregistered_package_rejected(self):
        self.assertFalse(ag.filename_valid("RELEASE_NOTES_juniper-nonesuch_v1.0.0.md", self.KNOWN))

    def test_non_semver_rejected(self):
        self.assertFalse(ag.filename_valid("RELEASE_NOTES_juniper-service-core_vABC.md", self.KNOWN))
        self.assertFalse(ag.filename_valid("RELEASE_NOTES_juniper-service-core_v1.2.md", self.KNOWN))

    def test_prerelease_semver_accepted(self):
        self.assertTrue(ag.filename_valid("RELEASE_NOTES_juniper-service-core_v0.5.0-rc1.md", self.KNOWN))


class ParseNameStatusTest(unittest.TestCase):
    def test_simple_add(self):
        changes = ag.parse_name_status(f"A\t{GOOD_SUB}\n")
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].status, "A")
        self.assertEqual(changes[0].path, GOOD_SUB)

    def test_rename_two_paths_and_score_stripped(self):
        changes = ag.parse_name_status("R100\tnotes/releases/old.md\tnotes/releases/new.md\n")
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].status, "R")  # leading letter only
        self.assertEqual(changes[0].paths, ["notes/releases/old.md", "notes/releases/new.md"])
        self.assertEqual(changes[0].path, "notes/releases/new.md")

    def test_blank_and_short_lines_ignored(self):
        changes = ag.parse_name_status("\n   \nA\tnotes/releases/x.md\ngarbage-no-tab\n")
        self.assertEqual([c.path for c in changes], ["notes/releases/x.md"])


class ClassifyDiffTest(unittest.TestCase):
    """The four structural rules driven directly (plan S7.2)."""

    KNOWN = frozenset({"juniper-ml", "juniper-service-core", "juniper-ci-tools", "juniper-observability"})

    # ---- PASS cases --------------------------------------------------------------------------
    def test_pure_subpackage_notes_add_passes(self):
        res = ag.classify_diff(_changes(("A", GOOD_SUB)), self.KNOWN)
        self.assertEqual(res.verdict, "OK")
        self.assertTrue(res.passed)
        self.assertTrue(res.is_archive_pr)
        self.assertEqual(res.violations, [])
        self.assertEqual(res.added, [GOOD_SUB])

    def test_pure_meta_notes_add_passes(self):
        res = ag.classify_diff(_changes(("A", GOOD_META)), self.KNOWN)
        self.assertEqual(res.verdict, "OK")
        self.assertTrue(res.passed)

    def test_two_valid_archive_adds_pass(self):
        # The exempt PR may carry more than one archive file (still single-purpose).
        res = ag.classify_diff(_changes(("A", GOOD_SUB), ("A", GOOD_META)), self.KNOWN)
        self.assertEqual(res.verdict, "OK", res.violations)

    def test_non_archive_pr_skips(self):
        res = ag.classify_diff(_changes(("M", "src/foo.py"), ("A", "tests/test_foo.py")), self.KNOWN)
        self.assertEqual(res.verdict, "SKIP")
        self.assertTrue(res.passed)  # a normal code PR is never blocked by the guard
        self.assertFalse(res.is_archive_pr)
        self.assertEqual(res.violations, [])

    # ---- the five synthetic FAIL cases (task acceptance) -------------------------------------
    def test_modify_archive_file_fails(self):
        res = ag.classify_diff(_changes(("M", GOOD_SUB)), self.KNOWN)
        self.assertEqual(res.verdict, "FAIL")
        self.assertFalse(res.passed)
        self.assertTrue(any(v.startswith("rule1") for v in res.violations), res.violations)

    def test_delete_archive_file_fails(self):
        res = ag.classify_diff(_changes(("D", GOOD_SUB)), self.KNOWN)
        self.assertEqual(res.verdict, "FAIL")
        self.assertTrue(any(v.startswith("rule1") for v in res.violations), res.violations)

    def test_out_of_path_within_releases_fails(self):
        # A path *under* notes/releases/ (so the PR is enforced) but not a flat RELEASE_NOTES_*.md.
        nested = "notes/releases/archive/RELEASE_NOTES_juniper-service-core_v0.5.0.md"
        res = ag.classify_diff(_changes(("A", nested)), self.KNOWN)
        self.assertEqual(res.verdict, "FAIL")
        self.assertTrue(any(v.startswith("rule2") for v in res.violations), res.violations)
        # This shape fails ARCHIVE_PATH_RE first (``archive/`` precedes RELEASE_NOTES_), so it
        # never exercises the slash-in-basename flatness arm — see the next case.
        self.assertFalse(
            any("nested under notes/releases/" in v for v in res.violations),
            res.violations,
        )

    def test_slash_in_basename_nested_archive_path_fails(self):
        # ARCHIVE_PATH_RE is ``^notes/releases/RELEASE_NOTES_.*\\.md$`` — the ``.*`` admits a
        # slash. A path that still matches the regex but nests under notes/releases/ must hit the
        # dedicated flatness check (archive_guard.py rule2 ``"/" in basename``), not only the
        # non-matching-prefix arm covered by test_out_of_path_within_releases_fails.
        nested = "notes/releases/RELEASE_NOTES_juniper-service-core/v0.5.0.md"
        self.assertIsNotNone(ag.ARCHIVE_PATH_RE.match(nested), nested)
        basename = nested[len(ag.RELEASES_PREFIX) :]
        self.assertIn("/", basename)
        res = ag.classify_diff(_changes(("A", nested)), self.KNOWN)
        self.assertEqual(res.verdict, "FAIL")
        self.assertTrue(res.is_archive_pr)
        self.assertFalse(res.passed)
        nested_violations = [v for v in res.violations if "nested under notes/releases/" in v]
        self.assertEqual(len(nested_violations), 1, res.violations)
        self.assertTrue(nested_violations[0].startswith("rule2"), nested_violations[0])
        # Matched ARCHIVE_PATH_RE, so rule4 (out-of-scope non-match) must not be the sole signal.
        self.assertFalse(
            any(v.startswith("rule4") for v in res.violations),
            res.violations,
        )

    def test_bad_name_fails(self):
        bad = "notes/releases/RELEASE_NOTES_juniper-nonesuch_v1.0.0.md"  # unregistered package
        res = ag.classify_diff(_changes(("A", bad)), self.KNOWN)
        self.assertEqual(res.verdict, "FAIL")
        self.assertTrue(any(v.startswith("rule3") for v in res.violations), res.violations)

    def test_mixed_diff_fails(self):
        # A valid archive add PLUS an unrelated modification -> touches releases/, but not single-purpose.
        res = ag.classify_diff(_changes(("A", GOOD_SUB), ("M", "CHANGELOG.md")), self.KNOWN)
        self.assertEqual(res.verdict, "FAIL")
        self.assertFalse(res.passed)
        self.assertTrue(any(v.startswith("rule1") for v in res.violations), res.violations)  # the M
        self.assertTrue(any(v.startswith("rule4") for v in res.violations), res.violations)  # CHANGELOG out of scope

    def test_out_of_path_extra_added_code_file_fails(self):
        # A valid archive add + an added file OUTSIDE notes/releases/.
        res = ag.classify_diff(_changes(("A", GOOD_SUB), ("A", "util/release_train/sneaky.py")), self.KNOWN)
        self.assertEqual(res.verdict, "FAIL")
        self.assertTrue(any(v.startswith("rule4") for v in res.violations), res.violations)

    def test_rename_into_releases_fails(self):
        res = ag.classify_diff(_changes(("R", "notes/foo.md", GOOD_SUB)), self.KNOWN)
        self.assertEqual(res.verdict, "FAIL")
        self.assertTrue(any(v.startswith("rule1") for v in res.violations), res.violations)


class CliTest(unittest.TestCase):
    """CLI exit-code contract (0 SKIP/OK, 1 FAIL, 2 invocation) via the --name-status-file seam."""

    def _run(self, name_status_text, *extra):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
            fh.write(name_status_text)
            path = fh.name
        self.addCleanup(lambda: Path(path).unlink(missing_ok=True))
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ag.main(["--name-status-file", path, "--registry", str(REAL_REGISTRY), *extra])
        return rc, buf.getvalue()

    def test_pass_ok_exit_0(self):
        rc, out = self._run(f"A\t{GOOD_SUB}\n")
        self.assertEqual(rc, 0)
        self.assertIn("OK", out)

    def test_skip_exit_0(self):
        rc, out = self._run("M\tsrc/foo.py\n")
        self.assertEqual(rc, 0)
        self.assertIn("SKIP", out)

    def test_fail_exit_1(self):
        rc, out = self._run(f"M\t{GOOD_SUB}\n")
        self.assertEqual(rc, 1)
        self.assertIn("FAIL", out)

    def test_json_shape(self):
        rc, out = self._run(f"A\t{GOOD_SUB}\n", "--json")
        self.assertEqual(rc, 0)
        payload = json.loads(out)
        self.assertEqual(payload["verdict"], "OK")
        self.assertTrue(payload["passed"])
        self.assertEqual(payload["added"], [GOOD_SUB])
        self.assertEqual(payload["schema"], "juniper-release-train/archive-guard/v1")

    def test_no_diff_source_exit_2(self):
        buf = io.StringIO()
        err = io.StringIO()
        # No --name-status-file and no --base/--head -> invocation error.
        with redirect_stdout(buf):
            import contextlib

            with contextlib.redirect_stderr(err):
                rc = ag.main(["--registry", str(REAL_REGISTRY)])
        self.assertEqual(rc, 2)
        self.assertIn("no diff source", err.getvalue())

    def test_real_registry_subpackage_and_meta_validate(self):
        # End-to-end against the REAL registry: the queued service-core payload + the meta form pass.
        rc_sub, _ = self._run(f"A\t{GOOD_SUB}\n")
        rc_meta, _ = self._run(f"A\t{GOOD_META}\n")
        self.assertEqual((rc_sub, rc_meta), (0, 0))


if __name__ == "__main__":
    unittest.main()
