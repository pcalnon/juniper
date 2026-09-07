#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/ad-hoc/register_open_set.py`` -- the AUTHORITATIVE open/fixed
counter the defect-register close protocol keys on.

``util/`` is outside every pre-commit Python hook's scope, so this suite is the
gate. Hermetic: every assertion drives ``parse_register`` / ``format_report``
over a synthetic fragment. The live register is never the fixture.

What it pins, and why it mattered:

- ``**FIXED`` is the only fixed token. Inventing ``**CLOSED`` / ``**PARKED``,
  writing ``FIXED`` without the stars, or using ``*FIXED*`` leaves the row
  counted OPEN -- the exact silent miss §1 of the register warns about, and
  the reason a WON'T FIX close still writes ``**FIXED`` with the qualification
  *inside* the marker.
- Letter-suffix ids ``001a`` / ``001b`` are distinct. ``APD-CASCOR-001`` was
  split into those two; collapsing the suffix would hide one of them.
- The same id in two table rows (the §4 detail row and the §5.1 verification
  row) is FIXED if ANY row carries the token -- union, not last-row-wins.
  Last-row-wins would un-fix an id whose verification cell omitted the marker.
- Dagger ``†`` after the id still matches. Register-original rows write
  ``| APD-DATA-001 † |``; dropping them silently shrinks both counts.
- Prefix grouping uses ``rsplit("-", 1)`` so ``APD-CASCOR-001a`` reports as
  ``APD-CASCOR``, not ``APD-CASCOR-001``.
- The headline counts unique ids, not raw table lines. Fixed ids appear twice
  by construction; a line-count headline would disagree with every other
  reading of the register.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "register_open_set.py"
REGISTER_NAME = "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"


def _load():
    spec = importlib.util.spec_from_file_location("register_open_set", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()


def _parse(*rows: str) -> tuple[set[str], set[str]]:
    return mod.parse_register("\n".join(rows) + "\n")


class TokenAndIdentityTest(unittest.TestCase):
    def test_only_starred_FIXED_counts_as_fixed(self) -> None:
        """Lookalikes stay OPEN. Mutation: ``FIXED_MARK = "FIXED"`` goes red here."""
        seen, fixed = _parse(
            "| APD-DATA-018 | No async job pattern |",
            "| APD-DATA-019 | FIXED without the stars |",
            "| APD-DATA-022 | **CLOSED (invented marker) |",
            "| APD-DATA-026 | **PARKED |",
            "| APD-DATA-008 | *FIXED* single stars |",
            "| APD-DATA-002 | **FIXED (#261) — Body limit |",
        )
        self.assertEqual(
            seen,
            {
                "APD-DATA-018",
                "APD-DATA-019",
                "APD-DATA-022",
                "APD-DATA-026",
                "APD-DATA-008",
                "APD-DATA-002",
            },
        )
        self.assertEqual(fixed, {"APD-DATA-002"})

    def test_wont_fix_still_writes_FIXED_inside_the_marker(self) -> None:
        seen, fixed = _parse(
            "| APD-SVCCORE-016 | **FIXED (won't-fix — disclosure) |",
        )
        self.assertEqual(seen, {"APD-SVCCORE-016"})
        self.assertEqual(fixed, {"APD-SVCCORE-016"})

    def test_letter_suffix_ids_are_distinct(self) -> None:
        seen, fixed = _parse(
            "| APD-CASCOR-001a | **FIXED (#x) — first half |",
            "| APD-CASCOR-001b | still open |",
        )
        self.assertEqual(seen, {"APD-CASCOR-001a", "APD-CASCOR-001b"})
        self.assertEqual(fixed, {"APD-CASCOR-001a"})
        self.assertIn("APD-CASCOR-001b", seen - fixed)

    def test_any_row_FIXED_marks_the_id_fixed(self) -> None:
        """§4 FIXED + §5.1 without the token must stay fixed.

        Mutation: last-row-wins (``if mark: add else: discard``) goes red here.
        """
        seen, fixed = _parse(
            "| APD-DATA-002 | **FIXED (#261) — Body limit |",
            "| APD-DATA-002 | verified in #261; no marker in this cell |",
        )
        self.assertEqual(seen, {"APD-DATA-002"})
        self.assertEqual(fixed, {"APD-DATA-002"})

    def test_dagger_row_still_matches(self) -> None:
        seen, fixed = _parse(
            "| APD-DATA-001 † | **FIXED (#266) — 401 path |",
            "| APD-DATA-034 † | still open, register-original |",
        )
        self.assertEqual(seen, {"APD-DATA-001", "APD-DATA-034"})
        self.assertEqual(fixed, {"APD-DATA-001"})


class ReportShapeTest(unittest.TestCase):
    def test_prefix_groups_letter_suffix_under_the_repo(self) -> None:
        seen, fixed = _parse(
            "| APD-DATA-018 | open |",
            "| APD-DATA-019 | open |",
            "| APD-CASCOR-001a | open |",
            "| APD-DATA-002 | **FIXED (#261) |",
        )
        report = mod.format_report(seen, fixed)
        self.assertIn("4 rows | 1 fixed | 3 open", report)
        self.assertRegex(report, r"APD-DATA\s+2")
        self.assertRegex(report, r"APD-CASCOR\s+1")
        self.assertNotIn("APD-CASCOR-001", report.split("OPEN by prefix:")[1].split("OPEN ids:")[0])
        self.assertIn("  APD-CASCOR-001a", report)
        self.assertIn("  APD-DATA-018", report)
        self.assertNotIn("APD-DATA-002", report.split("OPEN ids:")[1])

    def test_headline_counts_unique_ids_not_raw_lines(self) -> None:
        seen, fixed = _parse(
            "| APD-DATA-002 | **FIXED (#261) |",
            "| APD-DATA-002 | **FIXED (#261) verification |",
            "| APD-DATA-018 | open |",
            "| APD-DATA-018 | still open in another table |",
        )
        self.assertEqual(len(seen), 2)
        self.assertEqual(len(fixed), 1)
        self.assertEqual(mod.format_report(seen, fixed).splitlines()[0], "2 rows | 1 fixed | 1 open")

    def test_cli_reads_cwd_relative_register_and_import_does_not(self) -> None:
        """Operator usage is CWD-relative; importing the module must not scan."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "notes").mkdir()
            (root / "notes" / REGISTER_NAME).write_text(
                "| APD-DATA-018 | open |\n| APD-DATA-002 | **FIXED (#261) |\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(SCRIPT)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("2 rows | 1 fixed | 1 open", completed.stdout)
            self.assertIn("APD-DATA-018", completed.stdout)
            self.assertNotIn("APD-DATA-002", completed.stdout.split("OPEN ids:")[1])

        # Import already succeeded at module load; a CWD without the register
        # must not be required for parse_register to run.
        seen, fixed = mod.parse_register("| APD-ML-001 | Record it; do not action it |\n")
        self.assertEqual(seen, {"APD-ML-001"})
        self.assertEqual(fixed, set())


if __name__ == "__main__":
    unittest.main()
