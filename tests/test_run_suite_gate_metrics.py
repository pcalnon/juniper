#!/usr/bin/env python3
"""Complementary pins for ``run_suite._gate_metrics`` / REPORT work-invariant (P2 1.4).

``tests/test_run_suite.py`` (ml#1643) asserts that ``aggregate.csv`` *names*
``step_count`` and ``mean_step_seconds``, and that REPORT.md *contains the
strings* ``DE-RATIFIED`` / ``work invariant`` / ``single workload``. Those
headers and labels are hardcoded in ``aggregate()``. The stub driver writes
no ``metrics_series.csv``, so ``_gate_metrics`` returning ``{}`` still PASSes
that suite — the class of lie the comment at ``run_suite.py:492`` exists to
prevent (a swallowed ``ImportError`` shipped blank columns that looked
identical to an unmeasured suite).

This file is the leftover those tests cannot see: the VALUES, the HOLDS /
BROKEN / not-measured distinctions, and that the sibling import is not
wrapped. No live stack. ``util/`` is not pre-commit-lint-gated, so this
unittest is the gate.
"""

from __future__ import annotations

import ast
import csv
import importlib.util
import inspect
import io
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "experiments" / "run_suite.py"

spec = importlib.util.spec_from_file_location("run_suite_gate_metrics", MODULE_PATH)
run_suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_suite)

STEP_SUM = "juniper_cascor_training_step_duration_seconds_sum"
STEP_COUNT = "juniper_cascor_training_step_duration_seconds_count"
SERIES_HEADER = "ts_unix,fsm_status,current_epoch,current_hidden_units," f"{STEP_SUM},{STEP_COUNT}\n"

SAME_WORKLOAD = "experiment:\n  description: repeat\n  seed: 7\ntraining:\n  params:\n    max_epochs: 50\n"
OTHER_WORKLOAD = "experiment:\n  description: repeat\n  seed: 7\ntraining:\n  params:\n    max_epochs: 500\n"


def _write_run(root: Path, run_id: str, *, samples=((10.0, 100), (50.0, 1000)), with_series: bool = True, header_only: bool = False) -> Path:
    run_dir = root / run_id
    (run_dir / "artifacts" / "results").mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_id, "outcome": "succeeded"}), encoding="utf-8")
    if with_series:
        body = SERIES_HEADER
        if not header_only:
            for idx, (ssum, scount) in enumerate(samples):
                body += f"{1000.0 + idx},TRAINING,{idx},1,{ssum},{scount}\n"
        (run_dir / "artifacts" / "results" / "metrics_series.csv").write_text(body, encoding="utf-8")
    return run_dir


def _write_registry(suite_dir: Path, rows: list[dict]) -> None:
    suite_dir.mkdir(parents=True, exist_ok=True)
    (suite_dir / "registry.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _write_cell_yaml(suite_dir: Path, cell_id: str, body: str) -> None:
    cell_dir = suite_dir / "cells" / cell_id
    cell_dir.mkdir(parents=True, exist_ok=True)
    (cell_dir / "experiment.yaml").write_text(body, encoding="utf-8")


def _cells(*ids: str) -> list[dict]:
    return [{"cell_id": cell_id, "name": cell_id, "overrides": {}} for cell_id in ids]


def _aggregate(suite_dir: Path, cell_ids: tuple[str, ...], *, comparison: str | None = None) -> int:
    return run_suite.aggregate(suite_dir, {"name": "t-suite", "description": "gate-metrics"}, _cells(*cell_ids), comparison=comparison)


class GateMetricsReaderTest(unittest.TestCase):
    """``_gate_metrics`` must read the ratified inputs, not invent zeros."""

    def test_reads_the_last_histogram_row_not_wall_seconds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _write_run(root, "r1", samples=((5.0, 40), (30.0, 900), (50.0, 1000)))
            suite = root / "suite"
            _write_registry(suite, [{"cell_id": "c000", "run_dir": str(run), "wall_seconds": 999.0}])
            gate = run_suite._gate_metrics(suite, _cells("c000"))
            self.assertEqual(gate["c000"]["step_count"], 1000.0)
            self.assertAlmostEqual(gate["c000"]["mean_step_seconds"], 0.05)
            self.assertNotEqual(gate["c000"]["step_count"], 999.0, "wall_seconds must not leak into the work half")

    def test_missing_run_dir_omits_the_cell_instead_of_inventing_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            suite = Path(tmp) / "suite"
            _write_registry(suite, [{"cell_id": "c000", "run_id": "ghost"}])
            gate = run_suite._gate_metrics(suite, _cells("c000"))
            self.assertNotIn("c000", gate)
            self.assertEqual(gate, {})

    def test_absent_series_is_none_not_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _write_run(root, "r1", with_series=False)
            suite = root / "suite"
            _write_registry(suite, [{"cell_id": "c000", "run_dir": str(run)}])
            gate = run_suite._gate_metrics(suite, _cells("c000"))
            self.assertIsNone(gate["c000"]["step_count"])
            self.assertIsNone(gate["c000"]["mean_step_seconds"])

    def test_header_only_series_is_none_not_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _write_run(root, "r1", header_only=True)
            suite = root / "suite"
            _write_registry(suite, [{"cell_id": "c000", "run_dir": str(run)}])
            gate = run_suite._gate_metrics(suite, _cells("c000"))
            self.assertIsNone(gate["c000"]["step_count"])
            self.assertIsNone(gate["c000"]["mean_step_seconds"])


class AggregateValuesTest(unittest.TestCase):
    """CSV / REPORT must carry the measured numbers, not just the column names."""

    def test_csv_writes_the_measured_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _write_run(root, "r1", samples=((10.0, 100), (50.0, 1000)))
            suite = root / "suite"
            _write_registry(
                suite,
                [{"cell_id": "c000", "run_id": "r1", "outcome": "succeeded", "run_dir": str(run), "wall_seconds": 12.5, "exit_code": 0}],
            )
            self.assertEqual(_aggregate(suite, ("c000",)), 0)
            rows = list(csv.DictReader(io.StringIO((suite / "aggregate.csv").read_text(encoding="utf-8"))))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["step_count"], "1000.0")
            self.assertAlmostEqual(float(rows[0]["mean_step_seconds"]), 0.05)
            self.assertEqual(rows[0]["wall_seconds"], "12.5")

    def test_work_invariant_holds_when_counts_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _write_run(root, "ra", samples=((50.0, 1000),))
            b = _write_run(root, "rb", samples=((51.0, 1000),))
            suite = root / "suite"
            _write_registry(
                suite,
                [
                    {"cell_id": "c000", "run_dir": str(a), "outcome": "succeeded"},
                    {"cell_id": "c001", "run_dir": str(b), "outcome": "succeeded"},
                ],
            )
            _write_cell_yaml(suite, "c000", SAME_WORKLOAD)
            _write_cell_yaml(suite, "c001", SAME_WORKLOAD)
            _aggregate(suite, ("c000", "c001"))
            report = (suite / "REPORT.md").read_text(encoding="utf-8")
            self.assertIn("work invariant**: HOLDS", report)
            self.assertIn("step_count [1000]", report)
            self.assertIn("single workload**: yes", report)

    def test_work_invariant_broken_when_counts_differ(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _write_run(root, "ra", samples=((50.0, 1000),))
            b = _write_run(root, "rb", samples=((80.0, 2000),))
            suite = root / "suite"
            _write_registry(
                suite,
                [
                    {"cell_id": "c000", "run_dir": str(a), "outcome": "succeeded"},
                    {"cell_id": "c001", "run_dir": str(b), "outcome": "succeeded"},
                ],
            )
            _aggregate(suite, ("c000", "c001"))
            report = (suite / "REPORT.md").read_text(encoding="utf-8")
            self.assertIn("work invariant**: BROKEN", report)
            self.assertIn("step_count [1000, 2000]", report)
            self.assertIn("not repeats of each other", report)
            self.assertNotIn("work invariant**: HOLDS", report)

    def test_unmeasured_suite_says_not_measured_not_holds(self) -> None:
        """Empty gate → BROKEN / not measured. HOLDS would be a vacuous pass."""
        with tempfile.TemporaryDirectory() as tmp:
            suite = Path(tmp) / "suite"
            _write_registry(suite, [{"cell_id": "c000", "outcome": "succeeded"}])
            _aggregate(suite, ("c000",))
            report = (suite / "REPORT.md").read_text(encoding="utf-8")
            self.assertIn("work invariant**: BROKEN", report)
            self.assertIn("step_count not measured", report)
            self.assertNotIn("work invariant**: HOLDS", report)

    def test_single_workload_no_when_fingerprints_differ(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = _write_run(root, "ra", samples=((50.0, 1000),))
            b = _write_run(root, "rb", samples=((50.0, 1000),))
            suite = root / "suite"
            _write_registry(
                suite,
                [
                    {"cell_id": "c000", "run_dir": str(a), "outcome": "succeeded"},
                    {"cell_id": "c001", "run_dir": str(b), "outcome": "succeeded"},
                ],
            )
            _write_cell_yaml(suite, "c000", SAME_WORKLOAD)
            _write_cell_yaml(suite, "c001", OTHER_WORKLOAD)
            _aggregate(suite, ("c000", "c001"))
            report = (suite / "REPORT.md").read_text(encoding="utf-8")
            self.assertIn("single workload**: NO", report)
            self.assertNotIn("single workload**: yes", report)
            # Matching step_count with different fingerprints is the config-edit lie:
            # work HOLDS, identity does not. Both facts must stay visible.
            self.assertIn("work invariant**: HOLDS", report)

    def test_mean_step_is_reported_in_milliseconds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = _write_run(root, "r1", samples=((50.0, 1000),))
            suite = root / "suite"
            _write_registry(suite, [{"cell_id": "c000", "run_dir": str(run), "outcome": "succeeded", "wall_seconds": 12.5}])
            _aggregate(suite, ("c000",))
            report = (suite / "REPORT.md").read_text(encoding="utf-8")
            self.assertIn("| c000 | succeeded | 1000.0 | 50.000 |", report)


class StructuralGateTest(unittest.TestCase):
    """A revert that inlines the old blank-on-ImportError draft must fail here."""

    def test_aggregate_calls_gate_metrics(self) -> None:
        source = inspect.getsource(run_suite.aggregate)
        self.assertIn("_gate_metrics(", source)

    def test_gate_metrics_does_not_swallow_import_error(self) -> None:
        source = inspect.getsource(run_suite._gate_metrics)
        tree = ast.parse(source)
        swallowed: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            for handler in node.handlers:
                names: list[str] = []
                if handler.type is None:
                    names.append("bare")
                elif isinstance(handler.type, ast.Name):
                    names.append(handler.type.id)
                elif isinstance(handler.type, ast.Tuple):
                    names.extend(elt.id for elt in handler.type.elts if isinstance(elt, ast.Name))
                if "ImportError" in names or "bare" in names:
                    swallowed.append("ImportError" if "ImportError" in names else "bare except")
        self.assertEqual(swallowed, [], f"_gate_metrics swallows {swallowed}; blank columns look like an unmeasured suite")
        self.assertIn("from experiments import read_run_metrics", source)


if __name__ == "__main__":
    unittest.main()
