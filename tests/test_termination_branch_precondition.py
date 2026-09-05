#!/usr/bin/env python3
"""Complementary pins for the termination-branch precondition (PR #1733).

``tests/test_compare_baseline.py`` already ships the five-case comparator counterexample
(branch flip REFUSES, same-branch move still FAILS, candidate truncated / mixed / absent).
Those tests never call ``make_baseline``'s new refusals, never assert the reader's
summarise fields, and never exercise the baseline-side fail-closed or a same-count
branch flip. This suite is the leftover those tests cannot see.

``util/`` draws "(no files to check) Skipped" from every pre-commit Python hook, so this
unittest is the gate for these properties.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import compare_baseline as cb  # noqa: E402
from experiments import make_baseline as mb  # noqa: E402
from experiments import read_run_metrics as rrm  # noqa: E402

SERIES_HEADER = (
    "ts_unix,fsm_status,current_epoch,current_hidden_units,"
    "juniper_cascor_candidate_correlation,juniper_cascor_hidden_units_total,"
    "juniper_cascor_training_loss,juniper_cascor_training_accuracy_ratio,"
    f"{rrm.STEP_SUM_COLUMN},{rrm.STEP_COUNT_COLUMN}\n"
)


def _write_run(root: Path, run_id: str, *, step_count=1770, step_sum=63.0, reason="early_stopped", omit_reason=False) -> Path:
    run_dir = root / run_id
    (run_dir / "artifacts" / "results").mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "outcome": "succeeded",
        "timings": {"drive": 65.0},
        "drive_loop": {"polls": 14},
        "environment": {"nproc": 16, "python": "3.13.13", "platform": "Linux-test", "thread_env": {"OMP_NUM_THREADS": None}},
        "metrics_scraped": {"scrape_confirmed": True},
    }
    if not omit_reason:
        manifest["completion_reason"] = reason
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (run_dir / "artifacts" / "results" / "metrics_series.csv").write_text(SERIES_HEADER + f"1000.0,TRAINING,1,1,0.1,1,0.5,0.9,{step_sum},{step_count}\n", encoding="utf-8")
    return run_dir


def _write_suite(root: Path, name: str, cells, *, epochs=4000) -> Path:
    """``cells`` is a list of kwargs for ``_write_run`` (plus optional ``omit_reason``)."""
    suite_dir = root / name
    (suite_dir / "cells").mkdir(parents=True, exist_ok=True)
    lines = []
    for idx, kwargs in enumerate(cells):
        kwargs = dict(kwargs)
        cell_id = f"c{idx:03d}"
        run_dir = _write_run(root, f"{name}-run{idx}", **kwargs)
        (suite_dir / "cells" / cell_id).mkdir(parents=True, exist_ok=True)
        (suite_dir / "cells" / cell_id / "experiment.yaml").write_text(
            f"experiment:\n  description: repeat {idx}\n  seed: 42\ntraining:\n  params:\n    max_epochs: {epochs}\n",
            encoding="utf-8",
        )
        lines.append(json.dumps({"cell_id": cell_id, "run_dir": str(run_dir), "overrides": {}, "config_sha256": f"sha-{cell_id}"}))
    (suite_dir / "registry.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return suite_dir


def _baseline(root: Path, tag: str, suite: Path):
    payload = mb.build_baseline(tag, [suite])
    manifests = {r["run_id"]: rrm._load_json(Path(r["run_dir"]) / "manifest.json") for r in rrm.read_suite(suite)}
    return payload, mb.collect_host(list(manifests.values()))


class ReaderExtractTest(unittest.TestCase):
    def test_read_run_carries_the_manifest_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = _write_run(Path(tmp), "r1", reason="below_threshold")
            self.assertEqual(rrm.read_run(run)["completion_reason"], "below_threshold")

    def test_missing_null_and_empty_reasons_are_not_a_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = rrm.read_run(_write_run(root, "missing", omit_reason=True))
            null = rrm.read_run(_write_run(root, "null", reason=None))
            empty = rrm.read_run(_write_run(root, "empty", reason=""))
            self.assertIsNone(missing["completion_reason"])
            self.assertIsNone(null["completion_reason"])
            self.assertEqual(empty["completion_reason"], "")
            summary = rrm.summarise([missing, null, empty])
            self.assertEqual(summary["completion_reasons"], [])
            self.assertFalse(summary["single_completion_reason"])
            self.assertEqual(summary["truncated_terminations"], [])


class SummariseBranchTest(unittest.TestCase):
    def test_matching_reasons_are_a_single_branch(self):
        rows = [{"completion_reason": "early_stopped", "step_count": 1770, "work_countable": True} for _ in range(3)]
        summary = rrm.summarise(rows)
        self.assertEqual(summary["completion_reasons"], ["early_stopped"])
        self.assertTrue(summary["single_completion_reason"])
        self.assertEqual(summary["truncated_terminations"], [])

    def test_mixed_reasons_are_not_a_single_branch(self):
        rows = [
            {"completion_reason": "early_stopped", "step_count": 1770, "work_countable": True},
            {"completion_reason": "below_threshold", "step_count": 1770, "work_countable": True},
        ]
        summary = rrm.summarise(rows)
        self.assertEqual(summary["completion_reasons"], ["below_threshold", "early_stopped"])
        self.assertFalse(summary["single_completion_reason"])

    def test_truncated_set_is_only_the_driver_stops(self):
        self.assertEqual(rrm.TRUNCATING_TERMINATIONS, frozenset({"timed_out", "torn_down_early", "stalled"}))
        rows = [
            {"completion_reason": "early_stopped", "step_count": 100, "work_countable": True},
            {"completion_reason": "timed_out", "step_count": 100, "work_countable": True},
            {"completion_reason": "below_threshold", "step_count": 100, "work_countable": True},
        ]
        self.assertEqual(rrm.summarise(rows)["truncated_terminations"], ["timed_out"])

    def test_all_same_truncating_reason_is_still_truncated(self):
        # single_completion_reason True must NOT hide the budget-vs-code distinction.
        rows = [{"completion_reason": "timed_out", "step_count": 50, "work_countable": True} for _ in range(2)]
        summary = rrm.summarise(rows)
        self.assertTrue(summary["single_completion_reason"])
        self.assertEqual(summary["truncated_terminations"], ["timed_out"])

    def test_a_partially_annotated_suite_is_not_a_single_branch(self):
        # The fail-open #1733's all-absent candidate test cannot see: one labelled cell
        # plus one missing reason used to collapse to a unanimous branch.
        rows = [
            {"completion_reason": "early_stopped", "step_count": 1770, "work_countable": True},
            {"completion_reason": None, "step_count": 1770, "work_countable": True},
        ]
        summary = rrm.summarise(rows)
        self.assertEqual(summary["completion_reasons"], ["early_stopped"])
        self.assertFalse(summary["single_completion_reason"], "a missing neighbour is not a repeat of the labelled cell")

    def test_empty_rows_are_not_a_single_branch(self):
        summary = rrm.summarise([])
        self.assertFalse(summary["single_completion_reason"])
        self.assertEqual(summary["truncated_terminations"], [])


class MakeBaselineBranchTest(unittest.TestCase):
    def test_records_the_reason_beside_the_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), "s", [{}, {}])
            payload = mb.build_baseline("t", [suite])
            work = payload["scenarios"][0]["work"]
            self.assertEqual(work["step_count"], 1770.0)
            self.assertEqual(work["completion_reason"], "early_stopped")
            self.assertTrue(work["invariant"])

    def test_refuses_each_truncating_reason(self):
        for reason in sorted(rrm.TRUNCATING_TERMINATIONS):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as tmp:
                suite = _write_suite(Path(tmp), "s", [{"reason": reason}, {"reason": reason}])
                with self.assertRaises(mb.BaselineError) as ctx:
                    mb.build_baseline("t", [suite])
                message = str(ctx.exception)
                self.assertIn(reason, message)
                self.assertIn("budget", message.lower())

    def test_refuses_mixed_branches(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), "s", [{"reason": "early_stopped"}, {"reason": "below_threshold"}])
            with self.assertRaises(mb.BaselineError) as ctx:
                mb.build_baseline("t", [suite])
            self.assertIn("different branches", str(ctx.exception))

    def test_refuses_a_partially_annotated_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = _write_suite(Path(tmp), "s", [{}, {"omit_reason": True}])
            with self.assertRaises(mb.BaselineError) as ctx:
                mb.build_baseline("t", [suite])
            self.assertIn("different branches", str(ctx.exception))


class CompareComplementTest(unittest.TestCase):
    def test_legacy_baseline_without_a_reason_is_REFUSED(self):
        # Symmetric fail-closed. #1733 pins the CANDIDATE-absent path; a baseline cut
        # before the guard records no branch, and skipping that check makes the guard
        # vacuous where it is most needed.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = _write_suite(root, "base", [{}, {}])
            payload, host = _baseline(root, "pf1-legacy", base)
            payload["scenarios"][0]["work"].pop("completion_reason", None)
            cand = _write_suite(root, "cand", [{}, {}])
            result = cb.compare(payload, host, [cand])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertEqual(cb.EXIT[result["verdict"]], 2)
            joined = " ".join(result["reasons"])
            self.assertIn("no completion_reason", joined)
            self.assertIn("Re-cut", joined)

    def test_same_count_different_branch_is_still_REFUSED(self):
        # #1733's flip test couples 6496 vs 6095. A guard that only refused when the
        # counts ALSO moved would still emit a false FAIL the next time two branches
        # happened to land on the same histogram length.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = _write_suite(root, "base", [{"reason": "early_stopped"}, {"reason": "early_stopped"}])
            payload, host = _baseline(root, "t", base)
            cand = _write_suite(root, "cand", [{"reason": "below_threshold"}, {"reason": "below_threshold"}])
            result = cb.compare(payload, host, [cand])
            self.assertEqual(result["verdict"], cb.REFUSED)
            self.assertIn("WITHIN a termination branch", " ".join(result["reasons"]))

    def test_waiver_cannot_override_a_branch_flip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = _write_suite(root, "base", [{"reason": "early_stopped"}, {"reason": "early_stopped"}])
            payload, host = _baseline(root, "t", base)
            cand = _write_suite(root, "cand", [{"reason": "below_threshold"}, {"reason": "below_threshold"}])
            result = cb.compare(payload, host, [cand], accept_work_change="I really mean it")
            self.assertEqual(result["verdict"], cb.REFUSED)

    def test_partially_annotated_candidate_is_REFUSED(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = _write_suite(root, "base", [{}, {}])
            payload, host = _baseline(root, "t", base)
            cand = _write_suite(root, "cand", [{}, {"omit_reason": True}])
            self.assertEqual(cb.compare(payload, host, [cand])["verdict"], cb.REFUSED)


if __name__ == "__main__":
    unittest.main()
