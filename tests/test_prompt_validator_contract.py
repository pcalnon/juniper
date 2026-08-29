"""Static contract test for the ``prompt-validator`` subagent (custom-agent suite PR 3).

Validates the headless validator deliverable without a live model:

* ``.claude/agents/prompt-validator.md`` frontmatter shape -- ``name`` is the kebab id,
  ``description`` is substantive and on-topic, ``tools`` is exactly the read-only + Bash
  set (no file-mutating tool), and ``model`` is a concrete pin (resolving design OQ-4,
  not left as ``inherit``);
* every rubric criterion ID the agent body cites actually exists in
  ``prompts/agent_templates/RUBRIC.md`` (so the validator can never reference a check that was
  renamed or dropped), and the two hard gates (``R2.0``, ``R3.4``) are present;
* the pinned verdict JSON schema (``tests/fixtures/prompt_validator/verdict.schema.json``)
  declares the section-5.3 contract, and the bundled PASS/FAIL sample verdicts conform to
  it (top-level keys, enums, finding IDs present in RUBRIC.md, and PASS-bar consistency).

The ``.claude/**`` subtree is git-tracked via the PR-1 ``.gitignore`` negation but is
excluded from every pre-commit hook except markdownlint, so this unittest -- wired into
``.github/workflows/ci.yml`` -- is the behavioural gate for the validator surface.

Design-of-record: ``notes/JUNIPER_2026-06-23_JUNIPER-ML_CUSTOM-AGENT-SUITE-DESIGN.md`` (S5.3, S5.5, S8).
Location-agnostic: discovers the repo root by walking up for ``.github/workflows/``.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

# --- canonical verdict contract (design S5.3 / RUBRIC.md) -------------------------
# The schema, the sample fixtures, and the agent body are all asserted against these so
# the three artifacts cannot silently drift apart.
_TOP_LEVEL_KEYS = {"validator_status", "head_sha", "iteration", "findings", "hallucination_risk", "overall"}
_VALIDATOR_STATUS = {"ok", "partial", "error"}
_OVERALL = {"PASS", "FAIL"}
_SEVERITY = {"blocker", "major", "minor"}
_CLAIM_CLASS = {"path", "symbol", "version", "port", "env", "flag"}
_FINDING_KEYS = {"id", "severity", "location", "problem", "fix", "evidence"}
_RISK_KEYS = {"claim", "class", "grounded", "evidence"}

# read-only + Bash (design S5.3). The validator must never mutate the repository.
_EXPECTED_TOOLS = {"Read", "Grep", "Glob", "Bash"}
_MUTATING_TOOLS = {"Write", "Edit", "NotebookEdit"}

# The two hard gates: a single failure of either fails the prompt (RUBRIC.md severity table).
_HARD_GATES = {"R2.0", "R3.4"}

# A rubric criterion ID: R1..R5, optional dotted child (R2.0), optional sub-class letter
# (R3.4a). Used to extract IDs from both the agent body and RUBRIC.md.
_RUBRIC_ID = re.compile(r"\bR[1-5](?:\.\d+[a-e]?)?\b")
_FINDING_ID = re.compile(r"^R[1-5](?:\.\d+[a-e]?)?$")
_HEX_SHA = re.compile(r"^[0-9a-f]{7,40}$")
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


class PromptValidatorAgentTest(unittest.TestCase):
    """`.claude/agents/prompt-validator.md` frontmatter + rubric-citation integrity."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.agent_path = cls.repo_root / ".claude" / "agents" / "prompt-validator.md"
        cls.rubric_path = cls.repo_root / "prompts" / "agent_templates" / "RUBRIC.md"
        cls.agent_text = cls.agent_path.read_text(encoding="utf-8") if cls.agent_path.exists() else None
        cls.front, cls.body = _split_frontmatter(cls.agent_text) if cls.agent_text else (None, "")
        cls.rubric_ids = set(_RUBRIC_ID.findall(cls.rubric_path.read_text(encoding="utf-8"))) if cls.rubric_path.exists() else set()

    def setUp(self):
        if self.agent_text is None:
            self.skipTest(f"validator agent absent at {self.agent_path}")

    def test_agent_file_exists(self):
        self.assertTrue(self.agent_path.exists(), f"missing validator subagent at {self.agent_path}")

    def test_frontmatter_parses(self):
        self.assertIsNotNone(self.front, "agent file has no parseable YAML frontmatter between '---' fences")

    def test_name_is_kebab_id(self):
        name = self.front.get("name")
        self.assertEqual(name, "prompt-validator", "subagent name must be 'prompt-validator'")
        self.assertRegex(name, _KEBAB, "subagent name must be lowercase kebab-case")

    def test_description_substantive_and_on_topic(self):
        desc = self.front.get("description", "")
        self.assertIsInstance(desc, str)
        self.assertGreaterEqual(len(desc), 60, "description should meaningfully describe when to delegate")
        low = desc.lower()
        self.assertIn("verdict", low, "description should mention it returns a verdict")
        self.assertTrue("rubric" in low or "r1-r5" in low, "description should reference the rubric it applies")

    def test_tools_are_read_only_plus_bash(self):
        tools = _as_tool_set(self.front.get("tools"))
        self.assertEqual(tools, _EXPECTED_TOOLS, f"tools must be exactly {sorted(_EXPECTED_TOOLS)}, got {sorted(tools)}")
        self.assertEqual(tools & _MUTATING_TOOLS, set(), "validator must carry no file-mutating tool")

    def test_model_pinned_to_opus(self):
        model = self.front.get("model")
        self.assertIsNotNone(model, "validator model must be pinned (resolves OQ-4)")
        base = str(model).split(":")[0].strip().lower()
        is_opus = base == "opus" or base.startswith("claude-opus")
        self.assertTrue(is_opus, f"suite default model is latest Opus (owner directive 2026-06-24); got {model!r}")

    def test_effort_is_max(self):
        effort = self.front.get("effort")
        self.assertEqual(str(effort).strip().lower(), "max", f"suite default effort is 'max' (owner directive 2026-06-24); got {effort!r}")

    def test_body_cites_only_real_rubric_ids(self):
        self.assertTrue(self.rubric_path.exists(), "RUBRIC.md must be present (ships in PR 2b-i)")
        body_ids = set(_RUBRIC_ID.findall(self.body))
        self.assertTrue(body_ids, "agent body cites no rubric IDs -- it must apply named criteria")
        orphans = sorted(body_ids - self.rubric_ids)
        self.assertEqual(orphans, [], f"agent cites rubric ID(s) not declared in RUBRIC.md: {orphans}")

    def test_body_applies_the_hard_gates(self):
        body_ids = set(_RUBRIC_ID.findall(self.body))
        missing = sorted(_HARD_GATES - body_ids)
        self.assertEqual(missing, [], f"agent body must apply the hard gates {sorted(_HARD_GATES)}; missing {missing}")

    def test_body_documents_pass_bar(self):
        low = self.body.lower()
        for token in ("blocker", "major", "grounded", "pass"):
            self.assertIn(token, low, f"agent body must state the measurable PASS bar (missing '{token}')")

    def test_body_documents_verdict_keys(self):
        for key in _TOP_LEVEL_KEYS:
            self.assertIn(key, self.body, f"agent body must document the verdict key '{key}' it must emit")

    def test_body_is_read_only_contract(self):
        low = self.body.lower()
        self.assertTrue("never" in low and ("edit" in low or "mutate" in low), "agent body must state it never edits/mutates files")

    def test_reprobe_block_is_target_qualified_not_cwd(self):
        """E-3: the validator re-probes the TARGET repo, never its own CWD -- so cross-repo
        validation binds to the right tree instead of silently probing juniper-ml."""
        body = self.body
        self.assertRegex(
            body,
            r"git\s+-C\s+<target>\s+rev-parse\s+HEAD",
            "freshness gate must use `git -C <target> rev-parse HEAD` so the verdict head_sha binds to the target",
        )
        self.assertNotRegex(
            body,
            r"\bgit rev-parse HEAD\b",
            "no bare `git rev-parse HEAD` (CWD-relative) may remain -- it would probe the wrong tree cross-repo",
        )
        self.assertGreaterEqual(
            body.count("<target>"),
            5,
            "the whole re-probe taxonomy (freshness + R3.4a-e), not just the freshness gate, must be retargeted to <target>",
        )


class VerdictSchemaTest(unittest.TestCase):
    """The pinned verdict schema + PASS/FAIL sample fixtures conform to the S5.3 contract."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = _find_repo_root(Path(__file__).resolve().parent)
        cls.fixtures_dir = cls.repo_root / "tests" / "fixtures" / "prompt_validator"
        cls.schema_path = cls.fixtures_dir / "verdict.schema.json"
        cls.sample_paths = sorted(cls.fixtures_dir.glob("verdict.sample.*.json"))
        cls.rubric_path = cls.repo_root / "prompts" / "agent_templates" / "RUBRIC.md"
        cls.rubric_ids = set(_RUBRIC_ID.findall(cls.rubric_path.read_text(encoding="utf-8"))) if cls.rubric_path.exists() else set()

    def setUp(self):
        if not self.schema_path.exists():
            self.skipTest(f"verdict schema absent at {self.schema_path}")
        self.schema = json.loads(self.schema_path.read_text(encoding="utf-8"))

    def _load_samples(self):
        return {p.name: json.loads(p.read_text(encoding="utf-8")) for p in self.sample_paths}

    def test_schema_is_valid_and_pins_top_level(self):
        self.assertIn("$schema", self.schema, "schema should declare its $schema dialect")
        self.assertEqual(self.schema.get("type"), "object")
        self.assertIs(self.schema.get("additionalProperties"), False, "verdict schema must be closed (additionalProperties: false)")
        self.assertEqual(set(self.schema.get("required", [])), _TOP_LEVEL_KEYS)

    def test_schema_enums_match_contract(self):
        props = self.schema["properties"]
        self.assertEqual(set(props["validator_status"]["enum"]), _VALIDATOR_STATUS)
        self.assertEqual(set(props["overall"]["enum"]), _OVERALL)
        finding_props = props["findings"]["items"]["properties"]
        self.assertEqual(set(finding_props["severity"]["enum"]), _SEVERITY)
        self.assertIn("pattern", finding_props["id"], "finding id must be pattern-constrained to rubric IDs")
        risk_props = props["hallucination_risk"]["items"]["properties"]
        self.assertEqual(set(risk_props["class"]["enum"]), _CLAIM_CLASS)

    def test_samples_present_pass_and_fail(self):
        self.assertTrue(self.sample_paths, "at least one sample verdict fixture must ship with PR 3")
        overalls = {v["overall"] for v in self._load_samples().values()}
        self.assertEqual(overalls, _OVERALL, "fixtures must demonstrate both a PASS and a FAIL verdict")

    def test_samples_conform_to_contract(self):
        for name, v in self._load_samples().items():
            self.assertEqual(set(v), _TOP_LEVEL_KEYS, f"{name}: top-level keys must match the pinned contract exactly")
            self.assertIn(v["validator_status"], _VALIDATOR_STATUS, name)
            self.assertIn(v["overall"], _OVERALL, name)
            self.assertIsInstance(v["iteration"], int, name)
            self.assertGreaterEqual(v["iteration"], 1, name)
            self.assertRegex(v["head_sha"], _HEX_SHA, f"{name}: head_sha must be a hex sha")
            for f in v["findings"]:
                self.assertEqual(set(f), _FINDING_KEYS, f"{name}: finding keys must match the contract")
                self.assertIn(f["severity"], _SEVERITY, name)
                self.assertRegex(f["id"], _FINDING_ID, f"{name}: finding id {f['id']!r} malformed")
                self.assertTrue(f["evidence"] is None or isinstance(f["evidence"], str), name)
            for r in v["hallucination_risk"]:
                self.assertEqual(set(r), _RISK_KEYS, f"{name}: hallucination_risk keys must match the contract")
                self.assertIn(r["class"], _CLAIM_CLASS, name)
                self.assertIsInstance(r["grounded"], bool, name)
                self.assertTrue(r["evidence"] is None or isinstance(r["evidence"], str), name)

    def test_sample_finding_ids_exist_in_rubric(self):
        if not self.rubric_ids:
            self.skipTest("RUBRIC.md not present")
        for name, v in self._load_samples().items():
            for f in v["findings"]:
                self.assertIn(f["id"], self.rubric_ids, f"{name}: finding id {f['id']!r} not declared in RUBRIC.md")

    def test_samples_obey_pass_bar(self):
        for name, v in self._load_samples().items():
            has_blocker = any(f["severity"] == "blocker" for f in v["findings"])
            has_major = any(f["severity"] == "major" for f in v["findings"])
            all_grounded = all(r["grounded"] for r in v["hallucination_risk"])
            expected = "PASS" if (not has_blocker and not has_major and all_grounded) else "FAIL"
            self.assertEqual(v["overall"], expected, f"{name}: overall must follow the PASS bar (zero blocker+major, all grounded)")


if __name__ == "__main__":
    unittest.main()
