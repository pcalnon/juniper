#!/usr/bin/env python3
"""Complementary pins for the work_countable third state (PR #1683 / P2 item 3.1).

``tests/test_read_run_metrics.py`` RecurrenceKindTest already pins that a train-only
run is kind=recurrence and work_countable=False, and that a synthetic two-row
summarise without step_counts reports work_invariant False.
``tests/test_make_baseline.py`` RecurrenceRefusalTest already pins that
``build_baseline`` refuses such a suite.
``tests/test_compare_baseline.py`` never constructs a recurrence candidate.

This file covers the leftover those three cannot see:

* ``compare()`` refuses a recurrence candidate with exit 2 and the honest reason
  ("no countable work" / "Report the run"), not FAIL and not "not a set of repeats".
* A waiver cannot override that refusal (same contract as identity refusal).
* Matching planted cascor histogram counts do not make an uncountable suite
  work_invariant -- and a hand-built same-fingerprint baseline still cannot PASS.
* Detection: ``drive`` wins when both timing keys are present (misclassification
  would refuse a valid cascor gate). ``n_epochs=200`` is still uncountable.
  ``n_epochs`` / ``n_windows`` never become ``step_count``.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import compare_baseline as cb  # noqa: E402  (path-invoked util import)
from experiments import make_baseline as mb  # noqa: E402
from experiments import read_run_metrics as rrm  # noqa: E402

SERIES_HEADER = (
    "ts_unix,fsm_status,current_epoch,current_hidden_units,"
    "juniper_cascor_candidate_correlation,juniper_cascor_hidden_units_total,"
    "juniper_cascor_training_loss,juniper_cascor_training_accuracy_ratio,"
    f"{rrm.STEP_SUM_COLUMN},{rrm.STEP_COUNT_COLUMN}\n"
)

CASCOR_ENV = {"nproc": 16, "python": "3.13.13", "platform": "Linux-test", "thread_env": {"OMP_NUM_THREADS": None}}


def _cascor_suite(root: Path, name: str, *, step_count=1770, step_sum=63.0, cells=2) -> Path:
    suite_dir = root / name
    (suite_dir / "cells").mkdir(parents=True, exist_ok=True)
    lines = []
    for idx in range(cells):
        cell_id = f"c{idx:03d}"
        run_dir = root / f"{name}-run{idx}"
        (run_dir / "artifacts" / "results").mkdir(parents=True, exist_ok=True)
        (run_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "run_id": f"{name}-run{idx}",
                    "outcome": "succeeded",
                    "timings": {"drive": 65.0},
                    "drive_loop": {"polls": 14},
                    "environment": CASCOR_ENV,
                    "metrics_scraped": {"scrape_confirmed": True},
                }
            ),
            encoding="utf-8",
        )
        (run_dir / "artifacts" / "results" / "metrics_series.csv").write_text(SERIES_HEADER + f"1000.0,TRAINING,1,1,0.1,1,0.5,0.9,{step_sum},{step_count}\n", encoding="utf-8")
        (suite_dir / "cells" / cell_id).mkdir(parents=True, exist_ok=True)
        (suite_dir / "cells" / cell_id / "experiment.yaml").write_text(
            f"experiment:\n  description: repeat {idx}\n  seed: 42\ntraining:\n  params:\n    max_epochs: 4000\n",
            encoding="utf-8",
        )
        lines.append(json.dumps({"cell_id": cell_id, "run_dir": str(run_dir), "overrides": {}, "config_sha256": f"sha-{cell_id}"}))
    (suite_dir / "registry.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return suite_dir


def _recurrence_run(
    root: Path,
    run_id: str,
    *,
    train=0.5,
    crossval=1.9,
    n_epochs=1,
    n_windows=1574,
    timings=None,
    write_train_response=True,
    plant_step_count=None,
) -> Path:
    run = root / run_id
    (run / "artifacts" / "results").mkdir(parents=True, exist_ok=True)
    if timings is None:
        timings = {"train": train, "crossval": crossval, "total": train + crossval}
    (run / "manifest.json").write_text(
        json.dumps({"run_id": run_id, "outcome": "succeeded", "timings": timings, "environment": CASCOR_ENV}),
        encoding="utf-8",
    )
    if write_train_response:
        (run / "artifacts" / "results" / "train_response.json").write_text(
            json.dumps({"n_epochs": n_epochs, "stopped_reason": "converged" if n_epochs == 1 else "max_epochs", "dataset": {"n_windows": n_windows, "lookback": 32}}),
            encoding="utf-8",
        )
    if plant_step_count is not None:
        (run / "artifacts" / "results" / "metrics_series.csv").write_text(SERIES_HEADER + f"1000.0,TRAINING,1,1,0.1,1,0.5,0.9,63.0,{plant_step_count}\n", encoding="utf-8")
    return run


def _recurrence_suite(root: Path, name: str, *, cells=2, plant_step_count=None, n_epochs=1) -> Path:
    suite_dir = root / name
    (suite_dir / "cells").mkdir(parents=True, exist_ok=True)
    lines = []
    for idx in range(cells):
        cell_id = f"c{idx:03d}"
        run_dir = _recurrence_run(root, f"{name}-run{idx}", n_epochs=n_epochs, plant_step_count=plant_step_count)
        (suite_dir / "cells" / cell_id).mkdir(parents=True, exist_ok=True)
        (suite_dir / "cells" / cell_id / "experiment.yaml").write_text(
            f"experiment:\n  description: r{idx}\n  seed: 42\ntrain:\n  readout: linear\n",
            encoding="utf-8",
        )
        lines.append(json.dumps({"cell_id": cell_id, "run_dir": str(run_dir), "overrides": {}, "config_sha256": f"sha-{cell_id}"}))
    (suite_dir / "registry.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return suite_dir


def _cascor_baseline(root: Path, tag: str, suite: Path):
    payload = mb.build_baseline(tag, [suite])
    manifests = {r["run_id"]: rrm._load_json(Path(r["run_dir"]) / "manifest.json") for r in rrm.read_suite(suite)}
    return payload, mb.collect_host(list(manifests.values()))


class DetectionEdgeTest(unittest.TestCase):
    """Kind detection and the counters the reader must never invent."""

    def test_drive_wins_when_both_timing_keys_are_present(self):
        # A cascor run that also recorded train timings must stay countable. Flipping
        # the predicate to `if "train" in timings` would refuse a valid WORK gate.
        with tempfile.TemporaryDirectory() as tmp:
            run = _recurrence_run(Path(tmp), "both", timings={"drive": 65.0, "train": 0.5})
            (run / "artifacts" / "results" / "metrics_series.csv").write_text(SERIES_HEADER + "1000.0,TRAINING,1,1,0.1,1,0.5,0.9,63.0,1770\n", encoding="utf-8")
            row = rrm.read_run(run)
            self.assertEqual(row["kind"], "cascor")
            self.assertTrue(row["work_countable"])
            self.assertEqual(row["step_count"], 1770.0)

    def test_n_epochs_200_is_still_NOT_countable(self):
        # The survey's other value. RecurrenceKindTest only constructs n_epochs=1.
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(_recurrence_run(Path(tmp), "maxed", n_epochs=200))
            self.assertEqual(row["kind"], "recurrence")
            self.assertFalse(row["work_countable"])
            self.assertEqual(row["n_epochs"], 200)
            self.assertIn("1-or-200", row["work_uncountable_reason"])

    def test_n_epochs_and_n_windows_never_become_step_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(_recurrence_run(Path(tmp), "rec", n_epochs=200, n_windows=3149))
            self.assertIsNone(row["step_count"])
            self.assertEqual(row["n_epochs"], 200)
            self.assertEqual(row["n_windows"], 3149)

    def test_missing_train_response_is_still_uncountable(self):
        # Absence of the JSON must not invent a counter, and must not fall back to cascor.
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(_recurrence_run(Path(tmp), "bare", write_train_response=False))
            self.assertEqual(row["kind"], "recurrence")
            self.assertFalse(row["work_countable"])
            self.assertIsNone(row["n_epochs"])
            self.assertIsNone(row["n_windows"])


class SummariseThirdStateTest(unittest.TestCase):
    """work_invariant must not read 'uncountable' as 'counted, and they matched'."""

    def test_matching_planted_counts_do_not_make_uncountable_rows_invariant(self):
        # RecurrenceKindTest's summarise rows have no step_count, so dropping the
        # `countable and` conjunct would still report False (vacuous). Matching
        # planted counts are the case that conjunct exists to reject.
        rows = [
            {"work_countable": False, "kind": "recurrence", "step_count": 1770},
            {"work_countable": False, "kind": "recurrence", "step_count": 1770},
        ]
        summary = rrm.summarise(rows)
        self.assertFalse(summary["work_countable"])
        self.assertFalse(summary["work_invariant"])
        self.assertEqual(summary["step_counts"], [1770])

    def test_mixed_cascor_and_recurrence_suite_is_not_countable(self):
        rows = [
            {"work_countable": True, "kind": "cascor", "step_count": 1770},
            {"work_countable": False, "kind": "recurrence"},
        ]
        summary = rrm.summarise(rows)
        self.assertFalse(summary["work_countable"])
        self.assertFalse(summary["work_invariant"])
        self.assertEqual(summary["kinds"], ["cascor", "recurrence"])

    def test_empty_rows_are_not_countable(self):
        summary = rrm.summarise([])
        self.assertFalse(summary["work_countable"])
        self.assertFalse(summary["work_invariant"])
        self.assertEqual(summary["kinds"], [])


class CompareRefusalTest(unittest.TestCase):
    """The comparator is the operator-facing gate. The reason is the product."""

    def test_recurrence_candidate_is_REFUSED_not_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload, host = _cascor_baseline(root, "t", _cascor_suite(root, "base"))
            result = cb.compare(payload, host, [_recurrence_suite(root, "cand")])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(cb.EXIT[result["verdict"]], 2)
            joined = " ".join(result["reasons"])
            self.assertIn("no countable work", joined)
            self.assertIn("Report the run", joined)
            self.assertNotIn("not a set of repeats", joined)
            self.assertEqual(result["scenarios"], [])

    def test_waiver_cannot_override_the_uncountable_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload, host = _cascor_baseline(root, "t", _cascor_suite(root, "base"))
            result = cb.compare(payload, host, [_recurrence_suite(root, "cand")], accept_work_change="I really mean it")
            self.assertEqual(result["verdict"], cb.REFUSED)
            text = cb.render(result)
            self.assertIn("NO effect", text)
            self.assertNotIn("WAIVED by operator", text)

    def test_planted_matching_counts_against_a_same_fingerprint_baseline_still_refuse(self):
        # Double-bug path: drop compare's work_countable check AND the summarise
        # countable conjunct, and a planted histogram plus a hand-built matching
        # baseline would PASS. Either guard alone is not enough if the other
        # stays; both together are the contract.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = _recurrence_suite(root, "cand", plant_step_count=1770)
            rows = rrm.read_suite(candidate)
            summary = rrm.summarise(rows)
            self.assertFalse(summary["work_countable"])
            self.assertFalse(summary["work_invariant"])
            self.assertTrue(summary["single_workload"])
            fingerprint = summary["workload_fingerprints"][0]
            payload = {
                "tag": "forged",
                "scenarios": [
                    {
                        "suite": "forged",
                        "workload_fingerprint": fingerprint,
                        "work": {"step_count": 1770.0, "invariant": True},
                        "speed": {"mean": 0.03},
                    }
                ],
            }
            host = mb.collect_host([rrm._load_json(Path(r["run_dir"]) / "manifest.json") for r in rows])
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("no countable work", " ".join(result["reasons"]))
            self.assertEqual(result["scenarios"], [])


class CompareCliTest(unittest.TestCase):
    def test_recurrence_candidate_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = _cascor_suite(root, "base")
            payload, host = _cascor_baseline(root, "t", base)
            mb.write_baseline(root, "t", payload, {}, host)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                rc = cb.main(["--baseline", "t", "--suite", str(_recurrence_suite(root, "cand")), "--run-root", str(root)])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
