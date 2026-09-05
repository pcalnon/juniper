#!/usr/bin/env python3
"""Hermetic coverage for the canopy E2E matrix bulk-fill writer.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/e2e_matrix_fill.py`` is the bulk writer into the 298-row click-by-click
matrix. Distinct from ``2026-09-02_matrix_set_verdicts.py`` (single-row ``--from`` /
``--set``) and from ``e2e_matrix_rescore.py`` (named-row re-score). Documented incident:
splitting on every ``|`` wrote a PASS into C2.2-04's FA column because
``display:block\\|none`` created a phantom cell. Status must be located by header name
per table (C2.4 vs M-* have different column counts). A green bulk-fill that overwrites
a hand-authored cell, writes a ``pending`` bookkeeping token as a verdict, or lets an
older TSV beat a newer one, is worse than no tool.

``util/`` is outside every pre-commit Python hook's scope, so this unittest is the gate.
Stdlib-only; never opens the live matrix.
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
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "e2e_matrix_fill.py"

_spec = importlib.util.spec_from_file_location("e2e_matrix_fill", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(mod)

_M_HEADER = "| row id | control | interaction | expected | backend | verify | auto | mode | FA | status |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
_C24_HEADER = "| row id | # | Badge text | Trigger | Colour | mode | status |\n| --- | --- | --- | --- | --- | --- | --- |\n"


def _m_row(rid: str, *, expected: str = "ok", fa: str = "—", status: str = "—") -> str:
    return f"| {rid} | ctrl | click | {expected} | be | ver | AUTO | LIVE | {fa} | {status} |\n"


def _c24_row(rid: str, *, status: str = "—") -> str:
    return f"| {rid} | 1 | badge | click | green | LIVE | {status} |\n"


def _matrix(*sections: str) -> str:
    return "# fixture\n\n" + "".join(sections)


def _invoke(matrix: Path, verdicts: list[Path], *extra: str) -> tuple[int, str, str]:
    argv = ["e2e_matrix_fill.py", "--matrix", str(matrix)]
    for path in verdicts:
        argv.extend(["--verdicts", str(path)])
    argv.extend(extra)
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(sys, "argv", argv), redirect_stdout(out), redirect_stderr(err):
        rc = mod.main()
    return rc, out.getvalue(), err.getvalue()


class ExpandRowIdsTest(unittest.TestCase):
    """Compressed range / slash / lane-arm tokens must address the matrix ids they name."""

    def test_range_slash_and_lane_suffix(self) -> None:
        self.assertEqual(
            mod.expand_row_ids("M-TOPOLOGY-01..03"),
            ["M-TOPOLOGY-01", "M-TOPOLOGY-02", "M-TOPOLOGY-03"],
        )
        self.assertEqual(
            mod.expand_row_ids("M-PARAMETERS-01/02/03"),
            ["M-PARAMETERS-01", "M-PARAMETERS-02", "M-PARAMETERS-03"],
        )
        self.assertEqual(mod.expand_row_ids("M-DATASET-04-L"), ["M-DATASET-04"])
        self.assertEqual(mod.expand_row_ids("M-DATASET-04-D"), ["M-DATASET-04"])


class SplitRowTest(unittest.TestCase):
    def test_escaped_pipe_stays_inside_its_cell(self) -> None:
        """NEGATIVE CONTROL for the C2.2-04 incident.

        Splitting on every ``|`` turns ``display:block\\|none`` into a phantom cell, so a
        header-derived status index writes into FA and the status cell stays empty.
        Mutation-tested: ``re.split(r'\\|', line)`` fails this (extra cell, escaped content
        split). Reverted after.
        """
        line = "| C2.2-04 | ctrl | click | display:block\\|none | be | ver | AUTO | LIVE | — | — |"
        cells = mod.split_row(line)
        self.assertEqual(len(cells), len(mod.split_row(_m_row("C2.2-04").rstrip("\n"))))
        joined = "|".join(c.strip() for c in cells)
        self.assertIn("display:block\\|none", joined)
        self.assertNotIn("display:block\\", [c.strip() for c in cells])


class ShortenTest(unittest.TestCase):
    def test_keeps_a_finding_id_when_the_cell_fits(self) -> None:
        text = "PASS(request path) / FAIL(status message -- F-CANOPY-013)"
        self.assertEqual(mod.shorten(text, max_len=len(text)), text)

    def test_truncation_cuts_at_a_balanced_point_not_mid_parenthetical(self) -> None:
        text = "PASS(request path) / FAIL(status message -- F-CANOPY-013)"
        out = mod.shorten(text, max_len=40)
        self.assertLess(len(out), len(text))
        self.assertEqual(out.count("("), out.count(")"))
        self.assertFalse(out.rstrip("…").endswith("("))


class FillWriteTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.matrix = self.dir / "matrix.md"

    def _tsv(self, name: str, rows: dict[str, str]) -> Path:
        path = self.dir / name
        body = "row_id\tstatus\n" + "".join(f"{rid}\t{status}\n" for rid, status in rows.items())
        path.write_text(body, encoding="utf-8")
        return path

    def test_dry_run_writes_nothing(self) -> None:
        original = _matrix("### M\n\n" + _M_HEADER + _m_row("M-TOPOLOGY-01"))
        self.matrix.write_text(original, encoding="utf-8")
        rc, out, err = _invoke(self.matrix, [self._tsv("v.tsv", {"M-TOPOLOGY-01": "PASS"})])
        self.assertEqual(rc, 0, msg=err)
        self.assertIn("DRY RUN", out)
        self.assertEqual(self.matrix.read_text(encoding="utf-8"), original)

    def test_already_filled_without_overwrite_is_left_alone(self) -> None:
        original = _matrix("### M\n\n" + _M_HEADER + _m_row("M-TOPOLOGY-01", status="INCONCLUSIVE"))
        self.matrix.write_text(original, encoding="utf-8")
        rc, out, err = _invoke(self.matrix, [self._tsv("v.tsv", {"M-TOPOLOGY-01": "PASS"})], "--write")
        self.assertEqual(rc, 1, msg=err)
        self.assertIn("nothing to fill", out)
        self.assertEqual(self.matrix.read_text(encoding="utf-8"), original)
        self.assertIn("INCONCLUSIVE", self.matrix.read_text(encoding="utf-8"))

    def test_write_updates_only_the_named_row_not_a_prefix_neighbor(self) -> None:
        self.matrix.write_text(
            _matrix(
                "### M\n\n",
                _M_HEADER,
                _m_row("M-TOPOLOGY-01"),
                _m_row("M-TOPOLOGY-010"),
                _m_row("M-TOPOLOGY-10"),
            ),
            encoding="utf-8",
        )
        rc, _out, err = _invoke(self.matrix, [self._tsv("v.tsv", {"M-TOPOLOGY-01": "PASS"})], "--write")
        self.assertEqual(rc, 0, msg=err)
        text = self.matrix.read_text(encoding="utf-8")
        self.assertRegex(text, r"\| M-TOPOLOGY-01 \| .* \| PASS \|")
        self.assertRegex(text, r"\| M-TOPOLOGY-010 \| .* \| — \|")
        self.assertRegex(text, r"\| M-TOPOLOGY-10 \| .* \| — \|")

    def test_first_source_wins_so_an_older_fail_cannot_clobber_a_newer_pass(self) -> None:
        self.matrix.write_text(_matrix("### M\n\n" + _M_HEADER + _m_row("M-TOPOLOGY-01")), encoding="utf-8")
        newer = self._tsv("new.tsv", {"M-TOPOLOGY-01": "PASS"})
        older = self._tsv("old.tsv", {"M-TOPOLOGY-01": "FAIL"})
        rc, _out, err = _invoke(self.matrix, [newer, older], "--write")
        self.assertEqual(rc, 0, msg=err)
        text = self.matrix.read_text(encoding="utf-8")
        self.assertRegex(text, r"\| M-TOPOLOGY-01 \| .* \| PASS \|")
        self.assertNotRegex(text, r"\| M-TOPOLOGY-01 \| .* \| FAIL \|")

    def test_pending_prefix_is_not_a_verdict_and_writes_nothing(self) -> None:
        original = _matrix("### M\n\n" + _M_HEADER + _m_row("M-TOPOLOGY-01"))
        self.matrix.write_text(original, encoding="utf-8")
        rc, out, err = _invoke(
            self.matrix,
            [self._tsv("v.tsv", {"M-TOPOLOGY-01": "pending demo lane"})],
            "--write",
        )
        self.assertEqual(rc, 1, msg=err)
        self.assertIn("non-terminal", out)
        self.assertEqual(self.matrix.read_text(encoding="utf-8"), original)

    def test_escaped_pipe_fill_lands_in_status_not_fa(self) -> None:
        """Write-path form of the C2.2-04 incident: FA must stay ``—``, status becomes PASS."""
        self.matrix.write_text(
            _matrix("### M\n\n", _M_HEADER, _m_row("C2.2-04", expected="display:block\\|none")),
            encoding="utf-8",
        )
        rc, _out, err = _invoke(self.matrix, [self._tsv("v.tsv", {"C2.2-04": "PASS"})], "--write")
        self.assertEqual(rc, 0, msg=err)
        line = next(ln for ln in self.matrix.read_text(encoding="utf-8").splitlines() if "C2.2-04" in ln)
        self.assertIn("display:block\\|none", line)
        cells = [c.strip() for c in mod.split_row(line)]
        self.assertEqual(cells[4], "display:block\\|none")
        self.assertEqual(cells[9], "—")
        self.assertEqual(cells[10], "PASS")

    def test_status_is_located_by_header_name_on_a_shorter_c24_table(self) -> None:
        """A hardcoded M-* status index (10) would skip every C2.4 row."""
        self.matrix.write_text(_matrix("### C2.4\n\n" + _C24_HEADER + _c24_row("C2.4-01")), encoding="utf-8")
        rc, _out, err = _invoke(self.matrix, [self._tsv("v.tsv", {"C2.4-01": "PASS"})], "--write")
        self.assertEqual(rc, 0, msg=err)
        line = next(ln for ln in self.matrix.read_text(encoding="utf-8").splitlines() if "C2.4-01" in ln)
        cells = [c.strip() for c in mod.split_row(line)]
        self.assertEqual(cells[2], "1")
        self.assertEqual(cells[-2], "PASS")

    def test_lane_suffix_annotates_live_arm_rather_than_folding_bare_pass(self) -> None:
        self.matrix.write_text(_matrix("### M\n\n" + _M_HEADER + _m_row("M-DATASET-04")), encoding="utf-8")
        rc, _out, err = _invoke(self.matrix, [self._tsv("v.tsv", {"M-DATASET-04-L": "PASS"})], "--write")
        self.assertEqual(rc, 0, msg=err)
        text = self.matrix.read_text(encoding="utf-8")
        self.assertIn("PASS (LIVE arm)", text)
        self.assertNotRegex(text, r"\| M-DATASET-04 \| .* \| PASS \|")

    def test_bullet_continuation_is_not_unpacked(self) -> None:
        """A leading-token bullet must not guess at a bare ``-03 PASS`` continuation."""
        rowlog = self.dir / "rowlog.md"
        rowlog.write_text(
            "- M-PARAMETERS-01/02/03 PASS (tables render: ok)\n-03 FAIL should-not-count\n",
            encoding="utf-8",
        )
        self.matrix.write_text(
            _matrix(
                "### M\n\n",
                _M_HEADER,
                _m_row("M-PARAMETERS-01"),
                _m_row("M-PARAMETERS-02"),
                _m_row("M-PARAMETERS-03"),
            ),
            encoding="utf-8",
        )
        rc, _out, err = _invoke(self.matrix, [rowlog], "--write")
        self.assertEqual(rc, 0, msg=err)
        text = self.matrix.read_text(encoding="utf-8")
        self.assertRegex(text, r"\| M-PARAMETERS-01 \| .* \| PASS \|")
        self.assertRegex(text, r"\| M-PARAMETERS-02 \| .* \| PASS \|")
        self.assertRegex(text, r"\| M-PARAMETERS-03 \| .* \| PASS \|")
        self.assertNotIn("FAIL", text)


if __name__ == "__main__":
    unittest.main()
