"""Tests for util/generated_prompt_index.py (index + safety-gated prune/archive of prompts/generated/).

Emphasis on the destructive-path SAFETY: ``--prune`` / ``--archive`` without ``--yes`` (or under
``--dry-run``) deletes/moves nothing, and ``.gitkeep`` / non-convention files are never candidates.
Also: name parsing, ``.gitkeep`` ignored, and that the generated-dir location is read from
``conventions.yaml`` (authoritative, not hard-coded).

util/ is not a package; importlib-loaded. Location-agnostic.
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
_MODULE = _REPO_ROOT / "util" / "generated_prompt_index.py"
_OLD = "Juniper_juniper-ml_test-subject_PLAN_2020-01-01_1200.md"


def _load():
    spec = importlib.util.spec_from_file_location("generated_prompt_index", _MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mk_repo(root: Path, conventions_location=None):
    (root / ".github" / "workflows").mkdir(parents=True)
    gen = root / "prompts" / "generated"
    gen.mkdir(parents=True)
    (gen / ".gitkeep").write_text("", encoding="utf-8")
    (gen / _OLD).write_text("# old prompt\n", encoding="utf-8")
    (gen / "hand-placed-notes.md").write_text("not convention\n", encoding="utf-8")
    if conventions_location is not None:
        data = root / "prompts" / "agent_templates" / "data"
        data.mkdir(parents=True)
        (data / "conventions.yaml").write_text(f'version: 1\ndeliverable_locations:\n  generated_prompts: "{conventions_location}"\n', encoding="utf-8")
    return gen


class ParseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_parse_convention_name(self):
        parsed = self.mod.parse_name(_OLD)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["project"], "Juniper")
        self.assertEqual(parsed["application"], "juniper-ml")
        self.assertEqual(parsed["date"], "2020-01-01")
        self.assertEqual(parsed["time"], "1200")

    def test_parse_rejects_malformed(self):
        self.assertIsNone(self.mod.parse_name("hand-placed-notes.md"))
        self.assertIsNone(self.mod.parse_name(".gitkeep"))


class CliTest(unittest.TestCase):
    def _run(self, root, *args):
        return subprocess.run(
            [sys.executable, str(_MODULE), "--repo-root", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def test_index_ignores_gitkeep_and_flags_malformed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _mk_repo(root)
            proc = self._run(root, "--json")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads(proc.stdout)
            files = [p["file"] for p in data["prompts"]]
            self.assertEqual(files, [_OLD])
            self.assertIn("hand-placed-notes.md", data["malformed"])

    def test_prune_without_yes_deletes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            gen = _mk_repo(root)
            proc = self._run(root, "--older-than", "1", "--prune")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((gen / _OLD).exists(), "prune without --yes must NOT delete")
            self.assertIn("would-prune", proc.stdout)

    def test_dry_run_overrides_yes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            gen = _mk_repo(root)
            proc = self._run(root, "--older-than", "1", "--prune", "--yes", "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((gen / _OLD).exists(), "--dry-run must override --yes")

    def test_prune_with_yes_deletes_only_convention_stale(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            gen = _mk_repo(root)
            proc = self._run(root, "--older-than", "1", "--prune", "--yes")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse((gen / _OLD).exists(), "stale convention file should be pruned with --yes")
            self.assertTrue((gen / ".gitkeep").exists(), ".gitkeep must never be pruned")
            self.assertTrue((gen / "hand-placed-notes.md").exists(), "non-convention file must never be pruned")

    def test_archive_without_yes_moves_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            gen = _mk_repo(root)
            archive = root / "archive_out"
            proc = self._run(root, "--older-than", "1", "--archive", str(archive))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((gen / _OLD).exists(), "archive without --yes must NOT move")
            self.assertFalse(archive.exists(), "preview must not create the archive dir")
            self.assertIn("would-archive", proc.stdout)

    def test_archive_dry_run_overrides_yes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            gen = _mk_repo(root)
            archive = root / "archive_out"
            proc = self._run(root, "--older-than", "1", "--archive", str(archive), "--yes", "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((gen / _OLD).exists(), "--dry-run must override --yes for archive")
            self.assertFalse(archive.exists(), "--dry-run must not create the archive dir")

    def test_archive_with_yes_moves_only_convention_stale(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            gen = _mk_repo(root)
            archive = root / "archive_out"
            proc = self._run(root, "--older-than", "1", "--archive", str(archive), "--yes")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse((gen / _OLD).exists(), "stale convention file should leave generated/")
            self.assertTrue((archive / _OLD).exists(), "stale convention file should land in archive DIR")
            self.assertEqual((archive / _OLD).read_text(encoding="utf-8"), "# old prompt\n")
            self.assertTrue((gen / ".gitkeep").exists(), ".gitkeep must never be archived")
            self.assertTrue((gen / "hand-placed-notes.md").exists(), "non-convention file must never be archived")

    def test_location_read_from_conventions(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "prompts" / "agent_templates" / "data").mkdir(parents=True)
            (root / "prompts" / "agent_templates" / "data" / "conventions.yaml").write_text('version: 1\ndeliverable_locations:\n  generated_prompts: "custom_out/"\n', encoding="utf-8")
            custom = root / "custom_out"
            custom.mkdir()
            (custom / _OLD).write_text("# x\n", encoding="utf-8")
            proc = self._run(root, "--json")
            data = json.loads(proc.stdout)
            self.assertTrue(data["generated_dir"].endswith("custom_out"), data["generated_dir"])
            self.assertEqual([p["file"] for p in data["prompts"]], [_OLD])


if __name__ == "__main__":
    unittest.main()
