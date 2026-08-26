"""Drift-lint for the Juniper custom-agent template library (``prompts/agent_templates/``).

Enforces manifest <-> template consistency so the library cannot silently drift:
every registered template exists and every template is registered; every template
follows the canonical section skeleton (in order); every ``{{placeholder}}`` uses the
systematic convention; the ``generic`` fallback always matches.

This is the **sole gate** for the library because ``prompts/**`` is excluded from all
pre-commit hooks (``.pre-commit-config.yaml`` global ``exclude``), so this test MUST
stay wired into ``.github/workflows/ci.yml``'s regression-test list.

Design-of-record: ``notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md`` (S5.4, S9).

Location-agnostic: discovers the repo root by walking up for ``.github/workflows/`` so
the file can live anywhere in any Juniper repo's ``tests/`` directory. PR 2a ships the
scaffold + the ``generic`` fallback; PR 2b adds the six category templates + ``RUBRIC.md``.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

# --- canonical placeholder convention (the contract this test enforces) ----------
#   {{NAME}}          fill slot      (NAME is UPPER_SNAKE)
#   {{!NAME: hint}}   REQUIRED slot  (must be filled before the prompt is valid)
#   {{?NAME: hint}}   OPTIONAL slot  (may be dropped)
_PLACEHOLDER_TOKEN = re.compile(r"\{\{.*?\}\}")
_FILL_RE = re.compile(r"^\{\{[A-Z][A-Z0-9_]*\}\}$")
_REQUIRED_RE = re.compile(r"^\{\{![A-Z][A-Z0-9_]*:\s.+\}\}$")
_OPTIONAL_RE = re.compile(r"^\{\{\?[A-Z][A-Z0-9_]*:\s.+\}\}$")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# Every criterion ID RUBRIC.md must declare, so a validation check can't be silently
# dropped (the rubric is the prompt-validator's contract -- design S5.5). Lands in PR 2b-i.
_EXPECTED_RUBRIC_IDS = [
    "R1.1",
    "R1.2",
    "R1.3",
    "R1.4",
    "R2.0",
    "R2.1",
    "R2.2",
    "R2.3",
    "R2.4",
    "R2.5",
    "R2.6",
    "R3.1",
    "R3.2",
    "R3.3",
    "R3.4",
    "R3.4a",
    "R3.4b",
    "R3.4c",
    "R3.4d",
    "R3.4e",
    "R3.5",
    "R4",
    "R5",
]

# Library meta-files under prompts/agent_templates/ that are NOT templates (excluded from the
# orphan check). Every OTHER *.md must be registered in manifest.yaml.
_NON_TEMPLATE_MD = {"README.md", "RUBRIC.md"}


def _strip_html_comments(text: str) -> str:
    """Remove HTML comments so example placeholders/headings inside a comment block
    do not count toward the structural checks."""
    return _HTML_COMMENT.sub("", text)


def _classify_placeholder(token: str) -> str | None:
    if _FILL_RE.match(token):
        return "fill"
    if _REQUIRED_RE.match(token):
        return "required"
    if _OPTIONAL_RE.match(token):
        return "optional"
    return None


def _find_placeholders(text: str) -> list[str]:
    return _PLACEHOLDER_TOKEN.findall(text)


def _ordered_heading_indices(text: str, headings: list[str]) -> dict[str, int]:
    """Map each heading to the line index of its first exact-line occurrence; -1 if absent."""
    lines = [ln.strip() for ln in text.splitlines()]
    return {h: (lines.index(h) if h in lines else -1) for h in headings}


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


class TemplateLibraryDriftTest(unittest.TestCase):
    """manifest.yaml <-> prompts/agent_templates/*.md must stay consistent."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.templates_dir = cls.repo_root / "prompts" / "agent_templates"
        cls.manifest_path = cls.templates_dir / "manifest.yaml"
        cls.manifest = yaml.safe_load(cls.manifest_path.read_text(encoding="utf-8")) if cls.manifest_path.exists() else None

    def setUp(self):
        if self.manifest is None:
            self.skipTest(f"no template library at {self.templates_dir} (manifest.yaml absent)")

    # -- structure ---------------------------------------------------------------
    def test_templates_dir_exists(self):
        self.assertTrue(self.templates_dir.is_dir(), f"missing {self.templates_dir}")

    def test_manifest_has_core_keys(self):
        for key in ("version", "skeleton", "placeholders", "templates"):
            self.assertIn(key, self.manifest, f"manifest.yaml missing top-level '{key}'")
        self.assertIsInstance(self.manifest["version"], int)
        self.assertIn("required", self.manifest["skeleton"])
        self.assertIsInstance(self.manifest["skeleton"]["required"], list)
        self.assertTrue(self.manifest["templates"], "manifest declares no templates")

    # -- manifest <-> files ------------------------------------------------------
    def test_every_registered_template_file_exists(self):
        missing = [t["file"] for t in self.manifest["templates"] if not (self.templates_dir / t["file"]).exists()]
        self.assertEqual(missing, [], f"manifest references missing template file(s): {missing}")

    def test_no_orphan_template_files(self):
        registered = {t["file"] for t in self.manifest["templates"]}
        on_disk = {p.name for p in self.templates_dir.glob("*.md") if p.name not in _NON_TEMPLATE_MD}
        orphans = sorted(on_disk - registered)
        self.assertEqual(orphans, [], f"template file(s) on disk but not registered in manifest.yaml: {orphans}")

    def test_each_template_entry_has_required_keys(self):
        required_keys = {"id", "title", "when_to_use", "match_signals", "file", "class"}
        for t in self.manifest["templates"]:
            missing = required_keys - set(t)
            self.assertEqual(missing, set(), f"template '{t.get('id', '?')}' missing manifest keys: {missing}")

    # -- skeleton ----------------------------------------------------------------
    def test_every_template_follows_canonical_skeleton(self):
        required = self.manifest["skeleton"]["required"]
        optional = self.manifest["skeleton"].get("optional", [])
        order = required + optional
        for t in self.manifest["templates"]:
            text = _strip_html_comments((self.templates_dir / t["file"]).read_text(encoding="utf-8"))
            first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
            self.assertTrue(first.startswith("# "), f"{t['file']}: first non-empty line must be an H1 title, got {first!r}")
            idx = _ordered_heading_indices(text, order)
            for h in required:
                self.assertGreaterEqual(idx[h], 0, f"{t['file']}: missing required section '{h}'")
            present = [idx[h] for h in order if idx[h] >= 0]
            self.assertEqual(present, sorted(present), f"{t['file']}: sections out of canonical skeleton order")

    # -- placeholders ------------------------------------------------------------
    def test_every_placeholder_is_well_formed(self):
        bad = []
        for t in self.manifest["templates"]:
            text = _strip_html_comments((self.templates_dir / t["file"]).read_text(encoding="utf-8"))
            for token in _find_placeholders(text):
                if _classify_placeholder(token) is None:
                    bad.append((t["file"], token))
        self.assertEqual(bad, [], "malformed placeholder(s) -- must be {{NAME}} / {{!NAME: hint}} / {{?NAME: hint}}: " + repr(bad))

    # -- generic fallback --------------------------------------------------------
    def test_generic_fallback_registered_and_always_matches(self):
        gen = [t for t in self.manifest["templates"] if t.get("id") == "generic"]
        self.assertEqual(len(gen), 1, "exactly one 'generic' template must be registered")
        self.assertEqual(gen[0].get("class"), "generic")
        self.assertIs(gen[0].get("match_signals", {}).get("always"), True, "generic must declare match_signals.always: true")

    # -- rubric cross-check (becomes meaningful in PR 2b) ------------------------
    def test_rubric_is_non_trivial_when_present(self):
        rubric = self.templates_dir / "RUBRIC.md"
        if rubric.exists():
            self.assertGreater(len(rubric.read_text(encoding="utf-8").strip()), 200, "RUBRIC.md looks empty/stub")

    def test_rubric_declares_all_criteria_when_present(self):
        rubric = self.templates_dir / "RUBRIC.md"
        if not rubric.exists():
            self.skipTest("RUBRIC.md not present yet (lands in PR 2b-i)")
        text = rubric.read_text(encoding="utf-8")
        missing = [rid for rid in _EXPECTED_RUBRIC_IDS if rid not in text]
        self.assertEqual(missing, [], f"RUBRIC.md is missing criterion ID(s): {missing}")


class PlaceholderClassifierTest(unittest.TestCase):
    """Direct unit tests for the placeholder helpers."""

    def test_fill(self):
        self.assertEqual(_classify_placeholder("{{CATEGORY_TITLE}}"), "fill")
        self.assertEqual(_classify_placeholder("{{APPLICATION}}"), "fill")

    def test_required(self):
        self.assertEqual(_classify_placeholder("{{!ROLE: adopt an expert role}}"), "required")
        self.assertEqual(_classify_placeholder("{{!RESOURCES: real file:line anchors}}"), "required")

    def test_optional(self):
        self.assertEqual(_classify_placeholder("{{?CONSTRAINTS: hard limits}}"), "optional")

    def test_malformed(self):
        for bad in ("{{lowercase}}", "{{!NOHINT}}", "{{ SPACED }}", "{{123}}", "{{!: x}}", "{{?ONLYNAME}}"):
            self.assertIsNone(_classify_placeholder(bad), f"{bad!r} should be classified malformed")

    def test_find_placeholders(self):
        self.assertEqual(_find_placeholders("a {{X}} b {{!Y: z}} c {{?W: v}}"), ["{{X}}", "{{!Y: z}}", "{{?W: v}}"])

    def test_strip_html_comments(self):
        self.assertEqual(_strip_html_comments("a<!-- {{!BAD}} -->b").strip(), "ab")


if __name__ == "__main__":
    unittest.main()
