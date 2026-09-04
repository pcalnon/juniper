#!/usr/bin/env python3
"""Hermetic tests for ``util/ad-hoc/e2e_finding_triage.py``.

Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

``util/`` is outside every pre-commit Python hook, so this suite is the gate.
The script is the mechanical P0/P1 open-count for the canopy E2E Phase 2 exit
criterion (plan §6.3). A green triage that counts ACCEPTED as FIXED overstates
what shipped; counting ACCEPTED as OPEN keeps an owner-settled exit criterion
red.

Hermetic: every case feeds a TemporaryDirectory ledger. The real evidence note
is never read.
"""

from __future__ import annotations

import re
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "e2e_finding_triage.py"

_TOTAL = re.compile(
    r"total findings : (\d+)\n"
    r"  fixed        : (\d+)\n"
    r"  accepted     : (\d+)\n"
    r"  open         : (\d+)",
)


def _run(note: str, *extra: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="e2e-finding-triage-") as tmp:
        path = Path(tmp) / "ledger.md"
        path.write_text(note, encoding="utf-8")
        return subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--note", str(path), *extra],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )


def _totals(stdout: str) -> tuple[int, int, int, int]:
    match = _TOTAL.search(stdout)
    assert match is not None, f"totals block missing from:\n{stdout}"
    return tuple(int(g) for g in match.groups())  # type: ignore[return-value]


class AcceptedIsAThirdDisposition(unittest.TestCase):
    """Plan §6.3: owner sign-off closes the exit criterion without pretending a fix shipped."""

    NOTE = (
        "**F-CANOPY-004 — server lag (P0/P1 systemic; owner ACCEPTED 2026-08-26).**\n"
        "**F-CANOPY-001 — dark-mode toggle (P2, OPEN).**\n"
        "**F-CANOPY-003 — loading state (P1; VERIFIED LIVE, FIXED).**\n"
    )

    def test_accepted_is_neither_fixed_nor_open(self) -> None:
        result = _run(self.NOTE)
        self.assertEqual(result.returncode, 0, result.stderr)
        total, fixed, accepted, opened = _totals(result.stdout)
        self.assertEqual((total, fixed, accepted, opened), (3, 1, 1, 1))
        self.assertRegex(result.stdout, r"(?m)^ACCEPT P0/P1  F-CANOPY-004\b")
        self.assertRegex(result.stdout, r"(?m)^OPEN   P2     F-CANOPY-001\b")
        self.assertRegex(result.stdout, r"(?m)^FIXED  P1     F-CANOPY-003\b")

    def test_open_only_hides_fixed_and_accepted_but_keeps_full_totals(self) -> None:
        result = _run(self.NOTE, "--open-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        listing = [ln for ln in result.stdout.splitlines() if ln.startswith(("ACCEPT", "FIXED", "OPEN"))]
        self.assertEqual(len(listing), 1)
        self.assertTrue(listing[0].startswith("OPEN") and "F-CANOPY-001" in listing[0])
        self.assertNotIn("F-CANOPY-004", listing[0])
        self.assertNotIn("F-CANOPY-003", listing[0])
        self.assertEqual(_totals(result.stdout), (3, 1, 1, 1))

    def test_fixed_in_the_same_tail_wins_over_accepted(self) -> None:
        result = _run("**F-CANOPY-099 — owner ACCEPTED then landed (P1, FIXED).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (1, 1, 0, 0))
        self.assertRegex(result.stdout, r"(?m)^FIXED  P1     F-CANOPY-099\b")


class StatusTokensAndIdentity(unittest.TestCase):
    def test_healed_counts_as_fixed(self) -> None:
        result = _run("**F-E2E-001 — cascor main broken by over-deletion (CRITICAL, HEALED).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (1, 1, 0, 0))
        self.assertRegex(result.stdout, r"(?m)^FIXED  CRITICAL F-E2E-001\b")

    def test_first_heading_wins_so_a_later_fixed_cannot_close_an_open(self) -> None:
        note = (
            "**F-CANOPY-010 — still broken (P1, OPEN).**\n"
            "**F-CANOPY-010 — later closed (P1, FIXED).**\n"
        )
        result = _run(note)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (1, 0, 0, 1))
        listing = [ln for ln in result.stdout.splitlines() if "F-CANOPY-010" in ln]
        self.assertEqual(len(listing), 1)
        self.assertTrue(listing[0].startswith("OPEN"))

    def test_p0_slash_p1_is_not_classified_as_p0(self) -> None:
        result = _run("**F-CANOPY-004 — freshness contract (P0/P1 systemic; OPEN).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"(?m)^OPEN   P0/P1  F-CANOPY-004\b")
        self.assertIn("open P0/P1", result.stdout)
        self.assertNotIn("open P0      :", result.stdout)

    def test_letter_suffix_ids_are_distinct(self) -> None:
        note = (
            "**F-CANOPY-027 — original mount-order defect (P1, FIXED).**\n"
            "**F-CANOPY-027a — follow-on starvation (P1, OPEN).**\n"
        )
        result = _run(note)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (2, 1, 0, 1))
        self.assertRegex(result.stdout, r"(?m)^FIXED  P1     F-CANOPY-027\b")
        self.assertRegex(result.stdout, r"(?m)^OPEN   P1     F-CANOPY-027a\b")

    def test_untagged_header_reports_priority_question_mark(self) -> None:
        result = _run("**F-CANOPY-050 — a finding with no priority token at all.**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"(?m)^OPEN   \?      F-CANOPY-050\b")
        self.assertIn("open ?       : 1", result.stdout)

    def test_fixed_outside_the_tail_window_does_not_close_an_open_status(self) -> None:
        """Status tokens are taken from the last 170 characters of the header body.

        Searching the whole body would treat a title that says \"needs a FIXED
        remediation\" as closed while the tail still says OPEN.
        """
        body = "needs a FIXED remediation " + ("padding " * 30) + "(P1, OPEN)"
        self.assertGreater(body.find("FIXED") + 5, 0)
        self.assertLess(body.find("FIXED"), len(body) - 170)
        result = _run(f"**F-CANOPY-088 — {body}.**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (1, 0, 0, 1))
        self.assertRegex(result.stdout, r"(?m)^OPEN   P1     F-CANOPY-088\b")


if __name__ == "__main__":
    unittest.main()
