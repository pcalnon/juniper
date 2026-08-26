"""Drift detection for the ``juniper-service-core`` pin in juniper-ml's
``[tools]`` extra (and, once they exist, in consumer repos).

Closest sibling to ``tests/test_model_core_drift.py``; both pin a *library*
dependency in juniper-ml's ``pyproject.toml`` ``[tools]`` extra (rather than a
CI-workflow ``pip install`` like the ``doc-tools`` / ``ci-tools`` drift lints).
Two notes specific to ``juniper-service-core``:

1. **Version source.** Unlike ``juniper-model-core`` (setuptools dynamic versioning
   from ``_version.py``), ``juniper-service-core`` declares a *static*
   ``[project].version`` in its own ``pyproject.toml`` -- so "current version" is
   read from there.
2. **Consumers.** The recurrence app consumes ``juniper-service-core`` (pins it in its app
   ``pyproject.toml`` ``dependencies``, ``>=0.3.0`` for the ``create_app(lifespan=)`` hook), so
   ``_CONSUMER_REPOS`` lists it and the cross-repo assertion below verifies that pin still admits
   the current version. recurrence is a *monorepo*, so the consumer path is the app subdir
   ``juniper-recurrence/juniper-recurrence`` (where the dependency lives), not the repo root.

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

# Pin-range pattern: juniper-service-core>=0.1.0,<0.2.0 (whitespace-forgiving).
_PIN_PATTERN = re.compile(r"juniper-service-core\s*>=\s*([0-9]+(?:\.[0-9]+)+)\s*,\s*<\s*([0-9]+(?:\.[0-9]+)+)")

# How many minor versions back is still "supported" before a soft warning.
_SUPPORTED_MINORS_BACK = 2

# Consumer paths (relative to the ecosystem root) that pin juniper-service-core in their own
# pyproject.toml. juniper-recurrence is a monorepo, so its consumer is the app subdir
# `juniper-recurrence/juniper-recurrence` (where the service-core dependency lives), not the repo
# root — `ecosystem_root / repo / "pyproject.toml"` resolves the slashed path correctly.
_CONSUMER_REPOS: tuple[str, ...] = ("juniper-recurrence/juniper-recurrence",)


def _parse_version(v: str) -> tuple[int, ...]:
    """Convert "0.1.0" -> (0, 1, 0). Ignores any pre-release/build tags."""
    parts = v.split(".")
    return tuple(int(p.split("-")[0].split("+")[0]) for p in parts)


def _read_current_version(juniper_ml_root: Path) -> str | None:
    """Read the current juniper-service-core version from its ``pyproject.toml``
    ``[project].version`` (service-core declares a static version). Returns None
    if not locatable (test skips)."""
    pyproject = juniper_ml_root / "juniper-service-core" / "pyproject.toml"
    if not pyproject.exists():
        return None
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    version = data.get("project", {}).get("version")
    return version if isinstance(version, str) else None


def _extract_pins_from_text(text: str) -> list[tuple[str, str]]:
    """Find every ``juniper-service-core>=X,<Y`` reference; returns (lower, upper) tuples."""
    return [(m.group(1), m.group(2)) for m in _PIN_PATTERN.finditer(text)]


def _read_tools_pins(juniper_ml_root: Path) -> list[tuple[str, str]]:
    """Extract the juniper-service-core pin(s) from juniper-ml's ``[tools]`` extra."""
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
    known = set(_CONSUMER_REPOS)
    for candidate in (juniper_ml_root.parent, juniper_ml_root.parent.parent):
        try:
            found = sum(1 for repo in known if (candidate / repo).is_dir())
        except OSError:
            continue
        if found >= 1:
            return candidate
    return None


class JuniperServiceCoreDriftTest(unittest.TestCase):
    """Assert juniper-ml's ``[tools]`` pin (and, later, consumer pins) still admit
    the current juniper-service-core version."""

    @classmethod
    def setUpClass(cls):
        cls.juniper_ml_root = Path(__file__).resolve().parent.parent
        cls.current_version = _read_current_version(cls.juniper_ml_root)
        cls.ecosystem_root = _find_ecosystem_root(cls.juniper_ml_root)

    def test_current_version_is_readable(self):
        self.assertIsNotNone(
            self.current_version,
            "Could not read juniper-service-core version from juniper-service-core/pyproject.toml [project].version.",
        )

    def test_juniper_ml_tools_pin_admits_current(self):
        """juniper-ml's own [tools] pin must accept the current service-core version.
        Catches a service-core minor bump (in this same repo) not accompanied by a
        pin bump."""
        if self.current_version is None:
            self.skipTest("no current version available")
        pins = _read_tools_pins(self.juniper_ml_root)
        self.assertEqual(
            len(pins),
            1,
            f"expected exactly one juniper-service-core pin in juniper-ml's [tools] extra; found {pins}. Keep pyproject.toml and this lint in lockstep (RK-11).",
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
        """For each consumer in ``_CONSUMER_REPOS``, read its pyproject.toml and assert its
        juniper-service-core pin still admits the current version. Skips when the ecosystem
        siblings are not on disk (juniper-ml's own CI does not clone them) or, locally, without
        ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1``."""
        if not _CONSUMER_REPOS:
            self.skipTest("no juniper-service-core consumers yet (recurrence app WS-4b)")
        if self.ecosystem_root is None:
            self.skipTest("ecosystem siblings not on disk")
        if self.current_version is None:
            self.skipTest("no current version available")
        if os.environ.get("GITHUB_ACTIONS") != "true" and not os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL"):
            self.skipTest("skipping local cross-repo lint (set JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 to override)")

        current_tuple = _parse_version(self.current_version)
        warnings: list[str] = []
        for repo in _CONSUMER_REPOS:
            with self.subTest(repo=repo):
                pyproject = self.ecosystem_root / repo / "pyproject.toml"
                if not pyproject.exists():
                    print(f"WARN: {repo}/pyproject.toml not present (clone failure?)")
                    continue
                pins = _extract_pins_from_text(pyproject.read_text(encoding="utf-8"))
                if not pins:
                    self.fail(f"{repo}/pyproject.toml has no juniper-service-core pin")
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
            print("=== juniper-service-core pin drift warnings ===", file=sys.stderr)
            for w in warnings:
                print(f"  {w}", file=sys.stderr)


class PinParsingHelperTest(unittest.TestCase):
    """Direct unit tests for the helpers (independent of the integration test)."""

    def test_extracts_simple_pin(self):
        self.assertEqual(_extract_pins_from_text('"juniper-service-core>=0.1.0,<0.2.0"'), [("0.1.0", "0.2.0")])

    def test_ignores_unrelated_pins(self):
        self.assertEqual(_extract_pins_from_text('"juniper-model-core>=0.1.0,<0.2.0"'), [])

    def test_parses_versions(self):
        self.assertEqual(_parse_version("0.1.0"), (0, 1, 0))
        self.assertEqual(_parse_version("0.10.0"), (0, 10, 0))
        self.assertEqual(_parse_version("1.2.3-rc1"), (1, 2, 3))

    def test_supported_window_constant(self):
        self.assertEqual(_SUPPORTED_MINORS_BACK, 2)


if __name__ == "__main__":
    unittest.main()
