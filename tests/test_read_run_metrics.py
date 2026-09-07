#!/usr/bin/env python3
"""Hermetic tests for ``util/experiments/read_run_metrics.py`` (P2 item 0.4).

The module is the canonical reader for the perf lane's two gate inputs, so the properties
pinned here are the ones a wrong answer would silently corrupt:

* **The LAST sampled row wins.** ``step_count`` is gated at ZERO tolerance, so reading a
  mid-run sample instead of the terminal one would fail a correct run. The drive loop
  samples ``/metrics`` before it tests for termination, which is what makes the final row
  post-completion and the count exact.
* **The scrape tri-state is preserved.** ``None`` means "could not ask" (Prometheus
  unreachable), ``False`` means "asked, nothing there". Collapsing ``None`` into ``False``
  reinstates exactly the false negative ml#1550 removed -- and it was live on 2026-09-02,
  when a valid 5-repeat run reported ``None`` because Prometheus was down.
* **``work_invariant`` can FAIL.** A check that cannot fail is not a check, so a suite with
  differing ``step_count`` is asserted to report ``False`` (negative control).

``util/`` draws "(no files to check) Skipped" from every pre-commit Python hook, so this
unittest is the gate for this module.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import read_run_metrics as rrm  # noqa: E402  (path-invoked util import)

SERIES_HEADER = "ts_unix,fsm_status,current_epoch,current_hidden_units," "juniper_cascor_candidate_correlation,juniper_cascor_hidden_units_total," "juniper_cascor_training_loss,juniper_cascor_training_accuracy_ratio," f"{rrm.STEP_SUM_COLUMN},{rrm.STEP_COUNT_COLUMN}\n"


def _write_run(root: Path, run_id: str, *, drive=60.0, polls=13, samples=((10.0, 100), (63.4, 1770)), scrape=True, with_series=True, reason="early_stopped") -> Path:
    """Build a synthetic RUN_DIR. ``samples`` is an ordered list of (sum, count) poll rows."""
    run_dir = root / run_id
    (run_dir / "artifacts" / "results").mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "outcome": "succeeded",
        "timings": {"drive": drive, "total": drive + 3},
        "drive_loop": {"polls": polls},
        "metrics_scraped": {"grafana_bridge": True, "scrape_confirmed": scrape, "target_file_written": True},
        "completion_reason": reason,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    if with_series:
        rows = SERIES_HEADER
        for idx, (ssum, scount) in enumerate(samples):
            rows += f"{1000.0 + idx},TRAINING,{idx},1,0.1,1,0.5,0.9,{ssum},{scount}\n"
        (run_dir / "artifacts" / "results" / "metrics_series.csv").write_text(rows, encoding="utf-8")
    return run_dir


def _write_suite(root: Path, cells) -> Path:
    """``cells`` is a list of (cell_id, run_kwargs)."""
    suite_dir = root / "suite"
    suite_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for cell_id, kwargs in cells:
        run_dir = _write_run(root, f"run-{cell_id}", **kwargs)
        lines.append(json.dumps({"cell_id": cell_id, "run_dir": str(run_dir), "overrides": {}, "grafana_bridge": True}))
    (suite_dir / "registry.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return suite_dir


class StepTotalsTest(unittest.TestCase):
    def test_reads_the_last_sampled_row_not_the_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _write_run(Path(tmp), "r1", samples=((5.0, 40), (30.0, 900), (63.383, 1770)))
            self.assertEqual(rrm.step_totals(run), (63.383, 1770.0))

    def test_absent_series_is_none_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _write_run(Path(tmp), "r1", with_series=False)
            self.assertEqual(rrm.step_totals(run), (None, None))

    def test_header_only_series_is_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _write_run(Path(tmp), "r1", samples=())
            self.assertEqual(rrm.step_totals(run), (None, None))

    def test_missing_run_dir_is_none(self):
        self.assertEqual(rrm.step_totals(Path("/nonexistent/run")), (None, None))


class ReadRunTest(unittest.TestCase):
    def test_extracts_both_gate_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _write_run(Path(tmp), "r1", drive=65.234, polls=14, samples=((63.383, 1770),))
            row = rrm.read_run(run)
            self.assertEqual(row["drive_seconds"], 65.234)
            self.assertEqual(row["polls"], 14)
            self.assertEqual(row["step_count"], 1770.0)
            self.assertAlmostEqual(row["mean_step_seconds"], 63.383 / 1770)

    def test_scrape_tristate_none_is_preserved(self):
        # The live case on 2026-09-02: bridge armed, Prometheus down -> "could not ask".
        with tempfile.TemporaryDirectory() as tmp:
            run = _write_run(Path(tmp), "r1", scrape=None)
            self.assertIsNone(rrm.read_run(run)["scrape_confirmed"])

    def test_scrape_tristate_false_is_not_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _write_run(Path(tmp), "r1", scrape=False)
            self.assertIs(rrm.read_run(run)["scrape_confirmed"], False)

    def test_scrape_tristate_true_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _write_run(Path(tmp), "r1", scrape=True)
            self.assertIs(rrm.read_run(run)["scrape_confirmed"], True)

    def test_absent_manifest_yields_nones_not_an_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(Path(tmp) / "missing")
            self.assertIsNone(row["drive_seconds"])
            self.assertIsNone(row["step_count"])


class SummariseTest(unittest.TestCase):
    def test_work_invariant_holds_when_counts_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(
                Path(tmp),
                [("c000", {"samples": ((58.507, 1770),)}), ("c001", {"samples": ((66.016, 1770),)})],
            )
            summary = rrm.summarise(rrm.read_suite(suite))
            self.assertTrue(summary["work_invariant"])
            self.assertEqual(summary["step_counts"], [1770.0])

    def test_work_invariant_FAILS_when_counts_differ(self):
        # Negative control: the gate must bite. A suite of "repeats" whose work amount moved
        # is not a set of repeats, and this is the only signal that says so.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(
                Path(tmp),
                [("c000", {"samples": ((58.5, 1770),)}), ("c001", {"samples": ((66.0, 1771),)})],
            )
            summary = rrm.summarise(rrm.read_suite(suite))
            self.assertFalse(summary["work_invariant"])
            self.assertEqual(summary["step_counts"], [1770.0, 1771.0])

    def test_work_invariant_is_false_when_nothing_was_measured(self):
        # Vacuity guard: no counts at all must NOT read as "invariant holds".
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [("c000", {"with_series": False}), ("c001", {"with_series": False})])
            self.assertFalse(rrm.summarise(rrm.read_suite(suite))["work_invariant"])

    def test_spread_statistics(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(
                Path(tmp),
                [
                    ("c000", {"drive": 60.0, "samples": ((60.0, 100),)}),
                    ("c001", {"drive": 70.0, "samples": ((70.0, 100),)}),
                ],
            )
            summary = rrm.summarise(rrm.read_suite(suite))
            self.assertEqual(summary["drive"]["median"], 65.0)
            self.assertAlmostEqual(summary["drive"]["spread_pct"], 100 * 10 / 60)
            self.assertEqual(summary["cells"], 2)

    def test_work_invariant_is_false_when_one_cell_is_unmeasured(self):
        """The invariant must describe the SUITE, not the cells that answered.

        `counts` keeps only numeric step_counts, so before the `len(counts) == len(rows)`
        guard a two-cell suite with one unmeasured cell reported `step_counts=[1770.0]`
        and `work_invariant=True` -- an invariant over a subset of one.
        """
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(
                Path(tmp),
                [("c000", {"samples": ((63.0, 1770),)}), ("c001", {"with_series": False})],
            )
            summary = rrm.summarise(rrm.read_suite(suite))
            self.assertEqual(summary["cells"], 2)
            self.assertEqual(summary["step_counts"], [1770.0])
            self.assertFalse(summary["work_invariant"])

    def test_completion_reasons_KEEPS_the_unknown_member_rather_than_filtering_it(self):
        # The whole list, not just the derived boolean. ml#1776 removed the falsy filter
        # (`... for r in rows if r.get("completion_reason")`) because dropping unknown cells
        # BEFORE uniqueness made `4x early_stopped + 1x None` read as ONE branch -- fail-open
        # on exactly the mixed case the guard exists for.
        #
        # Nothing pinned the list itself, only `single_completion_reason`. A parked fleet PR
        # (ml#1735) still asserts the filtered form `["early_stopped"]`, so re-introducing the
        # filter would satisfy that test and break nothing else. This is what says no.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [("c000", {"reason": "early_stopped"}), ("c001", {"reason": None})])
            summary = rrm.summarise(rrm.read_suite(suite))
            self.assertEqual(summary["completion_reasons"], ["None", "early_stopped"])
            self.assertTrue(summary["has_unknown_completion_reason"])
            self.assertFalse(summary["single_completion_reason"])

    def test_single_workload_false_when_some_identities_unknown(self):
        """One known fingerprint plus one unknown is not "the same workload".

        `fingerprints` DROPS cells with no fingerprint, so `len(fingerprints) == 1` alone
        read True here -- the same fail-open the `reasons` comment in
        `read_run_metrics.py` warns about, left in place on the sibling field. Note the
        assertion keeps `len(fingerprints) == 1` true: the guard has to come from
        `identified == len(rows)`, not from the fingerprint set changing.
        """
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [("c000", {}), ("c001", {})])
            (suite / "cells" / "c000").mkdir(parents=True, exist_ok=True)
            (suite / "cells" / "c000" / "experiment.yaml").write_text("experiment:\n  seed: 42\n", encoding="utf-8")
            summary = rrm.summarise(rrm.read_suite(suite))
            self.assertEqual(len(summary["workload_fingerprints"]), 1)
            self.assertFalse(summary["single_workload"])


class ReadSuiteTest(unittest.TestCase):
    def test_preserves_registry_order_and_cell_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [("c000", {}), ("c001", {}), ("c002", {})])
            rows = rrm.read_suite(suite)
            self.assertEqual([r["cell_id"] for r in rows], ["c000", "c001", "c002"])

    def test_absent_registry_is_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(rrm.read_suite(Path(tmp)), [])

    def test_malformed_registry_line_is_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [("c000", {})])
            registry = suite / "registry.jsonl"
            registry.write_text(registry.read_text(encoding="utf-8") + "{not json\n", encoding="utf-8")
            self.assertEqual(len(rrm.read_suite(suite)), 1)


class WorkloadFingerprintTest(unittest.TestCase):
    """The identity check that P2 item 1.5's fail-on-mismatch rule depends on.

    A ``step_count`` mismatch only means "the code regressed" when both sides ran the SAME
    workload. Without this, an ordinary config edit would be reported as a regression -- and a
    gate that blames the wrong thing gets switched off.
    """

    def _cell(self, suite: Path, cell_id: str, body: str) -> None:
        (suite / "cells" / cell_id).mkdir(parents=True, exist_ok=True)
        (suite / "cells" / cell_id / "experiment.yaml").write_text(body, encoding="utf-8")

    def test_ignores_cosmetic_description_and_name(self):
        # PF-1's five repeats differ ONLY by these; registry config_sha256 differs across all five,
        # so it cannot serve as a workload identity.
        with tempfile.TemporaryDirectory() as tmp:
            suite = Path(tmp) / "s"
            self._cell(suite, "c000", "experiment:\n  description: repeat 1\n  name: a\n  seed: 42\ntraining:\n  params:\n    max_epochs: 4000\n")
            self._cell(suite, "c001", "experiment:\n  description: repeat 2\n  name: b\n  seed: 42\ntraining:\n  params:\n    max_epochs: 4000\n")
            self.assertEqual(rrm.workload_fingerprint(suite, "c000"), rrm.workload_fingerprint(suite, "c001"))

    def test_seed_is_NOT_cosmetic(self):
        # Two runs at different seeds are different workloads, not repeats.
        with tempfile.TemporaryDirectory() as tmp:
            suite = Path(tmp) / "s"
            self._cell(suite, "c000", "experiment:\n  description: x\n  seed: 42\n")
            self._cell(suite, "c001", "experiment:\n  description: x\n  seed: 43\n")
            self.assertNotEqual(rrm.workload_fingerprint(suite, "c000"), rrm.workload_fingerprint(suite, "c001"))

    def test_computation_relevant_change_moves_the_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = Path(tmp) / "s"
            self._cell(suite, "c000", "experiment:\n  seed: 42\ntraining:\n  params:\n    max_epochs: 4000\n")
            self._cell(suite, "c001", "experiment:\n  seed: 42\ntraining:\n  params:\n    max_epochs: 500\n")
            self.assertNotEqual(rrm.workload_fingerprint(suite, "c000"), rrm.workload_fingerprint(suite, "c001"))

    def test_missing_cell_yaml_is_none_not_a_shared_identity(self):
        # Unknown identity must NOT collapse into "same as everything else unknown" -- callers
        # treat None as a refusal, and two Nones comparing equal would be a vacuous pass.
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(rrm.workload_fingerprint(Path(tmp) / "s", "c000"))

    def test_single_workload_false_when_identities_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [("c000", {}), ("c001", {})])
            self.assertFalse(rrm.summarise(rrm.read_suite(suite))["single_workload"])

    def test_non_json_yaml_is_none_not_a_crash(self):
        # PyYAML loads an unquoted ISO date as datetime.date; json.dumps then TypeErrors.
        # Unknown identity must come back as None so callers can refuse, not abort the suite.
        with tempfile.TemporaryDirectory() as tmp:
            suite = Path(tmp) / "s"
            self._cell(suite, "c000", "experiment:\n  seed: 42\ndataset:\n  params:\n    start_date: 2015-01-01\n")
            self.assertIsNone(rrm.workload_fingerprint(suite, "c000"))

    def test_malformed_cell_yaml_is_none_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = Path(tmp) / "s"
            self._cell(suite, "c000", "experiment: [\nunterminated\n")
            self.assertIsNone(rrm.workload_fingerprint(suite, "c000"))

    def test_non_dict_cell_yaml_is_none(self):
        # A list (or scalar) is loadable YAML but is not a config; hashing it would invent an
        # identity for something that is not a workload.
        with tempfile.TemporaryDirectory() as tmp:
            suite = Path(tmp) / "s"
            self._cell(suite, "c000", "- not\n- a\n- mapping\n")
            self.assertIsNone(rrm.workload_fingerprint(suite, "c000"))


class CliTest(unittest.TestCase):
    def test_json_mode_emits_parseable_payload(self):
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [("c000", {}), ("c001", {})])
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = rrm.main([str(suite), "--json"])
            self.assertEqual(rc, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["suites"][0]["summary"]["cells"], 2)

    def test_no_arguments_is_an_error(self):
        import contextlib
        import io

        # argparse writes its usage to stderr before exiting; swallow it so a passing run
        # does not look like a failure in the CI log.
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            rrm.main([])


class RecurrenceKindTest(unittest.TestCase):
    """Recurrence has NO work counter, and the reader must say so rather than imply one.

    Surveyed across 36 real runs on 2026-09-04: ``n_epochs`` takes exactly two values -- 1
    (28 runs, "converged") and 200 (2 runs, "max_epochs") -- because it tracks the READOUT
    TYPE, and is invariant to ``d`` and ``n_steps``, the dimensions PF-5 and PF-6 exist to
    vary. ``n_windows`` does vary but is INPUT SIZE, fixed by config: a code change doing
    redundant work does not move it.

    So ``work_countable`` is a THIRD state, distinct from "counted and matched" and from
    "counted and differed". Collapsing it into either would let a recurrence suite be gated
    on something that cannot regress.
    """

    def _recurrence_run(self, root: Path, *, train=0.5, crossval=1.9, n_epochs=1, n_windows=1574) -> Path:
        run = root / "rec"
        (run / "artifacts" / "results").mkdir(parents=True, exist_ok=True)
        (run / "manifest.json").write_text(
            json.dumps({"run_id": "rec", "outcome": "succeeded", "timings": {"train": train, "crossval": crossval, "total": train + crossval}}),
            encoding="utf-8",
        )
        (run / "artifacts" / "results" / "train_response.json").write_text(json.dumps({"n_epochs": n_epochs, "stopped_reason": "converged", "dataset": {"n_windows": n_windows, "lookback": 32}}), encoding="utf-8")
        return run

    def test_recurrence_run_is_detected_by_its_timings(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(self._recurrence_run(Path(tmp)))
            self.assertEqual(row["kind"], "recurrence")
            self.assertEqual(row["train_seconds"], 0.5)
            self.assertEqual(row["n_windows"], 1574)

    def test_recurrence_work_is_NOT_countable(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(self._recurrence_run(Path(tmp)))
            self.assertFalse(row["work_countable"])
            self.assertIn("n_epochs", row["work_uncountable_reason"])

    def test_a_cascor_run_stays_countable(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = rrm.read_run(_write_run(Path(tmp), "c"))
            self.assertEqual(row["kind"], "cascor")
            self.assertTrue(row["work_countable"])

    def test_work_invariant_is_FALSE_when_work_is_not_countable(self):
        # The third state must not read as "counted, and they matched".
        rows = [{"work_countable": False, "kind": "recurrence"}, {"work_countable": False, "kind": "recurrence"}]
        summary = rrm.summarise(rows)
        self.assertFalse(summary["work_countable"])
        self.assertFalse(summary["work_invariant"])
        self.assertEqual(summary["kinds"], ["recurrence"])


if __name__ == "__main__":
    unittest.main()
