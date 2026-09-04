#!/usr/bin/env python3
"""Hermetic tests for ``pri_of`` first-token-in-prose (not the parenthetical).

Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

``tests/test_e2e_finding_triage.py`` (#1642) pins dispositions (ACCEPTED / FIXED /
HEALED, first heading, tail-170). Every header in that suite puts the priority
as the FIRST (or only) severity token in the parenthetical, so it cannot see
the F-CANOPY-037 close: prose ``P0/P1`` before ``(LEDGER; …)`` is triaged
**P0/P1**, and the finding stays in the Phase 2 P0/P1 open-count.

This suite is that leftover. ``util/`` is outside every pre-commit Python hook,
so this unittest is the gate. Hermetic temp ledgers; the real evidence note is
never read. Do not open a second PR on this file.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "e2e_finding_triage.py"


def _load():
    spec = importlib.util.spec_from_file_location("e2e_finding_triage", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()


def _run(note: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="e2e-finding-pri-") as tmp:
        path = Path(tmp) / "ledger.md"
        path.write_text(note, encoding="utf-8")
        return subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--note", str(path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )


class FirstTokenInProse(unittest.TestCase):
    """The token in the header prose wins, even when a later parenthetical disagrees."""

    def test_prose_p0_slash_p1_beats_later_ledger(self) -> None:
        """F-037 shape: 'holding the arc's only P0/P1 open' before (LEDGER)."""
        self.assertEqual(
            mod.pri_of("holding the arc's only P0/P1 open (LEDGER; OPEN)"),
            "P0/P1",
        )

    def test_prose_not_a_p2_is_still_the_first_token(self) -> None:
        """The footgun the operator surface warns about — do not name another severity."""
        self.assertEqual(mod.pri_of("this is not a P2 (P1; OPEN)"), "P2")

    def test_critical_in_prose_beats_later_p2(self) -> None:
        self.assertEqual(mod.pri_of("the CRITICAL remaining hole (P2; OPEN)"), "CRITICAL")

    def test_parenthetical_only_is_still_the_first_token(self) -> None:
        self.assertEqual(mod.pri_of("freshness contract (P1; OPEN)"), "P1")

    def test_ledger_only_when_it_is_the_first_token(self) -> None:
        self.assertEqual(mod.pri_of("census row (LEDGER; OPEN)"), "LEDGER")

    def test_p0_slash_p1_in_prose_is_not_classified_as_p0(self) -> None:
        """Alternation order PLUS first-token: #1642 only covers the parenthetical-only case."""
        self.assertEqual(mod.pri_of("the remaining P0/P1 (P0; OPEN)"), "P0/P1")

    def test_first_of_two_parentheticals_wins(self) -> None:
        self.assertEqual(mod.pri_of("renamed (P2; was P1) (P1; OPEN)"), "P2")

    def test_untagged_body_is_question_mark(self) -> None:
        self.assertEqual(mod.pri_of("a finding with no priority token at all"), "?")


class WordBoundariesAndCase(unittest.TestCase):
    def test_p10_is_not_p1(self) -> None:
        self.assertEqual(mod.pri_of("walkthrough P10 (P2; OPEN)"), "P2")

    def test_embedded_p1_is_not_a_token(self) -> None:
        self.assertEqual(mod.pri_of("the AP1x follow-on (P2; OPEN)"), "P2")

    def test_lowercase_p1_is_not_a_token(self) -> None:
        self.assertEqual(mod.pri_of("mentions p1 in passing (P2; OPEN)"), "P2")


class CliUsesPriOf(unittest.TestCase):
    def test_cli_triages_prose_p0_slash_p1_as_p0_slash_p1_not_ledger(self) -> None:
        result = _run(
            "**F-CANOPY-037 — holding the arc's only P0/P1 open (LEDGER; OPEN).**\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"(?m)^OPEN   P0/P1  F-CANOPY-037\b")
        self.assertIn("open P0/P1", result.stdout)
        self.assertNotIn("open LEDGER", result.stdout)

    def test_cli_triages_not_a_p2_as_p2(self) -> None:
        result = _run("**F-CANOPY-099 — this is not a P2 (P1; OPEN).**\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"(?m)^OPEN   P2     F-CANOPY-099\b")
        self.assertIn("open P2", result.stdout)
        self.assertNotIn("open P1", result.stdout)


class PriOfIsTheSharedImplementation(unittest.TestCase):
    def test_pri_of_is_module_level(self) -> None:
        self.assertTrue(callable(mod.pri_of))

    def test_main_calls_pri_of_not_an_inline_search(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        calls = [
            n.func.id
            for n in ast.walk(main)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        ]
        self.assertIn("pri_of", calls)
        self.assertTrue(
            any(
                isinstance(n, ast.Constant) and isinstance(n.value, str) and "P0/P1" in n.value
                for n in ast.walk(tree)
            ),
            "pri_of must keep the P0/P1-first alternation",
        )


class AlternationOrder(unittest.TestCase):
    def test_regex_lists_p0_slash_p1_before_p0(self) -> None:
        """A rewrite that searches P0 first would classify P0/P1 as P0."""
        source = SCRIPT.read_text(encoding="utf-8")
        match = re.search(r"P0/P1\|P0\|P1\|P2\|CRITICAL\|LEDGER", source)
        self.assertIsNotNone(match)
        self.assertLess(source.index("P0/P1"), source.index("P0|P1|P2"))


if __name__ == "__main__":
    unittest.main()
