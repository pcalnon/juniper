#!/usr/bin/env python3
"""Hermetic tests for ``util/experiments/make_baseline.py`` (P2 item 1.1, P1 design §4).

A baseline is the reference every later comparison is judged against, so the tests here are
mostly about what the tool must REFUSE. The design's own words: *"a run that promotes itself
to baseline can launder a bad number into the reference."*

Pinned refusals, each with a positive counterpart so the guard is not merely restrictive:

* **Overwriting a tag.** §4's retention rule is that baselines are never auto-deleted and a
  superseded tag is superseded BY NAME. There is deliberately no ``--force``, so the test
  asserts the absence of an escape hatch as well as the refusal.
* **A broken work invariant.** A suite whose ``step_count`` moved between cells is not a set
  of repeats, and a baseline cut from it fixes a work count that was never stable.
* **Unmeasured or failed runs**, and **runs carrying ``validation_warnings``** -- the last
  overridable, but the override is RECORDED in ``baseline.json`` rather than silent.

``HOST.json`` is load-bearing rather than metadata (the run tier's regression definition
requires "same hardware"), so its fidelity caveat is pinned too.

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

from experiments import make_baseline as mb  # noqa: E402  (path-invoked util import)
from experiments import read_run_metrics as rrm  # noqa: E402

SERIES_HEADER = "ts_unix,fsm_status,current_epoch,current_hidden_units," "juniper_cascor_candidate_correlation,juniper_cascor_hidden_units_total," "juniper_cascor_training_loss,juniper_cascor_training_accuracy_ratio," f"{rrm.STEP_SUM_COLUMN},{rrm.STEP_COUNT_COLUMN}\n"


def _write_run(root: Path, run_id: str, *, step_sum=63.0, step_count=1770, outcome="succeeded", warnings=None, python="3.13.13", with_series=True, reason="early_stopped") -> Path:
    run_dir = root / run_id
    (run_dir / "artifacts" / "results").mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "outcome": outcome,
        "timings": {"drive": 65.0},
        "drive_loop": {"polls": 14},
        "environment": {"nproc": 16, "python": python, "platform": "Linux-test", "thread_env": {"OMP_NUM_THREADS": None}},
        "metrics_scraped": {"scrape_confirmed": True},
        "completion_reason": reason,
    }
    if warnings:
        manifest["validation_warnings"] = warnings
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    if with_series:
        (run_dir / "artifacts" / "results" / "metrics_series.csv").write_text(SERIES_HEADER + f"1000.0,TRAINING,1,1,0.1,1,0.5,0.9,{step_sum},{step_count}\n", encoding="utf-8")
    return run_dir


def _write_suite(root: Path, cells, name="suite", workload="A") -> Path:
    """Synthetic suite. ``cells`` entries may carry ``workload`` to force a differing fingerprint.

    Each cell gets a materialised ``cells/<cell_id>/experiment.yaml`` because that is what
    ``workload_fingerprint`` reads -- and a baseline REFUSES a scenario whose workload identity is
    unknown, so a fixture without one would exercise the refusal rather than the happy path.
    """
    suite_dir = root / name
    (suite_dir / "cells").mkdir(parents=True, exist_ok=True)
    lines = []
    for idx, kwargs in enumerate(cells):
        kwargs = dict(kwargs)
        cell_workload = kwargs.pop("workload", workload)
        cell_id = f"c{idx:03d}"
        run_dir = _write_run(root, f"{name}-run{idx}", **kwargs)
        (suite_dir / "cells" / cell_id).mkdir(parents=True, exist_ok=True)
        # `experiment.description` differs per cell and is COSMETIC -- the fingerprint must ignore
        # it, exactly as PF-1's five repeats do in the field.
        (suite_dir / "cells" / cell_id / "experiment.yaml").write_text(
            f"experiment:\n  description: repeat {idx}\n  name: cell-{cell_id}\n  seed: 42\n" f"training:\n  params:\n    max_epochs: {4000 if cell_workload == 'A' else 500}\n",
            encoding="utf-8",
        )
        lines.append(json.dumps({"cell_id": cell_id, "run_dir": str(run_dir), "overrides": {"training.params.max_epochs": 4000}, "config_sha256": f"sha-{cell_id}"}))
    (suite_dir / "registry.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return suite_dir


class BuildRefusalTest(unittest.TestCase):
    def test_happy_path_builds(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}, {}, {}])
            payload = mb.build_baseline("t", [suite])
            self.assertEqual(payload["scenarios"][0]["work"]["step_count"], 1770.0)
            self.assertTrue(payload["scenarios"][0]["work"]["invariant"])

    def test_refuses_when_work_invariant_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{"step_count": 1770}, {"step_count": 1771}])
            with self.assertRaises(mb.BaselineError) as ctx:
                mb.build_baseline("t", [suite])
            self.assertIn("NOT invariant", str(ctx.exception))

    def test_refuses_failed_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}, {"outcome": "failed"}])
            with self.assertRaises(mb.BaselineError) as ctx:
                mb.build_baseline("t", [suite])
            self.assertIn("did not succeed", str(ctx.exception))

    def test_refuses_unmeasured_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}, {"with_series": False}])
            with self.assertRaises(mb.BaselineError) as ctx:
                mb.build_baseline("t", [suite])
            self.assertIn("cannot baseline an unmeasured run", str(ctx.exception))

    def test_refuses_cells_that_ran_different_workloads(self):
        # Distinct from the work invariant: a step_count spread across DIFFERENT configs is a fact
        # about the configs, not about the host or the code. A baseline scenario must be ONE
        # workload, or every later comparison against it is meaningless.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{"workload": "A"}, {"workload": "B"}])
            with self.assertRaises(mb.BaselineError) as ctx:
                mb.build_baseline("t", [suite])
            self.assertIn("different workloads", str(ctx.exception))

    def test_records_the_workload_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}, {}])
            payload = mb.build_baseline("t", [suite])
            self.assertIsNotNone(payload["scenarios"][0]["workload_fingerprint"])

    def test_fingerprint_ignores_cosmetic_description(self):
        # The five cells differ by `experiment.description` and nothing else that matters; if the
        # fingerprint saw that field, a suite could never be a set of repeats.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}, {}, {}])
            summary = rrm.summarise(rrm.read_suite(suite))
            self.assertTrue(summary["single_workload"])
            self.assertEqual(len(summary["workload_fingerprints"]), 1)
            self.assertEqual(len({r["config_sha256"] for r in rrm.read_suite(suite)}), 3, "fixture must vary config_sha256, as the real registry does")

    def test_refuses_empty_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty"
            empty.mkdir()
            with self.assertRaises(mb.BaselineError):
                mb.build_baseline("t", [empty])

    def test_refuses_mixed_known_and_missing_completion_reason(self):
        # Blessing this would record early_stopped from the one known cell and hide the null.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{"reason": "early_stopped"}, {"reason": None}])
            with self.assertRaises(mb.BaselineError) as ctx:
                mb.build_baseline("t", [suite])
            self.assertIn("single known branch", str(ctx.exception))

    def test_refuses_validation_warnings_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{"warnings": ["max_epochs without output_epochs"]}])
            with self.assertRaises(mb.BaselineError) as ctx:
                mb.build_baseline("t", [suite])
            self.assertIn("validation_warnings", str(ctx.exception))

    def test_accept_warnings_records_the_acceptance(self):
        # The escape exists, but it must leave a trace in the artifact -- a silently accepted
        # warning is indistinguishable from a clean run to whoever reads the baseline later.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{"warnings": ["max_epochs without output_epochs"]}])
            payload = mb.build_baseline("t", [suite], accept_warnings=True)
            self.assertTrue(payload["accepted_warnings"])
            self.assertTrue(payload["scenarios"][0]["validation_warnings"])


class WriteTest(unittest.TestCase):
    def _payload(self, tmp):
        suite = _write_suite(Path(tmp), [{}, {}])
        payload = mb.build_baseline("tag1", [suite])
        manifests = {r["run_id"]: json.loads((Path(r["run_dir"]) / "manifest.json").read_text()) for r in rrm.read_suite(suite)}
        return payload, manifests, mb.collect_host(list(manifests.values()))

    def test_writes_the_section_4_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload, manifests, host = self._payload(tmp)
            target = mb.write_baseline(Path(tmp) / "state", "tag1", payload, manifests, host)
            self.assertTrue((target / "baseline.json").is_file())
            self.assertTrue((target / "HOST.json").is_file())
            self.assertEqual(len(list((target / "manifests").glob("*.json"))), 2)
            self.assertEqual(target.parent.name, "baselines")

    def test_manifests_are_copied_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload, manifests, host = self._payload(tmp)
            target = mb.write_baseline(Path(tmp) / "state", "tag1", payload, manifests, host)
            run_id = next(iter(manifests))
            written = json.loads((target / "manifests" / f"{run_id}.json").read_text())
            self.assertEqual(written, manifests[run_id])

    def test_refuses_to_overwrite_an_existing_tag(self):
        # §4: baselines are never auto-deleted; a superseded tag is superseded BY NAME.
        with tempfile.TemporaryDirectory() as tmp:
            payload, manifests, host = self._payload(tmp)
            root = Path(tmp) / "state"
            mb.write_baseline(root, "tag1", payload, manifests, host)
            with self.assertRaises(mb.BaselineError) as ctx:
                mb.write_baseline(root, "tag1", payload, manifests, host)
            self.assertIn("superseded BY NAME", str(ctx.exception))

    def test_there_is_no_force_escape_hatch(self):
        """Pins the ABSENCE of an override: overwriting in place is the one operation the
        retention policy forbids, so it must not be reachable by flag.

        Asserted BEHAVIOURALLY, not by grepping the source. An earlier draft of this test did
        `assertNotIn("--force", inspect.getsource(mb))` and failed -- because the module
        docstring *explains* that there is deliberately no --force. Grepping a file that
        mentions a flag cannot distinguish prose from a live argument; only invoking the parser
        can.
        """
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}])
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
                mb.main(["--tag", "t", "--suite", str(suite), "--run-root", str(Path(tmp) / "state"), "--force"])
            self.assertEqual(ctx.exception.code, 2, "argparse must reject --force as an unknown argument")


class HostTest(unittest.TestCase):
    def test_records_the_required_section_4_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}])
            manifests = [json.loads((Path(r["run_dir"]) / "manifest.json").read_text()) for r in rrm.read_suite(suite)]
            host = mb.collect_host(manifests)
            for key in ("cpu_model", "cpu_count", "total_ram_kb", "gpu_present", "thread_budget", "versions"):
                self.assertIn(key, host)
            self.assertIn("torch", host["versions"])
            self.assertIn("numpy", host["versions"])

    def test_caveat_when_run_python_differs_from_tool(self):
        # torch/numpy are read from THIS interpreter; if the runs used another, say so rather
        # than record a plausible-but-wrong version.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{"python": "3.9.0-not-this-one"}])
            manifests = [json.loads((Path(r["run_dir"]) / "manifest.json").read_text()) for r in rrm.read_suite(suite)]
            host = mb.collect_host(manifests)
            self.assertIn("caveat", host["versions"])

    def test_no_caveat_when_pythons_match(self):
        import platform

        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{"python": platform.python_version()}])
            manifests = [json.loads((Path(r["run_dir"]) / "manifest.json").read_text()) for r in rrm.read_suite(suite)]
            self.assertNotIn("caveat", mb.collect_host(manifests)["versions"])

    def test_flags_mixed_cpu_counts(self):
        host = mb.collect_host(
            [
                {"environment": {"nproc": 16, "python": "3.13.13"}},
                {"environment": {"nproc": 8, "python": "3.13.13"}},
            ]
        )
        self.assertIn("caveat_cpu_count", host)


class CliTest(unittest.TestCase):
    def test_dry_run_writes_nothing(self):
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}])
            root = Path(tmp) / "state"
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                rc = mb.main(["--tag", "t", "--suite", str(suite), "--run-root", str(root), "--dry-run"])
            self.assertEqual(rc, 0)
            self.assertFalse((root / "baselines").exists())

    def test_rejects_a_tag_with_a_path_separator(self):
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}])
            with contextlib.redirect_stderr(io.StringIO()):
                rc = mb.main(["--tag", "../escape", "--suite", str(suite), "--run-root", str(Path(tmp) / "state")])
            self.assertEqual(rc, 2)

    def test_refusal_exits_2(self):
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{"step_count": 1}, {"step_count": 2}])
            with contextlib.redirect_stderr(io.StringIO()):
                rc = mb.main(["--tag", "t", "--suite", str(suite), "--run-root", str(Path(tmp) / "state")])
            self.assertEqual(rc, 2)

    def test_end_to_end_write(self):
        import contextlib
        import io

        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), [{}, {}])
            root = Path(tmp) / "state"
            with contextlib.redirect_stdout(io.StringIO()):
                rc = mb.main(["--tag", "pf1-test", "--suite", str(suite), "--run-root", str(root)])
            self.assertEqual(rc, 0)
            payload = json.loads((root / "baselines" / "pf1-test" / "baseline.json").read_text())
            self.assertEqual(payload["tag"], "pf1-test")
            self.assertEqual(payload["metric_contract"]["work"].split(" --")[0], "step_count")


if __name__ == "__main__":
    unittest.main()


class RecurrenceRefusalTest(unittest.TestCase):
    """A baseline supports the WORK gate, so a run with no work counter cannot back one.

    Recurrence exposes none (see the reader's RecurrenceKindTest). A "speed-only baseline"
    would exist solely to support the comparison this host's 13-20.5% drift floor rules out --
    i.e. it would be an invitation to draw exactly the conclusion the lane rejected. Refusing
    is the honest outcome; the runs are still worth REPORTING.
    """

    def _recurrence_suite(self, root: Path) -> Path:
        suite_dir = root / "rsuite"
        (suite_dir / "cells").mkdir(parents=True, exist_ok=True)
        lines = []
        for idx in range(2):
            cell_id = f"c{idx:03d}"
            run_dir = root / f"rrun{idx}"
            (run_dir / "artifacts" / "results").mkdir(parents=True, exist_ok=True)
            (run_dir / "manifest.json").write_text(
                json.dumps({"run_id": f"rrun{idx}", "outcome": "succeeded", "timings": {"train": 0.5, "crossval": 1.9}, "environment": {"nproc": 16, "python": "3.13.13"}}),
                encoding="utf-8",
            )
            (run_dir / "artifacts" / "results" / "train_response.json").write_text(json.dumps({"n_epochs": 1, "stopped_reason": "converged", "dataset": {"n_windows": 1574}}), encoding="utf-8")
            (suite_dir / "cells" / cell_id).mkdir(parents=True, exist_ok=True)
            (suite_dir / "cells" / cell_id / "experiment.yaml").write_text(f"experiment:\n  description: r{idx}\n  seed: 42\ntrain:\n  readout: linear\n", encoding="utf-8")
            lines.append(json.dumps({"cell_id": cell_id, "run_dir": str(run_dir), "overrides": {}, "config_sha256": f"sha-{cell_id}"}))
        (suite_dir / "registry.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return suite_dir

    def test_refuses_to_baseline_a_run_with_no_work_counter(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = self._recurrence_suite(Path(tmp))
            with self.assertRaises(mb.BaselineError) as ctx:
                mb.build_baseline("t", [suite])
            self.assertIn("no countable work", str(ctx.exception))

    def test_the_refusal_names_why_rather_than_just_refusing(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = self._recurrence_suite(Path(tmp))
            with self.assertRaises(mb.BaselineError) as ctx:
                mb.build_baseline("t", [suite])
            message = str(ctx.exception)
            self.assertIn("n_epochs", message)
            self.assertIn("Report these runs instead", message)
