#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for ``util/ad-hoc/2026-08-21_soak_probe_evidence.py``.

``util/`` is outside every pre-commit Python hook, so this suite is the only
check on it. Hermetic: every transcript is a TemporaryDirectory jsonl; nothing
reads ``~/.claude`` or a live session.

Why this suite exists
---------------------
The pointer-follow soak scores a run on whether the session *demonstrably
retrieved* the relocated fact. Reciting ``docs/REFERENCE.md`` in answer prose
is the strongest possible example of *not* following the pointer -- and it is
exactly the defect that inflated follows (PR #1644 / P15). This extractor is
the independent evidence channel the scorer is supposed to see, and it had
zero tests.

A test must be able to fail for the reason it exists.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-08-21_soak_probe_evidence.py"

# Distinctive prose that must never leak into the scorer's view. The name trips
# bandit B105 (hardcoded_password_string), which fires on any *SECRET* identifier
# bound to a literal -- this is a test sentinel, not a credential. Space-separated
# code on purpose: the comma form under-suppresses and still reads as applied.
SECRET_PROSE = "SECRET_FACT_per_run_timeout_seconds_must_not_reach_stdout"  # nosec B105


def load_mod():
    spec = importlib.util.spec_from_file_location("soak_probe_evidence", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = load_mod()


def write_transcript(tmp: Path, records: list[object], name: str = "t.jsonl") -> Path:
    p = tmp / name
    lines = [r if isinstance(r, str) else json.dumps(r) for r in records]
    p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return p


def tool_use(name: str, **inp: object) -> dict:
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}}


def tool_result(content: object) -> dict:
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": content}]}}


def assistant_text(text: str) -> dict:
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


class RetrievalIsToolLayerOnly(unittest.TestCase):
    def test_opening_pointer_doc_in_tool_input_is_retrieved(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(Path(t), [tool_use("Read", file_path="docs/REFERENCE.md")])
            out = mod.scan(path)
        self.assertTrue(out["retrieved"])
        self.assertGreaterEqual(out["dest_hits"], 1)
        self.assertEqual(out["dest_via_output"], 0)

    def test_reciting_pointer_path_in_assistant_text_is_not_retrieved(self) -> None:
        # THE #1644 class. P15 named the file in the answer ("before the
        # docs/REFERENCE.md relocation...") with zero tool calls touching it.
        # Counting that as a follow is the opposite of the measurement.
        with TemporaryDirectory() as t:
            path = write_transcript(
                Path(t),
                [assistant_text("before the docs/REFERENCE.md relocation cut it to ~35k")],
            )
            out = mod.scan(path)
        self.assertFalse(out["retrieved"])
        self.assertEqual(out["dest_hits"], 0)
        self.assertEqual(out["dest_via_output"], 0)

    def test_pointer_doc_in_tool_result_is_retrieved_via_output(self) -> None:
        # 2026-08-21: `grep -rn term docs/` retrieved REFERENCE.md content
        # without the path ever appearing in the command. Scanning only
        # tool_use inputs reported zero refs while the run cited line numbers.
        with TemporaryDirectory() as t:
            path = write_transcript(
                Path(t),
                [
                    tool_use("Bash", command="grep -rn per_run_timeout docs/"),
                    tool_result("docs/REFERENCE.md:120:per_run_timeout_seconds: 30"),
                ],
            )
            out = mod.scan(path)
        self.assertTrue(out["retrieved"])
        self.assertEqual(out["dest_hits"], 0)
        self.assertGreaterEqual(out["dest_via_output"], 1)


class Contamination(unittest.TestCase):
    def test_answer_key_in_tool_input_contaminates(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(Path(t), [tool_use("Read", file_path="conf/soak_probes.json")])
            out = mod.scan(path)
        self.assertTrue(out["contaminated"])
        self.assertGreaterEqual(out["contamination_hits"], 1)

    def test_protocol_doc_in_tool_input_contaminates(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(
                Path(t),
                [tool_use("Grep", pattern="x", path="notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md")],
            )
            out = mod.scan(path)
        self.assertTrue(out["contaminated"])

    def test_answer_key_in_tool_result_contaminates(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(
                Path(t),
                [tool_use("Glob", glob_pattern="conf/*"), tool_result("conf/soak_probes.json")],
            )
            out = mod.scan(path)
        self.assertTrue(out["contaminated"])

    def test_protocol_doc_in_tool_result_is_currently_invisible(self) -> None:
        # Characterization: PROTOCOL_DOC is checked on tool_use input only.
        # A grep that returns the ledger filename in tool_result does not
        # currently flag contamination. Pin so a silent widening or narrowing
        # cannot land unreviewed.
        with TemporaryDirectory() as t:
            path = write_transcript(
                Path(t),
                [tool_use("Glob", glob_pattern="notes/*SOAK*"), tool_result("POINTER-FOLLOW-SOAK-LEDGER.md")],
            )
            out = mod.scan(path)
        self.assertFalse(out["contaminated"])


class ParseHonesty(unittest.TestCase):
    def test_malformed_json_is_skipped_not_raised(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(Path(t), ["not json", tool_use("Read", file_path="docs/REFERENCE.md")])
            out = mod.scan(path)
        self.assertTrue(out["retrieved"])
        self.assertEqual(out["records"], 2)

    def test_empty_transcript_is_not_retrieved(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(Path(t), [])
            out = mod.scan(path)
        self.assertFalse(out["retrieved"])
        self.assertFalse(out["contaminated"])
        self.assertEqual(out["records"], 0)
        self.assertEqual(out["tool_calls"], 0)

    def test_unprefixed_paths_are_not_collected(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(Path(t), [tool_use("Read", file_path="/tmp/scratch.py")])
            out = mod.scan(path)
        collected = [name for name, _n in out["files"]]
        self.assertNotIn("/tmp/scratch.py", collected)
        self.assertNotIn("scratch.py", collected)

    def test_prefixed_repo_paths_are_collected(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(Path(t), [tool_use("Read", file_path="util/soak_ledger.py")])
            out = mod.scan(path)
        collected = [name for name, _n in out["files"]]
        self.assertIn("util/soak_ledger.py", collected)


class CliDoesNotLeakMessageText(unittest.TestCase):
    def _run(self, path: Path, *flags: str) -> subprocess.CompletedProcess:
        return subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--path", str(path), *flags],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_human_stdout_never_echoes_transcript_prose(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(
                Path(t),
                [
                    assistant_text(SECRET_PROSE),
                    tool_use("Read", file_path="docs/REFERENCE.md"),
                ],
            )
            r = self._run(path)
        self.assertEqual(r.returncode, 0)
        self.assertNotIn(SECRET_PROSE, r.stdout)
        self.assertNotIn(SECRET_PROSE, r.stderr)
        self.assertIn("RETRIEVED docs/REFERENCE.md", r.stdout)

    def test_recitation_only_prints_did_not_open(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(
                Path(t),
                [assistant_text(f"I followed {mod.DEST} because {SECRET_PROSE}")],
            )
            r = self._run(path)
        self.assertEqual(r.returncode, 0)
        self.assertIn("did NOT open docs/REFERENCE.md", r.stdout)
        self.assertNotIn(SECRET_PROSE, r.stdout)

    def test_json_shape_carries_retrieved_and_contaminated(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(Path(t), [tool_use("Read", file_path="conf/soak_probes.json")])
            r = self._run(path, "--json")
        self.assertEqual(r.returncode, 0)
        payload = json.loads(r.stdout)
        self.assertEqual(len(payload), 1)
        row = next(iter(payload.values()))
        self.assertFalse(row["retrieved"])
        self.assertTrue(row["contaminated"])
        self.assertNotIn(SECRET_PROSE, r.stdout)


if __name__ == "__main__":
    unittest.main()
