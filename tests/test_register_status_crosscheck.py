#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/ad-hoc/register_status_crosscheck.py`` -- the independent third
reading of the defect register.

``register_open_set.py`` and ``grep -cE '\\*\\*FIXED'`` both read the §4 table
rows, so they can agree with each other and still both be wrong. This script is
the one that would catch a close-protocol miss (FIXED in §4, absent from §2 or
§5.1, or listed in §2 while the table row is still OPEN). ``util/`` is outside
every pre-commit Python hook's scope, so this suite is the gate.

Hermetic: fixtures are strings. The live register is never opened.
"""

from __future__ import annotations

import importlib.util
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "register_status_crosscheck.py"


def _load():
    spec = importlib.util.spec_from_file_location("register_status_crosscheck", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()


def _doc(
    *,
    prose: str,
    section4: list[str],
    section51: list[str],
    include_s4: bool = True,
    include_s5: bool = True,
    include_s51: bool = True,
    include_s52: bool = True,
) -> str:
    """Minimal register with the headings the parser keys on."""
    parts = [
        "# Defect Register",
        "",
        "## 2. Status",
        prose,
        "",
    ]
    if include_s4:
        parts.extend(["## 4. Full register", "", *section4, ""])
    if include_s5:
        parts.append("## 5. Fixed findings")
        if include_s51:
            parts.extend(
                [
                    "",
                    "### 5.1 Fixed since this register was published",
                    "",
                    "| ID | Finding | Fixed by | Verification |",
                    "| --- | --- | --- | --- |",
                    *section51,
                    "",
                ]
            )
        if include_s52:
            parts.extend(["### 5.2 Fixed before this register", ""])
    return "\n".join(parts) + "\n"


def _row4(entry_id: str, cell: str) -> str:
    return f"| {entry_id} | {cell} | S | src | 1 | High |"


def _row51(entry_id: str, verification: str = "verified") -> str:
    return f"| {entry_id} | finding | pr | {verification} |"


def _run(text: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = mod.crosscheck(text)
    return rc, out.getvalue(), err.getvalue()


class RegisterStatusCrosscheckTest(unittest.TestCase):
    def test_agree_when_the_three_sets_match(self):
        rc, out, _ = _run(
            _doc(
                prose="**Two have since been fixed** — `APD-DATA-001`, `APD-CASCOR-001a`.",
                section4=[
                    _row4("APD-DATA-001 †", "**FIXED (#1)** — done"),
                    _row4("APD-CASCOR-001a", "**FIXED (#2)** — done"),
                    _row4("APD-DATA-008", "still open — cache hit returns 201"),
                ],
                section51=[_row51("APD-DATA-001"), _row51("APD-CASCOR-001a")],
            )
        )
        self.assertEqual(rc, 0, out)
        self.assertIn("AGREE", out)
        self.assertNotIn("DISAGREE", out)

    def test_disagree_when_section4_fixed_is_missing_from_prose(self):
        """Close protocol missed touch 4: the §2 status paragraph."""
        rc, out, _ = _run(
            _doc(
                prose="**One have since been fixed** — `APD-DATA-001`.",
                section4=[
                    _row4("APD-DATA-001", "**FIXED (#1)** — done"),
                    _row4("APD-DATA-002", "**FIXED (#2)** — done"),
                ],
                section51=[_row51("APD-DATA-001"), _row51("APD-DATA-002")],
            )
        )
        self.assertEqual(rc, 1, out)
        self.assertIn("DISAGREE", out)
        self.assertIn("APD-DATA-002", out)
        self.assertIn("absent from §2 prose", out)

    def test_disagree_when_prose_lists_an_open_row(self):
        """Close protocol inverted: §2 names an id whose §4 row is still OPEN."""
        rc, out, _ = _run(
            _doc(
                prose="**Two have since been fixed** — `APD-DATA-001`, `APD-DATA-008`.",
                section4=[
                    _row4("APD-DATA-001", "**FIXED (#1)** — done"),
                    _row4("APD-DATA-008", "still open — cache hit returns 201"),
                ],
                section51=[_row51("APD-DATA-001"), _row51("APD-DATA-008")],
            )
        )
        self.assertEqual(rc, 1, out)
        self.assertIn("DISAGREE", out)
        self.assertIn("APD-DATA-008", out)
        self.assertIn("NOT **FIXED in §4", out)

    def test_disagree_when_section4_fixed_is_missing_from_section51(self):
        """Close protocol missed touch 3: the §5.1 verification row."""
        rc, out, _ = _run(
            _doc(
                prose="**Two have since been fixed** — `APD-DATA-001`, `APD-DATA-002`.",
                section4=[
                    _row4("APD-DATA-001", "**FIXED (#1)** — done"),
                    _row4("APD-DATA-002", "**FIXED (#2)** — done"),
                ],
                section51=[_row51("APD-DATA-001")],
            )
        )
        self.assertEqual(rc, 1, out)
        self.assertIn("DISAGREE", out)
        self.assertIn("APD-DATA-002", out)
        self.assertIn("absent from §5.1 rows", out)

    def test_missing_section51_headings_are_an_error_not_an_agree(self):
        rc, _, err = _run(
            _doc(
                prose="**One have since been fixed** — `APD-DATA-001`.",
                section4=[_row4("APD-DATA-001", "**FIXED (#1)** — done")],
                section51=[],
                include_s51=False,
                include_s52=False,
            )
        )
        self.assertEqual(rc, 1)
        self.assertIn("could not locate §5.1/§5.2 headings", err)

    def test_missing_section4_heading_is_an_error_not_an_agree(self):
        """The §4 window is fail-closed: no heading means no census, not empty-and-AGREE."""
        rc, _, err = _run(
            _doc(
                prose="**One have since been fixed** — `APD-DATA-001`.",
                section4=[],
                section51=[_row51("APD-DATA-001")],
                include_s4=False,
            )
        )
        self.assertEqual(rc, 1)
        self.assertIn("could not locate §4/§5 headings", err)

    def test_dagger_and_letter_suffix_are_the_id(self):
        """NEGATIVE CONTROL on the id regex. `†` and `001a` must not drop or split the id."""
        rc, out, _ = _run(
            _doc(
                prose="**Two have since been fixed** — `APD-DATA-001`, `APD-CASCOR-001b`.",
                section4=[
                    _row4("APD-DATA-001 †", "**FIXED (#1)** — done"),
                    _row4("APD-CASCOR-001b", "**FIXED (#2)** — done"),
                ],
                section51=[_row51("APD-DATA-001"), _row51("APD-CASCOR-001b")],
            )
        )
        self.assertEqual(rc, 0, out)
        self.assertIn("2 marked **FIXED", out)

    def test_section51_fixed_token_does_not_poison_an_open_section4_row(self):
        """The hole this window exists to close.

        A §5.1 verification cell that mentions ``**FIXED`` used to add that id to
        ``table_fixed``. Combined with a §2 list that named the still-OPEN §4 row,
        all three sets agreed and the script printed AGREE -- the exact lie it
        was written to catch.
        """
        rc, out, _ = _run(
            _doc(
                prose="**Two have since been fixed** — `APD-DATA-001`, `APD-DATA-008`.",
                section4=[
                    _row4("APD-DATA-001", "**FIXED (#1)** — done"),
                    _row4("APD-DATA-008", "still open — cache hit returns 201"),
                ],
                section51=[
                    _row51("APD-DATA-001"),
                    _row51("APD-DATA-008", "mentions **FIXED in passing"),
                ],
            )
        )
        self.assertEqual(rc, 1, out)
        self.assertIn("DISAGREE", out)
        self.assertIn("APD-DATA-008", out)
        self.assertIn("NOT **FIXED in §4", out)

    def test_eighty_still_matches_the_status_paragraph(self):
        """``**Seventy`` is the live wording; the durable clause is ``have since been fixed**."""
        rc, out, _ = _run(
            _doc(
                prose="**Eighty-one have since been fixed** — `APD-DATA-001`.",
                section4=[_row4("APD-DATA-001", "**FIXED (#1)** — done")],
                section51=[_row51("APD-DATA-001")],
            )
        )
        self.assertEqual(rc, 0, out)
        self.assertIn("AGREE", out)


if __name__ == "__main__":
    unittest.main()
