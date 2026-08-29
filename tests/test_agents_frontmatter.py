"""Suite-wide frontmatter gate for every ``.claude/agents/*.md`` (custom-agent suite).

Enforces that EVERY custom-agent subagent conforms to the suite contract -- the ``name``
matches the filename, the ``description`` is substantive, ``tools`` are declared, the body
is non-trivial, and the owner-directed defaults ``model: opus`` + ``effort: max`` hold --
so new agents (round-2 ``planner`` / ``auditor`` / ``task-executor`` and beyond) cannot
drift from the standing defaults. The validator additionally has its own deep contract test
(``tests/test_prompt_validator_contract.py``); this is the shared invariant across all agents.

``.claude/**`` is git-tracked via the PR-1 ``.gitignore`` negation but excluded from every
pre-commit hook except markdownlint, so this unittest -- wired into ``ci.yml`` -- is the gate.

Location-agnostic: discovers the repo root by walking up for ``.github/workflows/``.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

_KEBAB = re.compile(r"^[a-z][a-z0-9-]*$")


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


def _split_frontmatter(text: str):
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    front = yaml.safe_load(parts[1])
    return (front if isinstance(front, dict) else None), parts[2]


def _as_set(value):
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(v).strip() for v in value if str(v).strip()}
    return {tok.strip() for tok in re.split(r"[,\s]+", str(value)) if tok.strip()}


class AgentsFrontmatterTest(unittest.TestCase):
    """Every .claude/agents/*.md must honour the suite frontmatter contract."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.agents_dir = cls.repo_root / ".claude" / "agents"
        cls.agent_files = sorted(cls.agents_dir.glob("*.md")) if cls.agents_dir.is_dir() else []

    def setUp(self):
        if not self.agent_files:
            self.skipTest(f"no agents at {self.agents_dir}")

    def _each(self):
        for path in self.agent_files:
            front, body = _split_frontmatter(path.read_text(encoding="utf-8"))
            yield path, front, body

    def test_at_least_one_agent(self):
        self.assertTrue(self.agent_files, "expected at least one .claude/agents/*.md")

    def test_frontmatter_parses(self):
        for path, front, _ in self._each():
            self.assertIsNotNone(front, f"{path.name}: no parseable YAML frontmatter")

    def test_name_matches_filename_kebab(self):
        for path, front, _ in self._each():
            name = front.get("name")
            self.assertEqual(name, path.stem, f"{path.name}: name {name!r} must equal the filename stem")
            self.assertRegex(name, _KEBAB, f"{path.name}: name must be lowercase kebab-case")

    def test_description_substantive(self):
        for path, front, _ in self._each():
            desc = front.get("description", "")
            self.assertIsInstance(desc, str)
            self.assertGreaterEqual(len(desc), 60, f"{path.name}: description should describe when to delegate")

    def test_tools_declared(self):
        for path, front, _ in self._each():
            self.assertTrue(_as_set(front.get("tools")), f"{path.name}: tools must be declared (non-empty)")

    def test_model_is_opus(self):
        for path, front, _ in self._each():
            base = str(front.get("model", "")).split(":")[0].strip().lower()
            self.assertTrue(
                base == "opus" or base.startswith("claude-opus"),
                f"{path.name}: suite default model is Opus (owner directive); got {front.get('model')!r}",
            )

    def test_effort_is_max(self):
        for path, front, _ in self._each():
            self.assertEqual(
                str(front.get("effort", "")).strip().lower(),
                "max",
                f"{path.name}: suite default effort is 'max' (owner directive); got {front.get('effort')!r}",
            )

    def test_body_non_trivial(self):
        for path, _, body in self._each():
            self.assertGreater(len(body.strip()), 200, f"{path.name}: agent body looks empty/stub")


if __name__ == "__main__":
    unittest.main()
