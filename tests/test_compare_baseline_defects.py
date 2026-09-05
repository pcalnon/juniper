#!/usr/bin/env python3
"""Complementary hermetic tests for ``util/experiments/compare_baseline.py`` defects A1–A7.

``tests/test_compare_baseline.py`` (#1622) pins the happy-path matrix: matching
``succeeded`` cells PASS, a one-step move FAILs at exit 1, identity/host mismatches
REFUSE at exit 2, and SPEED never fails the gate. Every fixture in that file is a
clean ``outcome=succeeded`` cell with a histogram. Those tests cannot see the six
ways Lane B1 found the comparator reaching a wrong verdict
(``HANDOFF_2026-09-04_perf-lane-gate-built-waves-not-closed.md``):

* **A1** -- ``summarise()`` drops ``None`` step_counts, so 4-of-5 unmeasured with
  one matching count is ``work_invariant`` and PASSes. ``make_baseline`` already
  refuses the missing cells.
* **A2** -- compare never reads ``outcome``. A ``timed_out`` rerun whose last
  histogram row happens to match PASSes. ``make_baseline`` already refuses
  non-``succeeded``.
* **A3** -- ``if reasons: REFUSED`` ran before the work-mismatch branch, so one
  unreadable suite on the CLI converted a true FAIL(1) into REFUSED(2).
* **A4** -- ``bool([0.0, 0.0, 0.0])`` is True, so a do-nothing run is invariant
  and PASSes.
* **A6** -- scenario coverage is unchecked; comparing one of two blessed
  workloads PASSes.
* **A7** -- duplicate fingerprints collapse in a dict comprehension and produce
  a false FAIL against the surviving sibling.

``util/`` is outside every pre-commit Python hook, so this unittest is the gate.
"""

from __future__ import annotations

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

SERIES_HEADER = "ts_unix,fsm_status,current_epoch,current_hidden_units," "juniper_cascor_candidate_correlation,juniper_cascor_hidden_units_total," "juniper_cascor_training_loss,juniper_cascor_training_accuracy_ratio," f"{rrm.STEP_SUM_COLUMN},{rrm.STEP_COUNT_COLUMN}\n"


def _write_run(root: Path, run_id: str, *, step_sum=63.0, step_count=1770, outcome="succeeded", with_series=True, completion_reason="below_threshold") -> Path:
    """A finished cell.

    ``completion_reason`` is not decoration. `main` gained a termination-branch
    precondition after this suite was written -- step_count is deterministic only
    WITHIN a branch, so cells that ended differently are not repeats and their
    agreement would be luck. A fixture that leaves it unset lands every cell on the
    ``None`` branch, and `build_baseline` refuses the whole suite before any of these
    tests reaches its own assertion.
    """
    run_dir = root / run_id
    (run_dir / "artifacts" / "results").mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "outcome": outcome,
                "completion_reason": completion_reason,
                "timings": {"drive": 65.0},
                "drive_loop": {"polls": 14},
                "environment": {"nproc": 16, "python": "3.13.13", "platform": "Linux-test", "thread_env": {"OMP_NUM_THREADS": None}},
                "metrics_scraped": {"scrape_confirmed": True},
            }
        ),
        encoding="utf-8",
    )
    if with_series:
        (run_dir / "artifacts" / "results" / "metrics_series.csv").write_text(
            SERIES_HEADER + f"1000.0,TRAINING,1,1,0.1,1,0.5,0.9,{step_sum},{step_count}\n",
            encoding="utf-8",
        )
    return run_dir


def _write_suite(root: Path, cells, name="suite", *, epochs=4000) -> Path:
    suite_dir = root / name
    (suite_dir / "cells").mkdir(parents=True, exist_ok=True)
    lines = []
    for idx, kwargs in enumerate(cells):
        cell_id = f"c{idx:03d}"
        run_dir = _write_run(root, f"{name}-run{idx}", **dict(kwargs))
        (suite_dir / "cells" / cell_id).mkdir(parents=True, exist_ok=True)
        (suite_dir / "cells" / cell_id / "experiment.yaml").write_text(
            f"experiment:\n  description: repeat {idx}\n  seed: 42\ntraining:\n  params:\n    max_epochs: {epochs}\n",
            encoding="utf-8",
        )
        lines.append(json.dumps({"cell_id": cell_id, "run_dir": str(run_dir), "overrides": {}, "config_sha256": f"sha-{cell_id}"}))
    (suite_dir / "registry.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return suite_dir


def _baseline(root: Path, tag: str, *suites: Path):
    payload = mb.build_baseline(tag, list(suites))
    manifests: list[dict] = []
    for suite in suites:
        manifests.extend(rrm._load_json(Path(r["run_dir"]) / "manifest.json") for r in rrm.read_suite(suite))
    return payload, mb.collect_host(manifests)


class HappyPathStillPasses(unittest.TestCase):
    def test_matching_succeeded_cells_still_pass(self):
        """The A1–A7 refusals must not fire on the fixture the #1622 suite already uses."""
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}, {}])
            payload, host = _baseline(Path(tmp), "t", suite)
            result = cb.compare(payload, host, [suite])
            self.assertEqual(result["verdict"], cb.PASS)
            self.assertEqual(cb.EXIT[result["verdict"]], 0)


class UnmeasuredMixedTest(unittest.TestCase):
    """A1. Existing tests never construct a mixed measured/unmeasured suite."""

    def test_four_of_five_unmeasured_is_REFUSED(self):
        # summarise() keeps only the one measured count, so work_invariant is True
        # and the pre-fix comparator PASSed. That is how missing data is laundered.
        with tempfile.TemporaryDirectory() as tmp:
            base = _write_suite(Path(tmp), [{}, {}, {}, {}, {}], name="base")
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _write_suite(
                Path(tmp),
                [{"with_series": False}, {"with_series": False}, {"with_series": False}, {"with_series": False}, {}],
                name="cand",
            )
            rows = rrm.read_suite(candidate)
            self.assertEqual(sum(1 for r in rows if r.get("step_count") is None), 4)
            # This asserted TRUE, with the message "the bug is that summarise calls this
            # invariant" -- it documented the defect as a precondition. ml#1776 fixed it:
            # `work_invariant` now requires a count for EVERY row, so four missing series
            # make it False at the summarise layer instead of being laundered into a
            # one-cell agreement. Assert the fix. The refusal below is unchanged and is
            # still what this test is for -- the comparator must refuse even if a future
            # summarise regressed.
            self.assertFalse(rrm.summarise(rows)["work_invariant"], "ml#1776: an unmeasured cell must break the invariant, not be dropped")
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(cb.EXIT[result["verdict"]], 2)
            self.assertIn("no step-duration data", " ".join(result["reasons"]))

    def test_all_unmeasured_uses_the_missing_data_reason(self):
        # All-None already failed work_invariant ("not a set of repeats"). The
        # missing-data reason must win so the operator is not told the cells
        # "disagreed" when they were never measured.
        with tempfile.TemporaryDirectory() as tmp:
            base = _write_suite(Path(tmp), [{}, {}], name="base")
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _write_suite(Path(tmp), [{"with_series": False}, {"with_series": False}], name="cand")
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            joined = " ".join(result["reasons"])
            self.assertIn("no step-duration data", joined)
            self.assertNotIn("not a set of repeats", joined)


class OutcomeTest(unittest.TestCase):
    """A2. Existing tests hard-code outcome=succeeded."""

    def test_every_cell_timed_out_is_REFUSED(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _write_suite(Path(tmp), [{}, {}], name="base")
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _write_suite(Path(tmp), [{"outcome": "timed_out"}, {"outcome": "timed_out"}], name="cand")
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(cb.EXIT[result["verdict"]], 2)
            self.assertIn("the driver stopped before the workload did", " ".join(result["reasons"]))
            self.assertIn("timed_out", " ".join(result["reasons"]))

    def test_one_failed_cell_among_succeeded_is_REFUSED(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _write_suite(Path(tmp), [{}, {}], name="base")
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _write_suite(Path(tmp), [{}, {"outcome": "failed"}], name="cand")
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("did not succeed", " ".join(result["reasons"]))


class VerdictPriorityTest(unittest.TestCase):
    """A3. Existing tests never pass a second, unreadable suite next to a real FAIL."""

    def test_unreadable_extra_suite_does_not_convert_FAIL_to_REFUSED(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = _write_suite(root, [{}, {}], name="base")
            payload, host = _baseline(root, "t", base)
            moved = _write_suite(root, [{"step_count": 1771}, {"step_count": 1771}], name="moved")
            empty = root / "empty"
            empty.mkdir()
            result = cb.compare(payload, host, [moved, empty])
            self.assertEqual(result["verdict"], cb.FAIL)
            self.assertEqual(cb.EXIT[result["verdict"]], 1)
            self.assertFalse(result["scenarios"][0]["work"]["match"])
            self.assertTrue(any("no registry" in r or "no cells" in r for r in result["reasons"]))

    def test_unreadable_alone_is_still_REFUSED(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = _write_suite(root, [{}, {}], name="base")
            payload, host = _baseline(root, "t", base)
            empty = root / "empty"
            empty.mkdir()
            result = cb.compare(payload, host, [empty])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(cb.EXIT[result["verdict"]], 2)

    def test_host_mismatch_still_REFUSES_even_with_a_work_mismatch(self):
        # A3 is "extra junk on the CLI must not hide a FAIL". A host mismatch is
        # not junk -- it is "these are not the same machine".
        with tempfile.TemporaryDirectory() as tmp:
            base = _write_suite(Path(tmp), [{}, {}], name="base")
            payload, host = _baseline(Path(tmp), "t", base)
            moved = _write_suite(Path(tmp), [{"step_count": 1771}, {"step_count": 1771}], name="moved")
            foreign = dict(host, cpu_model="Some Other CPU")
            result = cb.compare(payload, foreign, [moved])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("cpu_model", " ".join(result["reasons"]) + json.dumps(result["host"]))


class ZeroWorkTest(unittest.TestCase):
    """A4. Existing tests always write a non-zero histogram."""

    def test_all_zero_step_count_is_REFUSED(self):
        with tempfile.TemporaryDirectory() as tmp:
            # make_baseline still blesses zeros (bool([0.0]) is True). That is the
            # asymmetry this test pins on the COMPARE side.
            base = _write_suite(Path(tmp), [{"step_count": 0}, {"step_count": 0}], name="base")
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _write_suite(Path(tmp), [{"step_count": 0}, {"step_count": 0}], name="cand")
            self.assertTrue(rrm.summarise(rrm.read_suite(candidate))["work_invariant"])
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(cb.EXIT[result["verdict"]], 2)
            self.assertIn("nobody did any work", " ".join(result["reasons"]))


class CoverageTest(unittest.TestCase):
    """A6. Existing tests bless and compare a single suite."""

    def test_partial_scenario_coverage_is_REFUSED(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_a = _write_suite(root, [{}, {}], name="pf1", epochs=4000)
            suite_b = _write_suite(root, [{}, {}], name="pf2", epochs=500)
            payload, host = _baseline(root, "t", suite_a, suite_b)
            self.assertEqual(len(payload["scenarios"]), 2)
            result = cb.compare(payload, host, [suite_a])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(cb.EXIT[result["verdict"]], 2)
            self.assertIn("covered 1 of 2 baseline scenario", " ".join(result["reasons"]))
            self.assertIn("1 of 2", " ".join(result["reasons"]))

    def test_covering_both_scenarios_still_PASSes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_a = _write_suite(root, [{}, {}], name="pf1", epochs=4000)
            suite_b = _write_suite(root, [{}, {}], name="pf2", epochs=500)
            payload, host = _baseline(root, "t", suite_a, suite_b)
            result = cb.compare(payload, host, [suite_a, suite_b])
            self.assertEqual(result["verdict"], cb.PASS)


class DuplicateFingerprintTest(unittest.TestCase):
    """A7. Existing tests never hand-build a baseline with a colliding fingerprint."""

    def test_duplicate_baseline_fingerprints_REFUSE_not_false_FAIL(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}, {}], name="s")
            payload, host = _baseline(Path(tmp), "t", suite)
            colliding = json.loads(json.dumps(payload))
            sibling = dict(colliding["scenarios"][0])
            sibling["work"] = {"step_count": 9999, "invariant": True}
            colliding["scenarios"].append(sibling)
            # The collapsed dict keeps 9999. A candidate at 1770 would then FAIL
            # against a count that was never the first scenario's.
            result = cb.compare(colliding, host, [suite])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(cb.EXIT[result["verdict"]], 2)
            self.assertIn("DUPLICATE workload fingerprint", " ".join(result["reasons"]))
            self.assertEqual(result["scenarios"], [])


if __name__ == "__main__":
    unittest.main()
