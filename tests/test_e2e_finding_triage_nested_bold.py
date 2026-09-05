#!/usr/bin/env python3
"""Hermetic tests for nested-bold header truncation in ``e2e_finding_triage.py``.

Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

``tests/test_e2e_finding_triage.py`` (#1642) pins dispositions (FIXED / HEALED /
ACCEPTED, first heading, tail-170) on headers with a single ``**`` pair.
``tests/test_e2e_finding_triage_priority.py`` (#1712) pins ``pri_of`` on a
pre-extracted body. Neither feeds a header whose body contains
``**CLOSED date**`` — the F-CANOPY-037 close shape in
``notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md``.

The header regex is non-greedy to the first ``**``. Nested bold therefore
truncates the body: CLOSED never reaches the disposition parser (CLOSED is
not a disposition anyway), and the Phase 2 open-P0/P1 count then depends on
whether ``mechanism FIXED`` appears *before* the inner ``**``.

``util/`` is outside every pre-commit Python hook, so this suite is the gate.
Hermetic temp ledgers; the real evidence note is never read.
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

# `withdrawn` is matched but not returned -- it arrived after this suite was written, and
# the regex, expecting `accepted` to be followed by `open`, then matched NOTHING. Required
# rather than optional: a disposition disappearing from the operator summary should fail
# here. The `\s+` separators are this file's own style and are kept.
_TOTAL = re.compile(
    r"total findings\s*:\s*(\d+)\s+" r"fixed\s*:\s*(\d+)\s+" r"accepted\s*:\s*(\d+)\s+" r"withdrawn\s*:\s*\d+\s+" r"open\s*:\s*(\d+)",
)
_OPEN_P0P1 = re.compile(r"open P0/P1\s*:\s*(\d+)")


def _run(note: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="e2e-finding-nested-") as tmp:
        path = Path(tmp) / "ledger.md"
        path.write_text(note, encoding="utf-8")
        return subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--note", str(path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )


def _totals(stdout: str) -> tuple[int, int, int, int]:
    match = _TOTAL.search(stdout)
    assert match is not None, f"totals block missing from:\n{stdout}"
    return tuple(int(g) for g in match.groups())  # type: ignore[return-value]


def _open_p0p1(stdout: str) -> int:
    match = _OPEN_P0P1.search(stdout)
    return int(match.group(1)) if match else 0


class NestedBoldTruncatesTheHeader(unittest.TestCase):
    """An inner ``**`` ends the header body. Tokens after it are invisible."""

    def test_nested_closed_without_fixed_stays_open(self) -> None:
        """The F-037 close token, alone, never reaches the disposition parser."""
        result = _run("**F-CANOPY-037 — graph race (P0/P1; **CLOSED 2026-09-04** on the owed re-drive).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (1, 0, 0, 1))
        self.assertRegex(result.stdout, r"(?m)^OPEN\s+P0/P1\s+F-CANOPY-037\b")
        self.assertEqual(_open_p0p1(result.stdout), 1)
        self.assertNotIn("CLOSED", result.stdout.split("total findings")[0])

    def test_f037_shape_mechanism_fixed_before_nested_closed_is_fixed(self) -> None:
        """Current close: FIXED sits before the inner ``**``, so the count drops."""
        result = _run("**F-CANOPY-037 — graph race (P0/P1; mechanism FIXED canopy#531; " "**CLOSED 2026-09-04** on the owed re-drive).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (1, 1, 0, 0))
        self.assertRegex(result.stdout, r"(?m)^FIXED\s+P0/P1\s+F-CANOPY-037\b")
        self.assertEqual(_open_p0p1(result.stdout), 0)

    def test_fixed_after_the_inner_bold_is_invisible(self) -> None:
        """Swap the order and the same finding stays in the open P0/P1 bucket."""
        result = _run("**F-CANOPY-037 — graph race (P0/P1; **CLOSED 2026-09-04**; mechanism FIXED).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (1, 0, 0, 1))
        self.assertRegex(result.stdout, r"(?m)^OPEN\s+P0/P1\s+F-CANOPY-037\b")
        self.assertEqual(_open_p0p1(result.stdout), 1)

    def test_nested_fixed_truncates_before_the_token(self) -> None:
        """Bolding FIXED hides it. The finding stays OPEN."""
        result = _run("**F-CANOPY-037 — graph race (P0/P1; **FIXED**; still OPEN).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (1, 0, 0, 1))
        self.assertRegex(result.stdout, r"(?m)^OPEN\s+P0/P1\s+F-CANOPY-037\b")

    def test_multiline_header_inner_bold_still_truncates(self) -> None:
        """``re.S`` lets the match cross a newline; the first ``**`` still wins."""
        result = _run("**F-CANOPY-037 — graph race (P0/P1;\n" "mechanism still open; **CLOSED 2026-09-04** on the owed re-drive).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (1, 0, 0, 1))
        self.assertRegex(result.stdout, r"(?m)^OPEN\s+P0/P1\s+F-CANOPY-037\b")


class ClosedIsNotADisposition(unittest.TestCase):
    def test_plain_closed_without_fixed_stays_open(self) -> None:
        """Even a well-formed header: CLOSED is not FIXED / HEALED / ACCEPTED."""
        result = _run("**F-CANOPY-037 — graph race (P0/P1; CLOSED 2026-09-04).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (1, 0, 0, 1))
        self.assertRegex(result.stdout, r"(?m)^OPEN\s+P0/P1\s+F-CANOPY-037\b")
        self.assertEqual(_open_p0p1(result.stdout), 1)

    def test_well_formed_fixed_still_closes(self) -> None:
        """Negative control: a single ``**`` pair with FIXED still counts."""
        result = _run("**F-CANOPY-003 — loading state (P1; VERIFIED LIVE, FIXED).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_totals(result.stdout), (1, 1, 0, 0))
        self.assertRegex(result.stdout, r"(?m)^FIXED\s+P1\s+F-CANOPY-003\b")


class NestedBoldDoesNotInventARow(unittest.TestCase):
    def test_inner_bold_is_not_a_second_finding(self) -> None:
        result = _run("**F-CANOPY-037 — graph race (P0/P1; **CLOSED 2026-09-04** on the owed re-drive).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        listing = [ln for ln in result.stdout.splitlines() if "F-CANOPY-037" in ln]
        self.assertEqual(len(listing), 1)
        self.assertEqual(_totals(result.stdout), (1, 0, 0, 1))


class HeaderRegexIsNongreedyFirstBold(unittest.TestCase):
    def test_source_uses_nongreedy_body_then_bold(self) -> None:
        """A greedy rewrite would swallow the inner ``**`` and see CLOSED / trailing FIXED."""
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn(r"(.*?)\*\*", source)
        greedy = re.search(r" — \(\.\*\)\\\*\\\*", source)
        self.assertIsNone(greedy, "header body must stay non-greedy (.*?), not greedy (.*)")


if __name__ == "__main__":
    unittest.main()
