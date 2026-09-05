#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Complementary leftover of ``tests/test_soak_ledger.py``, ml#1728, ml#1725,
ml#1699 and ml#1700.

``analyse()`` has no date filter. ml#1728 now makes ``pick_next`` ignore
pre-intervention rows; ml#1725 pins that the spend-control token is
``analyse()["verdict"]``. Together that means the picker and the stopper
read different corpora: a pre-intervention pile can arm BET-FAILING and
refuse billed sessions even when the post-intervention side is still
IN-PROGRESS. That is consensus finding #3 of
``notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md``
— the forbidden pooled method — and none of those suites can see it.

``tests/test_soak_ledger.py`` builds synthetic rows with a single hard-coded
``ts`` and never asks whether a date split would change the verdict.
ml#1699 pins the *ad-hoc* reducer's split; ml#1700 pins Wilson power at an
observed rate. This suite drives the production reducer.

Hermetic: synthetic rows only. Never launches ``claude``. Never reads the
live ledger.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import unittest
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "util" / "soak_ledger.py"

_spec = importlib.util.spec_from_file_location("soak_ledger", MODULE_PATH)
assert _spec and _spec.loader
sl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sl)

CUTOFF = "2026-08-31"
PRE_TS = "2026-08-30T12:00:00Z"
POST_TS = "2026-09-01T12:00:00Z"
ON_CUTOFF_TS = "2026-08-31T00:00:00Z"


def obs(**kw) -> dict:
    d = {
        "obs_id": str(uuid.uuid4()),
        "kind": "observation",
        "ts": PRE_TS,
        "in_scope": True,
        "arm": "seeded",
        "severity": "operational",
        "area": "publish",
        "probe_id": "P01",
        "session": "s1",
        "outcome": "follow",
    }
    d.update(kw)
    return d


def seeded_dated(n_follow: int, n_miss: int, ts: str, probes: int = 15) -> list[dict]:
    rows, i = [], 0
    for k in range(n_follow):
        rows.append(
            obs(
                session=f"{ts}-f{i}",
                probe_id=f"P{i % probes:02d}",
                outcome="follow",
                ts=ts,
                severity="hazard" if k % 3 == 0 else "operational",
            )
        )
        i += 1
    for k in range(n_miss):
        rows.append(
            obs(
                session=f"{ts}-m{i}",
                probe_id=f"P{i % probes:02d}",
                outcome="miss",
                miss_class="discoverability",
                ts=ts,
                area=["publish", "docs-ci", "experiments", "worktrees"][k % 4],
            )
        )
        i += 1
    return rows


def post_only(rows: list[dict]) -> list[dict]:
    """The filter pick_next applies and analyse() does not."""
    return [r for r in rows if (r.get("ts") or "") >= CUTOFF]


def write(tmp: Path, rows: list[dict]) -> Path:
    p = tmp / "l.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


def status_cli(ledger: Path) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603
        [sys.executable, str(MODULE_PATH), "--ledger", str(ledger), "status"],
        capture_output=True,
        text=True,
        timeout=30,
    )


class AnalyseHasNoDateFilter(unittest.TestCase):
    """The API itself cannot honour §15.4; there is no knob to pass."""

    def test_analyse_takes_only_rows_and_bad_lines(self) -> None:
        params = inspect.signature(sl.analyse).parameters
        self.assertEqual(list(params), ["rows", "bad_lines"])
        for forbidden in ("since", "until", "after", "split", "cutoff", "ts"):
            self.assertNotIn(forbidden, params)


class PreAndPostAreIndividuallyNotThePooledVerdict(unittest.TestCase):
    """Consensus §4.3 / §4.6: 24/35 is not terminal; 26/43 is; n=8 is not
    even eligible. The spend-control token is the pooled one."""

    def test_pre_24_of_35_is_inconclusive(self) -> None:
        pre = seeded_dated(24, 11, PRE_TS)
        st = sl.analyse(pre)
        self.assertEqual(st["seeded"]["follows"], 24)
        self.assertEqual(st["seeded"]["denom"], 35)
        self.assertGreaterEqual(st["seeded"]["ci_high"], sl.DECISION_BOUNDARY)
        self.assertEqual(st["verdict"], "INCONCLUSIVE")

    def test_post_only_2_of_8_is_in_progress(self) -> None:
        post = seeded_dated(2, 6, POST_TS)
        st = sl.analyse(post)
        self.assertEqual(st["seeded"]["denom"], 8)
        self.assertLess(st["seeded"]["runs"], sl.TARGET_PROBE_RUNS)
        self.assertEqual(st["verdict"], "IN-PROGRESS")

    def test_pooled_26_of_43_is_bet_failing(self) -> None:
        rows = seeded_dated(24, 11, PRE_TS) + seeded_dated(2, 6, POST_TS)
        st = sl.analyse(rows)
        self.assertEqual(st["seeded"]["follows"], 26)
        self.assertEqual(st["seeded"]["denom"], 43)
        self.assertLess(st["seeded"]["ci_high"], sl.DECISION_BOUNDARY)
        self.assertEqual(st["verdict"], "BET-FAILING")

    def test_neither_side_is_the_pooled_verdict(self) -> None:
        pre = seeded_dated(24, 11, PRE_TS)
        post = seeded_dated(2, 6, POST_TS)
        self.assertEqual(sl.analyse(pre)["verdict"], "INCONCLUSIVE")
        self.assertEqual(sl.analyse(post)["verdict"], "IN-PROGRESS")
        self.assertEqual(sl.analyse(pre + post)["verdict"], "BET-FAILING")

    def test_caller_side_date_filter_yields_a_different_verdict(self) -> None:
        rows = seeded_dated(24, 11, PRE_TS) + seeded_dated(2, 6, POST_TS)
        self.assertEqual(sl.analyse(rows)["verdict"], "BET-FAILING")
        self.assertEqual(sl.analyse(post_only(rows))["verdict"], "IN-PROGRESS")

    def test_three_fewer_post_misses_keep_the_pool_inconclusive(self) -> None:
        # Consensus §4.3: 26/40 and 26/42 are not terminal; 26/43 is.
        # The spend-control flips on the extra non-follows, not on the date.
        rows_40 = seeded_dated(24, 11, PRE_TS) + seeded_dated(2, 3, POST_TS)
        st = sl.analyse(rows_40)
        self.assertEqual(st["seeded"]["follows"], 26)
        self.assertEqual(st["seeded"]["denom"], 40)
        self.assertGreaterEqual(st["seeded"]["ci_high"], sl.DECISION_BOUNDARY)
        self.assertEqual(st["verdict"], "INCONCLUSIVE")


class AnalyseCountsRowsThePickerWouldDrop(unittest.TestCase):
    """pick_next's post_intervention() drops these; analyse() still scores them."""

    def test_pre_intervention_rows_stay_in_the_denominator(self) -> None:
        pre_miss = seeded_dated(0, 1, PRE_TS)
        post = seeded_dated(24, 10, POST_TS)
        st = sl.analyse(pre_miss + post)
        self.assertEqual(st["seeded"]["denom"], 35)
        self.assertEqual(st["seeded"]["misses"], 11)

    def test_on_cutoff_row_is_counted(self) -> None:
        # No filter means the cutoff token is just another row. The picker
        # treats it as POST; analyse treats it as data. Either way it counts.
        rows = seeded_dated(24, 10, PRE_TS) + seeded_dated(0, 1, ON_CUTOFF_TS)
        st = sl.analyse(rows)
        self.assertEqual(st["seeded"]["denom"], 35)
        self.assertEqual(st["seeded"]["misses"], 11)

    def test_empty_and_missing_ts_still_count(self) -> None:
        base = seeded_dated(24, 10, PRE_TS)
        empty = obs(session="empty-ts", probe_id="P00", outcome="miss", miss_class="discoverability", ts="")
        missing = obs(session="no-ts", probe_id="P01", outcome="miss", miss_class="discoverability")
        del missing["ts"]
        st = sl.analyse(base + [empty, missing])
        self.assertEqual(st["seeded"]["denom"], 36)
        self.assertEqual(st["seeded"]["misses"], 12)

    def test_organic_post_rows_do_not_change_the_seeded_verdict(self) -> None:
        pre = seeded_dated(24, 11, PRE_TS)
        organic = [
            obs(session=f"org{i}", arm="organic", outcome="follow", ts=POST_TS, probe_id=f"P{i:02d}")
            for i in range(20)
        ]
        self.assertEqual(sl.analyse(pre)["verdict"], sl.analyse(pre + organic)["verdict"])
        self.assertEqual(sl.analyse(pre + organic)["organic"]["follows"], 20)


class SpendControlTokenIsThePooledVerdict(unittest.TestCase):
    """soak_run_probe.py reads status's first token. That token is the pool."""

    def test_status_first_token_is_pooled_bet_failing(self) -> None:
        rows = seeded_dated(24, 11, PRE_TS) + seeded_dated(2, 6, POST_TS)
        with TemporaryDirectory() as tmp:
            ledger = write(Path(tmp), rows)
            r = status_cli(ledger)
        token = (r.stdout.split() or [""])[0]
        self.assertEqual(token, "BET-FAILING")
        self.assertEqual(r.returncode, 1)

    def test_status_first_token_on_post_only_is_in_progress(self) -> None:
        rows = seeded_dated(2, 6, POST_TS)
        with TemporaryDirectory() as tmp:
            ledger = write(Path(tmp), rows)
            r = status_cli(ledger)
        token = (r.stdout.split() or [""])[0]
        self.assertEqual(token, "IN-PROGRESS")
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
