"""Tests for util/scaffold_template.py (new-template generator, P5).

The headline check: a scaffolded template PASSES the library-drift contract -- validated by
reusing the real helpers from tests/test_template_library_drift.py (skeleton order +
placeholder well-formedness). Plus: refuse-on-collision, bad-class / missing-keywords exit 2,
--dry-run writes nothing, and the tool NEVER edits manifest.yaml (it prints the stanza).

util/ is not a package; modules are importlib-loaded. Location-agnostic.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_MODULE = _REPO_ROOT / "util" / "scaffold_template.py"
_DRIFT = _REPO_ROOT / "tests" / "test_template_library_drift.py"

_REQUIRED = ["## Role", "## Resources", "## Primary Objective", "## Assigned Tasks / Directives", "## Key Deliverables & Requirements"]
_OPTIONAL = ["## Constraints", "## Finalize / Validation"]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mk_repo(root: Path, with_manifest=False):
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / "prompts" / "agent_templates").mkdir(parents=True)
    if with_manifest:
        (root / "prompts" / "agent_templates" / "manifest.yaml").write_text("version: 1\ntemplates: []\n", encoding="utf-8")


class ScaffoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load("scaffold_template", _MODULE)
        cls.drift = _load("test_template_library_drift", _DRIFT)

    def _run(self, root, *args):
        return subprocess.run(
            [sys.executable, str(_MODULE), "--repo-root", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def test_generated_template_is_drift_compliant(self):
        text = self.mod.render_template("My New Category", "target")
        stripped = self.drift._strip_html_comments(text)
        first = next(ln.strip() for ln in stripped.splitlines() if ln.strip())
        self.assertTrue(first.startswith("# "), f"first non-empty line must be an H1, got {first!r}")
        # placeholders all well-formed per the convention
        for token in self.drift._find_placeholders(stripped):
            self.assertIsNotNone(self.drift._classify_placeholder(token), f"malformed placeholder: {token}")
        # required sections present and in canonical order; optional sections trail in order
        idx = self.drift._ordered_heading_indices(stripped, _REQUIRED + _OPTIONAL)
        for h in _REQUIRED:
            self.assertGreaterEqual(idx[h], 0, f"missing required section {h}")
        present = [idx[h] for h in (_REQUIRED + _OPTIONAL) if idx[h] >= 0]
        self.assertEqual(present, sorted(present), "sections out of canonical order")

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk_repo(root)
            proc = self._run(root, "--id", "my-cat", "--title", "My Cat", "--class", "execution", "--keywords", "do a thing", "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse((root / "prompts" / "agent_templates" / "my-cat.md").exists())
            self.assertIn("## Role", proc.stdout)
            self.assertIn("id: my-cat", proc.stdout)

    def test_writes_file_and_prints_stanza(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk_repo(root)
            proc = self._run(root, "--id", "my-cat", "--title", "My Cat", "--class", "review", "--keywords", "k1,k2")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((root / "prompts" / "agent_templates" / "my-cat.md").exists())
            self.assertIn("class: review", proc.stdout)

    def test_refuse_on_collision(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk_repo(root)
            (root / "prompts" / "agent_templates" / "dup.md").write_text("existing\n", encoding="utf-8")
            proc = self._run(root, "--id", "dup", "--title", "Dup", "--class", "execution", "--keywords", "x")
            self.assertEqual(proc.returncode, 1)
            self.assertEqual((root / "prompts" / "agent_templates" / "dup.md").read_text(encoding="utf-8"), "existing\n")

    def test_bad_class_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk_repo(root)
            proc = self._run(root, "--id", "x", "--title", "X", "--class", "bogus", "--keywords", "x")
            self.assertEqual(proc.returncode, 2)

    def test_non_generic_needs_keywords_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk_repo(root)
            proc = self._run(root, "--id", "x", "--title", "X", "--class", "execution")
            self.assertEqual(proc.returncode, 2)

    def test_does_not_edit_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk_repo(root, with_manifest=True)
            manifest = root / "prompts" / "agent_templates" / "manifest.yaml"
            before = manifest.read_text(encoding="utf-8")
            proc = self._run(root, "--id", "my-cat", "--title", "My Cat", "--class", "execution", "--keywords", "k1")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(manifest.read_text(encoding="utf-8"), before, "scaffold must NOT edit manifest.yaml")
            self.assertIn("- id: my-cat", proc.stdout)


if __name__ == "__main__":
    unittest.main()
