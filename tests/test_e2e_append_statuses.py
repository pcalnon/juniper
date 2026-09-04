#!/usr/bin/env python3
"""Hermetic coverage for the canopy E2E TSV verdict appender.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/e2e_append_statuses.py`` is the dup-guarded writer into a Phase-1
run's ``statuses.tsv``. Distinct from ``e2e_matrix_fill.py`` (bulk matrix writer),
``e2e_matrix_rescore.py`` (named-row matrix re-score), and
``2026-09-02_matrix_set_verdicts.py`` (single-row matrix ``--from`` / ``--set``).
Those TSVs are what ``e2e_row_coverage.py`` and the matrix-fill pipeline trust, so
a green append that double-counts a lane, ``--replace``s a prefix neighbour, or
lets a tab/newline split one verdict across two TSV lines is worse than no tool.

``util/`` is outside every pre-commit Python hook's scope, so this unittest is the
gate. Stdlib-only; never opens a live run directory.
"""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "e2e_append_statuses.py"

_spec = importlib.util.spec_from_file_location("e2e_append_statuses", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(mod)

_HEADER = "row_id\tstatus\tnotes\tscreenshots"
_DASH = "—"


def _tsv(*rows: str) -> str:
    return _HEADER + "\n" + "\n".join(rows) + "\n"


def _row(rid: str, status: str = "PASS", notes: str = "ok", shots: str = _DASH) -> str:
    return f"{rid}\t{status}\t{notes}\t{shots}"


class CleanTest(unittest.TestCase):
    def test_tab_and_newline_collapse_to_one_field(self) -> None:
        """One input row must stay one TSV line even when notes carry a tab or newline."""
        self.assertEqual(mod.clean("a\tb\nc"), "a b c")
        self.assertEqual(mod.clean("  keep   spaces\ttrimmed  "), "keep spaces trimmed")


class AppendWriteTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.tsv = self.dir / "statuses.tsv"
        self.rows = self.dir / "rows.json"

    def _write_tsv(self, *rows: str) -> None:
        self.tsv.write_text(_tsv(*rows), encoding="utf-8")

    def _write_json(self, payload) -> None:
        self.rows.write_text(json.dumps(payload), encoding="utf-8")

    def _invoke(self, *extra: str) -> tuple[int, str, str]:
        argv = ["e2e_append_statuses.py", str(self.tsv), str(self.rows), *extra]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = mod.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_existing_row_is_skipped_without_replace(self) -> None:
        """A re-run must not double-count a lane. Neighbour stays put."""
        original = _tsv(_row("M-TOPOLOGY-01", "PASS", "first"), _row("M-TOPOLOGY-02", "FAIL", "other"))
        self.tsv.write_text(original, encoding="utf-8")
        self._write_json(
            [{"row_id": "M-TOPOLOGY-01", "status": "FAIL", "notes": "should-not-land"}]
        )
        rc, out, err = self._invoke()
        self.assertEqual(rc, 0, msg=err)
        self.assertIn("skipped 1", out)
        text = self.tsv.read_text(encoding="utf-8")
        self.assertEqual(text.count("M-TOPOLOGY-01"), 1)
        self.assertIn(_row("M-TOPOLOGY-01", "PASS", "first"), text)
        self.assertIn(_row("M-TOPOLOGY-02", "FAIL", "other"), text)
        self.assertNotIn("should-not-land", text)

    def test_replace_rewrites_in_place_keeping_position(self) -> None:
        """Later evidence revises a verdict without moving it to the end."""
        self._write_tsv(
            _row("M-TOPOLOGY-01", "FAIL", "old"),
            _row("M-TOPOLOGY-02", "PASS", "keep"),
            _row("M-TOPOLOGY-03", "PASS", "tail"),
        )
        self._write_json(
            [{"row_id": "M-TOPOLOGY-01", "status": "PASS", "notes": "revised", "screenshots": "shot.png"}]
        )
        rc, out, err = self._invoke("--replace")
        self.assertEqual(rc, 0, msg=err)
        self.assertIn("replaced 1", out)
        lines = self.tsv.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], _HEADER)
        self.assertEqual(lines[1], _row("M-TOPOLOGY-01", "PASS", "revised", "shot.png"))
        self.assertEqual(lines[2], _row("M-TOPOLOGY-02", "PASS", "keep"))
        self.assertEqual(lines[3], _row("M-TOPOLOGY-03", "PASS", "tail"))
        self.assertEqual(len(lines), 4)

    def test_replace_does_not_touch_a_prefix_neighbour(self) -> None:
        """NEGATIVE CONTROL. ``M-TOPOLOGY-01`` must not rewrite ``M-TOPOLOGY-010``.

        Mutation-tested: matching with ``line.startswith(row_id)`` or ``row_id in line``
        fails this. Reverted after.
        """
        self._write_tsv(
            _row("M-TOPOLOGY-010", "FAIL", "keep-fail"),
            _row("M-TOPOLOGY-01", "FAIL", "old"),
            _row("M-TOPOLOGY-10", "FAIL", "keep-10"),
        )
        self._write_json([{"row_id": "M-TOPOLOGY-01", "status": "PASS", "notes": "revised"}])
        rc, _out, err = self._invoke("--replace")
        self.assertEqual(rc, 0, msg=err)
        text = self.tsv.read_text(encoding="utf-8")
        self.assertIn(_row("M-TOPOLOGY-01", "PASS", "revised"), text)
        self.assertIn(_row("M-TOPOLOGY-010", "FAIL", "keep-fail"), text)
        self.assertIn(_row("M-TOPOLOGY-10", "FAIL", "keep-10"), text)
        self.assertEqual(text.count("PASS"), 1)

    def test_skip_does_not_block_a_prefix_neighbour_append(self) -> None:
        """Existing ``M-TOPOLOGY-01`` must not skip a new ``M-TOPOLOGY-010``."""
        self._write_tsv(_row("M-TOPOLOGY-01", "PASS", "first"))
        self._write_json([{"row_id": "M-TOPOLOGY-010", "status": "FAIL", "notes": "new"}])
        rc, out, err = self._invoke()
        self.assertEqual(rc, 0, msg=err)
        self.assertIn("appended 1", out)
        text = self.tsv.read_text(encoding="utf-8")
        self.assertIn(_row("M-TOPOLOGY-01", "PASS", "first"), text)
        self.assertIn(_row("M-TOPOLOGY-010", "FAIL", "new"), text)

    def test_tab_and_newline_in_notes_stay_one_tsv_line(self) -> None:
        self._write_tsv(_row("M-TOPOLOGY-02", "PASS", "keep"))
        self._write_json(
            [{"row_id": "M-TOPOLOGY-01", "status": "PASS", "notes": "line1\tline2\nline3"}]
        )
        rc, _out, err = self._invoke()
        self.assertEqual(rc, 0, msg=err)
        lines = [ln for ln in self.tsv.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertEqual(len(lines), 3)  # header + neighbour + new
        new = next(ln for ln in lines if ln.startswith("M-TOPOLOGY-01\t"))
        self.assertEqual(new.count("\t"), 3)
        self.assertIn("line1 line2 line3", new)
        self.assertNotIn("\tline2", new)

    def test_new_row_is_appended_header_preserved_screenshots_default(self) -> None:
        self._write_tsv(_row("M-TOPOLOGY-01", "PASS", "first"))
        self._write_json([{"row_id": "C2.4-01", "status": "PASS", "notes": "badge"}])
        rc, out, err = self._invoke()
        self.assertEqual(rc, 0, msg=err)
        self.assertIn("appended 1", out)
        lines = self.tsv.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], _HEADER)
        self.assertEqual(lines[1], _row("M-TOPOLOGY-01", "PASS", "first"))
        self.assertEqual(lines[2], _row("C2.4-01", "PASS", "badge", _DASH))

    def test_missing_tsv_is_rc_2_and_creates_nothing(self) -> None:
        missing = self.dir / "no-such.tsv"
        self._write_json([{"row_id": "M-TOPOLOGY-01", "status": "PASS"}])
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = mod.main(["e2e_append_statuses.py", str(missing), str(self.rows)])
        self.assertEqual(rc, 2)
        self.assertIn("no such TSV", err.getvalue())
        self.assertFalse(missing.exists())

    def test_non_array_json_is_rc_2_and_tsv_unchanged(self) -> None:
        original = _tsv(_row("M-TOPOLOGY-01", "PASS", "first"))
        self.tsv.write_text(original, encoding="utf-8")
        self._write_json({"row_id": "M-TOPOLOGY-02", "status": "FAIL"})
        rc, _out, err = self._invoke()
        self.assertEqual(rc, 2)
        self.assertIn("JSON array", err)
        self.assertEqual(self.tsv.read_text(encoding="utf-8"), original)

    def test_wrong_argc_is_rc_2(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = mod.main(["e2e_append_statuses.py", "only-one-arg"])
        self.assertEqual(rc, 2)
        self.assertIn("Append verdict rows", out.getvalue())


if __name__ == "__main__":
    unittest.main()
