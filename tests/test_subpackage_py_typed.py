#!/usr/bin/env python3
"""Structural gate: every published sub-package ships a PEP 561 ``py.typed`` marker.

Closes ``APD-SVCCORE-008`` and ``APD-OBS-002`` in the ecosystem defect register,
and the four unrecorded siblings the register never filed -- all six in-repo
sub-packages were affected, not the two on the books.

Without the marker a consumer's type checker refuses to read the package at all::

    error: Skipping analyzing "juniper_service_core.auth_posture": module is
    installed, but missing library stubs or py.typed marker  [import-untyped]

Every annotation is then discarded and every symbol degrades to ``Any``, so a
consumer calling ``enforce_auth_posture(keys, require_auth="yes")`` -- a ``str``
where a ``bool`` is declared -- type-checks clean. The annotations exist
(service-core alone carries 310+ annotated defs plus a 75-line ``TYPE_CHECKING``
block); nothing was reading them.

**Two independent things must both hold, which is why this gate checks both.**
The marker file existing in the repo does *not* mean it reaches consumers:
setuptools ships it only if it is also declared as package data, and these
packages carry no ``MANIFEST.in``. A gate that checked only the file would go
green while every wheel shipped without it -- the vacuous-pass class.

``test_package_data_does_not_swallow_packages_find_keys`` guards a regression
observed while authoring this change: ``[tool.setuptools.package-data]`` was
inserted between ``packages.find``'s ``include`` and ``exclude`` keys, silently
re-homing ``exclude = ["tests*"]`` into the new table and packaging
``juniper-model-core``'s test suite into its wheel. Both tables stay valid TOML,
so nothing failed -- only reading the parsed result showed it.

Run: python3 -m unittest -v tests/test_subpackage_py_typed.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-21
"""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path
from typing import Any

# The six published in-repo sub-packages. Discovery below is by glob so a
# seventh is covered automatically; this set exists purely to prove the glob
# found something real -- an empty discovery would pass every other test here
# vacuously.
EXPECTED_SUBPACKAGES: frozenset[str] = frozenset(
    {
        "juniper-ci-tools",
        "juniper-config-tools",
        "juniper-doc-tools",
        "juniper-model-core",
        "juniper-observability",
        "juniper-service-core",
    }
)

TYPED_CLASSIFIER = "Typing :: Typed"

# Keys that belong to [tool.setuptools.packages.find]; finding one inside
# [tool.setuptools.package-data] means a table header was inserted mid-table.
PACKAGES_FIND_KEYS: frozenset[str] = frozenset({"include", "exclude", "where", "namespaces"})


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


def _import_name(subdir: Path) -> str:
    """``juniper-service-core`` -> ``juniper_service_core``."""
    return subdir.name.replace("-", "_")


class PyTypedMarkerTests(unittest.TestCase):
    """Each sub-package must both contain and publish its ``py.typed`` marker."""

    repo_root: Path
    subdirs: list[Path]
    parsed: dict[str, dict[str, Any]]

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.subdirs = sorted(p.parent for p in cls.repo_root.glob("juniper-*/pyproject.toml"))
        cls.parsed = {d.name: tomllib.loads((d / "pyproject.toml").read_text(encoding="utf-8")) for d in cls.subdirs}

    def test_discovery_is_not_vacuous(self) -> None:
        """Anti-vacuous guard: every other test here loops over this set."""
        found = {d.name for d in self.subdirs}
        self.assertTrue(found, "no juniper-*/pyproject.toml found -- every other assertion here would pass vacuously")
        missing = EXPECTED_SUBPACKAGES - found
        self.assertFalse(missing, f"known sub-packages not discovered: {sorted(missing)}")

    def test_every_subpackage_ships_a_py_typed_marker(self) -> None:
        for subdir in self.subdirs:
            with self.subTest(package=subdir.name):
                marker = subdir / _import_name(subdir) / "py.typed"
                self.assertTrue(
                    marker.is_file(),
                    f"{subdir.name}: missing PEP 561 marker at {marker.relative_to(self.repo_root)} -- " "consumers will see [import-untyped] and discard every annotation",
                )

    def test_every_subpackage_declares_py_typed_as_package_data(self) -> None:
        """The file alone is not enough: undeclared, setuptools omits it from the wheel."""
        for subdir in self.subdirs:
            with self.subTest(package=subdir.name):
                pkg = _import_name(subdir)
                package_data = self.parsed[subdir.name].get("tool", {}).get("setuptools", {}).get("package-data", {})
                self.assertIn(
                    pkg,
                    package_data,
                    f"{subdir.name}: [tool.setuptools.package-data] does not declare '{pkg}' -- " "the marker exists in the repo but never reaches a wheel (no MANIFEST.in here)",
                )
                self.assertIn(
                    "py.typed",
                    package_data[pkg],
                    f"{subdir.name}: '{pkg}' package-data does not list py.typed",
                )

    def test_every_subpackage_declares_the_typed_classifier(self) -> None:
        for subdir in self.subdirs:
            with self.subTest(package=subdir.name):
                classifiers = self.parsed[subdir.name].get("project", {}).get("classifiers", [])
                self.assertIn(
                    TYPED_CLASSIFIER,
                    classifiers,
                    f"{subdir.name}: missing the '{TYPED_CLASSIFIER}' classifier",
                )

    def test_package_data_does_not_swallow_packages_find_keys(self) -> None:
        """A table header inserted mid-table silently re-homes the keys below it."""
        for subdir in self.subdirs:
            with self.subTest(package=subdir.name):
                setuptools_cfg = self.parsed[subdir.name].get("tool", {}).get("setuptools", {})
                package_data = setuptools_cfg.get("package-data", {})
                strays = PACKAGES_FIND_KEYS & set(package_data)
                self.assertFalse(
                    strays,
                    f"{subdir.name}: {sorted(strays)} appears under [tool.setuptools.package-data] -- " "it belongs to [tool.setuptools.packages.find]; a table header was inserted mid-table, " "so packaging discovery silently lost it",
                )


if __name__ == "__main__":
    unittest.main()
