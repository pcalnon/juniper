#!/usr/bin/env python3
"""Complementary pins for REPORT.md's work-invariant third state (PR #1683 / P2 3.1).

``tests/test_read_run_metrics.py`` RecurrenceKindTest pins the reader row.
``tests/test_make_baseline.py`` RecurrenceRefusalTest pins ``build_baseline``.
``tests/test_work_countable_contract.py`` (#1689) pins ``compare()``.
``tests/test_recurrence_kind_edges.py`` (#1698) pins ``rrm.render()`` and
``_gate_metrics`` fields — it never calls ``aggregate()``.
``tests/test_run_suite_gate_metrics.py`` (#1685) pins cascor HOLDS / BROKEN /
not-measured. ``tests/test_run_suite.py`` (#1643) pins that the strings
``work invariant`` / ``DE-RATIFIED`` appear.

None of those suites can see that ``aggregate()`` keyed HOLDS off
``len(counts) == 1`` alone. A recurrence suite with planted matching
histogram counts, or a mixed cascor+recurrence suite whose only measured
count is the cascor cell, printed ``work invariant: HOLDS`` — the collapse
item 3.1 exists to close.

Do not touch the files listed above.
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "experiments" / "run_suite.py"

spec = importlib.util.spec_from_file_location("run_suite_uncountable_report", MODULE_PATH)
run_suite = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(run_suite)

STEP_SUM = "juniper_cascor_training_step_duration_seconds_sum"
STEP_COUNT = "juniper_cascor_training_step_duration_seconds_count"
SERIES_HEADER = (
    "ts_unix,fsm_status,current_epoch,current_hidden_units,"
    f"{STEP_SUM},{STEP_COUNT}\n"
)


def _write_run(
    root: Path,
    run_id: str,
    *,
    timings: dict,
    n_epochs: int | None = None,
    n_windows: int = 1574,
    samples: tuple[tuple[float, int], ...] | None = None,
) -> Path:
    run_dir = root / run_id
    results = run_dir / "artifacts" / "results"
    results.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(
        json.dumps({"run_id": run_id, "outcome": "succeeded", "timings": timings}),
        encoding="utf-8",
    )
    if n_epochs is not None:
        (results / "train_response.json").write_text(
            json.dumps({"n_epochs": n_epochs, "stopped_reason": "converged", "dataset": {"n_windows": n_windows}}),
            encoding="utf-8",
        )
    if samples:
        body = SERIES_HEADER
        for idx, (ssum, scount) in enumerate(samples):
            body += f"{1000.0 + idx},TRAINING,{idx},1,{ssum},{scount}\n"
        (results / "metrics_series.csv").write_text(body, encoding="utf-8")
    return run_dir


def _write_registry(suite_dir: Path, rows: list[dict]) -> None:
    suite_dir.mkdir(parents=True, exist_ok=True)
    (suite_dir / "registry.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _cells(*ids: str) -> list[dict]:
    return [{"cell_id": cell_id, "name": cell_id, "overrides": {}} for cell_id in ids]


def _aggregate(suite_dir: Path, cell_ids: tuple[str, ...]) -> str:
    run_suite.aggregate(suite_dir, {"name": "t-suite", "description": "uncountable-report"}, _cells(*cell_ids))
    return (suite_dir / "REPORT.md").read_text(encoding="utf-8")


def _assert_third_state(report: str) -> None:
    self_check = unittest.TestCase()
    self_check.assertIn("work invariant**: not countable", report)
    self_check.assertIn("n_epochs", report)
    self_check.assertNotIn("work invariant**: HOLDS", report)
    self_check.assertNotIn("work invariant**: BROKEN", report)
    self_check.assertNotIn("not repeats of each other", report)


class RecurrenceReportTest(unittest.TestCase):
    """REPORT.md must keep 'not countable' distinct from HOLDS / BROKEN."""

    def test_recurrence_suite_is_not_countable_not_unmeasured(self) -> None:
        # No histogram → counts is empty. The old line printed BROKEN / not
        # measured, which is the cascor-unmeasured token, not the third state.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _write_run(root, "r0", timings={"train": 0.5, "crossval": 1.9}, n_epochs=1)
            suite = root / "suite"
            _write_registry(suite, [{"cell_id": "c000", "run_dir": str(run), "outcome": "succeeded"}])
            _assert_third_state(_aggregate(suite, ("c000",)))

    def test_planted_matching_counts_do_not_print_holds(self) -> None:
        # RecurrenceKindTest / #1698 render rows either omit step_count or go
        # through rrm.render(). aggregate() keyed HOLDS off len(counts)==1, so
        # matching leftover cascor histogram rows were the path that LIED.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _write_run(root, "ra", timings={"train": 0.5, "crossval": 1.9}, n_epochs=1, samples=((50.0, 1770),))
            b = _write_run(root, "rb", timings={"train": 0.6, "crossval": 1.8}, n_epochs=1, samples=((51.0, 1770),))
            suite = root / "suite"
            _write_registry(
                suite,
                [
                    {"cell_id": "c000", "run_dir": str(a), "outcome": "succeeded"},
                    {"cell_id": "c001", "run_dir": str(b), "outcome": "succeeded"},
                ],
            )
            report = _aggregate(suite, ("c000", "c001"))
            _assert_third_state(report)
            gate = run_suite._gate_metrics(suite, _cells("c000", "c001"))
            self.assertEqual(gate["c000"]["step_count"], 1770.0)
            self.assertFalse(gate["c000"]["work_countable"])

    def test_planted_differing_counts_are_not_called_not_repeats(self) -> None:
        # "not repeats" is the cascor work-invariant failure. Printing it for
        # an uncountable suite is the misleading reason 3.1 replaced.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _write_run(root, "ra", timings={"train": 0.5, "crossval": 1.9}, n_epochs=1, samples=((50.0, 1000),))
            b = _write_run(root, "rb", timings={"train": 0.6, "crossval": 1.8}, n_epochs=200, samples=((80.0, 2000),))
            suite = root / "suite"
            _write_registry(
                suite,
                [
                    {"cell_id": "c000", "run_dir": str(a), "outcome": "succeeded"},
                    {"cell_id": "c001", "run_dir": str(b), "outcome": "succeeded"},
                ],
            )
            _assert_third_state(_aggregate(suite, ("c000", "c001")))

    def test_csv_does_not_write_n_epochs_as_step_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _write_run(root, "r0", timings={"train": 0.5, "crossval": 1.9}, n_epochs=1)
            suite = root / "suite"
            _write_registry(suite, [{"cell_id": "c000", "run_dir": str(run), "outcome": "succeeded", "run_id": "r0"}])
            _aggregate(suite, ("c000",))
            rows = list(csv.DictReader(io.StringIO((suite / "aggregate.csv").read_text(encoding="utf-8"))))
            self.assertEqual(rows[0]["step_count"], "")
            self.assertNotEqual(rows[0]["step_count"], "1")
            self.assertNotEqual(rows[0]["step_count"], "1.0")


class MixedSuiteReportTest(unittest.TestCase):
    """One countable cascor cell must not launder a mixed suite into HOLDS."""

    def test_mixed_cascor_plus_recurrence_is_not_countable(self) -> None:
        # counts = {1000} from the cascor cell alone → len==1 → the old line
        # printed HOLDS. That is the singleton-set hole the conjunct cannot
        # see from a pure-recurrence fixture.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cascor = _write_run(root, "cas", timings={"drive": 20.0}, samples=((50.0, 1000),))
            rec = _write_run(root, "rec", timings={"train": 0.5, "crossval": 1.9}, n_epochs=1)
            suite = root / "suite"
            _write_registry(
                suite,
                [
                    {"cell_id": "c000", "run_dir": str(cascor), "outcome": "succeeded"},
                    {"cell_id": "c001", "run_dir": str(rec), "outcome": "succeeded"},
                ],
            )
            report = _aggregate(suite, ("c000", "c001"))
            _assert_third_state(report)
            gate = run_suite._gate_metrics(suite, _cells("c000", "c001"))
            self.assertTrue(gate["c000"]["work_countable"])
            self.assertEqual(gate["c000"]["step_count"], 1000.0)
            self.assertFalse(gate["c001"]["work_countable"])
            self.assertIsNone(gate["c001"]["step_count"])


class CascorReportStillHoldsTest(unittest.TestCase):
    """The third state must not steal the cascor HOLDS / unmeasured tokens."""

    def test_matching_cascor_counts_still_hold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _write_run(root, "ra", timings={"drive": 20.0}, samples=((50.0, 1000),))
            b = _write_run(root, "rb", timings={"drive": 21.0}, samples=((51.0, 1000),))
            suite = root / "suite"
            _write_registry(
                suite,
                [
                    {"cell_id": "c000", "run_dir": str(a), "outcome": "succeeded"},
                    {"cell_id": "c001", "run_dir": str(b), "outcome": "succeeded"},
                ],
            )
            report = _aggregate(suite, ("c000", "c001"))
            self.assertIn("work invariant**: HOLDS", report)
            self.assertIn("step_count [1000]", report)
            self.assertNotIn("work invariant**: not countable", report)

    def test_empty_gate_stays_broken_not_measured(self) -> None:
        # `any(work_countable is False)` must not fire on an empty gate, or
        # the cascor-unmeasured token (#1685) becomes "not countable".
        with tempfile.TemporaryDirectory() as tmp:
            suite = Path(tmp) / "suite"
            _write_registry(suite, [{"cell_id": "c000", "outcome": "succeeded"}])
            report = _aggregate(suite, ("c000",))
            self.assertIn("work invariant**: BROKEN", report)
            self.assertIn("step_count not measured", report)
            self.assertNotIn("work invariant**: HOLDS", report)
            self.assertNotIn("work invariant**: not countable", report)


if __name__ == "__main__":
    unittest.main()
