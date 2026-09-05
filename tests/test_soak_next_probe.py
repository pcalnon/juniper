#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for ``util/soak_next_probe.py``. ``util/`` is outside every pre-commit
Python hook's scope, so this suite is the only check on it.

What it pins, and why it matters more than it looks
---------------------------------------------------
The soak protocol's second requirement is that a probe reaches an UNPRIMED
session: it must never see the fact, the pointer or the discriminator before
answering (ledger §7; priming is what invalidated option A in §11 D2). A primed
run cannot be un-primed afterwards, and nothing downstream can detect it -- the
run just looks like a follow.

So the load-bearing property is a NEGATIVE one: stdout must carry the task and
NOTHING else. That is not visible by reading the output (a leak looks like extra
helpful context), which is exactly the kind of property that needs a test rather
than a careful author.

The second load-bearing property is WHICH probe is dispatched. Default pick is
least-covered then registry order -- that evens the pooled estimate. Organic,
pre-intervention, and non-observation rows (rescore / resolve / invalidate)
must not inflate a probe's count, or the timer under-samples it and
characterisation (``--probe-id``) silently diverges from least-covered.
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "soak_next_probe.py"
PROBES = REPO_ROOT / "conf" / "soak_probes.json"


def load_mod():
    spec = importlib.util.spec_from_file_location("soak_next_probe", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


mod = load_mod()


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )


def probes() -> list[dict]:
    return json.loads(PROBES.read_text(encoding="utf-8"))["probes"]


class StdoutCarriesOnlyTheTask(unittest.TestCase):
    """The unprimed guarantee. A leak here silently contaminates every run."""

    def test_default_stdout_is_exactly_one_probe_task(self) -> None:
        out = run().stdout.strip()
        self.assertTrue(out)
        tasks = {p["task"].strip() for p in probes()}
        self.assertIn(out, tasks)

    def test_stdout_never_contains_a_fact_pointer_or_discriminator(self) -> None:
        out = run().stdout
        for p in probes():
            for field in ("fact", "pointer", "evidence", "discriminator"):
                val = p.get(field)
                if isinstance(val, str) and val.strip():
                    self.assertNotIn(val.strip(), out, f"{field} of {p['probe_id']} leaked to stdout")

    def test_stdout_never_names_the_soak_or_the_probe_id(self) -> None:
        out = run().stdout.lower()
        for word in ("soak", "probe", "pointer-follow", "ledger", "rung"):
            self.assertNotIn(word, out, f"{word!r} leaked to stdout and primes the session")
        for p in probes():
            self.assertNotIn(p["probe_id"].lower(), out)

    def test_metadata_goes_to_stderr_so_a_redirect_stays_clean(self) -> None:
        r = run()
        self.assertIn("Paste ONLY the stdout", r.stderr)
        self.assertNotIn("Paste ONLY the stdout", r.stdout)


class RevealIsOptIn(unittest.TestCase):
    def test_reveal_shows_the_fact_and_the_discriminator(self) -> None:
        pid = probes()[0]["probe_id"]
        out = run("--reveal", "--probe-id", pid).stdout
        self.assertIn(probes()[0]["fact"], out)
        self.assertIn("discriminator", out)

    def test_reveal_does_not_print_a_pasteable_bare_task(self) -> None:
        # --reveal is for scoring. It must not double as a dispatch path, or an
        # operator could paste scoring output into a session and prime it.
        pid = probes()[0]["probe_id"]
        out = run("--reveal", "--probe-id", pid).stdout
        self.assertIn("probe_id", out)

    def test_status_prints_no_task_text(self) -> None:
        out = run("--status").stdout
        for p in probes():
            self.assertNotIn(p["task"].strip(), out)


class ProbeSelection(unittest.TestCase):
    def test_unknown_probe_id_is_rejected_not_silently_defaulted(self) -> None:
        r = run("--probe-id", "P99-does-not-exist")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout.strip(), "")

    def test_named_probe_is_honoured(self) -> None:
        p = probes()[3]
        self.assertEqual(run("--probe-id", p["probe_id"]).stdout.strip(), p["task"].strip())

    def test_status_lists_every_registered_probe(self) -> None:
        out = run("--status").stdout
        for p in probes():
            self.assertIn(p["probe_id"], out)


def _seeded(probe_id: str, ts: str | None, **extra: object) -> dict:
    row: dict = {
        "kind": "observation",
        "arm": "seeded",
        "ts": ts,
        "probe_id": probe_id,
    }
    row.update(extra)
    return row


class PostInterventionFilter(unittest.TestCase):
    """Least-covered counts must not include organic, pre-cut, or ledger-meta rows.

    A test must be able to fail for the reason it exists: if the filter is
    dropped, these cases return the row and the timer treats the probe as
    covered.
    """

    POST = "2026-08-31T00:00:00Z"
    PRE = "2026-08-30T23:59:59Z"

    def test_intervention_marker_is_the_rung1_date(self) -> None:
        self.assertEqual(mod.INTERVENTION, "2026-08-31")

    def test_post_intervention_seeded_observation_is_kept(self) -> None:
        rows = [_seeded("P01", self.POST)]
        self.assertEqual(mod.post_intervention(rows), rows)

    def test_pre_intervention_seeded_observation_is_excluded(self) -> None:
        rows = [_seeded("P01", self.PRE)]
        self.assertEqual(mod.post_intervention(rows), [])

    def test_organic_arm_is_excluded_even_when_post_intervention(self) -> None:
        rows = [_seeded("P01", self.POST, arm="organic")]
        self.assertEqual(mod.post_intervention(rows), [])

    def test_rescore_resolve_invalidate_do_not_count_as_coverage(self) -> None:
        for kind in ("rescore", "resolve", "invalidate"):
            with self.subTest(kind=kind):
                rows = [_seeded("P01", self.POST, kind=kind)]
                self.assertEqual(
                    mod.post_intervention(rows),
                    [],
                    f"{kind} rows must not inflate least-covered counts",
                )

    def test_missing_kind_is_treated_as_observation(self) -> None:
        row = {"arm": "seeded", "ts": self.POST, "probe_id": "P01"}
        self.assertEqual(mod.post_intervention([row]), [row])

    def test_missing_ts_is_excluded(self) -> None:
        # Empty / absent ts sorts before INTERVENTION and must not count.
        self.assertEqual(
            mod.post_intervention([{"kind": "observation", "arm": "seeded", "probe_id": "P01"}]),
            [],
        )
        self.assertEqual(mod.post_intervention([_seeded("P01", None)]), [])


class LeastCoveredThenRegistryOrder(unittest.TestCase):
    """Default dispatch evens the pooled estimate; --probe-id is characterisation.

    Hermetic: patches the module LEDGER so the live soak file cannot change
    which probe is selected. A test that read the real ledger would drift as
    runs accumulate and could not fail for a selection-logic regression.
    """

    def setUp(self) -> None:
        self._orig_ledger = mod.LEDGER
        self._plist = probes()
        self.assertGreaterEqual(len(self._plist), 2)

    def tearDown(self) -> None:
        mod.LEDGER = self._orig_ledger

    def _write_ledger(self, rows: list[dict]) -> None:
        tmp = Path(tempfile.mkdtemp()) / "pointer_follow_soak.jsonl"
        tmp.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        mod.LEDGER = tmp

    def _main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["soak_next_probe.py", *argv]):
            with redirect_stdout(out), redirect_stderr(err):
                rc = mod.main()
        return rc, out.getvalue(), err.getvalue()

    def test_empty_ledger_picks_the_first_registry_probe(self) -> None:
        self._write_ledger([])
        rc, out, err = self._main()
        first = self._plist[0]
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), first["task"].strip())
        self.assertIn(first["probe_id"], err)

    def test_default_picks_the_probe_with_fewest_post_intervention_runs(self) -> None:
        a, b = self._plist[0], self._plist[1]
        self._write_ledger(
            [
                _seeded(a["probe_id"], "2026-09-01T00:00:00Z"),
                _seeded(a["probe_id"], "2026-09-01T01:00:00Z"),
            ]
        )
        rc, out, err = self._main()
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), b["task"].strip())
        self.assertIn(b["probe_id"], err)
        self.assertNotIn(a["task"].strip(), out)

    def test_probe_id_overrides_least_covered_for_characterisation(self) -> None:
        a, b = self._plist[0], self._plist[1]
        self._write_ledger([_seeded(a["probe_id"], "2026-09-01T00:00:00Z")] * 5)
        rc, out, _err = self._main("--probe-id", a["probe_id"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), a["task"].strip())
        rc2, out2, _err2 = self._main()
        self.assertEqual(rc2, 0)
        self.assertEqual(out2.strip(), b["task"].strip())

    def test_pre_intervention_runs_do_not_make_a_probe_look_covered(self) -> None:
        a, b = self._plist[0], self._plist[1]
        self._write_ledger(
            [
                _seeded(b["probe_id"], "2026-08-01T00:00:00Z"),
                _seeded(b["probe_id"], "2026-08-15T00:00:00Z"),
                _seeded(a["probe_id"], "2026-09-01T00:00:00Z"),
            ]
        )
        rc, out, err = self._main()
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), b["task"].strip())
        self.assertIn(b["probe_id"], err)

    def test_organic_runs_do_not_make_a_probe_look_covered(self) -> None:
        a, b = self._plist[0], self._plist[1]
        self._write_ledger(
            [
                _seeded(b["probe_id"], "2026-09-01T00:00:00Z", arm="organic"),
                _seeded(b["probe_id"], "2026-09-01T01:00:00Z", arm="organic"),
                _seeded(a["probe_id"], "2026-09-01T00:00:00Z"),
            ]
        )
        rc, out, err = self._main()
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), b["task"].strip())
        self.assertIn(b["probe_id"], err)

    def test_rescore_rows_do_not_make_a_probe_look_covered(self) -> None:
        a, b = self._plist[0], self._plist[1]
        self._write_ledger(
            [
                _seeded(b["probe_id"], "2026-09-01T00:00:00Z", kind="rescore"),
                _seeded(a["probe_id"], "2026-09-01T00:00:00Z"),
            ]
        )
        rc, out, err = self._main()
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), b["task"].strip())
        self.assertIn(b["probe_id"], err)


if __name__ == "__main__":
    unittest.main()
