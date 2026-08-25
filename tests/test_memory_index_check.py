#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Tests for ``util/memory_index_check.py`` -- enforcement option A of
``notes/JUNIPER_2026-08-24_JUNIPER-ML_MEMORY-INDEX-RUNWAY-AND-ENFORCEMENT-OPTIONS.md``.

``util/`` is outside every pre-commit Python hook's scope (flake8/bandit scope to
``scripts/`` + ``tests/``), so this suite IS the gate.

The load-bearing cases are the ones that would let this become another
vacuous-pass check:

* a MISSING memory file must be exit 2, not a silent success -- the tool's whole
  subject is a file that lives outside the repo, so "not found" is the easiest
  possible way for it to pass while measuring nothing;
* the cap must bind the HOOK, not the line. A whole-line reading is unwritable
  (the link alone averages 90 B, max 115) and would fire on every row;
* grandfathered rows must NOT fire, or the first run makes 137 findings and the
  tool gets ignored;
* over the HARD cap must fail, because that is the point at which the index is
  already being truncated silently.
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
MODULE_PATH = REPO_ROOT / "util" / "memory_index_check.py"

_spec = importlib.util.spec_from_file_location("memory_index_check", MODULE_PATH)
assert _spec and _spec.loader
mic = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mic)


def row(slug: str, hook: str = " — short hook", title: str = "T") -> str:
    return f"- [{title}]({slug}){hook}"


def write_memory(tmp: Path, rows: list[str], name: str = "MEMORY.md") -> Path:
    p = tmp / name
    p.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return p


def write_baseline(tmp: Path, slugs: list[str], history: list[dict] | None = None) -> Path:
    p = tmp / "baseline.json"
    p.write_text(json.dumps({"slugs": slugs, "history": history or []}), encoding="utf-8")
    return p


def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603,B607 - fixed argv, hermetic fixtures
        [sys.executable, str(MODULE_PATH), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


class FailsClosed(unittest.TestCase):
    """A check that cannot find its subject must not report success."""

    def test_missing_memory_file_is_exit_two(self) -> None:
        with TemporaryDirectory() as t:
            r = cli("--memory-file", str(Path(t) / "nope.md"), "--baseline", str(write_baseline(Path(t), [])))
            self.assertEqual(r.returncode, 2, msg=r.stdout + r.stderr)
            self.assertIn("not found", r.stderr)

    def test_skip_if_absent_is_explicit_and_announced(self) -> None:
        with TemporaryDirectory() as t:
            r = cli("--memory-file", str(Path(t) / "nope.md"), "--baseline", str(write_baseline(Path(t), [])), "--skip-if-absent")
            self.assertEqual(r.returncode, 0)
            self.assertIn("SKIPPED", r.stdout)

    def test_malformed_baseline_is_exit_two(self) -> None:
        with TemporaryDirectory() as t:
            tmp = Path(t)
            m = write_memory(tmp, [row("a.md")])
            b = tmp / "baseline.json"
            b.write_text("{not json", encoding="utf-8")
            r = cli("--memory-file", str(m), "--baseline", str(b))
            self.assertEqual(r.returncode, 2, msg=r.stdout + r.stderr)

    def test_baseline_absent_is_tolerated_not_fatal(self) -> None:
        """First run has no baseline; every row is new, which is the point."""
        with TemporaryDirectory() as t:
            tmp = Path(t)
            m = write_memory(tmp, [row("a.md")])
            r = cli("--memory-file", str(m), "--baseline", str(tmp / "absent.json"), "--json")
            self.assertEqual(r.returncode, 0)
            self.assertEqual(json.loads(r.stdout)["new_rows"], 1)


class HardCap(unittest.TestCase):
    def test_over_byte_cap_fails(self) -> None:
        with TemporaryDirectory() as t:
            tmp = Path(t)
            big = [row(f"s{i}.md", hook=" — " + "x" * 100) for i in range(300)]
            m = write_memory(tmp, big)
            r = cli("--memory-file", str(m), "--baseline", str(write_baseline(tmp, [f"s{i}.md" for i in range(300)])))
            self.assertEqual(r.returncode, 1, msg=r.stdout)
            self.assertIn("OVER THE HARD CAP", r.stdout)

    def test_under_cap_passes(self) -> None:
        with TemporaryDirectory() as t:
            tmp = Path(t)
            m = write_memory(tmp, [row("a.md"), row("b.md")])
            r = cli("--memory-file", str(m), "--baseline", str(write_baseline(tmp, ["a.md", "b.md"])))
            self.assertEqual(r.returncode, 0, msg=r.stdout)
            self.assertIn("OK:", r.stdout)


class HookCapBindsTheHookNotTheLine(unittest.TestCase):
    """A whole-line reading is unwritable and would fire on ordinary rows."""

    def test_long_link_short_hook_passes(self) -> None:
        long_slug = "reference_" + "a" * 130 + ".md"
        with TemporaryDirectory() as t:
            tmp = Path(t)
            m = write_memory(tmp, [row(long_slug, hook=" — tiny")])
            line = m.read_text(encoding="utf-8").splitlines()[0]
            # The point of the case: this LINE is over the budget while its HOOK
            # is nowhere near it. A whole-line cap would fire here, on a row that
            # is entirely well-behaved -- which is why the cap binds the hook.
            self.assertGreater(len(line), 120, msg=f"fixture must exceed the budget as a LINE: {len(line)}")
            r = cli("--memory-file", str(m), "--baseline", str(write_baseline(tmp, [])))
            self.assertEqual(r.returncode, 0, msg=r.stdout)

    def test_new_row_with_oversize_hook_fails(self) -> None:
        with TemporaryDirectory() as t:
            tmp = Path(t)
            m = write_memory(tmp, [row("new.md", hook=" — " + "x" * 200)])
            r = cli("--memory-file", str(m), "--baseline", str(write_baseline(tmp, [])))
            self.assertEqual(r.returncode, 1, msg=r.stdout)
            self.assertIn("new.md", r.stdout)
            self.assertIn("hook", r.stdout)

    def test_grandfathered_oversize_hook_does_not_fire(self) -> None:
        """Existing rows are not rewritten -- decision #4, and the reason the
        first run does not produce 137 findings and get ignored."""
        with TemporaryDirectory() as t:
            tmp = Path(t)
            m = write_memory(tmp, [row("old.md", hook=" — " + "x" * 200)])
            r = cli("--memory-file", str(m), "--baseline", str(write_baseline(tmp, ["old.md"])))
            self.assertEqual(r.returncode, 0, msg=r.stdout)

    def test_hook_max_is_configurable(self) -> None:
        with TemporaryDirectory() as t:
            tmp = Path(t)
            m = write_memory(tmp, [row("new.md", hook=" — " + "x" * 50)])
            base = str(write_baseline(tmp, []))
            self.assertEqual(cli("--memory-file", str(m), "--baseline", base, "--hook-max", "200").returncode, 0)
            self.assertEqual(cli("--memory-file", str(m), "--baseline", base, "--hook-max", "10").returncode, 1)


class AdvisoryAndAccept(unittest.TestCase):
    def test_advisory_always_exits_zero(self) -> None:
        with TemporaryDirectory() as t:
            tmp = Path(t)
            m = write_memory(tmp, [row("new.md", hook=" — " + "x" * 200)])
            r = cli("--memory-file", str(m), "--baseline", str(write_baseline(tmp, [])), "--advisory")
            self.assertEqual(r.returncode, 0)
            self.assertIn("hook", r.stdout)  # still REPORTS the violation

    def test_accept_grandfathers_and_records_a_sample(self) -> None:
        with TemporaryDirectory() as t:
            tmp = Path(t)
            m = write_memory(tmp, [row("new.md", hook=" — " + "x" * 200)])
            b = write_baseline(tmp, [])
            self.assertEqual(cli("--memory-file", str(m), "--baseline", str(b), "--accept").returncode, 0)
            data = json.loads(b.read_text(encoding="utf-8"))
            self.assertIn("new.md", data["slugs"])
            self.assertEqual(len(data["history"]), 1)
            self.assertIn("bytes", data["history"][0])
            # And the previously-failing row now passes.
            self.assertEqual(cli("--memory-file", str(m), "--baseline", str(b)).returncode, 0)


class Runway(unittest.TestCase):
    def test_needs_two_samples(self) -> None:
        self.assertIsNone(mic.runway_days([{"date": "2026-08-19", "bytes": 100}], 1000))

    def test_computes_from_the_last_two(self) -> None:
        hist = [
            {"date": "2026-08-19", "bytes": 16933},
            {"date": "2026-08-24", "bytes": 20256},
        ]
        # (20256-16933)/5 = 664.6 B/day; 4744 headroom -> ~7.1 days
        self.assertAlmostEqual(mic.runway_days(hist, 4744), 7.14, places=1)

    def test_shrinking_index_is_infinite_not_negative(self) -> None:
        hist = [{"date": "2026-08-19", "bytes": 20000}, {"date": "2026-08-24", "bytes": 18000}]
        self.assertEqual(mic.runway_days(hist, 5000), float("inf"))

    def test_same_day_samples_do_not_divide_by_zero(self) -> None:
        hist = [{"date": "2026-08-24", "bytes": 100}, {"date": "2026-08-24", "bytes": 200}]
        self.assertIsNone(mic.runway_days(hist, 1000))


class Parsing(unittest.TestCase):
    def test_non_row_lines_are_ignored(self) -> None:
        rows = mic.parse_rows("# heading\n\nsome prose\n" + row("a.md") + "\n")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["slug"], "a.md")

    def test_hook_excludes_the_link(self) -> None:
        r = mic.parse_rows(row("some_long_slug_name.md", hook=" — hook"))[0]
        self.assertEqual(r["hook"], " — hook")
        self.assertLess(r["hook_len"], r["line_len"])


class ShippedConstantsMatchTheRealLimits(unittest.TestCase):
    """These are the shipped truncation limits, not preferences."""

    def test_hard_caps(self) -> None:
        self.assertEqual(mic.HARD_MAX_LINES, 200)
        self.assertEqual(mic.HARD_MAX_BYTES, 25000)

    def test_hook_default_is_decision_four(self) -> None:
        self.assertEqual(mic.DEFAULT_HOOK_MAX, 120)


if __name__ == "__main__":
    unittest.main()
