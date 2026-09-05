#!/usr/bin/env python3
"""Complementary pins for recurrence kind detection (PR #1683 / P2 item 3.1).

``tests/test_read_run_metrics.py`` RecurrenceKindTest already pins that a
train-only run is kind=recurrence and work_countable=False.
``tests/test_make_baseline.py`` RecurrenceRefusalTest already pins that
``build_baseline`` refuses such a suite.
``tests/test_work_countable_contract.py`` (#1689) already pins the
``compare()`` refusal, planted-count summarise, and ``drive``+``train`` both
valued staying cascor.

This file covers the leftover those suites cannot see:

* Recurrence ``train`` must not be aliased onto ``drive_seconds`` (the
  quantized cascor column). Aliasing would let a speed-only duration look
  like a gated cascor drive.
* Classification is key presence, not truthiness: ``drive: null`` keeps
  cascor; ``train: null`` with no drive key is still recurrence.
* ``render()`` of an uncountable suite must not print WORK INVARIANT HOLDS
  (including when matching step_counts are planted).
* CLI ``--run`` JSON emits kind / work_countable / train_seconds.
* Non-mapping ``timings`` / ``dataset`` must not crash ``read_run``.
* ``run_suite._gate_metrics`` carries ``work_countable=False`` and does not
  invent ``step_count`` from ``n_epochs``.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import read_run_metrics as rrm  # noqa: E402  (path-invoked util import)

SUITE_PATH = REPO_ROOT / "util" / "experiments" / "run_suite.py"
_spec = importlib.util.spec_from_file_location("run_suite_kind_edges", SUITE_PATH)
run_suite = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(run_suite)

SERIES_HEADER = (
    "ts_unix,fsm_status,current_epoch,current_hidden_units,"
    "juniper_cascor_candidate_correlation,juniper_cascor_hidden_units_total,"
    "juniper_cascor_training_loss,juniper_cascor_training_accuracy_ratio,"
    f"{rrm.STEP_SUM_COLUMN},{rrm.STEP_COUNT_COLUMN}\n"
)


def _recurrence_run(
    root: Path,
    run_id: str = "rec",
    *,
    train=0.5,
    crossval=1.9,
    n_epochs=1,
    n_windows=1574,
    timings=None,
    dataset=None,
    stopped_reason="converged",
    plant_step_count=None,
) -> Path:
    run = root / run_id
    (run / "artifacts" / "results").mkdir(parents=True, exist_ok=True)
    if timings is None:
        timings = {"train": train, "crossval": crossval, "total": train + crossval}
    (run / "manifest.json").write_text(
        json.dumps({"run_id": run_id, "outcome": "succeeded", "timings": timings}),
        encoding="utf-8",
    )
    body = {"n_epochs": n_epochs, "stopped_reason": stopped_reason}
    if dataset is not None:
        body["dataset"] = dataset
    else:
        body["dataset"] = {"n_windows": n_windows, "lookback": 32}
    (run / "artifacts" / "results" / "train_response.json").write_text(json.dumps(body), encoding="utf-8")
    if plant_step_count is not None:
        (run / "artifacts" / "results" / "metrics_series.csv").write_text(
            SERIES_HEADER + f"1000.0,TRAINING,1,1,0.1,1,0.5,0.9,63.0,{plant_step_count}\n",
            encoding="utf-8",
        )
    return run


def _recurrence_suite(root: Path, name: str = "rsuite", *, cells=2, plant_step_count=None) -> Path:
    suite_dir = root / name
    (suite_dir / "cells").mkdir(parents=True, exist_ok=True)
    lines = []
    for idx in range(cells):
        cell_id = f"c{idx:03d}"
        run_dir = _recurrence_run(root, f"{name}-run{idx}", plant_step_count=plant_step_count)
        (suite_dir / "cells" / cell_id).mkdir(parents=True, exist_ok=True)
        (suite_dir / "cells" / cell_id / "experiment.yaml").write_text(
            f"experiment:\n  description: r{idx}\n  seed: 42\ntrain:\n  readout: linear\n",
            encoding="utf-8",
        )
        lines.append(json.dumps({"cell_id": cell_id, "run_dir": str(run_dir), "overrides": {}, "config_sha256": f"sha-{cell_id}"}))
    (suite_dir / "registry.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return suite_dir


class TrainNotDriveTest(unittest.TestCase):
    """Recurrence duration must stay on the train column, never look like cascor drive."""

    def test_train_seconds_is_NOT_aliased_to_drive_seconds(self):
        # RecurrenceKindTest asserts train_seconds == 0.5 but never that drive_seconds
        # stayed None. Copying train onto drive would make a speed-only duration look
        # like the quantized cascor column the lane de-ratified.
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(_recurrence_run(Path(tmp)))
            self.assertEqual(row["kind"], "recurrence")
            self.assertEqual(row["train_seconds"], 0.5)
            self.assertIsNone(row["drive_seconds"])
            self.assertNotIn("drive", (rrm._load_json(Path(row["run_dir"]) / "manifest.json").get("timings") or {}))


class KeyPresenceTest(unittest.TestCase):
    """Kind detection is `\"drive\" not in timings`, not bool(timings[\"drive\"])."""

    def test_null_drive_key_keeps_cascor(self):
        # A cascor poll that wrote drive: null still has the key. Treating a
        # falsey value as "no drive" would mis-classify it as recurrence and
        # refuse a countable run.
        with tempfile.TemporaryDirectory() as tmp:
            run = _recurrence_run(Path(tmp), timings={"drive": None, "train": 0.5})
            (run / "artifacts" / "results" / "metrics_series.csv").write_text(
                SERIES_HEADER + "1000.0,TRAINING,1,1,0.1,1,0.5,0.9,63.0,1770\n",
                encoding="utf-8",
            )
            row = rrm.read_run(run)
            self.assertEqual(row["kind"], "cascor")
            self.assertTrue(row["work_countable"])
            self.assertEqual(row["step_count"], 1770.0)

    def test_null_train_without_drive_is_still_recurrence(self):
        # The converse: a recurrence manifest that recorded train: null is still
        # a recurrence run. Falling back to cascor would report work_countable
        # True with no counter -- the silent mis-gate 3.1 exists to prevent.
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(_recurrence_run(Path(tmp), timings={"train": None, "crossval": 1.9}))
            self.assertEqual(row["kind"], "recurrence")
            self.assertFalse(row["work_countable"])
            self.assertIsNone(row["train_seconds"])


class FieldSurfaceTest(unittest.TestCase):
    def test_stopped_reason_and_crossval_are_surfaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(_recurrence_run(Path(tmp), crossval=2.25, stopped_reason="max_epochs", n_epochs=200))
            self.assertEqual(row["crossval_seconds"], 2.25)
            self.assertEqual(row["stopped_reason"], "max_epochs")
            self.assertEqual(row["n_epochs"], 200)
            self.assertFalse(row["work_countable"])


class RenderThirdStateTest(unittest.TestCase):
    """The human table must not read 'not countable' as 'counted, and they matched'."""

    def test_render_does_not_claim_work_invariant_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _recurrence_suite(Path(tmp))
            rows = rrm.read_suite(suite)
            text = rrm.render(suite, rows, rrm.summarise(rows))
            self.assertNotIn("WORK INVARIANT HOLDS", text)

    def test_render_does_not_claim_holds_when_matching_counts_are_planted(self):
        # RecurrenceKindTest's summarise rows have no step_count, so a render
        # that keyed HOLDS off matching counts alone would still stay quiet.
        # Planted matching counts are the case that would print HOLDS.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _recurrence_suite(Path(tmp), plant_step_count=1770)
            rows = rrm.read_suite(suite)
            summary = rrm.summarise(rows)
            self.assertEqual(summary["step_counts"], [1770.0])
            self.assertFalse(summary["work_invariant"])
            text = rrm.render(suite, rows, summary)
            self.assertNotIn("WORK INVARIANT HOLDS", text)


class CliRunTest(unittest.TestCase):
    def test_cli_run_json_emits_kind_and_work_countable(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _recurrence_run(Path(tmp))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = rrm.main(["--run", str(run), "--json"])
            self.assertEqual(rc, 0)
            payload = json.loads(buf.getvalue())
            row = payload["runs"][0]
            self.assertEqual(row["kind"], "recurrence")
            self.assertFalse(row["work_countable"])
            self.assertEqual(row["train_seconds"], 0.5)
            self.assertEqual(row["n_windows"], 1574)
            self.assertIsNone(row["drive_seconds"])


class MalformedArtifactTest(unittest.TestCase):
    """A bad train_response / timings shape must not crash the reader."""

    def test_non_mapping_dataset_does_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(_recurrence_run(Path(tmp), dataset=["not", "a", "mapping"]))
            self.assertEqual(row["kind"], "recurrence")
            self.assertFalse(row["work_countable"])
            self.assertIsNone(row["n_windows"])

    def test_string_dataset_does_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(_recurrence_run(Path(tmp), dataset="windows=1574"))
            self.assertEqual(row["kind"], "recurrence")
            self.assertFalse(row["work_countable"])
            self.assertIsNone(row["n_windows"])

    def test_non_mapping_timings_does_not_crash(self):
        # A non-dict timings is not a recurrence signal. It must degrade to the
        # cascor default rather than TypeError on `"train" in timings`.
        with tempfile.TemporaryDirectory() as tmp:
            run = _recurrence_run(Path(tmp), timings="train")
            row = rrm.read_run(run)
            self.assertEqual(row["kind"], "cascor")
            self.assertTrue(row["work_countable"])
            self.assertIsNone(row["drive_seconds"])


class GateMetricsConsumerTest(unittest.TestCase):
    """The suite driver's per-cell gate dict is what REPORT.md / aggregate.csv read."""

    def test_gate_metrics_carries_work_countable_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _recurrence_suite(Path(tmp), cells=1)
            cells = [{"cell_id": "c000"}]
            gate = run_suite._gate_metrics(suite, cells)
            self.assertIn("c000", gate)
            self.assertEqual(gate["c000"]["kind"], "recurrence")
            self.assertFalse(gate["c000"]["work_countable"])

    def test_gate_metrics_does_not_invent_step_count_from_n_epochs(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _recurrence_suite(Path(tmp), cells=1)
            gate = run_suite._gate_metrics(suite, [{"cell_id": "c000"}])
            self.assertIsNone(gate["c000"]["step_count"])
            self.assertEqual(gate["c000"]["n_epochs"], 1)
            self.assertIsNone(gate["c000"]["drive_seconds"])
            self.assertEqual(gate["c000"]["train_seconds"], 0.5)


if __name__ == "__main__":
    unittest.main()
