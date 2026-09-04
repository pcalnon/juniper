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

import contextlib
import importlib.util
import io
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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


class TerminalVerdictDoesNotGateADryRun(unittest.TestCase):
    """The stopping rule rations billed sessions, so it must not fire on a dry run.

    Regression pin for the ordering hazard that broke CI on ml#1644 with NO code
    change: the guard ran before the --dry-run branch, so the moment three
    non-follow rows pushed the Wilson upper bound under 0.75 the dry run began
    exiting 2 with empty stdout.

    Every member here drives either the predicate directly or `main()` with the
    verdict STUBBED. Neither reads the live ledger, deliberately: the corpus is
    currently INCONCLUSIVE, so any test that shells out and asserts rc==0 passes
    whether or not the fix is present. The first version of the end-to-end member
    did exactly that and pinned nothing -- it survived a full revert.
    """

    def test_a_terminal_verdict_refuses_a_real_run(self) -> None:
        for verdict in ("BET-FAILING", "HOLDS-AT-0.75"):
            with self.subTest(verdict=verdict):
                self.assertTrue(mod.refuses_terminal_verdict(verdict, force=False, dry_run=False))

    def test_a_terminal_verdict_does_not_refuse_a_dry_run(self) -> None:
        for verdict in ("BET-FAILING", "HOLDS-AT-0.75"):
            with self.subTest(verdict=verdict):
                self.assertFalse(mod.refuses_terminal_verdict(verdict, force=False, dry_run=True))

    def test_force_still_overrides_a_real_run(self) -> None:
        self.assertFalse(mod.refuses_terminal_verdict("BET-FAILING", force=True, dry_run=False))

    def test_a_non_terminal_verdict_never_refuses(self) -> None:
        for verdict in ("INCONCLUSIVE", "IN-PROGRESS", ""):
            with self.subTest(verdict=verdict):
                self.assertFalse(mod.refuses_terminal_verdict(verdict, force=False, dry_run=False))

    def _dry_run_under(self, verdict_line: str) -> tuple[int, str, str]:
        """Drive `main()` with the ledger's verdict STUBBED, leaving dispatch real.

        The verdict must be injected rather than read. An earlier version of this
        test shelled out to the real script and asserted rc==0, which passes
        against ANY corpus whose verdict is not terminal -- i.e. it passed with
        the fix fully reverted, pinning nothing. The stub is what makes it a test
        of the ordering rather than a test of today's ledger.

        `_py` is patched selectively: the ledger call is faked, dispatch still
        runs for real, so the dry-run branch is exercised end to end.
        """
        real_py = mod._py

        def fake_py(*args, **kwargs):
            if args and args[0] == str(mod.LEDGER_TOOL):
                return subprocess.CompletedProcess(args=list(args), returncode=0, stdout=verdict_line, stderr="")
            return real_py(*args, **kwargs)

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(mod, "_py", fake_py), mock.patch.object(sys, "argv", ["soak_run_probe.py", "--dry-run"]), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = mod.main()
        return rc, out.getvalue(), err.getvalue()

    def test_dry_run_survives_a_terminal_verdict_end_to_end(self) -> None:
        """A terminal verdict must not stop the dry run reaching its own branch."""
        rc, out, err = self._dry_run_under("BET-FAILING  seeded=43/35 rate=60.5% ci=[0.456, 0.736]\n")
        self.assertEqual(rc, 0, f"dry run refused under a terminal verdict; stderr={err!r}")
        self.assertIn("priming", out.lower())

    def test_dry_run_under_a_terminal_verdict_still_reports_it(self) -> None:
        """Proceeding is not the same as concealing.

        The dry run is exempt from the stopping rule, so it must SAY that a real
        run would refuse -- otherwise the operator reads a clean dry run and
        learns nothing about the state. Pinned because deleting the notice leaves
        every other test in this file green.
        """
        rc, out, err = self._dry_run_under("BET-FAILING  seeded=43/35 rate=60.5%\n")
        # rc and the absence of REFUSING are what separate the NOTE from the guard's
        # own message -- that message ALSO names the verdict and --force, so asserting
        # only on those two strings passes against the unfixed script.
        self.assertEqual(rc, 0)
        self.assertNotIn("REFUSING", err)
        self.assertIn("BET-FAILING", err)
        self.assertIn("--force", err)
        self.assertNotIn("BET-FAILING", out, "verdict chatter must not pollute the scorer's stdout")

    def test_a_non_terminal_verdict_produces_no_notice(self) -> None:
        _, _, err = self._dry_run_under("INCONCLUSIVE  seeded=40/35 rate=65.0%\n")
        self.assertNotIn("terminal", err.lower())


if __name__ == "__main__":
    unittest.main()
