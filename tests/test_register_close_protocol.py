#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Complementary leftover ``tests/test_register_open_set.py`` (#1648) and
``tests/test_register_status_crosscheck.py`` (#1717) cannot see.

#1648 pins the open-set token / suffix / ANY-row / dagger / prefix matrix on a
synthetic fragment. #1717 pins DISAGREE-on-a-missed-touch and then *explicitly
refuses* to pin live AGREE -- ``main()`` may exit 0 or 1. The close protocol
the trigger PR ran by hand is the pair: open-set counts AND the third reading
must AGREE. A close that misses a §2/§5.1 touch is green on #1717 and red here.

Also pins two edges neither suite constructs:

- the first matching §2 status line wins (a later ``have since been fixed**``
  decoy must not steal ids)
- a §5.1 first cell ``APD-CASCOR-003 (partial)`` still extracts the id

No production edits -- #1648 / #1717 own the extracts. This suite drives the
public CLI / ``main()`` / ``REGISTER`` path so it stays valid after those
extracts land. Hermetic fixtures are temp files; the live pin reads the
committed register only.
"""

from __future__ import annotations

import importlib.util
import io
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OPEN_SET = REPO_ROOT / "util" / "ad-hoc" / "register_open_set.py"
CROSSCHECK = REPO_ROOT / "util" / "ad-hoc" / "register_status_crosscheck.py"
REGISTER_NAME = "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
LIVE_REGISTER = REPO_ROOT / "notes" / REGISTER_NAME

_HEADLINE = re.compile(r"^(\d+) rows \| (\d+) fixed \| (\d+) open$", re.M)
_TABLE_FIXED = re.compile(r"§4 tables\s+:\s+(\d+) rows, (\d+) marked \*\*FIXED")


def _load_crosscheck():
    spec = importlib.util.spec_from_file_location("register_status_crosscheck", CROSSCHECK)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


crosscheck = _load_crosscheck()


def _run_open_set(cwd: Path) -> str:
    completed = subprocess.run(
        [sys.executable, str(OPEN_SET)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout


def _run_crosscheck_main() -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = crosscheck.main()
    return rc, out.getvalue(), err.getvalue()


def _write_register(root: Path, text: str) -> Path:
    notes = root / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    path = notes / REGISTER_NAME
    path.write_text(text, encoding="utf-8")
    return path


def _three_touch(
    *,
    table: list[str],
    status: str,
    verified: list[str],
    extra: str = "",
) -> str:
    return (
        "## 2. Summary\n"
        f"{status}\n\n"
        "## 4. Tables\n"
        + "\n".join(table)
        + "\n\n"
        "### 5.1 Fixed since this register was published\n"
        "| ID | Finding | Fixed by | Verification |\n"
        "| --- | --- | --- | --- |\n"
        + "\n".join(verified)
        + "\n\n"
        "### 5.2 Fixed before this register\n"
        f"{extra}\n"
    )


class LiveOperatorPairTest(unittest.TestCase):
    """#1717 allows main() to exit 1. The close protocol does not."""

    def test_committed_register_agrees(self):
        rc, out, err = _run_crosscheck_main()
        self.assertEqual(rc, 0, err + out)
        self.assertIn("AGREE", out)
        self.assertNotIn("DISAGREE", out)

    def test_open_set_fixed_count_matches_crosscheck_table_fixed(self):
        open_out = _run_open_set(REPO_ROOT)
        headline = _HEADLINE.search(open_out)
        self.assertIsNotNone(headline, open_out)
        rc, cross_out, err = _run_crosscheck_main()
        self.assertEqual(rc, 0, err + cross_out)
        table = _TABLE_FIXED.search(cross_out)
        self.assertIsNotNone(table, cross_out)
        self.assertEqual(headline.group(1), table.group(1), "seen/row count drifted between the two scripts")
        self.assertEqual(headline.group(2), table.group(2), "fixed count drifted between the two scripts")


class FirstStatusLineTest(unittest.TestCase):
    def test_later_decoy_status_line_does_not_steal_ids(self):
        text = _three_touch(
            table=["| APD-DATA-018 | **FIXED (data#354)** — bound the inputs | R |"],
            status="**Seventy-nine have since been fixed** — `APD-DATA-018`.",
            verified=["| APD-DATA-018 | both halves shipped | data#354 | verified |"],
            extra="**Eighty have since been fixed** — `APD-DATA-019`.\n",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_register(Path(tmp), text)
            original = crosscheck.REGISTER
            try:
                crosscheck.REGISTER = path
                rc, out, err = _run_crosscheck_main()
            finally:
                crosscheck.REGISTER = original
        self.assertEqual(rc, 0, err + out)
        self.assertIn("AGREE", out)
        self.assertNotIn("APD-DATA-019", out)


class PartialVerificationCellTest(unittest.TestCase):
    def test_section_five_partial_first_cell_still_extracts_the_id(self):
        text = _three_touch(
            table=["| APD-CASCOR-003 | **FIXED — partial (cascor#593)** — 44 of 46 | M |"],
            status="**Seventy have since been fixed** — `APD-CASCOR-003`.",
            verified=["| APD-CASCOR-003 (partial) | 44 of 46 done | cascor#593 | why partial |"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_register(Path(tmp), text)
            original = crosscheck.REGISTER
            try:
                crosscheck.REGISTER = path
                rc, out, err = _run_crosscheck_main()
            finally:
                crosscheck.REGISTER = original
        self.assertEqual(rc, 0, err + out)
        self.assertIn("1 verification rows", out)
        self.assertIn("AGREE", out)


if __name__ == "__main__":
    unittest.main()
