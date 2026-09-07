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

    def test_zero_baseline_speed_is_n_a_and_still_passes(self):
        # `if base_speed and cand_speed` treats 0 as missing. Rewriting that as `is not None`
        # would divide by zero. Matching work with a zero baseline speed must still PASS.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_sum=0.0, step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            result = cb.compare(payload, host, [_suite(Path(tmp), "cand", step_sum=63.0, step_count=1770)])
            self.assertEqual(result["verdict"], cb.PASS)
            self.assertIsNone(result["scenarios"][0]["speed"]["delta_pct"])
            self.assertIn("n/a", cb.render(result))


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

    def test_a_non_dict_work_section_is_REFUSED_not_an_AttributeError(self):
        # A baseline is written once and never rewritten, so a malformed `work` outlives the
        # writer that made it. `(matched.get("work") or {}).get(...)` passes a truthy non-dict
        # through to `.get` and aborts the whole comparison -- including the sibling suites whose
        # reasons were already collected. It must read as "no branch recorded" and take the
        # existing fail-closed path instead.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s")
            payload, host = _baseline(Path(tmp), "t", suite)
            payload["scenarios"][0]["work"] = "1770 steps"
            result = cb.compare(payload, host, [suite])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("no completion_reason", " ".join(result["reasons"]))

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

    def test_mixed_known_and_unknown_identity_is_REFUSED_not_passed(self):
        # Dropping None before the uniqueness test would treat "1 known + 1 missing YAML" as a
        # single workload and PASS against the known cell. Unknown on EITHER side is a refusal.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base")
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand")
            (candidate / "cells" / "c001" / "experiment.yaml").unlink()
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(cb.EXIT[result["verdict"]], 2)
            # The REFUSAL is the property; "cannot be identified" was this branch's wording.
            # Main says "(or their identity is unknown) -- cannot compare". Asserting the
            # verdict plus the substantive phrase keeps the discrimination without pinning
            # prose: a comparator that PASSED here would fail on the verdict line above,
            # whichever words it printed.
            self.assertIn("identity is unknown", " ".join(result["reasons"]))
            self.assertIn("cannot compare", " ".join(result["reasons"]))

    def test_one_unmeasured_cell_is_REFUSED_not_passed(self):
        # work_invariant used to drop missing step_count before testing uniqueness, so a suite
        # with one matching cell and one missing series would PASS. make_baseline already
        # refuses this shape; the comparator must too.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base")
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand")
            series = Path(rrm.read_suite(candidate)[1]["run_dir"]) / "artifacts/results/metrics_series.csv"
            series.unlink()
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            # Same: main says "no step-duration data ... would satisfy it vacuously".
            # "unmeasured" was this branch's word for the same refusal.
            self.assertIn("no step-duration data", " ".join(result["reasons"]))
            self.assertIn("vacuously", " ".join(result["reasons"]))

    def test_different_workload_with_matching_step_count_is_still_REFUSED(self):
        # The silent-green complement of the 4012-vs-1770 case. A config edit that happens to
        # keep step_count identical would PASS if identity were dropped; the existing test
        # would still FAIL (loud, wrong reason) because its counts differ.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", epochs=4000, step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand", epochs=500, step_count=1770)
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(result["scenarios"], [])
            self.assertIn("INVALID comparison rather than a regression", " ".join(result["reasons"]))

    def test_mixed_fingerprints_in_candidate_are_REFUSED_not_first_matched(self):
        # Two cells, two known identities, identical step_count. Picking the first fingerprint
        # that happens to be in the baseline would PASS; the suite is not a set of repeats.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", epochs=4000, step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand", cells=2, epochs=4000, step_count=1770)
            (candidate / "cells" / "c001" / "experiment.yaml").write_text(
                "experiment:\n  description: other workload\n  seed: 42\ntraining:\n  params:\n    max_epochs: 500\n",
                encoding="utf-8",
            )
            result = cb.compare(payload, host, [candidate])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(result["scenarios"], [])
            self.assertIn("different workloads", " ".join(result["reasons"]))

    def test_empty_candidate_suite_is_REFUSED_not_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base")
            payload, host = _baseline(Path(tmp), "t", base)
            empty = Path(tmp) / "empty"
            empty.mkdir()
            result = cb.compare(payload, host, [empty])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(result["scenarios"], [])
            self.assertIn("no registry.jsonl or no cells", " ".join(result["reasons"]))


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

    def test_host_mismatch_still_REFUSES_even_when_work_also_moved(self):
        # Cross-hardware plus a step_count delta cannot be attributed to the code.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            candidate = _suite(Path(tmp), "cand", step_count=1771)
            foreign = dict(host, cpu_model="Some Other CPU")
            self.assertEqual(cb.compare(payload, foreign, [candidate])["verdict"], cb.REFUSED)

    def test_cpu_count_mismatch_is_refused(self):
        # The third HOST_IDENTITY_FIELDS member. cpu_model and thread_budget are pinned above;
        # dropping cpu_count from the blocking set would make a core-count change advisory.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s")
            payload, host = _baseline(Path(tmp), "t", suite)
            foreign = dict(host, cpu_count=1)
            result = cb.compare(payload, foreign, [suite])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("cpu_count", " ".join(result["reasons"]) + json.dumps(result["host"]))


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

    def test_a_real_FAIL_beats_a_SIBLING_suite_refusal(self):
        """The multi-suite case the single-suite guard above cannot reach.

        ``test_waiver_does_not_mask_a_refusal`` passes ONE suite whose identity is unknown.
        That suite yields no scenario result at all, so "did work move?" finds nothing and
        the chain falls through to REFUSED no matter where the refusal check sits. The
        guard therefore cannot detect a reordering of the verdict chain at all.

        This is the case that discriminates. TWO suites are compared:

          * ``moved``   -- same workload as the baseline, different ``step_count``, so it
                           DOES produce a scenario result and the work half does not match;
          * ``foreign`` -- a different workload, so its identity is unknown and it
                           contributes a REFUSAL reason and no scenario.

        Now "work moved" and "a refusal reason exists" are simultaneously true. ml#1741
        settled the precedence deliberately -- **FAIL > REFUSED > PASS** -- because the old
        ``if reasons: REFUSED`` first meant one unreadable suite on the command line
        converted a REAL regression on another suite into "could not compare", and a caller
        treating exit 2 as non-blocking then loses the regression entirely.

        So the verdict here is FAIL / exit 1: a positively-detected work regression is
        knowledge and outranks an unrelated refusal. Pinned so a future reordering that
        restores the old precedence, and re-loses the regression, goes red.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770, epochs=4000)
            payload, host = _baseline(Path(tmp), "t", base)
            moved = _suite(Path(tmp), "moved", step_count=1771, epochs=4000)
            foreign = _suite(Path(tmp), "foreign", step_count=1770, epochs=500)

            result = cb.compare(payload, host, [moved, foreign])

            self.assertEqual(result["verdict"], cb.FAIL, "a detected regression outranks an unrelated refusal")
            self.assertEqual(cb.EXIT[result["verdict"]], 1, "exit 1, not the refusal's 2 -- a caller must be able to block")
            self.assertTrue(result["reasons"], "the sibling's refusal reason must still survive into the result")

    def test_a_waived_run_still_REPORTS_the_uncompared_sibling(self):
        """With a waiver the same pair is WAIVED / exit 0 -- so the REPORT is the only signal.

        A waiver blesses the deliberate work change, and under the FAIL > REFUSED
        precedence it carries the whole run to exit 0 even though ``foreign`` was never
        compared to anything. That is defensible only while the operator is still TOLD:
        ``render`` prints every reason as a ``REFUSED:`` line regardless of verdict, so the
        uncompared suite is named on screen.

        This pins that reporting, not the exit code. If someone later suppresses reasons
        under a non-REFUSED verdict as cosmetic, exit 0 becomes genuinely silent about a
        suite that was never compared -- and nothing else in this file would notice.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770, epochs=4000)
            payload, host = _baseline(Path(tmp), "t", base)
            moved = _suite(Path(tmp), "moved", step_count=1771, epochs=4000)
            foreign = _suite(Path(tmp), "foreign", step_count=1770, epochs=500)

            result = cb.compare(payload, host, [moved, foreign], accept_work_change="deliberate epoch bump")
            self.assertEqual(result["verdict"], cb.WAIVED)
            self.assertEqual(cb.EXIT[result["verdict"]], 0)

            text = cb.render(result)
            self.assertIn("REFUSED:", text, "the uncompared sibling must be named even under WAIVED")
            self.assertIn("foreign", text)

    def test_moved_work_alone_IS_waivable(self):
        # The other control, and the reason this guard is narrow: with NO refusing sibling,
        # a waiver legitimately turns a moved-work FAIL into WAIVED / exit 0. If this ever
        # goes red, the guard above has over-tightened and broken the waiver's real purpose.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770, epochs=4000)
            payload, host = _baseline(Path(tmp), "t", base)
            moved = _suite(Path(tmp), "moved", step_count=1771, epochs=4000)
            result = cb.compare(payload, host, [moved], accept_work_change="deliberate epoch bump")
            self.assertEqual(result["verdict"], cb.WAIVED)
            self.assertEqual(cb.EXIT[result["verdict"]], 0)

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

    def test_unreadable_baseline_json_in_existing_tag_dir_exits_2(self):
        # Distinct from a missing tag directory: the dir is present, baseline.json is not a payload.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite = _suite(root, "s")
            payload, host = _baseline(root, "t", suite)
            mb.write_baseline(root, "t", payload, {}, host)
            (root / mb.BASELINES_DIRNAME / "t" / "baseline.json").write_text("{not-json", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()) as err:
                rc = cb.main(["--baseline", "t", "--suite", str(suite), "--run-root", str(root)])
            self.assertEqual(rc, 2)
            self.assertIn("missing or unreadable", err.getvalue())

    def test_end_to_end_fail_exits_1(self):
        # FAIL through argparse, not just compare() + the EXIT dict. A caller that keys on
        # exit 1 vs 2 must not see a wiring miss that always returns 0 after printing FAIL.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = _suite(root, "base", step_count=1770)
            payload, host = _baseline(root, "t", base)
            mb.write_baseline(root, "t", payload, {}, host)
            candidate = _suite(root, "cand", step_count=1771)
            with contextlib.redirect_stdout(io.StringIO()) as out:
                rc = cb.main(["--baseline", "t", "--suite", str(candidate), "--run-root", str(root)])
            self.assertEqual(rc, 1)
            self.assertIn("FAIL", out.getvalue())


if __name__ == "__main__":
    unittest.main()


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


class FailOpenRegressionTest(unittest.TestCase):
    """The two fail-open holes `ml#1733` shipped, and the vacuous test that hid one.

    Both were found by validating the FIX rather than re-validating the original claim.
    """

    def test_truncation_is_detected_from_OUTCOME_in_the_production_shape(self):
        """The driver writes ``outcome=timed_out`` while the service is still TRAINING, so
        ``completion_reason`` stays None. The original guard matched the truncating names against
        ``completion_reason`` and could never fire: across 370 manifests those names appear ONLY in
        ``outcome``, and all 15 driver-stopped runs carry ``completion_reason=None``.

        The original test passed only because its fixture wrote "timed_out" into the reason field —
        a shape production never produces. This asserts the real one.
        """
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s", reason="early_stopped")
            row = rrm.read_suite(suite)[0]
            mpath = Path(row["run_dir"]) / "manifest.json"
            m = json.loads(mpath.read_text())
            m["outcome"] = "timed_out"
            m["completion_reason"] = None
            mpath.write_text(json.dumps(m), encoding="utf-8")

            summary = rrm.summarise(rrm.read_suite(suite))
            self.assertEqual(summary["truncated_terminations"], ["timed_out"], "truncation must be read from outcome, not completion_reason")

    def test_a_MIXED_null_reason_no_longer_reads_as_one_branch(self):
        """`4x early_stopped + 1x None` used to read as a single branch, because the reason set was
        built with `if r.get("completion_reason")` — dropping unknown cells BEFORE uniqueness. That
        is fail-open on exactly the mixed case the guard exists for."""
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s", cells=2, reason="early_stopped")
            row = rrm.read_suite(suite)[1]
            mpath = Path(row["run_dir"]) / "manifest.json"
            m = json.loads(mpath.read_text())
            m["completion_reason"] = None
            mpath.write_text(json.dumps(m), encoding="utf-8")

            summary = rrm.summarise(rrm.read_suite(suite))
            self.assertTrue(summary["has_unknown_completion_reason"])
            self.assertFalse(summary["single_completion_reason"], "a mixed known/unknown set is not one branch")

    def test_an_ALL_unknown_suite_also_refuses(self):
        # All-None must not look uniform either: one distinct value, but the value is "unknown".
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s", cells=2, reason=None)
            summary = rrm.summarise(rrm.read_suite(suite))
            self.assertFalse(summary["single_completion_reason"])

    def test_the_mixed_case_REFUSES_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", reason="early_stopped")
            payload, host = _baseline(Path(tmp), "t", base)
            cand = _suite(Path(tmp), "cand", cells=2, reason="early_stopped")
            row = rrm.read_suite(cand)[1]
            mpath = Path(row["run_dir"]) / "manifest.json"
            m = json.loads(mpath.read_text())
            m["completion_reason"] = None
            mpath.write_text(json.dumps(m), encoding="utf-8")
            self.assertEqual(cb.compare(payload, host, [cand])["verdict"], cb.REFUSED)

    def test_a_driver_stopped_candidate_REFUSES_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", reason="early_stopped")
            payload, host = _baseline(Path(tmp), "t", base)
            cand = _suite(Path(tmp), "cand", reason="early_stopped")
            for row in rrm.read_suite(cand):
                mpath = Path(row["run_dir"]) / "manifest.json"
                m = json.loads(mpath.read_text())
                m["outcome"] = "torn_down_early"
                m["completion_reason"] = None
                mpath.write_text(json.dumps(m), encoding="utf-8")
            result = cb.compare(payload, host, [cand])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("torn_down_early", " ".join(result["reasons"]))


class ComparatorDefectTest(unittest.TestCase):
    """A1 / A2 / A3 / A4 / A6 / A7 — the ways the comparator reached a wrong verdict.

    All six were found by adversarial validation of the shipped gate. The asymmetry behind
    A1/A2/A4 is the theme: a suite `make_baseline` would REJECT was still good enough to
    COMPARE, so the comparator passed on runs the blesser would refuse.
    """

    def _mutate(self, suite: Path, index: int, **fields) -> None:
        row = rrm.read_suite(suite)[index]
        mpath = Path(row["run_dir"]) / "manifest.json"
        m = json.loads(mpath.read_text())
        m.update(fields)
        mpath.write_text(json.dumps(m), encoding="utf-8")

    def test_A3_a_real_FAIL_is_not_masked_by_an_unrelated_refusal(self):
        """THE ONE THAT MATTERS FOR CI WIRING.

        `if reasons: verdict = REFUSED` used to precede the FAIL branch, so adding any
        unreadable suite to the command line converted a true FAIL(1) into REFUSED(2). A
        caller treating exit 2 as "cannot compare, don't block" would lose the regression.
        Precedence is now FAIL > REFUSED > PASS.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            regressed = _suite(Path(tmp), "cand", step_count=1771)
            empty = Path(tmp) / "empty"
            empty.mkdir()

            alone = cb.compare(payload, host, [regressed])
            self.assertEqual(alone["verdict"], cb.FAIL, "control: the regression fails on its own")

            with_noise = cb.compare(payload, host, [empty, regressed])
            self.assertEqual(with_noise["verdict"], cb.FAIL, "an unreadable suite must not mask a real regression")
            self.assertEqual(cb.EXIT[with_noise["verdict"]], 1)
            self.assertTrue(with_noise["reasons"], "the refusal is still reported alongside the failure")

    def test_A3_a_refusal_still_beats_a_PASS(self):
        # "Could not verify" must never report clean.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base")
            payload, host = _baseline(Path(tmp), "t", base)
            empty = Path(tmp) / "empty"
            empty.mkdir()
            self.assertEqual(cb.compare(payload, host, [empty, base])["verdict"], cb.REFUSED)

    def test_A1_unmeasured_cells_are_refused(self):
        # 4 of 5 cells with no metrics used to PASS: nulls were dropped before the work
        # invariant, so one surviving cell satisfied it vacuously.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base")
            payload, host = _baseline(Path(tmp), "t", base)
            cand = _suite(Path(tmp), "cand", cells=2)
            series = Path(rrm.read_suite(cand)[0]["run_dir"]) / "artifacts/results/metrics_series.csv"
            series.unlink()
            result = cb.compare(payload, host, [cand])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("no step-duration data", " ".join(result["reasons"]))

    def test_A2_a_failed_candidate_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base")
            payload, host = _baseline(Path(tmp), "t", base)
            cand = _suite(Path(tmp), "cand", cells=2)
            self._mutate(cand, 0, outcome="failed")
            self.assertEqual(cb.compare(payload, host, [cand])["verdict"], cb.REFUSED)

    def test_A4_zero_work_on_both_sides_is_refused(self):
        # `bool(counts)` is True for [0.0, 0.0], so a do-nothing run compared equal and PASSed.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=0, step_sum=0.0)
            cand = _suite(Path(tmp), "cand", step_count=0, step_sum=0.0)
            # make_baseline already refuses this, so build the payload by hand to test the
            # comparator's own guard rather than the blesser's.
            payload = {"tag": "t", "scenarios": [{"suite": "base", "workload_fingerprint": rrm.summarise(rrm.read_suite(base))["workload_fingerprints"][0], "work": {"step_count": 0, "completion_reason": "early_stopped"}, "speed": {"mean": 0.0}}]}
            host = mb.collect_host([rrm._load_json(Path(r["run_dir"]) / "manifest.json") for r in rrm.read_suite(base)])
            result = cb.compare(payload, host, [cand])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("nobody did any work", " ".join(result["reasons"]))

    def test_A6_partial_scenario_coverage_is_refused(self):
        # A PASS must not mean "the scenarios you happened to pass still match".
        with tempfile.TemporaryDirectory() as tmp:
            covered = _suite(Path(tmp), "a", epochs=4000)
            other = _suite(Path(tmp), "b", epochs=500)
            payload = mb.build_baseline("t", [covered, other])
            host = mb.collect_host([rrm._load_json(Path(r["run_dir"]) / "manifest.json") for r in rrm.read_suite(covered)])
            result = cb.compare(payload, host, [covered])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("uncovered", " ".join(result["reasons"]))

    def test_A7_duplicate_baseline_fingerprints_are_refused(self):
        # Two scenarios sharing a fingerprint used to collapse to the LAST in a dict
        # comprehension, so a candidate could be judged against an arbitrary one -- and the
        # doc's own warning is that a false FAIL is the credibility failure.
        with tempfile.TemporaryDirectory() as tmp:
            suite = _suite(Path(tmp), "s")
            payload = mb.build_baseline("t", [suite])
            fp = payload["scenarios"][0]["workload_fingerprint"]
            twin = json.loads(json.dumps(payload["scenarios"][0]))
            twin["work"]["step_count"] = 9999
            payload["scenarios"].append(twin)
            host = mb.collect_host([rrm._load_json(Path(r["run_dir"]) / "manifest.json") for r in rrm.read_suite(suite)])
            result = cb.compare(payload, host, [suite])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("DUPLICATE workload", " ".join(result["reasons"]))
            self.assertIn(fp[:12], " ".join(result["reasons"]))


class VerdictPrecedenceTest(unittest.TestCase):
    def test_sibling_refusal_does_not_hide_a_FAIL(self):
        # --suite is repeatable. Work that moved on a comparable suite is still FAIL even if
        # another suite is a different workload. Collapsing that to REFUSED (exit 2) would hide
        # the gate firing from a caller that treats refusal as "not a code problem".
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            moved = _suite(Path(tmp), "moved", step_count=1771)
            other = _suite(Path(tmp), "other", epochs=500, step_count=4012)
            result = cb.compare(payload, host, [moved, other])
            self.assertEqual(result["verdict"], cb.FAIL)
            self.assertEqual(cb.EXIT[result["verdict"]], 1)
            self.assertFalse(result["scenarios"][0]["work"]["match"])

    def test_sibling_refusal_does_not_PASS_the_comparison(self):
        # The other direction: matching work on one suite plus an incomparable sibling is not
        # a clean PASS. Incomplete comparison stays REFUSED.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base")
            payload, host = _baseline(Path(tmp), "t", base)
            matching = _suite(Path(tmp), "ok")
            other = _suite(Path(tmp), "other", epochs=500, step_count=4012)
            result = cb.compare(payload, host, [matching, other])
            self.assertEqual(result["verdict"], cb.REFUSED)


class MultiSuiteTest(unittest.TestCase):
    def test_one_identity_mismatch_among_suites_REFUSES_the_whole_comparison(self):
        # `--suite` is repeatable. Any refusal must win: a matching sibling must not let a
        # different-workload suite be reported as PASS or as a work FAIL.
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", epochs=4000, step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            matching = _suite(Path(tmp), "match", epochs=4000, step_count=1770)
            foreign = _suite(Path(tmp), "foreign", epochs=500, step_count=1770)
            result = cb.compare(payload, host, [matching, foreign])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("INVALID comparison rather than a regression", " ".join(result["reasons"]))

    def test_one_moved_suite_among_matching_suites_FAILS(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = _suite(Path(tmp), "base", step_count=1770)
            payload, host = _baseline(Path(tmp), "t", base)
            matching = _suite(Path(tmp), "match", step_count=1770)
            moved = _suite(Path(tmp), "moved", step_count=1771)
            result = cb.compare(payload, host, [matching, moved])
            self.assertEqual(result["verdict"], cb.FAIL)
            self.assertEqual(cb.EXIT[result["verdict"]], 1)
            matches = {s["suite"]: s["work"]["match"] for s in result["scenarios"]}
            self.assertEqual(matches, {"match": True, "moved": False})
