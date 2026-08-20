#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/soak_ledger.py`` (section 6 of the shared-session-memory plan).

``util/`` is outside every pre-commit Python hook's scope (flake8/bandit scope to
``scripts/`` + ``tests/``), so this suite IS the gate.

What this pins is not arithmetic -- it is the set of properties that let the soak
*falsify* the relocation bet instead of confirming it:

* **the ladder cannot be jumped by assertion.** ``area-systematic`` is derived
  from >=3 misses sharing an area and must never be a recordable class, or an
  author can declare the escalation they want.
* **a hazard miss escalates immediately**, without waiting for N=20. A hazard
  miss is a live defect, not a statistic to accumulate.
* **the denominator cannot be padded.** Out-of-scope rows (HEAD not descended
  from the start marker) never count toward the rate.
* **pointer defects do not flatter the architecture** -- they are excluded from
  the architectural rate *and* still surfaced, so a pile of broken pointers can
  never read as success.
* **union-merge duplicates do not double-count.** ~24 concurrent worktrees make
  duplicate lines a certainty, not an edge case (plan section 7.7).
* **the thresholds are the ones fixed in advance**, so the result cannot be
  rationalised after the fact.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "util" / "soak_ledger.py"

_spec = importlib.util.spec_from_file_location("soak_ledger", MODULE_PATH)
assert _spec and _spec.loader
sl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sl)


def row(
    session: str = "s1",
    seq: int = 1,
    outcome: str = "follow",
    miss_class: str | None = None,
    area: str | None = None,
    in_scope: bool = True,
    ts: str = "2026-08-20T00:00:00Z",
) -> dict:
    return {
        "ts": ts,
        "session": session,
        "seq": seq,
        "outcome": outcome,
        "fact": "f",
        "pointer": "docs/REFERENCE.md#x",
        "task": "t",
        "area": area,
        "miss_class": miss_class,
        "in_scope": in_scope,
    }


def follows(n: int, start_session: int = 0) -> list[dict]:
    return [row(session=f"s{start_session + i}") for i in range(n)]


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MODULE_PATH), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )


class LadderIntegrity(unittest.TestCase):
    """The escalation ladder must be derived, never asserted."""

    def test_area_systematic_is_not_recordable(self) -> None:
        # If this ever becomes a recordable class, an author can declare the
        # escalation they want instead of earning it with three observations.
        self.assertNotIn("area-systematic", sl.MISS_CLASSES)

    def test_recordable_classes_are_exactly_the_three(self) -> None:
        self.assertEqual(
            sorted(sl.MISS_CLASSES),
            ["discoverability", "hazard", "pointer-defect"],
        )

    def test_area_systematic_is_derived_at_threshold(self) -> None:
        rows = follows(30)
        rows += [
            row(session="m1", seq=1, outcome="miss", miss_class="discoverability", area="publish"),
            row(session="m2", seq=1, outcome="miss", miss_class="discoverability", area="publish"),
        ]
        self.assertEqual(sl.analyse(rows)["systematic_areas"], [])

        rows.append(row(session="m3", seq=1, outcome="miss", miss_class="discoverability", area="publish"))
        stats = sl.analyse(rows)
        self.assertEqual(stats["systematic_areas"], ["publish"])
        self.assertEqual(stats["verdict"], "ESCALATE-AREA")
        self.assertEqual(stats["ladder_step"], 3)

    def test_threshold_constant_is_three(self) -> None:
        self.assertEqual(sl.AREA_SYSTEMATIC_THRESHOLD, 3)


class HazardEscalatesImmediately(unittest.TestCase):
    def test_single_hazard_miss_escalates_below_target_n(self) -> None:
        rows = [row(session="s1"), row(session="s2", outcome="miss", miss_class="hazard")]
        stats = sl.analyse(rows)
        self.assertLess(stats["sessions"], sl.TARGET_SESSIONS)
        self.assertEqual(stats["verdict"], "ESCALATE-HAZARD")
        self.assertEqual(stats["ladder_step"], 2)

    def test_hazard_outranks_an_otherwise_passing_rate(self) -> None:
        rows = follows(50)
        rows.append(row(session="hz", outcome="miss", miss_class="hazard"))
        stats = sl.analyse(rows)
        self.assertGreater(stats["follow_rate"], sl.RATE_BET_HOLDS)
        self.assertEqual(stats["verdict"], "ESCALATE-HAZARD")


class ScopeGate(unittest.TestCase):
    def test_out_of_scope_rows_do_not_count(self) -> None:
        rows = follows(5) + [row(session="old1", outcome="miss", miss_class="discoverability", in_scope=False)]
        stats = sl.analyse(rows)
        self.assertEqual(stats["occasions"], 5)
        self.assertEqual(stats["out_of_scope"], 1)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["follow_rate"], 1.0)

    def test_start_marker_is_the_post_p3_commit(self) -> None:
        self.assertEqual(sl.START_MARKER, "500508b")


class PointerDefects(unittest.TestCase):
    def test_excluded_from_architectural_rate_but_reported(self) -> None:
        rows = follows(9)
        rows.append(row(session="pd", outcome="miss", miss_class="pointer-defect"))
        stats = sl.analyse(rows)
        # 9 follows, 0 architectural misses -> the architecture scores 100%...
        self.assertEqual(stats["follow_rate"], 1.0)
        self.assertEqual(stats["misses"], 0)
        # ...but the defect is still visible, so it cannot be quietly buried.
        self.assertEqual(stats["pointer_defects"], 1)

    def test_pointer_defect_never_triggers_area_escalation(self) -> None:
        rows = follows(20) + [row(session=f"pd{i}", outcome="miss", miss_class="pointer-defect", area="publish") for i in range(4)]
        self.assertEqual(sl.analyse(rows)["systematic_areas"], [])


class UnionMergeSafety(unittest.TestCase):
    def test_duplicate_lines_are_deduped_by_session_and_seq(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "l.jsonl"
            line = json.dumps(row(session="s1", seq=1))
            ledger.write_text(f"{line}\n{line}\n{line}\n", encoding="utf-8")
            self.assertEqual(len(sl.load_rows(ledger)), 1)

    def test_distinct_seqs_from_same_session_both_survive(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "l.jsonl"
            a = json.dumps(row(session="s1", seq=1))
            b = json.dumps(row(session="s1", seq=2))
            ledger.write_text(f"{a}\n{b}\n{a}\n", encoding="utf-8")
            self.assertEqual(len(sl.load_rows(ledger)), 2)

    def test_unparseable_line_is_skipped_not_fatal(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "l.jsonl"
            good = json.dumps(row(session="s1", seq=1))
            ledger.write_text(f"{good}\n<<<<<<< HEAD\nnot json\n", encoding="utf-8")
            self.assertEqual(len(sl.load_rows(ledger)), 1)

    def test_missing_ledger_is_empty_not_an_error(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(sl.load_rows(Path(tmp) / "absent.jsonl"), [])

    def test_next_seq_is_per_session(self) -> None:
        rows = [row(session="a", seq=1), row(session="a", seq=2), row(session="b", seq=1)]
        self.assertEqual(sl.next_seq(rows, "a"), 3)
        self.assertEqual(sl.next_seq(rows, "b"), 2)
        self.assertEqual(sl.next_seq(rows, "new"), 1)


class Thresholds(unittest.TestCase):
    """The numbers fixed in advance, so the result cannot be rationalised."""

    def test_constants(self) -> None:
        self.assertEqual(sl.TARGET_SESSIONS, 20)
        self.assertEqual(sl.RATE_BET_HOLDS, 0.90)
        self.assertEqual(sl.RATE_BET_FAILING, 0.70)

    def test_below_target_n_is_in_progress_even_at_a_bad_rate(self) -> None:
        rows = [row(session="s1")] + [row(session=f"m{i}", outcome="miss", miss_class="discoverability") for i in range(5)]
        stats = sl.analyse(rows)
        self.assertLess(stats["follow_rate"], sl.RATE_BET_FAILING)
        self.assertEqual(stats["verdict"], "IN-PROGRESS")
        self.assertEqual(stats["ladder_step"], 0)

    def test_bet_holds_at_or_above_ninety(self) -> None:
        rows = follows(27) + [row(session=f"m{i}", outcome="miss", miss_class="discoverability") for i in range(3)]
        stats = sl.analyse(rows)
        self.assertEqual(stats["follow_rate"], 0.9)
        self.assertEqual(stats["verdict"], "BET-HOLDS")
        self.assertEqual(stats["ladder_step"], 0)

    def test_ladder_one_between_seventy_and_ninety(self) -> None:
        rows = follows(24) + [row(session=f"m{i}", outcome="miss", miss_class="discoverability") for i in range(6)]
        stats = sl.analyse(rows)
        self.assertEqual(stats["follow_rate"], 0.8)
        self.assertEqual(stats["verdict"], "LADDER-1")
        self.assertEqual(stats["ladder_step"], 1)

    def test_bet_failing_below_seventy(self) -> None:
        rows = follows(18) + [row(session=f"m{i}", outcome="miss", miss_class="discoverability") for i in range(12)]
        stats = sl.analyse(rows)
        self.assertEqual(stats["follow_rate"], 0.6)
        self.assertEqual(stats["verdict"], "BET-FAILING")

    def test_sessions_counts_distinct_sessions_not_occasions(self) -> None:
        # One session producing 30 occasions is NOT 30 sessions. Without this
        # the plan's "N >= 20 sessions" is satisfiable from a single session.
        rows = [row(session="s1", seq=i) for i in range(1, 31)]
        stats = sl.analyse(rows)
        self.assertEqual(stats["occasions"], 30)
        self.assertEqual(stats["sessions"], 1)
        self.assertEqual(stats["verdict"], "IN-PROGRESS")


class EmptyLedger(unittest.TestCase):
    def test_analyse_of_nothing_is_in_progress_with_no_rate(self) -> None:
        stats = sl.analyse([])
        self.assertIsNone(stats["follow_rate"])
        self.assertEqual(stats["verdict"], "IN-PROGRESS")
        self.assertEqual(stats["ladder_step"], 0)

    def test_markdown_render_of_nothing_does_not_crash(self) -> None:
        out = sl._render_markdown([], sl.analyse([]))
        self.assertIn("no observations recorded yet", out)


class RecordValidation(unittest.TestCase):
    """Negative controls: the ways a record could be recorded meaninglessly."""

    def test_miss_without_class_is_rejected(self) -> None:
        r = run_cli("record", "--outcome", "miss", "--fact", "f", "--pointer", "p", "--task", "t", "--dry-run")
        self.assertEqual(r.returncode, 2)
        self.assertIn("requires --class", r.stderr)

    def test_follow_with_class_is_rejected(self) -> None:
        r = run_cli("record", "--outcome", "follow", "--fact", "f", "--pointer", "p", "--task", "t", "--class", "hazard", "--dry-run")
        self.assertEqual(r.returncode, 2)

    def test_area_systematic_is_rejected_at_the_cli(self) -> None:
        r = run_cli("record", "--outcome", "miss", "--fact", "f", "--pointer", "p", "--task", "t", "--class", "area-systematic", "--dry-run")
        self.assertNotEqual(r.returncode, 0)

    def test_unknown_outcome_is_rejected(self) -> None:
        r = run_cli("record", "--outcome", "maybe", "--fact", "f", "--pointer", "p", "--task", "t", "--dry-run")
        self.assertNotEqual(r.returncode, 0)

    def test_dry_run_writes_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "l.jsonl"
            r = run_cli("--ledger", str(ledger), "record", "--outcome", "follow", "--fact", "f", "--pointer", "p", "--task", "t", "--dry-run")
            self.assertEqual(r.returncode, 0)
            self.assertFalse(ledger.exists())

    def test_record_appends_and_is_readable(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "sub" / "l.jsonl"
            for _ in range(2):
                r = run_cli("--ledger", str(ledger), "record", "--outcome", "follow", "--fact", "f", "--pointer", "p", "--task", "t", "--session", "fixed")
                self.assertEqual(r.returncode, 0, r.stderr)
            rows = sl.load_rows(ledger)
            self.assertEqual([x["seq"] for x in rows], [1, 2])


class StatusExitCodes(unittest.TestCase):
    """A gate that cannot fail is not a gate."""

    def _status(self, rows: list[dict]) -> subprocess.CompletedProcess:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "l.jsonl"
            ledger.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
            return run_cli("--ledger", str(ledger), "status")

    def test_in_progress_exits_zero(self) -> None:
        self.assertEqual(self._status(follows(3)).returncode, 0)

    def test_bet_holds_exits_zero(self) -> None:
        rows = follows(27) + [row(session=f"m{i}", outcome="miss", miss_class="discoverability") for i in range(3)]
        self.assertEqual(self._status(rows).returncode, 0)

    def test_hazard_exits_one(self) -> None:
        rows = [row(session="s1"), row(session="hz", outcome="miss", miss_class="hazard")]
        r = self._status(rows)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ladder 2", r.stdout)

    def test_ladder_one_exits_one(self) -> None:
        rows = follows(24) + [row(session=f"m{i}", outcome="miss", miss_class="discoverability") for i in range(6)]
        r = self._status(rows)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ladder 1", r.stdout)

    def test_never_re_inline_is_stated_on_escalation(self) -> None:
        # The plan's one absolute rule. If the escalation advice ever stops
        # saying it, the ladder's cheapest wrong turn goes unmarked.
        rows = [row(session="s1"), row(session="hz", outcome="miss", miss_class="hazard")]
        self.assertIn("NEVER re-inline", self._status(rows).stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
