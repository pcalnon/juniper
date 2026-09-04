#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for ``util/soak_run_probe.py``. ``util/`` is outside every pre-commit Python
hook, so this suite is the only check on it.

Hermetic: nothing here launches ``claude`` or spends a probe. The event parser is
exercised against synthetic ``stream-json``.

What it pins
------------
1. **The task never reaches this script's own stdout.** ``soak_next_probe.py``
   protects the *dispatch* path; this wrapper is a second place the task passes
   through, and its stdout is read by the operator who will later SCORE the run.
   Echoing the task there re-introduces priming at the far end of the pipeline,
   after the dispatcher was careful about the near end.
2. **The retrieval channel is mechanical and honest about its limits.** A pointer
   miss is consistent with BOTH source-recovered and miss; the wrapper must not
   collapse that into a scored outcome, because correctness against the frozen
   discriminator is the judgement the protocol reserves for a scorer.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "soak_run_probe.py"
PROBES = REPO_ROOT / "conf" / "soak_probes.json"


def load_mod():
    spec = importlib.util.spec_from_file_location("soak_run_probe", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = load_mod()


def probes() -> list[dict]:
    return json.loads(PROBES.read_text(encoding="utf-8"))["probes"]


class DryRunDoesNotLeakTheTask(unittest.TestCase):
    def test_dry_run_stdout_contains_no_probe_task(self) -> None:
        r = subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--dry-run"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(r.returncode, 0)
        for p in probes():
            self.assertNotIn(p["task"].strip(), r.stdout)

    def test_dry_run_stdout_contains_no_fact_or_discriminator(self) -> None:
        r = subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--dry-run"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        for p in probes():
            for field in ("fact", "discriminator"):
                val = p.get(field)
                if isinstance(val, str) and val.strip():
                    self.assertNotIn(val.strip(), r.stdout)

    def test_dry_run_says_why_the_task_is_withheld(self) -> None:
        r = subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--dry-run"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertIn("priming", r.stdout.lower())


class RetrievalChannel(unittest.TestCase):
    def test_pointer_hit_is_detected_from_tool_inputs(self) -> None:
        parsed = {"tool_inputs": [json.dumps({"file_path": "docs/REFERENCE.md"})], "answer": ""}
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#utility-script-reference")
        self.assertTrue(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "follow")

    def test_pointer_absence_does_not_assert_a_miss(self) -> None:
        # The load-bearing honesty: no pointer hit is consistent with a CORRECT
        # source-recovered answer as well as with a wrong one.
        parsed = {"tool_inputs": [json.dumps({"file_path": "util/assert_release_tag.bash"})], "answer": ""}
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#utility-script-reference")
        self.assertFalse(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "source-recovered-or-miss")
        self.assertNotEqual(ch["suggests"], "miss")

    def test_channel_carries_its_own_caveat(self) -> None:
        ch = mod.retrieval_channel({"tool_inputs": [], "answer": ""}, "docs/REFERENCE.md#x")
        self.assertIn("MECHANICAL ONLY", ch["note"])
        self.assertIn("judgement", ch["note"].lower())

    def test_anchor_is_stripped_before_matching(self) -> None:
        ch = mod.retrieval_channel({"tool_inputs": [], "answer": ""}, "docs/REFERENCE.md#deep-anchor")
        self.assertEqual(ch["pointer_doc"], "docs/REFERENCE.md")


class EventParsing(unittest.TestCase):
    def _log(self, lines: list[dict]) -> Path:
        d = Path(tempfile.mkdtemp())
        p = d / "stream.jsonl"
        p.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
        return p

    def test_extracts_answer_and_tool_calls(self) -> None:
        log = self._log(
            [
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "tool_use", "name": "Read", "input": {"file_path": "util/x.bash"}},
                        ]
                    },
                },
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "the answer"}]}},
                {"type": "result", "subtype": "success", "is_error": False, "num_turns": 2},
            ]
        )
        out = mod.parse_events(log)
        self.assertIn("the answer", out["answer"])
        self.assertEqual(out["tool_calls"], ["Read"])
        self.assertFalse(out["result"]["is_error"])

    def test_malformed_lines_do_not_abort_the_parse(self) -> None:
        d = Path(tempfile.mkdtemp())
        p = d / "stream.jsonl"
        p.write_text('not json\n{"type":"assistant","message":{"content":[{"type":"text","text":"ok"}]}}\n', encoding="utf-8")
        self.assertIn("ok", mod.parse_events(p)["answer"])

    def test_empty_log_yields_no_answer_rather_than_crashing(self) -> None:
        d = Path(tempfile.mkdtemp())
        p = d / "stream.jsonl"
        p.write_text("", encoding="utf-8")
        out = mod.parse_events(p)
        self.assertEqual(out["answer"], "")
        self.assertEqual(out["tool_calls"], [])


if __name__ == "__main__":
    unittest.main()


class RetrievalChannelIgnoresAnswerText(unittest.TestCase):
    """A mention of the pointer in PROSE is not retrieval.

    Regression, found live on 2026-09-04 by probe P15. The first version of
    `retrieval_channel` searched tool inputs AND the answer text, so a run whose
    answer merely said "before the docs/REFERENCE.md relocation cut it to ~35k"
    scored as a follow -- while zero tool calls had touched the document.

    That is the worst possible direction for this instrument to fail in: a model
    reciting the pointer's path without opening it is the strongest example of
    NOT following the pointer, and the channel credited it as the opposite.
    """

    def test_answer_mention_alone_is_not_a_follow(self) -> None:
        parsed = {
            "tool_inputs": [json.dumps({"file_path": "util/some_helper.bash"})],
            "answer": "I checked; before the docs/REFERENCE.md relocation this was larger.",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#some-anchor")
        self.assertFalse(
            ch["pointer_doc_referenced"],
            "naming the pointer in prose must not count as retrieving it",
        )
        self.assertEqual(ch["suggests"], "source-recovered-or-miss")

    def test_tool_input_hit_is_still_a_follow(self) -> None:
        parsed = {
            "tool_inputs": [json.dumps({"command": "sed -n '10,40p' docs/REFERENCE.md"})],
            "answer": "no mention of the doc here at all",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#some-anchor")
        self.assertTrue(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "follow")

    def test_empty_tool_inputs_with_rich_answer_is_not_a_follow(self) -> None:
        parsed = {
            "tool_inputs": [],
            "answer": "docs/REFERENCE.md docs/REFERENCE.md docs/REFERENCE.md",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#x")
        self.assertFalse(ch["pointer_doc_referenced"])
