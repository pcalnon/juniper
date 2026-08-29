"""Selection-metadata lint for the custom-agent template library.

Validates that ``manifest.yaml``'s ``match_signals`` are coherent enough for the Template
Agent (PR 5) to select a category deterministically: exactly one always-match fallback
(``generic``), every other template carries non-empty keyword signals, no two templates
share an identical keyword set (which would make selection ambiguous), and every ``class``
is from the allowed set.

Companion to ``tests/test_template_library_drift.py``; both are the sole gate for
``prompts/agent_templates/`` because ``prompts/**`` is excluded from all pre-commit hooks, so this
test MUST stay wired into ``.github/workflows/ci.yml``.

Design-of-record: ``notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md`` (S5.4).
Location-agnostic: discovers the repo root by walking up for ``.github/workflows/``.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

# Allowed template classes. `class` gates rubric checks (e.g. R2.6 verification-&-
# recoverability applies to execution-class templates only).
_ALLOWED_CLASSES = {"generic", "execution", "analysis", "planning", "review"}


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


class TemplateSelectionTest(unittest.TestCase):
    """manifest.yaml match_signals must support deterministic category selection."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.manifest_path = cls.repo_root / "prompts" / "agent_templates" / "manifest.yaml"
        cls.manifest = yaml.safe_load(cls.manifest_path.read_text(encoding="utf-8")) if cls.manifest_path.exists() else None

    def setUp(self):
        if self.manifest is None:
            self.skipTest("manifest.yaml absent")
        self.templates = self.manifest["templates"]

    def test_exactly_one_always_match_and_it_is_generic(self):
        always = [t for t in self.templates if t.get("match_signals", {}).get("always") is True]
        self.assertEqual(len(always), 1, f"exactly one always-match template required, found {[t['id'] for t in always]}")
        self.assertEqual(always[0]["id"], "generic", "the always-match template must be 'generic'")
        self.assertEqual(always[0]["class"], "generic")

    def test_non_generic_templates_have_keyword_signals(self):
        for t in self.templates:
            if t["id"] == "generic":
                continue
            ms = t.get("match_signals", {})
            kw = ms.get("keywords")
            self.assertIsInstance(kw, list, f"{t['id']}: match_signals.keywords must be a list")
            self.assertTrue(kw, f"{t['id']}: match_signals.keywords must be non-empty")
            self.assertTrue(all(isinstance(k, str) and k for k in kw), f"{t['id']}: keywords must be non-empty strings")
            self.assertNotEqual(ms.get("always"), True, f"{t['id']}: only 'generic' may set always:true")

    def test_no_duplicate_keyword_sets(self):
        seen = {}
        for t in self.templates:
            if t["id"] == "generic":
                continue
            key = frozenset(k.lower() for k in t["match_signals"]["keywords"])
            self.assertNotIn(key, seen, f"templates '{seen.get(key)}' and '{t['id']}' have identical keyword sets -> ambiguous selection")
            seen[key] = t["id"]

    def test_all_classes_allowed(self):
        for t in self.templates:
            self.assertIn(t["class"], _ALLOWED_CLASSES, f"{t['id']}: class '{t['class']}' not in {sorted(_ALLOWED_CLASSES)}")

    def test_optional_signal_fields_well_typed(self):
        for t in self.templates:
            ms = t.get("match_signals", {})
            if "discovery" in ms:
                self.assertIsInstance(ms["discovery"], list, f"{t['id']}: match_signals.discovery must be a list")
            if "variants" in ms:
                self.assertIsInstance(ms["variants"], dict, f"{t['id']}: match_signals.variants must be a dict")


if __name__ == "__main__":
    unittest.main()
