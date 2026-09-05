#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Producer/consumer contract for the soak spend control.

``util/soak_run_probe.py`` takes the soak verdict as
``(status.stdout.split() or [""])[0]``. #1690 and #1703 stub that token, so they
stay green if ``soak_ledger.py status`` grows a banner, a leading note, or
JSON-first output -- the spend control then fails open (first token is not
``BET-FAILING`` / ``HOLDS-AT-*``) or refuses every timer firing.

``tests/test_soak_ledger.py`` only asserts ``NO-DATA`` / ``DEGRADED`` appear
*somewhere* in stdout. ``StatusGuidanceSafety`` pins guidance order, not token 0.
This suite is the leftover those members cannot see.

Hermetic: synthetic ledgers only. Never launches ``claude``. Never reads the
live corpus. A test must be able to fail for the reason it exists -- prefixing
the status line with ``NOTE: `` leaves every sibling soak suite green.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import unittest
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_TOOL = REPO_ROOT / "util" / "soak_ledger.py"
PROBE_WRAPPER = REPO_ROOT / "util" / "soak_run_probe.py"

_spec = importlib.util.spec_from_file_location("soak_ledger_status_token", LEDGER_TOOL)
assert _spec and _spec.loader
sl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sl)

# The prefixes soak_run_probe.py treats as terminal. Duplicated as a pin, not
# imported: the wrapper on main inlines the tuple, and a later extract must not
# be required for this producer-side suite to run.
TERMINAL_PREFIXES = ("BET-FAILING", "HOLDS-AT-")


def obs(**kw) -> dict:
    d = {
        "obs_id": str(uuid.uuid4()),
        "kind": "observation",
        "ts": "2026-08-21T00:00:00Z",
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


def seeded_run(n_follow: int, n_miss: int, probes: int = 15, severity_hazard: bool = True) -> list[dict]:
    rows, i = [], 0
    for k in range(n_follow):
        rows.append(
            obs(
                session=f"s{i}",
                probe_id=f"P{i % probes:02d}",
                outcome="follow",
                severity="hazard" if (severity_hazard and k % 3 == 0) else "operational",
            )
        )
        i += 1
    for k in range(n_miss):
        rows.append(
            obs(
                session=f"s{i}",
                probe_id=f"P{i % probes:02d}",
                outcome="miss",
                miss_class="discoverability",
                area=["publish", "docs-ci", "experiments", "worktrees"][k % 4],
            )
        )
        i += 1
    return rows


def write(tmp: Path, rows: list[dict], name: str = "l.jsonl") -> Path:
    p = tmp / name
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


def status(*args: str, flags: tuple[str, ...] = ()) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603
        [sys.executable, str(LEDGER_TOOL), *args, "status", *flags],
        capture_output=True,
        text=True,
        timeout=30,
    )


def first_token(stdout: str) -> str:
    """The exact consumer parse in ``soak_run_probe.py``."""
    return (stdout.split() or [""])[0]


class StatusFirstTokenIsTheVerdict(unittest.TestCase):
    """``status`` stdout token 0 must be ``analyse()['verdict']``, nothing else."""

    def _assert_token(self, rows: list[dict] | None, *, ledger: Path | None = None) -> tuple[str, str]:
        if ledger is None:
            assert rows is not None
            expected = sl.analyse(rows)["verdict"]
            with TemporaryDirectory() as t:
                r = status("--ledger", str(write(Path(t), rows)))
                token = first_token(r.stdout)
                self.assertEqual(token, expected, msg=r.stdout)
                self.assertFalse(r.stdout.startswith((" ", "\t", "\n")), msg="leading whitespace hides the verdict from split()[0]")
                return token, r.stdout
        expected = sl.analyse(*sl.load_rows(ledger))["verdict"]
        r = status("--ledger", str(ledger))
        token = first_token(r.stdout)
        self.assertEqual(token, expected, msg=r.stdout)
        return token, r.stdout

    def test_bet_failing_is_the_first_token(self) -> None:
        token, _ = self._assert_token(seeded_run(14, 26))
        self.assertEqual(token, "BET-FAILING")

    def test_holds_at_names_the_boundary_as_the_first_token(self) -> None:
        token, _ = self._assert_token(seeded_run(38, 2))
        self.assertEqual(token, f"HOLDS-AT-{sl.DECISION_BOUNDARY}")

    def test_inconclusive_spanning_the_boundary_is_the_first_token(self) -> None:
        token, _ = self._assert_token(seeded_run(28, 12))
        self.assertEqual(token, "INCONCLUSIVE")

    def test_in_progress_is_the_first_token(self) -> None:
        token, _ = self._assert_token(seeded_run(10, 2))
        self.assertEqual(token, "IN-PROGRESS")

    def test_empty_hazard_stratum_is_inconclusive_as_the_first_token(self) -> None:
        token, _ = self._assert_token(seeded_run(40, 0, severity_hazard=False))
        self.assertEqual(token, "INCONCLUSIVE")

    def test_missing_ledger_is_no_data_as_the_first_token(self) -> None:
        with TemporaryDirectory() as t:
            missing = Path(t) / "absent.jsonl"
            r = status("--ledger", str(missing))
            self.assertEqual(first_token(r.stdout), "NO-DATA", msg=r.stdout)
            self.assertEqual(r.returncode, 2)

    def test_empty_ledger_is_no_data_as_the_first_token(self) -> None:
        with TemporaryDirectory() as t:
            empty = Path(t) / "e.jsonl"
            empty.write_text("", encoding="utf-8")
            r = status("--ledger", str(empty))
            self.assertEqual(first_token(r.stdout), "NO-DATA", msg=r.stdout)

    def test_corrupt_ledger_is_degraded_as_the_first_token(self) -> None:
        with TemporaryDirectory() as t:
            bad = Path(t) / "c.jsonl"
            bad.write_text("<<<<<<< HEAD\nnot json\n", encoding="utf-8")
            r = status("--ledger", str(bad))
            self.assertEqual(first_token(r.stdout), "DEGRADED", msg=r.stdout)
            self.assertEqual(r.returncode, 2)

    def test_organic_only_is_no_seeded_data_as_the_first_token(self) -> None:
        rows = [obs(session=f"o{i}", arm="organic", outcome="follow") for i in range(60)]
        token, _ = self._assert_token(rows)
        self.assertEqual(token, "NO-SEEDED-DATA")


class EscalationDoesNotStealTokenZero(unittest.TestCase):
    """An open rung-2 block used to print ABOVE the verdict. Token 0 must stay the verdict."""

    def test_open_hazard_leaves_the_verdict_first(self) -> None:
        rows = seeded_run(24, 11)
        rows.append(
            obs(
                session="s-haz",
                probe_id="P07",
                outcome="miss",
                severity="hazard",
                miss_class="discoverability",
                area="publish",
            )
        )
        expected = sl.analyse(rows)["verdict"]
        with TemporaryDirectory() as t:
            r = status("--ledger", str(write(Path(t), rows)))
        self.assertEqual(first_token(r.stdout), expected, msg=r.stdout)
        self.assertIn("rung 2", r.stdout)
        self.assertGreater(r.stdout.index("rung 2"), 0)
        self.assertFalse(first_token(r.stdout).startswith("rung"))


class DefaultStatusIsNotJson(unittest.TestCase):
    """The consumer is a whitespace split. JSON-first output would make token 0 ``{``."""

    def test_default_status_does_not_start_with_a_brace(self) -> None:
        with TemporaryDirectory() as t:
            r = status("--ledger", str(write(Path(t), seeded_run(10, 2))))
        self.assertFalse(r.stdout.lstrip().startswith("{"), msg=r.stdout[:80])
        self.assertEqual(first_token(r.stdout), "IN-PROGRESS")

    def test_json_flag_is_opt_in(self) -> None:
        with TemporaryDirectory() as t:
            r = status("--ledger", str(write(Path(t), seeded_run(10, 2))), flags=("--json",))
        self.assertTrue(r.stdout.lstrip().startswith("{"), msg=r.stdout[:80])
        payload = json.loads(r.stdout)
        self.assertEqual(payload["verdict"], "IN-PROGRESS")


class TerminalPrefixesMatchTheSpendControl(unittest.TestCase):
    """The tokens this producer emits are the ones the wrapper treats as terminal."""

    def test_bet_failing_matches_a_terminal_prefix(self) -> None:
        self.assertTrue(any("BET-FAILING".startswith(p) for p in TERMINAL_PREFIXES))

    def test_holds_at_token_matches_a_terminal_prefix(self) -> None:
        token = f"HOLDS-AT-{sl.DECISION_BOUNDARY}"
        self.assertTrue(any(token.startswith(p) for p in TERMINAL_PREFIXES))

    def test_non_answers_are_not_terminal_tokens(self) -> None:
        for verdict in ("INCONCLUSIVE", "IN-PROGRESS", "NO-DATA", "DEGRADED", "NO-SEEDED-DATA", ""):
            with self.subTest(verdict=verdict):
                self.assertFalse(any(verdict.startswith(p) for p in TERMINAL_PREFIXES))

    def test_the_consumer_still_reads_stdout_split_zero(self) -> None:
        """A parse change in the wrapper (JSON, second field, regex) silently drops this contract."""
        src = PROBE_WRAPPER.read_text(encoding="utf-8")
        self.assertIn('verdict = (st.stdout.split() or [""])[0]', src)


if __name__ == "__main__":
    unittest.main()
