"""Static lint for the template-agent Skill (custom-agent suite PR 5).

The Skill (``.claude/skills/template-agent/SKILL.md``) is the interactive orchestrator;
its live behaviour needs a model, so CI asserts the *static* surface: frontmatter shape
(the suite's ``opus`` + ``max`` defaults, the tool allowlist including ``Agent`` for
validator delegation, and user-only invocation), and that the bounded state machine wires
to **real artifacts** -- the template library, the RUBRIC, the discovery CLI, the emission
dir, and the ``prompt-validator`` subagent -- so the Skill can never reference a path that
does not exist.

``.claude/**`` is git-tracked via the PR-1 ``.gitignore`` negation but excluded from every
pre-commit hook except markdownlint, so this unittest -- wired into ``ci.yml`` -- is the gate.

Design-of-record: ``notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md`` (S5.1, S5.2, S8).
Location-agnostic: discovers the repo root by walking up for ``.github/workflows/``.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

# Tools the Skill must pre-approve. `Agent` is required to delegate to prompt-validator;
# Write to emit; Read/Grep/Glob/Bash to discover and fill.
_REQUIRED_TOOLS = {"Read", "Grep", "Glob", "Bash", "Write", "Agent"}

# Repo artifacts the state machine wires to by literal path -- each must appear in the body
# AND exist on disk (no dangling wiring).
_REFERENCED_PATHS = [
    "prompts/agent_templates/manifest.yaml",
    "prompts/agent_templates/RUBRIC.md",
    "prompts/agent_templates/generic.md",
    "util/prompt_discovery/cli.py",
    "util/prompt_discovery/symbol_overlay.py",
    "prompts/generated",
]
_VALIDATOR_AGENT = ".claude/agents/prompt-validator.md"
_TERMINAL_STATES = ("EMIT_CLEAN", "EMIT_WITH_CAVEATS", "ESCALATE_TO_PAUL")


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


def _as_tool_set(value):
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(v).strip() for v in value if str(v).strip()}
    return {tok.strip() for tok in re.split(r"[,\s]+", str(value)) if tok.strip()}


class TemplateAgentSkillLintTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.skill_path = cls.repo_root / ".claude" / "skills" / "template-agent" / "SKILL.md"
        cls.text = cls.skill_path.read_text(encoding="utf-8") if cls.skill_path.exists() else None
        cls.front, cls.body = _split_frontmatter(cls.text) if cls.text else (None, "")

    def setUp(self):
        if self.text is None:
            self.skipTest(f"template-agent Skill absent at {self.skill_path}")

    def test_skill_file_exists(self):
        self.assertTrue(self.skill_path.exists(), f"missing Skill at {self.skill_path}")

    def test_frontmatter_parses(self):
        self.assertIsNotNone(self.front, "SKILL.md has no parseable YAML frontmatter")

    def test_name_and_description(self):
        self.assertEqual(self.front.get("name"), "template-agent")
        desc = self.front.get("description", "")
        self.assertIsInstance(desc, str)
        self.assertGreaterEqual(len(desc), 60, "description should describe when/what the Skill does")

    def test_argument_hint_present(self):
        self.assertTrue(str(self.front.get("argument-hint", "")).strip(), "argument-hint should be set")

    def test_allowed_tools_include_required(self):
        tools = _as_tool_set(self.front.get("allowed-tools"))
        missing = sorted(_REQUIRED_TOOLS - tools)
        self.assertEqual(missing, [], f"allowed-tools missing {missing} (Agent is required to delegate to the validator)")

    def test_model_pinned_to_opus(self):
        base = str(self.front.get("model", "")).split(":")[0].strip().lower()
        self.assertTrue(base == "opus" or base.startswith("claude-opus"), f"suite default model is Opus; got {self.front.get('model')!r}")

    def test_effort_is_max(self):
        self.assertEqual(str(self.front.get("effort", "")).strip().lower(), "max", "suite default effort is 'max'")

    def test_user_only_invocation(self):
        self.assertIs(self.front.get("disable-model-invocation"), True, "Skill is user-only initially (OQ-5)")

    def test_referenced_paths_exist(self):
        for rel in _REFERENCED_PATHS:
            self.assertIn(rel, self.body, f"SKILL.md should reference {rel}")
            self.assertTrue((self.repo_root / rel).exists(), f"SKILL.md references {rel} but it does not exist on disk")

    def test_delegates_to_validator(self):
        self.assertIn("prompt-validator", self.body, "Skill must delegate to the prompt-validator subagent")
        self.assertIn("Agent", self.body, "Skill must use the Agent tool to delegate")
        self.assertTrue((self.repo_root / _VALIDATOR_AGENT).exists(), f"delegation target {_VALIDATOR_AGENT} must exist")

    def test_passes_target_repo_to_validator(self):
        """E-3: the Skill accepts the cross-repo target and threads the resolved <target> path
        through discovery AND the validator delegation (so the validator re-probes the right tree)."""
        self.assertIn("--target-repo", self.body, "Skill must accept the cross-repo --target-repo alias")
        self.assertGreaterEqual(self.body.count("<target>"), 3, "Skill must resolve <target> and thread it through discovery + delegation")
        self.assertRegex(
            self.body,
            r"(?s)<target>.{0,400}prompt-validator|prompt-validator.{0,400}<target>",
            "the validator delegation must hand the target repo path <target> to prompt-validator",
        )

    def test_bounded_loop_and_terminal_states(self):
        self.assertRegex(self.body, r"max 3|3 rounds|bounded", "Skill must document the bounded (max 3) validation loop")
        for state in _TERMINAL_STATES:
            self.assertIn(state, self.body, f"Skill must document terminal state {state}")

    def test_pass_bar_documented(self):
        low = self.body.lower()
        for token in ("blocker", "major", "grounded"):
            self.assertIn(token, low, f"Skill must state the validator PASS bar (missing '{token}')")


if __name__ == "__main__":
    unittest.main()
