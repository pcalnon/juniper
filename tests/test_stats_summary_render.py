#!/usr/bin/env python3
"""Hermetic leftover for ``util/experiments/stats_summary.py``'s ``summary.md`` renderer.

``StatsSummaryUnitTest`` in ``tests/test_run_experiment.py`` pins percentile math, advancing
step-duration deltas, correlation, ``_to_float``, sequence shapes, and degraded-notes. Its one
``render_summary_md`` call uses the pre-2026-09-01 ``present`` key and never asserts the grafana
line. ``MetricsScrapedTest`` pins ``_metrics_scraped()`` *collection*. A renderer that treats
``target_file_written`` as scraped, or collapses a present ``None`` into ``False``, stays green.

The property these pin is the #1550 honesty contract operators read: a target file written is
not a scrape confirmed. Five bridged PF-1 runs wrote the file and Prometheus held no series.
``scrape_confirmed`` is tri-state — ``None`` means the question could not be asked — and a
pre-2026-09-01 manifest without the key must render ``n/a``, which is a different branch from
a present ``None``.

``util/`` draws "(no files to check) Skipped" from every pre-commit Python hook, so this
unittest is the gate for the renderer. Do not fold these into ``tests/test_run_experiment.py``.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import stats_summary as ss  # noqa: E402  (path-invoked util import)

NA = "n/a (pre-2026-09-01 manifest)"


def _row(sum_: float, count: float) -> dict:
    return {ss.STEP_SUM_COLUMN: str(sum_), ss.STEP_COUNT_COLUMN: str(count)}


def _render(*, scraped=None, identity=None, dataset=None, cascor=None, recurrence=None) -> str:
    stats = {
        "identity": identity or {"run_id": "r-unit", "git": {}},
        "dataset": dataset or {},
        "outcome": {"outcome": "succeeded", "acceptance": {"ok": True}, "wall_seconds": 1.0, "timings": {}},
        "provenance": {"metrics_scraped": scraped if scraped is not None else {}},
    }
    if cascor is not None:
        stats["cascor"] = cascor
    if recurrence is not None:
        stats["recurrence"] = recurrence
    return ss.render_summary_md(stats)


def _grafana_line(rendered: str) -> str:
    for line in rendered.splitlines():
        if line.startswith("- grafana bridge:"):
            return line
    raise AssertionError(f"no grafana-bridge line in:\n{rendered}")


def _manifest(**overrides):
    base = {
        "run_id": "r-unit",
        "experiment": {"name": "e", "description": None},
        "config_sha256": "x",
        "seeds": {"experiment": 1},
        "git": {},
        "packages": {},
        "timings": {"total": 1.0},
        "outcome": "succeeded",
        "acceptance": {"ok": True, "reasons": []},
        "metrics_scraped": {},
        "dataset": {
            "dataset_id": "d",
            "generator": "spiral",
            "version": "1",
            "split": "train",
            "params": {},
            "meta": {},
        },
    }
    base.update(overrides)
    return base


class ScrapeHonestyRenderTest(unittest.TestCase):
    """The #1550 line operators read. Collection is already gated; this is the render."""

    def test_both_facts_true_are_reported_separately(self) -> None:
        line = _grafana_line(_render(scraped={"grafana_bridge": True, "target_file_written": True, "scrape_confirmed": True}))
        self.assertEqual(line, "- grafana bridge: True, target file written: True, scrape confirmed: True")

    def test_written_true_confirmed_false_is_the_1550_lie(self) -> None:
        """Five PF-1 runs wrote the target file and Prometheus held no series."""
        line = _grafana_line(_render(scraped={"grafana_bridge": True, "target_file_written": True, "scrape_confirmed": False}))
        self.assertIn("target file written: True", line)
        self.assertIn("scrape confirmed: False", line)
        self.assertNotIn(f"scrape confirmed: {NA}", line)

    def test_present_none_is_could_not_ask_not_false_or_na(self) -> None:
        """A present None is 'could not ask'. ``.get(key) or 'n/a'`` or ``or False`` both lie."""
        line = _grafana_line(_render(scraped={"grafana_bridge": True, "target_file_written": True, "scrape_confirmed": None}))
        self.assertIn("scrape confirmed: None", line)
        self.assertNotIn("scrape confirmed: False", line)
        self.assertNotIn(NA, line)

    def test_missing_key_is_pre_2026_09_01_na_and_present_is_the_written_fallback(self) -> None:
        line = _grafana_line(_render(scraped={"grafana_bridge": False, "present": False}))
        self.assertIn("target file written: False", line)
        self.assertIn(f"scrape confirmed: {NA}", line)
        self.assertNotIn("scrape confirmed: None", line)
        self.assertNotIn("scrape confirmed: False", line)

    def test_written_key_wins_over_present_fallback(self) -> None:
        line = _grafana_line(_render(scraped={"target_file_written": True, "present": False, "scrape_confirmed": False}))
        self.assertIn("target file written: True", line)
        self.assertNotIn("target file written: False", line)

    def test_reason_rider_is_a_sub_bullet(self) -> None:
        rendered = _render(scraped={"grafana_bridge": True, "target_file_written": True, "scrape_confirmed": None, "reason": "prometheus unreachable"})
        self.assertIn("  - prometheus unreachable", rendered.splitlines())

    def test_renaming_written_onto_confirmed_fails(self) -> None:
        """The two facts must stay two facts. A single boolean standing in for both is the lie."""
        line = _grafana_line(_render(scraped={"grafana_bridge": True, "target_file_written": True, "scrape_confirmed": False}))
        written_idx = line.index("target file written:")
        confirmed_idx = line.index("scrape confirmed:")
        self.assertLess(written_idx, confirmed_idx)
        self.assertEqual(line.count("True"), 2)  # bridge + written
        self.assertIn("scrape confirmed: False", line)


class StepDurationEdgeTest(unittest.TestCase):
    """``StatsSummaryUnitTest`` only advances the count. These two arms crash or lie if rewritten."""

    def test_zero_count_overall_mean_is_none_not_zerodivision(self) -> None:
        result = ss.step_duration_stats([_row(0.0, 0)])
        self.assertEqual(result["total_steps"], 0)
        self.assertIsNone(result["overall_mean_seconds"])
        self.assertEqual(result["poll_samples"], 0)

    def test_stalled_and_backwards_counts_are_not_samples(self) -> None:
        # 2 → 2 (stall) → 1 (backwards) → 4 (the only advance).
        result = ss.step_duration_stats([_row(2.0, 2), _row(2.0, 2), _row(1.0, 1), _row(10.0, 4)])
        self.assertEqual(result["poll_samples"], 1)
        self.assertEqual(result["total_steps"], 4)
        self.assertAlmostEqual(result["overall_mean_seconds"], 2.5)
        self.assertAlmostEqual(result["p50_seconds"], 3.0)  # (10-1)/(4-1)


class GitAndKindRenderTest(unittest.TestCase):
    def test_dirty_sha_is_truncated_and_flagged(self) -> None:
        sha = "abcdef0123456789" + "0" * 24
        stats = ss.build_stats(_manifest(git={"juniper-ml": {"head_sha": sha, "dirty": True}}), kind="cascor")
        rendered = ss.render_summary_md(stats)
        self.assertIn(f"- juniper-ml: `{sha[:12]}` (DIRTY — not reproducible)", rendered)
        self.assertNotIn(sha, rendered)  # full 40-char sha must not leak

    def test_git_without_head_sha_is_unavailable(self) -> None:
        stats = ss.build_stats(_manifest(git={"juniper-ml": {"error": "unreadable"}}), kind="cascor")
        self.assertEqual(stats["identity"]["git"]["juniper-ml"], {"error": "unreadable"})
        self.assertIn("- juniper-ml: (unavailable)", ss.render_summary_md(stats))

    def test_cascor_empty_per_round_and_completion_reason(self) -> None:
        stats = ss.build_stats(_manifest(completion_reason="hidden_units_cap"), kind="cascor", series_rows=[])
        rendered = ss.render_summary_md(stats)
        self.assertIn("## cascor", rendered)
        self.assertIn("(no samples)", rendered)
        self.assertIn("- completion reason: hidden_units_cap", rendered)

    def test_recurrence_crossval_present_vs_disabled(self) -> None:
        present = ss.build_stats(
            _manifest(),
            kind="recurrence",
            train_summary={"final_metrics": {"r2": 0.9}},
            train_config={"theta": None},
            crossval={"n_folds": 3, "task_type": "regression", "eval_aggregate": {"r2": 0.8}, "eval_std": {"r2": 0.05}, "folds": []},
        )
        rendered = ss.render_summary_md(present)
        self.assertIn("- 3 folds (regression); aggregate:", rendered)
        self.assertIn("  - r2: 0.8 ± 0.05", rendered)
        self.assertNotIn("(disabled or failed)", rendered)

        absent = ss.build_stats(_manifest(), kind="recurrence", train_summary={"final_metrics": {"r2": 0.9}}, train_config={"theta": None})
        self.assertIn("(disabled or failed)", ss.render_summary_md(absent))

    def test_theta_explicit_is_not_data_driven(self) -> None:
        stats = ss.build_stats(_manifest(), kind="recurrence", train_summary={}, train_config={"theta": 0.5})
        self.assertEqual(stats["recurrence"]["theta"], {"value": 0.5, "note": "explicit"})
        self.assertIn("theta: 0.5 (explicit)", ss.render_summary_md(stats))
        self.assertNotIn("data-driven", ss.render_summary_md(stats))

    def test_class_distribution_line_is_conditional(self) -> None:
        with_dist = _render(dataset={"shapes": {}, "class_distribution": {"0": 10, "1": 12}})
        self.assertIn("- class distribution: {'0': 10, '1': 12}", with_dist)
        without = _render(dataset={"shapes": {}})
        self.assertNotIn("class distribution", without)


if __name__ == "__main__":
    unittest.main()
