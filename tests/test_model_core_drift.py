"""Drift detection for the ``juniper-model-core`` pin in juniper-ml's
``[tools]`` extra (and, once they exist, in consumer repos).

Companion to ``tests/test_doc_tools_drift.py`` / ``tests/test_ci_tools_drift.py``,
adapted to where ``juniper-model-core`` is actually pinned. Two differences from
those siblings:

1. **Pin location.** doc-tools / ci-tools are ``pip install``-ed in CI *workflows*,
   so their drift lints scan ``.github/workflows/*.yml``. juniper-model-core is a
   library dependency pinned in juniper-ml's ``pyproject.toml`` ``[tools]`` extra,
   so this lint reads the pin from there.
2. **Consumers.** The WS-4b recurrence app pins ``juniper-model-core[crossval]`` in its
   ``pyproject.toml`` (it drives ``POST /v1/crossval``); it is registered in
   ``_CONSUMER_REPOS`` below so the cross-repo assertion checks its pin still admits the
   current version. cascor (WS-6) joins when it adopts model-core. Each entry points at the
   *consuming package's* pyproject (which may be nested), so a multi-package repo only has
   its real consumer checked -- e.g. ``juniper-recurrence-model/`` deliberately stays on the
   0.1.x contract (it does not use crossval) and is intentionally not checked.

"Current version" is read from this repo's
``juniper-model-core/juniper_model_core/_version.py`` -- the source of truth for the
in-development version (the package uses setuptools dynamic versioning from that file).

The check covers the common drift case: a pin ceiling that no longer permits the
current version. Yank detection is out of scope (would need a PyPI network call).
"""

from __future__ import annotations

import os
import re
import sys
import tomllib
import unittest
from pathlib import Path

# Pin-range pattern: juniper-model-core>=0.1.0,<0.2.0 (whitespace-forgiving). An optional
# extras bracket is tolerated so consumer pins like juniper-model-core[crossval]>=0.2.0,<0.3.0
# (the recurrence app) match too.
_PIN_PATTERN = re.compile(r"juniper-model-core(?:\[[^\]]+\])?\s*>=\s*([0-9]+(?:\.[0-9]+)+)\s*,\s*<\s*([0-9]+(?:\.[0-9]+)+)")

# How many minor versions back is still "supported" before a soft warning.
_SUPPORTED_MINORS_BACK = 2

# Consumer repos that pin juniper-model-core, as ``(repo_dir, pyproject_relpath)``. The
# relpath points at the *consuming package's* pyproject within the repo (which may be nested),
# so a multi-package repo only has its real consumer checked. cascor (WS-6) joins here later.
_CONSUMER_REPOS: tuple[tuple[str, str], ...] = (
    # The WS-4b recurrence app drives POST /v1/crossval and pins model-core's [crossval] extra.
    # Its pin lives in the nested app package, NOT the repo root, and NOT in
    # juniper-recurrence-model/ (the model deliberately stays on the 0.1.x contract).
    ("juniper-recurrence", "juniper-recurrence/pyproject.toml"),
)


def _parse_version(v: str) -> tuple[int, ...]:
    """Convert "0.1.0" -> (0, 1, 0). Ignores any pre-release/build tags."""
    parts = v.split(".")
    return tuple(int(p.split("-")[0].split("+")[0]) for p in parts)


def _read_current_version(juniper_ml_root: Path) -> str | None:
    """Read the current juniper-model-core version from its ``_version.py`` (the
    dynamic-version source of truth). Returns None if not locatable (test skips)."""
    version_file = juniper_ml_root / "juniper-model-core" / "juniper_model_core" / "_version.py"
    if not version_file.exists():
        return None
    for line in version_file.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^__version__\s*=\s*"([^"]+)"\s*$', line.strip())
        if m:
            return m.group(1)
    return None


def _extract_pins_from_text(text: str) -> list[tuple[str, str]]:
    """Find every ``juniper-model-core>=X,<Y`` reference; returns (lower, upper) tuples."""
    return [(m.group(1), m.group(2)) for m in _PIN_PATTERN.finditer(text)]


def _read_tools_pins(juniper_ml_root: Path) -> list[tuple[str, str]]:
    """Extract the juniper-model-core pin(s) from juniper-ml's ``[tools]`` extra."""
    pyproject = juniper_ml_root / "pyproject.toml"
    if not pyproject.exists():
        return []
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    tools = data.get("project", {}).get("optional-dependencies", {}).get("tools", [])
    pins: list[tuple[str, str]] = []
    for entry in tools:
        pins.extend(_extract_pins_from_text(entry))
    return pins


def _find_ecosystem_root(juniper_ml_root: Path) -> Path | None:
    """Walk up looking for a directory holding the known consumer siblings. Returns
    None when there are no declared consumers (the dormant state)."""
    if not _CONSUMER_REPOS:
        return None
    known = {repo for repo, _ in _CONSUMER_REPOS}
    for candidate in (juniper_ml_root.parent, juniper_ml_root.parent.parent):
        try:
            found = sum(1 for repo in known if (candidate / repo).is_dir())
        except OSError:
            continue
        if found >= 1:
            return candidate
    return None


class JuniperModelCoreDriftTest(unittest.TestCase):
    """Assert juniper-ml's ``[tools]`` pin (and, later, consumer pins) still admit
    the current juniper-model-core version."""

    @classmethod
    def setUpClass(cls):
        cls.juniper_ml_root = Path(__file__).resolve().parent.parent
        cls.current_version = _read_current_version(cls.juniper_ml_root)
        cls.ecosystem_root = _find_ecosystem_root(cls.juniper_ml_root)

    def test_current_version_is_readable(self):
        self.assertIsNotNone(
            self.current_version,
            ("Could not read juniper-model-core version from " "juniper-model-core/juniper_model_core/_version.py."),
        )

    def test_juniper_ml_tools_pin_admits_current(self):
        """juniper-ml's own [tools] pin must accept the current model-core version.
        Catches a model-core minor bump (in this same repo) not accompanied by a pin
        bump."""
        if self.current_version is None:
            self.skipTest("no current version available")
        pins = _read_tools_pins(self.juniper_ml_root)
        self.assertEqual(
            len(pins),
            1,
            f"expected exactly one juniper-model-core pin in juniper-ml's [tools] extra; found {pins}. Keep pyproject.toml and this lint in lockstep (RK-11).",
        )
        current_tuple = _parse_version(self.current_version)
        lower, upper = pins[0]
        self.assertLessEqual(
            _parse_version(lower),
            current_tuple,
            f"[tools] pin lower bound {lower} is ahead of current {self.current_version}",
        )
        self.assertLess(
            current_tuple,
            _parse_version(upper),
            f"[tools] pin upper bound {upper} excludes current {self.current_version} -- bump the pin",
        )

    def test_consumer_repos_pin_current_version(self):
        """Dormant until model-core has consumers (recurrence WS-4 / cascor WS-6).
        When ``_CONSUMER_REPOS`` is populated, reads each consumer's pyproject.toml
        and asserts its juniper-model-core pin admits the current version."""
        if not _CONSUMER_REPOS:
            self.skipTest("no juniper-model-core consumers yet (recurrence WS-4 / cascor WS-6)")
        if self.ecosystem_root is None:
            self.skipTest("ecosystem siblings not on disk")
        if self.current_version is None:
            self.skipTest("no current version available")
        if os.environ.get("GITHUB_ACTIONS") != "true" and not os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL"):
            self.skipTest("skipping local cross-repo lint (set JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 to override)")

        current_tuple = _parse_version(self.current_version)
        warnings: list[str] = []
        for repo, relpath in _CONSUMER_REPOS:
            with self.subTest(repo=repo):
                pyproject = self.ecosystem_root / repo / relpath
                if not pyproject.exists():
                    print(f"WARN: {repo}/{relpath} not present (clone failure?)")
                    continue
                pins = _extract_pins_from_text(pyproject.read_text(encoding="utf-8"))
                if not pins:
                    self.fail(f"{repo}/{relpath} has no juniper-model-core pin")
                for lower, upper in pins:
                    upper_tuple = _parse_version(upper)
                    self.assertLessEqual(
                        _parse_version(lower),
                        current_tuple,
                        f"{repo} pin lower bound {lower} is ahead of current {self.current_version}",
                    )
                    if upper_tuple[0] == current_tuple[0] and upper_tuple[1] - current_tuple[1] - 1 > _SUPPORTED_MINORS_BACK:
                        warnings.append(f"{repo}: pin {lower}..{upper} is more than {_SUPPORTED_MINORS_BACK} minors behind current {self.current_version}")
                    self.assertLess(
                        current_tuple,
                        upper_tuple,
                        f"{repo} pin upper bound {upper} excludes current {self.current_version} -- bump the pin in {repo}.",
                    )

        if warnings:
            print("=== juniper-model-core pin drift warnings ===", file=sys.stderr)
            for w in warnings:
                print(f"  {w}", file=sys.stderr)


class PinParsingHelperTest(unittest.TestCase):
    """Direct unit tests for the helpers (independent of the integration test)."""

    def test_extracts_simple_pin(self):
        self.assertEqual(_extract_pins_from_text('"juniper-model-core>=0.1.0,<0.2.0"'), [("0.1.0", "0.2.0")])

    def test_extracts_pin_with_extra(self):
        # the recurrence app pins the [crossval] extra: juniper-model-core[crossval]>=0.2.0,<0.3.0
        self.assertEqual(_extract_pins_from_text('"juniper-model-core[crossval]>=0.2.0,<0.3.0"'), [("0.2.0", "0.3.0")])

    def test_ignores_unrelated_pins(self):
        self.assertEqual(_extract_pins_from_text('"juniper-doc-tools>=0.1.0,<0.2.0"'), [])

    def test_consumer_repos_are_repo_relpath_pairs(self):
        for entry in _CONSUMER_REPOS:
            self.assertEqual(len(entry), 2, f"each _CONSUMER_REPOS entry is (repo_dir, pyproject_relpath); got {entry!r}")
            _repo, relpath = entry
            self.assertTrue(relpath.endswith("pyproject.toml"), f"relpath should point at a pyproject.toml, got {relpath!r}")

    def test_parses_versions(self):
        self.assertEqual(_parse_version("0.1.0"), (0, 1, 0))
        self.assertEqual(_parse_version("0.10.0"), (0, 10, 0))
        self.assertEqual(_parse_version("1.2.3-rc1"), (1, 2, 3))

    def test_supported_window_constant(self):
        self.assertEqual(_SUPPORTED_MINORS_BACK, 2)


if __name__ == "__main__":
    unittest.main()
