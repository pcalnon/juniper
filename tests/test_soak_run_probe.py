#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.1
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
3. **A spent session must survive a non-object event.** ``parse_events`` used to
   assume ``message`` is always a dict; a bare string raised ``AttributeError``
   after the Claude session was already spent (PR #1616, recovered only because
   ``stream.jsonl`` was kept). Skip that event and keep parsing. Same class:
   non-object JSONL lines (array / string / number) must not abort either.
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

    def test_pointer_path_in_a_command_arg_currently_counts_as_a_hit(self) -> None:
        # P06 false-positive (PR #1616): the probe constructs a command containing
        # `--dest docs/REFERENCE.md`, so the pointer path appears in tool_inputs
        # whether or not the document was Read. The channel is over-inclusive;
        # pin that so a future narrowing is a deliberate test break, not a silent
        # flip of follow vs source-recovered.
        parsed = {
            "tool_inputs": [json.dumps({"command": "some-tool --dest docs/REFERENCE.md"})],
            "answer": "",
        }
        ch = mod.retrieval_channel(parsed, "docs/REFERENCE.md#utility-script-reference")
        self.assertTrue(ch["pointer_doc_referenced"])
        self.assertEqual(ch["suggests"], "follow")


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

    def test_string_message_does_not_abort_the_parse(self) -> None:
        # Live defect (PR #1616): some stream-json events carry `message` as a
        # bare string. `ev.get("message") or {}` yielded the string, then `.get`
        # raised AttributeError AFTER the session was spent. The P21 run was
        # recovered only because stream.jsonl was kept. Existing tests never
        # constructed a non-dict message, so they passed both before and after.
        log = self._log(
            [
                {"type": "system", "message": "session started"},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "survived"}]}},
            ]
        )
        out = mod.parse_events(log)
        self.assertIn("survived", out["answer"])

    def test_string_message_between_valid_events_does_not_drop_the_later(self) -> None:
        # Skip must be continue, not break / raise. A later tool_use after a
        # string-message event is still extracted -- otherwise a mid-stream
        # system event would silently drop the retrieval evidence.
        log = self._log(
            [
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "first"}]}},
                {"type": "system", "message": "not an object"},
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "tool_use", "name": "Read", "input": {"file_path": "docs/REFERENCE.md"}},
                        ]
                    },
                },
            ]
        )
        out = mod.parse_events(log)
        self.assertIn("first", out["answer"])
        self.assertEqual(out["tool_calls"], ["Read"])

    def test_null_and_list_message_do_not_abort(self) -> None:
        log = self._log(
            [
                {"type": "assistant", "message": None},
                {"type": "assistant", "message": []},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "ok"}]}},
            ]
        )
        out = mod.parse_events(log)
        self.assertIn("ok", out["answer"])

    def test_result_event_with_string_message_still_records_result_meta(self) -> None:
        # Result handling is BEFORE the type-guard. Moving the guard above it
        # would drop is_error / duration_ms after a spent session.
        log = self._log(
            [
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "duration_ms": 1234,
                    "num_turns": 3,
                    "session_id": "s1",
                    "message": "done",
                    "result": "final answer from result field",
                },
            ]
        )
        out = mod.parse_events(log)
        self.assertFalse(out["result"]["is_error"])
        self.assertEqual(out["result"]["duration_ms"], 1234)
        self.assertEqual(out["result"]["num_turns"], 3)
        self.assertIn("final answer from result field", out["answer"])

    def test_non_object_json_lines_do_not_abort(self) -> None:
        # Same failure class as a string `message`: a JSON array / string /
        # number is valid JSON so JSONDecodeError does not skip it, then
        # `ev.get` raises AttributeError and the rest of a spent session is lost.
        d = Path(tempfile.mkdtemp())
        p = d / "stream.jsonl"
        p.write_text(
            '["not","an","object"]\n'
            '"bare string"\n'
            "42\n"
            '{"type":"assistant","message":{"content":[{"type":"text","text":"ok"}]}}\n',
            encoding="utf-8",
        )
        self.assertIn("ok", mod.parse_events(p)["answer"])


if __name__ == "__main__":
    unittest.main()
