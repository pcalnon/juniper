#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Complementary gate for ``util/soak_run_probe.py``'s stopping rule.

``tests/test_soak_run_probe.py`` already pins the helper and a BET-FAILING
``--dry-run`` walk through ``main()``. Those members cannot see:

* a ``main()`` that always passes ``dry_run=True`` into the helper -- every
  existing test stays green and a real run keeps spending sessions after a
  terminal verdict;
* the live ledger's exit codes. ``soak_ledger.py status`` returns 1 for
  ``BET-FAILING`` *and* for ``INCONCLUSIVE`` with escalations, and 2 for
  ``DEGRADED`` / ``NO-DATA`` / ``NO-SEEDED-DATA``. The existing suite stubs
  ``rc=0``, so ``if st.returncode: return 2`` is invisible;
* ``verdict_is_terminal`` being prefix-only and case-sensitive.

Hermetic: ``dispatch`` is stubbed. Nothing here launches ``claude`` or
reads the live ledger.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import unittest
import unittest.mock as mock
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "soak_run_probe.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("soak_run_probe_stopping_rule", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = load_mod()


class _ReachedDispatch(Exception):
    """Sentinel: the spend control let the invocation through to dispatch."""


def _ledger_py(verdict_line: str, ledger_rc: int):
    def fake_py(*args, **kwargs):
        if args and args[0] == str(mod.LEDGER_TOOL):
            return subprocess.CompletedProcess(args=list(args), returncode=ledger_rc, stdout=verdict_line, stderr="")
        raise AssertionError(f"unexpected _py call: {args!r}")

    return fake_py


def _reached_dispatch(*_a, **_k):
    raise _ReachedDispatch()


class VerdictIsTerminalPrefixOnly(unittest.TestCase):
    """``startswith``, not ``in``. A substring match would refuse on chatter."""

    def test_the_two_terminal_names(self) -> None:
        self.assertTrue(mod.verdict_is_terminal("BET-FAILING"))
        self.assertTrue(mod.verdict_is_terminal("HOLDS-AT-0.75"))
        self.assertTrue(mod.verdict_is_terminal("HOLDS-AT-"))

    def test_a_substring_is_not_enough(self) -> None:
        for verdict in ("NOT-BET-FAILING", "PRE-BET-FAILING", "X-BET-FAILING"):
            with self.subTest(verdict=verdict):
                self.assertFalse(mod.verdict_is_terminal(verdict))

    def test_holds_at_requires_the_trailing_hyphen(self) -> None:
        for verdict in ("HOLDS-AT", "HOLDS-AT0.75", "HOLDS"):
            with self.subTest(verdict=verdict):
                self.assertFalse(mod.verdict_is_terminal(verdict))

    def test_case_is_significant(self) -> None:
        self.assertFalse(mod.verdict_is_terminal("bet-failing"))
        self.assertFalse(mod.verdict_is_terminal("holds-at-0.75"))

    def test_ledger_non_answers_are_not_terminal(self) -> None:
        for verdict in ("INCONCLUSIVE", "DEGRADED", "NO-DATA", "NO-SEEDED-DATA", ""):
            with self.subTest(verdict=verdict):
                self.assertFalse(mod.verdict_is_terminal(verdict))
                self.assertFalse(mod.refuses_terminal_verdict(verdict, force=False, dry_run=False))


class RealRunIsGatedThroughMain(unittest.TestCase):
    """#1690's e2e only drives ``--dry-run``. The spend control is the real run."""

    def _invoke(
        self,
        argv: list[str],
        verdict_line: str,
        *,
        ledger_rc: int = 0,
        dispatch=None,
    ) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        dispatch_impl = dispatch if dispatch is not None else mock.Mock(side_effect=AssertionError("dispatch must not run on this path"))
        with (
            mock.patch.object(mod, "_py", _ledger_py(verdict_line, ledger_rc)),
            mock.patch.object(mod, "dispatch", dispatch_impl),
            mock.patch.object(sys, "argv", argv),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            rc = mod.main()
        return rc, out.getvalue(), err.getvalue()

    def test_a_real_run_under_bet_failing_refuses_before_dispatch(self) -> None:
        rc, _, err = self._invoke(
            ["soak_run_probe.py"],
            "BET-FAILING  seeded=43/35 rate=60.5% ci=[0.456, 0.736]\n",
            ledger_rc=1,
        )
        self.assertEqual(rc, 2)
        self.assertIn("REFUSING", err)
        self.assertIn("BET-FAILING", err)

    def test_a_real_run_under_holds_at_refuses_before_dispatch(self) -> None:
        rc, _, err = self._invoke(
            ["soak_run_probe.py"],
            "HOLDS-AT-0.75  seeded=40/35 rate=82.0%\n",
        )
        self.assertEqual(rc, 2)
        self.assertIn("REFUSING", err)
        self.assertIn("HOLDS-AT-0.75", err)

    def test_force_reaches_dispatch_under_a_terminal_verdict(self) -> None:
        with self.assertRaises(_ReachedDispatch):
            self._invoke(
                ["soak_run_probe.py", "--force"],
                "BET-FAILING  seeded=43/35 rate=60.5%\n",
                ledger_rc=1,
                dispatch=_reached_dispatch,
            )

    def test_dry_run_under_holds_at_notes_and_proceeds(self) -> None:
        rc, out, err = self._invoke(
            ["soak_run_probe.py", "--dry-run"],
            "HOLDS-AT-0.75  seeded=40/35 rate=82.0%\n",
            dispatch=mock.Mock(return_value=("P-TEST", "secret task must not leak")),
        )
        self.assertEqual(rc, 0)
        self.assertNotIn("REFUSING", err)
        self.assertIn("HOLDS-AT-0.75", err)
        self.assertIn("priming", out.lower())
        self.assertNotIn("secret task must not leak", out)

    def test_inconclusive_with_ledger_exit_1_does_not_refuse(self) -> None:
        """Live ``status`` returns 1 when escalations are open, even if INCONCLUSIVE.

        Existing tests stub rc=0, so they cannot see a ``if st.returncode: return 2``
        that would refuse every escalated soak -- a spend-control false positive.
        """
        with self.assertRaises(_ReachedDispatch):
            self._invoke(
                ["soak_run_probe.py"],
                "INCONCLUSIVE  seeded=40/35 rate=65.0% escalations=1\n",
                ledger_rc=1,
                dispatch=_reached_dispatch,
            )

    def test_bet_failing_refuses_because_of_the_token_not_the_exit_code(self) -> None:
        """Same rc=1 as the INCONCLUSIVE+escalations case; only the token differs."""
        rc, _, err = self._invoke(
            ["soak_run_probe.py"],
            "BET-FAILING  seeded=43/35 rate=60.5%\n",
            ledger_rc=1,
        )
        self.assertEqual(rc, 2)
        self.assertIn("REFUSING", err)

    def test_degraded_fails_open_on_a_real_run(self) -> None:
        """Documented current semantics: DEGRADED / NO-DATA / NO-SEEDED-DATA are
        not terminal, and ``st.returncode`` is never consulted, so a real run
        proceeds. Pinning this is what makes a silent fail-closed change visible.
        """
        for verdict in ("DEGRADED", "NO-DATA", "NO-SEEDED-DATA"):
            with self.subTest(verdict=verdict), self.assertRaises(_ReachedDispatch):
                self._invoke(
                    ["soak_run_probe.py"],
                    f"{verdict}  seeded=0/35 rate=n/a\n",
                    ledger_rc=2,
                    dispatch=_reached_dispatch,
                )

    def test_a_ledger_tool_crash_fails_open(self) -> None:
        """Empty stdout + rc=2 is what a crashed ledger tool produces.

        ``verdict=""`` is not terminal. #1690 deferred fail-closed; this pin
        is how that deferral stays visible.
        """
        with self.assertRaises(_ReachedDispatch):
            self._invoke(
                ["soak_run_probe.py"],
                "",
                ledger_rc=2,
                dispatch=_reached_dispatch,
            )

    def test_a_prefixed_status_line_is_not_a_verdict(self) -> None:
        """Only ``stdout.split()[0]`` is consulted. A leading label hides the token."""
        with self.assertRaises(_ReachedDispatch):
            self._invoke(
                ["soak_run_probe.py"],
                "NOTE: BET-FAILING  seeded=43/35 rate=60.5%\n",
                dispatch=_reached_dispatch,
            )


if __name__ == "__main__":
    unittest.main()
