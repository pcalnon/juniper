"""Cross-repo drift detection for the ``juniper-ci-tools`` pin in
each consumer repo's CI workflow.

Plan §5.1 of ``notes/JUNIPER_2026-05-20_JUNIPER-ML_CI-TOOLS-PYPI-MIGRATION-PLAN.md``:

   "Soft-warn on > 2 minors of lag; hard-fail when the upper bound
   excludes the current version."

This test mirrors ``tests/test_doc_tools_drift.py`` (the doc-tools
sibling) and runs in three modes:

1. **Weekly cross-repo CI** (``docs-full-check.yml``): all sibling
   Juniper repos are freshly cloned alongside juniper-ml. Cross-repo
   assertions run against those fresh checkouts.
2. **Per-PR CI** (``ci.yml``): only juniper-ml is checked out. The
   cross-repo assertion auto-skips (no siblings present), but the
   helper unit tests and juniper-ml's own pin check still run --
   catching the case where someone bumps juniper-ci-tools in this
   same PR but forgets to bump the pin in juniper-ml's workflows.
3. **Local dev** (no ``GITHUB_ACTIONS`` env var): the cross-repo
   assertion is gated behind ``GITHUB_ACTIONS=true``. Local sibling
   working trees can lag ``origin/main`` (a freshly merged consumer
   repo PR might not have been pulled), and that local-stale state
   would produce false positives. Set
   ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`` to override and lint the
   local working trees anyway (useful when actively testing this
   suite itself).

The "current version" is read from this repo's
``juniper-ci-tools/pyproject.toml`` -- that file is the source of
truth for the in-development version, and the weekly workflow runs
against ``main``, so this is always the most-recently-released
version.

Yank detection is deliberately out of scope (would require a network
call to PyPI's JSON API on every test run; brittle and rarely
relevant). The check covers the common drift case: a consumer pin
ceiling that no longer permits the current version.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Pin-range pattern we expect in each consumer's ci.yml:
#   pip install "juniper-ci-tools>=0.1.0,<0.2.0"
# Whitespace inside the quoted spec is forgiving. The two captured
# groups are (lower-bound, upper-bound) -- both are full PEP 440
# version strings.
_PIN_PATTERN = re.compile(r"juniper-ci-tools\s*>=\s*([0-9]+(?:\.[0-9]+)+)\s*,\s*<\s*([0-9]+(?:\.[0-9]+)+)")

# How many minor versions back is still "supported". A consumer pinned
# at <0.X.0 is supported when current is in 0.X-1.* / 0.X.*; once
# current rolls to 0.X+1.*, the pin is one minor behind (warn); 0.X+2.*
# is two behind (warn); 0.X+3.* and beyond is hard fail.
_SUPPORTED_MINORS_BACK = 2

# Consumer repos that pin juniper-ci-tools in their CI. juniper-ml
# itself does too (in ci.yml + lockfile-update.yml) -- it gets linted
# as a special case via _ML_OWN_WORKFLOWS below.
_CONSUMER_REPOS = (
    "juniper-canopy",
    "juniper-cascor",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-data",
    "juniper-data-client",
)

# juniper-deploy is deliberately excluded: it has no "Generate
# Dependency Documentation" CI step and does not depend on
# juniper-ci-tools.

# When linting juniper-ml itself, walk every workflow under
# .github/workflows/ that installs juniper-ci-tools:
#   - ci.yml                  -- per-PR "Generate Dependency Documentation" (dep-docs)
#                                + the per-PR "Sequence Safety" screen job (>=0.8.0)
#                                + the tests job (test_predict_merge shells the screens)
#   - main-verify.yml         -- the post-merge (G3) sequence-safety screens (>=0.8.0;
#                                rollout W3 -- the sequence-safety.yml/main-verify.yml pin
#                                scan the plan §W3 step 3.3 calls for)
#   - lockfile-update.yml     -- weekly lockfile refresh
#   - docs-full-check.yml     -- §5.2 weekly downstream integration
_ML_OWN_WORKFLOWS = (
    ".github/workflows/ci.yml",
    ".github/workflows/main-verify.yml",
    ".github/workflows/lockfile-update.yml",
    ".github/workflows/docs-full-check.yml",
)

# Files/dirs that housed the in-repo sequence-safety screens before rollout W3 migrated
# them into the juniper-ci-tools package. Their reappearance in juniper-ml would resurrect
# the inline-copy drift class the migration killed (the same class the doc-tools + dep-docs
# migrations killed before it). The cli*.py class guard in juniper-ci-tools already covers
# the two new console scripts; this list is the juniper-ml-side resurrection guard.
_MIGRATED_INLINE_SCREENS = (
    "util/sequence_safety",
    "tests/test_symbol_loss_check.py",
    "tests/test_docs_additions_check.py",
)


def _resurrected_inline_screens(root: Path) -> list[str]:
    """Return the migrated inline-screen paths (from ``_MIGRATED_INLINE_SCREENS``) that
    still exist under ``root``. Empty list == clean (fully migrated)."""
    return [rel for rel in _MIGRATED_INLINE_SCREENS if (root / rel).exists()]


def _parse_version(v: str) -> tuple[int, ...]:
    """Convert "0.1.0" -> (0, 1, 0). Ignores any pre-release tags."""
    parts = v.split(".")
    return tuple(int(p.split("-")[0].split("+")[0]) for p in parts)


def _read_current_version(juniper_ml_root: Path) -> str | None:
    """Read the current juniper-ci-tools version from this repo's
    pyproject.toml. Returns None if the file or version line cannot
    be located (test gracefully skips in that case)."""
    pyproject = juniper_ml_root / "juniper-ci-tools" / "pyproject.toml"
    if not pyproject.exists():
        return None
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        # Match the ``version = "X.Y.Z"`` line inside [project]
        m = re.match(r'^version\s*=\s*"([^"]+)"\s*$', line)
        if m:
            return m.group(1)
    return None


def _extract_pins_from_yaml(yaml_text: str) -> list[tuple[str, str]]:
    """Find every ``juniper-ci-tools>=X,<Y`` reference in the file.
    Returns a list of (lower, upper) tuples. Multiple references in
    the same file are returned in order.
    """
    return [(m.group(1), m.group(2)) for m in _PIN_PATTERN.finditer(yaml_text)]


def _find_ecosystem_root(juniper_ml_root: Path) -> Path | None:
    """Walk up from ``juniper_ml_root`` looking for a directory that
    contains at least 3 known juniper-X siblings. Mirrors the heuristic
    used by ``test_doc_tools_drift.py``.
    """
    known = set(_CONSUMER_REPOS)
    for candidate in (juniper_ml_root.parent, juniper_ml_root.parent.parent):
        try:
            found = sum(1 for repo in known if (candidate / repo).is_dir())
        except OSError:
            # PermissionError is a subclass of OSError; covers both.
            continue
        if found >= 3:
            return candidate
    return None


class JuniperCiToolsDriftTest(unittest.TestCase):
    """Walk each consumer repo's CI workflows and assert the pinned
    ``juniper-ci-tools>=X,<Y`` range still includes the current
    version. Surface a soft warning when a pin is one or two minors
    behind; fail when it falls outside the supported window.
    """

    @classmethod
    def setUpClass(cls):
        cls.juniper_ml_root = Path(__file__).resolve().parent.parent
        cls.current_version = _read_current_version(cls.juniper_ml_root)
        cls.ecosystem_root = _find_ecosystem_root(cls.juniper_ml_root)

    def test_environment_is_either_weekly_or_skipped(self):
        """Sanity: either we have siblings to lint, or we don't. Both
        are valid; we just need to know which mode we're in so the
        operator reading CI logs is not confused."""
        if self.ecosystem_root is None:
            print("INFO: ecosystem siblings not present on disk -- drift " "check is skipping (run is not weekly cross-repo).")
        else:
            print(f"INFO: ecosystem root = {self.ecosystem_root}")

    def test_current_version_is_readable(self):
        self.assertIsNotNone(
            self.current_version,
            ("Could not read juniper-ci-tools version from " "juniper-ci-tools/pyproject.toml. The drift test depends " "on this file as the source of truth for 'current'."),
        )

    def test_juniper_ml_own_workflows_pin_current_version(self):
        """juniper-ml's own ci.yml + lockfile-update.yml +
        docs-full-check.yml must accept the current juniper-ci-tools
        version. This catches the case where a ci-tools minor bump
        (in this same repo, in this same PR) was not accompanied by
        a pin bump."""
        if self.current_version is None:
            self.skipTest("no current version available")
        current_tuple = _parse_version(self.current_version)
        for rel in _ML_OWN_WORKFLOWS:
            with self.subTest(workflow=rel):
                wf = self.juniper_ml_root / rel
                if not wf.exists():
                    self.skipTest(f"{rel} not present in this checkout")
                    continue
                pins = _extract_pins_from_yaml(wf.read_text(encoding="utf-8"))
                self.assertGreater(
                    len(pins),
                    0,
                    f"{rel} no longer pins juniper-ci-tools; did Wave 4 " "get reverted by accident?",
                )
                for lower, upper in pins:
                    lower_tuple = _parse_version(lower)
                    upper_tuple = _parse_version(upper)
                    self.assertLessEqual(
                        lower_tuple,
                        current_tuple,
                        f"{rel} pin lower bound {lower} is ahead of current {self.current_version}",
                    )
                    self.assertLess(
                        current_tuple,
                        upper_tuple,
                        f"{rel} pin upper bound {upper} excludes current {self.current_version} -- bump the pin",
                    )

    def test_consumer_repos_pin_current_version(self):
        """Read each cloned consumer repo's ci.yml and assert the
        juniper-ci-tools pin admits the current version. Skipped
        when siblings are not present (per-PR mode) or when running
        locally without ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`` (local
        sibling working trees can lag ``origin/main`` and produce
        false positives -- see this module's docstring).
        """
        if self.ecosystem_root is None:
            self.skipTest("ecosystem siblings not on disk")
        if self.current_version is None:
            self.skipTest("no current version available")
        if os.environ.get("GITHUB_ACTIONS") != "true" and not os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL"):
            self.skipTest("skipping local cross-repo lint (set " "JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 to override; siblings " "must be `git pull`ed to origin/main first)")

        current_tuple = _parse_version(self.current_version)
        warnings: list[str] = []
        for repo in _CONSUMER_REPOS:
            with self.subTest(repo=repo):
                ci = self.ecosystem_root / repo / ".github" / "workflows" / "ci.yml"
                if not ci.exists():
                    print(f"WARN: {repo}/.github/workflows/ci.yml not present (clone failure?)")
                    continue
                pins = _extract_pins_from_yaml(ci.read_text(encoding="utf-8"))
                if not pins:
                    self.fail(f"{repo}/.github/workflows/ci.yml has no juniper-ci-tools pin -- " "Wave 2 did not run here (or was reverted).")
                for lower, upper in pins:
                    lower_tuple = _parse_version(lower)
                    upper_tuple = _parse_version(upper)
                    self.assertLessEqual(
                        lower_tuple,
                        current_tuple,
                        f"{repo} pin lower bound {lower} is ahead of current {self.current_version}",
                    )
                    # Soft window: warn if the pin is more than the
                    # supported number of minors behind, even though it
                    # still admits current. Plan §5.1 specifies this as
                    # a soft warning, not a hard fail.
                    if upper_tuple[0] == current_tuple[0] and upper_tuple[1] - current_tuple[1] - 1 > _SUPPORTED_MINORS_BACK:
                        warnings.append(f"{repo}: pin {lower}..{upper} is more than " f"{_SUPPORTED_MINORS_BACK} minors behind current " f"{self.current_version}; consider widening.")
                    self.assertLess(
                        current_tuple,
                        upper_tuple,
                        f"{repo} pin upper bound {upper} excludes current " f"{self.current_version} -- bump the pin in {repo}.",
                    )

        if warnings:
            print("=== juniper-ci-tools pin drift warnings ===", file=sys.stderr)
            for w in warnings:
                print(f"  {w}", file=sys.stderr)


class PinParsingHelperTest(unittest.TestCase):
    """Direct unit tests for the helpers so they don't rely on the
    integration test for coverage."""

    def test_extracts_simple_pin(self):
        yaml_text = '          pip install "juniper-ci-tools>=0.1.0,<0.2.0"\n'
        self.assertEqual(_extract_pins_from_yaml(yaml_text), [("0.1.0", "0.2.0")])

    def test_extracts_multiple_pins(self):
        yaml_text = 'pip install "juniper-ci-tools>=0.1.0,<0.2.0"\n' 'pip install "juniper-ci-tools>=0.1.2,<0.3.0"\n'
        self.assertEqual(
            _extract_pins_from_yaml(yaml_text),
            [("0.1.0", "0.2.0"), ("0.1.2", "0.3.0")],
        )

    def test_ignores_unrelated_pin_strings(self):
        yaml_text = 'pip install "juniper-doc-tools>=0.1.0,<0.2.0"\n'
        self.assertEqual(_extract_pins_from_yaml(yaml_text), [])

    def test_parses_version_strings_to_tuples(self):
        self.assertEqual(_parse_version("0.1.0"), (0, 1, 0))
        self.assertEqual(_parse_version("1.2.3"), (1, 2, 3))
        self.assertEqual(_parse_version("0.1.1-rc1"), (0, 1, 1))
        self.assertEqual(_parse_version("0.10.0"), (0, 10, 0))

    def test_supported_window_constant_matches_plan(self):
        # Plan §5.1: "more than 2 minor versions behind current" warns.
        self.assertEqual(_SUPPORTED_MINORS_BACK, 2)


class SequenceSafetyPackageMigrationTest(unittest.TestCase):
    """Anti-resurrection gate for the sequence-safety package migration (rollout W3,
    plan §W3 step 3.3).

    The AST symbol-loss + docs deletion-magnitude screens now ship as the
    juniper-ci-tools console scripts ``juniper-symbol-loss-check`` /
    ``juniper-docs-additions-check`` (>=0.8.0); juniper-ml's ci.yml + main-verify.yml
    consume them and MUST NOT carry the inline ``util/sequence_safety/`` copy or its two
    moved unit tests. This gate has two halves:

      (a) *resurrection guard* -- juniper-ml's own tree carries none of the migrated
          inline paths (``test_inline_sequence_safety_tree_is_gone`` + a synthetic-fixture
          negative that proves the guard bites);
      (b) *pin admits current* -- the two new screen pins (``>=0.8.0,<0.9.0`` in ci.yml's
          sequence-safety job and in main-verify.yml) still admit the current
          juniper-ci-tools version, enforced by ``JuniperCiToolsDriftTest`` above now that
          ``main-verify.yml`` is in ``_ML_OWN_WORKFLOWS``.
    """

    def test_inline_sequence_safety_tree_is_gone(self):
        """(a) No resurrected inline screen tree / moved test lives in juniper-ml."""
        root = Path(__file__).resolve().parent.parent
        stragglers = _resurrected_inline_screens(root)
        self.assertEqual(
            stragglers,
            [],
            "the sequence-safety screens are migrated to the juniper-ci-tools package " "(rollout W3); delete the resurrected inline copy / moved test(s): " + ", ".join(stragglers),
        )

    def test_resurrection_guard_bites_on_synthetic_tree(self):
        """Red-then-green proof: the guard is silent on a clean synthetic root and FIRES
        when the migrated inline tree is planted there -- so a real resurrection in
        juniper-ml cannot slip past ``test_inline_sequence_safety_tree_is_gone``. The
        planting happens in a throwaway tmp fixture, never in the repo."""
        tmp = Path(tempfile.mkdtemp(prefix="seqsafety-resurrection-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)

        # GREEN: a clean synthetic root reports no resurrection.
        self.assertEqual(_resurrected_inline_screens(tmp), [])

        # RED: plant the migrated inline tree + its two moved tests; the guard must fire.
        (tmp / "util" / "sequence_safety").mkdir(parents=True)
        (tmp / "util" / "sequence_safety" / "symbol_loss_check.py").write_text("# resurrected\n", encoding="utf-8")
        (tmp / "tests").mkdir()
        (tmp / "tests" / "test_symbol_loss_check.py").write_text("# resurrected\n", encoding="utf-8")
        (tmp / "tests" / "test_docs_additions_check.py").write_text("# resurrected\n", encoding="utf-8")
        self.assertEqual(
            _resurrected_inline_screens(tmp),
            list(_MIGRATED_INLINE_SCREENS),
            "the resurrection guard must report every planted inline-screen path",
        )


class SequenceSafetyResurrectionHelperTest(unittest.TestCase):
    """Direct unit tests for ``_resurrected_inline_screens`` so it is covered independent
    of the real-tree assertion (which is empty in the healthy repo)."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="seqsafety-helper-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_empty_root_is_clean(self):
        self.assertEqual(_resurrected_inline_screens(self.tmp), [])

    def test_reports_only_the_paths_present(self):
        (self.tmp / "tests").mkdir()
        (self.tmp / "tests" / "test_docs_additions_check.py").write_text("x\n", encoding="utf-8")
        self.assertEqual(_resurrected_inline_screens(self.tmp), ["tests/test_docs_additions_check.py"])


if __name__ == "__main__":
    unittest.main()
