"""Tests for util/agent_suite_summary.py (the custom-agent suite quick-reference).

Drives the real suite: every agent and template appears; `--json` round-trips; `--markdown`
stays within the 512-char line-length convention. util/ is not a package; importlib-loaded.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_MODULE = _REPO_ROOT / "util" / "agent_suite_summary.py"


def _load():
    spec = importlib.util.spec_from_file_location("agent_suite_summary", _MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class SummaryUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_collect_agents_includes_known(self):
        agents = self.mod.collect_agents(_REPO_ROOT)
        names = {a["name"] for a in agents}
        self.assertTrue({"prompt-validator", "planner", "auditor", "task-executor"} <= names, names)
        self.assertTrue(all(a["model"] for a in agents), "every agent should report a model")

    def test_collect_templates_includes_known(self):
        ids = {t["id"] for t in self.mod.collect_templates(_REPO_ROOT)}
        self.assertTrue({"code-review", "generic"} <= ids, ids)
        self.assertGreaterEqual(len(ids), 7)

    def test_markdown_lines_within_512(self):
        agents = self.mod.collect_agents(_REPO_ROOT)
        templates = self.mod.collect_templates(_REPO_ROOT)
        md = self.mod._render_markdown(agents, templates, {"agents", "templates"})
        over = [ln for ln in md.splitlines() if len(ln) > 512]
        self.assertEqual(over, [], "markdown rows must respect the 512-char line-length convention")


class SummaryCliTest(unittest.TestCase):
    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(_MODULE), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def test_json_round_trips(self):
        proc = self._run("--repo-root", str(_REPO_ROOT), "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(set(data), {"agents", "templates"})
        self.assertTrue(data["agents"] and data["templates"])

    def test_agents_only_section(self):
        proc = self._run("--repo-root", str(_REPO_ROOT), "--agents", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["agents"])
        self.assertEqual(data["templates"], [])

    def test_default_text_exit_0(self):
        proc = self._run("--repo-root", str(_REPO_ROOT))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("AGENTS", proc.stdout)
        self.assertIn("TEMPLATES", proc.stdout)


if __name__ == "__main__":
    unittest.main()
