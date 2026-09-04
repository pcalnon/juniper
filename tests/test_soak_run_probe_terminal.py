#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for the BET-FAILING / HOLDS-AT- stopping rule in ``util/soak_run_probe.py``.

``util/`` is outside every pre-commit Python hook, so this suite is the only
check on the rule. Complementary to ``tests/test_soak_run_probe.py`` (retrieval
channel + parse_events) -- do not fold these into that file.

Hermetic: ``_py`` is patched so nothing consults the live ledger or launches
``claude``. A test that read the real ``pointer_follow_soak.jsonl`` would flip
when the corpus moved, which is the opposite of a regression pin.

Why this suite exists
---------------------
The unattended timer is the only spend-control in the dispatch path. The rule
fired live on 2026-09-04 (``REFUSING: soak verdict is BET-FAILING -- terminal``)
and blocked per-probe characterisation. Existing dry-run tests never inject a
terminal verdict, so a prefix-match regression stays green:

* too narrow (``== "BET-FAILING"`` and drop ``HOLDS-AT-``) spends sessions
  after a hold that cannot change the conclusion;
* too wide (``startswith("BET-")``) refuses ``BET-HOLDING`` / any future
  non-terminal BET-* token;
* first-token slip (search the whole status line) refuses an IN-PROGRESS
  report that merely *mentions* BET-FAILING in its note.

A test must be able to fail for the reason it exists.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stderr
from types import SimpleNamespace
from unittest.mock import patch

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "soak_run_probe.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("soak_run_probe_terminal", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = load_mod()

# Realistic ``soak_ledger.py status`` first line (cmd_status). The note is
# allowed to mention other verdict names -- only the first token is the verdict.
_FAILING_LINE = (
    "BET-FAILING  seeded=43/50 rate=60.5% ci=[0.456, 0.736] "
    "escalations=0  (upper bound below the boundary)"
)
_HOLDS_LINE = (
    "HOLDS-AT-0.75  seeded=50/50 rate=82.0% ci=[0.760, 0.880] "
    "escalations=0  (lower bound at or above the boundary)"
)
_PROGRESS_LINE = (
    "IN-PROGRESS  seeded=10/50 rate=n/a ci=n/a escalations=0  "
    "(10/50 runs; a later BET-FAILING mention must not trip the guard)"
)


def _run_main(argv: list[str], status_stdout: str, *, dispatch_ok: bool = True) -> tuple[int, str, int]:
    """Invoke ``main()`` with a fake ledger status. Returns (rc, stderr, dispatch_calls)."""
    dispatched = {"n": 0}

    def fake_dispatch(probe_id: str | None) -> tuple[str, str]:
        dispatched["n"] += 1
        return ("P99-test", "synthetic task that must never reach production")

    def fake_py(*args: str, **_kwargs: object) -> SimpleNamespace:
        if args and args[-1] == "status":
            return SimpleNamespace(stdout=status_stdout, stderr="", returncode=0)
        raise AssertionError(f"unexpected _py call {args!r}")

    err = io.StringIO()
    with (
        patch.object(mod, "_py", side_effect=fake_py),
        patch.object(mod, "dispatch", side_effect=fake_dispatch if dispatch_ok else AssertionError("dispatch must not run")),
        patch.object(sys, "argv", ["soak_run_probe.py", *argv]),
        redirect_stderr(err),
    ):
        rc = mod.main()
    return rc, err.getvalue(), dispatched["n"]


class TerminalVerdictParsing(unittest.TestCase):
    """Pure function: first token + prefix match. No subprocess, no argv."""

    def test_bet_failing_alone_is_terminal(self) -> None:
        self.assertEqual(mod.terminal_verdict("BET-FAILING"), "BET-FAILING")

    def test_bet_failing_status_line_is_terminal(self) -> None:
        self.assertEqual(mod.terminal_verdict(_FAILING_LINE), "BET-FAILING")

    def test_holds_at_boundary_is_terminal(self) -> None:
        self.assertEqual(mod.terminal_verdict(_HOLDS_LINE), "HOLDS-AT-0.75")

    def test_holds_at_prefix_without_digits_is_still_terminal(self) -> None:
        # startswith("HOLDS-AT-") -- a renamed boundary must still refuse.
        self.assertEqual(mod.terminal_verdict("HOLDS-AT-0.80  seeded=50/50"), "HOLDS-AT-0.80")

    def test_in_progress_is_not_terminal(self) -> None:
        self.assertIsNone(mod.terminal_verdict(_PROGRESS_LINE))

    def test_data_integrity_verdicts_are_not_terminal_spends(self) -> None:
        # NO-DATA / DEGRADED / NO-SEEDED-DATA are ledger problems, not a
        # finished bet. The timer must not treat them as "already answered".
        for token in ("NO-DATA", "DEGRADED", "NO-SEEDED-DATA", "INCONCLUSIVE"):
            self.assertIsNone(mod.terminal_verdict(token), token)

    def test_empty_and_whitespace_are_not_terminal(self) -> None:
        self.assertIsNone(mod.terminal_verdict(""))
        self.assertIsNone(mod.terminal_verdict("   \n"))

    def test_leading_whitespace_does_not_hide_a_terminal_verdict(self) -> None:
        # str.split() is load-bearing: lstrip-then-split would also work, but
        # indexing [0] on a raw line would miss the verdict.
        self.assertEqual(mod.terminal_verdict("   BET-FAILING  seeded=1/50"), "BET-FAILING")

    def test_later_mention_of_bet_failing_does_not_trip(self) -> None:
        # THE first-token contract. Searching the whole line would refuse
        # characterisation the moment a note named the terminal state.
        self.assertIsNone(mod.terminal_verdict(_PROGRESS_LINE))
        self.assertIn("BET-FAILING", _PROGRESS_LINE)

    def test_bet_prefix_alone_is_not_terminal(self) -> None:
        # startswith("BET-") would refuse any future BET-* token.
        self.assertIsNone(mod.terminal_verdict("BET-HOLDING  seeded=20/50"))
        self.assertIsNone(mod.terminal_verdict("BET  seeded=20/50"))


class StoppingRuleCli(unittest.TestCase):
    """``main()`` consults the helper before dispatch, and --force is the override."""

    def test_bet_failing_refuses_and_does_not_dispatch(self) -> None:
        rc, err, n = _run_main(["--dry-run"], _FAILING_LINE, dispatch_ok=False)
        self.assertEqual(rc, 2)
        self.assertIn("REFUSING", err)
        self.assertIn("BET-FAILING", err)
        self.assertIn("terminal", err)
        self.assertEqual(n, 0)

    def test_holds_at_refuses(self) -> None:
        rc, err, n = _run_main(["--dry-run"], _HOLDS_LINE, dispatch_ok=False)
        self.assertEqual(rc, 2)
        self.assertIn("REFUSING", err)
        self.assertIn("HOLDS-AT-0.75", err)
        self.assertEqual(n, 0)

    def test_in_progress_reaches_dry_run(self) -> None:
        rc, err, n = _run_main(["--dry-run"], _PROGRESS_LINE)
        self.assertEqual(rc, 0)
        self.assertNotIn("REFUSING", err)
        self.assertGreaterEqual(n, 1)

    def test_force_overrides_terminal_verdict(self) -> None:
        rc, err, n = _run_main(["--dry-run", "--force"], _FAILING_LINE)
        self.assertEqual(rc, 0)
        self.assertNotIn("REFUSING", err)
        self.assertGreaterEqual(n, 1)

    def test_dry_run_does_not_bypass_the_guard(self) -> None:
        # Characterization of current order: the guard runs BEFORE the dry-run
        # branch. Dry-run spends no session, but a missing --force still
        # refuses. Pin so a silent reorder is a test break, not a surprise.
        rc, err, n = _run_main(["--dry-run"], _FAILING_LINE, dispatch_ok=False)
        self.assertEqual(rc, 2)
        self.assertIn("Pass --force", err)
        self.assertEqual(n, 0)


if __name__ == "__main__":
    unittest.main()
