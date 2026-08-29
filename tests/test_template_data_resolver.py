"""Tests + drift gate for the custom-agent suite data layer (PR 6b).

Validates that ``prompts/agent_templates/data/*.yaml`` load, that ``util/template_data_resolver.py``'s
loader + dotted ``resolve()`` work, and -- as a drift gate -- that a couple of canonical
convention values (line-length, the handoff threshold) still match repo reality, since
RUBRIC R2.5 treats this layer as the source of truth for injected conventions.

``prompts/**`` is excluded from all pre-commit hooks, so this unittest is the sole gate for
the data layer. Location-agnostic: walks up for ``.github/workflows/``.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

import yaml


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_RESOLVER = _REPO_ROOT / "util" / "template_data_resolver.py"
_DATA_DIR = _REPO_ROOT / "prompts" / "agent_templates" / "data"
_EXPECTED_FILES = ("standing_rules", "anti_hallucination", "conventions", "ecosystem", "known_misses")


def _load_mod():
    spec = importlib.util.spec_from_file_location("template_data_resolver", _RESOLVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TemplateDataResolverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_mod()

    def test_resolver_exists(self):
        self.assertTrue(_RESOLVER.exists(), f"missing {_RESOLVER}")

    def test_all_data_files_present_and_valid(self):
        for name in _EXPECTED_FILES:
            path = _DATA_DIR / f"{name}.yaml"
            self.assertTrue(path.exists(), f"missing data file {path}")
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertIsInstance(data, dict, f"{name}.yaml must be a mapping")
            self.assertIn("version", data, f"{name}.yaml must declare a version")

    def test_load_returns_all_keys(self):
        data = self.mod.load(str(_REPO_ROOT))
        self.assertEqual(set(data), set(_EXPECTED_FILES))

    def test_resolve_dotted(self):
        self.assertEqual(self.mod.resolve("conventions.line_length", str(_REPO_ROOT)), 512)
        self.assertEqual(self.mod.resolve("conventions.handoff_threshold", str(_REPO_ROOT)), "95-99%")
        self.assertEqual(self.mod.resolve("ecosystem.service_ports.juniper-data.host", str(_REPO_ROOT)), 8100)

    def test_resolve_missing_returns_default(self):
        self.assertEqual(self.mod.resolve("nope.not.here", str(_REPO_ROOT), default="X"), "X")

    def test_known_misses_shape(self):
        misses = self.mod.resolve("known_misses.misses", str(_REPO_ROOT))
        self.assertIsInstance(misses, list)
        for entry in misses:
            for key in ("date", "claim", "reality"):
                self.assertIn(key, entry)

    def test_line_length_matches_markdownlint(self):
        md = yaml.safe_load((_REPO_ROOT / ".markdownlint.yaml").read_text(encoding="utf-8"))
        markdown_len = md.get("line-length", {}).get("line_length")
        self.assertEqual(
            self.mod.resolve("conventions.line_length", str(_REPO_ROOT)),
            markdown_len,
            "data-layer conventions.line_length drifted from .markdownlint.yaml",
        )

    def test_handoff_threshold_is_current(self):
        threshold = str(self.mod.resolve("conventions.handoff_threshold", str(_REPO_ROOT)))
        self.assertIn("95", threshold, "handoff threshold must reflect the current 95-99% policy")
        self.assertNotIn("80", threshold, "handoff threshold looks stale (80%)")

    def test_cli_resolve(self):
        ok = subprocess.run(
            [sys.executable, str(_RESOLVER), "conventions.line_length"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(ok.stdout.strip(), "512")
        miss = subprocess.run(
            [sys.executable, str(_RESOLVER), "no.such.key"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(miss.returncode, 1)


if __name__ == "__main__":
    unittest.main()
