#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Hermetic tests for ``util/ad-hoc/e2e_matrix_rescore.py`` -- the named-row
re-score writer for the canopy E2E click-by-click matrix.

Phase 2 uses this INSTEAD of ``e2e_matrix_fill.py --overwrite`` so hand-authored
cells on *other* rows (``INCONCLUSIVE``, ``DIVERGENCE D-1 CONFIRMED``) survive.
``util/`` is outside every pre-commit Python hook, so this suite is the gate.

What it pins, and why a green re-score that gets them wrong is worse than no tool:

- ``pending`` / ``pending ...`` is not a verdict (exit 2) and writes nothing even
  with ``--write``. A matrix reader would take ``pending`` as a recorded outcome.
- Default is a dry run. ``--write`` updates ONLY the named ``--row`` ids.
  A prefix near-miss (``M-TOPOLOGY-01`` vs ``M-TOPOLOGY-010``) and a neighbour
  stay put.
- A status that would change the row's cell count (a raw ``|``) is refused
  (exit 3). That is the C2.2-04 class: an extra cell shifts Status into FA.
- Escaped ``\\|`` in another cell stays inside that cell after a successful write.
- Status is located by header name per table, not a fixed index. A short table
  with Status in the middle must not overwrite Notes.
- Unlike fill, an already-filled status IS overwritten -- that is the re-score
  contract. Other columns on that row stay put.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "e2e_matrix_rescore.py"


def _load():
    spec = importlib.util.spec_from_file_location("e2e_matrix_rescore", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


rescore = _load()


MATRIX = """# fixture

## short table (status is not last)

| row id | status | notes |
| --- | --- | --- |
| C2.9-01 | FAIL | keep-this |
| C2.9-02 | BLOCKED | neighbour |

## long M-* table

| row id | control | interaction | expected | backend | verify | auto | mode | FA | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M-TOPOLOGY-01 | btn | click | drawn | y | z | yes | LIVE | display:block\\|none | INCONCLUSIVE |
| M-TOPOLOGY-02 | btn | click | drawn | y | z | yes | LIVE | — | FAIL |
| M-TOPOLOGY-010 | btn | click | drawn | y | z | yes | LIVE | — | BLOCKED |
"""


def _run(argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        with mock.patch.object(sys, "argv", ["e2e_matrix_rescore.py", *argv]):
            try:
                rc = rescore.main()
            except SystemExit as exc:
                rc = 0 if exc.code is None else int(exc.code)
    return rc, out.getvalue(), err.getvalue()


class E2EMatrixRescoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.matrix = Path(self.tmp.name) / "matrix.md"
        self.matrix.write_text(MATRIX, encoding="utf-8")

    def _argv(self, *extra: str) -> list[str]:
        return ["--matrix", str(self.matrix), *extra]

    def test_pending_is_refused_and_writes_nothing(self):
        before = self.matrix.read_bytes()
        rc, _out, err = _run(self._argv("--row", "C2.9-01", "--status", "pending demo lane", "--write"))
        self.assertEqual(rc, 2)
        self.assertIn("not a verdict", err)
        self.assertEqual(self.matrix.read_bytes(), before)

    def test_pending_prefix_is_case_insensitive(self):
        rc, _out, err = _run(self._argv("--row", "C2.9-01", "--status", "PENDING"))
        self.assertEqual(rc, 2)
        self.assertIn("not a verdict", err)

    def test_dry_run_writes_nothing(self):
        before = self.matrix.read_bytes()
        rc, out, _err = _run(self._argv("--row", "C2.9-01", "--status", "PASS"))
        self.assertEqual(rc, 0)
        self.assertIn("DRY RUN", out)
        self.assertEqual(self.matrix.read_bytes(), before)

    def test_write_overwrites_named_row_only(self):
        rc, _out, _err = _run(self._argv("--row", "C2.9-01", "--status", "PASS", "--write"))
        self.assertEqual(rc, 0)
        text = self.matrix.read_text(encoding="utf-8")
        self.assertIn("| C2.9-01 | PASS | keep-this |", text)
        self.assertIn("| C2.9-02 | BLOCKED | neighbour |", text)

    def test_status_located_by_header_not_last_column(self):
        """A last-column guess would write PASS into Notes on the short table."""
        rc, _out, _err = _run(self._argv("--row", "C2.9-01", "--status", "PASS", "--write"))
        self.assertEqual(rc, 0)
        row = [ln for ln in self.matrix.read_text(encoding="utf-8").splitlines() if "C2.9-01" in ln][0]
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual(cells[0], "C2.9-01")
        self.assertEqual(cells[1], "PASS")
        self.assertEqual(cells[2], "keep-this")

    def test_already_filled_status_is_overwritten(self):
        """Re-score, not fill: INCONCLUSIVE on the named row must yield to PASS."""
        rc, _out, _err = _run(self._argv("--row", "M-TOPOLOGY-01", "--status", "PASS", "--write"))
        self.assertEqual(rc, 0)
        text = self.matrix.read_text(encoding="utf-8")
        self.assertIn("INCONCLUSIVE", MATRIX)
        self.assertNotIn("INCONCLUSIVE", text)
        row = [ln for ln in text.splitlines() if ln.startswith("| M-TOPOLOGY-01 ")][0]
        self.assertIn("| PASS |", row)

    def test_prefix_near_miss_is_not_a_match(self):
        rc, _out, _err = _run(self._argv("--row", "M-TOPOLOGY-01", "--status", "PASS", "--write"))
        self.assertEqual(rc, 0)
        text = self.matrix.read_text(encoding="utf-8")
        self.assertIn("| M-TOPOLOGY-010 | btn | click | drawn | y | z | yes | LIVE | — | BLOCKED |", text)
        self.assertIn("| M-TOPOLOGY-02 | btn | click | drawn | y | z | yes | LIVE | — | FAIL |", text)

    def test_escaped_pipe_stays_in_its_cell(self):
        rc, _out, _err = _run(self._argv("--row", "M-TOPOLOGY-01", "--status", "PASS", "--write"))
        self.assertEqual(rc, 0)
        row = [ln for ln in self.matrix.read_text(encoding="utf-8").splitlines() if ln.startswith("| M-TOPOLOGY-01 ")][0]
        fill = rescore._load_filler()
        cells = [c.strip() for c in fill.split_row(row)]
        # split_row keeps the outer empties from the leading/trailing pipes.
        self.assertEqual(cells[1], "M-TOPOLOGY-01")
        self.assertEqual(cells[9], "display:block\\|none")
        self.assertEqual(cells[10], "PASS")
        naive = row.split("|")
        self.assertGreater(len(naive), len(fill.split_row(row)), "fixture lost the escaped-pipe incident class")

    def test_cell_count_change_is_refused_and_writes_nothing(self):
        before = self.matrix.read_bytes()
        rc, _out, err = _run(self._argv("--row", "C2.9-01", "--status", "PASS | extra", "--write"))
        self.assertEqual(rc, 3)
        self.assertIn("cell-count would change", err)
        self.assertEqual(self.matrix.read_bytes(), before)

    def test_missing_row_warns_but_updates_the_ones_found(self):
        rc, _out, err = _run(self._argv("--row", "C2.9-01", "--row", "M-NOPE-01", "--status", "PASS", "--write"))
        self.assertEqual(rc, 0)
        self.assertIn("not found", err)
        self.assertIn("M-NOPE-01", err)
        text = self.matrix.read_text(encoding="utf-8")
        self.assertIn("| C2.9-01 | PASS | keep-this |", text)
        self.assertIn("| C2.9-02 | BLOCKED | neighbour |", text)


if __name__ == "__main__":
    unittest.main()
