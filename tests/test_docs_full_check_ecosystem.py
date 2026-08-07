#!/usr/bin/env python3
"""Lockstep gate: docs-full-check.yml ECOSYSTEM_REPOS vs release-train registry.

Weekly ``docs-full-check.yml`` clones sibling repos for cross-repo doc-link
validation, consumer pin lint, downstream integration, and the L2/L3
``claude.yml`` audit. Omitting a publishing sibling (the historical
``juniper-recurrence`` gap called out in ``util/release_train/registry.yaml``)
silently drops that repo from every weekly cross-repo screen.

This unittest parses ``docs-full-check.yml`` with PyYAML and asserts
``env.ECOSYSTEM_REPOS`` equals:

  (registry.yaml unique ``repo`` values − {juniper-ml}) ∪ {juniper-deploy}

- Publishing siblings come from the release-train registry (S4.1 source of truth).
- ``juniper-ml`` is the workflow checkout, never an ECOSYSTEM_REPOS clone.
- ``juniper-deploy`` hosts no PyPI package but is intentionally cloned for
  doc / claude.yml coverage (release-train deliberately excludes it).

Companion: ``tests/test_release_train_workflow_guard.py`` pins the *release-train*
``ECOSYSTEM_REPOS`` (siblings only, no deploy). Workflow YAML is not otherwise
lint-gated for this property, so this unittest IS the gate.

Run: python3 -m unittest -v tests/test_docs_full_check_ecosystem.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-08-05
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

WORKFLOW_NAME = "docs-full-check.yml"
REGISTRY_REL = Path("util") / "release_train" / "registry.yaml"
# Doc/claude consumer with no PyPI package — allowed extra beyond registry siblings.
DOC_ONLY_EXTRA = frozenset({"juniper-deploy"})


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root: no .github/workflows/ above {start}")


def _multiline_repo_list(block: str) -> frozenset[str]:
    return frozenset(line.strip() for line in (block or "").splitlines() if line.strip())


class DocsFullCheckEcosystemReposTest(unittest.TestCase):
    """Pin docs-full-check ECOSYSTEM_REPOS membership against the registry."""

    repo_root: Path
    workflow_path: Path
    doc: dict
    registry_repos: frozenset[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.workflow_path = cls.repo_root / ".github" / "workflows" / WORKFLOW_NAME
        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
        cls.doc = yaml.safe_load(cls.workflow_path.read_text(encoding="utf-8"))
        registry_path = cls.repo_root / REGISTRY_REL
        if not registry_path.is_file():
            raise unittest.SkipTest(f"{REGISTRY_REL} not present")
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        packages = data.get("packages") or []
        cls.registry_repos = frozenset(str(pkg["repo"]) for pkg in packages if isinstance(pkg, dict) and pkg.get("repo"))
        if len(cls.registry_repos) < 2:
            raise unittest.SkipTest("registry.yaml did not resolve a non-trivial publishing-repo set")

    def test_registry_resolves_publishing_repos(self) -> None:
        self.assertGreaterEqual(len(self.registry_repos), 2)
        self.assertIn("juniper-ml", self.registry_repos)
        self.assertIn(
            "juniper-recurrence",
            self.registry_repos,
            "registry must list juniper-recurrence (the docs-full-check omission this gate closes)",
        )

    def test_ecosystem_repos_lockstep_with_registry_siblings_plus_deploy(self) -> None:
        expected = (self.registry_repos - {"juniper-ml"}) | DOC_ONLY_EXTRA
        block = (self.doc.get("env") or {}).get("ECOSYSTEM_REPOS")
        self.assertIsInstance(block, str, "workflow env.ECOSYSTEM_REPOS must be a multiline string")
        ecosystem = _multiline_repo_list(block)
        self.assertEqual(
            ecosystem,
            expected,
            "docs-full-check env.ECOSYSTEM_REPOS must equal registry publishing " "repos minus juniper-ml, plus juniper-deploy " f"(extra={sorted(ecosystem - expected)}, missing={sorted(expected - ecosystem)}).",
        )
        self.assertNotIn("juniper-ml", ecosystem, "juniper-ml is the workflow checkout, not an ECOSYSTEM_REPOS clone")
        self.assertIn(
            "juniper-recurrence",
            ecosystem,
            "juniper-recurrence must be cloned weekly (cross-repo links + ci-docs pin lint + downstream docs)",
        )
        self.assertIn("juniper-deploy", ecosystem, "juniper-deploy stays in the clone list for doc/claude coverage")


if __name__ == "__main__":
    unittest.main()
