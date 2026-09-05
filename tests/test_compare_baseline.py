#!/usr/bin/env python3
"""Hermetic tests for ``util/experiments/compare_baseline.py`` (P2 item 1.2).

This is the gate itself, so the tests are about the three outcomes staying DISTINCT:

* **PASS / FAIL** -- the work half, compared exactly. A ``step_count`` change is a statement
  about the code (item 1.5's decision), and the test asserts exit code 1, not merely a
  non-zero one, because a caller must be able to tell a failure from a refusal.
* **REFUSED** -- identity or host mismatch, exit 2. Verified against the real failure this
  design exists to prevent: the pre-``cascor#618`` PF-1 run has 4012 steps against the
  post-fix baseline's 1770, so a comparator without the identity precondition would report a
  **127% work regression** for what is simply a different workload. That is how a gate earns
  a reputation for lying and gets switched off while still green.
* **WAIVED** -- never PASS, always carrying the operator's reason.

And one property that is easy to lose later: **speed cannot fail the gate**, at any
magnitude. A test drives a 10x speed difference with matching work and asserts PASS.

``util/`` draws "(no files to check) Skipped" from every pre-commit Python hook, so this
unittest is the gate for this module.
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

SERIES_HEADER = "ts_unix,fsm_status,current_epoch,current_hidden_units," "juniper_cascor_candidate_correlation,juniper_cascor_hidden_units_total," "juniper_cascor_training_loss,juniper_cascor_training_accuracy_ratio," f"{rrm.STEP_SUM_COLUMN},{rrm.STEP_COUNT_COLUMN}\n"


def _suite(root: Path, name: str, *, step_count=1770, step_sum=63.0, epochs=4000, cells=2, with_cell_yaml=True, reason="early_stopped") -> Path:
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
                    "environment": {"nproc": 16, "python": "3.13.13", "platform": "Linux-test", "thread_env": {"OMP_NUM_THREADS": None}},
                    "metrics_scraped": {"scrape_confirmed": True},
                    "completion_reason": reason,
                }
            ),
            encoding="utf-8",
        )
        (run_dir / "artifacts" / "results" / "metrics_series.csv").write_text(SERIES_HEADER + f"1000.0,TRAINING,1,1,0.1,1,0.5,0.9,{step_sum},{step_count}\n", encoding="utf-8")
        if with_cell_yaml:
            (suite_dir / "cells" / cell_id).mkdir(parents=True, exist_ok=True)
            (suite_dir / "cells" / cell_id / "experiment.yaml").write_text(f"experiment:\n  description: repeat {idx}\n  seed: 42\ntraining:\n  params:\n    max_epochs: {epochs}\n", encoding="utf-8")
        lines.append(json.dumps({"cell_id": cell_id, "run_dir": str(run_dir), "overrides": {}, "config_sha256": f"sha-{cell_id}"}))
    (suite_dir / "registry.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return suite_dir


def _baseline(root: Path, tag: str, suite: Path):
    payload = mb.build_baseline(tag, [suite])
    manifests = {r["run_id"]: rrm._load_json(Path(r["run_dir"]) / "manifest.json") for r in rrm.read_suite(suite)}
    return payload, mb.collect_host(list(manifests.values()))


class WorkHalfTest(unittest.TestCase):
    def test_matching_work_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s")
            payload, host = _baseline(Path(tmp), "t", suite)
            result = cb.compare(payload, host, [suite])
            self.assertEqual(result["verdict"], cb.PASS)
            self.assertEqual(cb.EXIT[result["verdict"]], 0)

    def test_moved_work_FAILS_with_exit_1(self):
        # Item 1.5's decision. Exit 1 specifically -- a caller must distinguish a real failure
        # from a refusal, which is exit 2.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand", step_count=1771)  # same config -> same fingerprint
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.FAIL)
            self.assertEqual(cb.EXIT[result["verdict"]], 1)
            self.assertFalse(result["scenarios"][0]["work"]["match"])

    def test_a_single_step_difference_is_enough(self):
        # "Exactly" means exactly: 1770 vs 1771 fails. There is no tolerance to tune.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            result = cb.compare(payload, host, [_suite(Path(tmp), "cand", step_count=1771)])
            self.assertEqual(result["verdict"], cb.FAIL)


class SpeedHalfTest(unittest.TestCase):
    def test_speed_cannot_fail_the_gate_at_any_magnitude(self):
        # A 10x slowdown with identical work is still a PASS. The host's own drift floor is
        # 13-20.5%, so a speed threshold would fire on an idle machine.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_sum=63.0, step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand", step_sum=630.0, step_count=1770)
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.PASS)
            self.assertGreater(result["scenarios"][0]["speed"]["delta_pct"], 500)
            self.assertFalse(result["scenarios"][0]["speed"]["gated"])

    def test_speed_delta_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_sum=100.0, step_count=1000)
            payload, host = _baseline(Path(tmp), "t", base)
            result = cb.compare(payload, host, [_suite(Path(tmp), "cand", step_sum=110.0, step_count=1000)])
            self.assertAlmostEqual(result["scenarios"][0]["speed"]["delta_pct"], 10.0, places=6)


class IdentityRefusalTest(unittest.TestCase):
    def test_different_workload_is_REFUSED_not_failed(self):
        # The real case: pre-cascor#618 PF-1 ran 4012 steps, the post-fix baseline holds 1770.
        # Without this, the gate would report a 127% "regression" for a config change.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", epochs=4000, step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand", epochs=500, step_count=4012)
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(cb.EXIT[result["verdict"]], 2)
            self.assertIn("INVALID comparison rather than a regression", " ".join(result["reasons"]))

    def test_unknown_identity_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base")
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand", with_cell_yaml=False)
            self.assertEqual(cb.compare(payload, host, [candidate])["verdict"], cb.REFUSED)

    def test_incoherent_candidate_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base")
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand")
            # Break the candidate's own work invariant by rewriting one cell's series.
            row = rrm.read_suite(candidate)[0]
            series = Path(row["run_dir"]) / "artifacts/results/metrics_series.csv"
            series.write_text(SERIES_HEADER + "1000.0,TRAINING,1,1,0.1,1,0.5,0.9,63.0,9999\n", encoding="utf-8")
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("not a set of repeats", " ".join(result["reasons"]))


class HostRefusalTest(unittest.TestCase):
    def test_cpu_identity_mismatch_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s")
            payload, host = _baseline(Path(tmp), "t", suite)
            foreign = dict(host, cpu_model="Some Other CPU")
            result = cb.compare(payload, foreign, [suite])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("cpu_model", " ".join(result["reasons"]) + json.dumps(result["host"]))

    def test_thread_budget_mismatch_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s")
            payload, host = _baseline(Path(tmp), "t", suite)
            foreign = dict(host, thread_budget={"OMP_NUM_THREADS": "4"})
            self.assertEqual(cb.compare(payload, foreign, [suite])["verdict"], cb.REFUSED)

    def test_package_version_difference_is_ADVISORY_not_blocking(self):
        # A torch bump changes the reported SPEED but not the gated WORK count, so refusing
        # would make a routine dependency bump un-comparable for no benefit.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s")
            payload, host = _baseline(Path(tmp), "t", suite)
            foreign = json.loads(json.dumps(host))
            foreign["versions"]["torch"] = "0.0.1-different"
            result = cb.compare(payload, foreign, [suite])
            self.assertEqual(result["verdict"], cb.PASS)
            self.assertIn("torch", result["host"]["advisory_differences"])


class WaiverTest(unittest.TestCase):
    def test_waiver_yields_WAIVED_not_PASS(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand", step_count=1771)
            result = cb.compare(payload, host, [candidate], accept_work_change="deliberate: raised the epoch budget")
            self.assertEqual(result["verdict"], cb.WAIVED)
            self.assertEqual(cb.EXIT[result["verdict"]], 0)
            self.assertEqual(result["waiver"]["reason"], "deliberate: raised the epoch budget")

    def test_waiver_does_not_mask_a_refusal(self):
        # A waiver blesses a WORK change, not an invalid comparison. Letting it override a
        # refusal would turn "I know the work moved" into "compare anything to anything".
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", epochs=4000)
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand", epochs=500)
            result = cb.compare(payload, host, [candidate], accept_work_change="I really mean it")
            self.assertEqual(result["verdict"], cb.REFUSED)

    def test_render_does_not_claim_a_waiver_that_had_no_effect(self):
        """Found by running it: the first draft printed "WAIVED by operator" under a REFUSED
        verdict, which reads as though the override worked. Exit code was right (2), the words
        were not -- and the words are what an operator acts on."""
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", epochs=4000)
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand", epochs=500)
            result = cb.compare(payload, host, [candidate], accept_work_change="no effect here")
            text = cb.render(result)
            self.assertIn("NO effect", text)
            self.assertNotIn("WAIVED by operator", text)

    def test_render_reports_a_waiver_that_DID_take_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand", step_count=1771)
            text = cb.render(cb.compare(payload, host, [candidate], accept_work_change="deliberate"))
            self.assertIn("WAIVED by operator: deliberate", text)

    def test_empty_reason_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s")
            with contextlib.redirect_stderr(io.StringIO()):
                rc = cb.main(["--baseline", "t", "--suite", str(suite), "--run-root", str(Path(tmp)), "--accept-work-change", "   "])
            self.assertEqual(rc, 2, "a whitespace-only reason is not a reason")


class CliTest(unittest.TestCase):
    def test_missing_baseline_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s")
            with contextlib.redirect_stderr(io.StringIO()):
                rc = cb.main(["--baseline", "nope", "--suite", str(suite), "--run-root", str(Path(tmp))])
            self.assertEqual(rc, 2)

    def test_end_to_end_pass_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite = _suite(root, "s")
            payload, host = _baseline(root, "t", suite)
            mb.write_baseline(root, "t", payload, {}, host)
            with contextlib.redirect_stdout(io.StringIO()) as out:
                rc = cb.main(["--baseline", "t", "--suite", str(suite), "--run-root", str(root)])
            self.assertEqual(rc, 0)
            self.assertIn("PASS", out.getvalue())

    def test_json_mode_is_parseable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite = _suite(root, "s")
            payload, host = _baseline(root, "t", suite)
            mb.write_baseline(root, "t", payload, {}, host)
            with contextlib.redirect_stdout(io.StringIO()) as out:
                cb.main(["--baseline", "t", "--suite", str(suite), "--run-root", str(root), "--json"])
            self.assertEqual(json.loads(out.getvalue())["verdict"], "PASS")

    def test_exit_codes_are_three_distinct_values(self):
        # PASS/WAIVED share 0 deliberately; FAIL and REFUSED must NOT collapse together.
        self.assertEqual(cb.EXIT[cb.PASS], 0)
        self.assertEqual(cb.EXIT[cb.WAIVED], 0)
        self.assertEqual(cb.EXIT[cb.FAIL], 1)
        self.assertEqual(cb.EXIT[cb.REFUSED], 2)
        self.assertNotEqual(cb.EXIT[cb.FAIL], cb.EXIT[cb.REFUSED])


class TerminationBranchTest(unittest.TestCase):
    """The determinism question, settled 2026-09-04 and pinned here.

    `step_count` is deterministic for a seed-fixed config ONLY GIVEN the branch that ended
    training. Corpus census (`util/ad-hoc/2026-09-04_step_count_determinism_census.py`): 333
    runs, 153 distinct configs, 79 repeated, **29 divergent in step_count — and all 29 fully
    explained by `completion_reason`**, with ZERO still divergent within a branch.

    The real case this prevents: one config, identical seeds, all `succeeded`, giving 6496
    (`early_stopped`) / 6095 (`below_threshold`) / 6496 (`early_stopped`). Before this guard
    the comparator emitted **FAIL exit 1** for the middle one — a false regression, which is
    the failure mode that gets a gate switched off.
    """

    def test_a_flipped_branch_REFUSES_rather_than_FAILS(self):
        # The counterexample, reproduced in miniature.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=6496, reason="early_stopped")
            payload, host = _baseline(Path(tmp), "t", base)
            cand = _suite(Path(tmp), "cand", step_count=6095, reason="below_threshold")
            result = cb.compare(payload, host, [cand])
            self.assertEqual(result["verdict"], cb.REFUSED, "a branch flip is not a work regression")
            self.assertEqual(cb.EXIT[result["verdict"]], 2)
            self.assertIn("termination branch", " ".join(result["reasons"]).lower() + "step_count is deterministic only WITHIN a termination branch")

    def test_same_branch_still_FAILS_on_a_real_move(self):
        # The guard must not swallow genuine regressions.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770, reason="early_stopped")
            payload, host = _baseline(Path(tmp), "t", base)
            cand = _suite(Path(tmp), "cand", step_count=1771, reason="early_stopped")
            result = cb.compare(payload, host, [cand])
            self.assertEqual(result["verdict"], cb.FAIL)
            self.assertEqual(cb.EXIT[result["verdict"]], 1)

    def test_truncated_termination_is_refused(self):
        # timed_out stops the DRIVER, not the workload: the histogram is cut short, so the
        # count measures the budget rather than the code.
        for reason in ("timed_out", "torn_down_early", "stalled"):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as tmp:
                base = _suite(Path(tmp), "base", reason="early_stopped")
                payload, host = _baseline(Path(tmp), "t", base)
                cand = _suite(Path(tmp), "cand", reason=reason)
                self.assertEqual(cb.compare(payload, host, [cand])["verdict"], cb.REFUSED)

    def test_mixed_branches_within_a_candidate_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", reason="early_stopped")
            payload, host = _baseline(Path(tmp), "t", base)
            cand = _suite(Path(tmp), "cand", cells=2, reason="early_stopped")
            # Rewrite one cell's manifest so the two cells disagree.
            row = rrm.read_suite(cand)[1]
            mpath = Path(row["run_dir"]) / "manifest.json"
            m = json.loads(mpath.read_text())
            m["completion_reason"] = "below_threshold"
            mpath.write_text(json.dumps(m), encoding="utf-8")
            result = cb.compare(payload, host, [cand])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("different branches", " ".join(result["reasons"]))

    def test_absent_reason_fails_CLOSED(self):
        # Unknown branch means the precondition cannot be checked. Refuse rather than assume.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", reason="early_stopped")
            payload, host = _baseline(Path(tmp), "t", base)
            cand = _suite(Path(tmp), "cand", reason=None)
            self.assertEqual(cb.compare(payload, host, [cand])["verdict"], cb.REFUSED)

    def test_mixed_known_and_missing_reason_is_refused(self):
        # Dropping None before uniqueness (the ml#1613 / #1622 class) would treat one
        # early_stopped cell plus one null as a single branch and PASS.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", reason="early_stopped")
            payload, host = _baseline(Path(tmp), "t", base)
            cand = _suite(Path(tmp), "cand", cells=2, reason="early_stopped")
            row = rrm.read_suite(cand)[1]
            mpath = Path(row["run_dir"]) / "manifest.json"
            m = json.loads(mpath.read_text())
            m["completion_reason"] = None
            mpath.write_text(json.dumps(m), encoding="utf-8")
            result = cb.compare(payload, host, [cand])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(cb.EXIT[result["verdict"]], 2)

    def test_driver_timeout_with_null_reason_is_refused(self):
        # Production shape: the driver writes outcome=timed_out while the service is still
        # TRAINING, so completion_reason is None. Stuffing "timed_out" into the reason field
        # is not how manifests look; the guard must read outcome.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", reason="early_stopped")
            payload, host = _baseline(Path(tmp), "t", base)
            cand = _suite(Path(tmp), "cand", cells=2, reason="early_stopped")
            row = rrm.read_suite(cand)[1]
            mpath = Path(row["run_dir"]) / "manifest.json"
            m = json.loads(mpath.read_text())
            m["outcome"] = "timed_out"
            m["completion_reason"] = None
            mpath.write_text(json.dumps(m), encoding="utf-8")
            result = cb.compare(payload, host, [cand])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("BUDGET", " ".join(result["reasons"]))


if __name__ == "__main__":
    unittest.main()
