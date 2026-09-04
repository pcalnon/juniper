#!/usr/bin/env python3
"""Complementary leftover ``StatsSummaryUnitTest`` / ``MetricsScrapedTest`` cannot see.

Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

``tests/test_run_experiment.py`` already owns:

- ``StatsSummaryUnitTest`` — percentiles, delta-derived step stats, correlation
  grouping, ``build_stats`` sequence shapes, degraded-notes assembly, and ONE
  ``render_summary_md`` call that only asserts run-id / ``## recurrence`` /
  ``n_windows``.
- ``MetricsScrapedTest`` — the producer (``rx._metrics_scraped``) tri-state.

Neither suite reads the markdown renderer. The #1550 honesty bug was that a
written target file stood in for a confirmed scrape (five bridged PF-1 runs
wrote the file; Prometheus held no series). The producer is gated; the
``summary.md`` line an operator actually reads is not.

This file pins that leftover plus the step-duration / git / cascor-vs-recurrence
edges the single render call never constructs. Do NOT edit
``tests/test_run_experiment.py``. No production edits.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import stats_summary as ss  # noqa: E402  (path-invoked util import)

SUM = ss.STEP_SUM_COLUMN
COUNT = ss.STEP_COUNT_COLUMN


def _row(step_sum: str, step_count: str) -> dict[str, str]:
    return {SUM: step_sum, COUNT: step_count}


def _render(*, scraped: dict | None = None, git: dict | None = None, cascor: dict | None = None, recurrence: dict | None = None) -> str:
    stats = {
        "identity": {
            "run_id": "r-render",
            "experiment": "e",
            "description": "d",
            "config_sha256": "abc",
            "seeds": {"experiment": 1},
            "git": git or {},
            "packages": {},
        },
        "dataset": {"generator": "g", "generator_version": "1", "task_type": "t", "dataset_id": "d", "shapes": {"kind": "tabular"}},
        "outcome": {"outcome": "succeeded", "acceptance": {"ok": True}, "wall_seconds": 1.0, "timings": {"total": 1.0}},
        "provenance": {"metrics_scraped": scraped or {}, "degraded_notes": []},
    }
    if cascor is not None:
        stats["cascor"] = cascor
    if recurrence is not None:
        stats["recurrence"] = recurrence
    return ss.render_summary_md(stats)


class ScrapeConfirmedRenderTest(unittest.TestCase):
    """The #1550 honesty line: written ≠ scraped; None ≠ False; missing ≠ False."""

    def test_written_true_confirmed_false_keeps_both_facts(self) -> None:
        """The exact false positive: file on disk, Prometheus empty."""
        rendered = _render(scraped={"grafana_bridge": True, "target_file_written": True, "scrape_confirmed": False})
        self.assertIn("target file written: True", rendered)
        self.assertIn("scrape confirmed: False", rendered)
        self.assertNotIn("scrape confirmed: True", rendered)
        self.assertNotIn("n/a (pre-2026-09-01 manifest)", rendered)

    def test_confirmed_none_is_not_false(self) -> None:
        """Unaskable (Prometheus unreachable) must not read as 'nothing scraped'."""
        rendered = _render(scraped={"grafana_bridge": True, "target_file_written": True, "scrape_confirmed": None})
        self.assertIn("scrape confirmed: None", rendered)
        self.assertNotIn("scrape confirmed: False", rendered)
        self.assertNotIn("n/a (pre-2026-09-01 manifest)", rendered)

    def test_missing_confirmed_key_is_pre_cutoff_na(self) -> None:
        """Old manifests used ``present``; the question was never asked."""
        rendered = _render(scraped={"grafana_bridge": False, "present": True})
        self.assertIn("scrape confirmed: n/a (pre-2026-09-01 manifest)", rendered)
        self.assertIn("target file written: True", rendered)
        self.assertNotIn("scrape confirmed: True", rendered)
        self.assertNotIn("scrape confirmed: False", rendered)

    def test_confirmed_true_does_not_use_the_na_fallback(self) -> None:
        rendered = _render(scraped={"grafana_bridge": True, "target_file_written": True, "scrape_confirmed": True})
        self.assertIn("scrape confirmed: True", rendered)
        self.assertNotIn("n/a (pre-2026-09-01 manifest)", rendered)


class StepDurationEdgeTest(unittest.TestCase):
    """``last_count == 0`` and non-advancing counts — the happy-path suite never builds these."""

    def test_last_count_zero_is_none_mean_not_zerodivision(self) -> None:
        """``if last_count`` is load-bearing: ``is not None`` would divide by zero."""
        result = ss.step_duration_stats([_row("1.5", "0"), _row("1.5", "0")])
        self.assertEqual(result["total_steps"], 0)
        self.assertIsNone(result["overall_mean_seconds"])
        self.assertEqual(result["poll_samples"], 0)
        self.assertIsNone(result["p50_seconds"])

    def test_decreasing_count_does_not_mint_a_poll_sample(self) -> None:
        """Reset / scrape rewind: only a strictly greater count yields a per-poll mean."""
        rows = [_row("4.0", "4"), _row("4.0", "4"), _row("1.0", "1"), _row("5.0", "5")]
        result = ss.step_duration_stats(rows)
        # 4→4 skipped, 4→1 skipped, 1→5 is the only advance: (5-1)/(5-1) = 1.0
        self.assertEqual(result["poll_samples"], 1)
        self.assertEqual(result["p50_seconds"], 1.0)
        self.assertEqual(result["total_steps"], 5)
        self.assertEqual(result["overall_mean_seconds"], 1.0)


class GitProvenanceRenderTest(unittest.TestCase):
    def test_dirty_head_is_flagged_not_reproducible(self) -> None:
        sha = "abcdef0123456789" + "0" * 24
        rendered = _render(git={"juniper-ml": {"head_sha": sha, "dirty": True}})
        self.assertIn("`abcdef012345`", rendered)
        self.assertIn("(DIRTY — not reproducible)", rendered)

    def test_clean_head_omits_the_dirty_flag(self) -> None:
        sha = "abcdef0123456789" + "0" * 24
        rendered = _render(git={"juniper-ml": {"head_sha": sha, "dirty": False}})
        self.assertIn("`abcdef012345`", rendered)
        self.assertNotIn("DIRTY", rendered)

    def test_unavailable_git_is_stated(self) -> None:
        rendered = _render(git={"juniper-cascor": {"error": "not a git repo"}})
        self.assertIn("- juniper-cascor: (unavailable)", rendered)
        self.assertNotIn("DIRTY", rendered)


class CascorAndRecurrenceRenderTest(unittest.TestCase):
    def test_cascor_empty_rounds_and_completion_reason(self) -> None:
        rendered = _render(
            cascor={
                "final": {"epoch": 3},
                "eval_scalars": {},
                "candidate_correlation": {"per_round": []},
                "training_step_duration": {"total_steps": 0, "overall_mean_seconds": None, "p50_seconds": None, "p95_seconds": None, "basis": "per-poll mean"},
                "completion_reason": "max_epochs",
            }
        )
        self.assertIn("## cascor", rendered)
        self.assertIn("(no samples)", rendered)
        self.assertIn("completion reason: max_epochs", rendered)
        self.assertNotIn("## recurrence", rendered)

    def test_recurrence_disabled_crossval_is_not_silent(self) -> None:
        rendered = _render(
            recurrence={
                "final_metrics": {"r2": 0.9},
                "n_epochs": 4,
                "stopped_reason": "done",
                "theta": {"value": 0.25, "note": "explicit"},
                "readout": {"rung": "linear", "hyperparameters": {"d": 8}},
                "crossval": None,
            }
        )
        self.assertIn("## recurrence", rendered)
        self.assertIn("(disabled or failed)", rendered)
        self.assertIn("theta: 0.25 (explicit)", rendered)
        self.assertNotIn("## cascor", rendered)

    def test_recurrence_crossval_aggregate_is_rendered(self) -> None:
        rendered = _render(
            recurrence={
                "final_metrics": {"r2": 0.9},
                "n_epochs": 4,
                "stopped_reason": "done",
                "theta": {"value": None, "note": "data-driven (resolved from per-window elapsed time)"},
                "readout": {"rung": "linear", "hyperparameters": {}},
                "crossval": {"n_folds": 3, "task_type": "regression", "eval_aggregate": {"r2": 0.8}, "eval_std": {"r2": 0.05}, "folds": []},
            }
        )
        self.assertIn("- 3 folds (regression); aggregate:", rendered)
        self.assertIn("- r2: 0.8 ± 0.05", rendered)
        self.assertNotIn("(disabled or failed)", rendered)

    def test_build_stats_theta_explicit_is_not_data_driven(self) -> None:
        """Sibling unit pins theta=None → data-driven; the explicit arm was untested."""
        manifest = {
            "run_id": "r",
            "experiment": {"name": "e"},
            "timings": {},
            "outcome": "succeeded",
            "acceptance": {"ok": True},
            "dataset": {"meta": {}},
            "metrics_scraped": {},
        }
        stats = ss.build_stats(manifest, kind="recurrence", train_summary={}, train_config={"theta": 0.25, "d": 8})
        self.assertEqual(stats["recurrence"]["theta"], {"value": 0.25, "note": "explicit"})
        rendered = ss.render_summary_md(stats)
        self.assertIn("theta: 0.25 (explicit)", rendered)
        self.assertNotIn("data-driven", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
