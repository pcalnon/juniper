#!/usr/bin/env python3
"""Hermetic tests for ``util/ad-hoc/e2e_row_coverage.py``.

Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

``util/`` is outside every pre-commit Python hook, so this suite is the gate.
The script is the compressed-range ESTIMATOR for "which canopy E2E matrix rows
still need a verdict?". ``e2e_unfilled_rows.py`` is the AUTHORITATIVE
status-cell reader. Segment 15's first handoff planned from this estimator and
would have re-driven two already-PASS rows while silently dropping three
unfilled ones -- a census that certified a partial measurement as complete.

This suite does not replace that reader. It pins the estimator's own load-bearing
guards, because a regression here still reports remaining=0 while rows are
unfinished:

- compressed ranges expand inclusively (``01..06`` includes 01 and 06, not
  just the endpoints, and not 07/08 in a ``01..06,09`` spec);
- only the FIRST field of a TSV / rowlog line is a verdict subject -- prose
  mentions on the rest of the line must not credit a row;
- unmatched tokens go to ``unknown``, not into the remaining subtraction;
- TSV ``pending`` records ARE credited (characterization of the known
  limitation that makes unfilled_rows the authority).

Hermetic: every case feeds a TemporaryDirectory matrix. The real click-by-click
matrix is never read.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "e2e_row_coverage.py"
MATRIX_REL = Path("notes") / "JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md"


def _load():
    spec = importlib.util.spec_from_file_location("e2e_row_coverage", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load()


def _matrix(*row_ids: str) -> str:
    lines = [
        "### fixture",
        "",
        "| row id | status |",
        "|--------|--------|",
    ]
    lines.extend(f"| {rid} | — |" for rid in row_ids)
    return "\n".join(lines) + "\n"


def _cli(matrix: str, verdict_files: dict[str, str], extra: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="e2e-row-coverage-") as tmp:
        root = Path(tmp)
        path = root / MATRIX_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(matrix, encoding="utf-8")
        argv = [sys.executable, str(SCRIPT), "--repo-root", str(root), "--json"]
        for rel, content in verdict_files.items():
            dest = root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            argv.extend(["--verdict-file", str(dest)])
        if extra:
            argv.extend(extra)
        return subprocess.run(  # nosec B603
            argv,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )


class ExpandRanges(unittest.TestCase):
    def test_inclusive_bounds_and_the_gap_in_a_mixed_spec(self) -> None:
        """``01..06,09..11`` must include 01 and 06, and must not invent 07/08."""
        got = mod.expand("M-TOPOLOGY", "01..06,09..11", 2)
        self.assertIn("M-TOPOLOGY-01", got)
        self.assertIn("M-TOPOLOGY-06", got)
        self.assertIn("M-TOPOLOGY-03", got)
        self.assertIn("M-TOPOLOGY-09", got)
        self.assertIn("M-TOPOLOGY-11", got)
        self.assertNotIn("M-TOPOLOGY-07", got)
        self.assertNotIn("M-TOPOLOGY-08", got)
        self.assertEqual(len(got), 9)

    def test_width_zero_pads_a_bare_digit(self) -> None:
        self.assertEqual(mod.expand("C2.1", "1", 2), {"C2.1-01"})


class StripLane(unittest.TestCase):
    def test_live_and_demo_suffixes_fold_onto_the_matrix_row(self) -> None:
        self.assertEqual(mod.strip_lane("M-TOPOLOGY-05-L"), "M-TOPOLOGY-05")
        self.assertEqual(mod.strip_lane("C2.1-01-D"), "C2.1-01")

    def test_a_numeric_suffix_is_not_a_lane(self) -> None:
        """``-(?:L|D)$`` must not eat ``-01`` or a workload id would collapse."""
        self.assertEqual(mod.strip_lane("C2.1-01"), "C2.1-01")
        self.assertEqual(mod.strip_lane("W14-11"), "W14-11")


class FirstFieldOnly(unittest.TestCase):
    """The anti-vacuity guard: prose mentions must not shrink remaining."""

    KNOWN = {"C2.1-01", "C2.1-02", "M-TOPOLOGY-01"}

    def test_prose_on_the_rest_of_a_tsv_line_does_not_credit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="e2e-row-coverage-") as tmp:
            path = Path(tmp) / "statuses.tsv"
            path.write_text(
                "row_id\tstatus\n"
                "C2.1-01\tPASS see also C2.1-02 and M-TOPOLOGY-01\n",
                encoding="utf-8",
            )
            hit, unknown = mod.verdicted([path], self.KNOWN)
        self.assertEqual(hit, {"C2.1-01"})
        self.assertEqual(unknown, set())

    def test_markdown_rowlog_uses_the_first_cell_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="e2e-row-coverage-") as tmp:
            path = Path(tmp) / "rowlog.md"
            path.write_text(
                "| row_id | notes |\n"
                "| C2.1-01 | also C2.1-02 |\n",
                encoding="utf-8",
            )
            hit, unknown = mod.verdicted([path], self.KNOWN)
        self.assertEqual(hit, {"C2.1-01"})
        self.assertEqual(unknown, set())


class UnknownVersusHit(unittest.TestCase):
    def test_unmatched_tokens_do_not_enter_hit(self) -> None:
        """A token that is not a matrix row must not be able to shrink remaining."""
        with tempfile.TemporaryDirectory(prefix="e2e-row-coverage-") as tmp:
            path = Path(tmp) / "statuses.tsv"
            path.write_text("C2.9-99\tPASS\nC2.1-01\tPASS\n", encoding="utf-8")
            hit, unknown = mod.verdicted([path], {"C2.1-01", "C2.1-02"})
        self.assertEqual(hit, {"C2.1-01"})
        self.assertEqual(unknown, {"C2.9-99"})

    def test_headers_comments_and_missing_files_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory(prefix="e2e-row-coverage-") as tmp:
            path = Path(tmp) / "statuses.tsv"
            path.write_text("# leftover\nrow_id\tstatus\nC2.1-01\tPASS\n", encoding="utf-8")
            missing = Path(tmp) / "nope.tsv"
            hit, unknown = mod.verdicted([missing, path], {"C2.1-01"})
        self.assertEqual(hit, {"C2.1-01"})
        self.assertEqual(unknown, set())


class PendingOverCredit(unittest.TestCase):
    def test_tsv_pending_records_are_credited(self) -> None:
        """Characterization of the known estimator limitation.

        ``e2e_unfilled_rows.py`` does not treat TSV ``pending`` as a verdict.
        This estimator credits any first-field row id regardless of status --
        Segment 15 planned two already-PASS rows from that over-credit. Pin
        the current behaviour so a silent flip cannot be mistaken for the
        authoritative reader.
        """
        with tempfile.TemporaryDirectory(prefix="e2e-row-coverage-") as tmp:
            path = Path(tmp) / "statuses.tsv"
            path.write_text(
                "row_id\tstatus\n"
                "C2.1-01\tPASS\n"
                "C2.1-02\tpending ...\n",
                encoding="utf-8",
            )
            hit, unknown = mod.verdicted([path], {"C2.1-01", "C2.1-02", "C2.1-03"})
        self.assertEqual(hit, {"C2.1-01", "C2.1-02"})
        self.assertEqual(unknown, set())


class CompressedRangeCreditsInteriors(unittest.TestCase):
    def test_range_token_credits_every_in_range_known_row(self) -> None:
        with tempfile.TemporaryDirectory(prefix="e2e-row-coverage-") as tmp:
            path = Path(tmp) / "statuses.tsv"
            path.write_text("M-TOPOLOGY-01..06,09\tPASS\n", encoding="utf-8")
            known = {f"M-TOPOLOGY-{n:02d}" for n in range(1, 11)}
            hit, unknown = mod.verdicted([path], known)
        self.assertTrue({"M-TOPOLOGY-01", "M-TOPOLOGY-03", "M-TOPOLOGY-06", "M-TOPOLOGY-09"} <= hit)
        self.assertNotIn("M-TOPOLOGY-07", hit)
        self.assertNotIn("M-TOPOLOGY-08", hit)
        self.assertNotIn("M-TOPOLOGY-10", hit)
        self.assertEqual(unknown, set())


class CliJson(unittest.TestCase):
    def test_json_remaining_preserves_matrix_order_and_exits_0(self) -> None:
        matrix = _matrix("C2.1-01", "C2.1-02", "C2.1-03")
        result = _cli(
            matrix,
            {"reports/e2e/fake/statuses.tsv": "row_id\tstatus\nC2.1-01\tPASS\n"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["matrix_rows"], 3)
        self.assertEqual(payload["verdicted"], 1)
        self.assertEqual(payload["remaining"], 2)
        self.assertEqual(payload["remaining_rows"], ["C2.1-02", "C2.1-03"])


if __name__ == "__main__":
    unittest.main()
