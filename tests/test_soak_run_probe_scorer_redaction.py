#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for the scoring-packet redaction in ``util/soak_run_probe.py``.

``util/`` is outside every pre-commit Python hook, so this suite is the only
check on the filter. Complementary to ``tests/test_soak_run_probe.py``
(retrieval channel + parse_events) -- do not fold these into that file.

Hermetic: the helper is a pure string transform. One integration arm drives
the real ``soak_next_probe.py --reveal`` so a rename of the coverage line
cannot silently disable the filter. Nothing here launches ``claude`` or
consults a terminal soak verdict.

Why this suite exists
---------------------
Finding 3 of
``notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md``:
an earlier version embedded ``--reveal`` stdout verbatim in
``scoring_packet.md``. The isolated scorer then read a coverage tally sitting
beside the discriminator -- the one artifact built to keep the scorer from
having a stake in how the corpus is progressing.

A test must be able to fail for the reason it exists:

* drop the filter entirely and the tally reaches the packet;
* search the whole line with ``in`` and a discriminator that *names*
  ``post-interv.`` is stripped with the tally;
* loosen to ``startswith("post-interv")`` (no dot) and a keep-me line
  ``post-interv-note:`` disappears.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "soak_run_probe.py"
DISPATCH = REPO_ROOT / "util" / "soak_next_probe.py"
PROBES = REPO_ROOT / "conf" / "soak_probes.json"

# Distinctive tally that must never appear in a redacted packet unless some
# OTHER reveal field also carries it. The coverage line is the only place this
# token appears in the synthetic reveal below.
_TALLY = "9917 run(s)"
_COVERAGE = f"post-interv.  : {_TALLY}"

_REVEAL = (
    "probe_id      : P99-synthetic\n"
    "severity      : hazard    area: publish\n"
    "fact          : a frozen fact the scorer must still see\n"
    "pointer       : docs/REFERENCE.md#utility-script-reference\n"
    "evidence      : the evidence line\n"
    "discriminator : name the post-interv. coverage line without following it\n"
    f"{_COVERAGE}\n"
    "\n"
    "Record with:\n"
    "  python3 util/soak_ledger.py probe-run --probe-id P99-synthetic \\\n"
    "      --outcome follow|source-recovered|miss --session S --scored-by who\n"
)


def load_mod():
    spec = importlib.util.spec_from_file_location("soak_run_probe_scorer_redaction", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = load_mod()


def _packet(scorer_reveal: str) -> str:
    """The scoring-packet fragment main() builds around the redacted reveal."""
    return (
        "# Scoring packet -- P99-synthetic\n\n"
        "## Discriminator, pointer and fact (from --reveal)\n\n"
        f"```\n{scorer_reveal}```\n"
    )


class RedactRevealForScorer(unittest.TestCase):
    """Pure function. No subprocess, no live ledger."""

    def test_coverage_line_is_stripped(self) -> None:
        out = mod.redact_reveal_for_scorer(_REVEAL)
        self.assertNotIn(_COVERAGE, out)
        self.assertNotIn(_TALLY, out)

    def test_discriminator_pointer_and_fact_survive(self) -> None:
        out = mod.redact_reveal_for_scorer(_REVEAL)
        self.assertIn("discriminator : name the post-interv. coverage line", out)
        self.assertIn("pointer       : docs/REFERENCE.md#utility-script-reference", out)
        self.assertIn("fact          : a frozen fact the scorer must still see", out)

    def test_mid_line_mention_is_not_a_coverage_line(self) -> None:
        # THE startswith contract. ``"post-interv." in ln`` would drop this
        # discriminator -- a scorer that named the leak would lose the
        # judgement the packet exists to carry.
        line = "discriminator : name the post-interv. coverage line without following it"
        self.assertIn("post-interv.", line)
        out = mod.redact_reveal_for_scorer(line + "\n")
        self.assertEqual(out, line + "\n")

    def test_post_interv_note_prefix_without_the_dot_is_kept(self) -> None:
        # startswith("post-interv") -- no dot -- would strip this.
        line = "post-interv-note: keep this, it is not the coverage tally"
        out = mod.redact_reveal_for_scorer(line + "\n")
        self.assertEqual(out, line + "\n")

    def test_empty_and_whitespace_stay_empty(self) -> None:
        self.assertEqual(mod.redact_reveal_for_scorer(""), "")
        # splitlines() keeps the whitespace-only line and the blank line;
        # each is re-joined with a trailing newline. Nothing is invented.
        self.assertEqual(mod.redact_reveal_for_scorer("   \n\n"), "   \n\n")

    def test_every_coverage_line_is_stripped(self) -> None:
        raw = "keep\npost-interv.  : 1 run(s)\nkeep2\npost-interv.  : 2 run(s)\n"
        out = mod.redact_reveal_for_scorer(raw)
        self.assertEqual(out, "keep\nkeep2\n")

    def test_scoring_packet_never_carries_the_tally(self) -> None:
        packet = _packet(mod.redact_reveal_for_scorer(_REVEAL))
        self.assertNotIn(_TALLY, packet)
        self.assertNotIn(_COVERAGE, packet)
        self.assertIn("a frozen fact the scorer must still see", packet)
        self.assertIn("name the post-interv. coverage line", packet)

    def test_main_calls_the_helper(self) -> None:
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("scorer_reveal = redact_reveal_for_scorer(reveal.stdout)", src)
        # The filter expression must live in exactly one place -- the helper.
        # A second inline copy next to the call would silently fork the contract.
        self.assertEqual(src.count('if not ln.startswith("post-interv.")'), 1)


class LiveRevealPrefixStillMatches(unittest.TestCase):
    """The real ``--reveal`` line must still start with the prefix the filter uses.

    A rename of ``post-interv.`` in ``soak_next_probe.py`` would leave the unit
    tests green (they use a synthetic line) and re-open finding 3.
    """

    def test_real_reveal_coverage_line_is_redacted(self) -> None:
        probes = json.loads(PROBES.read_text(encoding="utf-8"))["probes"]
        self.assertTrue(probes)
        probe_id = probes[0]["probe_id"]
        r = subprocess.run(  # nosec B603
            [sys.executable, str(DISPATCH), "--reveal", "--probe-id", probe_id],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        coverage_lines = [ln for ln in r.stdout.splitlines() if ln.startswith("post-interv.")]
        self.assertTrue(coverage_lines, "soak_next_probe --reveal no longer prints a post-interv. line")
        out = mod.redact_reveal_for_scorer(r.stdout)
        for ln in coverage_lines:
            self.assertNotIn(ln, out)
        self.assertIn("discriminator", out)
        self.assertIn(probe_id, out)


if __name__ == "__main__":
    unittest.main()
