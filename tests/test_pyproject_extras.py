"""Lint test: pyproject.toml advertises the expected set of optional
dependency groups, each containing the expected packages, and ``[all]``
recursively bundles every other extra exactly once.

Catches the failure class where an edit to ``[project.optional-dependencies]``
silently drops, mistypes, or fails to roll up an extra. The PR that added
``[servers]`` + ``[tools]`` (juniper-ml#295) had no regression coverage for
this surface; one accidental deletion of ``servers`` from ``[all]`` would
have shipped without test failure.

The test is intentionally schema-strict (asserts the exact set of extras +
the exact set of packages per extra), so adding a new extra requires
updating this file in the same PR. That gate is the point of the lint.
"""

from __future__ import annotations

import sys
import tomllib
import unittest
from pathlib import Path
from typing import Any, ClassVar


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "pyproject.toml").is_file() and (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate juniper-ml repo root from {here}")


_REPO = _repo_root()
_PYPROJECT = _REPO / "pyproject.toml"

# The canonical extras contract. Updating pyproject.toml without updating
# this table (or vice versa) is the failure mode this lint catches.
EXPECTED_EXTRAS = {
    "clients": {
        "juniper-data-client>=0.4.1",
        "juniper-cascor-client>=0.5.0",
    },
    "worker": {
        "juniper-cascor-worker>=0.4.0",
    },
    "servers": {
        "juniper-canopy>=0.5.0",
        "juniper-cascor>=0.5.0",
        "juniper-data>=0.6.0",
    },
    "tools": {
        "juniper-ci-tools>=0.1.0",
        "juniper-config-tools>=0.1.0,<0.2.0",
        "juniper-doc-tools>=0.1.0,<0.2.0",
        "juniper-model-core>=0.1.0,<0.4.0",
        "juniper-observability>=0.2.0",
        "juniper-service-core>=0.2.0,<0.6.0",
    },
    "doc-tools": {
        "juniper-doc-tools>=0.1.0,<0.2.0",
    },
    "recurrence": {
        "juniper-recurrence-model>=0.1.5,<0.3.0",
        "juniper-recurrence>=0.2.0,<0.4.0",
        "juniper-recurrence-client>=0.2.0,<0.3.0",
    },
    "all": {
        "juniper-ml[clients,worker,servers,tools,recurrence]",
    },
}


class PyprojectExtrasTest(unittest.TestCase):
    """Pin the optional-dependency surface so accidental edits fail loudly."""

    pyproject: ClassVar[dict[str, Any]]
    extras: ClassVar[dict[str, list[str]]]

    @classmethod
    def setUpClass(cls) -> None:
        if sys.version_info < (3, 11):
            raise unittest.SkipTest("tomllib requires Python 3.11+")
        with _PYPROJECT.open("rb") as handle:
            cls.pyproject = tomllib.load(handle)
        cls.extras = cls.pyproject["project"].get("optional-dependencies", {})

    def test_expected_extras_present(self) -> None:
        self.assertEqual(
            set(self.extras.keys()),
            set(EXPECTED_EXTRAS.keys()),
            "pyproject.toml extras set drifted from the lint contract; " "update tests/test_pyproject_extras.py in the same PR as the " "pyproject change so reviewers see the diff.",
        )

    def test_each_extra_has_expected_members(self) -> None:
        for name, expected in EXPECTED_EXTRAS.items():
            with self.subTest(extra=name):
                self.assertEqual(
                    set(self.extras[name]),
                    expected,
                    f"[{name}] member set drifted from the lint contract",
                )

    def test_all_bundles_every_non_all_extra(self) -> None:
        """`[all]` must list every other extra (except itself and the
        back-compat `[doc-tools]` alias, which is already covered by the
        doc-tools member of `[tools]`)."""
        non_all = {n for n in EXPECTED_EXTRAS if n not in {"all", "doc-tools"}}
        (all_recursive_ref,) = self.extras["all"]
        # Parse "juniper-ml[a,b,c]" -> {"a","b","c"}
        self.assertTrue(
            all_recursive_ref.startswith("juniper-ml[") and all_recursive_ref.endswith("]"),
            f"Unexpected [all] recursive ref shape: {all_recursive_ref!r}",
        )
        inner = all_recursive_ref[len("juniper-ml[") : -1]
        referenced = {token.strip() for token in inner.split(",")}
        self.assertEqual(
            referenced,
            non_all,
            "[all] must aggregate every non-alias extra exactly once",
        )

    def test_version_is_semver_ish(self) -> None:
        version = self.pyproject["project"]["version"]
        # X.Y.Z, optionally with a pre-release/build suffix
        parts = version.split(".")
        self.assertGreaterEqual(len(parts), 3, f"version {version!r} is not X.Y.Z[.…]")
        for part in parts[:3]:
            head = part.split("-", 1)[0].split("+", 1)[0]
            self.assertTrue(head.isdigit(), f"version component {part!r} (from {version!r}) is not numeric")


if __name__ == "__main__":
    unittest.main()
