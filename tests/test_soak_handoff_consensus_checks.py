#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for ``util/ad-hoc/2026-09-04_soak_handoff_consensus_checks.py``.

The consensus validation of the 2026-09-04 per-probe handoff (ml#1694) exists
because a reducer that SILENTLY NO-OPS still prints a clean, plausible report.
Two independent bugs did that in review:

* keying invalidate/rescore records on their own ``obs_id`` instead of
  ``invalidates`` / ``rescores`` (49 valid / 67.3% retention instead of 43 / 95.3%);
* matching only the hyphenated retrieval marker (2 follows instead of 8).

``util/`` is outside every pre-commit Python hook, so this suite is the gate.
Hermetic: synthetic JSONL only. The live ledger is a moving corpus and is not
read.

A test must be able to fail for the reason it exists. Each pin below is the
case that would have certified the wrong number.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-09-04_soak_handoff_consensus_checks.py"
LEDGER = REPO_ROOT / "util" / "soak_ledger.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = _load(SCRIPT, "soak_handoff_consensus_checks")
sl = _load(LEDGER, "soak_ledger")


def obs(obs_id: str, *, outcome: str = "follow", ts: str = "2026-08-30T00:00:00Z", note: str = "") -> dict:
    return {
        "obs_id": obs_id,
        "kind": "observation",
        "ts": ts,
        "outcome": outcome,
        "note": note,
    }


def invalidate(target: str, own_id: str = "inv-1") -> dict:
    return {"obs_id": own_id, "kind": "invalidate", "invalidates": target, "reason": "defective"}


def rescore(target: str, to_outcome: str = "source-recovered", own_id: str = "rs-1") -> dict:
    return {
        "obs_id": own_id,
        "kind": "rescore",
        "rescores": target,
        "from_outcome": "miss",
        "to_outcome": to_outcome,
        "reason": "from source",
    }


def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


class MutationKeying(unittest.TestCase):
    """Key the TARGET fields. Keying the mutation's own obs_id is a silent no-op."""

    def test_invalidate_drops_the_named_observation_not_the_mutation(self) -> None:
        rows = [obs("T", outcome="miss"), obs("KEEP"), invalidate("T", own_id="M")]
        _obs, invalidated, _rescored, valid = mod.reduce_ledger(rows)
        self.assertEqual(invalidated, {"T"})
        self.assertNotIn("T", valid)
        self.assertIn("KEEP", valid)
        self.assertEqual(len(_obs), 2)

    def test_keying_on_the_mutation_obs_id_would_be_a_silent_noop(self) -> None:
        # THE pin. Mutation obs_id is never an observation id, so a set of
        # mutation obs_ids never intersects the observation map. The reducer
        # still prints "N valid" and a retention. This is the 49-vs-43 class.
        rows = [obs("T", outcome="miss"), invalidate("T", own_id="M")]
        _obs, invalidated, _rescored, valid = mod.reduce_ledger(rows)
        self.assertNotIn("T", valid)
        wrong = {r["obs_id"] for r in rows if r["kind"] == "invalidate"}
        self.assertEqual(wrong, {"M"})
        self.assertNotIn("T", wrong)

    def test_rescore_applies_to_the_named_observation(self) -> None:
        rows = [obs("T", outcome="miss"), rescore("T", own_id="M")]
        _obs, _inv, rescored, valid = mod.reduce_ledger(rows)
        self.assertEqual(rescored["T"], "source-recovered")
        self.assertIn("T", valid)
        self.assertEqual(mod.outcome_now("T", valid["T"], rescored), "source-recovered")
        self.assertNotIn("M", rescored)

    def test_rescore_keyed_on_its_own_obs_id_would_not_move_the_target(self) -> None:
        rows = [obs("T", outcome="miss"), rescore("T", own_id="M")]
        _obs, _inv, rescored, valid = mod.reduce_ledger(rows)
        wrong = {r["obs_id"]: r["to_outcome"] for r in rows if r["kind"] == "rescore"}
        self.assertEqual(mod.outcome_now("T", valid["T"], wrong), "miss")
        self.assertEqual(mod.outcome_now("T", valid["T"], rescored), "source-recovered")


class DualLexicalForms(unittest.TestCase):
    """Both recorded spellings of the output-scored marker must count."""

    def test_both_lexical_forms_count_as_via_output(self) -> None:
        rows = [
            obs("H", note="reached via-search-output"),
            obs("P", note="RETRIEVED via search output"),
            obs("I", note="opened docs/REFERENCE.md#utility-script-reference"),
        ]
        _o, _i, rescored, valid = mod.reduce_ledger(rows)
        follows, via = mod.follows_and_via_output(valid, rescored)
        self.assertEqual(len(follows), 3)
        self.assertEqual(set(via), {"H", "P"})

    def test_hyphenated_only_match_undercounts_the_prose_form(self) -> None:
        # THE pin. Matching only 'via-search-output' certified 2 instead of 8
        # and made the two-standards finding look like noise.
        rows = [
            obs("H", note="reached via-search-output"),
            obs("P", note="RETRIEVED via search output"),
        ]
        _o, _i, rescored, valid = mod.reduce_ledger(rows)
        _follows, both = mod.follows_and_via_output(valid, rescored)
        _follows, hyphen_only = mod.follows_and_via_output(valid, rescored, markers=("via-search-output",))
        self.assertEqual(len(both), 2)
        self.assertEqual(len(hyphen_only), 1)
        self.assertEqual(hyphen_only, ["H"])

    def test_missing_note_is_input_scored_not_a_crash(self) -> None:
        row = obs("X")
        del row["note"]
        _o, _i, rescored, valid = mod.reduce_ledger([row])
        follows, via = mod.follows_and_via_output(valid, rescored)
        self.assertEqual(len(follows), 1)
        self.assertEqual(via, [])


class OneWayRescore(unittest.TestCase):
    """A source-recovered rescore raises retention and must not shrink n."""

    def test_rescore_raises_retention_and_keeps_the_denominator(self) -> None:
        rows = [
            obs("F1", outcome="follow"),
            obs("F2", outcome="follow"),
            obs("M1", outcome="miss"),
            obs("M2", outcome="miss"),
            rescore("M1"),
        ]
        _o, _i, rescored, valid = mod.reduce_ledger(rows)
        _before, _after, ret_before, ret_after, n = mod.retention_pair(valid, rescored)
        self.assertEqual(n, 4)
        self.assertAlmostEqual(ret_before, 0.5)
        self.assertAlmostEqual(ret_after, 0.75)
        self.assertGreater(ret_after, ret_before)

    def test_rescore_does_not_invent_a_follow(self) -> None:
        rows = [obs("M", outcome="miss"), rescore("M")]
        _o, _i, rescored, valid = mod.reduce_ledger(rows)
        self.assertEqual(mod.outcome_now("M", valid["M"], rescored), "source-recovered")
        follows, _via = mod.follows_and_via_output(valid, rescored)
        self.assertEqual(follows, [])


class InterventionSplit(unittest.TestCase):
    """Sec 15.4: analyse() has no filter; this reducer must honour the cutoff."""

    def test_on_cutoff_row_is_post_not_pre(self) -> None:
        # Exact cutoff string, not an ISO datetime. "2026-08-31T00:00:00Z" is
        # already > "2026-08-31", so a `<` vs `<=` swap would not move it --
        # the exact token is the only input that makes the predicate bite.
        rows = [
            obs("PRE", ts="2026-08-30T23:59:59Z"),
            obs("ON", ts=mod.INTERVENTION_CUTOFF),
            obs("ISO", ts="2026-08-31T00:00:00Z"),
            obs("POST", ts="2026-09-01T00:00:00Z"),
        ]
        _o, _i, _r, valid = mod.reduce_ledger(rows)
        pre, post = mod.split_at_intervention(valid)
        self.assertEqual(set(pre), {"PRE"})
        self.assertEqual(set(post), {"ON", "ISO", "POST"})

    def test_empty_side_is_empty_not_a_crash(self) -> None:
        rows = [obs("ONLY", ts="2026-08-01T00:00:00Z")]
        _o, _i, _r, valid = mod.reduce_ledger(rows)
        pre, post = mod.split_at_intervention(valid)
        self.assertEqual(set(pre), {"ONLY"})
        self.assertEqual(post, {})

    def test_effective_outcome_is_used_in_the_split_follow_count(self) -> None:
        rows = [
            obs("A", outcome="miss", ts="2026-08-30T00:00:00Z"),
            rescore("A"),
        ]
        _o, _i, rescored, valid = mod.reduce_ledger(rows)
        pre, _post = mod.split_at_intervention(valid)
        self.assertEqual(mod.follow_count(pre, rescored), 0)
        self.assertEqual(mod.outcome_now("A", valid["A"], rescored), "source-recovered")


class WilsonIsTheLedgersEstimator(unittest.TestCase):
    """The operational boundary that turns main's Regression Tests red."""

    def test_load_wilson_matches_soak_ledger_wilson(self) -> None:
        # Fresh importlib load -- identity is not the contract; the numbers are.
        w = mod.load_wilson()
        for k, n in ((26, 43), (26, 40), (0, 0), (20, 20)):
            self.assertEqual(w(k, n), sl.wilson(k, n), (k, n))

    def test_twenty_six_of_forty_three_is_terminal(self) -> None:
        # +3 non-follow rows on main's 26/40. Wilson upper 0.7363 < 0.75.
        lo, hi = sl.wilson(26, 43)
        self.assertAlmostEqual(hi, 0.736, places=3)
        self.assertTrue(mod.is_terminal_bet_failing(hi))
        self.assertGreaterEqual(lo, 0.0)

    def test_twenty_six_of_forty_is_not_terminal(self) -> None:
        _lo, hi = sl.wilson(26, 40)
        self.assertAlmostEqual(hi, 0.779, places=3)
        self.assertFalse(mod.is_terminal_bet_failing(hi))

    def test_twenty_six_of_forty_two_sits_on_the_boundary_and_is_not_terminal(self) -> None:
        # +2 non-follow: upper 0.750003. Strict < 0.75, so this must NOT fire.
        _lo, hi = sl.wilson(26, 42)
        self.assertGreaterEqual(hi, 0.750)
        self.assertFalse(mod.is_terminal_bet_failing(hi))

    def test_none_upper_is_not_terminal(self) -> None:
        self.assertFalse(mod.is_terminal_bet_failing(None))

    def test_exact_boundary_is_not_terminal(self) -> None:
        # Strict <. `<= 0.750` would fire at the boundary and at 26/42 (0.750003
        # still would not -- that case is the operational number, this is the
        # predicate).
        self.assertFalse(mod.is_terminal_bet_failing(0.750))
        self.assertTrue(mod.is_terminal_bet_failing(0.749999))


class CliContract(unittest.TestCase):
    def test_missing_argv_exits_two(self) -> None:
        r = cli()
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage:", r.stderr)

    def test_synthetic_ledger_prints_the_reducer_counts(self) -> None:
        rows = [
            obs("F", outcome="follow", ts="2026-08-30T00:00:00Z", note="via-search-output"),
            obs("M", outcome="miss", ts="2026-09-01T00:00:00Z"),
            obs("D", outcome="miss", ts="2026-08-30T00:00:00Z"),
            invalidate("D", own_id="INV"),
            rescore("M", own_id="RS"),
        ]
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "l.jsonl"
            p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
            r = cli(str(p))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("5 records -> 3 observations, 1 invalidated, 1 rescored -> 2 valid", r.stdout)
        self.assertIn("follows scored on tool OUTPUT ('via-search-output'): 1", r.stdout)
        self.assertIn("PRE ", r.stdout)
        self.assertIn("POST", r.stdout)
        self.assertNotIn("NO ROWS", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
