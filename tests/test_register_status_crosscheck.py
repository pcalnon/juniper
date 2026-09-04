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

``register_open_set.py`` and ``grep -cE '\\*\\*FIXED'`` both read the SAME §4
rows, so they can agree with each other and still both be wrong. This script
is the other measurement: §2 prose and §5.1 verification must name exactly the
ids whose §4 status cell is ``**FIXED``. A false AGREE is the vacuous-pass
class -- the close protocol missed a touch and every count-based check still
passes.

``util/`` is outside every pre-commit Python hook's scope, so this suite is
the gate. Hermetic: fixtures are strings; nothing reads the living register.
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


def _register(
    *,
    prose: str,
    table_rows: list[str],
    verified_rows: list[str],
    heading_51: str = "### 5.1 Fixed since this register was published",
    heading_52: str = "### 5.2 Fixed before this register was published",
) -> str:
    """A minimal three-section register. Each row is the full pipe line."""
    table = "\n".join(table_rows)
    verified = "\n".join(verified_rows)
    return (
        f"## 2. Status\n\n{prose}\n\n"
        f"## 4. Tables\n\n{table}\n\n"
        f"{heading_51}\n\n"
        f"| ID | Finding | Fixed by | Verification |\n"
        f"| --- | --- | --- | --- |\n"
        f"{verified}\n\n"
        f"{heading_52}\n"
    )


def _run(text: str) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = mod.crosscheck(text)
    return rc, out.getvalue(), err.getvalue()


_FIXED = "| APD-DATA-001   | **FIXED (#266)** — 401 path unthrottled | S | `api/security.py` | High |"
_OPEN = "| APD-DATA-018   | No async job pattern | R | `api/routes/datasets.py` | High |"
_FIXED_DAGGER = "| APD-DATA-034 † | **FIXED (#262)** — blanket ValueError | C | `api/app.py` | High |"
_FIXED_SPLIT = "| APD-CASCOR-001a | **FIXED (#540)** — comment omitted middleware | M | `api/app.py` | Low |"
_V_001 = "| APD-DATA-001 | 401 path unthrottled | data#266 | ported FailedAuthThrottle |"
_V_018 = "| APD-DATA-018 | No async job pattern | -- | still open |"
_V_034 = "| APD-DATA-034 † | blanket ValueError | data#262 | narrowed handler |"
_V_001A = "| APD-CASCOR-001a | comment omitted middleware | cascor#540 | folded into 001b |"


class AgreeWhenTheThreeSetsMatch(unittest.TestCase):
    def test_fixed_plus_open_agrees(self) -> None:
        text = _register(
            prose="**One have since been fixed** — `APD-DATA-001`.",
            table_rows=[_FIXED, _OPEN],
            verified_rows=[_V_001],
        )
        rc, out, _ = _run(text)
        self.assertEqual(rc, 0, out)
        self.assertIn("AGREE", out)
        self.assertNotIn("DISAGREE", out)

    def test_dagger_and_split_suffix_ids_still_parse(self) -> None:
        text = _register(
            prose="**Two have since been fixed** — `APD-DATA-034`, `APD-CASCOR-001a`.",
            table_rows=[_FIXED_DAGGER, _FIXED_SPLIT, _OPEN],
            verified_rows=[_V_034, _V_001A],
        )
        rc, out, _ = _run(text)
        self.assertEqual(rc, 0, out)
        self.assertIn("2 marked **FIXED", out)


class DisagreeWhenATouchIsMissing(unittest.TestCase):
    def test_table_fixed_missing_from_prose(self) -> None:
        text = _register(
            prose="**Zero have since been fixed**.",
            table_rows=[_FIXED, _OPEN],
            verified_rows=[_V_001],
        )
        rc, out, _ = _run(text)
        self.assertEqual(rc, 1, out)
        self.assertIn("DISAGREE", out)
        self.assertIn("FIXED in §4 but absent from §2 prose", out)
        self.assertIn("APD-DATA-001", out)

    def test_table_fixed_missing_from_verification(self) -> None:
        text = _register(
            prose="**One have since been fixed** — `APD-DATA-001`.",
            table_rows=[_FIXED, _OPEN],
            verified_rows=[],
        )
        rc, out, _ = _run(text)
        self.assertEqual(rc, 1, out)
        self.assertIn("FIXED in §4 but absent from §5.1 rows", out)
        self.assertIn("APD-DATA-001", out)

    def test_prose_lists_an_id_the_table_still_reads_open(self) -> None:
        text = _register(
            prose="**One have since been fixed** — `APD-DATA-018`.",
            table_rows=[_OPEN],
            verified_rows=[],
        )
        rc, out, _ = _run(text)
        self.assertEqual(rc, 1, out)
        self.assertIn("In §2 prose but NOT **FIXED in §4", out)
        self.assertIn("APD-DATA-018", out)

    def test_verification_row_without_a_table_close(self) -> None:
        text = _register(
            prose="**Zero have since been fixed**.",
            table_rows=[_OPEN],
            verified_rows=[_V_018],
        )
        rc, out, _ = _run(text)
        self.assertEqual(rc, 1, out)
        self.assertIn("In §5.1 rows but NOT **FIXED in §4", out)
        self.assertIn("APD-DATA-018", out)


class StatusCellIsTheOnlyCloseMarker(unittest.TestCase):
    def test_verification_mentioning_fixed_does_not_close_an_open_row(self) -> None:
        """The whole-line ``**FIXED`` search is the false-AGREE.

        A §5.1 verification cell that *discusses* ``**FIXED`` (\"Booked **FIXED
        for the ownership half\") used to mark the id table-fixed even when the
        §4 status cell was still open. The close protocol's fifth touch then
        had nothing left to catch.
        """
        poisoned = (
            "| APD-DATA-018 | No async job pattern | -- | "
            "Booked **FIXED for the ownership half only |"
        )
        text = _register(
            prose="**Zero have since been fixed**.",
            table_rows=[_OPEN],
            verified_rows=[poisoned],
        )
        rc, out, _ = _run(text)
        self.assertEqual(rc, 1, out)
        self.assertIn("In §5.1 rows but NOT **FIXED in §4", out)
        self.assertNotIn("FIXED in §4 but absent", out)

    def test_status_cell_fixed_is_still_a_close(self) -> None:
        text = _register(
            prose="**One have since been fixed** — `APD-DATA-001`.",
            table_rows=[_FIXED],
            verified_rows=[_V_001],
        )
        rc, out, _ = _run(text)
        self.assertEqual(rc, 0, out)


class StatusLineAndHeadings(unittest.TestCase):
    def test_have_since_been_fixed_matches_a_count_that_is_not_seventy(self) -> None:
        text = _register(
            prose="**Eighty-one have since been fixed** — `APD-DATA-001`.",
            table_rows=[_FIXED],
            verified_rows=[_V_001],
        )
        rc, out, _ = _run(text)
        self.assertEqual(rc, 0, out)
        self.assertIn("1 ids enumerated", out)

    def test_missing_headings_exit_one(self) -> None:
        text = _register(
            prose="**One have since been fixed** — `APD-DATA-001`.",
            table_rows=[_FIXED],
            verified_rows=[_V_001],
            heading_51="### no such heading",
        )
        rc, out, err = _run(text)
        self.assertEqual(rc, 1, out)
        self.assertIn("could not locate §5.1/§5.2 headings", err)

    def test_main_reads_the_living_register_and_exits_zero_or_one(self) -> None:
        """Dogfood: the shipped register must be parseable. Agreement is a
        property of the document, not of this suite -- either exit is fine
        as long as the machinery did not crash."""
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = mod.main()
        self.assertIn(rc, (0, 1), err.getvalue())
        text = out.getvalue()
        self.assertTrue(text.endswith("AGREE\n") or text.endswith("DISAGREE\n"), text)


class StatusCellHelper(unittest.TestCase):
    def test_second_cell_is_the_status(self) -> None:
        self.assertIn("**FIXED", mod._status_cell(_FIXED))
        self.assertNotIn("**FIXED", mod._status_cell(_OPEN))
        self.assertNotIn("**FIXED", mod._status_cell(_V_001))


if __name__ == "__main__":
    unittest.main()
