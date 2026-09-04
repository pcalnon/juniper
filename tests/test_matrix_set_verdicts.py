#!/usr/bin/env python3
"""Hermetic coverage for the canopy E2E matrix status-cell writer.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/2026-09-02_matrix_set_verdicts.py`` is the only guarded write path
into the 298-row click-by-click matrix. Hand-editing is how a row silently
acquires a verdict nobody measured: neighbouring rows look identical at a
glance, and the status column is the last cell. The ``--from`` guard is
supposed to make a mis-aimed edit a loud failure. A green tool that overwrites
the wrong row, or writes a partial batch, is worse than no tool.

``util/`` is outside every pre-commit Python hook's scope, so this unittest is
the gate. Stdlib-only; never opens the live matrix.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-09-02_matrix_set_verdicts.py"

_spec = importlib.util.spec_from_file_location("matrix_set_verdicts", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(mod)


def _matrix(*body_rows: str) -> str:
    """A trailing-pipe table matching the live matrix's last-cell = status shape."""
    header = (
        "# fixture\n\n"
        "### Topology\n\n"
        "| id | description | vis | auto | grade | status |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
    )
    return header + "\n".join(body_rows) + "\n"


def _row(rid: str, desc: str, *, vis: str = "VIS", auto: str = "AUTO", grade: str = "B", status: str) -> str:
    return f"| {rid} | {desc} | {vis} | {auto} | {grade} | {status} |"


def _invoke(matrix: Path, from_status: str, *sets: str) -> tuple[int, str, str]:
    argv = [
        "matrix_set_verdicts.py",
        "--matrix",
        str(matrix),
        "--from",
        from_status,
    ]
    for item in sets:
        argv.extend(["--set", item])
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(sys, "argv", argv), redirect_stdout(out), redirect_stderr(err):
        rc = mod.main()
    return rc, out.getvalue(), err.getvalue()


class MatrixSetVerdictsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.matrix = Path(self._tmp.name) / "matrix.md"

    def _write(self, text: str) -> bytes:
        data = text.encode("utf-8")
        self.matrix.write_bytes(data)
        return data

    def test_from_mismatch_refuses_and_writes_nothing(self) -> None:
        """A PASS row must not be overwritten when the caller said it was BLOCKED."""
        original = self._write(
            _matrix(
                _row("M-TOPOLOGY-09", "node click", status="PASS"),
                _row("M-TOPOLOGY-10", "click empty", status="BLOCKED"),
            )
        )
        rc, _out, err = _invoke(self.matrix, "BLOCKED", "M-TOPOLOGY-09=FAIL")
        self.assertEqual(rc, 1, msg=err)
        self.assertIn("REFUSED", err)
        self.assertIn("M-TOPOLOGY-09", err)
        self.assertEqual(self.matrix.read_bytes(), original)

    def test_missing_row_exits_1_and_writes_nothing(self) -> None:
        original = self._write(_matrix(_row("M-TOPOLOGY-09", "node click", status="BLOCKED")))
        rc, _out, err = _invoke(self.matrix, "BLOCKED", "M-TOPOLOGY-99=PASS")
        self.assertEqual(rc, 1, msg=err)
        self.assertIn("MISSING", err)
        self.assertIn("M-TOPOLOGY-99", err)
        self.assertEqual(self.matrix.read_bytes(), original)

    def test_happy_path_updates_only_the_named_row(self) -> None:
        self._write(
            _matrix(
                _row("M-TOPOLOGY-09", "node click", status="BLOCKED"),
                _row("M-TOPOLOGY-10", "click empty", status="BLOCKED"),
            )
        )
        rc, out, err = _invoke(self.matrix, "BLOCKED", "M-TOPOLOGY-09=PASS")
        self.assertEqual(rc, 0, msg=err)
        self.assertIn("M-TOPOLOGY-09: BLOCKED -> PASS", out)
        text = self.matrix.read_text(encoding="utf-8")
        self.assertRegex(text, r"\| M-TOPOLOGY-09 \| .* \| PASS \|")
        self.assertRegex(text, r"\| M-TOPOLOGY-10 \| .* \| BLOCKED \|")
        # Earlier columns must survive: AUTO is not the status cell.
        self.assertIn("| AUTO |", text)

    def test_one_refuse_among_two_sets_writes_neither(self) -> None:
        """Partial apply would leave the matrix half-scored; refuse must be atomic."""
        original = self._write(
            _matrix(
                _row("M-TOPOLOGY-09", "node click", status="BLOCKED"),
                _row("M-TOPOLOGY-10", "click empty", status="PASS"),
            )
        )
        rc, _out, err = _invoke(
            self.matrix,
            "BLOCKED",
            "M-TOPOLOGY-09=PASS",
            "M-TOPOLOGY-10=FAIL",
        )
        self.assertEqual(rc, 1, msg=err)
        self.assertIn("REFUSED", err)
        self.assertIn("M-TOPOLOGY-10", err)
        self.assertEqual(self.matrix.read_bytes(), original)

    def test_exact_id_near_miss_does_not_update_a_prefix_neighbor(self) -> None:
        """Substring match would retarget M-TOPOLOGY-09 onto M-TOPOLOGY-090 / -10."""
        original = self._write(
            _matrix(
                _row("M-TOPOLOGY-090", "imposter", status="BLOCKED"),
                _row("M-TOPOLOGY-10", "click empty", status="BLOCKED"),
            )
        )
        rc, _out, err = _invoke(self.matrix, "BLOCKED", "M-TOPOLOGY-09=PASS")
        self.assertEqual(rc, 1, msg=err)
        self.assertIn("MISSING", err)
        self.assertIn("M-TOPOLOGY-09", err)
        self.assertEqual(self.matrix.read_bytes(), original)

        self._write(
            _matrix(
                _row("M-TOPOLOGY-09", "node click", status="BLOCKED"),
                _row("M-TOPOLOGY-090", "imposter", status="BLOCKED"),
                _row("M-TOPOLOGY-10", "click empty", status="BLOCKED"),
            )
        )
        rc, _out, err = _invoke(self.matrix, "BLOCKED", "M-TOPOLOGY-09=PASS")
        self.assertEqual(rc, 0, msg=err)
        text = self.matrix.read_text(encoding="utf-8")
        self.assertRegex(text, r"\| M-TOPOLOGY-09 \| .* \| PASS \|")
        self.assertRegex(text, r"\| M-TOPOLOGY-090 \| .* \| BLOCKED \|")
        self.assertRegex(text, r"\| M-TOPOLOGY-10 \| .* \| BLOCKED \|")

    def test_id_in_a_later_cell_is_not_the_row_identity(self) -> None:
        original = self._write(
            _matrix(_row("M-DATASET-14", "mentions M-TOPOLOGY-09 in the description", status="BLOCKED"))
        )
        rc, _out, err = _invoke(self.matrix, "BLOCKED", "M-TOPOLOGY-09=PASS")
        self.assertEqual(rc, 1, msg=err)
        self.assertIn("MISSING", err)
        self.assertEqual(self.matrix.read_bytes(), original)
        self.assertRegex(
            self.matrix.read_text(encoding="utf-8"),
            r"\| M-DATASET-14 \| .* \| BLOCKED \|",
        )

    def test_bad_set_syntax_exits_2_and_writes_nothing(self) -> None:
        original = self._write(_matrix(_row("M-TOPOLOGY-09", "node click", status="BLOCKED")))
        rc, _out, err = _invoke(self.matrix, "BLOCKED", "M-TOPOLOGY-09")
        self.assertEqual(rc, 2, msg=err)
        self.assertIn("bad --set", err)
        self.assertEqual(self.matrix.read_bytes(), original)

    def test_status_is_the_last_data_cell_not_an_earlier_AUTO_column(self) -> None:
        """--from AUTO must refuse when AUTO lives in a middle column and status is BLOCKED."""
        original = self._write(_matrix(_row("M-TOPOLOGY-09", "node click", auto="AUTO", status="BLOCKED")))
        rc, _out, err = _invoke(self.matrix, "AUTO", "M-TOPOLOGY-09=PASS")
        self.assertEqual(rc, 1, msg=err)
        self.assertIn("REFUSED", err)
        self.assertEqual(self.matrix.read_bytes(), original)

        rc, _out, err = _invoke(self.matrix, "BLOCKED", "M-TOPOLOGY-09=PASS")
        self.assertEqual(rc, 0, msg=err)
        text = self.matrix.read_text(encoding="utf-8")
        self.assertRegex(text, r"\| M-TOPOLOGY-09 \| .* \| AUTO \| B \| PASS \|")


if __name__ == "__main__":
    unittest.main()
