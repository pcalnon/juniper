"""Cross-repo drift detection for the ``juniper-doc-tools`` pin in
each consumer repo's CI workflow.

Plan §5.1 of ``notes/JUNIPER_2026-05-18_JUNIPER-ML_DOC-TOOLS-PYPI-MIGRATION-PLAN.md``:

   "A range that falls outside the supported window (more than 2 minor
   versions behind current) gets surfaced as a soft warning, not a
   hard fail. Hard fail only if the pin is for a version that has been
   yanked or pre-1.0."

This test runs in three modes:

1. **Weekly cross-repo CI** (``docs-full-check.yml``): all sibling
   Juniper repos are freshly cloned alongside juniper-ml. Cross-repo
   assertions run against those fresh checkouts.
2. **Per-PR CI** (``ci.yml``): only juniper-ml is checked out. The
   cross-repo assertion auto-skips (no siblings present), but the
   helper unit tests and juniper-ml's own pin check still run --
   catching the case where someone bumps juniper-doc-tools in this
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
``juniper-doc-tools/pyproject.toml`` -- that file is the source of
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
import sys
import tempfile
import unittest
from pathlib import Path

# Pin-range pattern we expect in each consumer's ci.yml:
#   pip install "juniper-doc-tools>=0.1.0,<0.2.0"
# Whitespace inside the quoted spec is forgiving. The two captured
# groups are (lower-bound, upper-bound) -- both are full PEP 440
# version strings.
_PIN_PATTERN = re.compile(r"juniper-doc-tools\s*>=\s*([0-9]+(?:\.[0-9]+)+)\s*,\s*<\s*([0-9]+(?:\.[0-9]+)+)")

# How many minor versions back is still "supported". A consumer pinned
# at <0.X.0 is supported when current is in 0.X-1.* / 0.X.*; once
# current rolls to 0.X+1.*, the pin is one minor behind (warn); 0.X+2.*
# is two behind (warn); 0.X+3.* and beyond is hard fail.
_SUPPORTED_MINORS_BACK = 2

# Consumer repos that pin juniper-doc-tools in their CI. juniper-ml
# itself does too (in docs-full-check.yml) -- it gets linted as a
# special case via _ML_OWN_WORKFLOWS below.
# juniper-recurrence ships the pin in ``ci-docs.yml`` (not ``ci.yml``);
# discovery walks every workflow under ``.github/workflows/``.
_CONSUMER_REPOS = (
    "juniper-canopy",
    "juniper-cascor",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-data",
    "juniper-data-client",
    "juniper-recurrence",
)

# juniper-deploy is deliberately excluded: it has no docs-link CI and
# does not depend on juniper-doc-tools.

# When linting juniper-ml itself, walk every workflow under
# .github/workflows/. ci.yml (per-PR docs job) and docs-full-check.yml
# (weekly cross-repo) both install juniper-doc-tools.
_ML_OWN_WORKFLOWS = (".github/workflows/ci.yml", ".github/workflows/docs-full-check.yml")


def _parse_version(v: str) -> tuple[int, ...]:
    """Convert "0.1.0" -> (0, 1, 0). Ignores any pre-release tags."""
    parts = v.split(".")
    return tuple(int(p.split("-")[0].split("+")[0]) for p in parts)


def _read_current_version(juniper_ml_root: Path) -> str | None:
    """Read the current juniper-doc-tools version from this repo's
    pyproject.toml. Returns None if the file or version line cannot
    be located (test gracefully skips in that case)."""
    pyproject = juniper_ml_root / "juniper-doc-tools" / "pyproject.toml"
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
    """Find every ``juniper-doc-tools>=X,<Y`` reference in the file.
    Returns a list of (lower, upper) tuples. Multiple references in
    the same file are returned in order -- e.g., ci.yml and
    docs-full-check.yml of juniper-ml each have one.
    """
    return [(m.group(1), m.group(2)) for m in _PIN_PATTERN.finditer(yaml_text)]


def _consumer_workflow_files(repo_root: Path) -> list[Path]:
    """Return ``.github/workflows/*.{yml,yaml}`` for a consumer checkout.

    Some siblings (notably ``juniper-recurrence``) pin juniper-doc-tools in
    a dedicated ``ci-docs.yml`` rather than ``ci.yml``. Scanning every
    workflow keeps the weekly pin lint honest without hardcoding filenames.
    """
    workflows = repo_root / ".github" / "workflows"
    if not workflows.is_dir():
        return []
    return sorted(workflows.glob("*.yml")) + sorted(workflows.glob("*.yaml"))


def _extract_pins_from_repo(repo_root: Path) -> list[tuple[str, str, str]]:
    """Collect ``(lower, upper, relative_workflow)`` pins from a consumer repo."""
    found: list[tuple[str, str, str]] = []
    for wf in _consumer_workflow_files(repo_root):
        try:
            text = wf.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = str(wf.relative_to(repo_root))
        for lower, upper in _extract_pins_from_yaml(text):
            found.append((lower, upper, rel))
    return found


def _find_ecosystem_root(juniper_ml_root: Path) -> Path | None:
    """Walk up from ``juniper_ml_root`` looking for a directory that
    contains at least 3 known juniper-X siblings. Mirrors the heuristic
    in ``juniper_doc_tools._ecosystem`` so this test does not need to
    import that package (which keeps it runnable on a runner that has
    not yet installed juniper-doc-tools).
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


class JuniperDocToolsDriftTest(unittest.TestCase):
    """Walk each consumer repo's CI workflows and assert the pinned
    ``juniper-doc-tools>=X,<Y`` range still includes the current
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
            ("Could not read juniper-doc-tools version from " "juniper-doc-tools/pyproject.toml. The drift test depends " "on this file as the source of truth for 'current'."),
        )

    def test_juniper_ml_own_workflows_pin_current_version(self):
        """juniper-ml's own ci.yml + docs-full-check.yml must accept
        the current juniper-doc-tools version. This catches the case
        where a doc-tools minor bump (in this same repo, in this same
        PR) was not accompanied by a pin bump."""
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
                    f"{rel} no longer pins juniper-doc-tools; did Wave 4 " "get reverted by accident?",
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
        """Read each cloned consumer repo's workflows and assert the
        juniper-doc-tools pin admits the current version. Skipped
        when siblings are not present (per-PR mode) or when running
        locally without ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`` (local
        sibling working trees can lag ``origin/main`` and produce
        false positives -- see this module's docstring).

        Scans every ``.github/workflows/*.{yml,yaml}`` so siblings that
        pin in a dedicated docs workflow (``juniper-recurrence`` /
        ``ci-docs.yml``) are not silently skipped.
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
                repo_root = self.ecosystem_root / repo
                if not repo_root.is_dir():
                    print(f"WARN: {repo}/ not present (clone failure?)")
                    continue
                pins = _extract_pins_from_repo(repo_root)
                if not pins:
                    self.fail(f"{repo}/.github/workflows/ has no juniper-doc-tools pin -- " "Wave 2 did not run here (or was reverted).")
                for lower, upper, rel in pins:
                    lower_tuple = _parse_version(lower)
                    upper_tuple = _parse_version(upper)
                    self.assertLessEqual(
                        lower_tuple,
                        current_tuple,
                        f"{repo} ({rel}) pin lower bound {lower} is ahead of current {self.current_version}",
                    )
                    # Soft window: warn if the pin is more than the
                    # supported number of minors behind, even though it
                    # still admits current. Plan §5.1 specifies this as
                    # a soft warning, not a hard fail.
                    if upper_tuple[0] == current_tuple[0] and upper_tuple[1] - current_tuple[1] - 1 > _SUPPORTED_MINORS_BACK:
                        warnings.append(f"{repo} ({rel}): pin {lower}..{upper} is more than " f"{_SUPPORTED_MINORS_BACK} minors behind current " f"{self.current_version}; consider widening.")
                    self.assertLess(
                        current_tuple,
                        upper_tuple,
                        f"{repo} ({rel}) pin upper bound {upper} excludes current " f"{self.current_version} -- bump the pin in {repo}.",
                    )

        if warnings:
            print("=== juniper-doc-tools pin drift warnings ===", file=sys.stderr)
            for w in warnings:
                print(f"  {w}", file=sys.stderr)


class PinParsingHelperTest(unittest.TestCase):
    """Direct unit tests for the helpers so they don't rely on the
    integration test for coverage."""

    def test_extracts_simple_pin(self):
        yaml_text = '          pip install "juniper-doc-tools>=0.1.0,<0.2.0"\n'
        self.assertEqual(_extract_pins_from_yaml(yaml_text), [("0.1.0", "0.2.0")])

    def test_extracts_multiple_pins(self):
        yaml_text = 'pip install "juniper-doc-tools>=0.1.0,<0.2.0"\n' 'pip install "juniper-doc-tools>=0.1.2,<0.3.0"\n'
        self.assertEqual(
            _extract_pins_from_yaml(yaml_text),
            [("0.1.0", "0.2.0"), ("0.1.2", "0.3.0")],
        )

    def test_ignores_unrelated_pin_strings(self):
        yaml_text = 'pip install "juniper-observability>=0.1.0,<0.2.0"\n'
        self.assertEqual(_extract_pins_from_yaml(yaml_text), [])

    def test_parses_version_strings_to_tuples(self):
        self.assertEqual(_parse_version("0.1.0"), (0, 1, 0))
        self.assertEqual(_parse_version("1.2.3"), (1, 2, 3))
        self.assertEqual(_parse_version("0.1.1-rc1"), (0, 1, 1))
        self.assertEqual(_parse_version("0.10.0"), (0, 10, 0))

    def test_supported_window_constant_matches_plan(self):
        # Plan §5.1: "more than 2 minor versions behind current" warns.
        self.assertEqual(_SUPPORTED_MINORS_BACK, 2)

    def test_consumer_workflow_scan_finds_ci_docs_pin(self):
        """Recurrence-shaped layout: pin lives in ``ci-docs.yml``, not ``ci.yml``."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wf = root / ".github" / "workflows"
            wf.mkdir(parents=True)
            (wf / "ci-pre-commit.yml").write_text("name: pre-commit\n", encoding="utf-8")
            (wf / "ci-docs.yml").write_text(
                '          pip install "juniper-doc-tools>=0.1.0,<0.2.0"\n',
                encoding="utf-8",
            )
            pins = _extract_pins_from_repo(root)
            self.assertEqual(pins, [("0.1.0", "0.2.0", ".github/workflows/ci-docs.yml")])

    def test_consumer_repos_include_recurrence(self):
        self.assertIn(
            "juniper-recurrence",
            _CONSUMER_REPOS,
            "juniper-recurrence ships ci-docs.yml with a juniper-doc-tools pin",
        )


if __name__ == "__main__":
    unittest.main()
