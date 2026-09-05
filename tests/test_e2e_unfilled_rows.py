#!/usr/bin/env python3
"""Hermetic tests for ``util/ad-hoc/e2e_unfilled_rows.py``.

Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

``util/`` is outside every pre-commit Python hook, so this suite is the gate.
The script is the AUTHORITATIVE ledger reader for "which canopy E2E matrix
rows still need a verdict?". ``e2e_row_coverage.py`` is an estimator that
over-credits compressed ranges and TSV ``pending ...`` records. Segment 15's
first handoff planned from the estimator and would have re-driven two
already-PASS rows while silently dropping three unfilled ones.

Hermetic: every case feeds a TemporaryDirectory matrix. The real click-by-click
matrix is never read. Distinct from the matrix writers (fill / rescore /
set_verdicts / append_statuses) and from finding-triage.
"""

from __future__ import annotations

import re
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "e2e_unfilled_rows.py"

_HEAD = re.compile(
    r"matrix rows   : (\d+)\n" r"verdicted     : (\d+)\n" r"UNFILLED      : (\d+)",
)


def _run(matrix: str, extra_files: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="e2e-unfilled-") as tmp:
        root = Path(tmp)
        path = root / "matrix.md"
        path.write_text(matrix, encoding="utf-8")
        for rel, content in (extra_files or {}).items():
            dest = root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
        return subprocess.run(  # nosec B603
            [sys.executable, str(SCRIPT), "--repo-root", str(root), "--matrix", str(path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )


def _counts(stdout: str) -> tuple[int, int, int]:
    match = _HEAD.search(stdout)
    assert match is not None, f"counts block missing from:\n{stdout}"
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _unfilled_ids(stdout: str) -> list[str]:
    """Row ids listed in the per-section table (not the header line)."""
    ids: list[str] = []
    for line in stdout.splitlines():
        if not line.startswith("| ") or line.startswith("| section"):
            continue
        if "unfilled" in line.lower() and "row ids" in line.lower():
            continue
        if set(line.replace("|", "").replace(":", "").replace("-", "").strip()) == set():
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        for token in re.split(r",\s*", cells[2]):
            token = token.strip()
            if token and (token.startswith("C2.") or token.startswith("M-")):
                ids.append(token)
    return ids


class PlaceholdersVersusVerdicts(unittest.TestCase):
    """Reuse fill's PLACEHOLDERS so the reader cannot drift from what fill will write."""

    MATRIX = """\
### 2.1 Header

| row id | control | status |
|--------|---------|--------|
| C2.1-01 | toggle | PASS |
| C2.1-02 | toggle | — |
| C2.1-03 | toggle | TBD |
| C2.1-04 | toggle | n/a |
| C2.1-05 | toggle | -- |
| C2.1-06 | toggle | - |
| C2.1-07 | toggle |  |
| C2.1-08 | toggle | FAIL |
| C2.1-09 | toggle | INCONCLUSIVE |
| C2.1-10 | toggle | DIVERGENCE D-1 CONFIRMED |
"""

    def test_placeholders_are_unfilled_and_real_verdicts_are_not(self) -> None:
        result = _run(self.MATRIX)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_counts(result.stdout), (10, 4, 6))
        self.assertEqual(
            _unfilled_ids(result.stdout),
            ["C2.1-02", "C2.1-03", "C2.1-04", "C2.1-05", "C2.1-06", "C2.1-07"],
        )
        for filled in ("C2.1-01", "C2.1-08", "C2.1-09", "C2.1-10"):
            self.assertNotIn(filled, _unfilled_ids(result.stdout))

    def test_pending_in_the_matrix_is_not_a_placeholder(self) -> None:
        """Pin fill's PLACEHOLDERS contract: ``pending`` is already-written.

        The estimator over-credits TSV ``pending ...`` records. This reader
        does not treat matrix-cell ``pending`` as unfilled — fill will not
        overwrite it without ``--overwrite``. A silent flip to "pending is
        empty" would make planning and filling disagree.
        """
        matrix = """\
### pending pin

| row id | status |
|--------|--------|
| C2.1-01 | pending |
| C2.1-02 | pending ... |
| C2.1-03 | PENDING |
| C2.1-04 | — |
"""
        result = _run(matrix)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_counts(result.stdout), (4, 3, 1))
        self.assertEqual(_unfilled_ids(result.stdout), ["C2.1-04"])


class ReadsTheMatrixAndNothingElse(unittest.TestCase):
    def test_tsv_pending_records_do_not_credit_a_placeholder_row(self) -> None:
        """Segment 15 incident: the estimator over-credits TSV pending; this must not."""
        matrix = """\
### 2.1 Header

| row id | status |
|--------|--------|
| C2.1-01 | PASS |
| C2.1-02 | — |
| C2.1-03 | — |
"""
        result = _run(
            matrix,
            extra_files={
                "reports/e2e/fake/statuses.tsv": ("row_id\tstatus\n" "C2.1-01\tPASS\n" "C2.1-02\tpending ...\n" "C2.1-03\tpending ...\n"),
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_counts(result.stdout), (3, 1, 2))
        self.assertEqual(_unfilled_ids(result.stdout), ["C2.1-02", "C2.1-03"])
        self.assertNotIn("C2.1-01", _unfilled_ids(result.stdout))


class StatusColumnAndEscapes(unittest.TestCase):
    def test_status_is_located_by_header_name_not_last_column(self) -> None:
        matrix = """\
### short table

| row id | status | notes |
|--------|--------|-------|
| C2.1-01 | — | leftover text that is not a placeholder |
| C2.1-02 | PASS | — |
"""
        result = _run(matrix)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_counts(result.stdout), (2, 1, 1))
        self.assertEqual(_unfilled_ids(result.stdout), ["C2.1-01"])

    def test_escaped_pipe_does_not_shift_the_status_cell(self) -> None:
        """C2.2-04 class: splitting on every ``|`` turns ``\\|`` into a phantom cell."""
        matrix = """\
### visibility

| row id | expected | status |
|--------|----------|--------|
| C2.2-04 | display:block\\|none | — |
| C2.2-05 | plain | PASS |
"""
        result = _run(matrix)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_counts(result.stdout), (2, 1, 1))
        self.assertEqual(_unfilled_ids(result.stdout), ["C2.2-04"])


class NamespaceAndIdentity(unittest.TestCase):
    def test_workload_rows_are_ignored(self) -> None:
        matrix = """\
### mixed

| row id | status |
|--------|--------|
| C2.1-01 | — |
| M-TOPOLOGY-01 | PASS |
| W1-01 | — |
| W14-11 | PASS |
"""
        result = _run(matrix)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_counts(result.stdout), (2, 1, 1))
        self.assertEqual(_unfilled_ids(result.stdout), ["C2.1-01"])
        self.assertNotIn("W1-01", result.stdout.split("row ids")[-1] if "row ids" in result.stdout else result.stdout)

    def test_prefix_near_miss_ids_are_distinct(self) -> None:
        matrix = """\
### topology

| row id | status |
|--------|--------|
| M-TOPOLOGY-01 | — |
| M-TOPOLOGY-010 | PASS |
| M-TOPOLOGY-011 | — |
"""
        result = _run(matrix)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_counts(result.stdout), (3, 1, 2))
        self.assertEqual(_unfilled_ids(result.stdout), ["M-TOPOLOGY-01", "M-TOPOLOGY-011"])
        self.assertNotIn("M-TOPOLOGY-010", _unfilled_ids(result.stdout))


class SectionGrouping(unittest.TestCase):
    def test_unfilled_ids_stay_under_their_own_heading(self) -> None:
        matrix = """\
### Alpha

| row id | notes | status |
|--------|-------|--------|
| C2.1-01 | hello | — |
| C2.1-02 | hello | PASS |

### Bravo

| row id | status | notes |
|--------|--------|-------|
| C2.1-03 | — | leftover that must not be read as status |
| C2.1-04 | FAIL | — |
"""
        result = _run(matrix)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(_counts(result.stdout), (4, 2, 2))
        self.assertIn("C2.1-01", result.stdout)
        self.assertIn("C2.1-03", result.stdout)
        alpha = [ln for ln in result.stdout.splitlines() if "Alpha" in ln]
        bravo = [ln for ln in result.stdout.splitlines() if "Bravo" in ln]
        self.assertEqual(len(alpha), 1, result.stdout)
        self.assertEqual(len(bravo), 1, result.stdout)
        self.assertIn("C2.1-01", alpha[0])
        self.assertNotIn("C2.1-03", alpha[0])
        self.assertIn("C2.1-03", bravo[0])
        self.assertNotIn("C2.1-01", bravo[0])
        self.assertRegex(result.stdout, r"sum of per-section unfilled counts: 2")


if __name__ == "__main__":
    unittest.main()
