"""Tests for util/template_select_preview.py (offline template-selection preview).

Drives the REAL manifest (so it also guards selection drift): a task containing a template's
own keyword selects that template; a no-keyword task falls back to ``generic``; the CLI exits
0 and emits the documented JSON shape. Also pins the degrade path: a missing or malformed
manifest must still exit 0, warn on stderr, and select ``generic`` (never crash / invent a pick).

util/ is not a package; the helper is importlib-loaded. Location-agnostic.
"""

from __future__ import annotations

import importlib.util
import json
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
_MODULE = _REPO_ROOT / "util" / "template_select_preview.py"
_DEGRADE_WARN = "could not load manifest.yaml; defaulting to 'generic'"


def _load():
    spec = importlib.util.spec_from_file_location("template_select_preview", _MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mk_repo(root: Path, *, manifest_text=None):
    """Minimal suite root: .github/workflows/ so --repo-root is accepted; optional manifest."""
    (root / ".github" / "workflows").mkdir(parents=True)
    templates = root / "prompts" / "agent_templates"
    templates.mkdir(parents=True)
    if manifest_text is not None:
        (templates / "manifest.yaml").write_text(manifest_text, encoding="utf-8")


class SelectPreviewUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.manifest = cls.mod._load_manifest(_REPO_ROOT)

    def setUp(self):
        if self.manifest is None:
            self.skipTest("manifest.yaml not loadable (PyYAML absent?)")

    def test_failing_tests_keyword_selects_failing_tests(self):
        selected, _ = self.mod.select("the test suite is failing after the refactor", self.manifest)
        self.assertEqual(selected["id"], "failing-tests")
        self.assertTrue(selected["matched"])

    def test_no_keyword_falls_back_to_generic(self):
        selected, ranked = self.mod.select("frobnicate the wizzle component thoroughly", self.manifest)
        self.assertEqual(selected["id"], "generic")
        self.assertEqual(selected["matched"], [])

    def test_rank_never_crashes_and_excludes_generic(self):
        ranked = self.mod.rank("any task text", self.manifest["templates"])
        ids = {r["id"] for r in ranked}
        self.assertNotIn("generic", ids, "the always-match fallback must not appear in the ranked candidates")
        self.assertTrue(all("score" in r and "matched" in r for r in ranked))

    def test_select_without_always_match_hardcodes_generic(self):
        # Corrupted-but-loadable manifest: dict with templates but no always-match fallback.
        selected, ranked = self.mod.select(
            "no keywords here",
            {"templates": [{"id": "only-keyword", "class": "target", "match_signals": {"keywords": ["zzz"]}}]},
        )
        self.assertEqual(selected["id"], "generic")
        self.assertEqual(selected["class"], "generic")
        self.assertEqual(selected["matched"], [])
        self.assertEqual(selected["score"], 0)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["score"], 0)


class SelectPreviewLoadManifestTest(unittest.TestCase):
    """Unit coverage for _load_manifest degrade arms (missing / non-dict / empty)."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_missing_manifest_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_repo(root)  # no manifest.yaml
            self.assertIsNone(self.mod._load_manifest(root))

    def test_non_dict_manifest_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_repo(root, manifest_text="- just\n- a\n- list\n")
            self.assertIsNone(self.mod._load_manifest(root))

    def test_empty_manifest_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_repo(root, manifest_text="")
            self.assertIsNone(self.mod._load_manifest(root))

    def test_scalar_manifest_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_repo(root, manifest_text="not-a-mapping\n")
            self.assertIsNone(self.mod._load_manifest(root))


class SelectPreviewCliTest(unittest.TestCase):
    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(_MODULE), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def test_cli_exit_0(self):
        proc = self._run("the test suite is failing", "--repo-root", str(_REPO_ROOT))
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_cli_json_shape(self):
        proc = self._run("the test suite is failing", "--repo-root", str(_REPO_ROOT), "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(set(data), {"task", "selected", "candidates"})
        self.assertEqual(data["selected"]["id"], "failing-tests")
        self.assertIsInstance(data["candidates"], list)

    def _assert_degraded_generic(self, proc):
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(_DEGRADE_WARN, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["selected"]["id"], "generic")
        self.assertEqual(data["selected"]["class"], "generic")
        self.assertEqual(data["selected"]["matched"], [])
        self.assertEqual(data["selected"]["score"], 0)
        self.assertEqual(data["candidates"], [])

    def test_cli_missing_manifest_defaults_to_generic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_repo(root)  # workflows present; manifest absent
            proc = self._run("any task text", "--repo-root", str(root), "--json")
            self._assert_degraded_generic(proc)

    def test_cli_malformed_manifest_defaults_to_generic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_repo(root, manifest_text="- not\n- a\n- mapping\n")
            proc = self._run("any task text", "--repo-root", str(root), "--json")
            self._assert_degraded_generic(proc)

    def test_cli_empty_manifest_defaults_to_generic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _mk_repo(root, manifest_text="")
            proc = self._run("any task text", "--repo-root", str(root), "--json")
            self._assert_degraded_generic(proc)


if __name__ == "__main__":
    unittest.main()
