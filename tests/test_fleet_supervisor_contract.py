"""Static contract test for the ``fleet-supervisor`` subagent (Stage-0 supervisor, P3 §1B).

Validates the read-only fleet-triage agent deliverable without a live model, modeled on
``tests/test_prompt_validator_contract.py``:

* ``.claude/agents/fleet-supervisor.md`` frontmatter shape -- ``name`` is the kebab id
  (== filename stem), ``description`` is substantive and on-topic, ``tools`` is exactly the
  read-only + Bash set (no file-mutating tool), and ``model``/``effort`` are the suite
  defaults ``opus`` / ``max``;
* the body wires to the real script -- it references ``util/fleet_triage/predict_merge.py``,
  documents all four SCRIPT verdict tokens (MERGE-CLEAN / NEEDS-UPDATE-BRANCH /
  DAMAGED-FIX-FIRST / CONFLICT), states the read-only / never-push mandate, and states the
  two-key DUP-CLOSE rule (content overlap AND owner confirmation; the script never
  auto-closes).

The ``.claude/**`` subtree is git-tracked via the PR-1 ``.gitignore`` negation but excluded
from every pre-commit hook except markdownlint, so this unittest -- wired into
``.github/workflows/ci.yml`` -- is the behavioural gate for the supervisor surface. It
complements the suite-wide ``tests/test_agents_frontmatter.py`` invariant.

Design of record: P3 §1B in
``notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md``.
Location-agnostic: discovers the repo root by walking up for ``.github/workflows/``.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

# read-only + Bash (P3 §1B). The supervisor must never mutate the repository or a PR.
_EXPECTED_TOOLS = {"Read", "Grep", "Glob", "Bash"}
_MUTATING_TOOLS = {"Write", "Edit", "NotebookEdit"}

# The four verdicts the deterministic SCRIPT emits (DUP-CLOSE is the agent-only 5th).
_SCRIPT_VERDICTS = {"MERGE-CLEAN", "NEEDS-UPDATE-BRANCH", "DAMAGED-FIX-FIRST", "CONFLICT"}

_KEBAB = re.compile(r"^[a-z][a-z0-9-]*$")


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


def _split_frontmatter(text: str):
    """Return ``(frontmatter_dict_or_None, body_text)`` for a ``---``-fenced markdown file."""
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    front = yaml.safe_load(parts[1])
    return (front if isinstance(front, dict) else None), parts[2]


def _as_tool_set(value):
    """Frontmatter ``tools`` may be a comma/space-separated string or a YAML list."""
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(v).strip() for v in value if str(v).strip()}
    return {tok.strip() for tok in re.split(r"[,\s]+", str(value)) if tok.strip()}


class FleetSupervisorAgentTest(unittest.TestCase):
    """`.claude/agents/fleet-supervisor.md` frontmatter + body-wiring integrity."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.agent_path = cls.repo_root / ".claude" / "agents" / "fleet-supervisor.md"
        cls.script_path = cls.repo_root / "util" / "fleet_triage" / "predict_merge.py"
        cls.agent_text = cls.agent_path.read_text(encoding="utf-8") if cls.agent_path.exists() else None
        cls.front, cls.body = _split_frontmatter(cls.agent_text) if cls.agent_text else (None, "")

    def setUp(self):
        if self.agent_text is None:
            self.skipTest(f"fleet-supervisor agent absent at {self.agent_path}")

    def test_agent_file_exists(self):
        self.assertTrue(self.agent_path.exists(), f"missing fleet-supervisor subagent at {self.agent_path}")

    def test_script_exists(self):
        self.assertTrue(self.script_path.exists(), f"the agent's script layer must ship at {self.script_path}")

    def test_frontmatter_parses(self):
        self.assertIsNotNone(self.front, "agent file has no parseable YAML frontmatter between '---' fences")

    def test_name_is_kebab_stem(self):
        name = self.front.get("name")
        self.assertEqual(name, "fleet-supervisor", "subagent name must be 'fleet-supervisor'")
        self.assertEqual(name, self.agent_path.stem, "name must equal the filename stem")
        self.assertRegex(name, _KEBAB, "subagent name must be lowercase kebab-case")

    def test_description_substantive_and_on_topic(self):
        desc = self.front.get("description", "")
        self.assertIsInstance(desc, str)
        self.assertGreaterEqual(len(desc), 60, "description should meaningfully describe when to delegate")
        low = desc.lower()
        self.assertTrue("read-only" in low or "read only" in low, "description must state the read-only stance")
        self.assertTrue(
            "pr" in low and ("triage" in low or "merge" in low),
            "description should reference triaging / predicted-merge of PRs",
        )

    def test_tools_are_read_only_plus_bash(self):
        tools = _as_tool_set(self.front.get("tools"))
        self.assertEqual(tools, _EXPECTED_TOOLS, f"tools must be exactly {sorted(_EXPECTED_TOOLS)}, got {sorted(tools)}")
        self.assertEqual(tools & _MUTATING_TOOLS, set(), "supervisor must carry no file-mutating tool")

    def test_model_pinned_to_opus(self):
        model = self.front.get("model")
        self.assertIsNotNone(model, "supervisor model must be pinned (suite default)")
        base = str(model).split(":")[0].strip().lower()
        is_opus = base == "opus" or base.startswith("claude-opus")
        self.assertTrue(is_opus, f"suite default model is latest Opus (owner directive); got {model!r}")

    def test_effort_is_max(self):
        effort = self.front.get("effort")
        self.assertEqual(str(effort).strip().lower(), "max", f"suite default effort is 'max'; got {effort!r}")

    def test_body_references_the_script_layer(self):
        self.assertIn(
            "util/fleet_triage/predict_merge.py",
            self.body,
            "the agent body must invoke the deterministic script util/fleet_triage/predict_merge.py",
        )

    def test_body_documents_all_four_verdict_tokens(self):
        missing = sorted(v for v in _SCRIPT_VERDICTS if v not in self.body)
        self.assertEqual(missing, [], f"agent body must document every script verdict; missing {missing}")

    def test_body_states_read_only_never_push_mandate(self):
        low = self.body.lower()
        self.assertIn("read-only", low, "agent body must state the read-only stance")
        self.assertTrue(
            "never" in low and ("push" in low or "merge" in low),
            "agent body must state it never pushes/merges (the read-only mandate)",
        )

    def test_body_states_two_key_dup_close_rule(self):
        self.assertIn("DUP-CLOSE", self.body, "agent body must document the DUP-CLOSE recommendation")
        low = self.body.lower()
        self.assertIn("two-key", low, "agent body must name the two-key DUP-CLOSE rule")
        self.assertTrue(
            ("owner confirm" in low) or ("owner confirmation" in low) or ("owner-confirmed" in low),
            "the two-key rule must require owner confirmation (a false close = lost real work)",
        )
        self.assertTrue(
            "overlap" in low or "jaccard" in low or "multiset" in low,
            "the two-key rule must require content overlap (the added-line multiset key)",
        )

    def test_body_scopes_gpgsign_bypass_to_keyless_contexts(self):
        """The ``-c commit.gpgsign=false`` bypass must be scoped to KEYLESS contexts only.

        Before 2026-08-07 the owner's card-resident key could not sign unattended, so this body
        carried a blanket "any headless commit MUST disable signing" rule -- and the *previous*
        version of this test pinned that blanket rule in place. Headless signing works on the
        workstation now, and the stale rule was the direct cause of the unsigned juniper-cascor#506
        branch commits (``verification.reason == "unsigned"`` while ``commit.gpgsign=true``).

        The bypass remains correct for genuinely keyless contexts -- CI runners, hermetic fixtures,
        throwaway clones (``propose.py`` / ``predict_merge.py``) -- so pin the SCOPING, not the
        flag's bare presence.
        """
        self.assertIn(
            "commit.gpgsign=false",
            self.body,
            "the keyless-context bypass must still be documented (propose.py / predict_merge.py rely on it)",
        )
        low = self.body.lower()
        self.assertTrue(
            any(token in low for token in ("keyless", "ci runner", "hermetic", "throwaway")),
            "the gpgsign bypass must be scoped to keyless contexts, not stated as a blanket rule",
        )
        self.assertNotIn(
            "any headless commit in a delegated flow must use",
            low,
            "the blanket 'every headless commit MUST disable signing' rule is stale (cascor#506 class)",
        )

    def test_body_is_non_trivial(self):
        self.assertGreater(len(self.body.strip()), 200, "agent body looks empty/stub")


if __name__ == "__main__":
    unittest.main()
