"""Tests for util/prompt_discovery/symbol_overlay.py (Serena overlay, design OQ-8).

Verifies the deterministic merge of Skill-resolved Serena facts into a discovery bundle's
``symbol_probe`` slice: Serena-resolved wins, grep is the fallback, an unresolvable symbol
stays UNRESOLVED, the input bundle is not mutated, and ``cli.py``'s contract is untouched
(the ``source`` / ``overlay`` markers are added here, on the overlay side).

``util/`` is not a package; the helper is loaded via ``importlib``. Location-agnostic.
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
_MODULE = _REPO_ROOT / "util" / "prompt_discovery" / "symbol_overlay.py"


def _load():
    spec = importlib.util.spec_from_file_location("symbol_overlay", _MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _bundle(symbols):
    return {
        "schema_version": 1,
        "provenance": {"head_sha": "deadbeef"},
        "symbol_probe": {"status": "ok", "symbols": symbols},
    }


class SymbolOverlayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_module_exists(self):
        self.assertTrue(_MODULE.exists(), f"missing {_MODULE}")

    def test_serena_resolved_overrides_grep(self):
        bundle = _bundle({"foo": {"status": "resolved", "definition": "a.py:1", "signature": "def foo()"}})
        serena = {"foo": {"status": "resolved", "definition": "real.py:88", "signature": "def foo(x, y)"}}
        out = self.mod.merge_symbol_probe(bundle, serena)
        foo = out["symbol_probe"]["symbols"]["foo"]
        self.assertEqual(foo["definition"], "real.py:88")
        self.assertEqual(foo["source"], "serena")
        self.assertEqual(out["symbol_probe"]["overlay"], "serena")

    def test_serena_unresolved_keeps_grep_fallback(self):
        bundle = _bundle({"foo": {"status": "resolved", "definition": "a.py:1", "signature": "def foo()"}})
        serena = {"foo": {"status": "unresolved", "definition": None, "signature": None}}
        out = self.mod.merge_symbol_probe(bundle, serena)
        foo = out["symbol_probe"]["symbols"]["foo"]
        self.assertEqual(foo["definition"], "a.py:1")
        self.assertEqual(foo["source"], "grep")

    def test_unresolved_when_neither_resolves(self):
        out = self.mod.merge_symbol_probe(_bundle({}), {"bar": {"status": "unresolved"}})
        bar = out["symbol_probe"]["symbols"]["bar"]
        self.assertEqual(bar["status"], "unresolved")
        self.assertIsNone(bar["definition"])
        self.assertEqual(bar["source"], "serena")

    def test_new_serena_symbol_added(self):
        out = self.mod.merge_symbol_probe(_bundle({}), {"baz": {"status": "resolved", "definition": "x.py:5", "signature": "class baz"}})
        self.assertEqual(out["symbol_probe"]["symbols"]["baz"]["definition"], "x.py:5")

    def test_input_bundle_not_mutated(self):
        bundle = _bundle({"foo": {"status": "resolved", "definition": "a.py:1", "signature": "def foo()"}})
        before = json.dumps(bundle, sort_keys=True)
        self.mod.merge_symbol_probe(bundle, {"foo": {"status": "resolved", "definition": "z.py:9", "signature": "x"}})
        self.assertEqual(json.dumps(bundle, sort_keys=True), before, "merge must not mutate the input bundle")

    def test_empty_serena_preserves_grep(self):
        out = self.mod.merge_symbol_probe(_bundle({"foo": {"status": "resolved", "definition": "a.py:1", "signature": "def foo()"}}), {})
        self.assertEqual(out["symbol_probe"]["symbols"]["foo"]["definition"], "a.py:1")
        self.assertEqual(out["symbol_probe"]["overlay"], "serena")

    def test_cli_merge(self):
        with tempfile.TemporaryDirectory() as d:
            bundle_path = Path(d) / "bundle.json"
            serena_path = Path(d) / "serena.json"
            bundle_path.write_text(
                json.dumps(_bundle({"foo": {"status": "resolved", "definition": "a.py:1", "signature": "def foo()"}})),
                encoding="utf-8",
            )
            serena_path.write_text(
                json.dumps({"foo": {"status": "resolved", "definition": "real.py:88", "signature": "def foo(x)"}}),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [sys.executable, str(_MODULE), "--bundle", str(bundle_path), "--serena", str(serena_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            merged = json.loads(proc.stdout)
            self.assertEqual(merged["symbol_probe"]["symbols"]["foo"]["definition"], "real.py:88")
            self.assertEqual(merged["symbol_probe"]["symbols"]["foo"]["source"], "serena")


if __name__ == "__main__":
    unittest.main()
